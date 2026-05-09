# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_db_freshness_probe import build_db_freshness_state, write_db_freshness_state


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow DB freshness probe")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--out", default="output/db_freshness_state.json")
    parser.add_argument("--stale-minutes", type=int, default=5)
    parser.add_argument("--tactical-stale-minutes", type=int, default=180)
    parser.add_argument("--no-process-probe", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    state = build_db_freshness_state(
        db_path=args.db,
        symbol=args.symbol,
        stale_minutes=args.stale_minutes,
        tactical_stale_minutes=args.tactical_stale_minutes,
        include_process_probe=not args.no_process_probe,
    )
    write_db_freshness_state(state, args.out, pretty=args.pretty)

    verdict = state.get("verdict", {})
    print("DB_FRESHNESS_PROBE_OK")
    print(f"out={Path(args.out)}")
    print(f"status={verdict.get('status')}")
    print(f"latest_timestamp={verdict.get('latest_timestamp')}")
    print(f"data_age_minutes={verdict.get('data_age_minutes')}")
    print(f"probable_cause={verdict.get('probable_cause')}")
    print("next_action=" + json.dumps(verdict.get("next_action", []), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
