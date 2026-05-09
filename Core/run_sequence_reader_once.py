#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - Run Sequence Reader Once V0.1

Usage:
    python run_sequence_reader_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00+00:00 --end 2026-05-04T10:15:00+00:00
    python run_sequence_reader_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T12:45:00+00:00 --end 2026-05-04T13:45:00+00:00 --json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_sequence_reader import scan_sequence


def parse_timeframes(value: str):
    out = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--timeframes", default="1,5,15")
    ap.add_argument("--min-delta", type=float, default=8.0)
    ap.add_argument("--price-lag-abs", type=float, default=0.00020)
    ap.add_argument("--price-pay-abs", type=float, default=0.00045)
    ap.add_argument("--limit", type=int, default=15)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"DB not found: {args.db}")

    result = scan_sequence(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        timeframes=parse_timeframes(args.timeframes),
        min_delta=args.min_delta,
        price_lag_abs=args.price_lag_abs,
        price_pay_abs=args.price_pay_abs,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print("PowerFlow Sequence Reader - V0.1")
    print("=" * 80)
    print(result["global_sentence"])
    print()
    print(f"DB       : {result['db']}")
    print(f"Symbol   : {result['symbol']}")
    print(f"Window   : {result['start']} -> {result['end']}")
    print(f"TF       : {','.join(str(x) for x in result['timeframes'])}")
    print(f"Events   : {result['event_count']}")
    print()

    print("TOP SEQUENCE EVENTS")
    print("-" * 80)

    for i, ev in enumerate(result["top_events"][: args.limit], 1):
        print(
            f"{i:02d}. {ev['start_time']} -> {ev['end_time']} | "
            f"TF={ev['timeframe']} | {ev['event_type']} | "
            f"score={ev['score']:.2f} | energy={ev['energy']:.1f}"
        )
        print(f"    {ev['cockpit_sentence']}")
        print(f"    UP   : {ev['up_deltas']}")
        print(f"    DOWN : {ev['down_deltas']}")
        print(f"    BID  : {ev['bid_start']} -> {ev['bid_end']} ({ev['bid_delta']})")
        print(f"    TAGS : {', '.join(ev['tags'])}")
        print()

    print("PER TIMEFRAME COVERAGE")
    print("-" * 80)
    for tf in result["per_timeframe"]:
        print(
            f"TF={tf['timeframe']} rows={tf['rows']} "
            f"{tf['first']} -> {tf['last']} events={len(tf['events'])}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
