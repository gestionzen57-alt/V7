from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


SYMBOL = "GBPUSD"
BASE = Path("output/dashboard_surface") / SYMBOL
BRIEF = BASE / "powerflow_live_brief.json"

SEND_WAKE_TRADER = True
SEND_WATCH_ATTENTION = False


def load_env() -> None:
    p = Path(".env")
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def send_telegram(text: str) -> bool:
    load_env()

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

    if not token or not chat_id:
        print("TELEGRAM_SKIPPED | missing TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID")
        return False

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    with urllib.request.urlopen(url, data=data, timeout=10) as r:
        body = r.read().decode("utf-8", errors="replace")

    obj = json.loads(body)
    if obj.get("ok"):
        print("TELEGRAM_SEND_OK")
        return True

    print("TELEGRAM_SEND_FAIL", body[:300])
    return False


def main() -> int:
    if not BRIEF.exists():
        print("BRIEF_MISSING", BRIEF)
        return 1

    d = json.loads(BRIEF.read_text(encoding="utf-8", errors="replace"))

    action = d.get("action", "NO_ALERT")
    synthesis = d.get("synthesis", "UNKNOWN")
    reading = d.get("reading", "")

    daily = d.get("daily", {})
    topdown = d.get("topdown", {})
    live = d.get("live", {})
    risks = d.get("technical_risks", [])

    should_send = False
    tone = "INFO"

    if action == "ALERT_READY":
        should_send = True
        tone = "ALERT"
    elif action == "WAKE_TRADER" and SEND_WAKE_TRADER:
        should_send = True
        tone = "WAKE"
    elif action == "WATCH_ATTENTION" and SEND_WATCH_ATTENTION:
        should_send = True
        tone = "WATCH"

    if not should_send:
        print(f"TELEGRAM_NOT_SENT | action={action}")
        return 0

    msg = f"""⚡ PowerFlow {tone} — {SYMBOL}

{action} | {synthesis}

{reading}

DAILY:
intent={daily.get("intent")}
position={daily.get("close_position")}
sweeps={daily.get("sweep_count")} rejected={daily.get("rejected_count")}

TOPDOWN:
driver={topdown.get("driver")}
condition={topdown.get("condition")}
intention={topdown.get("machine_intention")}
node={topdown.get("node")}

LIVE:
packet={live.get("packet_type")}
level={live.get("packet_level")}
bias={live.get("packet_bias")}
tf={live.get("packet_tf")}
score={live.get("packet_score")}

RISKS:
{chr(10).join("- " + str(r) for r in risks) if risks else "- none"}
"""

    send_telegram(msg)
    print("POWERFLOW_TELEGRAM_GATE_DONE")
    print("action=", action)
    print("synthesis=", synthesis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
