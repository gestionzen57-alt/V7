#!/usr/bin/env python3
"""
Runner — PowerFlow V7.2 Scene Memory Enrichment

Usage:
  python Core/run_scene_memory_enrichment_once.py --pretty
  python Core/run_scene_memory_enrichment_once.py --self-test --pretty
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

from pf_memory_scene_enrichment import run_enrichment


def candidate_queue_paths() -> list[Path]:
    return [
        Path("output") / "behavioral_alert_queue.json",
        Path("Core") / "output" / "behavioral_alert_queue.json",
        Path("output") / "alert_observability_selftest_queue.json",
        Path("behavioral_alert_queue.json"),
    ]


def resolve_queue(raw: Optional[str]) -> Path:
    if raw:
        return Path(raw)
    for p in candidate_queue_paths():
        if p.exists():
            return p
    return candidate_queue_paths()[0]


def build_self_test_queue(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    sample = [
        {
            "timestamp": "2026-05-10T09:00:00Z",
            "alert_type": "FIRST_DETACHMENT_MICRO",
            "symbol": "GBPUSD",
            "regime_context": {"regime": "COMPRESSION"},
            "session_context": {"session": "LONDON"},
            "EIE_state": "ELASTIC_IN_EXTREME",
            "B4_state": "CYCLE_COMPRESSING",
            "B5_direction": "DIVERGENT_EXTREME",
            "B3_noise_ratio": 0.08,
            "B7_state": "LAGGED",
            "technical_risks": ["EARLY_MATURITY"],
        },
        {
            "timestamp": "2026-05-10T09:10:00Z",
            "alert_type": "ZONE_BREATH",
            "symbol": "GBPUSD",
            "regime_context": {"regime": "RANGE"},
            "session_context": {"session": "ASIAN"},
            "EIE_state": "ABSENT",
            "B4_state": "CYCLE_COMPRESSING",
            "B5_direction": "NEUTRAL",
            "B3_noise_ratio": 0.42,
            "B7_state": "SILENT",
            "technical_risks": [],
        },
        {
            "timestamp": "2026-05-10T09:20:00Z",
            "alert_type": "REPULSION_CLEAN",
            "symbol": "GBPUSD",
            "regime_context": {"regime": "COMPRESSION"},
            "session_context": {"session": "LONDON"},
            "EIE_state": "ELASTIC_IN_EXTREME",
            "B4_state": "CYCLE_EXPANDING",
            "B5_direction": "SYNCHRO",
            "B3_noise_ratio": 0.06,
            "B7_state": "RESONANT",
            "outcome": "REJECTION_CONFIRMED",
            "bars_to_move": 8,
            "technical_risks": [],
        },
    ]
    path.write_text(json.dumps(sample, indent=2), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow scene memory enrichment")
    parser.add_argument("--queue", default=None)
    parser.add_argument("--out-queue", default=str(Path("output") / "behavioral_alert_queue_scene_enriched.json"))
    parser.add_argument("--out-report-json", default=str(Path("output") / "scene_memory_enrichment_report.json"))
    parser.add_argument("--out-report-md", default=str(Path("output") / "scene_memory_enrichment_report.md"))
    parser.add_argument("--threshold", type=float, default=0.35)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    queue = resolve_queue(args.queue)

    if args.self_test:
        queue = Path("output") / "scene_memory_enrichment_selftest_queue.json"
        build_self_test_queue(queue)

    report = run_enrichment(
        queue_path=queue,
        out_queue=Path(args.out_queue),
        out_report_json=Path(args.out_report_json),
        out_report_md=Path(args.out_report_md),
        threshold=args.threshold,
    )

    if args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(report, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
