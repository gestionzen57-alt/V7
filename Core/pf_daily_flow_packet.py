#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.3.1 - Daily Flow Packet

Purpose:
    Build a concrete daily reading packet from the existing V7.3 layers:
    HTF context, MTF plan, LTF conditions, OHLC levels, sweeps, rejection,
    data health, signal adaptive profile and flow ontology.

Doctrine:
    - Read-only DB.
    - Perception only. No trading decision.
    - M1 is never censored, only qualified.
    - If OHLC is unavailable or thin, the packet exposes the technical risk
      instead of inventing levels.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


PREFERRED_TABLES = [
    "price_candles",
    "candles",
    "ohlc",
    "rates",
    "market_data",
    "force_snapshots",
]

SYMBOL_COL_CANDIDATES = ["symbol", "pair", "instrument"]
TF_COL_CANDIDATES = ["timeframe", "tf", "tf_minutes", "period"]
TS_COL_CANDIDATES = ["timestamp", "time", "datetime", "created_at", "ts", "bar_time"]
OPEN_COL_CANDIDATES = ["open", "o", "bid_open", "price_open"]
HIGH_COL_CANDIDATES = ["high", "h", "bid_high", "price_high"]
LOW_COL_CANDIDATES = ["low", "l", "bid_low", "price_low"]
CLOSE_COL_CANDIDATES = ["close", "c", "bid_close", "price_close", "price"]

DEFAULT_TIMEFRAMES = [1, 5, 15, 30, 60, 240, 1440]
DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]


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
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def open_ro(db_path: Path) -> sqlite3.Connection:
    # Absolute path improves Windows URI behavior when path contains spaces.
    resolved = db_path.resolve()
    return sqlite3.connect(f"file:{resolved}?mode=ro", uri=True)


def list_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(r[0]) for r in rows]


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    try:
        rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    except Exception:
        return []
    return [str(r[1]) for r in rows]


