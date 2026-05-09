#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pf_session_overlay.py

PowerFlow V7.1 — Session Overlay.

Role:
    Convert a UTC timestamp into a behavioral market session context.

Doctrine:
    - Context enrichment only.
    - No trading decision.
    - No alert censorship.
    - No DB write.
    - No cockpit dependency.
    - Python stdlib only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class SessionWindow:
    name: str
    start_utc: time
    end_utc: time
    bias: str


@dataclass(frozen=True)
class SessionContext:
    session: str
    overlap: Optional[str]
    is_active: bool
    active_sessions: List[str]
    session_phase: str
    session_bias: str
    minutes_since_open: Optional[int]
    timestamp_utc: str


SESSION_WINDOWS: Tuple[SessionWindow, ...] = (
    SessionWindow(
        name="Asian",
        start_utc=time(23, 0),
        end_utc=time(8, 0),
        bias="COMPRESSION_OR_ROTATION_EXPECTED",
    ),
    SessionWindow(
        name="London",
        start_utc=time(7, 0),
        end_utc=time(16, 0),
        bias="IGNITION_OR_EXPANSION_EXPECTED",
    ),
    SessionWindow(
        name="NY",
        start_utc=time(12, 0),
        end_utc=time(21, 0),
        bias="CONFIRMATION_OR_COUNTER_MOVE_EXPECTED",
    ),
)


def parse_utc_timestamp(value: str | datetime) -> datetime:
    """
    Parse a timestamp into an aware UTC datetime.

    Accepted:
        - aware datetime
        - naive datetime, interpreted as UTC
        - ISO string with Z suffix
        - ISO string with explicit offset
        - ISO string without timezone, interpreted as UTC
    """
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"Invalid timestamp format: {value!r}") from exc
    else:
        raise TypeError(f"timestamp must be str or datetime, got {type(value).__name__}")

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def _time_in_window(current: time, start: time, end: time) -> bool:
    """
    Return True if current is inside [start, end).

    Handles midnight-crossing windows, for example 23:00 -> 08:00.
    """
    if start <= end:
        return start <= current < end

    return current >= start or current < end


def _session_open_datetime(dt: datetime, window: SessionWindow) -> datetime:
    """
    Return the latest opening datetime for a session window relative to dt.

    Uses timedelta instead of day replacement, so month/year boundaries are safe.
    """
    candidate = dt.replace(
        hour=window.start_utc.hour,
        minute=window.start_utc.minute,
        second=0,
        microsecond=0,
    )

    crosses_midnight = window.start_utc > window.end_utc

    if crosses_midnight:
        if dt.time() < window.end_utc:
            candidate -= timedelta(days=1)
    else:
        if dt.time() < window.start_utc:
            candidate -= timedelta(days=1)

    return candidate


