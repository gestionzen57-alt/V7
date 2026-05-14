from __future__ import annotations

import argparse
import json
import os
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

LABELS = {
    "HIGH_ZONE_REJECTION": "Rejet de zone haute",
    "HIGH_ZONE_EXHAUSTION_RISK": "Risque d\u2019\u00e9puisement en zone haute",
    "EXHAUSTION_RISK": "Risque d\u2019\u00e9puisement",
    "READING_PARTIAL": "lecture partielle",
    "FULL_READING": "lecture compl\u00e8te",
    "PRICE_REJECTED_LOW": "rejet bas",
    "PRICE_REJECTED_HIGH": "rejet haut",
    "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND": "high rejet\u00e9 puis unwind",
    "vraie acceptation prix, pas extension tardive.": "acceptation propre, pas extension tardive",
    "rejet haut confirmé ou déroulement inverse.": "rejet de zone haute ou unwind",
}


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:
        return {}


def _label(value: Any, default: str = "non disponible") -> str:
    if value is None or value == "":
        return default
    text = str(value)
    if text in LABELS:
        return LABELS[text]
    # Preserve already-human French labels from playbook/labels JSON.
    # Only prettify raw ALL_CAPS enums.
    if "_" in text and text.upper() == text:
        return text.replace("_", " ").lower()
    return text


def _day_fr(value: Any) -> str:
    if not value:
        return "jour calibr\u00e9"
    text = str(value)[:10]
    try:
        dt = datetime.strptime(text, "%Y-%m-%d")
        months = ["janvier", "f\u00e9vrier", "mars", "avril", "mai", "juin", "juillet", "ao\u00fbt", "septembre", "octobre", "novembre", "d\u00e9cembre"]
        return f"{dt.day:02d} {months[dt.month - 1]}"
    except Exception:
        return text


def _first_present(data: dict[str, Any], keys: list[str]) -> Any:
    for k in keys:
        if k in data and data[k] not in (None, ""):
            return data[k]
    return None


def _memory_day(memory: dict[str, Any]) -> Any:
    direct = _first_present(memory, ["day", "date", "film_day", "primary_day", "nearest_day"])
    if direct:
        return direct
    for key in ["top_matches", "matches", "nearest_films", "similar_films"]:
        seq = memory.get(key)
        if isinstance(seq, list) and seq:
            item = seq[0]
            if isinstance(item, dict):
                found = _first_present(item, ["day", "date", "film_day", "primary_day"])
                if found:
                    return found
    return None


def build_short_message(packet: dict[str, Any], memory: dict[str, Any], playbook: dict[str, Any]) -> str:
    symbol = str(packet.get("symbol") or playbook.get("symbol") or "GBPUSD")
    film_state = packet.get("film_state") or packet.get("last_structural_event") or playbook.get("playbook_state")
    title = _label(film_state, "Lecture terrain")

    reading = playbook.get("playbook_label_fr") or packet.get("qualified_bias") or packet.get("packet_quality")
    reading_label = _label(reading, "Lecture terrain partielle")

    mem_name = memory.get("memory_match") or memory.get("film_pattern") or memory.get("match")
    mem_label = _label(mem_name, "film calibr\u00e9 proche")
    mem_day = _day_fr(_memory_day(memory))

    plan = playbook.get("plan") or playbook.get("watch_condition") or packet.get("watch_condition")
    if isinstance(plan, list):
        plan = " ; ".join(str(x) for x in plan if x)
    if not plan or str(plan).isupper():
        plan = "ne pas chase ; attendre acceptation propre ou rejet confirm\u00e9"
    plan = str(plan).strip().rstrip(".")

    data = packet.get("data_visibility") or playbook.get("data_visibility")
    data_label = _label(data, "lecture partielle")

    return "\n".join([
        f"{symbol} \u2014 {title}",
        "",
        f"Lecture : {reading_label}",
        f"B6 : proche du {mem_day} \u2014 {mem_label}",
        f"Plan : {plan}",
        f"Data : {data_label}",
        "Rappel : contexte, pas ordre automatique",
    ])


def _load_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.exists():
        return out
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def load_telegram_config() -> tuple[str | None, str | None]:
    cfg = _read_json(ROOT / "config" / "telegram_alerts.local.json")
    token = cfg.get("bot_token") or cfg.get("token") or cfg.get("telegram_bot_token")
    chat_id = cfg.get("chat_id") or cfg.get("telegram_chat_id")
    env = _load_env_file(ROOT / "Core" / ".env")
    token = token or env.get("TELEGRAM_BOT_TOKEN") or env.get("TELEGRAM_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
    chat_id = chat_id or env.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")
    return token, chat_id


def send_telegram(text: str) -> dict[str, Any]:
    token, chat_id = load_telegram_config()
    if not token or not chat_id:
        return {"ok": False, "error": "missing telegram token/chat_id"}
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({"chat_id": chat_id, "text": text}).encode("utf-8")
    try:
        with urllib.request.urlopen(url, data=payload, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        try:
            return json.loads(body)
        except Exception:
            return {"ok": True, "raw": body}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--mode", choices=["dry-run", "send"], default="dry-run")
    ap.add_argument("--output", default="output/dashboard_surface/GBPUSD/v766_telegram_short_live_result.json")
    args = ap.parse_args()

    surface = ROOT / "output" / "dashboard_surface" / args.symbol
    packet = _read_json(surface / "terrain_packet.json")
    memory = _read_json(surface / "film_memory_match.json")
    playbook = _read_json(surface / "trader_playbook.json")
    text = build_short_message(packet, memory, playbook)

    result: dict[str, Any] = {
        "ok": True,
        "mode": args.mode,
        "symbol": args.symbol,
        "message_short": text,
        "sent": False,
    }
    if args.mode == "send":
        send_result = send_telegram(text)
        result["telegram_response"] = send_result
        result["sent"] = bool(send_result.get("ok"))
        result["ok"] = bool(send_result.get("ok"))

    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(text)
    if args.mode == "send" and not result["sent"]:
        print("SEND_FAILED", result.get("telegram_response"))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
