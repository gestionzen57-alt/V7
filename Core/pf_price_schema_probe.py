#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_price_schema_probe.py
PowerFlow V7.3 - read-only DB schema probe for price/OHLC and force snapshot data.

Role:
- Detect whether the DB contains usable OHLC data for top-down zone/rotation reading.
- Detect force snapshot fallback when OHLC is unavailable.
- Never writes to DB.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]
DEFAULT_TIMEFRAMES = [1, 5, 15, 30, 60, 240, 1440, 10080]

SYMBOL_CANDIDATES = ["symbol", "pair", "instrument", "ticker"]
TIMEFRAME_CANDIDATES = ["timeframe", "tf", "tf_minutes", "period", "timeframe_minutes", "interval"]
TIMESTAMP_CANDIDATES = ["timestamp", "time", "datetime", "created_at", "ts", "candle_time", "date_time", "bar_time"]
OPEN_CANDIDATES = ["open", "open_price", "o"]
HIGH_CANDIDATES = ["high", "high_price", "h"]
LOW_CANDIDATES = ["low", "low_price", "l"]
CLOSE_CANDIDATES = ["close", "close_price", "c", "price", "last", "value"]

CURRENCY_CODES = ["GBP", "EUR", "USD", "JPY", "CAD", "CHF", "AUD", "NZD", "XAU"]

TF_ALIASES: Dict[int, List[str]] = {
    1: ["1", "M1", "m1", "1m", "1min", "60"],
    5: ["5", "M5", "m5", "5m", "5min", "300"],
    15: ["15", "M15", "m15", "15m", "15min", "900"],
    30: ["30", "M30", "m30", "30m", "30min", "1800"],
    60: ["60", "H1", "h1", "1h", "60m", "3600"],
    240: ["240", "H4", "h4", "4h", "240m", "14400"],
    1440: ["1440", "D1", "d1", "1d", "daily", "86400"],
    10080: ["10080", "W1", "w1", "1w", "weekly", "604800"],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def quote_ident(name: str) -> str:
    if not isinstance(name, str) or not name:
        raise ValueError("Invalid SQL identifier")
    return '"' + name.replace('"', '""') + '"'


def list_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
    ).fetchall()
    return [str(r[0]) for r in rows]


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()
    return [str(r[1]) for r in rows]


