import json
from pathlib import Path

SYMBOL = "GBPUSD"
p = Path(f"output/dashboard_surface/{SYMBOL}/live_decision.json")
out = Path(f"output/dashboard_surface/{SYMBOL}/cockpit_live_status.txt")

if not p.exists():
    text = f"{SYMBOL} | NO_DECISION_FILE"
    print(text)
    out.write_text(text, encoding="utf-8")
    raise SystemExit(1)

d = json.loads(p.read_text(encoding="utf-8", errors="replace"))

state = d.get("state", "UNKNOWN")
level = d.get("level", "NONE")
bias = d.get("bias", "NONE")
msg = d.get("message", "")
live = d.get("live_count", 0)
old = d.get("expired_count", 0)

raw = d.get("raw_memory_packet") or {}

lines = []
lines.append(f"{SYMBOL} | {state} | {level} | {bias}")
lines.append(f"live={live} old={old}")

if state == "WATCH":
    lines.append("ACTION=NO_ALERT")
elif state in ("LIVE_INFO", "LIVE_ACTIVE", "LIVE_HOT"):
    lines.append("ACTION=WAKE_TRADER")
else:
    lines.append("ACTION=CHECK")

if raw:
    lines.append(
        "memory="
        + str(raw.get("type"))
        + " "
        + str(raw.get("level"))
        + " "
        + str(raw.get("bias"))
        + " TF="
        + str(raw.get("tf"))
        + " score="
        + str(raw.get("score"))
    )
    lines.append("last_signal=" + str(raw.get("last_signal_at")))

if msg:
    lines.append("message=" + str(msg))

text = "\n".join(lines)
out.write_text(text, encoding="utf-8")
print(text)
print("written=", out)
