# -*- coding: utf-8 -*-
"""Telegram bridge for PowerFlow V7.6.7 B9 perception alerts."""

from __future__ import annotations

from typing import Any, Dict


VERDICT_EMOJI = {
    "REJECTED": "🔴",
    "FAILED_REINTEGRATION": "🟥",
    "PULLBACK_ABSORBED": "🟢",
    "ACCEPTED": "🟢",
    "CENTER_MIGRATION": "🔵",
    "EFFORT_WITHOUT_RESULT": "🟡",
    "INCONCLUSIVE": "⚪",
}

FINAL_LINE = "⚡ Perception transmise — Trader filtre."
FORBIDDEN_WORDS = ("conseil", "risque", "attendre", "considérez")


def send_b9_alert(node: dict, requalified: dict, config: dict):
    """Send a B9 alert to Telegram, or dry-run when disabled.

    Args:
        node: Terrain node snapshot.
        requalified: Requalified packet.
        config: {"ENABLE_TELEGRAM": bool, "TELEGRAM_BOT_TOKEN": str,
            "TELEGRAM_CHAT_ID": str}
    """
    config = dict(config or {})
    message = format_b9_alert(node, requalified)

    if not config.get("ENABLE_TELEGRAM", False):
        print("[DRY-RUN B9 TELEGRAM]")
        print(message)
        return {"sent": False, "dry_run": True, "message": message}

    token = config.get("TELEGRAM_BOT_TOKEN")
    chat_id = config.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("[DRY-RUN B9 TELEGRAM - MISSING CONFIG]")
        print(message)
        return {"sent": False, "dry_run": True, "message": message}

    import requests

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(url, data={"chat_id": chat_id, "text": message}, timeout=10)
    response.raise_for_status()
    return {"sent": True, "dry_run": False, "message": message, "status_code": response.status_code}


def format_b9_alert(node: dict, requalified: dict) -> str:
    """Format a Telegram perception message.

    The final line is doctrinally fixed and must remain the last line.
    """
    node = dict(node or {})
    requalified = dict(requalified or {})

    symbol = str(node.get("symbol") or requalified.get("symbol") or "UNKNOWN").upper()
    node_role_fr = str(node.get("node_role_fr") or node.get("role_fr") or "Node terrain B9")

    verdict = _extract_verdict(node, requalified)
    emoji = VERDICT_EMOJI.get(verdict, "⚪")
    confidence = _extract_confidence(node, requalified)

    zone_low = _extract_float(node, ("zone_low", "low"), default=0.0)
    zone_high = _extract_float(node, ("zone_high", "high"), default=0.0)
    width_pips = abs(zone_high - zone_low) * 10000.0

    requalified_event = str(
        requalified.get("requalified_event_fr")
        or requalified.get("requalified_event")
        or "UNQUALIFIED"
    )
    data_visibility = str(
        node.get("data_visibility")
        or requalified.get("data_visibility")
        or requalified.get("data_visibility_state")
        or "READING_PARTIAL"
    )
    source_stack = str(requalified.get("source_stack") or node.get("source_stack") or "B9")

    message = (
        f"{emoji} {symbol} — {node_role_fr}\n"
        "────────────────────────\n"
        f"Zone : {zone_low:.4f} → {zone_high:.4f} ({width_pips:.1f} pips)\n"
        f"Verdict : {verdict} | conf {confidence:.2f}\n"
        f"Requalifié : {requalified_event}\n"
        f"Visibility : {data_visibility}\n"
        "────────────────────────\n"
        f"Source : {source_stack}\n"
        f"{FINAL_LINE}"
    )

    _assert_message_is_clean(message)
    return message


def _extract_verdict(node: Dict[str, Any], requalified: Dict[str, Any]) -> str:
    raw = node.get("price_verdict") or requalified.get("price_verdict")
    if isinstance(raw, dict):
        raw = raw.get("verdict") or raw.get("price_verdict")
    if raw is None:
        raw = node.get("verdict") or requalified.get("verdict") or "INCONCLUSIVE"
    return str(raw).upper()


def _extract_confidence(node: Dict[str, Any], requalified: Dict[str, Any]) -> float:
    raw = node.get("price_verdict") or requalified.get("price_verdict")
    if isinstance(raw, dict) and raw.get("confidence") is not None:
        return _safe_float(raw.get("confidence"), 0.0)
    for key in ("price_verdict_confidence", "confidence", "requalified_confidence"):
        if node.get(key) is not None:
            return _safe_float(node.get(key), 0.0)
        if requalified.get(key) is not None:
            return _safe_float(requalified.get(key), 0.0)
    return 0.0


def _extract_float(node: Dict[str, Any], keys: tuple[str, ...], default: float) -> float:
    for key in keys:
        if node.get(key) is not None:
            return _safe_float(node.get(key), default)
    zone = node.get("zone")
    if isinstance(zone, dict):
        for key in keys:
            if zone.get(key) is not None:
                return _safe_float(zone.get(key), default)
    return default


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _assert_message_is_clean(message: str) -> None:
    if not message.endswith(FINAL_LINE):
        raise ValueError("B9 Telegram message must end with doctrinal final line")

    lower = message.lower()
    for word in FORBIDDEN_WORDS:
        if word in lower:
            raise ValueError(f"Forbidden Telegram wording detected: {word}")

# B9_RUNTIME_CONTRACT_COMPAT_V5 telegram facade
try:
    _B9_V5_ORIGINAL_SEND_B9_ALERT = send_b9_alert
except NameError:  # pragma: no cover
    _B9_V5_ORIGINAL_SEND_B9_ALERT = None


def send_b9_alert(*args, **kwargs):
    """Dry-run default compatibility facade for B9 alert transmission."""
    original = _B9_V5_ORIGINAL_SEND_B9_ALERT
    enable = bool(kwargs.get("enable") or kwargs.get("ENABLE_TELEGRAM") or kwargs.get("send", False))
    if original is not None and enable:
        return original(*args, **kwargs)
    return {
        "status": "DRY_RUN",
        "alert_sent": False,
        "channel": "telegram_disabled",
        "limits": ["telegram compatibility facade dry-run"],
    }


def send_telegram_alert_b9(*args, **kwargs):
    return send_b9_alert(*args, **kwargs)
