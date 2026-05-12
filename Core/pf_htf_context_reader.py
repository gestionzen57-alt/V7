#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_htf_context_reader.py
PowerFlow V7.3 - HTF_CONTEXT reader.

Reads Weekly/Daily/H4 when OHLC exists; otherwise returns a qualified limitation.
No DB writes.
"""
from __future__ import annotations

import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pf_price_schema_probe import (
    connect_readonly,
    probe_price_schema,
    quote_ident,
    timeframe_where_clause,
    symbol_where_clause,
)

HTF_TIMEFRAMES = {"weekly": 10080, "daily": 1440, "h4": 240}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _to_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _fetch_ohlc_candles(db_path: str | Path, schema: Dict[str, Any], symbol: str, timeframe: int, limit: int = 300) -> List[Dict[str, Any]]:
    table = (schema.get("primary_ohlc_table") or {})
    cols = table.get("detected_columns") or {}
    if not table or not cols:
        return []
    t = table["table"]
    sc = cols.get("symbol")
    tfc = cols.get("timeframe")
    tc = cols.get("timestamp")
    oc = cols.get("open")
    hc = cols.get("high")
    lc = cols.get("low")
    cc = cols.get("close")
    if not (sc and tfc and tc and hc and lc and cc):
        return []

    fields = [tc, hc, lc, cc]
    if oc:
        fields.insert(1, oc)
    select_fields = ", ".join(quote_ident(x) for x in fields)
    tf_clause, tf_params = timeframe_where_clause(tfc, timeframe)
    sym_clause, sym_params = symbol_where_clause(sc, symbol)
    sql = (
        f"SELECT {select_fields} FROM {quote_ident(t)} "
        f"WHERE {sym_clause} AND {tf_clause} "
        f"ORDER BY {quote_ident(tc)} DESC LIMIT ?"
    )
    with connect_readonly(db_path) as conn:
        rows = conn.execute(sql, sym_params + tf_params + [limit]).fetchall()
    candles: List[Dict[str, Any]] = []
    for r in reversed(rows):
        item = {
            "timestamp": r[tc],
            "open": _to_float(r[oc]) if oc else None,
            "high": _to_float(r[hc]),
            "low": _to_float(r[lc]),
            "close": _to_float(r[cc]),
        }
        if item["high"] is not None and item["low"] is not None and item["close"] is not None:
            if item["open"] is None:
                item["open"] = item["close"]
            candles.append(item)
    return candles


def _slope(values: List[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    den = sum((x - mx) ** 2 for x in xs) or 1.0
    num = sum((x - mx) * (y - my) for x, y in zip(xs, values))
    return num / den


def _classify_close_position(ratio: Optional[float]) -> str:
    if ratio is None:
        return "UNKNOWN"
    if ratio >= 0.70:
        return "UPPER_RANGE"
    if ratio <= 0.30:
        return "LOWER_RANGE"
    return "MID_RANGE"


def _analyze_candles(label: str, timeframe: int, candles: List[Dict[str, Any]]) -> Dict[str, Any]:
    technical_risks: List[str] = []
    if not candles:
        return {
            "timeframe": timeframe,
            "status": "NO_DATA",
            "zone_status": "UNKNOWN",
            "trend_state": "UNKNOWN",
            "rotation": "UNKNOWN",
            "rejection": "UNKNOWN",
            "provenance": "UNKNOWN",
            "angle_state": "UNKNOWN",
            "speed_state": "UNKNOWN",
            "close_position": "UNKNOWN",
            "technical_risks": [f"{label.upper()}_NO_OHLC_DATA"],
        }

    lookback = candles[-min(len(candles), 80):]
    highs = [c["high"] for c in lookback]
    lows = [c["low"] for c in lookback]
    closes = [c["close"] for c in lookback]
    last = lookback[-1]
    hi = max(highs)
    lo = min(lows)
    rng = hi - lo
    close = last["close"]
    ratio = None if rng <= 0 else (close - lo) / rng
    close_position = _classify_close_position(ratio)
    near_upper = bool(ratio is not None and ratio >= 0.85)
    near_lower = bool(ratio is not None and ratio <= 0.15)
    if near_upper:
        zone_status = "NEAR_MAJOR_HIGH_ZONE"
    elif near_lower:
        zone_status = "NEAR_MAJOR_LOW_ZONE"
    else:
        zone_status = "INSIDE_HTF_RANGE"

    # Trend and angle from recent closes, normalized by range.
    recent = closes[-min(len(closes), 12):]
    older = closes[-min(len(closes), 36):-min(len(closes), 12)] if len(closes) > 16 else []
    raw_slope = _slope(recent)
    norm_slope = 0.0 if rng <= 0 else raw_slope / rng * len(recent)
    if norm_slope > 0.12:
        angle_state = "ANGLE_UP_ACCELERATING"
        trend_state = "NEW_TREND_UP_ATTEMPT" if older else "UP_PRESSURE_VISIBLE"
    elif norm_slope < -0.12:
        angle_state = "ANGLE_DOWN_ACCELERATING"
        trend_state = "NEW_TREND_DOWN_ATTEMPT" if older else "DOWN_PRESSURE_VISIBLE"
    else:
        angle_state = "ANGLE_FLAT_OR_ABSORBED"
        trend_state = "RANGE_OR_ABSORPTION"

    # Rotation based on movement from first third to last third of lookback.
    if len(closes) >= 12 and rng > 0:
        start_avg = statistics.mean(closes[:max(3, len(closes)//4)])
        end_avg = statistics.mean(closes[-max(3, len(closes)//4):])
        delta = (end_avg - start_avg) / rng
        if delta > 0.25:
            rotation = "ROTATION_UP_BUILDING"
        elif delta < -0.25:
            rotation = "ROTATION_DOWN_BUILDING"
        else:
            rotation = "ROTATION_NEUTRAL_OR_RANGE"
    else:
        rotation = "UNKNOWN"
        technical_risks.append(f"{label.upper()}_LOW_SAMPLE_FOR_ROTATION")

    # Rejection: latest candle wicked beyond zone and closed back inside.
    body_hi = max(last.get("open") or close, close)
    body_lo = min(last.get("open") or close, close)
    upper_wick = last["high"] - body_hi
    lower_wick = body_lo - last["low"]
    avg_range = statistics.mean([(c["high"] - c["low"]) for c in lookback if c["high"] >= c["low"]] or [0.0])
    if avg_range > 0 and upper_wick > avg_range * 0.6 and close < body_hi:
        rejection = "UPPER_WICK_REJECTION"
    elif avg_range > 0 and lower_wick > avg_range * 0.6 and close > body_lo:
        rejection = "LOWER_WICK_REJECTION"
    else:
        rejection = "NONE_VISIBLE"

    abs_moves = [abs(closes[i] - closes[i-1]) for i in range(1, len(closes))]
    avg_move = statistics.mean(abs_moves) if abs_moves else 0.0
    recent_move = abs(closes[-1] - closes[-min(len(closes), 5)]) if len(closes) >= 5 else 0.0
    if avg_move <= 0:
        speed_state = "UNKNOWN"
    elif recent_move > avg_move * 6:
        speed_state = "FAST_FROM_PRIOR_ZONE"
    elif recent_move < avg_move * 1.5:
        speed_state = "SLOW_OR_ABSORBED"
    else:
        speed_state = "NORMAL_DISPLACEMENT"

    # Provenance from last local extreme.
    recent_lows = lows[-min(20, len(lows)):]
    recent_highs = highs[-min(20, len(highs)):]
    idx_low = recent_lows.index(min(recent_lows)) if recent_lows else 0
    idx_high = recent_highs.index(max(recent_highs)) if recent_highs else 0
    if close_position == "UPPER_RANGE" and idx_low < len(recent_lows) // 2:
        provenance = "FROM_LOWER_ZONE_REJECTION_OR_ROTATION"
    elif close_position == "LOWER_RANGE" and idx_high < len(recent_highs) // 2:
        provenance = "FROM_UPPER_ZONE_REJECTION_OR_ROTATION"
    else:
        provenance = "INSIDE_RANGE_PROVENANCE_MIXED"

    return {
        "timeframe": timeframe,
        "status": "READABLE",
        "rows_used": len(candles),
        "latest_timestamp": last["timestamp"],
        "range_high": hi,
        "range_low": lo,
        "last_close": close,
        "close_position_ratio": None if ratio is None else round(ratio, 4),
        "close_position": close_position,
        "zone_status": zone_status,
        "trend_state": trend_state,
        "rotation": rotation,
        "rejection": rejection,
        "provenance": provenance,
        "angle_state": angle_state,
        "speed_state": speed_state,
        "technical_risks": technical_risks,
    }


def build_htf_context(
    db_path: str | Path,
    symbol: str,
    schema: Optional[Dict[str, Any]] = None,
    lookback: int = 300,
) -> Dict[str, Any]:
    symbol = symbol.upper()
    schema = schema or probe_price_schema(db_path, symbols=[symbol])
    technical_risks: List[str] = []
    out: Dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "method": "HTF_CONTEXT_READER_V73",
        "symbol": symbol,
        "db_mode": "READ_ONLY",
        "price_reading_capability": schema.get("price_reading_capability"),
        "htf_context": {},
        "surface_label": "UNKNOWN",
        "technical_risks": technical_risks,
    }
    if not schema.get("primary_ohlc_table"):
        technical_risks.append("NO_OHLC_PRICE_DATA_HTF_CONTEXT_LIMITED")
        out["surface_label"] = "HTF_CONTEXT_NOT_READABLE_NO_OHLC"
        for label, tf in HTF_TIMEFRAMES.items():
            out["htf_context"][label] = {
                "timeframe": tf,
                "status": "NO_OHLC",
                "zone_status": "UNKNOWN",
                "trend_state": "UNKNOWN",
                "rotation": "UNKNOWN",
                "technical_risks": ["NO_OHLC_PRICE_DATA"],
            }
        return out

    for label, tf in HTF_TIMEFRAMES.items():
        candles = _fetch_ohlc_candles(db_path, schema, symbol, tf, limit=lookback)
        out["htf_context"][label] = _analyze_candles(label, tf, candles)
        technical_risks.extend(out["htf_context"][label].get("technical_risks", []))

    readable = [v for v in out["htf_context"].values() if v.get("status") == "READABLE"]
    if not readable:
        out["surface_label"] = "HTF_CONTEXT_NO_DATA"
    else:
        rotations = [v.get("rotation") for v in readable]
        zones = [v.get("zone_status") for v in readable]
        if any("ROTATION" in str(r) and "BUILDING" in str(r) for r in rotations):
            out["surface_label"] = "HTF_ROTATION_BUILDING"
        elif any(str(z).startswith("NEAR_MAJOR") for z in zones):
            out["surface_label"] = "HTF_NEAR_REACTION_ZONE"
        else:
            out["surface_label"] = "HTF_INSIDE_RANGE_OR_NEUTRAL"
    # de-duplicate risks
    out["technical_risks"] = sorted(set(technical_risks))
    return out
