#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Telegram Trader Alert V0.1.1

Reads output/trader_alert_state.json and output/runtime_status.json, builds a short
Telegram-ready trader message, applies mode filtering and cooldown anti-spam, then
sends through Telegram when configured.

PowerFlow boundary:
- reads JSON outputs only
- never reads or writes powerflow.db
- does not import pf_* or cockpit_*
- does not emit BUY/SELL wording
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

VERSION = "0.1.1"

DEFAULT_TRADER_PATH = Path("output/trader_alert_state.json")
DEFAULT_RUNTIME_PATH = Path("output/runtime_status.json")
DEFAULT_LAST_PATH = Path("output/telegram_trader_alert_last.json")
DEFAULT_ENV_PATH = Path(".env")
DEFAULT_COOLDOWN_SECONDS = 300
DEFAULT_SYMBOL = "GBPUSD"

MODES = {"OFF", "HOT_ONLY", "SCALPING", "SYSTEM_ONLY"}
TRADER_FRESHNESS_OK = {"FRESH", "RECENT"}
SYSTEM_SEND_STATUSES = {"WARN", "FAIL"}

# Keep Telegram trader messages clean. PowerFlow alerts wake attention, they do not order.
FORBIDDEN_SIGNAL_WORDS = re.compile(
    r"\b(BUY|SELL|LONG|SHORT|ACHAT|VENTE|ACHETER|VENDRE)\b",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class Decision:
    mode: str
    verdict: str
    should_send: bool
    duplicate: bool
    message_kind: str
    message: str = ""
    key: str = ""
    reason: str = ""
    symbol: str = DEFAULT_SYMBOL
    level: str = ""
    freshness: str = ""
    age_seconds: Optional[int] = None


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return utc_now().isoformat(timespec="seconds")


def normalize_upper(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value).strip().upper() or default


def safe_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def load_json(path: Path, default: Any) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return default
    except json.JSONDecodeError as exc:
        return {"_error": f"JSON_DECODE_ERROR: {exc}"}
    except OSError as exc:
        return {"_error": f"READ_ERROR: {exc}"}


def write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    tmp_path.replace(path)


def load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return values

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
            os.environ.setdefault(key, value)
    return values


def iter_dicts(obj: Any) -> Iterable[Mapping[str, Any]]:
    if isinstance(obj, Mapping):
        yield obj
        for value in obj.values():
            yield from iter_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_dicts(item)


def find_value(data: Any, keys: Iterable[str]) -> Any:
    wanted = {k.lower() for k in keys}
    for d in iter_dicts(data):
        for key, value in d.items():
            if str(key).lower() in wanted:
                return value
    return None


def find_first_string(data: Any, keys: Iterable[str]) -> str:
    value = find_value(data, keys)
    if isinstance(value, list):
        parts = [str(x).strip() for x in value if str(x).strip()]
        return "\n".join(parts)
    if value is None:
        return ""
    return str(value).strip()


def find_bool(data: Any, keys: Iterable[str], default: bool = False) -> bool:
    value = find_value(data, keys)
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "ok", "ready"}:
        return True
    if text in {"0", "false", "no", "n", "none", "not_ready"}:
        return False
    return default


def clean_text(text: str, max_lines: int = 3, max_chars: int = 320) -> str:
    if not text:
        return "Scène PowerFlow active. Lecture trader requise."

    text = FORBIDDEN_SIGNAL_WORDS.sub("WATCH", text)
    text = re.sub(r"[ \t]+", " ", text)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Scène PowerFlow active. Lecture trader requise."

    text = "\n".join(lines[:max_lines]).strip()
    if len(text) > max_chars:
        text = text[: max_chars - 1].rstrip() + "…"
    return text


def extract_symbol(trader: Any, runtime: Any) -> str:
    symbol = find_first_string(trader, ["symbol", "pair", "instrument"])
    if not symbol:
        symbol = find_first_string(runtime, ["symbol", "pair", "instrument"])
    return symbol.upper() if symbol else DEFAULT_SYMBOL


def extract_trader_message(trader: Any) -> str:
    keys = [
        "trader_message",
        "short_message",
        "message_short",
        "message",
        "main_message",
        "summary",
        "scene",
        "scene_message",
        "text",
    ]
    return clean_text(find_first_string(trader, keys), max_lines=3, max_chars=320)


def extract_alert_title(trader: Any) -> str:
    title = find_first_string(
        trader,
        ["alert_id", "id", "title", "alert_title", "event_title", "name", "family", "type"],
    )
    if title:
        return title
    return extract_trader_message(trader).splitlines()[0][:120]


def extract_trader_ready(trader: Any) -> bool:
    return find_bool(trader, ["trader_alert_ready", "ready", "is_ready"], default=False)


