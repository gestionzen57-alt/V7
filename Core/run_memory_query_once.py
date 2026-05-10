"""Runner PowerFlow V7.2 — B6 Memory Engine."""
from __future__ import annotations

import argparse
import json

from pf_memory_engine import MemoryEngine, build_self_test_alerts, write_json

DEFAULT_OUTPUT = "output/memory_query_results.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow B6 behavioral memory query runner")
    p.add_argument("--queue", default=None, help="Path to behavioral_alert_queue.json")
    p.add_argument("--limit", type=int, default=5, help="Number of latest alerts to query")
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        alerts = build_self_test_alerts()
        engine = MemoryEngine(alerts=alerts)
        results = engine.query_last(limit=1)
        mode = "SELF_TEST_SAMPLE_NOT_LIVE_MARKET"
    else:
        engine = MemoryEngine(queue_path=args.queue)
        results = engine.query_last(limit=args.limit)
        mode = "LIVE_QUEUE_OR_EMPTY"

    payload = {
        "valid": True,
        "method": "behavioral_pattern_memory",
        "version": "MemoryEngineV1PatternIndexing",
        "mode": mode,
        "queue_size": len(engine.queue),
        "results": results,
    }
    write_json(args.output, payload)
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
