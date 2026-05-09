# -*- coding: utf-8 -*-
"""
CLI runner for PowerFlow V6 temporal_node_state.json.

Example:
    python run_temporal_node_state_once.py --db powerflow.db --symbol GBPUSD --recent-minutes 180 --out output/temporal_node_state.json --pretty
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_temporal_node_state import build_temporal_node_state, write_temporal_node_state


def _parse_timeframes(value: str) -> list[int]:
    out: list[int] = []
    for part in value.split(","):
        part = part.strip().upper()
        if not part:
            continue
        if part.startswith("M") and part[1:].isdigit():
            out.append(int(part[1:]))
        elif part.startswith("H") and part[1:].isdigit():
            out.append(int(part[1:]) * 60)
        elif part.isdigit():
            out.append(int(part))
        else:
            raise argparse.ArgumentTypeError(f"Invalid timeframe: {part}")
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PowerFlow temporal_node_state.json")
    parser.add_argument("--db", default="powerflow.db", help="SQLite DB path")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbol, e.g. GBPUSD")
    parser.add_argument("--recent-minutes", type=int, default=180, help="Recent window in minutes")
    parser.add_argument("--timeframes", type=_parse_timeframes, default=_parse_timeframes("1,5,15,30,60"))
    parser.add_argument("--telegram-mode", default="SCALPING", choices=["OFF", "WATCH", "SCALPING", "HOT_ONLY"])
    parser.add_argument("--out", default="output/temporal_node_state.json", help="Output JSON path")
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--min-score", type=float, default=3.0)
    parser.add_argument("--visual-htf-story", default="unknown", choices=["unknown", "confirmed", "rejected"])
    parser.add_argument("--no-extended", action="store_true", help="Disable force_snapshots_v2 extended layer")
    parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args()

    state = build_temporal_node_state(
        db_path=args.db,
        symbol=args.symbol,
        recent_minutes=args.recent_minutes,
        timeframes=args.timeframes,
        telegram_mode=args.telegram_mode,
        max_rows=args.max_rows,
        min_score=args.min_score,
        visual_htf_story=args.visual_htf_story,
        include_extended=not args.no_extended,
    )

    write_temporal_node_state(state, args.out, pretty=args.pretty)

    summary = state.get("node_summary", {})
    db_vision = state.get("db_vision", {})
    print("TEMPORAL_NODE_STATE_OK")
    print(f"out={Path(args.out)}")
    print(f"db_status={db_vision.get('status')}")
    print(f"table={db_vision.get('table')}")
    print(f"rows_loaded={db_vision.get('rows_loaded')}")
    print(f"data_age_minutes={db_vision.get('data_age_minutes')}")
    print(f"freshness_gate={db_vision.get('freshness_gate')}")
    print(f"telegram_live_allowed={db_vision.get('telegram_live_allowed')}")
    print(f"active_count={summary.get('active_count')}")
    print(f"highest_level={summary.get('highest_level')}")
    print(f"best_interest={summary.get('best_interest')}")
    print(f"dominant_direction={summary.get('dominant_direction')}")
    print(f"structure_label={summary.get('structure_label')}")
    print(f"fractal_state={summary.get('fractal_state')}")
    print(f"extended_micro_window={summary.get('extended_micro_window')}")

    if db_vision.get("notes"):
        print("notes=" + json.dumps(db_vision.get("notes"), ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
