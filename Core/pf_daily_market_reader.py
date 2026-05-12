#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_daily_market_reader.py
PowerFlow V7.3 - Top-down daily market reader.

Assembles HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS.
Creates a machine-readable JSON and a trader-friendly daily journal markdown.
No DB writes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from pf_price_schema_probe import probe_price_schema
from pf_htf_context_reader import build_htf_context, _fetch_ohlc_candles
from pf_zone_rotation_mapper import build_zone_rotation_map
from pf_mtf_day_plan_builder import build_mtf_day_plan, load_json
from pf_ltf_execution_condition_reader import build_ltf_execution_conditions


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def today_utc_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        return float(v)
    except Exception:
        return None


def _classify_close_position(ratio: Optional[float]) -> str:
    if ratio is None:
        return "UNKNOWN"
    if ratio >= 0.70:
        return "UPPER_RANGE"
    if ratio <= 0.30:
        return "LOWER_RANGE"
    return "MID_RANGE"


def _daily_profile_from_ohlc(db_path: str | Path, symbol: str, schema: Dict[str, Any], date: str) -> Dict[str, Any]:
    # Prefer M1, then M5, then M15 for daily profile.
    candles: List[Dict[str, Any]] = []
    tf_used = None
    for tf in [1, 5, 15, 30, 60, 240, 1440]:
        all_candles = _fetch_ohlc_candles(db_path, schema, symbol, tf, limit=5000)
        # date matching by timestamp prefix; tolerant for ISO strings.
        day_candles = [c for c in all_candles if str(c.get("timestamp", ""))[:10] == date]
        if day_candles:
            candles = day_candles
            tf_used = tf
            break
    if not candles:
        return {
            "status": "NO_OHLC_DAY_PROFILE",
            "date": date,
            "timeframe_used": None,
            "high": None,
            "low": None,
            "close": None,
            "close_position": "UNKNOWN",
            "close_position_ratio": None,
            "technical_risks": ["NO_OHLC_CANDLES_FOR_DATE"],
        }
    hi = max(c["high"] for c in candles)
    lo = min(c["low"] for c in candles)
    close = candles[-1]["close"]
    rng = hi - lo
    ratio = None if rng <= 0 else (close - lo) / rng
    return {
        "status": "READABLE",
        "date": date,
        "timeframe_used": tf_used,
        "rows_used": len(candles),
        "first_timestamp": candles[0]["timestamp"],
        "last_timestamp": candles[-1]["timestamp"],
        "high": hi,
        "low": lo,
        "close": close,
        "close_position": _classify_close_position(ratio),
        "close_position_ratio": None if ratio is None else round(ratio, 4),
        "technical_risks": [],
    }


def _read_cross_driver(symbol: str, base_dir: str | Path = ".") -> Dict[str, Any]:
    path = Path(base_dir) / "output" / "dashboard_surface" / "cross_validation.json"
    cv = load_json(path)
    cvp = cv.get("cross_validation", cv)
    return {
        "driver": cvp.get("driver") or cvp.get("dominant_driver") or "UNKNOWN",
        "confidence": cvp.get("confidence"),
        "timestamp_utc": cvp.get("timestamp") or cvp.get("timestamp_utc"),
        "source": str(path),
    }


def _read_ontology(symbol: str, base_dir: str | Path = ".") -> Dict[str, Any]:
    paths = [
        Path(base_dir) / "output" / "dashboard_surface" / symbol.upper() / "flow_ontology_report.json",
        Path(base_dir) / "output" / f"flow_ontology_report_{symbol.upper()}.json",
        Path(base_dir) / "output" / "dashboard_surface" / "flow_ontology_report.json",
    ]
    for p in paths:
        data = load_json(p)
        if data:
            cats = data.get("alerts_by_category", {})
            dominant = "UNKNOWN"
            if cats:
                dominant = max(cats.items(), key=lambda kv: kv[1])[0]
            return {
                "dominant_category": dominant,
                "ontology_coverage": data.get("ontology_coverage"),
                "alerts_total": data.get("alerts_total"),
                "source": str(p),
            }
    return {"dominant_category": "UNKNOWN", "ontology_coverage": None, "alerts_total": None, "source": None}


