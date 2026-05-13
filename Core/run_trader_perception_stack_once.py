#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.6 — Trader Perception Stack Runner E

Modes:
- Single symbol:
    python run_trader_perception_stack_once.py --symbol GBPUSD

- Multi-symbol compact scan:
    python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY

- Multi-symbol table scan:
    python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table

- Watch loop:
    python run_trader_perception_stack_once.py --symbols GBPUSD,EURUSD,USDJPY --table --watch-loop --interval 20

Stack per symbol:
1. pf_temporal_compression_reader_once.py
2. pf_legacy_behavioral_bridge_once.py
3. pf_perception_spine_once.py
4. pf_trader_attention_packet_once.py --compact

Doctrine:
- Does not decide trades.
- Refreshes perception layers and prints the final trader attention packet.
- In table mode, prints one minimal scan row per symbol.
- Watch loop refreshes terminal perception without Telegram.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Sequence


@dataclass
class StepResult:
    name: str
    command: list[str]
    returncode: int
    elapsed_seconds: float
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _run_step(
    name: str,
    command: Sequence[str],
    cwd: Path,
    *,
    required: bool = True,
    echo: bool = False,
) -> StepResult:
    started = time.perf_counter()

    proc = subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    result = StepResult(
        name=name,
        command=list(command),
        returncode=proc.returncode,
        elapsed_seconds=round(time.perf_counter() - started, 3),
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )

    if echo:
        if result.stdout.strip():
            print(result.stdout.strip())
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)

    if required and not result.ok:
        print(f"[STACK_FAIL] {name} returncode={result.returncode}", file=sys.stderr)
        if result.stdout.strip():
            print(result.stdout.strip(), file=sys.stderr)
        if result.stderr.strip():
            print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode or 1)

    return result


def _compact_tail(text: str, max_chars: int = 4000) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return "[...TAIL...]\n" + text[-max_chars:]


def _symbol_dir(core: Path, symbol: str) -> Path:
    return core / "output" / "dashboard_surface" / symbol.upper()


def _packet_json_path(core: Path, symbol: str) -> Path:
    return _symbol_dir(core, symbol) / "trader_attention_packet.json"


def _packet_txt_path(core: Path, symbol: str) -> Path:
    return _symbol_dir(core, symbol) / "trader_attention_packet.txt"


def _read_json(path: Path) -> dict:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def _first_existing(data: dict, keys: list[str], default=None):
    for key in keys:
        if key in data and data[key] not in (None, "", [], {}):
            return data[key]
    return default


def _as_text(value, default: str = "NONE") -> str:
    if value in (None, "", [], {}):
        return default
    if isinstance(value, list):
        return ",".join(str(x) for x in value if str(x)) or default
    return str(value)


def _short_attention(attention: str) -> str:
    a = (attention or "").upper()
    if "WAKE" in a:
        return "WAKE"
    if "WATCH" in a:
        return "WATCH"
    if "OBSERVE" in a:
        return "OBSERVE"
    if "IDLE" in a:
        return "IDLE"
    return a[:12] or "UNKNOWN"


def _short_film(film: str) -> str:
    f = (film or "").upper()
    mapping = [
        ("ELASTIC_RELEASE", "ELASTIC_RELEASE"),
        ("MULTI_TF_ELASTIC_LOADING", "ELASTIC_LOADING"),
        ("TIME_COMP_LOCK", "TEMPORAL_LOCK"),
        ("COMPRESSION_LOADING", "ELASTIC_LOADING"),
        ("LOW_SIGNAL", "LOW_SIGNAL"),
    ]
    for needle, label in mapping:
        if needle in f:
            return label
    return f[:22] or "UNKNOWN"


