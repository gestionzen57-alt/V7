# run_temporal_density_once.py — PowerFlow V7 — B4 Runner
# Usage : python run_temporal_density_once.py --db powerflow.db --pretty

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

from pf_temporal_density import (
    compute_temporal_density_multi,
    format_density_summary,
)

CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]
DEFAULT_TFS = [1, 5, 15]


def main():
    p = argparse.ArgumentParser(description="PowerFlow V7 — B4 Temporal Density")
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--tfs", default="1,5,15")
    p.add_argument("--bars", type=int, default=30)
    p.add_argument("--lookback", type=int, default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()

    tfs = [int(x) for x in args.tfs.split(",")]

    results = compute_temporal_density_multi(
        db_path=args.db,
        currencies=CURRENCIES,
        timeframes=tfs,
        bars=args.bars,
        lookback_min=args.lookback,
    )

    summary = format_density_summary(results)

    if args.summary:
        print(f"\n=== TEMPORAL DENSITY B4 ===")
        print(f"COMPRESSING ({summary['compression_count']}) : {summary['compressing']}")
        print(f"EXPANDING   : {summary['expanding']}")
        print(f"STABLE      : {summary['stable']}")
        print(f"NOISY       : {summary['noisy']}")
        if summary['compression_alert']:
            print(f"⚠️  COMPRESSION ALERT : {summary['compression_count']}+ devises comprimées")

    indent = 2 if args.pretty else None
    out_json = json.dumps(summary, indent=indent, ensure_ascii=False)

    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(out_json, encoding="utf-8")
        print(f"✅ Written: {args.out}")
    else:
        print(out_json)


if __name__ == "__main__":
    main()