def find_column(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    # fuzzy fallback: exact candidate as substring, but avoid too aggressive matches
    for cand in candidates:
        for c in columns:
            if cand.lower() == c.lower().replace("_", ""):
                return c
    return None


def detect_currency_columns(columns: Sequence[str]) -> List[str]:
    detected: List[str] = []
    lower_map = {c.lower(): c for c in columns}
    for code in CURRENCY_CODES:
        variants = [code.lower(), f"force_{code.lower()}", f"{code.lower()}_force", f"z_{code.lower()}"]
        if any(v in lower_map for v in variants):
            detected.append(code)
    return detected


def get_row_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {quote_ident(table)}").fetchone()[0])
    except Exception:
        return 0


def safe_minmax(conn: sqlite3.Connection, table: str, col: str) -> Tuple[Optional[Any], Optional[Any]]:
    try:
        row = conn.execute(
            f"SELECT MIN({quote_ident(col)}) AS mn, MAX({quote_ident(col)}) AS mx FROM {quote_ident(table)}"
        ).fetchone()
        return row["mn"], row["mx"]
    except Exception:
        return None, None


def normalize_tf_value(value: Any) -> Optional[int]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        n = int(float(s))
        # Common DBs use seconds for TF; map seconds to minutes.
        if n in (60, 300, 900, 1800, 3600, 14400, 86400, 604800):
            return {60: 1, 300: 5, 900: 15, 1800: 30, 3600: 60, 14400: 240, 86400: 1440, 604800: 10080}[n]
        return n
    except Exception:
        pass
    u = s.upper()
    mapping = {
        "M1": 1, "1M": 1, "1MIN": 1,
        "M5": 5, "5M": 5, "5MIN": 5,
        "M15": 15, "15M": 15, "15MIN": 15,
        "M30": 30, "30M": 30, "30MIN": 30,
        "H1": 60, "1H": 60,
        "H4": 240, "4H": 240,
        "D1": 1440, "1D": 1440, "DAILY": 1440,
        "W1": 10080, "1W": 10080, "WEEKLY": 10080,
    }
    return mapping.get(u)


def timeframe_where_clause(tf_col: str, timeframe: int) -> Tuple[str, List[str]]:
    aliases = TF_ALIASES.get(timeframe, [str(timeframe)])
    q = quote_ident(tf_col)
    placeholders = ",".join(["?"] * len(aliases))
    return f"CAST({q} AS TEXT) IN ({placeholders})", aliases


def symbol_where_clause(symbol_col: str, symbol: str) -> Tuple[str, List[str]]:
    return f"UPPER(CAST({quote_ident(symbol_col)} AS TEXT)) = UPPER(?)", [symbol]


def table_symbol_tf_stats(
    conn: sqlite3.Connection,
    table: str,
    symbol_col: Optional[str],
    timeframe_col: Optional[str],
    timestamp_col: Optional[str],
    symbols: Sequence[str],
    timeframes: Sequence[int],
) -> Dict[str, Any]:
    stats: Dict[str, Any] = {"symbols": {}}
    if not symbol_col or not timeframe_col or not timestamp_col:
        return stats
    qt = quote_ident(table)
    qs = quote_ident(symbol_col)
    qtf = quote_ident(timeframe_col)
    qts = quote_ident(timestamp_col)
    for sym in symbols:
        sym_payload: Dict[str, Any] = {"timeframes": {}}
        for tf in timeframes:
            tf_clause, tf_params = timeframe_where_clause(timeframe_col, tf)
            sym_clause, sym_params = symbol_where_clause(symbol_col, sym)
            sql = (
                f"SELECT COUNT(*) AS rows, MIN({qts}) AS earliest, MAX({qts}) AS latest "
                f"FROM {qt} WHERE {sym_clause} AND {tf_clause}"
            )
            try:
                row = conn.execute(sql, sym_params + tf_params).fetchone()
                sym_payload["timeframes"][str(tf)] = {
                    "row_count": int(row["rows"] or 0),
                    "earliest_timestamp": row["earliest"],
                    "latest_timestamp": row["latest"],
                }
            except Exception as exc:
                sym_payload["timeframes"][str(tf)] = {
                    "row_count": 0,
                    "earliest_timestamp": None,
                    "latest_timestamp": None,
                    "error": str(exc),
                }
        stats["symbols"][sym] = sym_payload
    return stats


def inspect_table(conn: sqlite3.Connection, table: str, symbols: Sequence[str], timeframes: Sequence[int]) -> Dict[str, Any]:
    columns = table_columns(conn, table)
    symbol_col = find_column(columns, SYMBOL_CANDIDATES)
    timeframe_col = find_column(columns, TIMEFRAME_CANDIDATES)
    timestamp_col = find_column(columns, TIMESTAMP_CANDIDATES)
    open_col = find_column(columns, OPEN_CANDIDATES)
    high_col = find_column(columns, HIGH_CANDIDATES)
    low_col = find_column(columns, LOW_CANDIDATES)
    close_col = find_column(columns, CLOSE_CANDIDATES)
    currency_cols = detect_currency_columns(columns)
    row_count = get_row_count(conn, table)

    has_symbol_tf_time = bool(symbol_col and timeframe_col and timestamp_col)
    has_ohlc = bool(has_symbol_tf_time and high_col and low_col and close_col)
    if close_col and not open_col:
        # Close-only table can still support limited price reading, but not full candle behavior.
        pass
    is_force_like = bool(has_symbol_tf_time and len(currency_cols) >= 2)
    score = 0
    if has_symbol_tf_time:
        score += 20
    if has_ohlc:
        score += 60
    if open_col:
        score += 10
    if is_force_like:
        score += 20
    score += min(row_count, 100000) // 5000

    stats = table_symbol_tf_stats(conn, table, symbol_col, timeframe_col, timestamp_col, symbols, timeframes)

    return {
        "table": table,
        "row_count": row_count,
        "columns": columns,
        "detected_columns": {
            "symbol": symbol_col,
            "timeframe": timeframe_col,
            "timestamp": timestamp_col,
            "open": open_col,
            "high": high_col,
            "low": low_col,
            "close": close_col,
            "currency_force_columns": currency_cols,
        },
        "capabilities": {
            "symbol_timeframe_timestamp": has_symbol_tf_time,
            "ohlc_full": has_ohlc and bool(open_col),
            "ohlc_partial": has_ohlc,
            "force_like": is_force_like,
        },
        "score": score,
        "stats": stats,
    }


def choose_primary_tables(tables: List[Dict[str, Any]]) -> Dict[str, Optional[Dict[str, Any]]]:
    ohlc_candidates = [t for t in tables if t["capabilities"].get("ohlc_partial")]
    force_candidates = [t for t in tables if t["capabilities"].get("force_like")]
    primary_ohlc = max(ohlc_candidates, key=lambda t: (t["score"], t["row_count"]), default=None)
    primary_force = max(force_candidates, key=lambda t: (t["score"], t["row_count"]), default=None)
    return {"primary_ohlc_table": primary_ohlc, "primary_force_table": primary_force}


def probe_price_schema(
    db_path: str | Path,
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    timeframes: Sequence[int] = DEFAULT_TIMEFRAMES,
) -> Dict[str, Any]:
    technical_risks: List[str] = []
    out: Dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "method": "PRICE_SCHEMA_PROBE_V73",
        "db_path": str(db_path),
        "db_mode": "READ_ONLY",
        "symbols_requested": list(symbols),
        "timeframes_requested": list(timeframes),
        "tables": [],
        "primary_ohlc_table": None,
        "primary_force_table": None,
        "price_reading_capability": "UNKNOWN",
        "technical_risks": technical_risks,
    }
    try:
        with connect_readonly(db_path) as conn:
            inspected = [inspect_table(conn, t, symbols, timeframes) for t in list_tables(conn)]
            inspected_sorted = sorted(inspected, key=lambda t: (t["score"], t["row_count"]), reverse=True)
            out["tables"] = inspected_sorted
            chosen = choose_primary_tables(inspected_sorted)
            out["primary_ohlc_table"] = chosen["primary_ohlc_table"]
            out["primary_force_table"] = chosen["primary_force_table"]
    except Exception as exc:
        technical_risks.append(f"SCHEMA_PROBE_FAILED:{type(exc).__name__}:{exc}")
        out["price_reading_capability"] = "PROBE_FAILED"
        return out

    if out["primary_ohlc_table"]:
        out["price_reading_capability"] = "OHLC_AVAILABLE"
    elif out["primary_force_table"]:
        out["price_reading_capability"] = "FORCE_ONLY_NO_OHLC"
        technical_risks.append("NO_OHLC_TABLE_DETECTED_TOPDOWN_LEVELS_LIMITED")
    else:
        out["price_reading_capability"] = "NO_USABLE_MARKET_TABLE_DETECTED"
        technical_risks.append("NO_SYMBOL_TIMEFRAME_MARKET_TABLE_DETECTED")
    return out


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Probe PowerFlow DB for OHLC/price schema.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--timeframes", default=",".join(str(x) for x in DEFAULT_TIMEFRAMES))
    parser.add_argument("--output", default="output/dashboard_surface/price_schema_probe.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    timeframes = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]
    state = probe_price_schema(args.db, symbols=symbols, timeframes=timeframes)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(state, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print(
            f"PRICE_SCHEMA_PROBE_OK | capability={state.get('price_reading_capability')} | out={out_path}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
