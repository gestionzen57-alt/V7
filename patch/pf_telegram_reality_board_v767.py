#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.6.7 - Reality Board Telegram primary.

Mission
-------
Make the Telegram message speak from the Reality Board, not from raw V7.6
technical packets. The old V7.6 qualified alert can remain a dry-run/debug
trace; this script is the trader-facing Telegram surface.

No trading decision is emitted here. This is a terrain-reading alert.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


# PF_V767_STDOUT_UTF8_SAFE_V2
# Avoid Windows cp1252 dry-run crash on arrows/accents in trader-facing text.
try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
# PF_V767_STDOUT_UTF8_SAFE_V2_END


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SYMBOL = "GBPUSD"
DEFAULT_MODE = "dry-run"

RAW_DISPLAY_TERMS = [
    "DATA FIRST",
    "REALITY BOARD",
    "ALIGNED_OR_PARTIAL",
    "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND",
    "READING_PARTIAL",
    "HIGH_ZONE_EXHAUSTION_RISK",
]

FR_MAP = {
    "DATA FIRST": "LECTURE TERRAIN",
    "REALITY BOARD": "RÉALITÉ MARCHÉ",
    "Reality Board": "Réalité marché",
    "ALIGNED_OR_PARTIAL": "alignement partiel",
    "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND": "high tardif rejeté puis unwind profond",
    "READING_PARTIAL": "lecture partielle",
    "HIGH_ZONE_EXHAUSTION_RISK": "risque d’épuisement en zone haute",
    "HIGH_ZONE_REJECTION": "rejet de zone haute",
    "EXHAUSTION_RISK": "risque d’épuisement",
    "PRICE_REJECTED_LOW": "prix rejeté en bas",
    "LTF_MTF_RELAY": "relais LTF vers MTF",
    "REJECTION_DETACHMENT": "détachement de rejet",
    "PAIR_UP": "poussée haussière brute",
    "PAIR_DOWN": "pression baissière brute",
    "UNKNOWN": "non déterminé",
    "MEDIUM": "moyen",
    "LOW": "faible",
    "HIGH": "fort",
}

MOJIBAKE_FIXES = {
    "Ã©": "é",
    "Ã¨": "è",
    "Ãª": "ê",
    "Ã ": "à",
    "Ã´": "ô",
    "Ã®": "î",
    "Ã§": "ç",
    "â€™": "’",
    "â€”": "-",
    "â€“": "-",
    "â†’": "→",
    "Ã¢â€šÂ¬": "€",
    "Ã‰": "É",
    "Ã€": "À",
}


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        out = value
    else:
        out = str(value)
    for old, new in MOJIBAKE_FIXES.items():
        out = out.replace(old, new)
    for old, new in FR_MAP.items():
        out = out.replace(old, new)
    while "Alternative : Alternative :" in out:
        out = out.replace("Alternative : Alternative :", "Alternative :")
    return out.strip()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Reality Board introuvable: {path}")
    raw = path.read_text(encoding="utf-8", errors="replace")
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError(f"Reality Board invalide: {path}")
    return data


def first_text(*values: Any, default: str = "") -> str:
    for value in values:
        txt = as_text(value)
        if txt and txt.lower() not in {"unknown", "non déterminé", "none", "null"}:
            return txt
    return default


def label_from(state: Mapping[str, Any], key: str, fallback: Any = "") -> str:
    labels = state.get("labels_fr", {})
    if isinstance(labels, Mapping):
        value = labels.get(key)
        if value:
            return as_text(value)
    return as_text(fallback)


def clean_strategy_label(value: Any) -> str:
    txt = as_text(value)
    prefix = "Alternative : "
    while txt.startswith(prefix + prefix):
        txt = txt[len(prefix):]
    if txt.startswith(prefix):
        return txt[len(prefix):].strip()
    return txt


