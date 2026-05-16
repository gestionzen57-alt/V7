"""
T009 Phase 2B - Telegram LIVE routing for Battlefield Flux events.

This module is intentionally isolated from dashboard and engine code. It only
formats and routes already-built battlefield alert packets.

Safety contract:
- LIVE send requires POWERFLOW_T009_ENABLE_TELEGRAM=1.
- LIVE send requires POWERFLOW_T009_DRY_RUN=0.
- RECONSTRUCTED data is never sent live.
- confidence must be >= 0.50.
- per-symbol rate limit: one message every 10 seconds.
- retry max: 3 attempts.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import json
import os
import time
import urllib.parse
import urllib.request

RATE_LIMIT_SECONDS = 10
MIN_LIVE_CONFIDENCE = 0.50
MAX_RETRY_ATTEMPTS = 3

# Rate limiter: last successful send timestamp per symbol.
_last_send: Dict[str, float] = {}


def _to_int_flag(value: Any, default: int = 0) -> int:
    """Convert bool/int/str feature flags to 0/1 without raising."""
    if value is None:
        return default
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return 1 if value != 0 else 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return 1
    if text in {"0", "false", "no", "off", "disabled"}:
        return 0
    return default


def reset_rate_limiter(symbol: Optional[str] = None) -> None:
    """Testing/admin helper. Clears rate limit for one symbol or all symbols."""
    if symbol is None:
        _last_send.clear()
    else:
        _last_send.pop(symbol, None)


def _send_telegram_api(chat_id: str, message: str, parse_mode: str = "Markdown") -> bool:
    """
    Real Telegram send using Telegram Bot HTTP API.

    The token is read from TELEGRAM_BOT_TOKEN. Tests monkeypatch this function,
    so unit tests never send real messages.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN missing")
    if not chat_id or chat_id == "YOUR_CHAT_ID":
        raise RuntimeError("TELEGRAM_CHAT_ID missing")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(url, data=payload, method="POST")
    request.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(request, timeout=8) as response:  # nosec B310 - explicit Telegram API URL
        body = response.read().decode("utf-8", errors="replace")
        if response.status >= 400:
            raise RuntimeError(f"Telegram HTTP {response.status}: {body}")
        try:
            parsed = json.loads(body)
            return bool(parsed.get("ok", False))
        except json.JSONDecodeError:
            return response.status == 200


def _strip_t009_prefix(event_type: str) -> str:
    return event_type[5:] if event_type.startswith("T009_") else event_type


def _extract_level(packet: Dict[str, Any]) -> Optional[float]:
    zone = packet.get("zone", {})
    if isinstance(zone, dict):
        level = zone.get("level", zone.get("center"))
        if level is None and zone.get("low") is not None and zone.get("high") is not None:
            try:
                level = (float(zone["low"]) + float(zone["high"])) / 2.0
            except (TypeError, ValueError):
                return None
        try:
            return float(level) if level is not None else None
        except (TypeError, ValueError):
            return None
    if isinstance(zone, (list, tuple)) and len(zone) >= 2:
        try:
            return (float(zone[0]) + float(zone[1])) / 2.0
        except (TypeError, ValueError):
            return None
    return None


def _score(packet: Dict[str, Any], *names: str) -> float:
    scores = packet.get("scores", {}) if isinstance(packet.get("scores"), dict) else {}
    for name in names:
        if name in packet:
            try:
                return float(packet[name])
            except (TypeError, ValueError):
                continue
        if name in scores:
            try:
                return float(scores[name])
            except (TypeError, ValueError):
                continue
    return 0.0


