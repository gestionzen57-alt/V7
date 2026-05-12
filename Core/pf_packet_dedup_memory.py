#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

MEMORY_PATH = Path("output/dashboard_surface/telegram_gate_memory.json")

LEVEL_RANK = {
    "NONE": 0,
    "INFO": 1,
    "WATCH": 2,
    "STANDARD": 2,
    "ACTIVE": 3,
    "CONFIRM": 3,
    "HOT": 4,
    "CRITICAL": 5,
}

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso_now() -> str:
    return now_utc().isoformat()

def parse_dt(v: Any) -> datetime | None:
    if not v:
        return None
    try:
        s = str(v).replace("Z", "+00:00")
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
    except Exception:
        return None

def age_minutes(v: Any) -> float | None:
    d = parse_dt(v)
    if not d:
        return None
    return round((now_utc() - d).total_seconds() / 60.0, 2)

def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}

def write_json_atomic(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)

def clean_text(v: Any) -> str:
    return str(v or "").strip()

def as_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default

def as_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default

def level_rank(level: Any) -> int:
    return LEVEL_RANK.get(clean_text(level).upper(), 0)

def normalize_types(v: Any) -> list[str]:
    if isinstance(v, list):
        return [clean_text(x) for x in v if clean_text(x)]
    if isinstance(v, str) and v.strip():
        return [x.strip() for x in v.split(",") if x.strip()]
    return []

def extract_live_packet(symbol: str = "GBPUSD") -> Dict[str, Any]:
    base = Path("output/dashboard_surface") / symbol

    brief = read_json(base / "powerflow_live_brief.json")
    decision = read_json(base / "live_decision.json")
    flow_packet = read_json(base / "flow_packet.json")
    cockpit = read_json(base / "cockpit_v73_status.json")

    live_from_brief = brief.get("live") if isinstance(brief.get("live"), dict) else {}
    raw_memory = decision.get("raw_memory_packet") if isinstance(decision.get("raw_memory_packet"), dict) else {}
    top_live = flow_packet.get("top_live_packet") if isinstance(flow_packet.get("top_live_packet"), dict) else {}
    top_packet = flow_packet.get("top_packet") if isinstance(flow_packet.get("top_packet"), dict) else {}

    src = top_live or raw_memory or live_from_brief or top_packet or {}

    packet_type = (
        src.get("type")
        or src.get("packet_type")
        or live_from_brief.get("packet")
        or raw_memory.get("type")
        or decision.get("message")
    )

    level = (
        src.get("level")
        or src.get("packet_level")
        or live_from_brief.get("level")
        or decision.get("level")
        or "NONE"
    )

    bias = (
        src.get("bias")
        or src.get("pair_bias")
        or live_from_brief.get("bias")
        or decision.get("bias")
        or "NONE"
    )

    tf = (
        src.get("tf")
        or src.get("timeframe")
        or live_from_brief.get("tf")
        or raw_memory.get("tf")
    )

    score = (
        src.get("score")
        or live_from_brief.get("score")
        or raw_memory.get("score")
    )

    first_signal_at = src.get("first_signal_at") or raw_memory.get("first_signal_at")
    last_signal_at = src.get("last_signal_at") or raw_memory.get("last_signal_at")

    types = normalize_types(src.get("types") or live_from_brief.get("types"))

    action = brief.get("action") or brief.get("state") or decision.get("state") or "UNKNOWN"
    synthesis = brief.get("synthesis") or brief.get("message") or decision.get("message") or "UNKNOWN"

    packet = {
        "symbol": symbol,
        "action": clean_text(action),
        "synthesis": clean_text(synthesis),
        "packet_type": clean_text(packet_type),
        "level": clean_text(level).upper(),
        "bias": clean_text(bias),
        "tf": as_int(tf, 0),
        "score": as_float(score, 0.0),
        "types": types,
        "first_signal_at": clean_text(first_signal_at),
        "last_signal_at": clean_text(last_signal_at),
        "age_min": age_minutes(last_signal_at),
        "source_files": {
            "brief": str(base / "powerflow_live_brief.json"),
            "decision": str(base / "live_decision.json"),
            "flow_packet": str(base / "flow_packet.json"),
            "cockpit": str(base / "cockpit_v73_status.json"),
        },
    }
    return packet

def packet_family(packet: Dict[str, Any]) -> str:
    parts = [
        packet.get("symbol"),
        packet.get("packet_type"),
        packet.get("bias"),
        packet.get("tf"),
        ",".join(packet.get("types") or []),
        packet.get("first_signal_at"),
        packet.get("last_signal_at"),
    ]
    return "|".join(clean_text(x) for x in parts)

