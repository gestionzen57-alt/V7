"""
pf_multi_symbol_db.py
PowerFlow V7.1 — Read-only helpers for multi-symbol force_snapshots access.

This file is intentionally small. It is a helper layer for refactoring B1-B7
without duplicating SQL patterns in every pf_* module.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import numpy as np

from pf_symbol_mapper import (
    DEFAULT_TABLE,
    SymbolMapping,
    build_force_select_sql,
    get_table_columns,
    resolve_symbol_mapping,
)


class PowerFlowDBError(RuntimeError):
    """Raised for explicit read-only DB access errors."""


def connect_readonly(db_path: str) -> sqlite3.Connection:
    """Open SQLite DB in read-only mode, never write."""
    path = Path(db_path)
    if not path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    return sqlite3.connect(f"file:{path}?mode=ro", uri=True)


def load_pair_force_series(
    conn: sqlite3.Connection,
    symbol: str,
    timeframe: int,
    *,
    table: str = DEFAULT_TABLE,
    limit: int = 100,
) -> Dict[str, object]:
    """
    Load base and quote force series for one symbol/timeframe.

    Returns oldest -> newest arrays so downstream rolling logic keeps natural
    chronological order.
    """
    columns = get_table_columns(conn, table=table)
    sql, params, mapping = build_force_select_sql(
        symbol,
        timeframe,
        columns,
        table=table,
        limit=limit,
        order_desc=True,
    )
    rows = conn.execute(sql, params).fetchall()

    # Query is DESC; reverse to chronological order.
    rows = list(reversed(rows))
    base_values: List[float] = []
    quote_values: List[float] = []
    timestamps: List[str] = []

    for base, quote, ts in rows:
        if base is None or quote is None:
            continue
        try:
            base_values.append(float(base))
            quote_values.append(float(quote))
            timestamps.append(str(ts))
        except (TypeError, ValueError):
            continue

    return {
        "symbol": mapping.symbol,
        "timeframe": int(timeframe),
        "mapping": mapping.as_dict(),
        "base": np.asarray(base_values, dtype=float),
        "quote": np.asarray(quote_values, dtype=float),
        "spread": np.asarray(base_values, dtype=float) - np.asarray(quote_values, dtype=float),
        "timestamps": timestamps,
        "samples": len(base_values),
    }


def load_force_matrix(
    db_path: str,
    symbol: str,
    timeframes: Sequence[int],
    *,
    mode: str = "base",
    table: str = DEFAULT_TABLE,
    limit: int = 100,
) -> Dict[int, np.ndarray]:
    """
    Load a dict {timeframe: np.ndarray} for B7/B4-style modules.

    mode:
      - base   : base currency force, backward-compatible with GBPUSD force_gbp
      - quote  : quote currency force
      - spread : base - quote symbol pressure
    """
    mode_clean = mode.lower().strip()
    if mode_clean not in {"base", "quote", "spread"}:
        raise ValueError("mode must be one of: base, quote, spread")

    conn = connect_readonly(db_path)
    try:
        result: Dict[int, np.ndarray] = {}
        for tf in timeframes:
            payload = load_pair_force_series(
                conn,
                symbol,
                int(tf),
                table=table,
                limit=limit,
            )
            arr = payload[mode_clean]
            if isinstance(arr, np.ndarray) and arr.size > 0:
                result[int(tf)] = arr
        return result
    finally:
        conn.close()