def _surface_reading(symbol: str, htf: Dict[str, Any], mtf: Dict[str, Any], ltf: Dict[str, Any], day_profile: Dict[str, Any], cross_driver: Dict[str, Any], ontology: Dict[str, Any]) -> Dict[str, Any]:
    flux = htf.get("surface_label", "UNKNOWN")
    zone = "UNKNOWN"
    for tf_label in ["daily", "h4", "weekly"]:
        ctx = (htf.get("htf_context") or {}).get(tf_label, {})
        zs = ctx.get("zone_status")
        if zs and zs != "UNKNOWN":
            zone = zs
            break
    condition = ltf.get("entry_attention", "WAIT")
    driver = cross_driver.get("driver", "UNKNOWN")
    fragility = sorted(set(
        (htf.get("technical_risks") or [])
        + (mtf.get("technical_risks") or [])
        + (ltf.get("technical_risks") or [])
        + (day_profile.get("technical_risks") or [])
    ))

    if condition.startswith("HOT"):
        window = "HOT"
    elif condition.startswith("WATCH"):
        window = "WATCH"
    else:
        window = "WAIT"

    machine_intention = "UNKNOWN"
    sweep_state = ltf.get("sweep_state")
    if sweep_state == "LIQUIDITY_SWEEP_CANDIDATE":
        sweeps = ltf.get("sweeps") or []
        if sweeps:
            machine_intention = sweeps[-1].get("intention_candidate", "TRAP_OR_ACCUMULATION_CANDIDATE")
    elif "REJECTION" in str(mtf.get("plan_bias")):
        machine_intention = "REJECTION_OR_TRAP_WATCH"
    elif "ROTATION" in str(flux):
        machine_intention = "ROTATION_CONTINUATION_OR_FAILURE_WATCH"
    elif driver and driver != "UNKNOWN":
        machine_intention = f"DRIVER_CONTEXT_{driver}"

    return {
        "flux": flux,
        "zone": zone,
        "driver": driver,
        "condition": condition,
        "window": window,
        "machine_intention": machine_intention,
        "ontology_dominant_category": ontology.get("dominant_category"),
        "daily_close_position": day_profile.get("close_position"),
        "technical_fragility": fragility,
        "what_powerflow_can_read": [
            "HTF context when OHLC depth is available",
            "MTF plan state from H1/M30/M15 availability and zone behavior",
            "LTF attention conditions from M15/M5/M1 surfaces",
            "Cross-symbol driver from existing validation",
            "Ontology category of behavioral alerts",
            "Daily high/low/close position when OHLC exists",
        ],
        "what_powerflow_cannot_confirm": [
            "Final discretionary intention",
            "Trade decision",
            "Post-catalyst result before the event",
            "Clean zone rejection if OHLC data is absent or thin",
        ],
    }


