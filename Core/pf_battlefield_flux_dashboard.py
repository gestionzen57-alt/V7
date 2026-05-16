#!/usr/bin/env python3
"""T009 Phase 1B - dashboard widget + Telegram dry-run helpers.

Standalone module. No dashboard_* import. No telegram_* import. No live send.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Optional

DEFAULT_OUTPUT_DIR = "output"
PREFIX = "T009_"

SOURCE_MATRIX = {
    "TIMER_1S_SAMPLE": ("LIVE", 1.0, False),
    "ONTICK_RAW": ("LIVE", 1.0, False),
    "M1_BAR_PROXY": ("RECONSTRUCTED", 0.35, False),
    "UNKNOWN": ("BLIND", 0.0, False),
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def clamp(value: Any, low: float = 0.0, high: float = 1.0, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def normalize_event_type(event_type: Any) -> str:
    raw = str(event_type or "UNKNOWN").upper().strip()
    return raw if raw.startswith(PREFIX) else f"{PREFIX}{raw}"


def trader_event_name(event_type: Any) -> str:
    internal = normalize_event_type(event_type)
    return internal[len(PREFIX):] if internal.startswith(PREFIX) else internal


def _nested(d: Mapping[str, Any], path: list[str], default: Any = None) -> Any:
    cur: Any = d
    for key in path:
        if not isinstance(cur, Mapping) or key not in cur:
            return default
        cur = cur[key]
    return cur


def get_score(event: Mapping[str, Any], name: str) -> float:
    if name in event:
        return clamp(event.get(name))
    scores = event.get("scores") or {}
    if isinstance(scores, Mapping):
        return clamp(scores.get(name))
    return 0.0


def visibility_from_source_mode(source_mode: str, explicit_visibility: Optional[str] = None):
    if explicit_visibility:
        v = str(explicit_visibility).upper()
        if v == "RECONSTRUCTED":
            return "RECONSTRUCTED", 0.35, False
        if v in {"LIVE", "FRESH"}:
            return "LIVE", 1.0, False
        if v in {"BLIND", "STALE"}:
            return v, 0.0 if v == "BLIND" else 0.5, False
    return SOURCE_MATRIX.get(str(source_mode or "UNKNOWN").upper(), SOURCE_MATRIX["UNKNOWN"])


def infer_source_mode(state: Optional[Mapping[str, Any]] = None, events: Optional[list[Mapping[str, Any]]] = None) -> str:
    state = state or {}
    context = state.get("context") if isinstance(state.get("context"), Mapping) else {}
    candidates = [state.get("source_mode"), context.get("source_mode")]
    if events:
        first = events[0] or {}
        candidates += [first.get("source_mode"), _nested(first, ["context", "source_mode"])]
    for c in candidates:
        if c:
            return str(c).upper()
    return "UNKNOWN"


def _zone(event: Mapping[str, Any]) -> dict:
    zone = event.get("zone") or {}
    if isinstance(zone, (list, tuple)) and len(zone) >= 2:
        low, high = float(zone[0]), float(zone[1])
        level = (low + high) / 2
        return {"low": low, "high": high, "level": level, "strength": max(get_score(event, "battle_score"), get_score(event, "absorption_score")), "dwell_time_sec": int(event.get("dwell_time_sec", 0) or 0)}
    if not isinstance(zone, Mapping):
        zone = {}
    low, high = zone.get("low"), zone.get("high")
    level = zone.get("level", zone.get("center", event.get("zone_level")))
    if level is None and low is not None and high is not None:
        try:
            level = (float(low) + float(high)) / 2
        except Exception:
            level = None
    strength = zone.get("strength", event.get("zone_strength"))
    if strength is None:
        strength = max(get_score(event, "battle_score"), get_score(event, "absorption_score"))
    return {"low": low, "high": high, "level": level, "strength": clamp(strength), "dwell_time_sec": int(zone.get("dwell_time_sec", event.get("dwell_time_sec", 0)) or 0)}


def _price(value: Any) -> str:
    try:
        return f"{float(value):.5f}"
    except Exception:
        return "zone"


def _label(confidence: float, visibility: str) -> str:
    if visibility == "RECONSTRUCTED":
        return "data reconstruite"
    if confidence >= 0.70:
        return "haute confiance"
    if confidence >= 0.50:
        return "confiance moyenne"
    return "confiance faible"


def _raw_confidence(event_type: str, scores: Mapping[str, float]) -> float:
    name = trader_event_name(event_type)
    if name == "BATTLE_LEVEL_BORN":
        return clamp(scores.get("battle_score"))
    if name == "ABSORPTION_CLUSTER":
        return clamp(scores.get("absorption_score"))
    return clamp(max(scores.values()) if scores else 0.0)


def _widget_event(event: Mapping[str, Any], source_mode: str, visibility: str) -> dict:
    internal = normalize_event_type(event.get("event_type"))
    scores = {"battle_score": get_score(event, "battle_score"), "absorption_score": get_score(event, "absorption_score")}
    cap_visibility, cap, _ = visibility_from_source_mode(source_mode, visibility)
    confidence = min(_raw_confidence(internal, scores), cap)
    return {"event_type": trader_event_name(internal), "internal_event_type": internal, "timestamp": event.get("timestamp") or event.get("ts_utc") or event.get("ts") or utc_now_iso(), "zone": _zone(event), "zone_level": _zone(event).get("level"), "battle_score": scores["battle_score"], "absorption_score": scores["absorption_score"], "confidence": confidence, "source_mode": source_mode, "data_visibility": cap_visibility}


def build_dashboard_evidence_widget(state: dict, events: list) -> dict:
    state = state or {}
    events = events or []
    context = state.get("context") if isinstance(state.get("context"), Mapping) else {}
    source_mode = infer_source_mode(state, events)
    visibility, cap, live_allowed = visibility_from_source_mode(source_mode, state.get("data_visibility") or context.get("data_visibility"))
    normalized = [_widget_event(e, source_mode, visibility) for e in events]
    top = normalized[0] if normalized else {}
    clusters = state.get("clusters") or state.get("buckets") or []
    tick_count = int(state.get("tick_count", state.get("ticks", 0)) or 0)
    lookback = int(state.get("lookback_min", context.get("lookback_min", 0)) or 0)
    return {
        "title": "Battlefield Flux",
        "module": "pf_battlefield_flux_dashboard",
        "version": "T009_PHASE1B",
        "timestamp": utc_now_iso(),
        "source_mode": source_mode,
        "data_visibility": visibility,
        "tick_count": tick_count,
        "lookback_min": lookback,
        "events": normalized,
        "clusters": clusters,
        "evidence_L1": {"event_type": top.get("event_type"), "zone_level": top.get("zone_level"), "timestamp": top.get("timestamp", utc_now_iso()), "battle_score": clamp(top.get("battle_score")), "absorption_score": clamp(top.get("absorption_score"))},
        "evidence_L2": {"zone_strength": clamp(_nested(top, ["zone", "strength"])), "dwell_time_sec": int(_nested(top, ["zone", "dwell_time_sec"], 0) or 0), "retest_count": int(state.get("retest_count", context.get("retest_count", 0)) or 0), "compression_ratio": clamp(state.get("compression_ratio", context.get("compression_ratio", 0.0))), "tick_count": tick_count, "cluster_count": len(clusters)},
        "evidence_L3": {"htf_alignment": context.get("htf_alignment", state.get("htf_alignment", "unknown")), "session_context": context.get("session_context", state.get("session_context", "unknown")), "coalition_strength": clamp(context.get("coalition_strength", state.get("coalition_strength", 0.0))), "source_mode": source_mode, "data_visibility": visibility, "confidence_cap": cap, "live_telegram_allowed": live_allowed},
    }


def format_trader_alert_packet(event: dict, context: dict) -> dict:
    event, context = event or {}, context or {}
    internal = normalize_event_type(event.get("event_type"))
    display = trader_event_name(internal)
    source_mode = str(event.get("source_mode") or context.get("source_mode") or "UNKNOWN").upper()
    visibility, cap, live_allowed = visibility_from_source_mode(source_mode, event.get("data_visibility") or context.get("data_visibility"))
    scores = {"battle_score": get_score(event, "battle_score"), "absorption_score": get_score(event, "absorption_score")}
    raw = _raw_confidence(internal, scores)
    confidence = min(raw, cap)
    zone = _zone(event)
    verb = "confirmé" if display == "ABSORPTION_CLUSTER" and confidence >= 0.70 else "détecté"
    if visibility == "RECONSTRUCTED":
        verb = "possible"
    message = f"{display} {_price(zone.get('level'))} {verb} (score {raw:.2f}, {_label(confidence, visibility)})"
    return {"event_type": internal, "symbol": event.get("symbol") or context.get("symbol") or "GBPUSD", "timestamp": event.get("timestamp") or event.get("ts_utc") or event.get("ts") or utc_now_iso(), "zone": zone, "scores": scores, "confidence": confidence, "raw_confidence": raw, "confidence_cap": cap, "data_visibility": visibility, "source_mode": source_mode, "live_telegram_allowed": live_allowed, "message_trader_fr": message, "technical_risks": list(event.get("technical_risks") or [])}


def _flag(flags: Any, full: str, short: str, default: Any) -> Any:
    if isinstance(flags, Mapping):
        return flags.get(full, flags.get(short, default))
    return getattr(flags, full, getattr(flags, short, default))


def _int(value: Any, default: int = 0) -> int:
    if isinstance(value, bool):
        return int(value)
    try:
        return int(value)
    except Exception:
        return default


def route_to_telegram_dry_run(packet: dict, flags: dict) -> dict:
    packet, flags = packet or {}, flags or {}
    enable = _int(_flag(flags, "POWERFLOW_T009_ENABLE_TELEGRAM", "ENABLE_TELEGRAM", 0), 0)
    dry = _int(_flag(flags, "POWERFLOW_T009_DRY_RUN", "DRY_RUN", 1), 1)
    output_dir = Path(str(_flag(flags, "POWERFLOW_T009_OUTPUT_DIR", "OUTPUT_DIR", DEFAULT_OUTPUT_DIR)))
    if enable != 0:
        return {"routed": False, "logged": False, "sent": False, "reason": "Phase 1B requires POWERFLOW_T009_ENABLE_TELEGRAM=0"}
    output_dir.mkdir(parents=True, exist_ok=True)
    visibility = str(packet.get("data_visibility", "UNKNOWN")).upper()
    if visibility == "RECONSTRUCTED":
        reason = "reconstructed data blocked from live Telegram; dry-run log only"
    elif dry == 1:
        reason = "dry-run mode active (Phase 1B)"
    else:
        reason = "Phase 1B forbids live Telegram send"
    entry = {"timestamp": utc_now_iso(), "event_type": packet.get("event_type"), "symbol": packet.get("symbol", "GBPUSD"), "message_trader_fr": packet.get("message_trader_fr", ""), "confidence": packet.get("confidence", 0.0), "data_visibility": visibility, "source_mode": packet.get("source_mode", "UNKNOWN"), "dry_run": True, "sent": False, "reason": reason}
    log_path = output_dir / "telegram_dry_run_log.json"
    existing = []
    if log_path.exists():
        try:
            loaded = json.loads(log_path.read_text(encoding="utf-8"))
            if isinstance(loaded, list):
                existing = loaded
        except Exception:
            existing = []
    existing.append(entry)
    log_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    return {"routed": True, "logged": True, "sent": False, "reason": reason, "log_path": str(log_path)}


def log_phase1b_event(event_type: str, data: dict, output_dir: str):
    path = Path(output_dir)
    path.mkdir(parents=True, exist_ok=True)
    log_file = path / "phase1b_events.log"
    line = f"[{utc_now_iso()}] {event_type}: {json.dumps(data or {}, ensure_ascii=False, sort_keys=True)}\n"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(line)
    return str(log_file)
