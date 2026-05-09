#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
run_alert_entropy_once.py

PowerFlow V7.1 — Alert Entropy Runner.

Role:
    Read behavioral_alert_queue.json, compute alert saturation metrics,
    and output a JSON report.

Doctrine:
    - No DB write.
    - No cockpit dependency.
    - Queue-in / JSON-out.
    - Alert fatigue is a technical metric, never an alert censor.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pf_alert_entropy import compute_alert_entropy, summarize_entropy_state


DEFAULT_INPUT = Path("output") / "behavioral_alert_queue.json"
DEFAULT_OUTPUT = Path("output") / "alert_entropy_report.json"


@dataclass(frozen=True)
class RunnerConfig:
    input_path: Path
    output_path: Optional[Path]
    window_minutes: int
    reference_time_utc: Optional[str]
    burst_threshold_count: int
    duplicate_ratio_threshold: float
    pretty: bool


def load_json_file(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json_file(path: Path, payload: Any, pretty: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as handle:
        if pretty:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
        else:
            json.dump(payload, handle, separators=(",", ":"), ensure_ascii=False)


def extract_alerts(payload: Any) -> List[Any]:
    """
    Accept common queue shapes:
        - list
        - {"alerts": list}
        - {"items": list}
        - {"queue": list}
        - {"behavioral_alert_queue": list}
        - {"payload": nested_queue}
    """
    if isinstance(payload, list):
        return payload

    if isinstance(payload, dict):
        for key in ("alerts", "items", "queue", "behavioral_alert_queue"):
            value = payload.get(key)
            if isinstance(value, list):
                return value

        if "payload" in payload:
            return extract_alerts(payload["payload"])

    raise ValueError(
        "Unsupported JSON shape. Expected list or object containing alerts/items/queue/behavioral_alert_queue."
    )


def build_report(
    metrics: Dict[str, Any],
    config: RunnerConfig,
    alerts_loaded: int,
) -> Dict[str, Any]:
    return {
        "runner": "run_alert_entropy_once.py",
        "status": "OK",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "input": str(config.input_path),
        "output": str(config.output_path) if config.output_path else None,
        "alerts_loaded": alerts_loaded,
        "entropy_state": summarize_entropy_state(metrics),
        "metrics": metrics,
    }


def run(config: RunnerConfig) -> Dict[str, Any]:
    payload = load_json_file(config.input_path)
    alerts = extract_alerts(payload)

    metrics = compute_alert_entropy(
        alerts=alerts,
        window_minutes=config.window_minutes,
        reference_time_utc=config.reference_time_utc,
        burst_threshold_count=config.burst_threshold_count,
        duplicate_ratio_threshold=config.duplicate_ratio_threshold,
    )

    report = build_report(
        metrics=metrics,
        config=config,
        alerts_loaded=len(alerts),
    )

    if config.output_path is not None:
        save_json_file(config.output_path, report, pretty=config.pretty)

    return report


def parse_args() -> RunnerConfig:
    parser = argparse.ArgumentParser(
        description="Compute PowerFlow alert entropy metrics from behavioral_alert_queue.json."
    )

    parser.add_argument(
        "--input",
        dest="input_path",
        default=str(DEFAULT_INPUT),
        help=f"Input behavioral queue JSON path. Default: {DEFAULT_INPUT}",
    )

    parser.add_argument(
        "--output",
        dest="output_path",
        default=str(DEFAULT_OUTPUT),
        help=f"Output report JSON path. Default: {DEFAULT_OUTPUT}",
    )

    parser.add_argument(
        "--stdout-only",
        action="store_true",
        help="Do not write report file. Print JSON report only.",
    )

    parser.add_argument(
        "--window-minutes",
        type=int,
        default=5,
        help="Rolling window size in minutes. Default: 5",
    )

    parser.add_argument(
        "--reference-time-utc",
        default=None,
        help="Optional ISO UTC reference time. Default: latest alert timestamp.",
    )

    parser.add_argument(
        "--burst-threshold-count",
        type=int,
        default=3,
        help="Alert count threshold for burst detection. Default: 3",
    )

    parser.add_argument(
        "--duplicate-ratio-threshold",
        type=float,
        default=0.50,
        help="Duplication ratio threshold for saturation flag. Default: 0.50",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Write and print indented JSON.",
    )

    parser.add_argument(
        "--compact",
        action="store_true",
        help="Write and print compact JSON. Overrides --pretty.",
    )

    args = parser.parse_args()

    if args.window_minutes <= 0:
        raise ValueError("--window-minutes must be > 0")

    if args.burst_threshold_count <= 0:
        raise ValueError("--burst-threshold-count must be > 0")

    if not 0.0 <= args.duplicate_ratio_threshold <= 1.0:
        raise ValueError("--duplicate-ratio-threshold must be between 0.0 and 1.0")

    pretty = bool(args.pretty and not args.compact)

    return RunnerConfig(
        input_path=Path(args.input_path),
        output_path=None if args.stdout_only else Path(args.output_path),
        window_minutes=args.window_minutes,
        reference_time_utc=args.reference_time_utc,
        burst_threshold_count=args.burst_threshold_count,
        duplicate_ratio_threshold=args.duplicate_ratio_threshold,
        pretty=pretty,
    )


def main() -> int:
    config: Optional[RunnerConfig] = None

    try:
        config = parse_args()
        report = run(config)
    except Exception as exc:
        error_payload = {
            "runner": "run_alert_entropy_once.py",
            "status": "ERROR",
            "error_type": type(exc).__name__,
            "error": str(exc),
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(error_payload, indent=2, ensure_ascii=False))
        return 1

    if config.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, separators=(",", ":"), ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
