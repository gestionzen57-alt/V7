"""
run_confluence_scan.py — PowerFlow V7  V2.0
Scan historique + API propre pour lab.py et film.py.

  python run_confluence_scan.py --date 2026-05-09 --summary
  python run_confluence_scan.py --history --currency GBP --limit 200
  python run_confluence_scan.py --summary --json
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pf_confluence_elastic import query_eie_history, query_eie_sessions_summary

DB_PATH_DEFAULT = Path("powerflow.db")


def cmd_summary(db_path, date_str, min_persist, zone_tf):
    result = query_eie_sessions_summary(
        db_path=db_path, date_str=date_str,
        zone_tf=zone_tf, min_persist=min_persist,
    )
    if not result:
        print(f"\n━━━ EIE SUMMARY — {date_str} — aucune donnée en DB ━━━\n")
        return {"date": date_str, "min_persist": min_persist, "eie_counts": {}, "total_eie": 0}

    print(f"\n━━━ EIE SUMMARY — {result['date']} — min_persist={result['min_persist']} ━━━")
    print(f"Total EIE persistants : {result['total_eie']}\n")
    counts = result["eie_counts"]
    max_count = max(counts.values()) if counts.values() else 1
    for currency, count in sorted(counts.items(), key=lambda x: -x[1]):
        bar = "█" * count + " " * (max(max_count, 1) - count)
        print(f"  {currency:3s}  {count:3d}x  {bar}")
    print()
    return result


def cmd_history(db_path, currency, limit):
    rows = query_eie_history(db_path=db_path, currency=currency, limit=limit)
    eie_rows = [r for r in rows if r["eie"]]
    print(f"\n━━━ EIE HISTORY — {currency} — {len(rows)} snapshots ━━━")
    print(f"EIE détectés : {len(eie_rows)} / {len(rows)}")
    for r in eie_rows[-20:]:
        print(f"  {r['timestamp']} | zone={r['zone_state']} z={r['zone_z']:+.2f} | elastic={r['elastic_label']}")
    print()
    return rows


# ── API pour lab.py / film.py ──────────────────────────────────────────────────
def get_eie_history_for_currency(db_path: Path, currency: str, limit: int = 200) -> list:
    return query_eie_history(db_path=db_path, currency=currency, limit=limit)


def get_eie_summary_for_date(db_path: Path, date_str: str = None, min_persist: int = 2, zone_tf: int = 15) -> dict:
    return query_eie_sessions_summary(db_path=db_path, date_str=date_str, zone_tf=zone_tf, min_persist=min_persist)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH_DEFAULT)
    parser.add_argument("--date", type=str, default=None)
    parser.add_argument("--min-persist", type=int, default=2)
    parser.add_argument("--zone-tf", type=int, default=15)
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--history", action="store_true")
    parser.add_argument("--currency", type=str, default=None)
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--json", action="store_true", dest="output_json")
    args = parser.parse_args()

    date_str = args.date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

    if args.history:
        if not args.currency:
            print("--history nécessite --currency")
            return
        rows = cmd_history(args.db, args.currency.upper(), args.limit)
        if args.output_json:
            print(json.dumps(rows, indent=2, ensure_ascii=False))
        return

    result = cmd_summary(args.db, date_str, args.min_persist, args.zone_tf)
    if args.output_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()