def build_daily_market_reader(
    db_path: str | Path,
    symbol: str,
    date: Optional[str] = None,
    base_dir: str | Path = ".",
    schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    symbol = symbol.upper()
    date = date or today_utc_date()
    schema = schema or probe_price_schema(db_path, symbols=[symbol])
    htf = build_htf_context(db_path, symbol, schema=schema)
    zones = build_zone_rotation_map(db_path, symbol, schema=schema)
    mtf = build_mtf_day_plan(symbol, htf, zones, base_dir=base_dir)
    ltf = build_ltf_execution_conditions(db_path, symbol, schema=schema, base_dir=base_dir)
    if schema.get("primary_ohlc_table"):
        day_profile = _daily_profile_from_ohlc(db_path, symbol, schema, date)
    else:
        day_profile = {
            "status": "NO_OHLC_DAY_PROFILE",
            "date": date,
            "high": None,
            "low": None,
            "close": None,
            "close_position": "UNKNOWN",
            "close_position_ratio": None,
            "technical_risks": ["NO_OHLC_TABLE_DAILY_LEVELS_NOT_COMPUTABLE"],
        }
    cross_driver = _read_cross_driver(symbol, base_dir=base_dir)
    ontology = _read_ontology(symbol, base_dir=base_dir)
    surface = _surface_reading(symbol, htf, mtf, ltf, day_profile, cross_driver, ontology)
    risks = sorted(set(
        schema.get("technical_risks", [])
        + htf.get("technical_risks", [])
        + zones.get("technical_risks", [])
        + mtf.get("technical_risks", [])
        + ltf.get("technical_risks", [])
        + day_profile.get("technical_risks", [])
    ))
    return {
        "timestamp_utc": utc_now_iso(),
        "method": "TOPDOWN_MARKET_READER_V73",
        "symbol": symbol,
        "date": date,
        "db_mode": "READ_ONLY",
        "price_schema_summary": {
            "price_reading_capability": schema.get("price_reading_capability"),
            "primary_ohlc_table": (schema.get("primary_ohlc_table") or {}).get("table"),
            "primary_force_table": (schema.get("primary_force_table") or {}).get("table"),
        },
        "day_profile": day_profile,
        "reading_stack": {
            "htf_context": htf,
            "zone_rotation": zones,
            "mtf_day_plan": mtf,
            "ltf_execution_conditions": ltf,
            "cross_symbol_driver": cross_driver,
            "flow_ontology": ontology,
        },
        "surface_reading": surface,
        "daily_journal_fields": {
            "high_du_jour": day_profile.get("high"),
            "low_du_jour": day_profile.get("low"),
            "niveaux_testes": _extract_levels_by_status(zones, ["ZONE_TESTED"]),
            "niveaux_rejetes": _extract_levels_by_status(zones, ["ZONE_REJECTED", "BREAK_AND_REINTEGRATE"]),
            "close_position": day_profile.get("close_position"),
            "intention_detectee_machine": surface.get("machine_intention"),
            "prediction_demain_trader": "MANUAL_TO_FILL",
            "resultat_reel_j_plus_1": "MANUAL_TO_FILL",
            "apprentissage": "MANUAL_TO_FILL",
        },
        "technical_risks": risks,
        "note": "PowerFlow reads HTF -> MTF -> LTF. It qualifies perception; the trader analyzes and decides.",
    }


def _extract_levels_by_status(zone_map: Dict[str, Any], statuses: Sequence[str]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for tf_label, payload in (zone_map.get("zone_rotation") or {}).items():
        for lev in payload.get("levels", []) or []:
            if lev.get("status") in statuses:
                out.append({
                    "timeframe": tf_label,
                    "type": lev.get("type"),
                    "price": lev.get("price"),
                    "status": lev.get("status"),
                    "touch_count": lev.get("touch_count"),
                    "rejection_count": lev.get("rejection_count"),
                })
    return out[:20]


def render_daily_market_reader_markdown(state: Dict[str, Any]) -> str:
    sym = state.get("symbol", "UNKNOWN")
    date = state.get("date", "UNKNOWN")
    surf = state.get("surface_reading", {})
    day = state.get("day_profile", {})
    fields = state.get("daily_journal_fields", {})
    risks = state.get("technical_risks", [])
    stack = state.get("reading_stack", {})
    htf_label = stack.get("htf_context", {}).get("surface_label", "UNKNOWN")
    mtf = stack.get("mtf_day_plan", {})
    ltf = stack.get("ltf_execution_conditions", {})
    lines = [
        f"# DAILY MARKET READER V7.3 - {sym} - {date}",
        "",
        "## 1. Lecture top-down PowerFlow",
        f"- HTF: {htf_label}",
        f"- MTF plan: {mtf.get('plan_bias', 'UNKNOWN')}",
        f"- LTF condition: {ltf.get('entry_attention', 'UNKNOWN')}",
        f"- Driver cross-symbol: {surf.get('driver', 'UNKNOWN')}",
        f"- Fenetre: {surf.get('window', 'UNKNOWN')}",
        f"- Intention machine: {surf.get('machine_intention', 'UNKNOWN')}",
        "",
        "## 2. Journal des niveaux",
        f"- High du jour: {fields.get('high_du_jour')}",
        f"- Low du jour: {fields.get('low_du_jour')}",
        f"- Close position: {fields.get('close_position')}",
        f"- Niveaux testes: {len(fields.get('niveaux_testes') or [])}",
        f"- Niveaux rejetes: {len(fields.get('niveaux_rejetes') or [])}",
        "",
        "## 3. Plan MTF",
        f"- H1: {mtf.get('h1', 'UNKNOWN')}",
        f"- M30: {mtf.get('m30', 'UNKNOWN')}",
        f"- M15: {mtf.get('m15', 'UNKNOWN')}",
        f"- Scenario A: {mtf.get('scenario_a', 'UNKNOWN')}",
        f"- Scenario B: {mtf.get('scenario_b', 'UNKNOWN')}",
        f"- Invalidation analytique: {mtf.get('invalidation_observation', 'UNKNOWN')}",
        "",
        "## 4. Conditions LTF",
        f"- M15: {ltf.get('m15', 'UNKNOWN')}",
        f"- M5: {ltf.get('m5', 'UNKNOWN')}",
        f"- M1: {ltf.get('m1', 'UNKNOWN')}",
        f"- Sweep: {ltf.get('sweep_state', 'UNKNOWN')}",
        "",
        "## 5. Ce que PowerFlow peut lire",
    ]
    for item in surf.get("what_powerflow_can_read", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 6. Ce que PowerFlow ne confirme pas"])
    for item in surf.get("what_powerflow_cannot_confirm", []):
        lines.append(f"- {item}")
    lines.extend(["", "## 7. Champs trader", "- Prediction demain: MANUAL_TO_FILL", "- Resultat reel J+1: MANUAL_TO_FILL", "- Apprentissage: MANUAL_TO_FILL", ""])
    lines.append("## 8. Fragilites techniques")
    if risks:
        for r in risks:
            lines.append(f"- {r}")
    else:
        lines.append("- Aucune fragilite technique majeure remontee par cette brique.")
    lines.append("")
    return "\n".join(lines)


def write_daily_market_outputs(
    state: Dict[str, Any],
    output_json: str | Path,
    output_md: Optional[str | Path] = None,
    pretty: bool = True,
) -> Dict[str, str]:
    out_json = Path(output_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(state, indent=2 if pretty else None, ensure_ascii=False), encoding="utf-8")
    written = {"json": str(out_json)}
    if output_md:
        out_md = Path(output_md)
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(render_daily_market_reader_markdown(state), encoding="utf-8")
        written["markdown"] = str(out_md)
    return written
