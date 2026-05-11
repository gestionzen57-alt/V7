"""
PowerFlow V7.2 - Session Overlay V2

Role:
  Qualify behavioral alerts with UTC session context.
  This module never filters alerts. It only returns context.

Doctrine:
  session_context = qualifier only, never a filter.
"""

from __future__ import annotations

from datetime import datetime, timezone, time
from typing import Any, Dict, Optional, Union

METHOD = "SESSION_OVERLAY_V2"

VALID_SESSIONS = {"ASIAN", "LONDON", "NY", "OVERLAP", "DEAD_ZONE"}
VALID_PHASES = {"PRE_OPEN", "IGNITION", "MID_SESSION", "CLOSING", "MAX_VELOCITY_BATTLEFIELD", "DEAD_ZONE"}
VALID_BIASES = {"EXPANSION_EXPECTED", "COMPRESSION_EXPECTED", "ROTATION", "MAX_VELOCITY_BATTLEFIELD", "DEAD_ZONE"}


def _as_utc_datetime(timestamp_utc: Optional[Union[str, datetime]] = None) -> datetime:
    if timestamp_utc is None:
        return datetime.now(timezone.utc)
    if isinstance(timestamp_utc, datetime):
        dt = timestamp_utc
    elif isinstance(timestamp_utc, str):
        raw = timestamp_utc.strip()
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        dt = datetime.fromisoformat(raw)
    else:
        raise TypeError("timestamp_utc must be None, str, or datetime")
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _minutes_of_day(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def _in_range(minute: int, start: int, end: int) -> bool:
    """Half-open interval [start, end), supports midnight wrap."""
    if start <= end:
        return start <= minute < end
    return minute >= start or minute < end


def _minutes_since_open(minute: int, open_minute: int) -> int:
    delta = minute - open_minute
    if delta < 0:
        delta += 1440
    return max(0, int(delta))


def _t(h: int, m: int = 0) -> int:
    return h * 60 + m


def _phase_for_asian(minute: int) -> tuple[str, int, str]:
    if _in_range(minute, _t(21, 30), _t(22, 0)):
        return "PRE_OPEN", _minutes_since_open(minute, _t(22, 0)), "ROTATION"
    if _in_range(minute, _t(22, 0), _t(22, 30)):
        return "IGNITION", _minutes_since_open(minute, _t(22, 0)), "ROTATION"
    if _in_range(minute, _t(22, 30), _t(6, 0)):
        return "MID_SESSION", _minutes_since_open(minute, _t(22, 0)), "COMPRESSION_EXPECTED"
    if _in_range(minute, _t(6, 0), _t(8, 0)):
        return "CLOSING", _minutes_since_open(minute, _t(22, 0)), "COMPRESSION_EXPECTED"
    return "MID_SESSION", _minutes_since_open(minute, _t(22, 0)), "COMPRESSION_EXPECTED"


def _phase_for_london(minute: int) -> tuple[str, int, str]:
    if _in_range(minute, _t(6, 30), _t(7, 0)):
        return "PRE_OPEN", _minutes_since_open(minute, _t(7, 0)), "ROTATION"
    if _in_range(minute, _t(7, 0), _t(7, 45)):
        return "IGNITION", _minutes_since_open(minute, _t(7, 0)), "EXPANSION_EXPECTED"
    if _in_range(minute, _t(7, 45), _t(12, 0)):
        return "MID_SESSION", _minutes_since_open(minute, _t(7, 0)), "COMPRESSION_EXPECTED"
    if _in_range(minute, _t(15, 30), _t(16, 0)):
        return "CLOSING", _minutes_since_open(minute, _t(7, 0)), "ROTATION"
    return "MID_SESSION", _minutes_since_open(minute, _t(7, 0)), "ROTATION"


def _phase_for_ny(minute: int) -> tuple[str, int, str]:
    if _in_range(minute, _t(11, 30), _t(12, 0)):
        return "PRE_OPEN", _minutes_since_open(minute, _t(12, 0)), "ROTATION"
    if _in_range(minute, _t(12, 0), _t(12, 45)):
        return "IGNITION", _minutes_since_open(minute, _t(12, 0)), "EXPANSION_EXPECTED"
    if _in_range(minute, _t(12, 45), _t(20, 0)):
        return "MID_SESSION", _minutes_since_open(minute, _t(12, 0)), "ROTATION"
    if _in_range(minute, _t(20, 0), _t(21, 0)):
        return "CLOSING", _minutes_since_open(minute, _t(12, 0)), "ROTATION"
    return "MID_SESSION", _minutes_since_open(minute, _t(12, 0)), "ROTATION"


def get_session_context(timestamp_utc: Optional[Union[str, datetime]] = None) -> Dict[str, Any]:
    """
    Calcule le contexte de session pour un timestamp UTC donné.
    Si timestamp_utc=None, utilise datetime.now(timezone.utc).

    Returns:
      {
        "session": "ASIAN | LONDON | NY | OVERLAP | DEAD_ZONE",
        "session_secondary": "NY | null",
        "session_phase": "IGNITION | MID_SESSION | ...",
        "minutes_since_open": int,
        "session_bias": "EXPANSION_EXPECTED | ...",
        "utc_time": "HH:MM:SS",
        "method": "SESSION_OVERLAY_V2",
        "timestamp": ISO8601 UTC
      }
    """
    dt = _as_utc_datetime(timestamp_utc)
    minute = _minutes_of_day(dt)

    # Explicit dead-zone first: NY closing -> Asian pre-open.
    if _in_range(minute, _t(20, 0), _t(22, 0)):
        session = "DEAD_ZONE"
        session_secondary = None
        phase = "DEAD_ZONE"
        minutes = _minutes_since_open(minute, _t(20, 0))
        bias = "DEAD_ZONE"
    # London/NY overlap is a distinct battlefield state.
    elif _in_range(minute, _t(12, 0), _t(16, 0)):
        session = "OVERLAP"
        session_secondary = "NY"
        phase = "MAX_VELOCITY_BATTLEFIELD"
        minutes = _minutes_since_open(minute, _t(12, 0))
        bias = "EXPANSION_EXPECTED"
    elif _in_range(minute, _t(6, 30), _t(12, 0)) or _in_range(minute, _t(15, 30), _t(16, 0)):
        session = "LONDON"
        session_secondary = None
        phase, minutes, bias = _phase_for_london(minute)
    elif _in_range(minute, _t(11, 30), _t(21, 0)):
        session = "NY"
        session_secondary = None
        phase, minutes, bias = _phase_for_ny(minute)
    else:
        session = "ASIAN"
        session_secondary = None
        phase, minutes, bias = _phase_for_asian(minute)

    context = {
        "session": session,
        "session_secondary": session_secondary,
        "session_phase": phase,
        "minutes_since_open": max(0, int(minutes)),
        "session_bias": bias,
        "utc_time": dt.strftime("%H:%M:%S"),
        "method": METHOD,
        "timestamp": dt.isoformat().replace("+00:00", "Z"),
    }
    return context


if __name__ == "__main__":
    import json
    print(json.dumps(get_session_context(), indent=2, ensure_ascii=False))
