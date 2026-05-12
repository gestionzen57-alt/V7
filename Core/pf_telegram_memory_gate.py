#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

HOT_ACTIONS = {"WAKE_TRADER", "ALERT_READY", "HOT", "ACTIVE", "HOT_ATTENTION", "HOT_DETACHMENT"}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_json(path: Path, data: Dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2 if pretty else None, ensure_ascii=False), encoding="utf-8")


def deep_get(data: Dict[str, Any], *paths: str, default: Any = None) -> Any:
    for path in paths:
        obj: Any = data
        ok = True
        for part in path.split("."):
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                ok = False
                break
        if ok and obj not in (None, ""):
            return obj
    return default


def build_perception(brief: Dict[str, Any], live_decision: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    symbol = symbol.upper()

    action = deep_get(brief, "action", "status", "state", "brief.action", "brief.status", default=None)
    synthesis = deep_get(brief, "synthesis", "summary.synthesis", "reading_state", "brief.synthesis", default=None)
    reading = deep_get(brief, "reading", "summary.reading", "brief.reading", default=None)

    packet = deep_get(brief, "live.packet", "packet", "live.packet_type", default=deep_get(live_decision, "packet", "packet_type", "memory.packet", default="NONE"))
    level = deep_get(brief, "live.level", "level", default=deep_get(live_decision, "level", "memory.level", default="NONE"))
    bias = deep_get(brief, "live.bias", "bias", default=deep_get(live_decision, "bias", "memory.bias", default="NONE"))
    tf = deep_get(brief, "live.tf", "tf", "timeframe", default=deep_get(live_decision, "tf", "timeframe", "memory.tf", default="NONE"))
    score = deep_get(brief, "live.score", "score", default=deep_get(live_decision, "score", "memory.score", default=None))

    if not action:
        text_status = str(deep_get(brief, "text_status", default="") or "")
        action = "ALERT_READY" if "ALERT_READY" in text_status else "NO_ALERT"

    if not synthesis:
        synthesis = deep_get(live_decision, "synthesis", "message", default="UNKNOWN_SYNTHESIS")

    return {
        "symbol": symbol,
        "action": str(action),
        "synthesis": str(synthesis),
        "reading": str(reading or ""),
        "packet": str(packet),
        "level": str(level),
        "bias": str(bias),
        "tf": str(tf),
        "score": score,
    }


def perception_key(perception: Dict[str, Any]) -> str:
    raw = "|".join(str(perception.get(k, "")) for k in ("symbol", "action", "synthesis", "packet", "level", "bias", "tf"))
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]
    return f"{perception.get('symbol', 'UNK')}:{digest}"


def should_send(perception: Dict[str, Any]) -> bool:
    action = str(perception.get("action", "")).upper()
    level = str(perception.get("level", "")).upper()
    synthesis = str(perception.get("synthesis", "")).upper()
    if action in HOT_ACTIONS:
        return True
    if level in {"HOT", "ACTIVE"}:
        return True
    if "WAKE" in action or "ALERT" in action:
        return True
    if "TRAP_CONTEXT_ALIGNED" in synthesis or "CONFLICT_OR_REINTEGRATION" in synthesis:
        return True
    return False


def run_telegram_sender(sender: Path, timeout: int = 45) -> Dict[str, Any]:
    if not sender.exists():
        return {"returncode": 127, "stdout": "", "stderr": f"SENDER_MISSING:{sender}"}
    proc = subprocess.run([sys.executable, str(sender)], capture_output=True, text=True, timeout=timeout)
    return {"returncode": proc.returncode, "stdout": proc.stdout, "stderr": proc.stderr}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--brief", default=None)
    parser.add_argument("--live-decision", default=None)
    parser.add_argument("--memory", default="output/dashboard_surface/telegram_sent_memory.json")
    parser.add_argument("--sender", default="pf_powerflow_telegram_gate_once.py")
    parser.add_argument("--cooldown-min", type=float, default=10.0)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbol = args.symbol.upper()
    brief_path = Path(args.brief) if args.brief else Path("output/dashboard_surface") / symbol / "powerflow_live_brief.json"
    live_path = Path(args.live_decision) if args.live_decision else Path("output/dashboard_surface") / symbol / "live_decision.json"
    memory_path = Path(args.memory)

    brief = load_json(brief_path)
    live_decision = load_json(live_path)
    memory = load_json(memory_path)
    if "sent" not in memory or not isinstance(memory.get("sent"), dict):
        memory = {"method": "TELEGRAM_SENT_MEMORY_V733", "sent": {}}

    perception = build_perception(brief, live_decision, symbol)
    key = perception_key(perception)
    now = now_utc()
    entry = memory["sent"].get(key, {})
    last_sent = parse_dt(entry.get("last_sent_utc"))
    elapsed_min = (now - last_sent).total_seconds() / 60.0 if last_sent else None

    allowed_by_action = should_send(perception)
    allowed_by_cooldown = elapsed_min is None or elapsed_min >= args.cooldown_min
    should_execute = allowed_by_action and allowed_by_cooldown

    send_result = None
    if should_execute and args.execute:
        send_result = run_telegram_sender(Path(args.sender))
        if send_result.get("returncode") == 0:
            memory["sent"][key] = {
                "last_sent_utc": iso(now),
                "count": int(entry.get("count", 0)) + 1,
                "perception": perception,
            }
            memory["last_update_utc"] = iso(now)
            write_json(memory_path, memory, pretty=True)
    else:
        memory["last_update_utc"] = iso(now)
        write_json(memory_path, memory, pretty=True)

    report = {
        "timestamp_utc": iso(now),
        "method": "TELEGRAM_MEMORY_GATE_V733",
        "symbol": symbol,
        "memory_path": str(memory_path),
        "brief_path": str(brief_path),
        "live_decision_path": str(live_path),
        "key": key,
        "perception": perception,
        "allowed_by_action": allowed_by_action,
        "allowed_by_cooldown": allowed_by_cooldown,
        "cooldown_minutes": args.cooldown_min,
        "elapsed_minutes": round(elapsed_min, 3) if elapsed_min is not None else None,
        "decision": "SEND" if should_execute else "SUPPRESS",
        "execute": bool(args.execute),
        "send_result": send_result,
        "technical_risks": [],
        "note": "Telegram memory gate prevents duplicate perceptions while preserving fast alerts.",
    }
    if not allowed_by_action:
        report["technical_risks"].append("PERCEPTION_NOT_ALERT_LEVEL")
    if not allowed_by_cooldown:
        report["technical_risks"].append("TELEGRAM_COOLDOWN_ACTIVE")

    out_path = Path("output/dashboard_surface") / symbol / "telegram_memory_gate.json"
    write_json(out_path, report, pretty=True)

    if args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"TELEGRAM_MEMORY_GATE_{report['decision']} | symbol={symbol} | action={perception.get('action')} | synthesis={perception.get('synthesis')} | cooldown_ok={allowed_by_cooldown} | execute={args.execute} | out={out_path}")
    return 0 if (send_result is None or send_result.get("returncode", 0) == 0) else int(send_result.get("returncode", 1))


if __name__ == "__main__":
    raise SystemExit(main())
