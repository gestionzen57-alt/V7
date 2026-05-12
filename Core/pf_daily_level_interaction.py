#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

PREFERRED_TABLES = ["force_snapshots_v2", "price_candles", "candles", "ohlc", "rates", "market_data"]
SYMBOL_COL_CANDIDATES = ["symbol", "pair", "instrument"]
TF_COL_CANDIDATES = ["timeframe", "tf", "tf_minutes", "period"]
TS_COL_CANDIDATES = ["timestamp", "time", "datetime", "created_at", "ts", "bar_time"]
OPEN_COL_CANDIDATES = ["open", "o", "bid_open", "price_open"]
HIGH_COL_CANDIDATES = ["high", "h", "bid_high", "price_high"]
LOW_COL_CANDIDATES = ["low", "l", "bid_low", "price_low"]
CLOSE_COL_CANDIDATES = ["close", "c", "bid_close", "price_close", "price"]


@dataclass
class OhlcSchema:
    table: str
    symbol_col: str
    timeframe_col: str
    timestamp_col: str
    open_col: Optional[str]
    high_col: str
    low_col: str
    close_col: str


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def qname(name: str) -> str:
    return '"' + str(name).replace('"', '""') + '"'


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z") if dt else None


def connect_ro(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)


def list_tables(conn: sqlite3.Connection) -> List[str]:
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({qname(table)})").fetchall()]


