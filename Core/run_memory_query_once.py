"""run_memory_query_once.py — Query historical pattern context.

Memory V1 runner.
- Live mode: reads behavioral_alert_queue.json if it exists.
- Weekend/self-test mode: validates the engine without requiring open FX markets.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from pf_memory_engine import MemoryEngine

RUNNER_VERSION = "MemoryRunnerV1.1-weekend-pathfix"


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _resolve_output_path(engine: MemoryEngine, output_path: str | Path) -> Path:
    raw_path = Path(output_path)
    if raw_path.is_absolute():
        return raw_path

    # Prefer the same output folder as the loaded queue.
    if raw_path.parts and raw_path.parts[0].lower() == "output":
        if getattr(engine, "queue_exists", False) and engine.queue_path.parent.name.lower() == "output":
            return engine.queue_path.parent / raw_path.name
        return engine.project_root / raw_path

    return Path.cwd() / raw_path


def _sample_alerts() -> List[Dict[str, Any]]:
    """Small deterministic memory sample for weekend validation only."""
    base = {
        "alert_type": "FIRST_DETACHMENT_MICRO",
        "level": "HOT",
        "regime_context": {"regime": "COMPRESSION", "confidence": 0.82},
        "session_context": {"session": "LONDON", "session_phase": "IGNITION"},
        "EIE_state": "ELASTIC_IN_EXTREME",
        "B4_state": "CYCLE_COMPRESSING",
        "B5_direction": "DIVERGENT",
    }
    sample: List[Dict[str, Any]] = []
    outcomes = [
        ("RELEASE_CONFIRMED", 14),
        ("RELEASE_CONFIRMED", 12),
        ("RELEASE_CONFIRMED", 16),
        ("RELEASE_CONFIRMED", 15),
        ("RELEASE_CONFIRMED", 13),
        ("REJECTION", 8),
        ("REJECTION", 9),
    ]
    for idx, (outcome, bars) in enumerate(outcomes, start=1):
        row = dict(base)
        row["regime_context"] = dict(base["regime_context"])
        row["session_context"] = dict(base["session_context"])
        row["timestamp"] = f"2026-05-08T09:{idx:02d}:00Z"
        row["outcome"] = outcome
        row["bars_to_move"] = bars
        sample.append(row)

    variants = [
        ("CASCADE_BUILDING_ALERT", "COMPRESSION", "NY", "NEUTRAL", "CYCLE_EXPANDING", "SYNCHRO", "RELEASE_CONFIRMED", 6),
        ("EIE_LEADER_CONFIRMED", "TRANSITION", "OVERLAP", "ELASTIC_IN_EXTREME", "CYCLE_COMPRESSING", "DIVERGENT", "REJECTION", 10),
        ("FIRST_DETACHMENT_MICRO", "RANGE", "ASIAN", "NEUTRAL", "CYCLE_STABLE", "NEUTRAL", "UNKNOWN", 0),
        ("COUNTER_RELEASE_ATTEMPT", "TENDANCE", "LONDON", "LEAKING", "CYCLE_EXPANDING", "DIVERGENT", "RELEASE_CONFIRMED", 11),
        ("SEQUENCE_VELOCITY_HIGH", "COMPRESSION", "LONDON", "ELASTIC_IN_EXTREME", "CYCLE_COMPRESSING", "SYNCHRO", "RELEASE_CONFIRMED", 5),
    ]
    for idx, (alert_type, regime, session, eie, b4, b5, outcome, bars) in enumerate(variants, start=20):
        sample.append(
            {
                "alert_type": alert_type,
                "level": "WATCH",
                "timestamp": f"2026-05-08T10:{idx:02d}:00Z",
                "regime_context": {"regime": regime, "confidence": 0.71},
                "session_context": {"session": session, "session_phase": "MID_SESSION"},
                "EIE_state": eie,
                "B4_state": b4,
                "B5_direction": b5,
                "outcome": outcome,
                "bars_to_move": bars,
            }
        )
    return sample


def _write_self_test_queue(start_from: Path) -> Path:
    root = start_from.parent if start_from.name.lower() == "core" else start_from
    out_dir = root / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    queue_path = out_dir / "behavioral_alert_queue_MEMORY_SELF_TEST.json"
    queue_path.write_text(json.dumps(_sample_alerts(), indent=2, ensure_ascii=False), encoding="utf-8")
    return queue_path


def build_payload(engine: MemoryEngine, limit: int = 10, mode: str = "live") -> Dict[str, Any]:
    recent_alerts: List[Dict[str, Any]] = engine.queue[-limit:] if engine.queue else []
    results = engine.batch_query(recent_alerts)
    diagnostics = engine.diagnostics()
    diagnostics["runner_version"] = RUNNER_VERSION
    diagnostics["mode"] = mode

    technical_risks: List[str] = []
    if not diagnostics["queue_exists"]:
        technical_risks.append("QUEUE_FILE_NOT_FOUND")
    if diagnostics["queue_size"] == 0:
        technical_risks.append("NO_ALERTS_IN_QUEUE")
    if mode == "self_test":
        technical_risks.append("SELF_TEST_SAMPLE_NOT_LIVE_MARKET")

    return {
        "timestamp": _timestamp_now(),
        "total_queries": len(results),
        "total_alerts_in_queue": len(engine.queue),
        "memory_engine": diagnostics,
        "technical_risks": technical_risks,
        "results": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Query PowerFlow Memory V1 for recent behavioral patterns.")
    parser.add_argument("--queue", default="output/behavioral_alert_queue.json", help="Path to behavioral alert queue JSON")
    parser.add_argument("--output", default="output/memory_query_results.json", help="Path to output JSON")
    parser.add_argument("--limit", type=int, default=10, help="Number of recent alerts to query")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON to stdout")
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Use a generated sample queue for weekend/off-market validation without touching the live queue",
    )
    args = parser.parse_args()

    try:
        queue_arg = args.queue
        mode = "live"
        if args.self_test:
            queue_arg = str(_write_self_test_queue(Path(__file__).resolve().parent))
            mode = "self_test"

        engine = MemoryEngine(queue_arg)
        payload = build_payload(engine, limit=max(args.limit, 0), mode=mode)

        output_path = _resolve_output_path(engine, args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

        print(json.dumps(payload, indent=2, ensure_ascii=False))
    except Exception as exc:  # noqa: BLE001 - CLI boundary: emit clean stderr and non-zero code.
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
