#!/usr/bin/env python3
"""
T009 Battlefield Flux standalone CLI.

Usage examples:
  python Core/run_battlefield_flux_once.py --symbol GBPUSD --lookback-min 30
  python run_battlefield_flux_once.py --symbol GBPUSD --lookback-min 30
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

try:  # Repo-root execution
    from Core.config_t009_flags import FLAGS  # type: ignore
    from Core.pf_battlefield_flux import BattlefieldFlux  # type: ignore
except Exception:  # Core-folder execution
    from config_t009_flags import FLAGS  # type: ignore
    from pf_battlefield_flux import BattlefieldFlux  # type: ignore


def _json_default(value: Any) -> str:
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser(description="T009 Battlefield Flux - standalone tick-cluster perception")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbol to analyze, default GBPUSD")
    parser.add_argument("--lookback-min", type=int, default=30, help="Lookback window in minutes")
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--tick-db", default="tick_archive.db", help="Primary tick archive DB")
    parser.add_argument("--fallback-db", default="powerflow.db", help="Fallback PowerFlow DB")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Phase 1A is dry-run only")
    args = parser.parse_args()

    if args.lookback_min > FLAGS.MAX_LOOKBACK_MIN:
        raise ValueError(f"lookback-min={args.lookback_min} exceeds POWERFLOW_T009_MAX_LOOKBACK_MIN={FLAGS.MAX_LOOKBACK_MIN}")

    if FLAGS.ENABLE_TELEGRAM:
        raise ValueError("POWERFLOW_T009_ENABLE_TELEGRAM must remain 0 during Phase 1A")

    if FLAGS.ENABLE_ENGINE_INTEGRATION:
        raise ValueError("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION must remain 0 during Phase 1A")

    print("T009 Battlefield Flux")
    print(f"  Symbol: {args.symbol}")
    print(f"  Lookback: {args.lookback_min} min")
    print(f"  Dry-run: {args.dry_run or FLAGS.DRY_RUN}")
    print(f"  Tick DB: {args.tick_db}")
    print(f"  Fallback DB: {args.fallback_db}")

    module = BattlefieldFlux(db_path=args.tick_db, fallback_db=args.fallback_db)
    state: Dict[str, Any] = module.compute_state(symbol=args.symbol, lookback_min=args.lookback_min)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    state_file = output_dir / "battlefield_flux_state.json"
    events_file = output_dir / "battlefield_flux_events.json"

    with state_file.open("w", encoding="utf-8") as handle:
        json.dump(state, handle, indent=2, ensure_ascii=False, default=_json_default)

    with events_file.open("w", encoding="utf-8") as handle:
        json.dump(state.get("events", []), handle, indent=2, ensure_ascii=False, default=_json_default)

    print("Done")
    print(f"  Source used: {state.get('source_used')}")
    print(f"  Ticks: {state.get('tick_count')}")
    print(f"  Buckets: {state.get('bucket_count')}")
    print(f"  Events: {state.get('event_count')}")
    print(f"  State: {state_file}")
    print(f"  Events: {events_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
