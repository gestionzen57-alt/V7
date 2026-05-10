"""
run_fractal_resonance_once.py
B7 — Fractal Resonance Detection one-shot runner, multi-symbol aware.

Examples
--------
python Core/run_fractal_resonance_once.py --db Core/powerflow.db --symbol GBPUSD --tfs 1,5,15,30,60 --pretty
python Core/run_fractal_resonance_once.py --db Core/powerflow.db --symbol EURUSD --tfs 1,5,15 --force-mode spread --pretty
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

try:
    from pf_fractal_resonance import FractalResonanceAnalyzer
    from pf_multi_symbol_db import connect_readonly, load_force_matrix
    from pf_symbol_mapper import DEFAULT_SYMBOL, get_table_columns, resolve_symbol_mapping
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from pf_fractal_resonance import FractalResonanceAnalyzer
    from pf_multi_symbol_db import connect_readonly, load_force_matrix
    from pf_symbol_mapper import DEFAULT_SYMBOL, get_table_columns, resolve_symbol_mapping


DEFAULT_TFS = [1, 5, 15, 30, 60]
DEFAULT_OUTPUT = "output/fractal_resonance_{symbol}.json"


def parse_tfs(raw: str) -> List[int]:
    values: List[int] = []
    for part in str(raw).split(","):
        part = part.strip()
        if part:
            values.append(int(part))
    return values or DEFAULT_TFS


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_invalid_result(symbol: str, error: str, tfs: Sequence[int]) -> Dict[str, object]:
    return {
        "timestamp": utc_now_iso(),
        "symbol": symbol,
        "resonance_state": "SILENT",
        "resonance_score": 0.0,
        "avg_signed_correlation": 0.0,
        "resonant_tfs": [],
        "lagged_tfs": [],
        "dissonant_tfs": list(tfs),
        "pair_correlations": {},
        "pair_states": {},
        "lag_detection": {},
        "pair_xcorr_peak": {},
        "expected_amplification": False,
        "technical_risks": ["INSUFFICIENT_DATA"],
        "method": "cross_correlation_multi_tf",
        "valid": False,
        "error": error,
    }


def analyze_symbol(
    db_path: str,
    symbol: str,
    tfs: Sequence[int],
    *,
    table: str,
    limit: int,
    window: int,
    max_lag: int,
    force_mode: str,
) -> Dict[str, object]:
    conn = connect_readonly(db_path)
    try:
        columns = get_table_columns(conn, table=table)
        mapping = resolve_symbol_mapping(symbol, db_columns=columns)
    finally:
        conn.close()

    force_by_tf = load_force_matrix(
        db_path,
        mapping.symbol,
        list(tfs),
        mode=force_mode,
        table=table,
        limit=limit,
    )

    analyzer = FractalResonanceAnalyzer(corr_window=window, max_lag=max_lag)
    result = analyzer.analyze_multi_tf(force_by_tf)

    # Force stable top-level contract.
    result["timestamp"] = utc_now_iso()
    result["symbol"] = mapping.symbol
    result["method"] = "cross_correlation_multi_tf"
    result["valid"] = bool(result.get("valid", False))
    result["source"] = {
        "db_path": db_path,
        "table": table,
        "symbol": mapping.symbol,
        "base_asset": mapping.base_asset,
        "quote_asset": mapping.quote_asset,
        "force_columns": [mapping.base_column, mapping.quote_column],
        "force_mode": force_mode,
        "requested_tfs": list(tfs),
    }
    return result


def write_json(path_template: str, symbol: str, payload: Dict[str, object]) -> str:
    path = path_template.format(symbol=symbol)
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow B7 Fractal Resonance one-shot runner")
    parser.add_argument("--db", default="Core/powerflow.db", help="Path to powerflow.db")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Trading symbol, e.g. GBPUSD/EURUSD/USDJPY/XAUUSD")
    parser.add_argument("--tfs", default=",".join(str(x) for x in DEFAULT_TFS), help="Comma-separated TF list")
    parser.add_argument("--table", default="force_snapshots", help="SQLite table name")
    parser.add_argument("--limit", type=int, default=100, help="Rows loaded per timeframe")
    parser.add_argument("--window", type=int, default=50, help="Correlation window bars")
    parser.add_argument("--max-lag", type=int, default=10, help="Lag scan max bars")
    parser.add_argument(
        "--force-mode",
        choices=["base", "quote", "spread"],
        default="base",
        help="Series used for resonance: base, quote, or base-minus-quote spread",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output path template; {symbol} is supported")
    args = parser.parse_args()

    tfs = parse_tfs(args.tfs)
    try:
        result = analyze_symbol(
            args.db,
            args.symbol,
            tfs,
            table=args.table,
            limit=args.limit,
            window=args.window,
            max_lag=args.max_lag,
            force_mode=args.force_mode,
        )
    except Exception as exc:
        result = build_invalid_result(args.symbol, str(exc), tfs)

    out_path = write_json(args.output, str(result.get("symbol", args.symbol)), result)
    result.setdefault("output_path", out_path)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))

    return 0 if result.get("valid") else 2


if __name__ == "__main__":
    raise SystemExit(main())
