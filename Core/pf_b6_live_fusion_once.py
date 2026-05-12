#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional


SYMBOL = "GBPUSD"
BASE = Path("output/dashboard_surface") / SYMBOL


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def classify_b6_action(micro: Dict[str, Any]) -> Dict[str, Any]:
    m = micro.get("microstructure") or {}
    state = str(m.get("state") or "UNKNOWN")
    tension = float(m.get("tension_score") or 0.0)
    delta = float(m.get("delta_cumulative") or 0.0)
    absorption = m.get("absorption") or {}
    imbalance = m.get("imbalance") or {}
    alerts = m.get("alerts") or []

    direction = absorption.get("direction") or "UNKNOWN"
    absorption_label = absorption.get("interpretation") or "UNKNOWN"
    imbalance_label = imbalance.get("direction") or "UNKNOWN"

    if state == "LOADED" and tension >= 75 and alerts:
        action = "WAKE_TRADER"
        level = "HOT"
        synthesis = "B6_MICROSTRUCTURE_LOADED"
        message = "B6 lit une tension microstructure proxy forte. Flux potentiellement en formation."
    elif state == "LOADING" and tension >= 58:
        action = "WATCH"
        level = "WATCH"
        synthesis = "B6_LOADING"
        message = "B6 lit un chargement microstructure proxy. Surveiller absorption ou détachement."
    elif state == "RELEASING":
        action = "WATCH"
        level = "WATCH"
        synthesis = "B6_REINTEGRATION_OR_RELEASE"
        message = "B6 lit une absorption/réintégration proxy. Possible piège ou relâchement."
    elif state == "RELEASED":
        action = "NO_ALERT"
        level = "INFO"
        synthesis = "B6_RELEASED"
        message = "B6 lit une tension relâchée ou partiellement absorbée."
    else:
        action = "NO_ALERT"
        level = "INFO"
        synthesis = "B6_NEUTRAL"
        message = "B6 ne lit pas de tension microstructure exploitable."

    return {
        "action": action,
        "level": level,
        "synthesis": synthesis,
        "message": message,
        "state": state,
        "tension": tension,
        "delta": delta,
        "direction": direction,
        "absorption": absorption_label,
        "imbalance": imbalance_label,
        "alert_count": len(alerts),
    }


def main() -> int:
    micro_path = BASE / "microstructure_state.json"
    live_brief_path = BASE / "powerflow_live_brief.json"
    topdown_path = BASE / "topdown_market_reader.json"
    daily_path = BASE / "daily_flow_packet.json"
    cockpit_path = BASE / "cockpit_live_status.txt"

    micro = read_json(micro_path)
    live_brief = read_json(live_brief_path)
    topdown = read_json(topdown_path)
    daily = read_json(daily_path)

    b6 = classify_b6_action(micro)

    daily_packet = daily.get("daily_packet") or {}
    journal = daily_packet.get("journal_levels") or {}
    surface = topdown.get("surface_reading") or {}
    live = live_brief.get("live") or {}

    fusion = {
        "created_at": utc_now(),
        "symbol": SYMBOL,
        "method": "B6_1_LIVE_FUSION_NON_DESTRUCTIVE",
        "b6": b6,
        "daily_context": {
            "intent": daily_packet.get("intent_detected"),
            "prediction": daily_packet.get("prediction_next_session"),
            "close_position": journal.get("close_position"),
            "high": journal.get("high_of_day"),
            "low": journal.get("low_of_day"),
            "close": journal.get("close"),
        },
        "topdown_context": {
            "flux": surface.get("flux"),
            "driver": surface.get("driver"),
            "condition": surface.get("condition"),
            "machine_intention": surface.get("machine_intention"),
            "ontology": surface.get("ontology_dominant_category"),
        },
        "live_context": {
            "state": live.get("state") or live_brief.get("state"),
            "packet": live.get("packet") or live_brief.get("packet"),
            "bias": live.get("bias") or live_brief.get("bias"),
            "score": live.get("score") or live_brief.get("score"),
        },
        "final_reading": {},
        "technical_risks": micro.get("technical_risks", []),
    }

    state = b6["state"]
    daily_intent = str(fusion["daily_context"].get("intent") or "")
    live_bias = str(fusion["live_context"].get("bias") or "")

    if b6["action"] == "WAKE_TRADER":
        if "SHORT" in daily_intent and b6["direction"] == "BUY_SIDE":
            final_synthesis = "B6_CONFLICT_WITH_DAILY_TRAP"
            final_message = "B6 charge BUY alors que le daily lit un piège/distribution baissier possible. Surveiller réintégration ou piège inverse."
        elif "SHORT" in daily_intent and b6["direction"] == "SELL_SIDE":
            final_synthesis = "B6_ALIGNED_WITH_DAILY_DOWNSIDE_ACCEPTANCE"
            final_message = "B6 charge SELL dans le sens du daily trap/downside acceptance. Attention précoce renforcée."
        else:
            final_synthesis = "B6_EARLY_TENSION_PRESENT"
            final_message = "B6 détecte une tension précoce. Lire avec topdown/live avant action trader."
    elif b6["synthesis"] == "B6_LOADING":
        final_synthesis = "B6_WATCH_LOADING"
        final_message = "B6 voit un chargement mais pas encore une tension HOT. Surveiller le prochain paquet live."
    elif b6["synthesis"] == "B6_REINTEGRATION_OR_RELEASE":
        final_synthesis = "B6_REINTEGRATION_WATCH"
        final_message = "B6 voit absorption/réintégration. Lire comme zone de piège ou relâchement."
    elif b6["synthesis"] == "B6_RELEASED":
        final_synthesis = "B6_NO_IMMEDIATE_PRESSURE"
        final_message = "B6 ne justifie pas de réveil trader. Flux proxy relâché ou absorbé."
    else:
        final_synthesis = "B6_NEUTRAL"
        final_message = "B6 neutre."

    fusion["final_reading"] = {
        "action": b6["action"],
        "level": b6["level"],
        "synthesis": final_synthesis,
        "message": final_message,
    }

    out_json = BASE / "b6_live_fusion.json"
    out_txt = BASE / "b6_live_fusion.txt"

    out_json.write_text(json.dumps(fusion, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"{SYMBOL} | B6.1 | {fusion['final_reading']['action']} | {fusion['final_reading']['synthesis']}",
        f"message={fusion['final_reading']['message']}",
        "",
        "B6",
        f"state={b6['state']} level={b6['level']} tension={b6['tension']} delta={b6['delta']}",
        f"direction={b6['direction']} absorption={b6['absorption']} imbalance={b6['imbalance']} alerts={b6['alert_count']}",
        "",
        "DAILY",
        f"intent={fusion['daily_context']['intent']}",
        f"prediction={fusion['daily_context']['prediction']}",
        f"close_position={fusion['daily_context']['close_position']}",
        "",
        "TOPDOWN",
        f"flux={fusion['topdown_context']['flux']}",
        f"driver={fusion['topdown_context']['driver']}",
        f"condition={fusion['topdown_context']['condition']}",
        f"machine_intention={fusion['topdown_context']['machine_intention']}",
        "",
        "LIVE",
        f"state={fusion['live_context']['state']}",
        f"packet={fusion['live_context']['packet']}",
        f"bias={fusion['live_context']['bias']}",
        f"score={fusion['live_context']['score']}",
    ]

    out_txt.write_text("\n".join(lines), encoding="utf-8")

    print("B6_LIVE_FUSION_OK")
    print("json=", out_json)
    print("txt =", out_txt)
    print()
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
