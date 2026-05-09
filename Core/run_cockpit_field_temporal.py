"""
PowerFlow V6 - run_cockpit_field_temporal.py
Version: V0.1

Mission:
  Tester le bloc TEMPORAL_PATTERNS avant fusion dans run_cockpit_field.py.

Usage:
  python run_cockpit_field_temporal.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15 --recent-minutes 180 --out cockpit_temporal_block.txt

Read-only.
"""

from __future__ import annotations

import argparse
from typing import List

from pf_temporal_patterns_cockpit import build_temporal_patterns_cockpit


def parse_int_list(value: str) -> List[int]:
    return [int(x.strip()) for x in str(value).split(",") if x.strip()]


def parse_currency_list(value: str) -> List[str]:
    return [x.strip().upper() for x in str(value).split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow cockpit temporal patterns block - read only")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15")
    parser.add_argument("--currencies", default="GBP,USD,EUR,JPY,CAD,CHF,AUD")
    parser.add_argument("--recent-minutes", type=int, default=180)
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--min-density", type=float, default=0.0)
    parser.add_argument("--density-percentile", type=float, default=85.0)
    parser.add_argument("--min-breathing-energy", type=float, default=3.0)
    parser.add_argument("--angle-tolerance", type=float, default=4.0)
    parser.add_argument("--field-gap-minutes", type=int, default=10)
    parser.add_argument("--max-lines", type=int, default=6)
    parser.add_argument("--limit-bars", type=int, default=0)
    parser.add_argument("--out", default="")
    args = parser.parse_args()

    result = build_temporal_patterns_cockpit(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=parse_int_list(args.timeframes),
        currencies=parse_currency_list(args.currencies),
        recent_minutes=args.recent_minutes,
        window=args.window,
        min_density=args.min_density,
        density_percentile=args.density_percentile,
        min_breathing_energy=args.min_breathing_energy,
        angle_tolerance=args.angle_tolerance,
        field_gap_minutes=args.field_gap_minutes,
        max_lines=args.max_lines,
        limit_bars=args.limit_bars,
    )

    text = "\n".join(result.lines)
    print(text)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\nOK wrote temporal cockpit block: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
