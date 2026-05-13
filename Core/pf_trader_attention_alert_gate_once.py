#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.6 — Trader Attention Alert Gate

Purpose:
- Convert trader_attention_packet.json into sparse, pertinent alerts.
- Do NOT alert on every refresh.
- Alert only on meaningful film changes, first release, next_wake change, score jump, or high-score loading.
- Maintain per-symbol dedup/cooldown state.
- Optionally send Telegram if credentials are available.

Inputs:
    output/dashboard_surface/<SYMBOL>/trader_attention_packet.json

Outputs:
    output/dashboard_surface/<SYMBOL>/trader_attention_alert_state.json
    output/dashboard_surface/<SYMBOL>/trader_attention_last_alert.json
    output/dashboard_surface/<SYMBOL>/trader_attention_last_alert.txt
    output/dashboard_surface/trader_attention_alerts.jsonl

Telegram sources, in priority:
    --bot-token / --chat-id
    env POWERFLOW_TELEGRAM_BOT_TOKEN / POWERFLOW_TELEGRAM_CHAT_ID
    env TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID
    system_config.py attributes if present

Doctrine:
- Alert is perception, not an order.
- Early alerts are qualified, not censored.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
SURFACE = ROOT / "output" / "dashboard_surface"


RELEASE_FILM_KEYWORDS = (
    "ELASTIC_RELEASE",
    "RELEASE",
    "TIME_COMP_RELEASE",
)

LOADING_FILM_KEYWORDS = (
    "ELASTIC_LOADING",
    "MULTI_TF_ELASTIC_LOADING",
    "COMPRESSION_LOADING",
)

CRITICAL_NEXT_WAKE = (
    "LOCK_ACCEPTANCE_AFTER_RELEASE",
    "TIME_COMP_BREAK",
    "COMPRESSION_BREAK",
    "KISS_REJECT",
    "SLINGSHOT",
    "ZONE_REJECTION",
    "SECOND_LEG",
    "COUNTER_BREATH",
)

IMPORTANT_RISKS = (
    "EVENT_TIME_AHEAD_OF_DETECTED_AT",
    "EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE",
    "GBPUSD_TEMPORAL_GAPS",
    "EURUSD_TEMPORAL_GAPS",
    "USDJPY_TEMPORAL_GAPS",
    "TIME_SYNC",
)


