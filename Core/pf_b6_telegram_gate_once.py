#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request
from pathlib import Path


SYMBOL = "GBPUSD"
FUSION = Path("output/dashboard_surface") / SYMBOL / "b6_live_fusion.json"


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
        print("TELEGRAM_SKIPPED config missing")
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
    if not FUSION.exists():
        print("B6_TELEGRAM_GATE_NO_FUSION")
        return 1

    d = json.loads(FUSION.read_text(encoding="utf-8", errors="replace"))
    b6 = d.get("b6") or {}
    final = d.get("final_reading") or {}

    action = final.get("action")
    level = final.get("level")
    synthesis = final.get("synthesis")

    # Gate strict:
    # Telegram seulement si B6 = WAKE_TRADER + HOT.
    if action != "WAKE_TRADER" or level != "HOT":
        print("B6_TELEGRAM_NOT_SENT")
        print("action=", action)
        print("level=", level)
        print("synthesis=", synthesis)
        return 0

    msg = "\n".join([
        f"⚡ B6 MICROSTRUCTURE — {d.get('symbol')}",
        f"{synthesis}",
        "",
        f"state={b6.get('state')} tension={b6.get('tension')} delta={b6.get('delta')}",
        f"direction={b6.get('direction')} absorption={b6.get('absorption')}",
        "",
        final.get("message") or "",
    ])

    send_telegram(msg)
    print("B6_TELEGRAM_GATE_DONE")
    print("action=", action)
    print("level=", level)
    print("synthesis=", synthesis)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
