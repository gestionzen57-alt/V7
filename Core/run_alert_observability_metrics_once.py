#!/usr/bin/env python3
"""
Runner — PowerFlow V7.2 Alert Observability Metrics

Produces:
- output/alert_metrics.json
- output/alert_metrics.md

Non-blocking. Metrics only. No filtering.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from pf_alert_observability_metrics import compute_alert_observability, write_markdown_report


def candidate_queue_paths() -> list[Path]:
    return [
        Path("output") / "behavioral_alert_queue.json",
        Path("Core") / "output" / "behavioral_alert_queue.json",
        Path("behavioral_alert_queue.json"),
        Path("Core") / "behavioral_alert_queue.json",
    ]


def resolve_queue_path(raw: Optional[str]) -> Path:
    if raw:
        return Path(raw)
    for path in candidate_queue_paths():
        if path.exists():
            return path
    return candidate_queue_paths()[0]


def build_self_test_queue(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = [
        {
            "timestamp": "2026-05-10T09:00:00Z",
            "alert_type": "FIRST_DETACHMENT_MICRO",
            "level": "HOT",
            "maturity": "BIRTH",
            "symbol": "GBPUSD",
            "regime_context": {"regime": "COMPRESSION"},
            "session_context": {"session": "LONDON"},
            "technical_risks": ["EARLY_MATURITY", "M1_NOISE_POSSIBLE"],
        },
        {
            "timestamp": "2026-05-10T09:03:00Z",
            "alert_type": "FIRST_DETACHMENT_MICRO",
            "level": "WATCH",
            "maturity": "EARLY",
            "symbol": "GBPUSD",
            "regime_context": {"regime": "COMPRESSION"},
            "session_context": {"session": "LONDON"},
            "technical_risks": ["RELAY_ABSENT"],
        },
        {
            "timestamp": "2026-05-10T09:05:00Z",
            "alert_type": "EIE_LEADER_CONFIRMED",
            "level": "HOT",
            "maturity": "CANDIDATE",
            "symbol": "GBPUSD",
            "regime_context": {"regime": "COMPRESSION"},
            "session_context": {"session": "LONDON"},
            "technical_risks": [],
        },
    ]
    path.write_text(json.dumps(sample, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow alert observability metrics")
    parser.add_argument("--queue", default=None, help="Path to behavioral_alert_queue.json")
    parser.add_argument("--window-minutes", type=int, default=180)
    parser.add_argument("--out-json", default=str(Path("output") / "alert_metrics.json"))
    parser.add_argument("--out-md", default=str(Path("output") / "alert_metrics.md"))
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--self-test", action="store_true", help="Use a synthetic sample queue")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    queue_path = resolve_queue_path(args.queue)
    if args.self_test:
        queue_path = Path("output") / "alert_observability_selftest_queue.json"
        build_self_test_queue(queue_path)

    metrics = compute_alert_observability(
        queue_path=queue_path,
        window_minutes=args.window_minutes,
    )

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    out_json.write_text(json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown_report(metrics, out_md)

    if args.pretty:
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(metrics, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