@dataclass
class GateDecision:
    should_alert: bool
    reason: str
    severity: str
    fingerprint: str
    message: str
    alert: dict[str, Any]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _append_jsonl(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n")


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    if isinstance(value, str):
        return [x.strip() for x in value.replace("|", ",").split(",") if x.strip()]
    return [str(value)]


def _get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in data and data[key] not in (None, "", [], {}):
            return data[key]
    return default


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _contains_any(text: str, needles: Iterable[str]) -> bool:
    upper = (text or "").upper()
    return any(needle in upper for needle in needles)


def _symbol_dir(symbol: str) -> Path:
    return SURFACE / symbol.upper()


def _packet_path(symbol: str) -> Path:
    return _symbol_dir(symbol) / "trader_attention_packet.json"


def _state_path(symbol: str) -> Path:
    return _symbol_dir(symbol) / "trader_attention_alert_state.json"


def _last_alert_json_path(symbol: str) -> Path:
    return _symbol_dir(symbol) / "trader_attention_last_alert.json"


def _last_alert_txt_path(symbol: str) -> Path:
    return _symbol_dir(symbol) / "trader_attention_last_alert.txt"


def _global_alerts_jsonl() -> Path:
    return SURFACE / "trader_attention_alerts.jsonl"


def _risk_short(risks: list[str], limit: int = 3) -> list[str]:
    out: list[str] = []
    risk_text = ",".join(risks)
    for risk in IMPORTANT_RISKS:
        if risk in risk_text and risk not in out:
            out.append(risk)
    for risk in risks:
        if risk not in out:
            out.append(risk)
        if len(out) >= limit:
            break
    return out[:limit]


def _normalize_attention(attention: str) -> str:
    a = (attention or "").upper()
    if "WAKE" in a:
        return "WAKE"
    if "WATCH" in a:
        return "WATCH"
    if "OBSERVE" in a:
        return "OBSERVE"
    if "IDLE" in a:
        return "IDLE"
    return a or "UNKNOWN"


def _build_fingerprint(symbol: str, film: str, next_wake: str, bias: str, conflict: str) -> str:
    # Do not include raw score: score changes alone are handled by score jump rule.
    return "|".join([
        symbol.upper(),
        (film or "UNKNOWN").upper(),
        (next_wake or "NONE").upper(),
        (bias or "UNKNOWN").upper(),
        (conflict or "NONE").upper(),
    ])


def _human_reason(reason: str) -> str:
    mapping = {
        "FIRST_RELEASE": "premier relâchement détecté",
        "FILM_CHANGED": "changement de film",
        "NEXT_WAKE_CHANGED": "nouveau réveil à surveiller",
        "SCORE_JUMP": "accélération perceptive",
        "HIGH_SCORE_LOADING": "chargement multi-TF dense",
        "FIRST_PERTINENT_STATE": "première perception pertinente",
    }
    return mapping.get(reason, reason)


def _message_from_packet(
    symbol: str,
    packet: dict[str, Any],
    *,
    reason: str,
    severity: str,
) -> str:
    attention = str(_get(packet, "attention", "attention_level", default="UNKNOWN"))
    film = str(_get(packet, "main_film", "film", "state", default="UNKNOWN"))
    bias = str(_get(packet, "bias", default="UNKNOWN"))
    next_wake = str(_get(packet, "next_wake", "wake", "next", default="NONE"))
    score = round(_float(_get(packet, "score", default=0.0)), 2)
    conflict = str(_get(packet, "conflict", "main_conflict", default="NONE"))
    narrative = str(_get(packet, "narrative", "summary", "message", default="")).strip()
    risks = _risk_short(_as_list(_get(packet, "technical_risks", default=[])))

    if not narrative:
        if "RELEASE" in film.upper():
            narrative = "Élastique relâché — attendre acceptation, second leg ou rejet de zone."
        elif "LOADING" in film.upper():
            narrative = "Élastique multi-TF chargé — attendre détachement ou répulsion."
        else:
            narrative = "Perception PowerFlow active."

    lines = [
        f"POWERFLOW | {symbol.upper()} | {severity}",
        f"{film} | bias={bias} | score={score}",
        narrative,
        f"Réveil: {next_wake}",
        f"Raison: {_human_reason(reason)}",
    ]

    if conflict and conflict not in ("NONE", "NA"):
        lines.append(f"Conflit: {conflict}")

    if risks:
        lines.append("Tech: " + " | ".join(risks))

    return "\n".join(lines)


def decide_alert(
    symbol: str,
    packet: dict[str, Any],
    state: dict[str, Any],
    *,
    cooldown_seconds: int,
    repeat_after_seconds: int,
    release_threshold: float,
    loading_threshold: float,
    score_jump: float,
) -> GateDecision:
    now_ts = time.time()
    now_iso = _utc_now()

    attention_raw = str(_get(packet, "attention", "attention_level", default="UNKNOWN"))
    attention = _normalize_attention(attention_raw)
    film = str(_get(packet, "main_film", "film", "state", default="UNKNOWN"))
    bias = str(_get(packet, "bias", default="UNKNOWN"))
    next_wake = str(_get(packet, "next_wake", "wake", "next", default="NONE"))
    conflict = str(_get(packet, "conflict", "main_conflict", default="NONE"))
    score = _float(_get(packet, "score", default=0.0))

    fingerprint = _build_fingerprint(symbol, film, next_wake, bias, conflict)

    previous_fingerprint = str(state.get("last_fingerprint", ""))
    previous_film = str(state.get("last_film", ""))
    previous_next_wake = str(state.get("last_next_wake", ""))
    previous_score = _float(state.get("last_score", 0.0))
    last_alert_at = _float(state.get("last_alert_at", 0.0))

    seconds_since_alert = now_ts - last_alert_at if last_alert_at else 10**9
    in_cooldown = seconds_since_alert < cooldown_seconds
    stale_repeat_ok = seconds_since_alert >= repeat_after_seconds

    is_wake = attention == "WAKE" or "WAKE" in attention_raw.upper()
    is_watch = attention == "WATCH" or "WATCH" in attention_raw.upper()
    is_release = _contains_any(film, RELEASE_FILM_KEYWORDS)
    is_loading = _contains_any(film, LOADING_FILM_KEYWORDS)
    critical_next = _contains_any(next_wake, CRITICAL_NEXT_WAKE)

    reason = ""
    severity = "INFO"

    pertinent = False
    if is_release and score >= release_threshold:
        pertinent = True
        reason = "FIRST_RELEASE"
        severity = "WAKE"
    elif is_loading and score >= loading_threshold and (is_wake or is_watch):
        pertinent = True
        reason = "HIGH_SCORE_LOADING"
        severity = "WATCH"
    elif critical_next and (is_wake or is_watch) and score >= release_threshold:
        pertinent = True
        reason = "NEXT_WAKE_CHANGED"
        severity = "WAKE"

    if not pertinent:
        state_update = {
            "last_seen_at": now_iso,
            "last_fingerprint": fingerprint,
            "last_film": film,
            "last_next_wake": next_wake,
            "last_score": score,
            "last_attention": attention_raw,
        }
        return GateDecision(False, "NOT_PERTINENT", "NONE", fingerprint, "", {"state_update": state_update})

    # Transition refinements
    if not previous_fingerprint:
        reason = "FIRST_PERTINENT_STATE"
    elif previous_film and film != previous_film:
        reason = "FILM_CHANGED"
        severity = "WAKE"
    elif previous_next_wake and next_wake != previous_next_wake:
        reason = "NEXT_WAKE_CHANGED"
        severity = "WAKE"
    elif score - previous_score >= score_jump:
        reason = "SCORE_JUMP"
        severity = "WAKE" if is_release else "WATCH"

    duplicate = fingerprint == previous_fingerprint
    should_alert = True

    if in_cooldown and duplicate:
        should_alert = False
        reason = "DEDUP_COOLDOWN"
    elif duplicate and not stale_repeat_ok:
        should_alert = False
        reason = "DEDUP_REPEAT_WAIT"

    message = _message_from_packet(symbol, packet, reason=reason, severity=severity)

    alert = {
        "source": "trader_attention_alert_gate",
        "method": "TRADER_ATTENTION_ALERT_GATE_V76A",
        "symbol": symbol.upper(),
        "created_at": now_iso,
        "should_alert": should_alert,
        "reason": reason,
        "severity": severity,
        "fingerprint": fingerprint,
        "attention": attention_raw,
        "film": film,
        "bias": bias,
        "next_wake": next_wake,
        "score": score,
        "conflict": conflict,
        "technical_risks": _risk_short(_as_list(_get(packet, "technical_risks", default=[]))),
        "message": message,
        "state_update": {
            "last_seen_at": now_iso,
            "last_fingerprint": fingerprint,
            "last_film": film,
            "last_next_wake": next_wake,
            "last_score": score,
            "last_attention": attention_raw,
            "last_decision_reason": reason,
            "last_alert_at": now_ts if should_alert else last_alert_at,
            "last_alert_created_at": now_iso if should_alert else state.get("last_alert_created_at"),
        },
    }

    return GateDecision(should_alert, reason, severity, fingerprint, message, alert)


def _load_telegram_config(args: argparse.Namespace) -> tuple[str | None, str | None]:
    token = args.bot_token or os.getenv("POWERFLOW_TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = args.chat_id or os.getenv("POWERFLOW_TELEGRAM_CHAT_ID") or os.getenv("TELEGRAM_CHAT_ID")

    if token and chat_id:
        return token, chat_id

    try:
        import system_config  # type: ignore

        for token_name in ("POWERFLOW_TELEGRAM_BOT_TOKEN", "TELEGRAM_BOT_TOKEN", "BOT_TOKEN", "TELEGRAM_TOKEN"):
            if not token and hasattr(system_config, token_name):
                token = str(getattr(system_config, token_name))
        for chat_name in ("POWERFLOW_TELEGRAM_CHAT_ID", "TELEGRAM_CHAT_ID", "CHAT_ID", "TELEGRAM_DEFAULT_CHAT_ID"):
            if not chat_id and hasattr(system_config, chat_name):
                chat_id = str(getattr(system_config, chat_name))
    except Exception:
        pass

    return token, chat_id


def send_telegram(message: str, token: str, chat_id: str) -> tuple[bool, str]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8", errors="replace")
        return True, body[:500]
    except Exception as exc:
        return False, str(exc)


def process_symbol(symbol: str, args: argparse.Namespace) -> int:
    sym = symbol.upper()
    packet = _safe_read_json(_packet_path(sym))
    if not packet:
        print(f"{sym} | ALERT_GATE | NO_PACKET")
        return 2

    state = _safe_read_json(_state_path(sym))

    decision = decide_alert(
        sym,
        packet,
        state,
        cooldown_seconds=args.cooldown_seconds,
        repeat_after_seconds=args.repeat_after_seconds,
        release_threshold=args.release_threshold,
        loading_threshold=args.loading_threshold,
        score_jump=args.score_jump,
    )

    alert = decision.alert
    state_update = alert.get("state_update", {})
    if isinstance(state_update, dict):
        merged_state = {**state, **state_update}
        _write_json(_state_path(sym), merged_state)

    if not decision.should_alert:
        if args.pretty:
            print(f"{sym} | ALERT_GATE | QUIET | reason={decision.reason}")
        return 0

    _write_json(_last_alert_json_path(sym), alert)
    _last_alert_txt_path(sym).write_text(decision.message + "\n", encoding="utf-8")
    _append_jsonl(_global_alerts_jsonl(), alert)

    telegram_status = ""
    if args.send_telegram:
        token, chat_id = _load_telegram_config(args)
        if token and chat_id:
            ok, detail = send_telegram(decision.message, token, chat_id)
            telegram_status = "TELEGRAM_OK" if ok else f"TELEGRAM_FAIL:{detail}"
            alert["telegram_status"] = telegram_status
            _write_json(_last_alert_json_path(sym), alert)
        else:
            telegram_status = "TELEGRAM_CONFIG_MISSING"
            alert["telegram_status"] = telegram_status
            _write_json(_last_alert_json_path(sym), alert)

    if args.pretty:
        print(decision.message)
        if telegram_status:
            print(telegram_status)
    else:
        print(f"{sym} | ALERT | {decision.severity} | {decision.reason} | {alert.get('film')} | next={alert.get('next_wake')}")
        if telegram_status:
            print(telegram_status)

    return 0


def parse_symbols(raw: str | None, fallback: str) -> list[str]:
    src = raw if raw else fallback
    out: list[str] = []
    seen: set[str] = set()
    for part in src.split(","):
        sym = part.strip().upper()
        if sym and sym not in seen:
            out.append(sym)
            seen.add(sym)
    return out or ["GBPUSD"]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.6 Trader Attention Alert Gate")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--cooldown-seconds", type=int, default=180)
    parser.add_argument("--repeat-after-seconds", type=int, default=900)
    parser.add_argument("--release-threshold", type=float, default=70.0)
    parser.add_argument("--loading-threshold", type=float, default=78.0)
    parser.add_argument("--score-jump", type=float, default=5.0)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--send-telegram", action="store_true")
    parser.add_argument("--bot-token", default=None)
    parser.add_argument("--chat-id", default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    symbols = parse_symbols(args.symbols, args.symbol)
    codes = [process_symbol(sym, args) for sym in symbols]
    return 0 if all(code == 0 for code in codes) else 1


if __name__ == "__main__":
    raise SystemExit(main())
