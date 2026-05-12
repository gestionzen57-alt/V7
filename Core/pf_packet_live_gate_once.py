import os, json, sqlite3, subprocess, sys, urllib.parse, urllib.request
from pathlib import Path
from datetime import datetime, timezone

SYMBOL = "GBPUSD"
DB = "powerflow.db"
OUT = Path(f"output/dashboard_surface/{SYMBOL}/flow_packet.json")

MAX_AGE_BY_TF = {
    1: 4,
    5: 8,
    15: 20,
    30: 40,
    60: 80,
    240: 260,
}

def load_env():
    p = Path(".env")
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def dt_parse(x):
    if not x:
        return None
    d = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d

def age_min(x):
    d = dt_parse(x)
    if not d:
        return None
    return round((datetime.now(timezone.utc) - d).total_seconds() / 60, 2)

def send_telegram(text):
    load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("TELEGRAM_SKIPPED missing env")
        return

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=data, timeout=10) as r:
        body = r.read().decode("utf-8", errors="replace")

    obj = json.loads(body)
    print("TELEGRAM_SEND_OK" if obj.get("ok") else "TELEGRAM_SEND_FAIL " + body[:300])

print("RUN packetizer...")
subprocess.run([
    sys.executable,
    "pf_flow_packet_once.py",
    "--db", DB,
    "--symbol", SYMBOL,
    "--lookback-min", "20",
    "--window-seconds", "180",
    "--pretty",
], check=True)

j = json.loads(OUT.read_text(encoding="utf-8"))
packets = j.get("packets") or []

live_packets = []
expired_packets = []

for p in packets:
    tf = int(p.get("timeframe") or 0)
    a = age_min(p.get("last_signal_at"))
    max_age = MAX_AGE_BY_TF.get(tf, 10)

    p["age_min"] = a
    p["max_age_min"] = max_age

    if a is not None and a <= max_age:
        live_packets.append(p)
    else:
        expired_packets.append(p)

level_rank = {"HOT": 4, "ACTIVE": 3, "WATCH": 2, "INFO": 1}

def rank_packet(p):
    return (
        level_rank.get(p.get("packet_level"), 0),
        float(p.get("score") or 0),
        int(p.get("event_count") or 0),
        -float(p.get("age_min") or 9999),
    )

live_packets.sort(key=rank_packet, reverse=True)

top = live_packets[0] if live_packets else None

j["live_gate"] = {
    "engine": "pf_packet_live_gate",
    "created_at": datetime.now(timezone.utc).isoformat(),
    "symbol": SYMBOL,
    "live_count": len(live_packets),
    "expired_count": len(expired_packets),
    "max_age_by_tf": MAX_AGE_BY_TF,
}

j["top_live_packet"] = top
j["expired_packets"] = expired_packets[:10]

OUT.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")

print("\n=== LIVE PACKET GATE ===")
print("live_count=", len(live_packets))
print("expired_count=", len(expired_packets))

if not top:
    print("NO_LIVE_PACKET")
    raise SystemExit(0)

print("type=", top.get("packet_type"))
print("level=", top.get("packet_level"))
print("bias=", top.get("pair_bias"))
print("tf=", top.get("timeframe"))
print("score=", top.get("score"))
print("events=", top.get("event_count"))
print("age_min=", top.get("age_min"), "/", top.get("max_age_min"))
print("types=", top.get("types"))
print("first=", top.get("first_signal_at"))
print("last=", top.get("last_signal_at"))

msg = (
    f"⚡ POWERFLOW PACKET {SYMBOL}\n"
    f"{top.get('packet_level')} | {top.get('packet_type')}\n"
    f"Bias: {top.get('pair_bias')} | TF={top.get('timeframe')} | score={top.get('score')}\n"
    f"Age: {top.get('age_min')} min / max {top.get('max_age_min')}\n"
    f"Events: {', '.join(top.get('types') or [])}"
)

if top.get("packet_level") in ("HOT", "ACTIVE"):
    send_telegram(msg)
else:
    print("TELEGRAM_NOT_SENT level not HOT/ACTIVE")
