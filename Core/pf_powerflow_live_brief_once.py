from __future__ import annotations

import json
from pathlib import Path
from datetime import datetime, timezone


SYMBOL = "GBPUSD"
BASE = Path("output/dashboard_surface") / SYMBOL


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def load_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace").strip()


def dig(d: dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k)
    return cur if cur is not None else default


daily = load_json(BASE / "daily_flow_packet.json")
topdown = load_json(BASE / "topdown_market_reader.json")
live = load_json(BASE / "live_decision.json")
flow = load_json(BASE / "flow_packet.json")
cockpit_txt = load_text(BASE / "cockpit_live_status.txt")

daily_packet = daily.get("daily_packet", {})
journal = daily_packet.get("journal_levels", {})

surface = topdown.get("surface_reading", {})
reading_stack = topdown.get("reading_stack", {})
mtf = reading_stack.get("mtf_day_plan", {})
ltf = reading_stack.get("ltf_execution_conditions", {})

top_packet = flow.get("top_live_packet") or flow.get("top_packet") or {}
raw_memory = live.get("raw_memory_packet") or {}

daily_intent = daily_packet.get("intent_detected", "UNKNOWN")
daily_prediction = daily_packet.get("prediction_next_session", "UNKNOWN")
daily_close_position = journal.get("close_position", "UNKNOWN")

topdown_intention = surface.get("machine_intention", "UNKNOWN")
topdown_condition = surface.get("condition", "UNKNOWN")
topdown_driver = surface.get("driver", "UNKNOWN")
topdown_flux = surface.get("flux", "UNKNOWN")
ontology = surface.get("ontology_dominant_category", "UNKNOWN")

live_state = live.get("state", "UNKNOWN")
live_level = live.get("level", "UNKNOWN")
live_bias = live.get("bias", "UNKNOWN")
live_message = live.get("message", "UNKNOWN")
live_count = live.get("live_count", 0)
expired_count = live.get("expired_count", 0)

packet_type = top_packet.get("packet_type") or raw_memory.get("type") or "NONE"
packet_level = top_packet.get("packet_level") or raw_memory.get("level") or "NONE"
packet_bias = top_packet.get("pair_bias") or raw_memory.get("bias") or "NONE"
packet_tf = top_packet.get("timeframe") or raw_memory.get("tf")
packet_score = top_packet.get("score") or raw_memory.get("score")
packet_events = top_packet.get("event_count") or len(top_packet.get("events", []))

technical_risks = []
for src in [daily, topdown, live, flow]:
    risks = src.get("technical_risks")
    if isinstance(risks, list):
        technical_risks.extend(risks)

technical_risks = sorted(set(str(x) for x in technical_risks if x))

if live_state in ("HOT", "ACTIVE") or packet_level in ("HOT", "ACTIVE"):
    action = "ALERT_READY"
elif live_count and live_state in ("LIVE_INFO", "WATCH"):
    action = "WAKE_TRADER"
elif topdown_condition == "HOT_ATTENTION_CONDITION_PRESENT":
    action = "WATCH_ATTENTION"
else:
    action = "NO_ALERT"

if daily_intent == "SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP" and packet_bias == "PAIR_UP":
    synthesis = "CONFLICT_OR_REINTEGRATION_TEST"
    reading = "Daily lit un piège/distribution baissier possible, mais le live pousse PAIR_UP : surveiller réintégration, piège inverse ou second test."
elif "TRAP" in daily_intent and topdown_intention == "REJECTION_OR_TRAP_WATCH":
    synthesis = "TRAP_CONTEXT_ALIGNED"
    reading = "Daily et topdown convergent vers un contexte piège/rejet. Attendre un paquet live plus chaud pour alerte forte."
elif packet_type != "NONE":
    synthesis = "LIVE_PACKET_PRESENT"
    reading = f"Paquet live {packet_type} {packet_level} en {packet_bias}. Flux sous attention."
else:
    synthesis = "STRUCTURE_ONLY"
    reading = "Structure lisible, aucun paquet live fort actuellement."

brief = {
    "created_at": datetime.now(timezone.utc).isoformat(),
    "symbol": SYMBOL,
    "action": action,
    "synthesis": synthesis,
    "reading": reading,
    "daily": {
        "intent": daily_intent,
        "prediction_next_session": daily_prediction,
        "close_position": daily_close_position,
        "high": journal.get("high_of_day"),
        "low": journal.get("low_of_day"),
        "close": journal.get("close"),
        "tested_count": len(daily_packet.get("tested_levels", [])),
        "rejected_count": len(daily_packet.get("rejected_levels", [])),
        "sweep_count": len(daily_packet.get("sweep_candidates", [])),
    },
    "topdown": {
        "flux": topdown_flux,
        "driver": topdown_driver,
        "condition": topdown_condition,
        "machine_intention": topdown_intention,
        "ontology": ontology,
        "plan_bias": mtf.get("plan_bias"),
        "h1": mtf.get("h1"),
        "m30": mtf.get("m30"),
        "m15": mtf.get("m15"),
        "ltf_m15": ltf.get("m15"),
        "ltf_m5": ltf.get("m5"),
        "ltf_m1": ltf.get("m1"),
        "node": ltf.get("node_level"),
        "entry_attention": ltf.get("entry_attention"),
    },
    "live": {
        "state": live_state,
        "level": live_level,
        "bias": live_bias,
        "message": live_message,
        "live_count": live_count,
        "expired_count": expired_count,
        "packet_type": packet_type,
        "packet_level": packet_level,
        "packet_bias": packet_bias,
        "packet_tf": packet_tf,
        "packet_score": packet_score,
        "packet_events": packet_events,
    },
    "technical_risks": technical_risks,
}

BASE.mkdir(parents=True, exist_ok=True)

json_out = BASE / "powerflow_live_brief.json"
txt_out = BASE / "powerflow_live_brief.txt"

json_out.write_text(json.dumps(brief, ensure_ascii=False, indent=2), encoding="utf-8")

txt = f"""GBPUSD | {action} | {synthesis}
reading={reading}

DAILY
intent={daily_intent}
prediction={daily_prediction}
close_position={daily_close_position}
high={journal.get("high_of_day")} low={journal.get("low_of_day")} close={journal.get("close")}
tested={len(daily_packet.get("tested_levels", []))} rejected={len(daily_packet.get("rejected_levels", []))} sweeps={len(daily_packet.get("sweep_candidates", []))}

TOPDOWN
flux={topdown_flux}
driver={topdown_driver}
condition={topdown_condition}
machine_intention={topdown_intention}
ontology={ontology}
plan_bias={mtf.get("plan_bias")}
H1={mtf.get("h1")}
M30={mtf.get("m30")}
M15={mtf.get("m15")}
LTF_M15={ltf.get("m15")}
LTF_M5={ltf.get("m5")}
LTF_M1={ltf.get("m1")}
node={ltf.get("node_level")}

LIVE
state={live_state}
packet={packet_type}
level={packet_level}
bias={packet_bias}
tf={packet_tf}
score={packet_score}
live={live_count}
old={expired_count}

RISKS
{chr(10).join("- " + r for r in technical_risks) if technical_risks else "- none"}
"""

txt_out.write_text(txt, encoding="utf-8")

print("POWERFLOW_LIVE_BRIEF_OK")
print("json=", json_out)
print("txt =", txt_out)
print()
print(txt)
