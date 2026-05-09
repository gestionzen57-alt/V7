# run_spearman_gravity_once.py — PowerFlow V7 — B5 Runner
# Usage : python run_spearman_gravity_once.py --db powerflow.db --pretty

from __future__ import annotations
import argparse
import json
from pathlib import Path

from pf_spearman_gravity import (
    compute_spearman_all_pairs,
    format_spearman_summary,
    CURRENCIES,
)


def main():
    p = argparse.ArgumentParser(description="PowerFlow V7 — B5 Spearman Gravity")
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--tfs", default="1,5,15")
    p.add_argument("--bars", type=int, default=30)
    p.add_argument("--out", default=None)
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()

    tfs = [int(x) for x in args.tfs.split(",")]

    results = compute_spearman_all_pairs(
        db_path=args.db,
        timeframes=tfs,
        bars=args.bars,
    )

    summary = format_spearman_summary(results)

    if args.summary:
        print(f"\n=== SPEARMAN GRAVITY B5 ===")
        print(f"SYNCHRO    ({summary['synchro_count']}) : {summary['synchro_pairs']}")
        print(f"DIVERGENT  ({summary['divergent_count']}) : {summary['divergent_pairs']}")
        print(f"TAIL EXTREME : {summary['tail_extreme']}")
        print(f"MIXED RÉSOLU ({summary['mixed_count']}) :")
        for m in summary['mixed_resolved']:
            print(f"  {m['pair']} avg_rho={m['avg_rho']}")

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