def packet_fingerprint(packet: Dict[str, Any]) -> str:
    raw = json.dumps({
        "symbol": packet.get("symbol"),
        "packet_type": packet.get("packet_type"),
        "level": packet.get("level"),
        "bias": packet.get("bias"),
        "tf": packet.get("tf"),
        "score": packet.get("score"),
        "types": packet.get("types"),
        "first_signal_at": packet.get("first_signal_at"),
        "last_signal_at": packet.get("last_signal_at"),
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]

def load_memory() -> Dict[str, Any]:
    mem = read_json(MEMORY_PATH)
    if not mem:
        mem = {"method": "TELEGRAM_PACKET_MEMORY_V74", "families": {}, "fingerprints": {}, "events": []}
    mem.setdefault("families", {})
    mem.setdefault("fingerprints", {})
    mem.setdefault("events", [])
    return mem

def should_send(packet: Dict[str, Any], cooldown_min: int = 30, min_level: str = "ACTIVE") -> Tuple[bool, str, Dict[str, Any]]:
    mem = load_memory()

    fp = packet_fingerprint(packet)
    fam = packet_family(packet)

    packet["fingerprint"] = fp
    packet["family"] = fam

    if not packet.get("packet_type"):
        return False, "NO_PACKET_TYPE", {"fingerprint": fp, "family": fam}

    if level_rank(packet.get("level")) < level_rank(min_level):
        return False, f"LEVEL_BELOW_{min_level}", {"fingerprint": fp, "family": fam}

    fam_prev = mem["families"].get(fam)
    if not fam_prev:
        return True, "NEW_PACKET_FAMILY", {"fingerprint": fp, "family": fam}

    prev_sent_at = parse_dt(fam_prev.get("sent_at"))
    elapsed = None
    if prev_sent_at:
        elapsed = round((now_utc() - prev_sent_at).total_seconds() / 60.0, 2)

    prev_level = fam_prev.get("level", "NONE")
    prev_score = as_float(fam_prev.get("score"), 0.0)

    if level_rank(packet.get("level")) > level_rank(prev_level):
        return True, "LEVEL_ESCALATION", {"fingerprint": fp, "family": fam, "prev_level": prev_level}

    if packet.get("score", 0.0) >= prev_score + 2.0:
        return True, "SCORE_ACCELERATION", {"fingerprint": fp, "family": fam, "prev_score": prev_score}

    if elapsed is not None and elapsed >= cooldown_min:
        return True, "COOLDOWN_EXPIRED", {"fingerprint": fp, "family": fam, "elapsed_min": elapsed}

    return False, "DUPLICATE_PACKET_SUPPRESSED", {
        "fingerprint": fp,
        "family": fam,
        "elapsed_min": elapsed,
        "prev_level": prev_level,
        "prev_score": prev_score,
    }

def mark_sent(packet: Dict[str, Any], reason: str) -> None:
    mem = load_memory()
    fp = packet.get("fingerprint") or packet_fingerprint(packet)
    fam = packet.get("family") or packet_family(packet)

    record = {
        "sent_at": iso_now(),
        "reason": reason,
        "symbol": packet.get("symbol"),
        "packet_type": packet.get("packet_type"),
        "level": packet.get("level"),
        "bias": packet.get("bias"),
        "tf": packet.get("tf"),
        "score": packet.get("score"),
        "types": packet.get("types"),
        "first_signal_at": packet.get("first_signal_at"),
        "last_signal_at": packet.get("last_signal_at"),
        "fingerprint": fp,
        "family": fam,
    }

    mem["fingerprints"][fp] = record
    mem["families"][fam] = record
    mem["events"].append(record)
    mem["events"] = mem["events"][-200:]

    write_json_atomic(MEMORY_PATH, mem)

def decision_preview(symbol: str = "GBPUSD", cooldown_min: int = 30, min_level: str = "ACTIVE") -> Dict[str, Any]:
    packet = extract_live_packet(symbol)
    send, reason, meta = should_send(packet, cooldown_min=cooldown_min, min_level=min_level)
    return {
        "created_at": iso_now(),
        "method": "TELEGRAM_DEDUP_DECISION_V74",
        "symbol": symbol,
        "send": send,
        "reason": reason,
        "packet": packet,
        "meta": meta,
        "memory_path": str(MEMORY_PATH),
    }
