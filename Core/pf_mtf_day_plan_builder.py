#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_mtf_day_plan_builder.py
PowerFlow V7.3 - MTF day plan builder.

Builds scenario language from HTF context, zone map, and existing PowerFlow surfaces.
No DB writes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


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


def _get_symbol_data_health(symbol: str, base_dir: str | Path = ".") -> Dict[str, Any]:
    health = load_json(Path(base_dir) / "output" / "data_health_monitor.json")
    return (health.get("symbols") or {}).get(symbol.upper(), {})


def _get_signal_adaptive(symbol: str, base_dir: str | Path = ".") -> Dict[str, Any]:
    all_profiles = load_json(Path(base_dir) / "output" / "dashboard_surface" / "signal_adaptive_profiles.json")
    # support dict by symbol or list of profiles
    if isinstance(all_profiles.get("symbols"), dict):
        return all_profiles["symbols"].get(symbol.upper(), {})
    for item in all_profiles.get("symbols", []) or all_profiles.get("profiles", []) or []:
        if str(item.get("symbol", "")).upper() == symbol.upper():
            return item
    return load_json(Path(base_dir) / "output" / "dashboard_surface" / symbol.upper() / "signal_adaptive_profile.json")


def _extract_driver(symbol: str, base_dir: str | Path = ".") -> str:
    cv = load_json(Path(base_dir) / "output" / "dashboard_surface" / "cross_validation.json")
    cvp = cv.get("cross_validation", cv)
    driver = cvp.get("driver") or cvp.get("dominant_driver")
    if driver:
        return str(driver)
    strength = cvp.get("currency_strength", {}) or cvp.get("true_strength", {})
    if strength:
        try:
            best = sorted(strength.items(), key=lambda kv: abs(float(kv[1].get("score", 0))), reverse=True)[0]
            return f"{best[0]}_{best[1].get('label','UNKNOWN')}"
        except Exception:
            pass
    return "DRIVER_UNKNOWN"


def _mtf_tf_status(symbol_health: Dict[str, Any], tf: int) -> str:
    tfp = (symbol_health.get("timeframes") or {}).get(str(tf), {})
    rows = int(tfp.get("row_count") or 0)
    age = tfp.get("age_minutes")
    if rows <= 0:
        return "NO_DATA"
    if age is not None and age > 60:
        return "STALE"
    if tf == 15 and rows < 20:
        return "THIN"
    if tf == 30 and rows < 10:
        return "THIN"
    if tf == 60 and rows < 8:
        return "THIN"
    return "READABLE"


def build_mtf_day_plan(
    symbol: str,
    htf_context: Dict[str, Any],
    zone_map: Dict[str, Any],
    base_dir: str | Path = ".",
) -> Dict[str, Any]:
    symbol = symbol.upper()
    risks: List[str] = []
    health = _get_symbol_data_health(symbol, base_dir)
    adaptive = _get_signal_adaptive(symbol, base_dir)
    driver = _extract_driver(symbol, base_dir)

    htf_label = htf_context.get("surface_label", "UNKNOWN")
    zone_behavior = zone_map.get("dominant_zone_behavior", "UNKNOWN")
    signal_mode = adaptive.get("mode") or adaptive.get("signal_mode") or adaptive.get("permission") or "UNKNOWN"

    h1_status = _mtf_tf_status(health, 60)
    m30_status = _mtf_tf_status(health, 30)
    m15_status = _mtf_tf_status(health, 15)
    for label, status in [("H1", h1_status), ("M30", m30_status), ("M15", m15_status)]:
        if status in ("NO_DATA", "STALE", "THIN"):
            risks.append(f"{symbol}_{label}_{status}")

    if zone_behavior in ("ZONE_REJECTED", "BREAK_AND_REINTEGRATE"):
        scenario_a = "REJECTION_AND_REINTEGRATION_CONTINUATION_WATCH"
        scenario_b = "SECOND_TEST_OR_ABSORPTION_CHECK"
        plan_bias = "WATCH_REJECTION_OR_TRAP_CONTINUATION"
    elif zone_behavior == "BREAK_AND_HOLD":
        scenario_a = "BREAK_AND_HOLD_RETEST_WATCH"
        scenario_b = "FAILED_BREAK_REINTEGRATION_WATCH"
        plan_bias = "WATCH_HOLD_OR_FAILED_BREAK"
    elif "ROTATION" in htf_label:
        scenario_a = "ROTATION_CONTINUATION_IF_M15_RELAY_APPEARS"
        scenario_b = "ROTATION_FAILURE_IF_M15_REJECTS"
        plan_bias = "WATCH_ROTATION_CONFIRMATION"
    elif "NEAR_REACTION_ZONE" in htf_label:
        scenario_a = "ZONE_REACTION_REJECTION"
        scenario_b = "ZONE_BREAK_AND_HOLD"
        plan_bias = "WATCH_REACTION_ZONE"
    else:
        scenario_a = "WAIT_FOR_ZONE_TEST_OR_SWEEP"
        scenario_b = "WAIT_FOR_COMPRESSION_RELEASE"
        plan_bias = "WAIT_FOR_MARKET_TO_SHOW_INTENTION"

    h1_plan = "WATCH_HTF_ZONE_REACTION" if h1_status != "NO_DATA" else "H1_CONTEXT_UNAVAILABLE"
    m30_plan = "MAP_INTRADAY_COMPRESSION_OR_ROTATION" if m30_status != "NO_DATA" else "M30_CONTEXT_UNAVAILABLE"
    m15_plan = "WAIT_REJECTION_ABSORPTION_OR_RELAY" if m15_status != "NO_DATA" else "M15_CONDITION_UNAVAILABLE"

    if "M1_ONLY" in str(signal_mode):
        risks.append("SIGNAL_ADAPTIVE_M1_ONLY_PLAN_REDUCED_TO_MICROFILM")
    if "THIN_HTF" in str(signal_mode):
        risks.append("HTF_THIN_SIGNAL_ADAPTIVE_REDUCES_STRUCTURE_CONFIDENCE")

    return {
        "timestamp_utc": utc_now_iso(),
        "method": "MTF_DAY_PLAN_BUILDER_V73",
        "symbol": symbol,
        "driver_context": driver,
        "signal_adaptive_mode": signal_mode,
        "mtf_status": {"H1": h1_status, "M30": m30_status, "M15": m15_status},
        "plan_bias": plan_bias,
        "h1": h1_plan,
        "m30": m30_plan,
        "m15": m15_plan,
        "scenario_a": scenario_a,
        "scenario_b": scenario_b,
        "invalidation_observation": "SCENARIO_INVALID_IF_M15_M5_PRICE_ACTION_CONTRADICTS_ZONE_REACTION",
        "technical_risks": sorted(set(risks)),
    }