def _short_next(next_wake: str) -> str:
    n = (next_wake or "").upper()
    mapping = [
        ("LOCK_ACCEPTANCE_AFTER_RELEASE", "LOCK_ACCEPTANCE"),
        ("TIME_COMP_BREAK", "TIME_BREAK"),
        ("COMPRESSION_BREAK", "COMP_BREAK"),
        ("KISS_REJECT", "KISS_REJECT"),
        ("SLINGSHOT", "SLINGSHOT"),
        ("ZONE_REJECTION", "ZONE_REJECT"),
        ("SECOND_LEG", "SECOND_LEG"),
        ("COUNTER_BREATH", "COUNTER_BREATH"),
    ]
    for needle, label in mapping:
        if needle in n:
            return label
    return n[:18] or "NONE"


def _packet_data(core: Path, symbol: str) -> dict:
    data = _read_json(_packet_json_path(core, symbol))
    return data if data else {}


def _one_line_from_packet(core: Path, symbol: str, fallback_stdout: str = "") -> str:
    sym = symbol.upper()
    data = _packet_data(core, sym)

    if data:
        attention = _as_text(_first_existing(data, ["attention", "attention_level", "status"], "UNKNOWN"))
        film = _as_text(_first_existing(data, ["main_film", "film", "state"], "UNKNOWN"))
        next_wake = _as_text(_first_existing(data, ["next_wake", "wake", "next"], "NONE"))
        bias = _as_text(_first_existing(data, ["bias"], "UNKNOWN"), "UNKNOWN")
        score = _first_existing(data, ["score"], None)
        conflict = _as_text(_first_existing(data, ["conflict", "main_conflict"], "NONE"), "NONE")

        score_txt = ""
        try:
            if score is not None:
                score_txt = f" score={round(float(score), 2)}"
        except Exception:
            score_txt = f" score={score}"

        conflict_txt = "" if conflict in ("NONE", "NA", "") else f" conflict={conflict}"
        return f"{sym} | {attention} | {film} | bias={bias}{score_txt} next={next_wake}{conflict_txt}"

    lines = [line.strip() for line in (fallback_stdout or "").splitlines() if line.strip()]
    if lines:
        return lines[0]

    txt = _packet_txt_path(core, sym)
    if txt.exists():
        lines = [line.strip() for line in txt.read_text(encoding="utf-8").splitlines() if line.strip()]
        if lines:
            return lines[0]

    return f"{sym} | PACKET_MISSING | no trader_attention_packet found"


def _table_row(core: Path, symbol: str) -> dict:
    sym = symbol.upper()
    data = _packet_data(core, sym)

    if not data:
        return {
            "SYMBOL": sym,
            "ATTN": "MISSING",
            "FILM": "PACKET_MISSING",
            "BIAS": "UNKNOWN",
            "NEXT": "NONE",
            "SCORE": "",
            "RISK": "",
        }

    attention = _as_text(_first_existing(data, ["attention", "attention_level", "status"], "UNKNOWN"))
    film = _as_text(_first_existing(data, ["main_film", "film", "state"], "UNKNOWN"))
    bias = _as_text(_first_existing(data, ["bias"], "UNKNOWN"), "UNKNOWN")
    next_wake = _as_text(_first_existing(data, ["next_wake", "wake", "next"], "NONE"))
    score = _first_existing(data, ["score"], "")
    technical_risks = _first_existing(data, ["technical_risks"], [])
    weak_layers = _first_existing(data, ["weak_layers"], [])

    risk_flags = []
    risk_text = _as_text(technical_risks, "")
    weak_text = _as_text(weak_layers, "")
    if "EVENT_TIME_AHEAD_OF_DETECTED_AT" in risk_text or "TIME_SYNC" in weak_text:
        risk_flags.append("TIME")
    if "COUNTERFLOW" in risk_text:
        risk_flags.append("CFLOW")
    if "GAPS" in risk_text:
        risk_flags.append("GAP")

    try:
        score_txt = str(round(float(score), 1)) if score not in ("", None) else ""
    except Exception:
        score_txt = str(score)

    return {
        "SYMBOL": sym,
        "ATTN": _short_attention(attention),
        "FILM": _short_film(film),
        "BIAS": bias,
        "NEXT": _short_next(next_wake),
        "SCORE": score_txt,
        "RISK": ",".join(risk_flags) if risk_flags else "-",
    }


