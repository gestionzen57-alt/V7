"""T0111 — B9 Native Retest Source Fields.

Read-only enrichment module.
Adds native retest evidence fields to a B9 moment dict
produced by pf_t009_sequence_summarizer.

Doctrine:
    B9 ne cherche pas le signal.
    B9 lit la trace laissée par l'effort, montre où la mémoire
    se déplace, expose ses limites, puis laisse le trader décider.

Rules:
    - No DB write.
    - No dashboard mutation.
    - No Telegram.
    - No BUY / SELL.
    - No probability of success language.
    - No global Forex volume claim.
    - Source-aware: proxy reads produce lower confidence caps.

Fields added per moment:
    retest_source_fields_version   str   — T0111 tag
    retest_touch_count             int   — nb of zone touches detected
    retest_first_touch_time        str|None
    retest_last_touch_time         str|None
    retest_delay_seconds           float|None — delay first→last touch
    retest_acceptance_dwell_seconds float|None — time price spent inside zone
    retest_rejection_speed_pips_per_min float|None
    retest_zone_distance_pips      float|None — center delta from zone anchor
    retest_outcome_hint            str   — canonical outcome enum
    retest_source_field_confidence str   — HIGH / MEDIUM / LOW / PROXY_CAUTION
    zone_memory.touch_count        int   (updates zone_memory sub-dict)
    zone_memory.last_tested        str   (updates zone_memory sub-dict)
    zone_memory.retest_status      str   (updates zone_memory sub-dict)
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

T0111_VERSION = "T0111_NATIVE_RETEST_SOURCE_FIELDS_V0"

# ─────────────────────────────────────────────────────────────────────────────
# Outcome enums — kept minimal, no directional bias
# ─────────────────────────────────────────────────────────────────────────────

RETEST_OUTCOME_NOT_VISIBLE     = "RETEST_OUTCOME_NOT_VISIBLE"
RETEST_OUTCOME_ACCEPTED        = "RETEST_OUTCOME_ACCEPTED"
RETEST_OUTCOME_FAILED          = "RETEST_OUTCOME_FAILED"
RETEST_OUTCOME_PENDING         = "RETEST_OUTCOME_PENDING"
RETEST_OUTCOME_PARTIAL         = "RETEST_OUTCOME_PARTIAL"

# Confidence levels for source-aware language
CONFIDENCE_HIGH          = "HIGH"
CONFIDENCE_MEDIUM        = "MEDIUM"
CONFIDENCE_LOW           = "LOW"
CONFIDENCE_PROXY_CAUTION = "PROXY_CAUTION"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_iso(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        ts = float(value)
        if ts > 10_000_000_000:
            ts /= 1000.0
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    text = str(value).strip().replace("Z", "+00:00").replace(" ", "T")
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except ValueError:
        return None


def _iso_utc(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _seconds_between(t1: Any, t2: Any) -> Optional[float]:
    dt1, dt2 = _parse_iso(t1), _parse_iso(t2)
    if dt1 is None or dt2 is None:
        return None
    return abs((dt2 - dt1).total_seconds())


# ─────────────────────────────────────────────────────────────────────────────
# Source confidence — lower when proxy/reconstructed
# ─────────────────────────────────────────────────────────────────────────────

def _source_confidence(moment: Dict[str, Any]) -> str:
    source_mode = str(moment.get("source_mode") or "").upper()
    data_visibility = str(moment.get("data_visibility") or "").upper()
    confidence_cap = _safe_float(moment.get("confidence_cap"), default=1.0)

    if source_mode == "M1_BAR_PROXY" or data_visibility == "RECONSTRUCTED":
        return CONFIDENCE_PROXY_CAUTION
    if confidence_cap is not None and confidence_cap < 0.4:
        return CONFIDENCE_LOW
    if confidence_cap is not None and confidence_cap < 0.7:
        return CONFIDENCE_MEDIUM

    # Check source_profile sub-dict
    sp = moment.get("source_profile")
    if isinstance(sp, dict):
        quality = str(sp.get("quality") or "").upper()
        if "PROXY" in quality or "CAUTION" in quality:
            return CONFIDENCE_PROXY_CAUTION
        if "UNKNOWN" in quality:
            return CONFIDENCE_LOW

    return CONFIDENCE_HIGH


# ─────────────────────────────────────────────────────────────────────────────
# Touch count — derived from retest_status + moment_type
# ─────────────────────────────────────────────────────────────────────────────

_RETEST_MOMENT_TYPES = {
    "T009_MOMENT_BREAK_RETEST_FAILED",
    "T009_MOMENT_RETRACE_DECISION_AREA",
    "T009_MOMENT_BREAKOUT_PENDING_RETEST",
    "T009_MOMENT_FLOW_BREATHING",
}

_ACTIVE_RETEST_STATUSES = {"ACTIVE_RETEST", "ACCEPTED", "PENDING", "FAILED"}


def _infer_touch_count(moment: Dict[str, Any]) -> int:
    """
    Infer retest touch count from available fields.
    Priority:
      1. Explicit retest_touch_count already in moment (T0110 passthrough)
      2. moment_type signals at least 1 touch
      3. retest_status signals at least 1 touch
    """
    existing = moment.get("retest_touch_count")
    if existing is not None:
        try:
            v = int(existing)
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass

    moment_type = str(moment.get("moment_type") or "")
    retest_status = str(moment.get("retest_status") or "")

    if moment_type in _RETEST_MOMENT_TYPES:
        return 1
    if retest_status in _ACTIVE_RETEST_STATUSES:
        return 1
    # zone_memory may carry touch info from T0110
    zm = moment.get("zone_memory")
    if isinstance(zm, dict):
        tc = zm.get("touch_count")
        if tc is not None:
            try:
                v = int(tc)
                if v > 0:
                    return v
            except (TypeError, ValueError):
                pass
    return 0


# ─────────────────────────────────────────────────────────────────────────────
# Retest timing fields
# ─────────────────────────────────────────────────────────────────────────────

def _infer_retest_times(moment: Dict[str, Any], touch_count: int) -> Dict[str, Any]:
    """
    Return first/last touch times.
    When only one touch detected: first == last == time_end of moment.
    time_start is used as zone anchor reference.
    """
    if touch_count == 0:
        return {
            "retest_first_touch_time": None,
            "retest_last_touch_time": None,
            "retest_delay_seconds": None,
        }

    # Explicit fields take priority (may come from T0109/T0110 upstream)
    first = moment.get("retest_first_touch_time")
    last  = moment.get("retest_last_touch_time")

    if first is None:
        # Use time_end of the moment as the touch anchor
        first = moment.get("time_end") or moment.get("time_start")
    if last is None:
        last = first

    delay = _seconds_between(
        moment.get("time_start"),
        first,
    )

    return {
        "retest_first_touch_time": first,
        "retest_last_touch_time": last,
        "retest_delay_seconds": round(delay, 1) if delay is not None else None,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Dwell + rejection speed
# ─────────────────────────────────────────────────────────────────────────────

def _infer_dwell(moment: Dict[str, Any], touch_count: int) -> Optional[float]:
    """
    Estimate time price spent inside zone during retest.
    Proxy: time_start → time_end of the moment for retest-type moments.
    Returns None when not measurable.
    """
    if touch_count == 0:
        return None
    existing = moment.get("retest_acceptance_dwell_seconds")
    if existing is not None:
        v = _safe_float(existing)
        if v is not None and v > 0:
            return round(v, 1)

    moment_type = str(moment.get("moment_type") or "")
    if moment_type in (
        "T009_MOMENT_RETRACE_DECISION_AREA",
        "T009_MOMENT_FLOW_BREATHING",
        "T009_MOMENT_ABSORPTION_SHELF",
    ):
        secs = _seconds_between(moment.get("time_start"), moment.get("time_end"))
        if secs is not None:
            return round(secs, 1)
    return None


def _infer_rejection_speed(moment: Dict[str, Any], touch_count: int) -> Optional[float]:
    """
    Estimate rejection speed in pips/min when retest fails.
    Uses center_delta_pips and moment duration.
    """
    if touch_count == 0:
        return None
    existing = moment.get("retest_rejection_speed_pips_per_min")
    if existing is not None:
        v = _safe_float(existing)
        if v is not None and v > 0:
            return round(v, 2)

    moment_type = str(moment.get("moment_type") or "")
    retest_status = str(moment.get("retest_status") or "")

    if moment_type != "T009_MOMENT_BREAK_RETEST_FAILED" and retest_status != "FAILED":
        return None

    delta_pips = abs(_safe_float(moment.get("center_delta_pips"), 0.0) or 0.0)
    duration_s = _seconds_between(moment.get("time_start"), moment.get("time_end"))
    if duration_s and duration_s > 0 and delta_pips > 0:
        pips_per_min = delta_pips / (duration_s / 60.0)
        return round(pips_per_min, 2)
    return None


# ─────────────────────────────────────────────────────────────────────────────
# Zone distance
# ─────────────────────────────────────────────────────────────────────────────

def _infer_zone_distance(moment: Dict[str, Any]) -> Optional[float]:
    """
    Distance (pips) between center_end and midpoint of zone.
    Positive = above zone mid. Negative = below.
    Returns None when zone or center unavailable.
    """
    existing = moment.get("retest_zone_distance_pips")
    if existing is not None:
        v = _safe_float(existing)
        if v is not None:
            return round(v, 2)

    center_end = _safe_float(moment.get("center_end"))
    zone_low   = _safe_float(moment.get("zone_low"))
    zone_high  = _safe_float(moment.get("zone_high"))
    pip_size   = 0.0001  # default; B9 does not handle JPY pairs specially here

    if center_end is None or zone_low is None or zone_high is None:
        return None

    zone_mid = (zone_low + zone_high) / 2.0
    return round((center_end - zone_mid) / pip_size, 2)


# ─────────────────────────────────────────────────────────────────────────────
# Outcome hint — canonical enum, never directional signal
# ─────────────────────────────────────────────────────────────────────────────

def _infer_outcome_hint(moment: Dict[str, Any], touch_count: int) -> str:
    """
    Canonical outcome enum derived from available moment fields.
    Priority:
      1. Existing retest_outcome_hint if already non-trivial
      2. moment_type / retest_status combination
      3. NOT_VISIBLE fallback
    """
    existing = str(moment.get("retest_outcome_hint") or "").upper()
    if existing and existing not in ("", "RETEST_OUTCOME_NOT_VISIBLE", "NOT_VISIBLE"):
        # Normalise legacy bare values
        if existing in ("FAILED", "BREAK_RETEST_FAILED"):
            return RETEST_OUTCOME_FAILED
        if existing in ("ACCEPTED", "RETEST_ACCEPTED"):
            return RETEST_OUTCOME_ACCEPTED
        if existing in ("PENDING", "BREAKOUT_PENDING_RETEST"):
            return RETEST_OUTCOME_PENDING
        if existing in ("PARTIAL",):
            return RETEST_OUTCOME_PARTIAL
        # If already a canonical value, pass through
        if existing.startswith("RETEST_OUTCOME_"):
            return existing

    if touch_count == 0:
        return RETEST_OUTCOME_NOT_VISIBLE

    moment_type   = str(moment.get("moment_type") or "")
    retest_status = str(moment.get("retest_status") or "")

    if moment_type == "T009_MOMENT_BREAK_RETEST_FAILED" or retest_status == "FAILED":
        return RETEST_OUTCOME_FAILED

    if moment_type == "T009_MOMENT_BREAKOUT_PENDING_RETEST" or retest_status == "PENDING":
        return RETEST_OUTCOME_PENDING

    if retest_status == "ACCEPTED":
        return RETEST_OUTCOME_ACCEPTED

    if retest_status == "ACTIVE_RETEST":
        return RETEST_OUTCOME_PARTIAL

    if moment_type in ("T009_MOMENT_RETRACE_DECISION_AREA", "T009_MOMENT_FLOW_BREATHING"):
        return RETEST_OUTCOME_PENDING

    return RETEST_OUTCOME_NOT_VISIBLE


# ─────────────────────────────────────────────────────────────────────────────
# zone_memory enrichment
# ─────────────────────────────────────────────────────────────────────────────

def _enrich_zone_memory(
    zone_memory: Dict[str, Any],
    touch_count: int,
    last_touch_time: Optional[str],
    outcome_hint: str,
) -> Dict[str, Any]:
    zm = dict(zone_memory)
    # touch_count: take max of existing vs inferred
    existing_tc = 0
    try:
        existing_tc = int(zm.get("touch_count") or 0)
    except (TypeError, ValueError):
        pass
    zm["touch_count"] = max(existing_tc, touch_count)

    # last_tested: use most recent known time
    if last_touch_time is not None:
        existing_lt = zm.get("last_tested")
        if existing_lt is None:
            zm["last_tested"] = last_touch_time
        else:
            dt_existing = _parse_iso(existing_lt)
            dt_new      = _parse_iso(last_touch_time)
            if dt_existing is not None and dt_new is not None:
                zm["last_tested"] = _iso_utc(max(dt_existing, dt_new))

    # retest_status: canonical
    status_map = {
        RETEST_OUTCOME_FAILED:   "RETEST_FAILED",
        RETEST_OUTCOME_ACCEPTED: "RETEST_ACCEPTED",
        RETEST_OUTCOME_PENDING:  "RETEST_PENDING",
        RETEST_OUTCOME_PARTIAL:  "RETEST_PARTIAL",
        RETEST_OUTCOME_NOT_VISIBLE: "RETEST_NOT_VISIBLE",
    }
    zm["retest_status"] = status_map.get(outcome_hint, "RETEST_NOT_VISIBLE")
    return zm


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def enrich_moment_with_native_retest_source_fields(
    moment: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Enrich one B9 moment dict with native T0111 retest source fields.

    Additive only — never removes existing keys.
    Safe to call on any dict shape; missing keys default gracefully.

    Returns a new dict (deep copy + additions).
    """
    out = deepcopy(moment)

    touch_count   = _infer_touch_count(out)
    timing        = _infer_retest_times(out, touch_count)
    dwell         = _infer_dwell(out, touch_count)
    rejection_spd = _infer_rejection_speed(out, touch_count)
    zone_dist     = _infer_zone_distance(out)
    outcome_hint  = _infer_outcome_hint(out, touch_count)
    confidence    = _source_confidence(out)

    # Write T0111 fields
    out["retest_source_fields_version"]          = T0111_VERSION
    out["retest_touch_count"]                    = touch_count
    out["retest_first_touch_time"]               = timing["retest_first_touch_time"]
    out["retest_last_touch_time"]                = timing["retest_last_touch_time"]
    out["retest_delay_seconds"]                  = timing["retest_delay_seconds"]
    out["retest_acceptance_dwell_seconds"]       = dwell
    out["retest_rejection_speed_pips_per_min"]   = rejection_spd
    out["retest_zone_distance_pips"]             = zone_dist
    out["retest_outcome_hint"]                   = outcome_hint
    out["retest_source_field_confidence"]        = confidence

    # Enrich zone_memory sub-dict
    zm = out.get("zone_memory")
    if isinstance(zm, dict):
        out["zone_memory"] = _enrich_zone_memory(
            zm,
            touch_count,
            timing["retest_last_touch_time"],
            outcome_hint,
        )

    return out