def find_col(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    lower = {str(c).lower(): c for c in columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def detect_ohlc_schema(conn: sqlite3.Connection) -> Tuple[Optional[OhlcSchema], List[str]]:
    risks: List[str] = []
    tables = list_tables(conn)
    ordered = [t for t in PREFERRED_TABLES if t in tables] + [t for t in tables if t not in PREFERRED_TABLES]
    rejected: List[str] = []
    for table in ordered:
        cols = table_columns(conn, table)
        symbol_col = find_col(cols, SYMBOL_COL_CANDIDATES)
        tf_col = find_col(cols, TF_COL_CANDIDATES)
        ts_col = find_col(cols, TS_COL_CANDIDATES)
        open_col = find_col(cols, OPEN_COL_CANDIDATES)
        high_col = find_col(cols, HIGH_COL_CANDIDATES)
        low_col = find_col(cols, LOW_COL_CANDIDATES)
        close_col = find_col(cols, CLOSE_COL_CANDIDATES)
        if not (symbol_col and tf_col and ts_col and high_col and low_col and close_col):
            continue
        sample_cols = [high_col, low_col, close_col] + ([open_col] if open_col else [])
        try:
            select_expr = ", ".join(qname(c) for c in sample_cols)
            rows = conn.execute(
                f"SELECT {select_expr} FROM {qname(table)} "
                f"WHERE {qname(high_col)} IS NOT NULL AND {qname(low_col)} IS NOT NULL AND {qname(close_col)} IS NOT NULL "
                f"ORDER BY {qname(ts_col)} DESC LIMIT 20"
            ).fetchall()
        except Exception:
            rejected.append(f"{table}:SAMPLE_QUERY_FAILED")
            continue
        numeric_ok = False
        for row in rows:
            try:
                vals = [float(v) for v in row]
                if all(v == v for v in vals):
                    numeric_ok = True
                    break
            except Exception:
                continue
        if not numeric_ok:
            rejected.append(f"{table}:OHLC_COLUMNS_NOT_NUMERIC")
            continue
        return OhlcSchema(table, symbol_col, tf_col, ts_col, open_col, high_col, low_col, close_col), risks
    risks.append("OHLC_SCHEMA_NOT_FOUND")
    if rejected:
        risks.append("OHLC_SCHEMA_REJECTED:" + ",".join(rejected[:8]))
    return None, risks


def fetch_rows(conn: sqlite3.Connection, schema: OhlcSchema, symbol: str, timeframe: int, limit: int) -> List[Dict[str, Any]]:
    open_expr = qname(schema.open_col) if schema.open_col else qname(schema.close_col)
    sql = f'''
        SELECT {qname(schema.timestamp_col)} AS ts,
               {open_expr} AS open,
               {qname(schema.high_col)} AS high,
               {qname(schema.low_col)} AS low,
               {qname(schema.close_col)} AS close
        FROM {qname(schema.table)}
        WHERE UPPER({qname(schema.symbol_col)}) = UPPER(?)
          AND CAST({qname(schema.timeframe_col)} AS INTEGER) = ?
        ORDER BY {qname(schema.timestamp_col)} DESC
        LIMIT ?
    '''
    out: List[Dict[str, Any]] = []
    for ts, op, hi, lo, cl in conn.execute(sql, (symbol, timeframe, limit)).fetchall():
        dt = parse_dt(ts)
        try:
            out.append({
                "timestamp_utc": iso(dt), "dt": dt,
                "open": float(op) if op is not None else None,
                "high": float(hi), "low": float(lo), "close": float(cl),
            })
        except Exception:
            continue
    return list(reversed(out))


def rows_for_date(rows: Sequence[Dict[str, Any]], date_key: str) -> List[Dict[str, Any]]:
    return [r for r in rows if r.get("dt") and r["dt"].date().isoformat() == date_key]


def summarize(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [r for r in rows if r.get("high") is not None and r.get("low") is not None and r.get("close") is not None]
    if not valid:
        return {"open": None, "high": None, "low": None, "close": None, "rows": 0, "range": None, "close_position": "UNKNOWN", "start_utc": None, "end_utc": None}
    high = max(r["high"] for r in valid)
    low = min(r["low"] for r in valid)
    close = valid[-1]["close"]
    open_ = valid[0].get("open")
    rng = high - low
    if rng <= 0:
        pos = "UNKNOWN"
    else:
        ratio = (close - low) / rng
        pos = "HIGH_THIRD" if ratio >= 0.66 else "LOW_THIRD" if ratio <= 0.33 else "MIDDLE_THIRD"
    return {"open": round(open_, 6) if open_ is not None else None, "high": round(high, 6), "low": round(low, 6), "close": round(close, 6), "rows": len(valid), "range": round(rng, 6), "close_position": pos, "start_utc": valid[0].get("timestamp_utc"), "end_utc": valid[-1].get("timestamp_utc")}


def tolerance(symbol: str, price: float) -> float:
    return max(0.015, abs(price) * 0.00012) if symbol.upper().endswith("JPY") else max(0.00012, abs(price) * 0.00012)


def build_key_levels(symbol: str, current_rows: Sequence[Dict[str, Any]], previous_rows: Sequence[Dict[str, Any]], h1_rows: Sequence[Dict[str, Any]], h4_rows: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    current = summarize(current_rows)
    prev = summarize(previous_rows)
    levels: List[Dict[str, Any]] = []

    def add(name: str, price: Optional[float], source: str, ts: Optional[str]) -> None:
        if isinstance(price, (int, float)):
            levels.append({"name": name, "price": round(float(price), 6), "source": source, "timestamp_utc": ts})

    add("CURRENT_DAY_HIGH", current.get("high"), "M1_DERIVED_CURRENT_DAY", current.get("end_utc"))
    add("CURRENT_DAY_LOW", current.get("low"), "M1_DERIVED_CURRENT_DAY", current.get("end_utc"))
    add("PREVIOUS_DAY_HIGH", prev.get("high"), "M1_DERIVED_PREVIOUS_DAY", prev.get("end_utc"))
    add("PREVIOUS_DAY_LOW", prev.get("low"), "M1_DERIVED_PREVIOUS_DAY", prev.get("end_utc"))
    h1 = summarize(h1_rows[-12:])
    h4 = summarize(h4_rows[-6:])
    add("RECENT_H1_HIGH", h1.get("high"), "H1_RECENT_WINDOW", h1.get("end_utc"))
    add("RECENT_H1_LOW", h1.get("low"), "H1_RECENT_WINDOW", h1.get("end_utc"))
    add("RECENT_H4_HIGH", h4.get("high"), "H4_RECENT_WINDOW", h4.get("end_utc"))
    add("RECENT_H4_LOW", h4.get("low"), "H4_RECENT_WINDOW", h4.get("end_utc"))
    out, seen = [], set()
    for lvl in levels:
        key = (lvl["name"], lvl["price"])
        if key not in seen:
            out.append(lvl); seen.add(key)
    return out


def candle_crosses_level(c: Dict[str, Any], level: float, tol: float) -> bool:
    return c["low"] <= level + tol and c["high"] >= level - tol


def classify_level_interaction(symbol: str, current_rows: Sequence[Dict[str, Any]], level: Dict[str, Any]) -> Dict[str, Any]:
    price = float(level["price"])
    tol = tolerance(symbol, price)
    touches, pierce_up, pierce_down = [], [], []
    last_close = current_rows[-1]["close"] if current_rows else None

    for idx, c in enumerate(current_rows):
        if c.get("high") is None or c.get("low") is None or c.get("close") is None:
            continue
        if candle_crosses_level(c, price, tol):
            touches.append(idx)
        if c["high"] > price + tol:
            pierce_up.append(idx)
        if c["low"] < price - tol:
            pierce_down.append(idx)

    real_test = bool(touches)

    if not real_test:
        if last_close is not None and last_close > price + tol:
            state = "CONTEXT_ABOVE_LEVEL"
        elif last_close is not None and last_close < price - tol:
            state = "CONTEXT_BELOW_LEVEL"
        else:
            state = "UNTESTED"
    else:
        recent = current_rows[-10:] if len(current_rows) >= 10 else current_rows
        recent_above = sum(1 for c in recent if c.get("close") is not None and c["close"] > price + tol)
        recent_below = sum(1 for c in recent if c.get("close") is not None and c["close"] < price - tol)

        if last_close is not None and pierce_up and last_close < price - tol:
            state = "REJECTED_FROM_ABOVE"
        elif last_close is not None and pierce_down and last_close > price + tol:
            state = "REJECTED_FROM_BELOW"
        elif recent_above >= max(3, int(len(recent) * 0.6)):
            state = "ACCEPTED_ABOVE"
        elif recent_below >= max(3, int(len(recent) * 0.6)):
            state = "ACCEPTED_BELOW"
        elif pierce_up or pierce_down:
            state = "PIERCED"
        else:
            state = "TOUCHED"

    first_idx = touches[0] if touches else None
    first_ts = current_rows[first_idx]["timestamp_utc"] if first_idx is not None and first_idx < len(current_rows) else None

    robustness = 0.0
    if state in ("TOUCHED", "PIERCED"):
        robustness += 0.25
    if state.startswith("REJECTED") or state.startswith("ACCEPTED"):
        robustness += 0.35
    if len(touches) >= 2:
        robustness += 0.15
    if len(current_rows) >= 60:
        robustness += 0.15
    if str(level.get("source", "")).startswith(("H1", "H4", "M1_DERIVED_PREVIOUS")):
        robustness += 0.10
    if state.startswith("CONTEXT_"):
        robustness = min(robustness, 0.20)

    return {
        "level": level.get("name"),
        "price": price,
        "source": level.get("source"),
        "interaction_state": state,
        "first_touch_utc": first_ts,
        "touch_count": len(touches),
        "pierce_up_count": len(pierce_up),
        "pierce_down_count": len(pierce_down),
        "last_close": round(last_close, 6) if isinstance(last_close, (int, float)) else None,
        "tolerance": round(tol, 6),
        "robustness": round(min(1.0, robustness), 3),
    }

def dedupe_levels_by_price(symbol: str, levels: Sequence[Dict[str, Any]]) -> List[Dict[str, Any]]:
    clusters: List[Dict[str, Any]] = []

    def priority(level: Dict[str, Any]) -> int:
        name = str(level.get("name", ""))
        source = str(level.get("source", ""))
        if "PREVIOUS_DAY" in name:
            return 5
        if source.startswith("H4"):
            return 4
        if source.startswith("H1"):
            return 3
        if "CURRENT_DAY" in name:
            return 2
        return 1

    for lvl in levels:
        price = lvl.get("price")
        if not isinstance(price, (int, float)):
            continue
        tol = tolerance(symbol, float(price))
        matched = None
        for cluster in clusters:
            if abs(float(cluster["price"]) - float(price)) <= tol:
                matched = cluster
                break
        if matched is None:
            new_lvl = dict(lvl)
            new_lvl["aliases"] = [dict(lvl)]
            clusters.append(new_lvl)
        else:
            matched.setdefault("aliases", []).append(dict(lvl))
            if priority(lvl) > priority(matched):
                aliases = matched["aliases"]
                matched.clear()
                matched.update(dict(lvl))
                matched["aliases"] = aliases

    return clusters

def build_level_interactions(db_path: Path, symbol: str) -> Dict[str, Any]:
    technical_risks: List[str] = []
    conn = connect_ro(db_path)
    try:
        schema, risks = detect_ohlc_schema(conn)
        technical_risks.extend(risks)
        if schema is None:
            return {"timestamp_utc": now_utc_iso(), "symbol": symbol.upper(), "method": "DAILY_LEVEL_INTERACTION_V732", "schema_capability": "NO_OHLC", "levels": [], "interactions": [], "technical_risks": technical_risks}
        m1 = fetch_rows(conn, schema, symbol, 1, 12000)
        h1 = fetch_rows(conn, schema, symbol, 60, 300)
        h4 = fetch_rows(conn, schema, symbol, 240, 120)
    finally:
        conn.close()

    if not m1:
        technical_risks.append("NO_M1_OHLC_ROWS")
        return {"timestamp_utc": now_utc_iso(), "symbol": symbol.upper(), "method": "DAILY_LEVEL_INTERACTION_V732", "schema_capability": "OHLC_AVAILABLE", "schema": asdict(schema), "levels": [], "interactions": [], "technical_risks": technical_risks}

    latest_date = m1[-1]["dt"].date().isoformat() if m1[-1].get("dt") else None
    current_rows = rows_for_date(m1, latest_date) if latest_date else []
    prev_dates = sorted({r["dt"].date().isoformat() for r in m1 if r.get("dt") and r["dt"].date().isoformat() != latest_date})
    previous_rows = rows_for_date(m1, prev_dates[-1]) if prev_dates else []
    levels = dedupe_levels_by_price(symbol, build_key_levels(symbol, current_rows, previous_rows, h1, h4))
    interactions = [classify_level_interaction(symbol, current_rows, lvl) for lvl in levels]

    if len(current_rows) < 60: technical_risks.append("CURRENT_DAY_SAMPLE_THIN")
    if not previous_rows: technical_risks.append("PREVIOUS_DAY_REFERENCE_MISSING")
    if not any(i["interaction_state"] != "UNTESTED" for i in interactions): technical_risks.append("NO_LEVEL_INTERACTION_DETECTED")

    return {"timestamp_utc": now_utc_iso(), "symbol": symbol.upper(), "method": "DAILY_LEVEL_INTERACTION_V732", "schema_capability": "OHLC_AVAILABLE", "schema": asdict(schema), "reference_date_utc": latest_date, "day_summary": summarize(current_rows), "previous_day_summary": summarize(previous_rows), "levels": levels, "interactions": interactions, "technical_risks": technical_risks, "note": "Level interactions classify price behavior. They do not produce trade decisions."}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--output", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    symbol = args.symbol.upper()
    out = Path(args.output) if args.output else Path("output/dashboard_surface") / symbol / "daily_level_interaction.json"
    report = build_level_interactions(Path(args.db), symbol)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty: print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"DAILY_LEVEL_INTERACTION_OK | symbol={symbol} | interactions={len(report.get('interactions', []))} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
