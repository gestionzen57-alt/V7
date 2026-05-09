#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — run_orchestral_loop.py

Live loop: computes orchestral gravity state at regular intervals
and writes the result to JSON.

Read-only DB access. No writes. No Telegram. No crash.

Usage:
    # Default — LTF + M30, interval 60s, overwrite mode
    python run_orchestral_loop.py --db powerflow.db --symbol GBPUSD

    # Custom TFs, 30s interval, timestamped files
    python run_orchestral_loop.py \\
        --db powerflow.db --symbol GBPUSD \\
        --tfs "1,5,15,30,60" \\
        --interval 30 \\
        --lookback 180 \\
        --output output/orchestral_live.json \\
        --no-overwrite

    # HTF strategic
    python run_orchestral_loop.py \\
        --db powerflow.db --symbol GBPUSD \\
        --tfs "60,240,1440" \\
        --interval 300 \\
        --lookback 2880

    # Debug / single run test
    python run_orchestral_loop.py \\
        --db powerflow.db --symbol GBPUSD \\
        --once --pretty
"""

from __future__ import annotations

import argparse
import json
import logging
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from pf_orchestral_gravity_v02 import (
    compute_orchestra_multi_tf,
    OrchestraState,
)


# ==========================================================================
# CONSTANTS
# ==========================================================================

DEFAULT_TFS            = [1, 5, 15, 30]
DEFAULT_INTERVAL_SEC   = 60
DEFAULT_LOOKBACK_MIN   = 180
DEFAULT_AVG_BARS       = 3
DEFAULT_OUTPUT         = "output/orchestral_live.json"

TF_LABELS = {
    1: "M1", 5: "M5", 15: "M15", 30: "M30",
    60: "H1", 240: "H4", 1440: "D", 10080: "W",
}


# ==========================================================================
# LOGGING
# ==========================================================================

def _setup_logging(level: str) -> logging.Logger:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logging.basicConfig(
        level=lvl,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("orchestral_loop")


# ==========================================================================
# WINDOW BUILDER
# ==========================================================================

def _build_window(lookback_minutes: int) -> tuple[str, str]:
    """
    Build start/end ISO8601 strings for the lookback window ending NOW.
    """
    now = datetime.now(timezone.utc)
    start = now - timedelta(minutes=lookback_minutes)
    fmt = "%Y-%m-%dT%H:%M:%S+00:00"
    return start.strftime(fmt), now.strftime(fmt)


# ==========================================================================
# STATE BUILDER
# ==========================================================================

def _build_state(
    db_path: str,
    symbol: str,
    timeframes: List[int],
    lookback_minutes: int,
    avg_bars: int,
) -> Dict[str, Any]:
    """
    Compute orchestral state and return structured dict ready for JSON.
    """
    start, end = _build_window(lookback_minutes)
    now_ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    # Compute per-TF orchestra states
    try:
        states: Dict[int, Optional[OrchestraState]] = compute_orchestra_multi_tf(
            db_path, symbol, timeframes, start, end, avg_bars=avg_bars
        )
    except Exception as exc:
        return {
            "timestamp": now_ts,
            "symbol": symbol,
            "window_start": start,
            "window_end": end,
            "state": "ORCHESTRAL_LOOP_ERROR",
            "error": str(exc),
            "timeframes": {},
            "latest_tf": None,
            "latest_state": None,
            "compression_detected": False,
            "leader_currency": None,
            "patterns": [],
        }

    # Serialize per-TF
    tf_results: Dict[str, Any] = {}
    valid_tfs: List[int] = []

    for tf in timeframes:
        s = states.get(tf)
        if s is None:
            tf_results[str(tf)] = {
                "state": "ORCHESTRAL_TF_NO_DATA",
                "tf_label": TF_LABELS.get(tf, f"TF{tf}"),
            }
        else:
            tf_results[str(tf)] = {
                "tf_label": TF_LABELS.get(tf, f"TF{tf}"),
                **s.to_dict(),
            }
            valid_tfs.append(tf)

    # Latest TF = highest available
    latest_tf = max(valid_tfs) if valid_tfs else None
    latest_state_dict = None
    compression_detected = False
    leader_currency = None
    all_patterns: List[str] = []

    if latest_tf is not None:
        ls = states[latest_tf]
        if ls:
            latest_state_dict = ls.to_dict()
            all_patterns = ls.patterns or []
            compression_detected = "ORCHESTRAL_COMPRESSION" in all_patterns
            leader_currency = ls.leaders[0] if ls.leaders else None

    overall_state = "ORCHESTRAL_ACTIVE" if valid_tfs else "ORCHESTRAL_ALL_TF_FAILED"

    return {
        "timestamp": now_ts,
        "symbol": symbol,
        "window_start": start,
        "window_end": end,
        "lookback_minutes": lookback_minutes,
        "avg_bars": avg_bars,
        "state": overall_state,
        "timeframes": tf_results,
        "valid_tfs": valid_tfs,
        "latest_tf": latest_tf,
        "latest_tf_label": TF_LABELS.get(latest_tf, None) if latest_tf else None,
        "latest_state": latest_state_dict,
        "compression_detected": compression_detected,
        "leader_currency": leader_currency,
        "patterns": all_patterns,
    }


# ==========================================================================
# OUTPUT WRITER
# ==========================================================================

def _write_output(
    data: Dict[str, Any],
    output_path: str,
    overwrite: bool,
    pretty: bool,
) -> str:
    """
    Write state dict to JSON file.
    Returns the actual path written.
    """
    indent = 2 if pretty else None
    content = json.dumps(data, ensure_ascii=False, indent=indent)

    if overwrite:
        path = Path(output_path)
    else:
        # Timestamped filename: orchestral_live_20260507_142345.json
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        p = Path(output_path)
        path = p.parent / f"{p.stem}_{ts}{p.suffix}"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return str(path)


# ==========================================================================
# LOOP SUMMARY (console log)
# ==========================================================================

def _log_summary(log: logging.Logger, data: Dict[str, Any], elapsed: float) -> None:
    """Log a one-liner summary of the current state."""
    state = data.get("state", "?")
    leader = data.get("leader_currency") or "—"
    compression = "⚠ COMPRESSION" if data.get("compression_detected") else ""
    patterns = data.get("patterns", [])
    pat_str = f" | patterns={patterns}" if patterns else ""
    valid = data.get("valid_tfs", [])
    tfs_str = ",".join(TF_LABELS.get(t, str(t)) for t in valid)

    log.info(
        f"[{state}] leader={leader} tfs=[{tfs_str}] "
        f"{compression}{pat_str} ({elapsed:.2f}s)"
    )


# ==========================================================================
# GRACEFUL SHUTDOWN
# ==========================================================================

_RUNNING = True

def _handle_signal(sig, frame):
    global _RUNNING
    _RUNNING = False


# ==========================================================================
# MAIN LOOP
# ==========================================================================

def run_loop(
    db_path: str,
    symbol: str,
    timeframes: List[int],
    interval: int,
    lookback_minutes: int,
    avg_bars: int,
    output_path: str,
    overwrite: bool,
    pretty: bool,
    once: bool,
    log: logging.Logger,
) -> int:

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    if not Path(db_path).exists():
        log.error(f"DB not found: {db_path}")
        return 1

    tf_labels = [TF_LABELS.get(t, str(t)) for t in timeframes]
    log.info(
        f"🎼 Orchestral Loop starting — "
        f"symbol={symbol} tfs=[{','.join(tf_labels)}] "
        f"interval={interval}s lookback={lookback_minutes}min"
    )
    if once:
        log.info("Mode: SINGLE RUN (--once)")
    else:
        log.info(f"Mode: LOOP | output={output_path} overwrite={overwrite}")

    loop_count = 0

    while _RUNNING:
        loop_count += 1
        t0 = time.time()

        # --- Compute ---
        try:
            data = _build_state(
                db_path, symbol, timeframes, lookback_minutes, avg_bars
            )
        except Exception as exc:
            log.error(f"Loop #{loop_count} — unexpected error: {exc}")
            if once:
                return 1
            time.sleep(interval)
            continue

        elapsed = time.time() - t0

        # --- Log ---
        _log_summary(log, data, elapsed)

        # --- Write ---
        if once:
            # Print to stdout
            indent = 2 if pretty else None
            print(json.dumps(data, ensure_ascii=False, indent=indent))
        else:
            try:
                written = _write_output(data, output_path, overwrite, pretty)
                log.debug(f"Written → {written}")
            except Exception as exc:
                log.error(f"Write failed: {exc}")

        if once or not _RUNNING:
            break

        # --- Sleep (interruptible) ---
        sleep_remaining = interval - (time.time() - t0)
        if sleep_remaining > 0:
            # Sleep in small chunks to respond quickly to Ctrl+C
            chunks = max(1, int(sleep_remaining))
            for _ in range(chunks):
                if not _RUNNING:
                    break
                time.sleep(min(1.0, sleep_remaining))
                sleep_remaining -= 1.0

    log.info(f"🎼 Orchestral Loop stopped after {loop_count} iteration(s).")
    return 0


# ==========================================================================
# CLI
# ==========================================================================

def parse_tfs(value: str) -> List[int]:
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(
        description="PowerFlow V6 — Orchestral Gravity Live Loop",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Default loop (LTF + M30, 60s interval)
  python run_orchestral_loop.py --db powerflow.db --symbol GBPUSD

  # HTF strategic, 5min interval
  python run_orchestral_loop.py --db powerflow.db --tfs "60,240,1440" --interval 300

  # Single run test (prints JSON to stdout)
  python run_orchestral_loop.py --db powerflow.db --once --pretty

  # Timestamped files (no overwrite)
  python run_orchestral_loop.py --db powerflow.db --no-overwrite --output output/orch.json
        """,
    )

    ap.add_argument(
        "--db",
        default="powerflow.db",
        help="Path to powerflow.db (default: powerflow.db)",
    )
    ap.add_argument(
        "--symbol",
        default="GBPUSD",
        help="Symbol (default: GBPUSD)",
    )
    ap.add_argument(
        "--tfs",
        default=None,
        help="Comma-separated timeframes in minutes (default: 1,5,15,30)",
    )
    ap.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SEC,
        help=f"Seconds between each loop iteration (default: {DEFAULT_INTERVAL_SEC})",
    )
    ap.add_argument(
        "--lookback",
        type=int,
        default=DEFAULT_LOOKBACK_MIN,
        help=f"Lookback window in minutes (default: {DEFAULT_LOOKBACK_MIN})",
    )
    ap.add_argument(
        "--avg-bars",
        type=int,
        default=DEFAULT_AVG_BARS,
        help=f"Bars to average for angle smoothing (default: {DEFAULT_AVG_BARS})",
    )
    ap.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help=f"Output JSON file path (default: {DEFAULT_OUTPUT})",
    )
    ap.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Write timestamped files instead of overwriting (default: overwrite)",
    )
    ap.add_argument(
        "--pretty",
        action="store_true",
        help="Indent JSON output (default: compact)",
    )
    ap.add_argument(
        "--once",
        action="store_true",
        help="Run once and print to stdout (for testing)",
    )
    ap.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log verbosity (default: INFO)",
    )

    args = ap.parse_args()

    log = _setup_logging(args.log_level)

    # Resolve TFs
    if args.tfs:
        timeframes = parse_tfs(args.tfs)
    else:
        timeframes = DEFAULT_TFS

    if not timeframes:
        log.error("No valid timeframes provided.")
        return 1

    return run_loop(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=timeframes,
        interval=args.interval,
        lookback_minutes=args.lookback,
        avg_bars=args.avg_bars,
        output_path=args.output,
        overwrite=not args.no_overwrite,
        pretty=args.pretty,
        once=args.once,
        log=log,
    )


if __name__ == "__main__":
    raise SystemExit(main())
