#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_ltf_execution_condition_reader.py
PowerFlow V7.3 - LTF execution condition reader.

Reads M15/M5/M1 conditions, sweeps/reintegrations if OHLC exists, plus existing node/energy/signal adaptive surfaces.
It does not produce orders. It qualifies attention conditions.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from pf_price_schema_probe import probe_price_schema
from pf_htf_context_reader import _fetch_ohlc_candles


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_symbol_surface(symbol: str, filename: str, base_dir: str | Path = ".") -> Dict[str, Any]:
    return load_json(Path(base_dir) / "output" / "dashboard_surface" / symbol.upper() / filename)


def _detect_recent_sweep(candles: List[Dict[str, Any]], lookback_level: int = 120, trigger_window: int = 20) -> Dict[str, Any]:
    if len(candles) < max(lookback_level // 2, trigger_window + 20):
        return {"sweep_state": "NO_SWEEP_DETECTABLE_LOW_SAMPLE", "sweeps": []}
    base = candles[-min(len(candles), lookback_level):-trigger_window]
    recent = candles[-trigger_window:]
    if not base or not recent:
        return {"sweep_state": "NO_SWEEP_DETECTABLE_LOW_SAMPLE", "sweeps": []}
    prev_high = max(c["high"] for c in base)
    prev_low = min(c["low"] for c in base)
    price_range = max(c["high"] for c in candles[-lookback_level:]) - min(c["low"] for c in candles[-lookback_level:])
    tol = max(price_range * 0.0008, 1e-9)
    sweeps: List[Dict[str, Any]] = []
    for c in recent:
        if c["high"] > prev_high + tol and c["close"] < prev_high:
            sweeps.append({
                "type": "HIGH_SWEEP_REINTEGRATION",
                "level": prev_high,
                "timestamp_utc": c["timestamp"],
                "close": c["close"],
                "intention_candidate": "ACCUMULATION_DOWN_OR_TRAP_UP",
            })
        if c["low"] < prev_low - tol and c["close"] > prev_low:
            sweeps.append({
                "type": "LOW_SWEEP_REINTEGRATION",
                "level": prev_low,
                "timestamp_utc": c["timestamp"],
                "close": c["close"],
                "intention_candidate": "ACCUMULATION_UP_OR_TRAP_DOWN",
            })
    if sweeps:
        return {"sweep_state": "LIQUIDITY_SWEEP_CANDIDATE", "sweeps": sweeps[-5:]}
    return {"sweep_state": "NO_RECENT_SWEEP", "sweeps": []}


def _extract_highest_node(node: Dict[str, Any]) -> str:
    candidates = []
    for key in ["highest_level", "level", "status"]:
        if node.get(key):
            candidates.append(str(node.get(key)))
    for n in node.get("nodes", []) or []:
        for key in ["level", "heat_level", "node_level"]:
            if n.get(key):
                candidates.append(str(n.get(key)))
    if any("HOT" in c.upper() for c in candidates):
        return "HOT_NODE"
    if any("CONFIRMED" in c.upper() for c in candidates):
        return "NODE_CONFIRMED"
    if candidates:
        return candidates[0]
    return "UNKNOWN"


def _relay_quality(node: Dict[str, Any], energy: Dict[str, Any]) -> str:
    paths = [
        node.get("capture_quality", {}).get("relay_sample_state"),
        node.get("capture_quality", {}).get("m5_role_capture"),
        node.get("telegram_gating", {}).get("relay_sample_state"),
        node.get("energy_release_alignment", {}).get("relay_sample_state"),
        energy.get("relay_quality"),
        energy.get("m5_role_capture"),
    ]
    for p in paths:
        if p:
            s = str(p).upper()
            if "CLEAN" in s:
                return "M5_RELAY_CLEAN"
            if "THIN" in s:
                return "M5_RELAY_THIN"
            if "MISSING" in s:
                return "M5_RELAY_MISSING"
    return "M5_RELAY_UNKNOWN"


def build_ltf_execution_conditions(
    db_path: str | Path,
    symbol: str,
    schema: Optional[Dict[str, Any]] = None,
    base_dir: str | Path = ".",
) -> Dict[str, Any]:
    symbol = symbol.upper()
    schema = schema or probe_price_schema(db_path, symbols=[symbol])
    risks: List[str] = []
    node = _read_symbol_surface(symbol, "node.json", base_dir)
    energy = _read_symbol_surface(symbol, "energy.json", base_dir)
    m1_context = _read_symbol_surface(symbol, "m1_context_score.json", base_dir)
    adaptive = _read_symbol_surface(symbol, "signal_adaptive_profile.json", base_dir)
    node_level = _extract_highest_node(node)
    relay = _relay_quality(node, energy)

    ltf: Dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "method": "LTF_EXECUTION_CONDITION_READER_V73",
        "symbol": symbol,
        "m15": "CONDITION_UNKNOWN",
        "m5": relay,
        "m1": "MICROFILM_UNKNOWN",
        "node_level": node_level,
        "sweep_state": "UNKNOWN",
        "sweeps": [],
        "entry_attention": "WAIT",
        "technical_risks": risks,
    }

    # M1 status from node / adaptive / context.
    adaptive_mode = adaptive.get("mode") or adaptive.get("signal_permission") or ""
    if "M1" in str(adaptive_mode).upper() or node_level in ("HOT_NODE", "NODE_CONFIRMED"):
        ltf["m1"] = "M1_MICROFILM_ACTIVE"
    else:
        ltf["m1"] = "M1_MICROFILM_NOT_CONFIRMED"

    if relay == "M5_RELAY_CLEAN":
        ltf["m5"] = "M5_RELAY_CLEAN"
    elif relay == "M5_RELAY_THIN":
        ltf["m5"] = "M5_RELAY_THIN"
    elif relay == "M5_RELAY_MISSING":
        ltf["m5"] = "M5_RELAY_MISSING"
        risks.append("M5_RELAY_MISSING_LTF_CONDITION_FRAGILE")

    if schema.get("primary_ohlc_table"):
        m1_candles = _fetch_ohlc_candles(db_path, schema, symbol, 1, limit=180)
        m15_candles = _fetch_ohlc_candles(db_path, schema, symbol, 15, limit=80)
        sweep = _detect_recent_sweep(m1_candles or m15_candles)
        ltf["sweep_state"] = sweep["sweep_state"]
        ltf["sweeps"] = sweep["sweeps"]
        if m15_candles and len(m15_candles) >= 3:
            last = m15_candles[-1]
            prev = m15_candles[-2]
            if last["close"] > prev["high"]:
                ltf["m15"] = "M15_BREAK_PRESSURE_VISIBLE"
            elif last["close"] < prev["low"]:
                ltf["m15"] = "M15_BREAK_PRESSURE_DOWN_VISIBLE"
            elif sweep["sweeps"]:
                ltf["m15"] = "M15_REINTEGRATION_OR_REJECTION_WATCH"
            else:
                ltf["m15"] = "M15_CONDITION_NOT_CONFIRMED"
        else:
            ltf["m15"] = "M15_LOW_SAMPLE_OR_NO_OHLC"
            risks.append("M15_LOW_SAMPLE_OR_NO_OHLC")
    else:
        ltf["sweep_state"] = "NO_OHLC_SWEEP_UNAVAILABLE"
        ltf["m15"] = "M15_PRICE_ACTION_UNAVAILABLE_NO_OHLC"
        risks.append("NO_OHLC_LTF_SWEEP_READING_LIMITED")

    if node_level == "HOT_NODE" and relay == "M5_RELAY_CLEAN":
        ltf["entry_attention"] = "HOT_ATTENTION_CONDITION_PRESENT"
    elif ltf["sweep_state"] == "LIQUIDITY_SWEEP_CANDIDATE" and ltf["m1"] == "M1_MICROFILM_ACTIVE":
        ltf["entry_attention"] = "WATCH_SWEEP_REINTEGRATION_CONDITION"
    elif ltf["m1"] == "M1_MICROFILM_ACTIVE":
        ltf["entry_attention"] = "WATCH_M1_ACTIVE_CONDITION_FRAGILE"
    else:
        ltf["entry_attention"] = "WAIT_CONDITION_ABSENT"
    ltf["technical_risks"] = sorted(set(risks))
    return ltf