def profile_line(state: Mapping[str, Any], profile: str) -> str:
    roles = state.get("time_profile_roles", {})
    node: Any = {}
    if isinstance(roles, Mapping):
        node = roles.get(profile.lower()) or roles.get(profile.upper()) or {}
    if not isinstance(node, Mapping):
        node = {}

    default_role = {
        "htf": "HTF - Analyse",
        "mtf": "MTF - Plan",
        "ltf": "LTF - Action",
    }[profile.lower()]

    label = first_text(node.get("label_fr"), default=default_role)
    label = label.replace("—", "-").replace("–", "-")

    summary = first_text(node.get("summary_fr"), node.get("state"), default="")
    if not summary:
        return f"{label} : non déterminé"

    if "events_total" in summary or "last_event" in summary or len(summary) > 180:
        candidates: list[str] = []
        for key in ["profile_state", "cycle_phase", "event_type", "bias", "timeframe"]:
            m = re.search(rf"[\"']{key}[\"']\s*:\s*[\"']([^\"']+)[\"']", summary)
            if m:
                candidates.append(as_text(m.group(1)))
        summary = " / ".join(dict.fromkeys(candidates)) if candidates else "lecture disponible"

    summary = summary.replace("PAIR_DOWN", "pression baissière brute").replace("PAIR_UP", "poussée haussière brute")
    return f"{label} : {summary}"


def build_reality_telegram_text(state: Mapping[str, Any]) -> str:
    symbol = as_text(state.get("symbol") or DEFAULT_SYMBOL) or DEFAULT_SYMBOL

    display = state.get("display_fr", {})
    if not isinstance(display, Mapping):
        display = {}

    dominant = state.get("dominant_strategy", {})
    alternative = state.get("alternative_strategy", {})
    trap = state.get("trap", {})

    lecture = first_text(
        dominant.get("label_fr") if isinstance(dominant, Mapping) else "",
        display.get("lecture_active"),
        label_from(state, "qualified_bias_fr", state.get("qualified_bias")),
        default="lecture terrain en cours",
    )
    alternative_txt = clean_strategy_label(
        alternative.get("label_fr") if isinstance(alternative, Mapping) else ""
    )
    trap_txt = first_text(
        trap.get("label_fr") if isinstance(trap, Mapping) else "",
        default="aucun piège dominant identifié",
    )

    b6 = first_text(
        label_from(state, "b6_nearest_film_fr", ""),
        label_from(state, "film_sequence_fr", ""),
        state.get("b6_nearest_film"),
        state.get("film_sequence"),
        default="mémoire non alignée",
    )
    session = first_text(
        label_from(state, "session_alignment_fr", ""),
        display.get("alignement_session"),
        state.get("session_alignment"),
        default="alignement non déterminé",
    )
    data = first_text(
        label_from(state, "data_visibility_fr", ""),
        label_from(state, "reading_status_fr", ""),
        state.get("data_visibility"),
        state.get("reading_status"),
        default="lecture partielle",
    )

    lines = [
        f"{symbol} - Réalité marché",
        "",
        f"Lecture : {lecture}",
        profile_line(state, "htf"),
        profile_line(state, "mtf"),
        profile_line(state, "ltf"),
        f"B6 : {b6}",
        f"Session : {session}",
    ]

    if alternative_txt:
        lines.append(f"Alternative : {alternative_txt}")
    if trap_txt:
        lines.append(f"Piège : {trap_txt}")

    lines += [
        f"Data : {data}",
        "Rappel : lecture terrain, décision trader.",
    ]

    text = "\n".join(as_text(line) for line in lines)
    for raw in RAW_DISPLAY_TERMS:
        text = text.replace(raw, as_text(raw))
    return text.strip()


def fingerprint(text: str, symbol: str) -> str:
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    src = f"{today}|{symbol.upper()}|{text}".encode("utf-8", errors="replace")
    return hashlib.sha256(src).hexdigest()[:16]