def extract_level(trader: Any) -> str:
    return normalize_upper(find_value(trader, ["level", "severity", "alert_level"]), default="INFO")


def extract_freshness(trader: Any) -> str:
    return normalize_upper(find_value(trader, ["freshness", "freshness_status", "age_status"]), default="UNKNOWN")


def extract_age_seconds(trader: Any) -> Optional[int]:
    return safe_int(find_value(trader, ["age_seconds", "age_sec", "age", "alert_age_seconds"]))


def build_trader_message(symbol: str, level: str, trader_message: str, age: Optional[int], freshness: str) -> str:
    level = normalize_upper(level, "INFO")
    freshness = normalize_upper(freshness, "UNKNOWN")
    age_text = "?" if age is None else str(age)

    if level == "HOT":
        header = f"🔥 {symbol} — HOT"
        return f"{header}\n\n{trader_message}\nÂge : {age_text}s | {freshness}\nAction : WATCH"

    if level == "WATCH":
        header = f"👁 {symbol} — WATCH"
        return f"{header}\n\n{trader_message}\nÂge : {age_text}s | {freshness}"

    header = f"ℹ️ {symbol} — {level}"
    return f"{header}\n\n{trader_message}\nÂge : {age_text}s | {freshness}"


def extract_runtime_status(runtime: Any) -> str:
    return normalize_upper(find_value(runtime, ["status", "runtime_status", "state"]), default="UNKNOWN")


def extract_runtime_warning(runtime: Any) -> str:
    text = find_first_string(
        runtime,
        ["warning", "warning_message", "message", "reason", "error", "detail", "details", "summary"],
    )
    return clean_text(text or "Runtime PowerFlow à vérifier.", max_lines=2, max_chars=220)


def build_system_message(runtime: Any, trader: Any) -> str:
    status = extract_runtime_status(runtime)
    warning = extract_runtime_warning(runtime)
    dashboard_ready = find_bool(runtime, ["dashboard_ready", "dashboard_sync_ready"], default=False)
    trader_ready = extract_trader_ready(trader)
    return (
        f"⚠️ POWERFLOW {status}\n\n"
        f"{warning}\n"
        f"dashboard_ready={str(dashboard_ready).lower()}\n"
        f"trader_alert_ready={str(trader_ready).lower()}"
    )


def stable_hash(text: str, length: int = 16) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:length]


def build_key(mode: str, symbol: str, level: str, title: str, message_kind: str) -> str:
    base = "|".join([message_kind, symbol.upper(), level.upper(), title.strip()])
    return f"{mode}:{stable_hash(base)}"


def load_last_state(path: Path) -> Dict[str, Any]:
    state = load_json(path, default={})
    return state if isinstance(state, dict) else {}


