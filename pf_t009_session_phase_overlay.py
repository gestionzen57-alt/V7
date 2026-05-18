"""T0132 - B9 Session Phase Overlay V0.

Read-only helper that annotates B9/T009 moments with session context.
It does not decide, trade, write databases, call dashboard, or transmit alerts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0132_B9_SESSION_PHASE_OVERLAY_V0"

FORBIDDEN_TERMS = ("BUY", "SELL", "probability of success", "success rate", "win rate")

@dataclass(frozen=True)
class SessionContext:
    session: str
    session_phase: str
    session_bias: str
    minutes_since_open: Optional[int]
    session_context_source: str
    session_reading_fr: str
    session_limits: str


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    # Prefer full ISO timestamps.
    try:
        normalized = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except ValueError:
        pass
    # Accept HH:MM or HH:MM:SS as UTC clock-only for replay reports.
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            clock = datetime.strptime(text, fmt)
            return datetime(2000, 1, 1, clock.hour, clock.minute, clock.second)
        except ValueError:
            continue
    # Accept date + time with a space.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _minutes_since(hour: int, minute: int, start_hour: int) -> int:
    total = hour * 60 + minute
    start = start_hour * 60
    if total < start:
        total += 24 * 60
    return total - start


def _phase(minutes_since_open: Optional[int], session: str) -> str:
    if session == "DEAD_ZONE":
        return "DEAD_ZONE"
    if minutes_since_open is None:
        return "UNKNOWN_PHASE"
    if minutes_since_open < 30:
        return "IGNITION"
    if minutes_since_open >= 8 * 60:
        return "CLOSING"
    if minutes_since_open >= 7 * 60:
        return "CLOSING"
    return "MID_SESSION"


def classify_session(dt: Optional[datetime]) -> SessionContext:
    if dt is None:
        return SessionContext(
            session="SESSION_UNKNOWN",
            session_phase="UNKNOWN_PHASE",
            session_bias="SESSION_UNKNOWN",
            minutes_since_open=None,
            session_context_source="TIMESTAMP_NOT_PARSEABLE",
            session_reading_fr="Session non déterminée : timestamp absent ou non lisible.",
            session_limits="SESSION_TIMESTAMP_NOT_PARSEABLE",
        )
    h, m = dt.hour, dt.minute
    minutes_of_day = h * 60 + m
    # Priority order: overlap is a battlefield distinct from London/NY.
    if 12 * 60 <= minutes_of_day < 16 * 60:
        session = "OVERLAP"
        start = 12
        bias = "MAX_VELOCITY_BATTLEFIELD"
        fr = "Chevauchement London/NY : zone de bataille à vélocité maximale."
    elif 7 * 60 <= minutes_of_day < 12 * 60:
        session = "LONDON"
        start = 7
        bias = "EXPANSION_EXPECTED"
        fr = "Session London : phase d'ignition ou d'expansion potentielle selon le timing."
    elif 16 * 60 <= minutes_of_day < 20 * 60:
        session = "NY"
        start = 12
        bias = "CONFIRMATION_OR_COUNTER_MOVE"
        fr = "Session NY : confirmation, contre-mouvement ou redistribution de la scène."
    elif 20 * 60 <= minutes_of_day < 22 * 60:
        session = "DEAD_ZONE"
        start = 20
        bias = "LOW_LIQUIDITY_ROTATION"
        fr = "Dead zone : lecture souvent plus lente, rotative ou fragile."
    else:
        session = "ASIAN"
        start = 22
        bias = "COMPRESSION_OR_RANGE_EXPECTED"
        fr = "Session Asian : compression progressive, range ou préparation de terrain."
    mins = _minutes_since(h, m, start)
    phase = _phase(mins, session)
    return SessionContext(
        session=session,
        session_phase=phase,
        session_bias=bias,
        minutes_since_open=mins,
        session_context_source="UTC_TIMESTAMP",
        session_reading_fr=fr,
        session_limits="SESSION_CONTEXT_ONLY_NOT_DECISION",
    )


def _moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments"):
        value = summary.get(key)
        if isinstance(value, list):
            return value
    return []


def enrich_moment(moment: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(moment)
    timestamp_value = (
        moment.get("time_start_real")
        or moment.get("orig_start")
        or moment.get("time_start")
        or moment.get("start")
        or moment.get("timestamp")
    )
    dt = _parse_datetime(timestamp_value)
    ctx = classify_session(dt)
    enriched.update({
        "b9_session_overlay_version": VERSION,
        "b9_session": ctx.session,
        "b9_session_phase": ctx.session_phase,
        "b9_minutes_since_session_open": ctx.minutes_since_open if ctx.minutes_since_open is not None else "",
        "b9_session_bias": ctx.session_bias,
        "b9_session_context_source": ctx.session_context_source,
        "b9_session_reading_fr": ctx.session_reading_fr,
        "b9_session_limits": ctx.session_limits,
    })
    return enriched


def enrich_sequence_summary_session_overlay(summary: Dict[str, Any]) -> Dict[str, Any]:
    enriched = dict(summary)
    moments = _moments(summary)
    enriched_moments = [enrich_moment(m) for m in moments]
    if "moments" in enriched or not any(k in enriched for k in ("sequence_moments", "b9_moments")):
        enriched["moments"] = enriched_moments
    elif "sequence_moments" in enriched:
        enriched["sequence_moments"] = enriched_moments
    else:
        enriched["b9_moments"] = enriched_moments
    enriched["b9_session_overlay_version"] = VERSION
    return enriched


def required_fields() -> List[str]:
    return [
        "b9_session_overlay_version",
        "b9_session",
        "b9_session_phase",
        "b9_minutes_since_session_open",
        "b9_session_bias",
        "b9_session_context_source",
        "b9_session_reading_fr",
        "b9_session_limits",
    ]


def forbidden_hits(summary: Dict[str, Any]) -> List[str]:
    text = json_dumps(summary).upper()
    hits = []
    for term in FORBIDDEN_TERMS:
        if term.upper() in text:
            hits.append(term)
    return hits


def json_dumps(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)