def load_telegram_env(root: Path) -> dict[str, str]:
    env = dict(os.environ)

    for rel in [".env", "telegram.env", "config/telegram.env", "Core/telegram.env"]:
        path = root / rel
        if not path.exists():
            continue
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            env.setdefault(key.strip(), value.strip().strip('"').strip("'"))

    for rel in ["telegram_config.json", "config/telegram.json", "Core/telegram_config.json"]:
        path = root / rel
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
        if isinstance(data, Mapping):
            token = data.get("bot_token") or data.get("token") or data.get("TELEGRAM_BOT_TOKEN")
            chat_id = data.get("chat_id") or data.get("TELEGRAM_CHAT_ID")
            if token:
                env.setdefault("TELEGRAM_BOT_TOKEN", str(token))
            if chat_id:
                env.setdefault("TELEGRAM_CHAT_ID", str(chat_id))

    return env


def send_telegram(text: str, root: Path, dry: bool = False) -> dict[str, Any]:
    env = load_telegram_env(root)
    token = (
        env.get("POWERFLOW_TELEGRAM_BOT_TOKEN")
        or env.get("TELEGRAM_BOT_TOKEN")
        or env.get("BOT_TOKEN")
    )
    chat_id = (
        env.get("POWERFLOW_TELEGRAM_CHAT_ID")
        or env.get("TELEGRAM_CHAT_ID")
        or env.get("CHAT_ID")
    )

    if dry:
        return {"sent": False, "dry": True, "reason": "dry-run"}

    if not token or not chat_id:
        return {
            "sent": False,
            "error": "telegram_credentials_missing",
            "hint": "Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, or POWERFLOW_TELEGRAM_BOT_TOKEN and POWERFLOW_TELEGRAM_CHAT_ID.",
        }

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=20) as response:
        body = response.read().decode("utf-8", errors="replace")
    return {"sent": True, "telegram_response": body[:1000]}


def read_sent_memory(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.6.7 Reality Board Telegram primary")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL)
    parser.add_argument("--mode", choices=["dry-run", "live", "candidate-only"], default=DEFAULT_MODE)
    parser.add_argument("--input", default=None)
    parser.add_argument("--out", default=None)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    rb_path = Path(args.input) if args.input else ROOT / "output" / "dashboard_surface" / symbol / "reality_board_state.json"
    out_path = Path(args.out) if args.out else ROOT / "output" / "dashboard_surface" / symbol / "v767_reality_telegram_result.json"
    memory_path = ROOT / "output" / "dashboard_surface" / symbol / "v767_reality_telegram_sent_memory.json"

    state = load_json(rb_path)
    text = build_reality_telegram_text(state)
    fp = fingerprint(text, symbol)
    memory = read_sent_memory(memory_path)

    result: dict[str, Any] = {
        "engine": "V767_REALITY_BOARD_TELEGRAM_PRIMARY",
        "symbol": symbol,
        "mode": args.mode,
        "should_alert": True,
        "fingerprint": fp,
        "input": str(rb_path),
        "text_fr": text,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
    }

    if args.mode == "candidate-only":
        result.update({"sent": False, "reason": "candidate_only"})
    elif args.mode == "dry-run":
        result.update({"sent": False, "reason": "dry_run"})
    else:
        if not args.force and memory.get("fingerprint") == fp:
            result.update({"sent": False, "reason": "duplicate_fingerprint"})
        else:
            sent = send_telegram(text, ROOT, dry=False)
            result.update(sent)
            if sent.get("sent"):
                write_json(memory_path, {
                    "fingerprint": fp,
                    "sent_at_utc": datetime.now(timezone.utc).isoformat(),
                    "symbol": symbol,
                })

    write_json(out_path, result)

    print("=== V7.6.7 REALITY BOARD TELEGRAM PRIMARY ===")
    print(json.dumps({k: v for k, v in result.items() if k != "text_fr"}, ensure_ascii=False, indent=2))
    print()
    print(text)

    if args.mode == "live" and not result.get("sent") and result.get("error"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