def parse_iso_datetime(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def is_duplicate(last_state: Mapping[str, Any], key: str, cooldown_seconds: int) -> Tuple[bool, Optional[int]]:
    history = last_state.get("history")
    if not isinstance(history, Mapping):
        return False, None

    item = history.get(key)
    if not isinstance(item, Mapping):
        return False, None

    sent_at = parse_iso_datetime(item.get("sent_at"))
    if not sent_at:
        return False, None

    elapsed = int((utc_now() - sent_at).total_seconds())
    return elapsed < cooldown_seconds, elapsed


def trim_history(history: Mapping[str, Any], max_items: int = 200) -> Dict[str, Any]:
    items: List[Tuple[str, Any]] = list(history.items())

    def sort_key(item: Tuple[str, Any]) -> str:
        value = item[1]
        if isinstance(value, Mapping):
            return str(value.get("sent_at", ""))
        return ""

    items.sort(key=sort_key, reverse=True)
    return dict(items[:max_items])


def decide(mode: str, trader: Any, runtime: Any, last_state: Mapping[str, Any], cooldown_seconds: int) -> Decision:
    mode = normalize_upper(mode)
    symbol = extract_symbol(trader, runtime)

    if mode == "OFF":
        return Decision(
            mode=mode,
            verdict="OFF_SILENCE",
            should_send=False,
            duplicate=False,
            message_kind="off",
            reason="mode OFF",
            symbol=symbol,
        )

    if mode == "SYSTEM_ONLY":
        runtime_status = extract_runtime_status(runtime)
        if runtime_status not in SYSTEM_SEND_STATUSES:
            return Decision(
                mode=mode,
                verdict="NO_SEND_RUNTIME_OK",
                should_send=False,
                duplicate=False,
                message_kind="system",
                reason=f"runtime_status={runtime_status}",
                symbol=symbol,
            )

        message = clean_text(build_system_message(runtime, trader), max_lines=6, max_chars=420)
        title = f"runtime:{runtime_status}"
        key = build_key(mode, "POWERFLOW", runtime_status, title, "system")
        duplicate, elapsed = is_duplicate(last_state, key, cooldown_seconds)
        if duplicate:
            return Decision(
                mode=mode,
                verdict="NO_SEND_DUPLICATE",
                should_send=False,
                duplicate=True,
                message_kind="system",
                message=message,
                key=key,
                reason=f"cooldown active elapsed={elapsed}s",
                symbol="POWERFLOW",
                level=runtime_status,
            )
        return Decision(
            mode=mode,
            verdict="MESSAGE_READY",
            should_send=True,
            duplicate=False,
            message_kind="system",
            message=message,
            key=key,
            symbol="POWERFLOW",
            level=runtime_status,
        )

    trader_ready = extract_trader_ready(trader)
    if not trader_ready:
        return Decision(
            mode=mode,
            verdict="NO_SEND_TRADER_ALERT_NOT_READY",
            should_send=False,
            duplicate=False,
            message_kind="trader",
            reason="trader_alert_ready=false",
            symbol=symbol,
        )

    level = extract_level(trader)
    freshness = extract_freshness(trader)
    age = extract_age_seconds(trader)

    if freshness not in TRADER_FRESHNESS_OK:
        return Decision(
            mode=mode,
            verdict="NO_SEND_STALE_OR_UNKNOWN",
            should_send=False,
            duplicate=False,
            message_kind="trader",
            reason=f"freshness={freshness}",
            symbol=symbol,
            level=level,
            freshness=freshness,
            age_seconds=age,
        )

    if mode == "HOT_ONLY" and level != "HOT":
        return Decision(
            mode=mode,
            verdict="NO_SEND_LEVEL_FILTER",
            should_send=False,
            duplicate=False,
            message_kind="trader",
            reason=f"level={level}",
            symbol=symbol,
            level=level,
            freshness=freshness,
            age_seconds=age,
        )

    if mode == "SCALPING" and level not in {"HOT", "WATCH"}:
        return Decision(
            mode=mode,
            verdict="NO_SEND_LEVEL_FILTER",
            should_send=False,
            duplicate=False,
            message_kind="trader",
            reason=f"level={level}",
            symbol=symbol,
            level=level,
            freshness=freshness,
            age_seconds=age,
        )

    trader_message = extract_trader_message(trader)
    message = build_trader_message(symbol, level, trader_message, age, freshness)
    title = extract_alert_title(trader)
    key = build_key(mode, symbol, level, title, "trader")
    duplicate, elapsed = is_duplicate(last_state, key, cooldown_seconds)
    if duplicate:
        return Decision(
            mode=mode,
            verdict="NO_SEND_DUPLICATE",
            should_send=False,
            duplicate=True,
            message_kind="trader",
            message=message,
            key=key,
            reason=f"cooldown active elapsed={elapsed}s",
            symbol=symbol,
            level=level,
            freshness=freshness,
            age_seconds=age,
        )

    return Decision(
        mode=mode,
        verdict="MESSAGE_READY",
        should_send=True,
        duplicate=False,
        message_kind="trader",
        message=message,
        key=key,
        symbol=symbol,
        level=level,
        freshness=freshness,
        age_seconds=age,
    )


def telegram_configured() -> Tuple[Optional[str], Optional[str]]:
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    return token or None, chat_id or None


def send_telegram_message(token: str, chat_id: str, text: str, timeout: int) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode(
        {
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": "true",
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(body) if body else {}
            return {"ok": bool(parsed.get("ok")), "http_status": response.status, "response": parsed}
    except Exception as exc:  # noqa: BLE001 - operational script, must not crash live loop
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def build_trace(
    decision: Decision,
    dry_run: bool,
    configured: bool,
    telegram_result: Optional[Mapping[str, Any]],
    prior_state: Mapping[str, Any],
) -> Dict[str, Any]:
    trace: Dict[str, Any] = {
        "version": VERSION,
        "updated_at": iso_now(),
        "mode": decision.mode,
        "verdict": decision.verdict,
        "should_send": decision.should_send,
        "duplicate": decision.duplicate,
        "dry_run": dry_run,
        "configured": configured,
        "message_kind": decision.message_kind,
        "key": decision.key,
        "reason": decision.reason,
        "symbol": decision.symbol,
        "level": decision.level,
        "freshness": decision.freshness,
        "age_seconds": decision.age_seconds,
        "message_preview": decision.message,
        "telegram_result": dict(telegram_result or {}),
    }

    history_raw = prior_state.get("history")
    history = dict(history_raw) if isinstance(history_raw, Mapping) else {}

    actually_sent = (
        decision.should_send
        and not decision.duplicate
        and not dry_run
        and bool(telegram_result and telegram_result.get("ok"))
    )
    if actually_sent and decision.key:
        history[decision.key] = {
            "sent_at": trace["updated_at"],
            "mode": decision.mode,
            "message_kind": decision.message_kind,
            "symbol": decision.symbol,
            "level": decision.level,
            "freshness": decision.freshness,
            "age_seconds": decision.age_seconds,
            "message_preview": decision.message,
        }
        trace["last_sent_at"] = trace["updated_at"]
        trace["last_sent_key"] = decision.key
    else:
        trace["last_sent_at"] = prior_state.get("last_sent_at")
        trace["last_sent_key"] = prior_state.get("last_sent_key")

    trace["history"] = trim_history(history)
    return trace


def print_summary(decision: Decision, dry_run: bool, configured: bool, telegram_result: Optional[Mapping[str, Any]]) -> None:
    print(f"MODE: {decision.mode}")
    print(f"VERDICT: {decision.verdict}")
    print(f"SHOULD_SEND: {decision.should_send}")
    print(f"DUPLICATE: {decision.duplicate}")
    print(f"DRY_RUN: {dry_run}")
    print(f"CONFIGURED: {configured}")
    if decision.reason:
        print(f"REASON: {decision.reason}")
    if decision.key:
        print(f"KEY: {decision.key}")
    if telegram_result:
        print(f"TELEGRAM_OK: {telegram_result.get('ok')}")
    if decision.message:
        print("MESSAGE:")
        print(decision.message)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow Telegram Trader Alert V0.1")
    parser.add_argument("--mode", choices=sorted(MODES), default="HOT_ONLY")
    parser.add_argument("--trader", default=str(DEFAULT_TRADER_PATH), help="Path to trader_alert_state.json")
    parser.add_argument("--runtime", default=str(DEFAULT_RUNTIME_PATH), help="Path to runtime_status.json")
    parser.add_argument("--last", default=str(DEFAULT_LAST_PATH), help="Path to anti-spam trace JSON")
    parser.add_argument("--env", default=str(DEFAULT_ENV_PATH), help="Path to .env")
    parser.add_argument("--cooldown-seconds", type=int, default=DEFAULT_COOLDOWN_SECONDS)
    parser.add_argument("--timeout", type=int, default=10)
    parser.add_argument("--dry-run", action="store_true", help="Build message but do not send Telegram")
    parser.add_argument("--summary", action="store_true", help="Print compact decision summary")
    parser.add_argument("--print-message", action="store_true", help="Print only the built Telegram message when available")
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)

    mode = normalize_upper(args.mode)
    trader_path = Path(args.trader)
    runtime_path = Path(args.runtime)
    last_path = Path(args.last)
    env_path = Path(args.env)

    load_env_file(env_path)

    trader = load_json(trader_path, default={})
    runtime = load_json(runtime_path, default={})
    last_state = load_last_state(last_path)

    decision = decide(
        mode=mode,
        trader=trader,
        runtime=runtime,
        last_state=last_state,
        cooldown_seconds=max(0, int(args.cooldown_seconds)),
    )

    token, chat_id = telegram_configured()
    configured = bool(token and chat_id)
    telegram_result: Optional[Dict[str, Any]] = None

    if decision.should_send and not decision.duplicate:
        if args.dry_run:
            telegram_result = {"ok": True, "dry_run": True, "status": "DRY_RUN_MESSAGE_READY"}
        elif not configured:
            decision = Decision(
                mode=decision.mode,
                verdict="TELEGRAM_NOT_CONFIGURED",
                should_send=False,
                duplicate=decision.duplicate,
                message_kind=decision.message_kind,
                message=decision.message,
                key=decision.key,
                reason="missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID",
                symbol=decision.symbol,
                level=decision.level,
                freshness=decision.freshness,
                age_seconds=decision.age_seconds,
            )
            telegram_result = {"ok": False, "status": "TELEGRAM_NOT_CONFIGURED"}
        else:
            telegram_result = send_telegram_message(token=token or "", chat_id=chat_id or "", text=decision.message, timeout=args.timeout)
            if not telegram_result.get("ok"):
                decision = Decision(
                    mode=decision.mode,
                    verdict="TELEGRAM_SEND_FAILED",
                    should_send=False,
                    duplicate=decision.duplicate,
                    message_kind=decision.message_kind,
                    message=decision.message,
                    key=decision.key,
                    reason=str(telegram_result.get("error") or telegram_result.get("response") or "unknown error"),
                    symbol=decision.symbol,
                    level=decision.level,
                    freshness=decision.freshness,
                    age_seconds=decision.age_seconds,
                )
    else:
        telegram_result = {"ok": False, "status": decision.verdict}

    trace = build_trace(
        decision=decision,
        dry_run=bool(args.dry_run),
        configured=configured,
        telegram_result=telegram_result,
        prior_state=last_state,
    )
    write_json(last_path, trace)

    if args.summary:
        print_summary(decision, bool(args.dry_run), configured, telegram_result)

    if args.print_message and decision.message:
        print(decision.message)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
