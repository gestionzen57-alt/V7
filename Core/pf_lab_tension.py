#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - pf_lab_tension.py
Version: V0.1.0
Layer: 11 — Tension Signature (Lab Query Wrapper)

Mission:
    Wrapper couche 11 du lab PowerFlow.
    Charge force_snapshots per devise per TF,
    calcule la tension signature via pf_tension_signature,
    retourne dict structuré pour query_full_v3.

Doctrine:
    Read-only. No DB write. No Telegram. No Cockpit import.
    ELASTIC_LOADED / DIRECTIONAL_MOVE / DEAD_CURRENCY — exposé sans filtre.
    Trader décide.
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from pf_tension_signature import compute_tension_signature

# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────

CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]
FORCE_COLS = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
}

DEFAULT_BARS = 30
DEFAULT_WINDOW = 5


# ──────────────────────────────────────────────────────────────
# DB HELPERS
# ──────────────────────────────────────────────────────────────

def _norm_dt(dt_str: str) -> str:
    """Normalize datetime string — strip timezone offset for SQLite comparison."""
    if not dt_str:
        return dt_str
    for sep in ("+00:00", "+0000", "Z"):
        if dt_str.endswith(sep):
            return dt_str[: -len(sep)]
    return dt_str


def _load_force_series(
    db_path: str,
    symbol: str,
    tf: int,
    bars: int,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> Dict[str, List[float]]:
    """
    Load force series per currency from force_snapshots.
    Returns { "GBP": [f1, f2, ...], "USD": [...], ... }
    Falls back to last N bars if datetime window yields 0 rows.
    """
    uri = f"file:{db_path}?mode=ro"
    cols_str = ", ".join(FORCE_COLS.values())

    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row

        rows = []
        if start and end:
            s = _norm_dt(start)
            e = _norm_dt(end)
            cur = conn.execute(
                f"""
                SELECT created_at, {cols_str}
                FROM force_snapshots
                WHERE symbol = ? AND timeframe = ?
                  AND created_at >= ? AND created_at <= ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (symbol, tf, s, e, bars),
            )
            rows = cur.fetchall()

        # Fallback to last N bars
        if not rows:
            cur = conn.execute(
                f"""
                SELECT created_at, {cols_str}
                FROM force_snapshots
                WHERE symbol = ? AND timeframe = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (symbol, tf, bars),
            )
            rows = list(reversed(cur.fetchall()))

    series: Dict[str, List[float]] = {c: [] for c in CURRENCIES}
    for row in rows:
        for cur, col in FORCE_COLS.items():
            val = row[col]
            if val is not None:
                try:
                    series[cur].append(float(val))
                except (TypeError, ValueError):
                    pass

    return series


# ──────────────────────────────────────────────────────────────
# MAIN QUERY
# ──────────────────────────────────────────────────────────────

def query_tension_signature(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: Optional[str] = None,
    end: Optional[str] = None,
    bars: int = DEFAULT_BARS,
    window: int = DEFAULT_WINDOW,
) -> Dict[str, Any]:
    """
    Tension Signature multi-TF per devise — Layer 11 lab query.

    Args:
        db_path:    Path to powerflow.db
        symbol:     Symbol (ex: "GBPUSD")
        tfs:        List of timeframes (ex: [5, 15, 60])
        start:      ISO8601 datetime string (optional)
        end:        ISO8601 datetime string (optional)
        bars:       Max bars to load per TF (default 30)
        window:     Macro variance window size (default 5)

    Returns:
        {
            "timeframes": {
                "60": {
                    "currencies": {
                        "USD": {
                            "score": float,
                            "label": str,       # ELASTIC_LOADED / DIRECTIONAL_MOVE / DEAD_CURRENCY
                            "micro_var": float,
                            "macro_var": float,
                            "n_bars": int,
                            "note": str,
                        },
                        ...
                    },
                    "elastic_loaded": [str],    # currencies with ELASTIC_LOADED
                    "directional_move": [str],  # currencies with DIRECTIONAL_MOVE
                    "dead_currencies": [str],   # currencies with DEAD_CURRENCY
                    "top_elastic": str or None, # highest score ELASTIC_LOADED
                    "n_bars": int,
                    "error": str or None,
                }
            },
            "cross_tf_summary": {
                "elastic_currencies": {str: int},   # currency → count of TFs ELASTIC_LOADED
                "directional_currencies": {str: int},
                "top_elastic_global": str or None,  # most consistently ELASTIC
            },
            "error": str or None,
        }
    """
    result: Dict[str, Any] = {
        "timeframes": {},
        "cross_tf_summary": {
            "elastic_currencies": {},
            "directional_currencies": {},
            "top_elastic_global": None,
        },
        "error": None,
    }

    elastic_counts: Dict[str, int] = {}
    directional_counts: Dict[str, int] = {}

    for tf in tfs:
        tf_key = str(tf)
        tf_result: Dict[str, Any] = {
            "currencies": {},
            "elastic_loaded": [],
            "directional_move": [],
            "dead_currencies": [],
            "top_elastic": None,
            "n_bars": 0,
            "error": None,
        }

        try:
            series = _load_force_series(db_path, symbol, tf, bars, start, end)

            n_bars_max = max((len(v) for v in series.values()), default=0)
            tf_result["n_bars"] = n_bars_max

            if n_bars_max < 6:
                tf_result["error"] = f"INSUFFICIENT_DATA ({n_bars_max} bars)"
                result["timeframes"][tf_key] = tf_result
                continue

            top_elastic_score = -1.0
            top_elastic_cur = None

            for cur in CURRENCIES:
                vals = series.get(cur, [])
                if len(vals) < 6:
                    tf_result["currencies"][cur] = {
                        "score": 0.0,
                        "label": "INSUFFICIENT_DATA",
                        "micro_var": 0.0,
                        "macro_var": 0.0,
                        "n_bars": len(vals),
                        "note": f"Moins de 6 barres ({len(vals)}).",
                    }
                    continue

                sig = compute_tension_signature(vals, window=window)
                tf_result["currencies"][cur] = sig.to_dict()

                if sig.label == "ELASTIC_LOADED":
                    tf_result["elastic_loaded"].append(cur)
                    elastic_counts[cur] = elastic_counts.get(cur, 0) + 1
                    if sig.score > top_elastic_score:
                        top_elastic_score = sig.score
                        top_elastic_cur = cur
                elif sig.label == "DIRECTIONAL_MOVE":
                    tf_result["directional_move"].append(cur)
                    directional_counts[cur] = directional_counts.get(cur, 0) + 1
                elif sig.label in ("DEAD_CURRENCY", "INSUFFICIENT_DATA"):
                    tf_result["dead_currencies"].append(cur)

            tf_result["top_elastic"] = top_elastic_cur

        except Exception as exc:
            tf_result["error"] = f"TF_ERROR: {exc}"

        result["timeframes"][tf_key] = tf_result

    # Cross-TF summary
    result["cross_tf_summary"]["elastic_currencies"] = elastic_counts
    result["cross_tf_summary"]["directional_currencies"] = directional_counts

    if elastic_counts:
        result["cross_tf_summary"]["top_elastic_global"] = max(
            elastic_counts, key=elastic_counts.get
        )

    return result


# ──────────────────────────────────────────────────────────────
# CLI (standalone test)
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="pf_lab_tension — standalone test")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--tfs", default="5,15,60")
    parser.add_argument("--bars", type=int, default=30)
    parser.add_argument("--window", type=int, default=5)
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    tfs = [int(t) for t in args.tfs.split(",")]
    result = query_tension_signature(
        db_path=args.db,
        symbol=args.symbol,
        tfs=tfs,
        start=args.start,
        end=args.end,
        bars=args.bars,
        window=args.window,
    )

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent, default=str))
