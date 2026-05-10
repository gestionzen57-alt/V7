"""
run_fractal_resonance_once.py
B7 — Fractal Resonance Detection one-shot runner.

Example:
    python Core/run_fractal_resonance_once.py --db Core/powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --pretty
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

try:
    from pf_fractal_resonance import FractalResonanceAnalyzer
except ImportError:
    # Allows execution from repository root when this file is in Core/.
    sys.path.append(str(Path(__file__).resolve().parent))
    from pf_fractal_resonance import FractalResonanceAnalyzer


DEFAULT_TFS = [1, 5, 15, 30, 60]
DEFAULT_OUTPUT = "output/fractal_resonance.json"


def parse_tfs(raw: str) -> List[int]:
    values: List[int] = []
    for part in raw.split(","):
        part = part.strip()
        if not part:
            continue
        values.append(int(part))
    return values or DEFAULT_TFS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_symbol(symbol: str) -> str:
    return "".join(ch for ch in symbol.upper().strip() if ch.isalnum())


def infer_force_columns(symbol: str, requested_column: Optional[str]) -> List[str]:
    if requested_column:
        return [requested_column]

    symbol_clean = normalize_symbol(symbol)
    candidates: List[str] = []

    if len(symbol_clean) >= 3:
        base = symbol_clean[:3].lower()
        quote = symbol_clean[3:6].lower() if len(symbol_clean) >= 6 else ""
        candidates.append(f"force_{base}")
        if quote:
            candidates.append(f"force_{quote}")

    # Compatibility with previous B4 prompt variants and possible lab schemas.
    candidates.extend(["force", "angle_kalman", "angle", "force_gbp", "force_usd"])

    deduped: List[str] = []
    for col in candidates:
        if col and col not in deduped:
            deduped.append(col)
    return deduped


def get_table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [str(row[1]) for row in rows]


def choose_existing_column(existing_columns: Sequence[str], candidates: Sequence[str]) -> str:
    existing = set(existing_columns)
    for candidate in candidates:
        if candidate in existing:
            return candidate
    raise ValueError(
        "No usable force column found. Tried: "
        + ", ".join(candidates)
        + ". Existing columns: "
        + ", ".join(existing_columns)
    )


def load_force_series(
    conn: sqlite3.Connection,
    db_path: str,
    symbol: str,
    timeframe: int,
    force_column: str,
    limit: int,
    table: str = "force_snapshots",
) -> np.ndarray:
    existing_columns = get_table_columns(conn, table)
    has_symbol = "symbol" in existing_columns
    has_timestamp = "timestamp" in existing_columns

    if force_column not in existing_columns:
        raise ValueError(f"Column {force_column!r} not found in {table}")
    if "timeframe" not in existing_columns:
        raise ValueError(f"Column 'timeframe' not found in {table}")

    where = "timeframe = ?"
    params: List[object] = [int(timeframe)]
    if has_symbol:
        where = "symbol = ? AND " + where
        params.insert(0, normalize_symbol(symbol))

    order = "ORDER BY timestamp DESC" if has_timestamp else "ORDER BY rowid DESC"
    query = f"""
        SELECT {force_column}
        FROM {table}
        WHERE {where}
        {order}
        LIMIT ?
    """
    params.append(int(limit))

    rows = conn.execute(query, params).fetchall()
    values = [row[0] for row in reversed(rows) if row[0] is not None]
    return np.asarray(values, dtype=float)


def load_multi_tf_series(
    db_path: str,
    symbol: str,
    tfs: Iterable[int],
    force_column: Optional[str],
    limit: int,
    table: str = "force_snapshots",
) -> Tuple[Dict[int, np.ndarray], str, List[str]]:
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        existing_columns = get_table_columns(conn, table)
        chosen_column = choose_existing_column(existing_columns, infer_force_columns(symbol, force_column))
        risks: List[str] = []
        series_by_tf: Dict[int, np.ndarray] = {}

        for tf in tfs:
            arr = load_force_series(conn, db_path, symbol, int(tf), chosen_column, limit, table)
            if len(arr) == 0:
                risks.append(f"NO_DATA_TF{int(tf)}")
            elif len(arr) < limit:
                risks.append(f"PARTIAL_DATA_TF{int(tf)}:{len(arr)}")
            series_by_tf[int(tf)] = arr

        return series_by_tf, chosen_column, risks
    finally:
        conn.close()


def write_json(path: str, payload: object, pretty: bool) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2 if pretty else None, ensure_ascii=False)
        f.write("\n")


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PowerFlow B7 Fractal Resonance one-shot runner")
    parser.add_argument("--db", default="Core/powerflow.db", help="SQLite DB path, opened read-only")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbol, default GBPUSD")
    parser.add_argument("--tfs", default="1,5,15,30,60", help="Comma-separated timeframe list")
    parser.add_argument("--force-column", default=None, help="Optional explicit DB column, e.g. force_gbp")
    parser.add_argument("--window", type=int, default=50, help="Correlation window size")
    parser.add_argument("--max-lag", type=int, default=10, help="Max lag bars to scan")
    parser.add_argument("--table", default="force_snapshots", help="DB table name")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output JSON path")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = build_arg_parser().parse_args(argv)
    symbol = normalize_symbol(args.symbol)
    tfs = parse_tfs(args.tfs)

    analyzer = FractalResonanceAnalyzer(corr_window=args.window, max_lag=args.max_lag)
    timestamp = utc_now_iso()

    try:
        series_by_tf, chosen_column, load_risks = load_multi_tf_series(
            db_path=args.db,
            symbol=symbol,
            tfs=tfs,
            force_column=args.force_column,
            limit=args.window,
            table=args.table,
        )

        result = analyzer.analyze_multi_tf(series_by_tf, symbol=symbol, timestamp=timestamp)
        result["source"] = {
            "db_path": args.db,
            "table": args.table,
            "force_column": chosen_column,
            "requested_tfs": tfs,
        }

        if load_risks:
            merged = list(result.get("technical_risks", [])) + load_risks
            result["technical_risks"] = list(dict.fromkeys(merged))

        write_json(args.output, result, args.pretty)
        print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
        return 0 if result.get("valid") else 2

    except Exception as exc:
        error_payload = {
            "timestamp": timestamp,
            "symbol": symbol,
            "resonance_state": "SILENT",
            "resonance_score": 0.0,
            "resonant_tfs": [],
            "lagged_tfs": [],
            "dissonant_tfs": tfs,
            "pair_correlations": {},
            "lag_detection": {},
            "expected_amplification": False,
            "technical_risks": ["RUNNER_ERROR"],
            "method": "cross_correlation_multi_tf",
            "valid": False,
            "error": str(exc),
            "source": {
                "db_path": args.db,
                "table": args.table,
                "force_column": args.force_column,
                "requested_tfs": tfs,
            },
        }
        try:
            write_json(args.output, error_payload, args.pretty)
        finally:
            print(json.dumps(error_payload, indent=2 if args.pretty else None, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