def enrich_moments_batch(
    moments: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Convenience: enrich a list of moment dicts."""
    return [enrich_moment_with_native_retest_source_fields(m) for m in moments]


def probe() -> Dict[str, Any]:
    """Return module identity. Used by integration checks."""
    return {
        "version": T0111_VERSION,
        "state": "READY",
        "read_only": True,
        "no_db_write": True,
        "no_dashboard": True,
        "no_telegram": True,
        "no_buy_sell": True,
        "no_probability_of_success": True,
        "fields_added": [
            "retest_source_fields_version",
            "retest_touch_count",
            "retest_first_touch_time",
            "retest_last_touch_time",
            "retest_delay_seconds",
            "retest_acceptance_dwell_seconds",
            "retest_rejection_speed_pips_per_min",
            "retest_zone_distance_pips",
            "retest_outcome_hint",
            "retest_source_field_confidence",
            "zone_memory.touch_count",
            "zone_memory.last_tested",
            "zone_memory.retest_status",
        ],
    }


__all__ = [
    "T0111_VERSION",
    "RETEST_OUTCOME_NOT_VISIBLE",
    "RETEST_OUTCOME_ACCEPTED",
    "RETEST_OUTCOME_FAILED",
    "RETEST_OUTCOME_PENDING",
    "RETEST_OUTCOME_PARTIAL",
    "enrich_moment_with_native_retest_source_fields",
    "enrich_moments_batch",
    "probe",
]
