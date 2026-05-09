#!/usr/bin/env python3
"""
run_temporal_density.py

Runner separe pour pf_temporal_density.py.
Lit powerflow.db en read-only, scanne les 7 devises PowerFlow,
affiche le tableau et peut sauvegarder la sortie en .txt via --out.
"""

from __future__ import annotations

import argparse

from pf_temporal_density import format_temporal_density_table, scan_all_currencies


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow V6 - Runner Temporal Density")
    parser.add_argument("--db", required=True, help="Chemin vers powerflow.db")
    parser.add_argument("--symbol", required=True, help="Symbole, ex: GBPUSD")
    parser.add_argument("--tf", required=True, type=int, help="Timeframe entier, ex: 5 pour M5")
    parser.add_argument("--window", default=20, type=int, help="Nombre de barres a analyser")
    parser.add_argument("--out", help="Chemin optionnel pour sauvegarder la table en .txt")
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    results = scan_all_currencies(
        db_path=args.db,
        symbol=args.symbol,
        timeframe=args.tf,
        window=args.window,
    )
    table = format_temporal_density_table(results)
    print(table)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            handle.write(table)
            handle.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