def _print_table(rows: list[dict]) -> None:
    headers = ["SYMBOL", "ATTN", "FILM", "BIAS", "NEXT", "SCORE", "RISK"]
    widths = {h: len(h) for h in headers}
    for row in rows:
        for h in headers:
            widths[h] = max(widths[h], len(str(row.get(h, ""))))

    header = "  ".join(h.ljust(widths[h]) for h in headers)
    sep = "  ".join("-" * widths[h] for h in headers)
    print(header)
    print(sep)
    for row in rows:
        print("  ".join(str(row.get(h, "")).ljust(widths[h]) for h in headers))


def run_stack_single(
    *,
    symbol: str,
    lookback_minutes: int,
    core: Path,
    continue_on_error: bool,
    verbose: bool,
    final_echo: bool,
) -> tuple[int, str]:
    sym = symbol.upper()
    py = sys.executable

    steps: list[tuple[str, list[str], bool]] = [
        (
            "temporal_compression",
            [
                py,
                "pf_temporal_compression_reader_once.py",
                "--symbol",
                sym,
                "--lookback-minutes",
                str(lookback_minutes),
                "--pretty",
            ],
            False,
        ),
        (
            "legacy_behavioral_bridge",
            [
                py,
                "pf_legacy_behavioral_bridge_once.py",
                "--symbol",
                sym,
                "--lookback-minutes",
                str(lookback_minutes),
                "--pretty",
            ],
            False,
        ),
        (
            "perception_spine",
            [
                py,
                "pf_perception_spine_once.py",
                "--symbol",
                sym,
                "--pretty",
            ],
            False,
        ),
        (
            "trader_attention_packet",
            [
                py,
                "pf_trader_attention_packet_once.py",
                "--symbol",
                sym,
                "--pretty",
                "--compact",
            ],
            True,
        ),
    ]

    errors: list[str] = []
    final_stdout = ""

    for name, command, is_final in steps:
        try:
            result = _run_step(
                name,
                command,
                cwd=core,
                required=not continue_on_error,
                echo=verbose and not is_final,
            )
        except SystemExit:
            raise
        except Exception as exc:
            errors.append(f"{name}:{exc}")
            if not continue_on_error:
                raise SystemExit(1)
            continue

        if not result.ok:
            errors.append(f"{name}:returncode={result.returncode}")

        if is_final:
            final_stdout = result.stdout

    final_text = _compact_tail(final_stdout)
    if final_echo:
        if final_text:
            print(final_text)
        else:
            packet = _packet_txt_path(core, sym)
            if packet.exists():
                print(packet.read_text(encoding="utf-8").strip())
            else:
                print(f"{sym} | PACKET_MISSING | trader_attention_packet.txt not found")

    if errors:
        print(f"[STACK_WARN] {sym} errors={errors}", file=sys.stderr)
        return 1, final_stdout

    return 0, final_stdout


def parse_symbols(raw: str | None, fallback_symbol: str) -> list[str]:
    if raw:
        symbols = [part.strip().upper() for part in raw.split(",") if part.strip()]
    else:
        symbols = [fallback_symbol.strip().upper()]
    seen = set()
    out = []
    for sym in symbols:
        if sym and sym not in seen:
            out.append(sym)
            seen.add(sym)
    return out or ["GBPUSD"]