def format_telegram_message_fr(packet: Dict[str, Any]) -> str:
    """
    Format a battlefield alert packet into concise French trader-facing text.

    The message remains a perception packet, not a BUY/SELL instruction.
    """
    raw_type = str(packet.get("event_type", "UNKNOWN"))
    event_type = _strip_t009_prefix(raw_type)
    symbol = str(packet.get("symbol", "GBPUSD"))
    confidence = float(packet.get("confidence", 0.0) or 0.0)
    visibility = str(packet.get("data_visibility", "UNKNOWN"))
    source_mode = str(packet.get("source_mode", "UNKNOWN"))
    level = _extract_level(packet)
    level_str = f"{level:.5f}" if level is not None else "zone"

    if event_type == "BATTLE_LEVEL_BORN":
        emoji = "⚔️"
        title = "BATTLE_LEVEL_BORN"
        lecture = "niveau de bataille détecté"
    elif event_type == "ABSORPTION_CLUSTER":
        emoji = "🛡"
        title = "ABSORPTION_CLUSTER"
        lecture = "cluster d'absorption détecté"
    else:
        emoji = "📍"
        title = event_type
        lecture = "événement battlefield détecté"

    if visibility == "RECONSTRUCTED":
        conf_label = "data reconstruite"
    elif confidence >= 0.70:
        conf_label = "haute confiance"
    elif confidence >= 0.50:
        conf_label = "confiance moyenne"
    else:
        conf_label = "confiance faible"

    battle_score = _score(packet, "battle_score")
    absorption_score = _score(packet, "absorption_score")

    return (
        f"{emoji} *{title}* @ `{level_str}`\n"
        f"Symbole: *{symbol}*\n"
        f"Lecture: {lecture}\n"
        f"Scores: battle={battle_score:.2f} absorption={absorption_score:.2f}\n"
        f"Confiance: {conf_label} ({confidence:.2f})\n"
        f"Source: {source_mode} | Data: {visibility}"
    )


def send_battlefield_alert(packet: Dict[str, Any], flags: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a battlefield alert via Telegram if all Phase 2B safety gates pass.

    Returns a structured audit result. Unit tests monkeypatch _send_telegram_api,
    so no real Telegram call is made during tests.
    """
    enable = _to_int_flag(
        flags.get("POWERFLOW_T009_ENABLE_TELEGRAM", flags.get("ENABLE_TELEGRAM")),
        default=0,
    )
    dry_run = _to_int_flag(
        flags.get("POWERFLOW_T009_DRY_RUN", flags.get("DRY_RUN")),
        default=1,
    )

    symbol = str(packet.get("symbol", "GBPUSD"))
    visibility = str(packet.get("data_visibility", "UNKNOWN"))
    confidence = float(packet.get("confidence", 0.0) or 0.0)
    live_allowed = bool(packet.get("live_telegram_allowed", visibility != "RECONSTRUCTED"))
    timestamp = datetime.now(timezone.utc).isoformat()

    if enable != 1:
        return {"sent": False, "reason": "POWERFLOW_T009_ENABLE_TELEGRAM=0", "attempts": 0, "timestamp": timestamp}

    if dry_run == 1:
        return {"sent": False, "reason": "DRY_RUN=1 (LIVE Telegram disabled)", "attempts": 0, "timestamp": timestamp}

    if visibility == "RECONSTRUCTED" or live_allowed is False:
        return {"sent": False, "reason": "RECONSTRUCTED data blocked from live Telegram", "attempts": 0, "timestamp": timestamp}

    if confidence < MIN_LIVE_CONFIDENCE:
        return {
            "sent": False,
            "reason": f"confidence {confidence:.2f} < {MIN_LIVE_CONFIDENCE:.2f} threshold",
            "attempts": 0,
            "timestamp": timestamp,
        }

    now = time.time()
    last = _last_send.get(symbol, 0.0)
    if now - last < RATE_LIMIT_SECONDS:
        return {
            "sent": False,
            "reason": f"rate limit: {RATE_LIMIT_SECONDS}s not elapsed since last {symbol} send",
            "attempts": 0,
            "timestamp": timestamp,
        }

    message = format_telegram_message_fr(packet)
    chat_id = str(flags.get("TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID"))

    for attempt in range(1, MAX_RETRY_ATTEMPTS + 1):
        try:
            if _send_telegram_api(chat_id, message, parse_mode="Markdown"):
                _last_send[symbol] = now
                return {
                    "sent": True,
                    "reason": "LIVE send success",
                    "attempts": attempt,
                    "chat_id": chat_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as exc:  # noqa: BLE001 - retry surface must capture all send failures
            if attempt == MAX_RETRY_ATTEMPTS:
                return {
                    "sent": False,
                    "reason": f"failed after {MAX_RETRY_ATTEMPTS} attempts: {exc}",
                    "attempts": attempt,
                    "chat_id": chat_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            time.sleep(1)

    return {
        "sent": False,
        "reason": "unknown Telegram send failure",
        "attempts": MAX_RETRY_ATTEMPTS,
        "chat_id": chat_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
