"""
PowerFlow V6 - run_zone_evolution_report.py
CLI Windows/Linux pour lire le film de zone depuis powerflow.db.

Exemple Windows:
    python run_zone_evolution_report.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --top 20

Exporter dans un rapport:
    python run_zone_evolution_report.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --top 30 --out zone_evolution_report.txt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from pf_zone_evolution_reader import build_evolution_report


def parse_csv_ints(text: Optional[str]) -> Optional[List[int]]:
    if not text:
        return None
    out: List[int] = []
    for part in text.split(','):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out or None


def parse_csv_strs(text: Optional[str]) -> Optional[List[str]]:
    if not text:
        return None
    out = [x.strip().upper() for x in text.split(',') if x.strip()]
    return out or None


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow zone evolution report - film de zone")
    parser.add_argument("--db", default="powerflow.db", help="Chemin vers powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbole, ex: GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15,30,60", help="Liste TF, ex: 1,5,15,30,60")
    parser.add_argument("--currencies", default=None, help="Liste devises, ex: GBP,EUR,JPY")
    parser.add_argument("--since", default=None, help="Timestamp min source_created_at")
    parser.add_argument("--until", default=None, help="Timestamp max source_created_at")
    parser.add_argument("--top", type=int, default=20, help="Nombre de sequences/transitions a afficher")
    parser.add_argument("--out", default=None, help="Fichier de sortie optionnel .txt/.md")
    args = parser.parse_args(argv)

    db_path = Path(args.db)
    if not db_path.exists():
        print(f"ERROR: DB introuvable: {db_path}", file=sys.stderr)
        return 2

    try:
        report = build_evolution_report(
            db_path=str(db_path),
            symbol=args.symbol,
            timeframes=parse_csv_ints(args.timeframes),
            currencies=parse_csv_strs(args.currencies),
            since=args.since,
            until=args.until,
            top=args.top,
        )
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(report)

    if args.out:
        out_path = Path(args.out)
        out_path.write_text(report + "\n", encoding="utf-8")
        print(f"\nOK wrote report: {out_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
