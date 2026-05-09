"""
PowerFlow V6 — Telegram Agentic Nodes V0.1

Mission:
    Send Telegram WATCH alerts from output/cockpit_agentic_state_v01.json.

Architecture:
    - Reads JSON only.
    - Does not read powerflow.db.
    - Does not write DB.
    - Does not calculate market logic.
    - Does not emit BUY/SELL.
    - Deduplicates alerts with a small local state file.

Environment variables:
    TELEGRAM_BOT_TOKEN
    TELEGRAM_CHAT_ID

Examples:
    python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json --dry-run

    python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json

    python run_telegram_agentic_nodes_once.py --json output/cockpit_agentic_state_v01.json --force
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence
import argparse
import hashlib
import json
import os
import urllib.parse
import urllib.request


TELEGRAM_AGENTIC_NODES_VERSION = "0.1.0"


@dataclass(frozen=True)
class TelegramNodeAlert:
    should_send: bool
    key: str
    severity: str
    title: str
    message: str
    reason: str


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"JSON not found: {path}")
    return json.loads(p.read_text(encoding="utf-8"))


def _load_state(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_state(path: str, state: Dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def _compact_flags(flags: Sequence[str], max_items: int = 5) -> str:
    items = [str(x) for x in flags if x]
    if not items:
        return "-"
    if len(items) <= max_items:
        return " | ".join(items)
    return " | ".join(items[:max_items]) + f" | +{len(items) - max_items}"


def _phase_lines(state: Dict[str, Any], max_lines: int = 5) -> List[str]:
    phases = (((state.get("flow_events") or {}).get("phases")) or {})
    out: List[str] = []
    for phase, ev in phases.items():
        start = ev.get("start", "?")
        end = ev.get("end", "?")
        up = "+".join(ev.get("up_block") or []) or "-"
        down = "+".join(ev.get("down_block") or []) or "-"
        price = ev.get("price_response") or "-"
        out.append(f"{start}→{end} {phase} | up={up} | down={down} | {price}")
    return out[:max_lines]


def build_node_alert(state: Dict[str, Any], min_severity: str = "watch") -> TelegramNodeAlert:
    symbol = state.get("symbol", "UNKNOWN")
    window = state.get("window") or {}
    summary = state.get("agent_summary") or {}
    scene = state.get("scene") or {}
    fractal = state.get("fractal") or {}
    extended = state.get("extended") or {}

    scene_name = summary.get("scene") or scene.get("scene_name") or "-"
    window_state = summary.get("window_state") or scene.get("window_state") or "-"
    dominant_phase = summary.get("dominant_phase") or scene.get("dominant_phase") or "-"
    next_watch = summary.get("next_watch") or fractal.get("next_watch") or scene.get("next_watch") or "-"

    fractal_state = summary.get("fractal_state") or fractal.get("fractal_state") or "-"
    temporal_state = summary.get("temporal_state") or fractal.get("temporal_state") or "-"
    higher_story = summary.get("higher_story") or fractal.get("higher_story_state") or "-"
    htf_relation = summary.get("htf_relation") or fractal.get("htf_relation") or "-"

    extended_summary = summary.get("extended_summary") or extended.get("extended_summary") or "-"
    extended_flags = summary.get("extended_flags") or extended.get("extended_flags") or []
    fractal_flags = summary.get("flags") or fractal.get("flags") or []

    active_node = scene_name in {
        "RAW_NODE_BIRTH",
        "GRAVITY_RESPRING_NODE",
        "USD_RESPRING_AGAINST_RISK_FOLD",
    } or dominant_phase in {"NODE_BIRTH", "ABSORPTION"}

    active_fractal = fractal_state in {
        "LTF_BIRTH_INSIDE_VISUAL_HTF_STORY",
        "LTF_BIRTH_WITH_HTF_RELAY",
        "LTF_BIRTH_INSIDE_HTF_STORY",
    }

    active_micro = any(flag in extended_flags for flag in {
        "MICRO_WINDOW_ACTIVE",
        "MICRO_WINDOW_ACTIVE_WEAK",
        "MICRO_WINDOW_ACTIVE_STRONG",
        "M1_NODE_BIRTH",
        "M5_NODE_BIRTH",
    })

    active_next = str(next_watch).startswith("WATCH_")

    severity = "none"
    if active_node and active_fractal and active_next:
        severity = "important"
    if active_node and active_fractal and active_micro and active_next:
        severity = "hot"
    if "MICRO_WINDOW_ACTIVE_STRONG" in extended_flags:
        severity = "hot"

    order = {"none": 0, "watch": 1, "important": 2, "hot": 3}
    required = order.get(min_severity, 1)
    should_send = order.get(severity, 0) >= required

    title = "⚡ POWERFLOW NODE WATCH"
    if severity == "hot":
        title = "🔥 POWERFLOW NODE HOT"
    elif severity == "important":
        title = "⚡ POWERFLOW NODE IMPORTANT"

    phase_txt = "\n".join(_phase_lines(state)) or "-"
    key_raw = "|".join([
        str(symbol),
        str(window.get("start")),
        str(window.get("end")),
        str(scene_name),
        str(window_state),
        str(dominant_phase),
        str(next_watch),
        str(fractal_state),
        str(extended_summary),
    ])
    key = hashlib.sha1(key_raw.encode("utf-8")).hexdigest()[:16]

    message = (
        f"{title}\n"
        f"{symbol} | {scene_name} | {window_state}\n"
        f"NEXT: {next_watch}\n\n"
        f"FRACTAL: {fractal_state}\n"
        f"TEMPORAL: {temporal_state}\n"
        f"HTF: {htf_relation}\n"
        f"STORY: {higher_story}\n\n"
        f"EXTENDED: {extended_summary}\n"
        f"EXT_FLAGS: {_compact_flags(extended_flags)}\n"
        f"FRACTAL_FLAGS: {_compact_flags(fractal_flags)}\n\n"
        f"FILM:\n{phase_txt}\n\n"
        f"KEY: {key}"
    )

    reason = (
        f"active_node={active_node} active_fractal={active_fractal} "
        f"active_micro={active_micro} active_next={active_next} severity={severity}"
    )

    return TelegramNodeAlert(
        should_send=should_send,
        key=key,
        severity=severity,
        title=title,
        message=message,
        reason=reason,
    )


def send_telegram_message(token: str, chat_id: str, message: str, timeout: float = 10.0) -> Dict[str, Any]:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
    return json.loads(body)


def run_once(
    json_path: str,
    state_path: str = "output/telegram_agentic_nodes_state.json",
    min_severity: str = "watch",
    dry_run: bool = False,
    force: bool = False,
    token: Optional[str] = None,
    chat_id: Optional[str] = None,
) -> int:
    state = _load_json(json_path)
    alert = build_node_alert(state, min_severity=min_severity)
    saved = _load_state(state_path)

    duplicate = saved.get("last_key") == alert.key

    print("=== POWERFLOW TELEGRAM AGENTIC NODES ===")
    print(f"VERSION: {TELEGRAM_AGENTIC_NODES_VERSION}")
    print(f"JSON: {json_path}")
    print(f"SEVERITY: {alert.severity}")
    print(f"SHOULD_SEND: {alert.should_send}")
    print(f"DUPLICATE: {duplicate}")
    print(f"REASON: {alert.reason}")
    print("")
    print(alert.message)

    if not alert.should_send and not force:
        print("\nVERDICT: NO_SEND_FILTERED")
        return 0

    if duplicate and not force:
        print("\nVERDICT: NO_SEND_DUPLICATE")
        return 0

    if dry_run:
        print("\nVERDICT: DRY_RUN_NOT_SENT")
        return 0

    token = token or os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("\nVERDICT: NO_SEND_MISSING_TELEGRAM_ENV")
        print("Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, or pass --token / --chat-id.")
        return 2

    response = send_telegram_message(token, chat_id, alert.message)

    _save_state(state_path, {
        "last_key": alert.key,
        "last_sent_at_utc": _now_utc(),
        "last_severity": alert.severity,
        "last_title": alert.title,
        "last_reason": alert.reason,
        "telegram_response_ok": bool(response.get("ok")),
    })

    print("\nVERDICT: SENT")
    print(f"TELEGRAM_OK: {response.get('ok')}")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Telegram Agentic Nodes V0.1")
    parser.add_argument("--json", default="output/cockpit_agentic_state_v01.json")
    parser.add_argument("--state", default="output/telegram_agentic_nodes_state.json")
    parser.add_argument("--min-severity", default="watch", choices=["watch", "important", "hot"])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--token", default=None)
    parser.add_argument("--chat-id", default=None)
    args = parser.parse_args(argv)

    return run_once(
        json_path=args.json,
        state_path=args.state,
        min_severity=args.min_severity,
        dry_run=args.dry_run,
        force=args.force,
        token=args.token,
        chat_id=args.chat_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
