from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OUT = Path("output/dashboard_surface")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    try:
        if not path.exists():
            return {}
        obj = json.loads(path.read_text(encoding="utf-8-sig", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def rank_level(score: float) -> str:
    if score >= 7.5:
        return "HOT"
    if score >= 6.0:
        return "ACTIVE"
    if score >= 4.0:
        return "WATCH"
    return "INFO"


def read_daily(symbol: str) -> dict[str, Any]:
    per_symbol = load_json(OUT / symbol / "daily_flow_packet.json")
    if per_symbol:
        return {
            "intent": per_symbol.get("daily_packet", {}).get("intent_detected"),
            "prediction": per_symbol.get("daily_packet", {}).get("prediction_next_session"),
            "close_position": per_symbol.get("daily_packet", {}).get("journal_levels", {}).get("close_position"),
            "technical_risks": per_symbol.get("technical_risks", []),
        }

    surface = load_json(OUT / "daily_flow_packet.json")
    for item in surface.get("symbols", []):
        if isinstance(item, dict) and str(item.get("symbol", "")).upper() == symbol:
            return {
                "intent": item.get("intent_detected"),
                "prediction": item.get("prediction_next_session"),
                "close_position": item.get("close_position"),
                "technical_risks": item.get("technical_risks", []),
            }

    return {}


def read_topdown(symbol: str) -> dict[str, Any]:
    d = load_json(OUT / symbol / "topdown_market_reader.json")
    if not d:
        d = load_json(OUT / symbol / "topdown_market_reading.json")

    surface = d.get("surface_reading", {}) if isinstance(d, dict) else {}
    stack = d.get("reading_stack", {}) if isinstance(d, dict) else {}

    return {
        "flux": surface.get("flux"),
        "driver": surface.get("driver"),
        "condition": surface.get("condition"),
        "machine_intention": surface.get("machine_intention"),
        "ontology": surface.get("ontology_dominant_category"),
        "technical_fragility": surface.get("technical_fragility", []),
        "plan_bias": stack.get("mtf_day_plan", {}).get("plan_bias"),
    }


def read_b6(symbol: str) -> dict[str, Any]:
    d = load_json(OUT / symbol / "microstructure_state.json")
    m = d.get("microstructure", {}) if isinstance(d, dict) else {}

    absorption = m.get("absorption", {}) if isinstance(m.get("absorption"), dict) else {}
    imbalance = m.get("imbalance", {}) if isinstance(m.get("imbalance"), dict) else {}

    return {
        "state": m.get("state"),
        "tension_score": m.get("tension_score"),
        "delta_cumulative": m.get("delta_cumulative"),
        "absorption": absorption.get("interpretation"),
        "absorption_direction": absorption.get("direction"),
        "imbalance": imbalance.get("direction"),
        "imbalance_magnitude": imbalance.get("magnitude"),
        "alerts_count": len(m.get("alerts", []) or []),
    }


def read_live(symbol: str) -> dict[str, Any]:
    d = load_json(OUT / symbol / "powerflow_live_brief.json")
    if d:
        return {
            "action": d.get("action"),
            "synthesis": d.get("synthesis"),
            "reading": d.get("reading"),
            "live": d.get("live", {}),
        }

    d = load_json(OUT / symbol / "live_decision.json")
    return {
        "action": d.get("state") or d.get("action"),
        "synthesis": d.get("packet_type") or d.get("type"),
        "live": d,
    }


def score_bridge(eie: dict[str, Any], daily: dict[str, Any], topdown: dict[str, Any], b6: dict[str, Any], live: dict[str, Any]) -> dict[str, Any]:
    score = safe_float(eie.get("score"))
    bias = str(eie.get("bias") or "NEUTRAL").upper()
    state = str(eie.get("state") or "").upper()

    evidence: list[str] = []
    contradictions: list[str] = []
    risks: list[str] = []

    daily_intent = str(daily.get("intent") or "").upper()
    top_machine = str(topdown.get("machine_intention") or "").upper()
    top_condition = str(topdown.get("condition") or "").upper()
    b6_imbalance = str(b6.get("imbalance") or "").upper()
    b6_absorption = str(b6.get("absorption") or "").upper()
    live_action = str(live.get("action") or "").upper()
    live_synthesis = str(live.get("synthesis") or "").upper()

    if "TRAP" in daily_intent or "DISTRIBUTION" in daily_intent or "REINTEGRATION" in daily_intent:
        evidence.append("DAILY_TRAP_OR_REINTEGRATION_CONTEXT")
        score += 0.6

    if "REACTION" in daily_intent:
        evidence.append("DAILY_REACTION_ZONE_CONTEXT")
        score += 0.3

    if "REJECTION" in top_machine or "TRAP" in top_machine:
        evidence.append("TOPDOWN_REJECTION_OR_TRAP_WATCH")
        score += 0.5

    if "HOT" in top_condition:
        evidence.append("TOPDOWN_HOT_ATTENTION")
        score += 0.4

    if bias == "PAIR_DOWN" and "SELL" in b6_imbalance:
        evidence.append("B6_SELL_ALIGNMENT")
        score += 0.7
    elif bias == "PAIR_UP" and "BUY" in b6_imbalance:
        evidence.append("B6_BUY_ALIGNMENT")
        score += 0.7
    elif bias in ("PAIR_DOWN", "PAIR_UP") and b6_imbalance:
        contradictions.append("B6_DIRECTION_CONFLICT")
        score -= 0.6

    if "ABSORBING" in b6_absorption and "NOT_ABSORBING" not in b6_absorption:
        evidence.append("B6_ABSORPTION_VISIBLE")

    if "ALERT" in live_action or "ACTIVE" in live_action or "WAKE" in live_action:
        evidence.append("LIVE_ATTENTION_PRESENT")
        score += 0.4

    if "CONFLICT" in live_synthesis:
        contradictions.append("LIVE_SYNTHESIS_CONFLICT")
        score -= 0.3

    if state in ("EIE_LOADING", "EIE_LOADED", "EIE_OVERSTRETCHED", "EIE_RELEASE_PENDING"):
        evidence.append(state)
    else:
        risks.append("EIE_NOT_LOADED_CURRENTLY")

    score = max(0.0, min(10.0, round(score, 2)))
    level = rank_level(score)

    if contradictions:
        synthesis = "EIE_CONTEXT_CONFLICT"
    elif state in ("EIE_LOADED", "EIE_OVERSTRETCHED", "EIE_RELEASE_PENDING") and "DAILY_TRAP_OR_REINTEGRATION_CONTEXT" in evidence:
        synthesis = "TRAP_CONTEXT_ELASTIC_PRESSURE_ALIGNED"
    elif state in ("EIE_LOADING", "EIE_LOADED") and ("B6_SELL_ALIGNMENT" in evidence or "B6_BUY_ALIGNMENT" in evidence):
        synthesis = "ELASTIC_LOADING_WITH_B6_ALIGNMENT"
    elif "TOPDOWN_REJECTION_OR_TRAP_WATCH" in evidence and state != "EIE_IDLE":
        synthesis = "ELASTIC_PRESSURE_IN_REACTION_CONTEXT"
    elif "TOPDOWN_REJECTION_OR_TRAP_WATCH" in evidence or "DAILY_TRAP_OR_REINTEGRATION_CONTEXT" in evidence:
        synthesis = "CONTEXT_READY_EIE_IDLE"
    else:
        synthesis = "EIE_STANDALONE_MONITOR"

    return {
        "score": score,
        "level": level,
        "synthesis": synthesis,
        "evidence": evidence,
        "contradictions": contradictions,
        "technical_risks": risks,
    }


def build(symbol: str) -> dict[str, Any]:
    eie_doc = load_json(OUT / symbol / "eie_confluence.json")
    eie = eie_doc.get("eie", {}) if isinstance(eie_doc, dict) else {}

    daily = read_daily(symbol)
    topdown = read_topdown(symbol)
    b6 = read_b6(symbol)
    live = read_live(symbol)

    bridge = score_bridge(eie, daily, topdown, b6, live)

    risks = []
    risks.extend(eie_doc.get("technical_risks", []) if isinstance(eie_doc, dict) else [])
    risks.extend(daily.get("technical_risks", []) or [])
    risks.extend(topdown.get("technical_fragility", []) or [])
    risks.extend(bridge.get("technical_risks", []) or [])

    return {
        "timestamp_utc": now_utc(),
        "method": "EIE_GRAVITY_BRIDGE_V74",
        "symbol": symbol,
        "layer": "EIE_GRAVITY",
        "state": eie.get("state"),
        "level": bridge.get("level"),
        "bias": eie.get("bias"),
        "score": bridge.get("score"),
        "confidence": round(min(0.95, 0.35 + safe_float(bridge.get("score")) / 15.0), 3),
        "timeframe": eie.get("tf"),
        "event_family": eie.get("event_family") or "ELASTIC_CONFLUENCE",
        "event_type": eie.get("event_type") or "EIE_UNKNOWN",
        "synthesis": bridge.get("synthesis"),
        "eie": eie,
        "context": {
            "daily": daily,
            "topdown": topdown,
            "b6": b6,
            "live": live,
        },
        "evidence": bridge.get("evidence", []),
        "contradictions": bridge.get("contradictions", []),
        "technical_risks": sorted(set(risks)),
        "note": "EIE gravity bridge articulates elastic pressure with PowerFlow context. It does not decide.",
    }


def write_txt(path: Path, d: dict[str, Any]) -> None:
    lines = [
        f"{d.get('symbol')} | EIE GRAVITY V7.4 | {d.get('level')} | {d.get('synthesis')}",
        f"state={d.get('state')} bias={d.get('bias')} tf={d.get('timeframe')} score={d.get('score')} confidence={d.get('confidence')}",
        f"event={d.get('event_type')} family={d.get('event_family')}",
        "evidence=" + (",".join(d.get("evidence", [])) or "NONE"),
        "contradictions=" + (",".join(d.get("contradictions", [])) or "NONE"),
        "risks=" + (",".join(d.get("technical_risks", [])) or "NONE"),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--symbols", default=None)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    symbols = [args.symbol.upper()]
    if args.symbols:
        symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]

    surface = {
        "timestamp_utc": now_utc(),
        "method": "EIE_GRAVITY_SURFACE_V74",
        "symbols": [],
    }

    for symbol in symbols:
        d = build(symbol)
        out = OUT / symbol
        write_json(out / "eie_gravity.json", d)
        write_txt(out / "eie_gravity.txt", d)

        surface["symbols"].append({
            "symbol": symbol,
            "level": d.get("level"),
            "bias": d.get("bias"),
            "score": d.get("score"),
            "synthesis": d.get("synthesis"),
            "event_type": d.get("event_type"),
        })

        print(f"EIE_GRAVITY_OK | {symbol} | {d.get('level')} | {d.get('synthesis')} | score={d.get('score')}")

    write_json(OUT / "eie_gravity_surface.json", surface)

    if args.pretty:
        print(json.dumps(surface, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
