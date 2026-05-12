#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from pf_daily_level_interaction import build_level_interactions
from pf_daily_sweep_classifier import build_sweep_report


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def extract_symbol_obj(container: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    if not isinstance(container, dict):
        return {}
    symbol_u = symbol.upper()
    for key in ("symbols", "profiles", "readers", "packets", "reports", "summaries"):
        obj = container.get(key)
        if isinstance(obj, dict):
            item = obj.get(symbol) or obj.get(symbol_u)
            if isinstance(item, dict): return item
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, dict) and str(item.get("symbol", "")).upper() == symbol_u:
                    return item
    direct = container.get(symbol) or container.get(symbol_u)
    return direct if isinstance(direct, dict) else {}


def choose_intent(level_report: Dict[str, Any], sweep_report: Dict[str, Any], topdown_symbol: Dict[str, Any], signal_symbol: Dict[str, Any]) -> str:
    sweeps = sweep_report.get("sweeps") or []
    confirmed = [s for s in sweeps if s.get("status") == "SWEEP_REJECTED_CONFIRMED"]
    invalidated = [s for s in sweeps if s.get("status") == "SWEEP_ACCEPTED_INVALIDATED"]
    if confirmed:
        high = [s for s in confirmed if str(s.get("sweep_type")) == "HIGH_SWEEP"]
        low = [s for s in confirmed if str(s.get("sweep_type")) == "LOW_SWEEP"]
        if high and low: return "DUAL_SWEEP_TRAP_OR_ROTATION"
        if high: return "SHORT_ACCUMULATION"
        if low: return "LONG_ACCUMULATION"
    if invalidated:
        return "BREAK_ACCEPTANCE"
    close_position = str((level_report.get("day_summary") or {}).get("close_position") or "")
    htf = str(topdown_symbol.get("htf_read") or topdown_symbol.get("htf_flux") or topdown_symbol.get("flux") or "")
    signal_mode = str(signal_symbol.get("mode") or signal_symbol.get("signal_mode") or "")
    if "NEAR_REACTION_ZONE" in htf: return "REACTION_ZONE_PENDING"
    if close_position == "HIGH_THIRD": return "BUY_PRESSURE_OR_HIGH_ACCEPTANCE"
    if close_position == "LOW_THIRD": return "SELL_PRESSURE_OR_LOW_ACCEPTANCE"
    if "THIN" in signal_mode: return "TACTICAL_ACCUMULATION_WITH_THIN_STRUCTURE"
    return "BALANCED_ROTATION"


def build_prediction(intent: str) -> str:
    return {
        "SHORT_ACCUMULATION": "WATCH_NEXT_SESSION_FOR_DOWNSIDE_ACCEPTANCE_AFTER_HIGH_SWEEP",
        "LONG_ACCUMULATION": "WATCH_NEXT_SESSION_FOR_UPSIDE_ACCEPTANCE_AFTER_LOW_SWEEP",
        "DUAL_SWEEP_TRAP_OR_ROTATION": "WATCH_NEXT_SESSION_FOR_ROTATION_RESOLUTION",
        "BREAK_ACCEPTANCE": "WATCH_CONTINUATION_OR_FAILED_ACCEPTANCE",
        "REACTION_ZONE_PENDING": "WATCH_REACTION_ZONE_REJECTION_OR_BREAK_ACCEPTANCE",
        "BUY_PRESSURE_OR_HIGH_ACCEPTANCE": "WATCH_CONTINUATION_OR_FAILED_HIGH_ACCEPTANCE",
        "SELL_PRESSURE_OR_LOW_ACCEPTANCE": "WATCH_CONTINUATION_OR_FAILED_LOW_ACCEPTANCE",
        "TACTICAL_ACCUMULATION_WITH_THIN_STRUCTURE": "WATCH_M1_FOR_RELAY_OR_REJECTION",
        "BALANCED_ROTATION": "NO_DIRECTIONAL_PREDICTION_PACKET_NEEDS_NEXT_REACTION",
    }.get(intent, "NO_DIRECTIONAL_PREDICTION_PACKET_NEEDS_NEXT_REACTION")