def find_col(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    """
    Strict schema matcher.

    V7.3.1 V4 fix:
    the previous matcher was too permissive and could map:
    - open -> symbol
    - low -> symbol
    - close -> created_at

    For OHLC, false positives are worse than missing values.
    We only accept exact case-insensitive matches.
    """
    lower_map = {str(c).lower(): c for c in columns}
    for cand in candidates:
        c = str(cand).lower()
        if c in lower_map:
            return lower_map[c]
    return None

def detect_ohlc_schema(conn: sqlite3.Connection) -> Tuple[Optional[OhlcSchema], List[str]]:
    """
    Detect a valid OHLC schema.

    Hard rule:
    - symbol/timeframe/timestamp required
    - high/low/close required
    - high/low/close must be numeric on a recent non-null sample
    - if open exists it must also be numeric
    - force_snapshots is not treated as OHLC unless it has real OHLC columns

    This prevents force/metadata tables from being misread as price candles.
    """
    risks: List[str] = []
    tables = list_tables(conn)
    ordered_tables = [t for t in PREFERRED_TABLES if t in tables] + [
        t for t in tables if t not in PREFERRED_TABLES
    ]

    rejected: List[str] = []

    for table in ordered_tables:
        cols = table_columns(conn, table)
        if not cols:
            continue

        symbol_col = find_col(cols, SYMBOL_COL_CANDIDATES)
        tf_col = find_col(cols, TF_COL_CANDIDATES)
        ts_col = find_col(cols, TS_COL_CANDIDATES)
        open_col = find_col(cols, OPEN_COL_CANDIDATES)
        high_col = find_col(cols, HIGH_COL_CANDIDATES)
        low_col = find_col(cols, LOW_COL_CANDIDATES)
        close_col = find_col(cols, CLOSE_COL_CANDIDATES)

        if not (symbol_col and tf_col and ts_col and high_col and low_col and close_col):
            continue

        sample_cols = [high_col, low_col, close_col]
        if open_col:
            sample_cols.append(open_col)

        try:
            select_expr = ", ".join(qname(c) for c in sample_cols)
            rows = conn.execute(
                f"SELECT {select_expr} FROM {qname(table)} "
                f"WHERE {qname(high_col)} IS NOT NULL "
                f"AND {qname(low_col)} IS NOT NULL "
                f"AND {qname(close_col)} IS NOT NULL "
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

        return OhlcSchema(
            table=table,
            symbol_col=symbol_col,
            timeframe_col=tf_col,
            timestamp_col=ts_col,
            open_col=open_col,
            high_col=high_col,
            low_col=low_col,
            close_col=close_col,
        ), risks

    risks.append("OHLC_SCHEMA_NOT_FOUND")
    if rejected:
        risks.append("OHLC_SCHEMA_REJECTED_FALSE_POSITIVES:" + ",".join(rejected[:8]))
    return None, risks

def qname(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def fetch_rows(
    conn: sqlite3.Connection,
    schema: OhlcSchema,
    symbol: str,
    timeframe: int,
    limit: int,
) -> List[Dict[str, Any]]:
    open_expr = qname(schema.open_col) if schema.open_col else qname(schema.close_col)
    sql = f"""
        SELECT
            {qname(schema.timestamp_col)} AS ts,
            {open_expr} AS open,
            {qname(schema.high_col)} AS high,
            {qname(schema.low_col)} AS low,
            {qname(schema.close_col)} AS close
        FROM {qname(schema.table)}
        WHERE UPPER({qname(schema.symbol_col)}) = UPPER(?)
          AND CAST({qname(schema.timeframe_col)} AS INTEGER) = ?
        ORDER BY {qname(schema.timestamp_col)} DESC
        LIMIT ?
    """
    rows = conn.execute(sql, (symbol, timeframe, limit)).fetchall()
    out: List[Dict[str, Any]] = []
    for ts, op, high, low, close in rows:
        dt = parse_dt(ts)
        try:
            out.append({
                "timestamp_utc": iso(dt),
                "dt": dt,
                "open": float(op) if op is not None else None,
                "high": float(high) if high is not None else None,
                "low": float(low) if low is not None else None,
                "close": float(close) if close is not None else None,
            })
        except Exception:
            continue
    # chronological order
    return list(reversed(out))


def rows_for_date(rows: Sequence[Dict[str, Any]], date_key: str) -> List[Dict[str, Any]]:
    return [r for r in rows if r.get("dt") and r["dt"].date().isoformat() == date_key]


def summarize_period(rows: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    valid = [
        r for r in rows
        if r.get("high") is not None and r.get("low") is not None and r.get("close") is not None
    ]
    if not valid:
        return {
            "open": None, "high": None, "low": None, "close": None,
            "start_utc": None, "end_utc": None, "rows": 0,
            "close_position": "UNKNOWN", "range": None,
        }

    high = max(r["high"] for r in valid)
    low = min(r["low"] for r in valid)
    first = valid[0]
    last = valid[-1]
    close = last["close"]
    op = first.get("open")
    rng = high - low if high is not None and low is not None else None

    if rng is None or rng <= 0 or close is None:
        pos = "UNKNOWN"
    else:
        ratio = (close - low) / rng
        if ratio >= 0.66:
            pos = "HIGH_THIRD"
        elif ratio <= 0.33:
            pos = "LOW_THIRD"
        else:
            pos = "MIDDLE_THIRD"

    return {
        "open": round(op, 6) if op is not None else None,
        "high": round(high, 6),
        "low": round(low, 6),
        "close": round(close, 6) if close is not None else None,
        "start_utc": valid[0].get("timestamp_utc"),
        "end_utc": valid[-1].get("timestamp_utc"),
        "rows": len(valid),
        "close_position": pos,
        "range": round(rng, 6) if rng is not None else None,
    }


def price_tolerance(symbol: str, price: Optional[float]) -> float:
    # Technical tolerance, not a trading threshold.
    if price is None:
        return 0.0
    if symbol.upper().endswith("JPY"):
        return max(0.03, abs(price) * 0.00025)
    return max(0.0003, abs(price) * 0.00025)


def level_obj(name: str, price: Optional[float], source: str, timestamp_utc: Optional[str] = None) -> Dict[str, Any]:
    return {
        "name": name,
        "price": round(price, 6) if isinstance(price, (int, float)) else None,
        "source": source,
        "timestamp_utc": timestamp_utc,
    }


def build_levels(
    symbol: str,
    current_day: Dict[str, Any],
    previous_day: Dict[str, Any],
    h4_rows: Sequence[Dict[str, Any]],
    h1_rows: Sequence[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    levels = [
        level_obj("CURRENT_DAY_HIGH", current_day.get("high"), "M1_DERIVED_CURRENT_DAY", current_day.get("end_utc")),
        level_obj("CURRENT_DAY_LOW", current_day.get("low"), "M1_DERIVED_CURRENT_DAY", current_day.get("end_utc")),
        level_obj("PREVIOUS_DAY_HIGH", previous_day.get("high"), "M1_DERIVED_PREVIOUS_DAY", previous_day.get("end_utc")),
        level_obj("PREVIOUS_DAY_LOW", previous_day.get("low"), "M1_DERIVED_PREVIOUS_DAY", previous_day.get("end_utc")),
    ]

    recent_h4 = [r for r in h4_rows if r.get("high") is not None and r.get("low") is not None]
    if recent_h4:
        h4_zone = summarize_period(recent_h4[-6:])
        levels.append(level_obj("RECENT_H4_HIGH", h4_zone.get("high"), "H4_RECENT_WINDOW", h4_zone.get("end_utc")))
        levels.append(level_obj("RECENT_H4_LOW", h4_zone.get("low"), "H4_RECENT_WINDOW", h4_zone.get("end_utc")))

    recent_h1 = [r for r in h1_rows if r.get("high") is not None and r.get("low") is not None]
    if recent_h1:
        h1_zone = summarize_period(recent_h1[-12:])
        levels.append(level_obj("RECENT_H1_HIGH", h1_zone.get("high"), "H1_RECENT_WINDOW", h1_zone.get("end_utc")))
        levels.append(level_obj("RECENT_H1_LOW", h1_zone.get("low"), "H1_RECENT_WINDOW", h1_zone.get("end_utc")))

    seen = set()
    unique = []
    for lvl in levels:
        if lvl.get("price") is None:
            continue
        key = (lvl["name"], lvl["price"])
        if key not in seen:
            unique.append(lvl)
            seen.add(key)
    return unique


def detect_tested_rejected_sweeps(
    symbol: str,
    current_rows: Sequence[Dict[str, Any]],
    levels: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    if not current_rows:
        return [], [], []

    day = summarize_period(current_rows)
    day_high = day.get("high")
    day_low = day.get("low")
    day_close = day.get("close")
    tested: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    sweeps: List[Dict[str, Any]] = []

    for lvl in levels:
        price = lvl.get("price")
        if price is None:
            continue
        tol = price_tolerance(symbol, price)
        name = lvl.get("name", "LEVEL")

        touched_high = day_high is not None and abs(day_high - price) <= tol
        touched_low = day_low is not None and abs(day_low - price) <= tol
        crossed_up = day_high is not None and day_high > price + tol
        crossed_down = day_low is not None and day_low < price - tol

        if touched_high or touched_low or crossed_up or crossed_down:
            tested.append({
                "level": name,
                "price": price,
                "source": lvl.get("source"),
                "test_type": "CROSSED" if (crossed_up or crossed_down) else "TOUCHED",
                "tolerance": round(tol, 6),
            })

        if crossed_up and day_close is not None and day_close < price:
            item = {
                "level": name,
                "price": price,
                "source": lvl.get("source"),
                "rejection_type": "UPSIDE_BREAK_REJECTED",
                "evidence": {
                    "day_high": day_high,
                    "day_close": day_close,
                },
            }
            rejected.append(item)
            if "HIGH" in name:
                sweeps.append({
                    "sweep_type": "HIGH_SWEEP_REJECTED",
                    "level": name,
                    "price": price,
                    "intent_hint": "SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP",
                    "evidence": item["evidence"],
                })

        if crossed_down and day_close is not None and day_close > price:
            item = {
                "level": name,
                "price": price,
                "source": lvl.get("source"),
                "rejection_type": "DOWNSIDE_BREAK_REJECTED",
                "evidence": {
                    "day_low": day_low,
                    "day_close": day_close,
                },
            }
            rejected.append(item)
            if "LOW" in name:
                sweeps.append({
                    "sweep_type": "LOW_SWEEP_REJECTED",
                    "level": name,
                    "price": price,
                    "intent_hint": "LONG_ACCUMULATION_OR_STOP_HUNT",
                    "evidence": item["evidence"],
                })

    return tested, rejected, sweeps


def pick_intent(
    day_summary: Dict[str, Any],
    sweeps: Sequence[Dict[str, Any]],
    rejected: Sequence[Dict[str, Any]],
    topdown_symbol: Dict[str, Any],
    signal_symbol: Dict[str, Any],
) -> str:
    if sweeps:
        high_sweeps = [s for s in sweeps if s.get("sweep_type") == "HIGH_SWEEP_REJECTED"]
        low_sweeps = [s for s in sweeps if s.get("sweep_type") == "LOW_SWEEP_REJECTED"]
        if high_sweeps and low_sweeps:
            return "DUAL_SWEEP_TRAP_OR_ROTATION"
        if high_sweeps:
            return "SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP"
        if low_sweeps:
            return "LONG_ACCUMULATION_OR_STOP_HUNT"

    close_position = day_summary.get("close_position")
    mode = str(signal_symbol.get("mode") or signal_symbol.get("signal_mode") or "").upper()
    flux = str(topdown_symbol.get("htf_flux") or topdown_symbol.get("flux") or "").upper()

    if close_position == "HIGH_THIRD":
        return "BUY_PRESSURE_OR_HIGH_ACCEPTANCE"
    if close_position == "LOW_THIRD":
        return "SELL_PRESSURE_OR_LOW_ACCEPTANCE"
    if "NEAR_REACTION_ZONE" in flux:
        return "REACTION_ZONE_WAIT_FOR_REJECTION_OR_ACCEPTANCE"
    if "THIN" in mode:
        return "TACTICAL_ACCUMULATION_WITH_THIN_STRUCTURE"
    return "BALANCED_INSIDE_RANGE_OR_PREP"


def build_prediction(intent: str, day_summary: Dict[str, Any], topdown_symbol: Dict[str, Any]) -> str:
    flux = str(topdown_symbol.get("htf_flux") or topdown_symbol.get("flux") or "UNKNOWN")
    pos = day_summary.get("close_position") or "UNKNOWN"

    if "SHORT_ACCUMULATION" in intent:
        return "WATCH_NEXT_SESSION_FOR_DOWNSIDE_ACCEPTANCE_AFTER_HIGH_SWEEP"
    if "LONG_ACCUMULATION" in intent:
        return "WATCH_NEXT_SESSION_FOR_UPSIDE_ACCEPTANCE_AFTER_LOW_SWEEP"
    if pos == "HIGH_THIRD":
        return "WATCH_CONTINUATION_OR_FAILED_HIGH_ACCEPTANCE"
    if pos == "LOW_THIRD":
        return "WATCH_CONTINUATION_OR_FAILED_LOW_ACCEPTANCE"
    if "REACTION_ZONE" in flux:
        return "WATCH_REACTION_ZONE_REJECTION_OR_BREAK_ACCEPTANCE"
    return "NO_DIRECTIONAL_PREDICTION_PACKET_NEEDS_NEXT_REACTION"


def extract_symbol_obj(container: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    """
    Schema-flex extractor for dashboard/output surfaces.

    Accepts:
    - {"symbols": {"GBPUSD": {...}}}
    - {"symbols": [{"symbol": "GBPUSD", ...}]}
    - {"symbols": ["GBPUSD", "EURUSD"]}  # summary-only list, ignored safely
    - {"profiles": {...}}
    - {"readers": {...}}
    - {"packets": {...}}
    - {"reports": [{"symbol": "..."}]}
    - direct {"GBPUSD": {...}}

    Never assumes list items are dicts.
    """
    if not isinstance(container, dict) or not container:
        return {}

    symbol_u = str(symbol).upper()

    symbols_obj = container.get("symbols")
    if isinstance(symbols_obj, dict):
        item = symbols_obj.get(symbol) or symbols_obj.get(symbol_u)
        return item if isinstance(item, dict) else {}

    if isinstance(symbols_obj, list):
        for item in symbols_obj:
            if isinstance(item, dict) and str(item.get("symbol", "")).upper() == symbol_u:
                return item
        return {}

    for key in ("profiles", "readers", "packets", "reports"):
        obj = container.get(key)
        if isinstance(obj, dict):
            item = obj.get(symbol) or obj.get(symbol_u)
            if isinstance(item, dict):
                return item
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and str(item.get("symbol", "")).upper() == symbol_u:
                    return item

    direct = container.get(symbol) or container.get(symbol_u)
    return direct if isinstance(direct, dict) else {}

def extract_topdown_symbol(topdown: Dict[str, Any], normalized: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    raw = extract_symbol_obj(topdown, symbol)
    norm = extract_symbol_obj(normalized, symbol)
    merged = dict(raw)
    merged.update({k: v for k, v in norm.items() if v is not None})
    return merged


def extract_ltf_conditions(signal_symbol: Dict[str, Any], data_health_symbol: Dict[str, Any]) -> List[str]:
    conditions: List[str] = []
    mode = str(signal_symbol.get("mode") or signal_symbol.get("signal_mode") or "")
    permission = str(signal_symbol.get("signal_permission") or "")
    if mode:
        conditions.append(mode)
    if permission:
        conditions.append(permission)
    status = str(data_health_symbol.get("status") or "")
    if status:
        conditions.append("DATA_" + status)

    issues = data_health_symbol.get("issues") or data_health_symbol.get("technical_risks") or []
    for issue in issues[:5]:
        conditions.append(str(issue))

    # Preserve order, remove duplicates.
    out = []
    seen = set()
    for c in conditions:
        if c and c not in seen:
            out.append(c)
            seen.add(c)
    return out


def build_daily_flow_packet(
    db_path: Path,
    symbol: str,
    output_root: Path = Path("output/dashboard_surface"),
) -> Dict[str, Any]:
    technical_risks: List[str] = []
    conn = open_ro(db_path)
    try:
        schema, schema_risks = detect_ohlc_schema(conn)
        technical_risks.extend(schema_risks)
        if schema is None:
            return {
                "timestamp_utc": now_utc_iso(),
                "symbol": symbol,
                "method": "DAILY_FLOW_PACKET_V731",
                "db_mode": "READ_ONLY",
                "schema_capability": "FORCE_ONLY_NO_OHLC",
                "daily_packet": {
                    "journal_levels": {},
                    "tested_levels": [],
                    "rejected_levels": [],
                    "sweep_candidates": [],
                    "intent_detected": "NO_OHLC_NO_LEVEL_READING",
                    "prediction_next_session": "NO_PREDICTION_WITHOUT_PRICE_STRUCTURE",
                    "ltf_conditions": [],
                    "trader_comparison_notes": [],
                },
                "technical_risks": technical_risks,
                "note": "Packet exposes missing structure. It does not invent levels.",
            }

        m1_rows = fetch_rows(conn, schema, symbol, 1, 10000)
        h1_rows = fetch_rows(conn, schema, symbol, 60, 200)
        h4_rows = fetch_rows(conn, schema, symbol, 240, 120)

    finally:
        conn.close()

    if not m1_rows:
        technical_risks.append("NO_M1_OHLC_ROWS")
        latest_date = None
        current_rows: List[Dict[str, Any]] = []
        previous_rows: List[Dict[str, Any]] = []
    else:
        latest_dt = m1_rows[-1].get("dt")
        latest_date = latest_dt.date().isoformat() if latest_dt else None
        current_rows = rows_for_date(m1_rows, latest_date) if latest_date else []
        previous_dates = sorted({
            r["dt"].date().isoformat()
            for r in m1_rows
            if r.get("dt") and r["dt"].date().isoformat() != latest_date
        })
        prev_date = previous_dates[-1] if previous_dates else None
        previous_rows = rows_for_date(m1_rows, prev_date) if prev_date else []

    day_summary = summarize_period(current_rows)
    previous_day_summary = summarize_period(previous_rows)
    levels = build_levels(symbol, day_summary, previous_day_summary, h4_rows, h1_rows)
    tested, rejected, sweeps = detect_tested_rejected_sweeps(symbol, current_rows, levels)

    topdown_raw = load_json(output_root / "topdown_market_reader.json")
    topdown_norm = load_json(output_root / "topdown_reader.json")
    data_health = load_json(output_root / "data_health.json")
    signal_adaptive = load_json(output_root / "signal_adaptive.json")
    ontology = load_json(output_root / "flow_ontology_cycle_summary.json")

    topdown_symbol = extract_topdown_symbol(topdown_raw, topdown_norm, symbol)
    data_health_symbol = extract_symbol_obj(data_health, symbol)
    signal_symbol = extract_symbol_obj(signal_adaptive, symbol)

    intent = pick_intent(day_summary, sweeps, rejected, topdown_symbol, signal_symbol)
    prediction = build_prediction(intent, day_summary, topdown_symbol)
    ltf_conditions = extract_ltf_conditions(signal_symbol, data_health_symbol)

    if day_summary.get("rows", 0) < 30:
        technical_risks.append("CURRENT_DAY_M1_SAMPLE_THIN")
    if previous_day_summary.get("rows", 0) == 0:
        technical_risks.append("PREVIOUS_DAY_REFERENCE_MISSING")
    if not levels:
        technical_risks.append("NO_KEY_LEVELS_BUILT")
    if not tested:
        technical_risks.append("NO_LEVEL_TEST_DETECTED_YET")

    packet = {
        "timestamp_utc": now_utc_iso(),
        "symbol": symbol.upper(),
        "method": "DAILY_FLOW_PACKET_V731",
        "db_mode": "READ_ONLY",
        "schema_capability": "OHLC_AVAILABLE",
        "schema": asdict(schema),
        "daily_packet": {
            "reference_date_utc": latest_date,
            "journal_levels": {
                "high_of_day": day_summary.get("high"),
                "low_of_day": day_summary.get("low"),
                "open": day_summary.get("open"),
                "close": day_summary.get("close"),
                "close_position": day_summary.get("close_position"),
                "range": day_summary.get("range"),
                "rows_m1_current_day": day_summary.get("rows"),
                "previous_day_high": previous_day_summary.get("high"),
                "previous_day_low": previous_day_summary.get("low"),
            },
            "key_levels": levels,
            "tested_levels": tested,
            "rejected_levels": rejected,
            "sweep_candidates": sweeps,
            "intent_detected": intent,
            "prediction_next_session": prediction,
            "htf_read": topdown_symbol.get("htf_flux") or topdown_symbol.get("flux") or topdown_symbol.get("htf_read") or "UNKNOWN",
            "mtf_day_plan": topdown_symbol.get("mtf_plan") or topdown_symbol.get("day_plan") or "WAIT_FOR_REACTION_OR_RETEST",
            "ltf_conditions": ltf_conditions,
            "ontology_context": extract_symbol_obj(ontology, symbol),
            "trader_comparison_notes": [
                "Fill manually: what I see on Weekly/Daily/H4.",
                "Fill manually: zones/rotations/correlation/coalition I disagree with.",
                "Fill next session: prediction result and lesson.",
            ],
        },
        "dashboard_summary": {
            "line_1": f"{symbol.upper()} | {intent}",
            "line_2": f"Close={day_summary.get('close_position')} | HTF={topdown_symbol.get('htf_flux') or topdown_symbol.get('flux') or 'UNKNOWN'}",
            "line_3": f"tested={len(tested)} rejected={len(rejected)} sweeps={len(sweeps)}",
        },
        "technical_risks": technical_risks,
        "note": "Daily packet names observable market behavior. It does not produce trade decisions.",
    }
    return packet


def write_packet(packet: Dict[str, Any], output: Path, pretty: bool = False) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(packet, indent=2 if pretty else None, ensure_ascii=False)
    output.write_text(text, encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build one PowerFlow V7.3.1 daily flow packet.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--output", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbol = args.symbol.upper()
    output = Path(args.output) if args.output else Path("output/dashboard_surface") / symbol / "daily_flow_packet.json"
    packet = build_daily_flow_packet(Path(args.db), symbol)
    write_packet(packet, output, pretty=args.pretty)

    if args.pretty:
        print(json.dumps(packet, indent=2, ensure_ascii=False))
    print(
        "DAILY_FLOW_PACKET_OK | "
        f"symbol={symbol} | intent={packet.get('daily_packet', {}).get('intent_detected')} | out={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
