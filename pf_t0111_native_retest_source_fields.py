"""T0111 B9 native retest source fields scaffold.

This module is intentionally pure and DB-free.

It provides a canonical enrichment helper that can be called by
pf_t009_sequence_summarizer.py when it creates each B9 moment.

Doctrine:
- interpretation only
- no BUY/SELL language
- no DB write
- no external Temporalité dependency
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, MutableMapping, Optional


T0111_VERSION = "T0111_NATIVE_RETEST_SOURCE_FIELDS_V0"

OUTCOME_ACCEPTED = "RETEST_OUTCOME_ACCEPTED"
OUTCOME_REJECTED = "RETEST_OUTCOME_REJECTED_OR_FAILED"
OUTCOME_PENDING = "RETEST_OUTCOME_PENDING"
OUTCOME_FRICTION = "RETEST_OUTCOME_FRICTION"
OUTCOME_ROTATIONAL = "RETEST_OUTCOME_ROTATIONAL"
OUTCOME_NOT_VISIBLE = "RETEST_OUTCOME_NOT_VISIBLE"

CONF_EXPLICIT = "RETEST_SOURCE_FIELDS_EXPLICIT"
CONF_PARTIAL = "RETEST_SOURCE_FIELDS_PARTIAL"
CONF_INFERRED = "RETEST_SOURCE_FIELDS_INFERRED"
CONF_NOT_VISIBLE = "RETEST_SOURCE_FIELDS_NOT_VISIBLE"


def _s(value: Any) -> str:
    return "" if value is None else str(value)


def _f(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        return default


def _i(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except Exception:
        return default


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(text)
        except Exception:
            return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_dt(value: Any) -> Optional[str]:
    dt = _parse_dt(value)
    if dt is None:
        return None
    return dt.isoformat().replace("+00:00", "Z")


def _seconds_between(a: Any, b: Any) -> Optional[float]:
    da = _parse_dt(a)
    db = _parse_dt(b)
    if da is None or db is None:
        return None
    return round((db - da).total_seconds(), 3)


def _zone(moment: Mapping[str, Any]) -> dict[str, Any]:
    z = moment.get("zone_memory")
    return dict(z) if isinstance(z, Mapping) else {}


def _pick(moment: Mapping[str, Any], zone: Mapping[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in moment and moment.get(key) not in (None, ""):
            return moment.get(key)
        if key in zone and zone.get(key) not in (None, ""):
            return zone.get(key)
    return None


def _status_blob(moment: Mapping[str, Any], zone: Mapping[str, Any]) -> str:
    values = [
        moment.get("retest_status"),
        moment.get("retest_state"),
        moment.get("zone_retest_status"),
        moment.get("memory_state"),
        moment.get("retest_outcome_hint"),
        zone.get("retest_status"),
        zone.get("last_retest_status"),
        zone.get("state"),
        zone.get("memory_state"),
    ]
    return " ".join(_s(v).upper() for v in values if _s(v))


def infer_retest_outcome_hint(moment: Mapping[str, Any]) -> str:
    """Infer a conservative retest outcome hint from source fields.

    This does not predict. It only canonicalizes visible source evidence.
    """
    zone = _zone(moment)
    blob = _status_blob(moment, zone)

    if any(x in blob for x in ["FAILED", "FAIL", "REJECT", "INVALID"]):
        return OUTCOME_REJECTED
    if any(x in blob for x in ["ACCEPT", "VALID", "CONFIRM"]):
        return OUTCOME_ACCEPTED
    if any(x in blob for x in ["PENDING", "WATCH", "WAIT"]):
        return OUTCOME_PENDING
    if any(x in blob for x in ["ABSORB", "FRICTION"]):
        return OUTCOME_FRICTION
    if "ROTATION" in blob:
        return OUTCOME_ROTATIONAL

    return OUTCOME_NOT_VISIBLE


def _touch_count(moment: Mapping[str, Any], zone: Mapping[str, Any]) -> int:
    candidates = [
        moment.get("retest_touch_count"),
        moment.get("zone_touch_count"),
        moment.get("touch_count"),
        moment.get("test_count"),
        zone.get("retest_touch_count"),
        zone.get("zone_touch_count"),
        zone.get("touch_count"),
        zone.get("test_count"),
        zone.get("retest_count"),
        zone.get("tests"),
    ]
    return max([_i(v, 0) for v in candidates] + [0])


def _first_touch(moment: Mapping[str, Any], zone: Mapping[str, Any]) -> Any:
    return _pick(moment, zone, [
        "retest_first_touch_time",
        "first_retest_time",
        "first_touch_time",
        "zone_first_touch_time",
        "first_tested",
    ])


def _last_touch(moment: Mapping[str, Any], zone: Mapping[str, Any]) -> Any:
    return _pick(moment, zone, [
        "retest_last_touch_time",
        "last_retest_time",
        "last_touch_time",
        "zone_last_touch_time",
        "last_tested",
        "last_seen",
    ])


def _acceptance_dwell(moment: Mapping[str, Any], zone: Mapping[str, Any], outcome: str) -> Optional[float]:
    explicit = _pick(moment, zone, [
        "retest_acceptance_dwell_seconds",
        "acceptance_dwell_seconds",
        "retest_dwell_seconds",
    ])
    if explicit is not None:
        return _f(explicit, None)

    if outcome == OUTCOME_ACCEPTED:
        first_touch = _first_touch(moment, zone)
        last_touch = _last_touch(moment, zone)
        seconds = _seconds_between(first_touch, last_touch)
        if seconds is not None and seconds >= 0:
            return seconds
    return None


def _rejection_speed(moment: Mapping[str, Any], zone: Mapping[str, Any], outcome: str) -> Optional[float]:
    explicit = _pick(moment, zone, [
        "retest_rejection_speed_pips_per_min",
        "rejection_speed_pips_per_min",
    ])
    if explicit is not None:
        return _f(explicit, None)

    if outcome != OUTCOME_REJECTED:
        return None

    delta = abs(_f(moment.get("raw_delta_pips"), 0.0) or 0.0)
    seconds = _seconds_between(moment.get("time_start"), moment.get("time_end"))
    if seconds is None or seconds <= 0:
        return None
    return round((delta / seconds) * 60.0, 6)


def _zone_distance(moment: Mapping[str, Any], zone: Mapping[str, Any]) -> Optional[float]:
    value = _pick(moment, zone, [
        "retest_zone_distance_pips",
        "zone_distance_pips",
        "distance_to_zone_pips",
    ])
    return _f(value, None)


def _confidence(moment: Mapping[str, Any], zone: Mapping[str, Any], touch_count: int, first_touch: Any, last_touch: Any, outcome: str) -> str:
    blob = _status_blob(moment, zone)
    explicit_markers = ["ACCEPT", "VALID", "CONFIRM", "FAILED", "FAIL", "REJECT", "INVALID", "PENDING", "WATCH", "WAIT"]

    if any(marker in blob for marker in explicit_markers):
        return CONF_EXPLICIT
    if touch_count > 0 or first_touch or last_touch:
        return CONF_PARTIAL
    if outcome != OUTCOME_NOT_VISIBLE:
        return CONF_INFERRED
    return CONF_NOT_VISIBLE


def enrich_moment_with_native_retest_source_fields(moment: Mapping[str, Any]) -> dict[str, Any]:
    """Return a copy of a B9 moment enriched with T0111 native retest fields.

    Safe to call from the sequence summarizer when each moment is built.
    """
    out: dict[str, Any] = deepcopy(dict(moment))
    zone = _zone(out)

    outcome = infer_retest_outcome_hint(out)
    touch_count = _touch_count(out, zone)

    # If the source explicitly talks about a retest but lacks a count, expose one minimum touch.
    if touch_count <= 0 and outcome != OUTCOME_NOT_VISIBLE:
        touch_count = 1

    first_touch = _first_touch(out, zone)
    last_touch = _last_touch(out, zone)

    if outcome != OUTCOME_NOT_VISIBLE:
        if not first_touch:
            first_touch = out.get("time_start")
        if not last_touch:
            last_touch = out.get("time_end") or out.get("time_start")

    first_touch_fmt = _fmt_dt(first_touch)
    last_touch_fmt = _fmt_dt(last_touch)

    delay = None
    if last_touch_fmt and out.get("time_start"):
        delay = _seconds_between(last_touch_fmt, out.get("time_start"))

    out["retest_source_fields_version"] = T0111_VERSION
    out["retest_touch_count"] = touch_count
    out["retest_first_touch_time"] = first_touch_fmt
    out["retest_last_touch_time"] = last_touch_fmt
    out["retest_delay_seconds"] = delay
    out["retest_acceptance_dwell_seconds"] = _acceptance_dwell(out, zone, outcome)
    out["retest_rejection_speed_pips_per_min"] = _rejection_speed(out, zone, outcome)
    out["retest_zone_distance_pips"] = _zone_distance(out, zone)
    out["retest_outcome_hint"] = outcome
    out["retest_source_field_confidence"] = _confidence(out, zone, touch_count, first_touch_fmt, last_touch_fmt, outcome)
    out["retest_source_fields_limits"] = [
        "native summarizer fields only",
        "no DB write",
        "no external Temporalite dependency",
        "missing retest source remains NOT_VISIBLE",
        "no BUY/SELL language",
    ]

    # Sync calibrated output zone_memory, without writing any DB.
    if zone or outcome != OUTCOME_NOT_VISIBLE:
        if touch_count and "touch_count" not in zone:
            zone["touch_count"] = touch_count
        if last_touch_fmt and "last_tested" not in zone:
            zone["last_tested"] = last_touch_fmt
        if outcome != OUTCOME_NOT_VISIBLE and "retest_status" not in zone:
            zone["retest_status"] = outcome
        out["zone_memory"] = zone

    return out


def enrich_summary_with_native_retest_source_fields(summary: Mapping[str, Any]) -> dict[str, Any]:
    """Enrich every moment of a summary payload with T0111 fields."""
    payload: dict[str, Any] = deepcopy(dict(summary))
    payload["moments"] = [
        enrich_moment_with_native_retest_source_fields(moment)
        for moment in payload.get("moments", [])
    ]
    payload.setdefault("b9_sequence_summarizer_native_fields", {})
    payload["b9_sequence_summarizer_native_fields"].update({
        "version": T0111_VERSION,
        "fields": [
            "retest_touch_count",
            "retest_first_touch_time",
            "retest_last_touch_time",
            "retest_delay_seconds",
            "retest_acceptance_dwell_seconds",
            "retest_rejection_speed_pips_per_min",
            "retest_zone_distance_pips",
            "retest_outcome_hint",
            "retest_source_field_confidence",
        ],
        "external_temporality_dependency": False,
        "limits": [
            "interpretation-only",
            "native source fields are not a trading signal",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
