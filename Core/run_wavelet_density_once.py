"""run_wavelet_density_once.py - Single snapshot B4 Wavelet."""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from pf_wavelet_density import WaveletDensityAnalyzer


DEFAULT_DB = "powerflow.db"
DEFAULT_SYMBOL = "GBPUSD"
DEFAULT_TFS = "1,5,15"
DEFAULT_BARS = 100
DEFAULT_OUTPUT = "output/wavelet_density.json"


def parse_timeframes(raw: str) -> List[int]:
    values: List[int] = []
    for part in str(raw).split(","):
        part = part.strip().upper().replace("TF", "")
        if not part:
            continue
        values.append(int(part))
    if not values:
        raise ValueError("empty timeframe list")
    return values


def sanitize_symbol(symbol: str) -> str:
    cleaned = re.sub(r"[^A-Za-z]", "", str(symbol)).upper()
    return cleaned or DEFAULT_SYMBOL


def infer_currency_from_symbol(symbol: str) -> str:
    cleaned = sanitize_symbol(symbol)
    return cleaned[:3] if len(cleaned) >= 3 else cleaned


def get_table_columns(cursor: sqlite3.Cursor, table_name: str = "force_snapshots") -> List[str]:
    rows = cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row[1]) for row in rows]


def choose_time_column(columns: Sequence[str]) -> str:
    for candidate in ("timestamp", "created_at", "time", "datetime"):
        if candidate in columns:
            return candidate
    raise RuntimeError("force_snapshots has no timestamp/created_at time column")


def choose_force_column(columns: Sequence[str], symbol: str, currency: Optional[str], force_col: Optional[str]) -> str:
    if force_col:
        if force_col not in columns:
            raise RuntimeError(f"requested force column not found: {force_col}")
        return force_col

    # Mission schema: one generic force column + symbol filter.
    if "force" in columns:
        return "force"

    # PowerFlow V7 schema: force_gbp, force_usd, etc.
    ccy = (currency or infer_currency_from_symbol(symbol)).lower()
    candidates = [f"force_{ccy}", ccy, ccy.upper()]
    for candidate in candidates:
        if candidate in columns:
            return candidate

    force_columns = [col for col in columns if col.startswith("force_")]
    if force_columns:
        raise RuntimeError(
            f"no force column found for currency={ccy}; available force columns: {', '.join(force_columns)}"
        )

    raise RuntimeError("force_snapshots has no force column")


def fetch_force_series(
    cursor: sqlite3.Cursor,
    symbol: str,
    timeframe: int,
    bars: int,
    force_column: str,
    time_column: str,
    columns: Sequence[str],
) -> np.ndarray:
    where_parts = ["timeframe=?"]
    params: List[Any] = [int(timeframe)]

    # Use symbol filter only when the DB has this column. V7 single-symbol legacy DBs do not.
    if "symbol" in columns:
        where_parts.insert(0, "symbol=?")
        params.insert(0, sanitize_symbol(symbol))

    params.append(int(bars))
    where_sql = " AND ".join(where_parts)
    query = f"""
        SELECT {force_column}
        FROM force_snapshots
        WHERE {where_sql}
        ORDER BY {time_column} DESC
        LIMIT ?
    """
    rows = cursor.execute(query, params).fetchall()
    return np.asarray([row[0] for row in reversed(rows) if row[0] is not None], dtype=float)


def analyze_db_snapshot(
    db_path: str,
    symbol: str,
    timeframes: Iterable[int],
    bars: int,
    currency: Optional[str] = None,
    force_col: Optional[str] = None,
) -> Dict[str, Any]:
    analyzer = WaveletDensityAnalyzer()
    results: Dict[str, Any] = {}

    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        cursor = conn.cursor()
        columns = get_table_columns(cursor)
        if not columns:
            raise RuntimeError("force_snapshots table not found or empty schema")

        time_column = choose_time_column(columns)
        force_column = choose_force_column(columns, symbol, currency, force_col)

        for tf in timeframes:
            try:
                force = fetch_force_series(
                    cursor=cursor,
                    symbol=symbol,
                    timeframe=int(tf),
                    bars=int(bars),
                    force_column=force_column,
                    time_column=time_column,
                    columns=columns,
                )
                result = analyzer.analyze_timeframe(symbol, int(tf), force)
                results[str(int(tf))] = result
            except Exception as exc:
                results[str(int(tf))] = analyzer._invalid_result(  # internal format is the public JSON contract here
                    symbol=symbol,
                    timeframe=int(tf),
                    validity="INVALID",
                    reason=f"TF_ERROR: {exc}",
                )
    finally:
        conn.close()

    return results


def write_json(path: str, payload: Dict[str, Any], pretty: bool) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2 if pretty else None, ensure_ascii=False)
        handle.write("\n")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PowerFlow B4 Wavelet Density one-shot runner")
    parser.add_argument("--db", default=DEFAULT_DB, help="SQLite DB path, read-only")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Symbol label, default GBPUSD")
    parser.add_argument("--currency", default=None, help="Force currency for V7 schema, default inferred from symbol")
    parser.add_argument("--force-col", default=None, help="Explicit force column override, e.g. force_gbp")
    parser.add_argument("--tfs", default=DEFAULT_TFS, help="Comma-separated timeframes, e.g. 1,5,15")
    parser.add_argument("--bars", type=int, default=DEFAULT_BARS, help="Number of latest bars to read")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        tfs = parse_timeframes(args.tfs)
        symbol = sanitize_symbol(args.symbol)
        results = analyze_db_snapshot(
            db_path=args.db,
            symbol=symbol,
            timeframes=tfs,
            bars=args.bars,
            currency=args.currency,
            force_col=args.force_col,
        )
        write_json(args.output, results, pretty=args.pretty)
        print(json.dumps(results, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
