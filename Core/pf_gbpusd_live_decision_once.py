import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime, timezone

def safe_console_text(value):
    text = str(value)
    return text.encode("ascii", "replace").decode("ascii")


SYMBOL = "GBPUSD"
FLOW_PACKET = Path(f"output/dashboard_surface/{SYMBOL}/flow_packet.json")
LIVE_DECISION = Path(f"output/dashboard_surface/{SYMBOL}/live_decision.json")

def now_utc():
    return datetime.now(timezone.utc).isoformat()

def run(cmd):
    print("RUN:", " ".join(cmd))
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.stdout.strip():
        print(p.stdout.strip())
    if p.stderr.strip():
        print("STDERR:", p.stderr.strip())
    return p.returncode

def write_decision(payload):
    LIVE_DECISION.parent.mkdir(parents=True, exist_ok=True)
    LIVE_DECISION.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print("LIVE_DECISION_WRITTEN:", LIVE_DECISION)

print("\n=== GBPUSD COMMANDO LIVE DECISION ===")

run([sys.executable, "pf_packet_live_gate_once.py"])

if not FLOW_PACKET.exists():
    decision = {
        "created_at": now_utc(),
        "symbol": SYMBOL,
        "state": "NO_PACKET_FILE",
        "level": "NONE",
        "bias": "NONE",
        "technical_risk": "flow_packet.json missing",
    }
    write_decision(decision)
    raise SystemExit(1)

data = json.loads(FLOW_PACKET.read_text(encoding="utf-8", errors="replace"))

live_gate = data.get("live_gate", {})
top_live = data.get("top_live_packet")
raw_top = data.get("top_packet")

if not top_live:
    decision = {
        "created_at": now_utc(),
        "symbol": SYMBOL,
        "state": "WATCH",
        "level": "NONE",
        "bias": "NONE",
        "message": "NO_LIVE_PACKET",
        "live_count": live_gate.get("live_count", 0),
        "expired_count": live_gate.get("expired_count", 0),
        "raw_memory_packet": {
            "type": raw_top.get("packet_type") if isinstance(raw_top, dict) else None,
            "level": raw_top.get("packet_level") if isinstance(raw_top, dict) else None,
            "bias": raw_top.get("pair_bias") if isinstance(raw_top, dict) else None,
            "tf": raw_top.get("timeframe") if isinstance(raw_top, dict) else None,
            "score": raw_top.get("score") if isinstance(raw_top, dict) else None,
            "last_signal_at": raw_top.get("last_signal_at") if isinstance(raw_top, dict) else None,
        },
        "interpretation": "Flux surveillé, aucun paquet vivant validé par le gate.",
    }
    write_decision(decision)

    print("\n=== DECISION ===")
    print("GBPUSD | WATCH | NO_LIVE_PACKET")
    print("expired_count=", decision["expired_count"])
    raise SystemExit(0)

level = str(top_live.get("packet_level", "UNKNOWN")).upper()
bias = top_live.get("pair_bias")
ptype = top_live.get("packet_type")
tf = top_live.get("timeframe")
score = top_live.get("score")
types = top_live.get("types", [])
notes = top_live.get("notes", [])

state = "LIVE_HOT" if level == "HOT" else "LIVE_ACTIVE" if level == "ACTIVE" else "LIVE_INFO"

decision = {
    "created_at": now_utc(),
    "symbol": SYMBOL,
    "state": state,
    "level": level,
    "bias": bias,
    "packet_type": ptype,
    "timeframe": tf,
    "score": score,
    "types": types,
    "notes": notes[:5],
    "live_count": live_gate.get("live_count", 0),
    "expired_count": live_gate.get("expired_count", 0),
    "interpretation": "Paquet vivant validé par le gate.",
}

write_decision(decision)

print("\n=== DECISION ===")
print(f"{SYMBOL} | {state} | {ptype} | {bias} | TF={tf} | score={score}")
for n in notes[:3]:
    print("-", safe_console_text(str(n).replace("\n", " | ")))