def _minutes_since_open(dt: datetime, window: SessionWindow) -> int:
    opened_at = _session_open_datetime(dt, window)
    return max(0, int((dt - opened_at).total_seconds() // 60))


def _phase_from_minutes(minutes_since_open: Optional[int], is_active: bool) -> str:
    if not is_active or minutes_since_open is None:
        return "DEAD_ZONE"

    if minutes_since_open < 30:
        return "IGNITION"

    if minutes_since_open < 180:
        return "MID_SESSION"

    return "CLOSING_OR_LATE_SESSION"


def _primary_session(active_sessions: Sequence[str]) -> str:
    """
    Determine the dominant readable session label.

    Priority:
        - London when London is active, including overlaps
        - NY
        - Asian
        - Dead
    """
    if not active_sessions:
        return "Dead"

    if "London" in active_sessions:
        return "London"

    if "NY" in active_sessions:
        return "NY"

    if "Asian" in active_sessions:
        return "Asian"

    return active_sessions[0]


def _overlap_label(active_sessions: Sequence[str]) -> Optional[str]:
    active = set(active_sessions)

    if {"London", "NY"}.issubset(active):
        return "NY"

    if {"Asian", "London"}.issubset(active):
        return "London"

    if len(active_sessions) >= 2:
        return "+".join(active_sessions[1:])

    return None


def _combined_bias(active_sessions: Sequence[str]) -> str:
    active = set(active_sessions)

    if {"London", "NY"}.issubset(active):
        return "MAX_VELOCITY_BATTLEFIELD"

    if {"Asian", "London"}.issubset(active):
        return "ASIAN_TO_LONDON_HANDOVER"

    if "London" in active:
        return "IGNITION_OR_EXPANSION_EXPECTED"

    if "NY" in active:
        return "CONFIRMATION_OR_COUNTER_MOVE_EXPECTED"

    if "Asian" in active:
        return "COMPRESSION_OR_ROTATION_EXPECTED"

    return "LOW_SESSION_ACTIVITY"


def get_session_context(timestamp_utc: str | datetime) -> Dict[str, Any]:
    """
    Return PowerFlow session context for one UTC timestamp.

    Minimal expected shape:
        {
            "session": "London",
            "overlap": "NY",
            "is_active": true
        }

    Extended keys are added for traceability and qualification.
    """
    dt = parse_utc_timestamp(timestamp_utc)
    current_time = dt.time()

    active_windows = [
        window
        for window in SESSION_WINDOWS
        if _time_in_window(current_time, window.start_utc, window.end_utc)
    ]

    active_sessions = [window.name for window in active_windows]
    primary = _primary_session(active_sessions)
    is_active = bool(active_sessions)

    primary_window = next(
        (window for window in active_windows if window.name == primary),
        None,
    )

    minutes_since_open = (
        _minutes_since_open(dt, primary_window)
        if primary_window is not None
        else None
    )

    context = SessionContext(
        session=primary,
        overlap=_overlap_label(active_sessions),
        is_active=is_active,
        active_sessions=active_sessions,
        session_phase=_phase_from_minutes(minutes_since_open, is_active),
        session_bias=_combined_bias(active_sessions),
        minutes_since_open=minutes_since_open,
        timestamp_utc=dt.isoformat(),
    )

    return asdict(context)


def enrich_payload_with_session_context(
    payload: Dict[str, Any],
    timestamp_field_candidates: Sequence[str] = ("timestamp", "created_at", "time", "generated_at_utc"),
) -> Dict[str, Any]:
    """
    Return a shallow-enriched copy of an alert-like dictionary.

    Missing or invalid timestamps are exposed as technical risks.
    The alert is never removed or censored.
    """
    enriched = dict(payload)

    timestamp_value: Optional[Any] = None
    timestamp_field: Optional[str] = None

    for field in timestamp_field_candidates:
        value = enriched.get(field)
        if value:
            timestamp_value = value
            timestamp_field = field
            break

    if timestamp_value is None:
        enriched["session_context"] = {
            "session": "Unknown",
            "overlap": None,
            "is_active": False,
            "active_sessions": [],
            "session_phase": "UNKNOWN",
            "session_bias": "UNKNOWN",
            "minutes_since_open": None,
            "timestamp_utc": None,
            "technical_risks": ["MISSING_TIMESTAMP"],
        }
        return enriched

    try:
        session_context = get_session_context(timestamp_value)
        session_context["timestamp_field"] = timestamp_field
    except (TypeError, ValueError) as exc:
        session_context = {
            "session": "Unknown",
            "overlap": None,
            "is_active": False,
            "active_sessions": [],
            "session_phase": "UNKNOWN",
            "session_bias": "UNKNOWN",
            "minutes_since_open": None,
            "timestamp_utc": None,
            "timestamp_field": timestamp_field,
            "technical_risks": ["INVALID_TIMESTAMP"],
            "error": str(exc),
        }

    enriched["session_context"] = session_context
    return enriched


if __name__ == "__main__":
    import json
    import sys

    ts = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).isoformat()
    print(json.dumps(get_session_context(ts), indent=2, ensure_ascii=False))