def technical_robustness(level_report: Dict[str, Any], sweep_report: Dict[str, Any]) -> float:
    score = 0.25
    if (level_report.get("day_summary") or {}).get("rows", 0) >= 60: score += 0.20
    if (level_report.get("previous_day_summary") or {}).get("rows", 0) > 0: score += 0.15
    if sweep_report.get("counts", {}).get("confirmed", 0) > 0: score += 0.25
    elif sweep_report.get("counts", {}).get("candidate", 0) > 0: score += 0.10
    if not level_report.get("technical_risks"): score += 0.15
    return round(min(1.0, score), 3)


def build_daily_journal(db_path: Path, symbol: str) -> Dict[str, Any]:
    symbol = symbol.upper()
    level_report = build_level_interactions(db_path, symbol)
    sweep_report = build_sweep_report(level_report, symbol)
    surface = Path("output/dashboard_surface")
    topdown_symbol = extract_symbol_obj(load_json(surface / "topdown_reader.json"), symbol)
    signal_symbol = extract_symbol_obj(load_json(surface / "signal_adaptive.json"), symbol)
    health_symbol = extract_symbol_obj(load_json(surface / "data_health.json"), symbol)
    ontology_symbol = extract_symbol_obj(load_json(surface / "flow_ontology_cycle_summary.json"), symbol)
    intent = choose_intent(level_report, sweep_report, topdown_symbol, signal_symbol)
    prediction = build_prediction(intent)
    day = level_report.get("day_summary") or {}
    prev = level_report.get("previous_day_summary") or {}
    interactions = level_report.get("interactions") or []
    tested = [i for i in interactions if i.get("interaction_state") not in ("UNTESTED", None)]
    rejected = [i for i in interactions if str(i.get("interaction_state", "")).startswith("REJECTED")]
    accepted = [i for i in interactions if str(i.get("interaction_state", "")).startswith("ACCEPTED")]
    risks = []
    for src in (level_report, sweep_report):
        for r in src.get("technical_risks", []):
            if r not in risks: risks.append(r)
    return {
        "timestamp_utc": now_utc_iso(), "symbol": symbol, "method": "DAILY_JOURNAL_V732", "date_utc": level_report.get("reference_date_utc"),
        "journal": {"high_of_day": day.get("high"), "low_of_day": day.get("low"), "open": day.get("open"), "close": day.get("close"), "close_position": day.get("close_position"), "previous_day_high": prev.get("high"), "previous_day_low": prev.get("low"), "levels_tested": tested, "levels_rejected": rejected, "levels_accepted": accepted, "sweeps": sweep_report.get("sweeps", []), "intent_detected": intent, "prediction_next_session": prediction, "actual_result_next_session": None, "lesson": None, "trader_notes": None},
        "context": {"htf_read": topdown_symbol.get("htf_read") or topdown_symbol.get("htf_flux") or topdown_symbol.get("flux"), "mtf_day_plan": topdown_symbol.get("mtf_day_plan") or topdown_symbol.get("mtf_plan"), "signal_mode": signal_symbol.get("mode") or signal_symbol.get("signal_mode"), "data_status": health_symbol.get("status"), "ontology": ontology_symbol},
        "robustness": technical_robustness(level_report, sweep_report), "technical_risks": risks, "note": "Daily journal is a perception/journaling object. It does not decide trades."
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--output", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    symbol = args.symbol.upper()
    out = Path(args.output) if args.output else Path("output/dashboard_surface") / symbol / "daily_journal.json"
    report = build_daily_journal(Path(args.db), symbol)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty: print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"DAILY_JOURNAL_OK | symbol={symbol} | intent={report.get('journal', {}).get('intent_detected')} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
