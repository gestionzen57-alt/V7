#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_zone_rotation_mapper.py
PowerFlow V7.3 - zone and rotation mapper.

Detects candidate zones from OHLC data and labels tested/rejected/break behavior.
Read-only DB only.
"""
from __future__ import annotations

import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pf_price_schema_probe import probe_price_schema
from pf_htf_context_reader import _fetch_ohlc_candles

ZONE_TFS = {"daily": 1440, "h4": 240, "h1": 60, "m30": 30, "m15": 15}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _pivot_levels(candles: List[Dict[str, Any]], window: int = 2, max_levels: int = 12) -> List[Dict[str, Any]]:
    if len(candles) < (window * 2 + 3):
        return []
    levels: List[Dict[str, Any]] = []
    for i in range(window, len(candles) - window):
        c = candles[i]
        hs = [x["high"] for x in candles[i-window:i+window+1]]
        ls = [x["low"] for x in candles[i-window:i+window+1]]
        if c["high"] == max(hs):
            levels.append({"type": "RESISTANCE", "price": c["high"], "timestamp": c["timestamp"], "source": "PIVOT_HIGH"})
        if c["low"] == min(ls):
            levels.append({"type": "SUPPORT", "price": c["low"], "timestamp": c["timestamp"], "source": "PIVOT_LOW"})
    # keep most recent and de-duplicate close prices
    levels = levels[-max_levels * 3:]
    dedup: List[Dict[str, Any]] = []
    prices: List[float] = []
    price_range = max([c["high"] for c in candles]) - min([c["low"] for c in candles])
    tol = max(price_range * 0.002, 1e-9)
    for lev in reversed(levels):
        if all(abs(lev["price"] - p) > tol for p in prices):
            dedup.append(lev)
            prices.append(lev["price"])
        if len(dedup) >= max_levels:
            break
    return list(reversed(dedup))


def _test_reject_status(candles: List[Dict[str, Any]], level: Dict[str, Any], recent_n: int = 20) -> Dict[str, Any]:
    recent = candles[-min(recent_n, len(candles)):]
    if not recent:
        return {"status": "UNKNOWN", "touch_count": 0, "rejection_count": 0}
    price = float(level["price"])
    price_range = max(c["high"] for c in candles) - min(c["low"] for c in candles)
    tol = max(price_range * 0.0015, 1e-9)
    touches = 0
    rejections = 0
    breaks_hold = 0
    reintegrations = 0
    typ = level.get("type")
    for c in recent:
        touched = c["low"] - tol <= price <= c["high"] + tol
        if touched:
            touches += 1
        if typ == "RESISTANCE":
            if c["high"] > price + tol and c["close"] < price:
                rejections += 1
                reintegrations += 1
            if c["close"] > price + tol:
                breaks_hold += 1
        elif typ == "SUPPORT":
            if c["low"] < price - tol and c["close"] > price:
                rejections += 1
                reintegrations += 1
            if c["close"] < price - tol:
                breaks_hold += 1
    if rejections > 0:
        status = "ZONE_REJECTED" if touches else "BREAK_AND_REINTEGRATE"
    elif breaks_hold >= 2:
        status = "BREAK_AND_HOLD"
    elif touches > 0:
        status = "ZONE_TESTED"
    else:
        status = "UNTOUCHED_RECENTLY"
    return {
        "status": status,
        "touch_count": touches,
        "rejection_count": rejections,
        "break_hold_count": breaks_hold,
        "reintegrate_count": reintegrations,
        "tolerance": tol,
    }


def _rotation_from_zones(candles: List[Dict[str, Any]]) -> str:
    if len(candles) < 12:
        return "UNKNOWN_LOW_SAMPLE"
    closes = [c["close"] for c in candles[-40:]]
    highs = [c["high"] for c in candles[-40:]]
    lows = [c["low"] for c in candles[-40:]]
    rng = max(highs) - min(lows)
    if rng <= 0:
        return "UNKNOWN_FLAT_RANGE"
    first = statistics.mean(closes[:max(3, len(closes)//4)])
    last = statistics.mean(closes[-max(3, len(closes)//4):])
    delta = (last - first) / rng
    if delta > 0.35:
        return "ROTATION_UP_BUILDING"
    if delta < -0.35:
        return "ROTATION_DOWN_BUILDING"
    # contraction hint: last 10 range smaller than full average range
    ranges = [c["high"] - c["low"] for c in candles[-20:]]
    if ranges and statistics.mean(ranges[-5:]) < statistics.mean(ranges) * 0.7:
        return "ROTATION_COMPRESSING"
    return "ROTATION_NEUTRAL"


def build_zone_rotation_map(
    db_path: str | Path,
    symbol: str,
    schema: Optional[Dict[str, Any]] = None,
    lookback: int = 250,
) -> Dict[str, Any]:
    symbol = symbol.upper()
    schema = schema or probe_price_schema(db_path, symbols=[symbol])
    risks: List[str] = []
    out: Dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "method": "ZONE_ROTATION_MAPPER_V73",
        "symbol": symbol,
        "db_mode": "READ_ONLY",
        "zone_rotation": {},
        "dominant_zone_behavior": "UNKNOWN",
        "technical_risks": risks,
    }
    if not schema.get("primary_ohlc_table"):
        risks.append("NO_OHLC_PRICE_DATA_ZONE_READING_LIMITED")
        out["dominant_zone_behavior"] = "NO_OHLC_ZONE_MAP_UNAVAILABLE"
        return out

    behavior_votes: List[str] = []
    for label, tf in ZONE_TFS.items():
        candles = _fetch_ohlc_candles(db_path, schema, symbol, tf, limit=lookback)
        if not candles:
            out["zone_rotation"][label] = {"timeframe": tf, "status": "NO_DATA", "levels": [], "rotation": "UNKNOWN"}
            risks.append(f"{label.upper()}_NO_OHLC_DATA")
            continue
        levels = _pivot_levels(candles)
        enriched: List[Dict[str, Any]] = []
        for lev in levels:
            status = _test_reject_status(candles, lev)
            enriched.append({**lev, **status})
            if status.get("status") in ("ZONE_REJECTED", "BREAK_AND_REINTEGRATE", "BREAK_AND_HOLD", "ZONE_TESTED"):
                behavior_votes.append(status["status"])
        rotation = _rotation_from_zones(candles)
        out["zone_rotation"][label] = {
            "timeframe": tf,
            "status": "READABLE",
            "rows_used": len(candles),
            "latest_timestamp": candles[-1]["timestamp"],
            "rotation": rotation,
            "levels": enriched,
        }
    if behavior_votes:
        # priority: rejection/reintegration more important than simple test
        for candidate in ["BREAK_AND_REINTEGRATE", "ZONE_REJECTED", "BREAK_AND_HOLD", "ZONE_TESTED"]:
            if candidate in behavior_votes:
                out["dominant_zone_behavior"] = candidate
                break
    else:
        out["dominant_zone_behavior"] = "NO_RECENT_ZONE_INTERACTION_DETECTED"
    out["technical_risks"] = sorted(set(risks))
    return out
