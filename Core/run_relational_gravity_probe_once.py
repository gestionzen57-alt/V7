"""
run_relational_gravity_probe_once.py
PowerFlow V6 — Runner unique pour Relational Gravity Probe V0.1

Usage:
    python run_relational_gravity_probe_once.py \
        --db powerflow.db \
        --symbol GBPUSD \
        --timeframe 1 \
        --bars 30 \
        --out output/relational_gravity_m1.json \
        --pretty

Options:
    --db          Chemin vers powerflow.db
    --symbol      Symbole (ex: GBPUSD)
    --timeframe   Timeframe en minutes (1, 5, 15, 30, ...)
    --bars        Nombre de barres à analyser (ex: 30)
    --currencies  Devises à analyser, séparées par virgule (ex: GBP,USD,EUR,JPY)
                  Si absent : toutes les 7 devises
    --out         Chemin de sortie JSON (ex: output/relational_gravity_m1.json)
    --pretty      Indentation JSON lisible
    --summary     Affiche un résumé console après execution
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

# Local import
from pf_relational_gravity_probe import (
    run_relational_gravity_probe,
    result_to_dict,
    ALL_CURRENCIES,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PowerFlow V6 — Relational Gravity Probe V0.1"
    )
    parser.add_argument("--db", required=True, help="Path to powerflow.db")
    parser.add_argument("--symbol", required=True, help="Symbol (e.g. GBPUSD)")
    parser.add_argument(
        "--timeframe", required=True, type=int,
        help="Timeframe in minutes (1, 5, 15, 30)"
    )
    parser.add_argument(
        "--bars", required=False, type=int, default=30,
        help="Number of bars to analyze (default: 30)"
    )
    parser.add_argument(
        "--currencies", required=False, default=None,
        help="Currencies to include, comma-separated (e.g. GBP,USD,EUR,JPY). Default: all 7"
    )
    parser.add_argument(
        "--out", required=False, default=None,
        help="Output JSON file path (e.g. output/relational_gravity_m1.json)"
    )
    parser.add_argument(
        "--pretty", action="store_true",
        help="Pretty-print JSON output"
    )
    parser.add_argument(
        "--summary", action="store_true",
        help="Print a brief summary to console"
    )
    return parser.parse_args()


def print_summary(result_dict: dict) -> None:
    print("\n" + "=" * 60)
    print(f"  RELATIONAL GRAVITY PROBE — {result_dict['symbol']} TF{result_dict['timeframe']}")
    print("=" * 60)
    print(f"  Status       : {result_dict['status']}")
    print(f"  Bars         : {result_dict['window']['bars']}")
    print(f"  State        : {result_dict['primary_state']}")
    print(f"  Direction    : {result_dict['direction']}")
    print(f"  Group        : {result_dict['group']}")
    print(f"  Gap Mode     : {result_dict['gap_mode']}  (slope: {result_dict['gap_slope']})")
    print(f"  Angle Spread : {result_dict['angle_spread_deg']}°")
    print(f"  Leader       : {result_dict['leader']}")
    print(f"  Followers    : {result_dict['followers']}")
    print(f"  Antagonist   : {result_dict['antagonist']}")
    print(f"  Score        : {result_dict['score']}  [{result_dict['confidence']}]")
    print(f"  Signatures   : {result_dict['lab_signatures']}")
    print(f"  Interpretation: {result_dict['interpretation']}")
    if result_dict.get("errors"):
        print(f"  Errors       : {result_dict['errors']}")
    print("=" * 60 + "\n")


def main() -> None:
    args = parse_args()

    # Validate DB path
    db_path = Path(args.db)
    if not db_path.exists():
        print(f"[ERROR] DB not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    # Parse currencies
    if args.currencies:
        currencies = [c.strip().upper() for c in args.currencies.split(",")]
    else:
        currencies = None  # Will use ALL_CURRENCIES inside probe

    # Run probe
    print(
        f"[RUN] Relational Gravity Probe | {args.symbol} TF{args.timeframe} | "
        f"{args.bars} bars | {datetime.now().strftime('%H:%M:%S')}"
    )

    result = run_relational_gravity_probe(
        db_path=str(db_path),
        symbol=args.symbol,
        timeframe=args.timeframe,
        bars=args.bars,
        currencies=currencies,
    )

    result_dict = result_to_dict(result)

    # Output JSON
    indent = 2 if args.pretty else None
    json_str = json.dumps(result_dict, indent=indent, ensure_ascii=False)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json_str, encoding="utf-8")
        print(f"[OK] Output written: {out_path}")
    else:
        print(json_str)

    if args.summary:
        print_summary(result_dict)

    # Exit code based on status
    if result.status == "NO_DATA":
        sys.exit(2)
    elif result.status == "PARTIAL":
        sys.exit(0)  # Not an error — partial is valid
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