def run_multi(
    *,
    symbols: list[str],
    lookback_minutes: int,
    core: Path,
    continue_on_error: bool,
    verbose: bool,
    details: bool,
    table: bool,
) -> int:
    statuses: list[int] = []
    rows: list[str] = []

    for sym in symbols:
        if details and not table:
            print(f"--- {sym} ---")
        rc, stdout = run_stack_single(
            symbol=sym,
            lookback_minutes=lookback_minutes,
            core=core,
            continue_on_error=continue_on_error or len(symbols) > 1,
            verbose=verbose and not table,
            final_echo=details and not table,
        )
        statuses.append(rc)
        rows.append(_one_line_from_packet(core, sym, stdout))

    if table:
        _print_table([_table_row(core, sym) for sym in symbols])
    elif not details:
        for row in rows:
            print(row)

    wake_count = sum(1 for row in rows if "WAKE" in row)
    watch_count = sum(1 for row in rows if "WATCH" in row)
    observe_count = sum(1 for row in rows if "OBSERVE" in row)
    print(f"SUMMARY | symbols={len(rows)} wake={wake_count} watch={watch_count} observe={observe_count}")

    return 0 if all(code == 0 for code in statuses) else 1


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _clear_screen(enabled: bool) -> None:
    if not enabled:
        return
    # Simple ANSI clear. Works in modern Windows terminals; harmless if unsupported.
    print("\033[2J\033[H", end="")


def run_watch_loop(
    *,
    symbols: list[str],
    lookback_minutes: int,
    core: Path,
    interval: int,
    continue_on_error: bool,
    verbose: bool,
    details: bool,
    table: bool,
    clear: bool,
    max_cycles: int | None,
) -> int:
    cycle = 0
    last_rc = 0
    interval = max(1, int(interval))

    try:
        while True:
            cycle += 1
            _clear_screen(clear)
            print(f"POWERFLOW WATCH LOOP | cycle={cycle} | { _utc_stamp() } | interval={interval}s")
            print(f"symbols={','.join(symbols)}")
            print()

            last_rc = run_multi(
                symbols=symbols,
                lookback_minutes=lookback_minutes,
                core=core,
                continue_on_error=True if continue_on_error else True,
                verbose=verbose,
                details=details,
                table=table,
            )

            if max_cycles is not None and cycle >= max_cycles:
                return last_rc

            print()
            print("Ctrl+C to stop.")
            time.sleep(interval)

    except KeyboardInterrupt:
        print()
        print(f"POWERFLOW WATCH LOOP STOPPED | cycles={cycle}")
        return last_rc


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PowerFlow V7.6 trader perception stack once.")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--symbols", default=None, help="CSV symbols, e.g. GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--lookback-minutes", type=int, default=240)
    parser.add_argument("--core", default=None, help="Core directory. Defaults to this script's directory.")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--verbose", action="store_true", help="Print intermediate reader outputs.")
    parser.add_argument("--details", action="store_true", help="In multi-symbol mode, print full compact packet per symbol.")
    parser.add_argument("--table", action="store_true", help="In multi-symbol mode, print a scanner table.")
    parser.add_argument("--watch-loop", action="store_true", help="Refresh repeatedly until Ctrl+C.")
    parser.add_argument("--interval", type=int, default=20, help="Watch loop refresh interval in seconds.")
    parser.add_argument("--clear", action="store_true", help="Clear terminal between watch-loop refreshes.")
    parser.add_argument("--max-cycles", type=int, default=None, help="Optional max cycles for watch loop testing.")
    args = parser.parse_args(list(argv) if argv is not None else None)

    core = Path(args.core).resolve() if args.core else Path(__file__).resolve().parent
    symbols = parse_symbols(args.symbols, args.symbol)

    if args.watch_loop:
        return run_watch_loop(
            symbols=symbols,
            lookback_minutes=args.lookback_minutes,
            core=core,
            interval=args.interval,
            continue_on_error=args.continue_on_error,
            verbose=args.verbose,
            details=args.details,
            table=args.table or bool(args.symbols),
            clear=args.clear,
            max_cycles=args.max_cycles,
        )

    if args.symbols:
        return run_multi(
            symbols=symbols,
            lookback_minutes=args.lookback_minutes,
            core=core,
            continue_on_error=args.continue_on_error,
            verbose=args.verbose,
            details=args.details,
            table=args.table,
        )

    rc, _ = run_stack_single(
        symbol=symbols[0],
        lookback_minutes=args.lookback_minutes,
        core=core,
        continue_on_error=args.continue_on_error,
        verbose=args.verbose,
        final_echo=True,
    )
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
