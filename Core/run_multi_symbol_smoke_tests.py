"""
run_multi_symbol_smoke_tests.py
PowerFlow V7.1 — Schema and row-density smoke test for multi-symbol extension.

This runner does not mutate DB. It validates that each requested symbol maps to
existing force columns and has rows in force_snapshots per timeframe.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

try:
    from pf_symbol_mapper import DEFAULT_TABLE, get_table_columns, parse_symbols, resolve_symbol_mapping
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from pf_symbol_mapper import DEFAULT_TABLE, get_table_columns, parse_symbols, resolve_symbol_mapping


DEFAULT_SYMBOLS = "GBPUSD,EURUSD,USDJPY,XAUUSD"
DEFAULT_TFS = "1,5,15,30,60"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_tfs(raw: str) -> List[int]:
    out: List[int] = []
    for part in str(raw).split(","):
        part = part.strip()
        if part:
            out.append(int(part))
    return out


def connect_readonly(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def count_rows(conn: sqlite3.Connection, table: str, symbol: str, tf: int, has_symbol: bool) -> int:
    if has_symbol:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE symbol=? AND timeframe=?",
            (symbol, int(tf)),
        ).fetchone()
    else:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE timeframe=?",
            (int(tf),),
        ).fetchone()
    return int(row[0] if row else 0)


def run_smoke(db_path: str, symbols: Sequence[str], tfs: Sequence[int], table: str) -> Dict[str, object]:
    conn = connect_readonly(db_path)
    try:
        columns = get_table_columns(conn, table=table)
        has_symbol = "symbol" in columns
        results: Dict[str, object] = {}

        for symbol in symbols:
            try:
                mapping = resolve_symbol_mapping(symbol, db_columns=columns)
                rows_by_tf = {str(tf): count_rows(conn, table, mapping.symbol, int(tf), has_symbol) for tf in tfs}
                missing_tfs = [int(tf) for tf, n in rows_by_tf.items() if int(n) == 0]
                status = "OK" if not missing_tfs else "PARTIAL"
                results[mapping.symbol] = {
                    "status": status,
                    "mapping": mapping.as_dict(),
                    "rows_by_tf": rows_by_tf,
                    "missing_tfs": missing_tfs,
                }
            except Exception as exc:
                results[str(symbol).upper()] = {"status": "FAIL", "error": str(exc)}

        statuses = [str(v.get("status")) for v in results.values() if isinstance(v, dict)]
        overall = "OK" if statuses and all(s == "OK" for s in statuses) else "PARTIAL"
        if any(s == "FAIL" for s in statuses):
            overall = "FAIL" if all(s == "FAIL" for s in statuses) else "PARTIAL"

        return {
            "timestamp": utc_now_iso(),
            "db_path": db_path,
            "table": table,
            "has_symbol_column": has_symbol,
            "requested_symbols": list(symbols),
            "requested_tfs": list(tfs),
            "symbols": results,
            "overall_status": overall,
            "method": "multi_symbol_schema_smoke_test",
        }
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow multi-symbol smoke test")
    parser.add_argument("--db", default="Core/powerflow.db")
    parser.add_argument("--symbols", default=DEFAULT_SYMBOLS)
    parser.add_argument("--tfs", default=DEFAULT_TFS)
    parser.add_argument("--table", default=DEFAULT_TABLE)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", default="output/multi_symbol_smoke_test.json")
    args = parser.parse_args()

    payload = run_smoke(
        args.db,
        parse_symbols(args.symbols, default=DEFAULT_SYMBOLS),
        parse_tfs(args.tfs),
        args.table,
    )

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0 if payload.get("overall_status") in {"OK", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
