#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path

from pf_packet_dedup_memory import decision_preview, mark_sent, write_json_atomic

OUT_JSON = Path("output/dashboard_surface/GBPUSD/telegram_dedup_decision.json")
OUT_TXT = Path("output/dashboard_surface/GBPUSD/telegram_dedup_decision.txt")

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

def send_telegram(text: str) -> str:
    load_env()
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return "TELEGRAM_CONFIG_MISSING"

    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    with urllib.request.urlopen(url, data=data, timeout=12) as r:
        body = r.read().decode("utf-8", errors="replace")

    try:
        obj = json.loads(body)
        return "TELEGRAM_SEND_OK" if obj.get("ok") else "TELEGRAM_SEND_FAIL"
    except Exception:
        return "TELEGRAM_SEND_UNKNOWN"

def build_message(d: dict) -> str:
    p = d.get("packet") or {}
    types = ", ".join(p.get("types") or [])
    return (
        f"⚡ POWERFLOW PACKET {p.get('symbol')}\n"
        f"{p.get('level')} | {p.get('packet_type')}\n"
        f"Bias: {p.get('bias')} | TF={p.get('tf')} | score={p.get('score')}\n"
        f"Age: {p.get('age_min')} min\n"
        f"Events: {types}\n"
        f"Gate: {d.get('reason')}"
    )

def write_txt(d: dict, telegram_status: str) -> None:
    p = d.get("packet") or {}
    lines = [
        f"{p.get('symbol')} | V7.4 TELEGRAM DEDUP | send={d.get('send')} | {d.get('reason')}",
        f"telegram={telegram_status}",
        f"packet={p.get('packet_type')} level={p.get('level')} bias={p.get('bias')} tf={p.get('tf')} score={p.get('score')}",
        f"age_min={p.get('age_min')} fingerprint={p.get('fingerprint')}",
        f"memory={d.get('memory_path')}",
    ]
    OUT_TXT.parent.mkdir(parents=True, exist_ok=True)
    OUT_TXT.write_text("\n".join(lines), encoding="utf-8")

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--cooldown-min", type=int, default=30)
    ap.add_argument("--min-level", default="ACTIVE")
    ap.add_argument("--send", action="store_true")
    args = ap.parse_args()

    d = decision_preview(args.symbol, cooldown_min=args.cooldown_min, min_level=args.min_level)

    telegram_status = "DRY_RUN"
    if d.get("send") and args.send:
        msg = build_message(d)
        telegram_status = send_telegram(msg)
        if telegram_status == "TELEGRAM_SEND_OK":
            mark_sent(d["packet"], d["reason"])

    if d.get("send") and not args.send:
        telegram_status = "WOULD_SEND_DRY_RUN"
        # V7.4 dry-run must also mark memory so dedup can be tested without real Telegram spam.
        mark_sent(d, d.get("reason") or "DRY_RUN_MARK_SEEN")

    write_json_atomic(OUT_JSON, {**d, "telegram_status": telegram_status})
    write_txt(d, telegram_status)

    print("POWERFLOW_TELEGRAM_DEDUP_DONE")
    print("send=", d.get("send"))
    print("reason=", d.get("reason"))
    print("telegram=", telegram_status)
    print("json=", OUT_JSON)
    print("txt =", OUT_TXT)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
