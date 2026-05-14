from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Tuple

# PowerFlow Windows UTF-8 stdout guard
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

DEFAULT_PACKET = Path("output") / "dashboard_surface" / "GBPUSD" / "terrain_packet.json"
DEFAULT_TEXT = Path("output") / "dashboard_surface" / "GBPUSD" / "terrain_packet_fr.txt"
DEFAULT_STATE = Path("output") / "telegram_alerts" / "state.json"
DEFAULT_LOCAL_CONFIG = Path("config") / "telegram_alerts.local.json"

QUALIFIED_BIAS_BLOCKLIST = {"UNKNOWN", "HONEST_UNKNOWN", "", None}
RAW_ONLY_BIAS = {"PAIR_UP", "PAIR_DOWN", "HOT", "WATCH", "ACTIVE", "MIXED", "NEUTRAL"}

IMPORTANT_PRICE = {
    "PRICE_CONFIRMED",
    "PRICE_REJECTED_HIGH",
    "PRICE_REJECTED_LOW",
    "PRICE_ACCEPTED_ABOVE_ZONE",
    "PRICE_ACCEPTED_BELOW_ZONE",
    "PRICE_INVALIDATED",
}

IMPORTANT_QUALITY = {
    "STRUCTURAL_REACTION",
    "STRUCTURAL_CONTINUATION",
    "CONTINUATION_ACCEPTED",
    "EXHAUSTION_RISK",
    "REACTION_NOT_RELEASE",
}

IMPORTANT_FILMS = {
    "HIGH_ZONE_REJECTION",
    "LOWER_LOCK",
    "LOWER_ZONE_ACTIVE",
    "HIGH_ZONE_ACTIVE",
    "POST_RELEASE_UNWIND",
    "POST_RELEASE_REBUILD",
}


def _read_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected at {path}")
    return data


def _write_json(path: str | Path, data: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def _load_local_config(path: str | Path = DEFAULT_LOCAL_CONFIG) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return _read_json(p)


def _token_and_chat(args: argparse.Namespace) -> Tuple[str | None, str | None]:
    config = _load_local_config(args.config)
    token = args.token or os.getenv("TELEGRAM_BOT_TOKEN") or config.get("bot_token")
    chat_id = args.chat_id or os.getenv("TELEGRAM_CHAT_ID") or config.get("chat_id")
    return token, chat_id


def packet_fingerprint(packet: Dict[str, Any]) -> str:
    important = {
        "symbol": packet.get("symbol"),
        "market_time": packet.get("market_time"),
        "film_state": packet.get("film_state"),
        "last_structural_event": packet.get("last_structural_event"),
        "current_move_role": packet.get("current_move_role"),
        "raw_bias": packet.get("raw_bias"),
        "qualified_bias": packet.get("qualified_bias"),
        "packet_quality": packet.get("packet_quality"),
        "price_confirmation": packet.get("price_confirmation"),
        "propagation_state": packet.get("propagation_state"),
        "detachment_texture": packet.get("detachment_texture"),
        "data_visibility": packet.get("data_visibility"),
        "technical_risks": packet.get("technical_risks") or [],
    }
    payload = json.dumps(important, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def should_alert(packet: Dict[str, Any], state: Dict[str, Any], cooldown_seconds: int = 900) -> Tuple[bool, str]:
    qualified = packet.get("qualified_bias")
    raw = packet.get("raw_bias")
    film = packet.get("film_state")
    quality = packet.get("packet_quality")
    price = packet.get("price_confirmation")
    data = packet.get("data_visibility")
    risks = packet.get("technical_risks") or []

    if qualified in QUALIFIED_BIAS_BLOCKLIST:
        return False, "qualified_bias is unknown"

    if qualified in RAW_ONLY_BIAS and price not in IMPORTANT_PRICE:
        return False, "raw-only packet without important price confirmation"

    important = (
        price in IMPORTANT_PRICE
        or quality in IMPORTANT_QUALITY
        or film in IMPORTANT_FILMS
        or data not in ("FULL_READING", "UNKNOWN", None, "")
        or bool(risks)
    )
    if not important:
        return False, "packet is not important enough"

    fp = packet_fingerprint(packet)
    now = int(time.time())
    last = state.get(fp)
    if isinstance(last, int) and now - last < cooldown_seconds:
        return False, f"cooldown active for fingerprint {fp}"

    return True, "qualified alert"


def build_message(packet: Dict[str, Any], text_fr: str) -> str:
    header = "PowerFlow — alerte qualifiée"
    symbol = packet.get("symbol", "UNKNOWN")
    qualified = packet.get("qualified_bias", "UNKNOWN")
    price = packet.get("price_confirmation", "UNKNOWN")
    data = packet.get("data_visibility", "UNKNOWN")
    footer = (
        "\n\n"
        f"Résumé technique : {symbol} | {qualified} | {price} | DATA={data}\n"
        "Rappel : alerte de contexte, pas ordre automatique."
    )
    return header + "\n\n" + text_fr.strip() + footer


def send_telegram(token: str, chat_id: str, message: str) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(request, timeout=20) as response:
        data = response.read().decode("utf-8")
    return json.loads(data)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Send qualified PowerFlow terrain_packet alerts to Telegram in French."
    )
    parser.add_argument("--packet", default=str(DEFAULT_PACKET), help="terrain_packet.json path")
    parser.add_argument("--text-fr", default=str(DEFAULT_TEXT), help="terrain_packet_fr.txt path")
    parser.add_argument("--state", default=str(DEFAULT_STATE), help="alert state JSON path")
    parser.add_argument("--config", default=str(DEFAULT_LOCAL_CONFIG), help="local Telegram config JSON path")
    parser.add_argument("--cooldown-seconds", type=int, default=900)
    parser.add_argument("--token")
    parser.add_argument("--chat-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    packet = _read_json(args.packet)
    text_fr = _read_text(args.text_fr)
    state_path = Path(args.state)
    state = _read_json(state_path) if state_path.exists() else {}

    ok, reason = should_alert(packet, state, args.cooldown_seconds)
    fp = packet_fingerprint(packet)
    message = build_message(packet, text_fr)

    if args.force:
        ok = True
        reason = "forced alert"

    result = {
        "should_alert": ok,
        "reason": reason,
        "fingerprint": fp,
        "packet": str(args.packet),
        "text_fr": str(args.text_fr),
    }

    if args.dry_run:
        print("=== TELEGRAM DRY RUN ===")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("")
        print(message)
        return 0

    if not args.send:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if ok else 2

    if not ok:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    token, chat_id = _token_and_chat(args)
    if not token or not chat_id:
        raise SystemExit(
            "Missing Telegram credentials. "
            "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, "
            "or create config/telegram_alerts.local.json with bot_token/chat_id."
        )

    response = send_telegram(token, chat_id, message)
    result["telegram_response"] = response
    state[fp] = int(time.time())
    _write_json(state_path, state)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



