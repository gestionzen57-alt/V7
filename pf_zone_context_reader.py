"""PowerFlow B9 - Zone context reader.

Read-only helper that qualifies a worked price zone from local touch history.
It does not mutate the database, dashboard, or external outputs.
"""

from __future__ import annotations

from typing import Any, Mapping

PIP_SIZE = 0.0001

MIN_REACTIVATION_DWELL = 30.0
MIN_REACTION_PIPS = 8.0
MIN_TICKS = 5
MIN_TOTAL_DWELL = 45.0
MIN_ACCEPTANCE_DWELL = 20.0
MAX_LOW_PROGRESS = 3.0
STALE_BARS_THRESHOLD = 50
MIN_ABSORPTION_TOUCHES = 2
MIN_ABSORPTION_TICKS = 10
MIN_ROTATION_CENTER_CROSSES = 3
ROTATION_MAX_DISTANCE_FACTOR = 0.6

ZONE_ROLE_REJECTION = "REJECTION_ZONE"
ZONE_ROLE_ACCEPTANCE = "ACCEPTANCE_ZONE"
ZONE_ROLE_ABSORPTION = "ABSORPTION_ZONE"
ZONE_ROLE_BREAK_RETEST = "BREAK_RETEST_ZONE"
ZONE_ROLE_ROTATION_ANCHOR = "ROTATION_ANCHOR_ZONE"
ZONE_ROLE_UNDEFINED = "UNDEFINED"

ZONE_STATUS_ACTIVE = "ACTIVE"
ZONE_STATUS_STALE = "STALE"
ZONE_STATUS_REACTIVATED = "OLD_BUT_REACTIVATED"
ZONE_STATUS_CONSUMED = "CONSUMED"

REACTIVATION_SINGLE_STRONG = "SINGLE_STRONG"
REACTIVATION_MULTI_TOUCH = "MULTI_TOUCH"
REACTIVATION_NONE = "NONE"


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_history(zone_touch_history: list[dict] | None) -> list[dict]:
    if not zone_touch_history:
        return []
    return [entry for entry in zone_touch_history if isinstance(entry, dict)]


def _field(entry: Mapping[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in entry and entry[name] is not None:
            return entry[name]
    return default


def _inside_zone(price: float, zone_low: float, zone_high: float) -> bool:
    return zone_low <= price <= zone_high


def _pips(distance: float) -> float:
    return abs(distance) / PIP_SIZE


def _zone_width_pips(zone_low: float, zone_high: float) -> float:
    return _pips(zone_high - zone_low)


def _touch_price_exit(entry: Mapping[str, Any]) -> float | None:
    raw = _field(entry, "price_exit", "exit_price", "close", default=None)
    if raw is None:
        return None
    return _as_float(raw)


def _net_progress_pips(history: list[dict], fallback: float | None = None) -> float:
    explicit_values = [
        _as_float(_field(entry, "net_price_progress_pips", default=None), default=float("nan"))
        for entry in history
        if _field(entry, "net_price_progress_pips", default=None) is not None
    ]
    if explicit_values:
        return abs(explicit_values[-1])

    exits = [_touch_price_exit(entry) for entry in history]
    exits = [value for value in exits if value is not None]
    if len(exits) >= 2:
        return _pips(exits[-1] - exits[0])
    if fallback is not None:
        return abs(fallback)
    return 0.0


def _center_penetration_ratio(
    history: list[dict], zone_low: float, zone_high: float, current_price: float
) -> float:
    explicit = [
        _as_float(_field(entry, "center_penetration_ratio", default=None), default=-1.0)
        for entry in history
        if _field(entry, "center_penetration_ratio", default=None) is not None
    ]
    if explicit:
        return max(0.0, min(1.0, max(explicit)))

    width = max(zone_high - zone_low, PIP_SIZE)
    center = (zone_low + zone_high) / 2.0
    distances = []
    for entry in history:
        exit_price = _touch_price_exit(entry)
        if exit_price is not None:
            distances.append(abs(exit_price - center))
    distances.append(abs(current_price - center))
    best_distance = min(distances) if distances else width / 2.0
    return max(0.0, min(1.0, 1.0 - (best_distance / (width / 2.0))))


def _center_accepted(history: list[dict], zone_low: float, zone_high: float, current_price: float) -> bool:
    for entry in history:
        value = _field(entry, "center_accepted", default=None)
        if value is not None:
            return bool(value)
    return _center_penetration_ratio(history, zone_low, zone_high, current_price) >= 0.5


def _price_returned_to_zone(history: list[dict], zone_low: float, zone_high: float, current_price: float) -> bool:
    if _inside_zone(current_price, zone_low, zone_high):
        return True
    for entry in history:
        if bool(_field(entry, "price_returns_to_zone", default=False)):
            return True
        exit_price = _touch_price_exit(entry)
        if exit_price is not None and _inside_zone(exit_price, zone_low, zone_high):
            return True
    return False


def _has_prior_breakout(history: list[dict]) -> bool:
    return any(bool(_field(entry, "prior_breakout", default=False)) for entry in history)


def _retest_outcome(history: list[dict]) -> str | None:
    allowed = {"ACCEPTED", "REJECTED", "FAILED"}
    for entry in reversed(history):
        outcome = _field(entry, "retest_outcome", default=None)
        if isinstance(outcome, str) and outcome.upper() in allowed:
            return outcome.upper()
    return None


def _center_cross_count(history: list[dict]) -> int:
    explicit = [
        _as_int(_field(entry, "center_cross_count", default=None), default=0)
        for entry in history
        if _field(entry, "center_cross_count", default=None) is not None
    ]
    if explicit:
        return max(explicit)
    return sum(1 for entry in history if bool(_field(entry, "center_crossed", default=False)))


def _max_distance(history: list[dict], name: str, default: float) -> float:
    values = [
        _as_float(_field(entry, name, default=None), default=0.0)
        for entry in history
        if _field(entry, name, default=None) is not None
    ]
    if not values:
        return default
    return max(values)


def _directional_escape(history: list[dict]) -> bool:
    return any(bool(_field(entry, "directional_escape", default=False)) for entry in history)


def _confidence(
    *,
    touch_count: int,
    total_ticks_inside: int,
    total_dwell_seconds: float,
    zone_role: str,
    zone_status: str,
    source_stack: str,
) -> float:
    score = 0.20
    if touch_count > 0:
        score += 0.15
    if total_ticks_inside >= MIN_TICKS:
        score += 0.10
    if total_ticks_inside >= MIN_ABSORPTION_TICKS:
        score += 0.05
    if total_dwell_seconds >= MIN_ACCEPTANCE_DWELL:
        score += 0.10
    if total_dwell_seconds >= MIN_TOTAL_DWELL:
        score += 0.05
    if zone_role != ZONE_ROLE_UNDEFINED:
        score += 0.20
    if zone_status == ZONE_STATUS_REACTIVATED:
        score += 0.10
    elif zone_status == ZONE_STATUS_ACTIVE:
        score += 0.05
    elif zone_status == ZONE_STATUS_STALE:
        score -= 0.10

    if "READING_PARTIAL" in source_stack or "DEGRADED" in source_stack:
        score = min(score, 0.45)

    return round(max(0.05, min(0.95, score)), 3)


def read_zone_context(
    zone_low: float,
    zone_high: float,
    zone_touch_history: list[dict],
    zone_bars_since_touch: int,
    current_price: float,
    source_stack: str = "FORCE_SNAPSHOT_DERIVED",
) -> dict:
    """Qualify a price zone from local touch evidence.

    The function is deliberately read-only. It transforms input facts into a
    compact B9 zone context that downstream readers can consume.
    """

    if zone_high < zone_low:
        zone_low, zone_high = zone_high, zone_low

    history = _safe_history(zone_touch_history)
    center = (zone_low + zone_high) / 2.0
    width_pips = _zone_width_pips(zone_low, zone_high)

    touch_count = len(history)
    touch_zone = touch_count > 0 or _inside_zone(current_price, zone_low, zone_high)
    ticks_per_touch = [
        _as_int(_field(entry, "ticks", "raw_tick_count", "ticks_inside_zone", default=0))
        for entry in history
    ]
    dwell_per_touch = [
        _as_float(_field(entry, "dwell_sec", "dwell_seconds", "dwell_seconds_inside_zone", default=0.0))
        for entry in history
    ]
    reaction_per_touch = [
        abs(_as_float(_field(entry, "reaction_pips", "reaction_distance_pips", default=0.0)))
        for entry in history
    ]

    total_ticks_inside = sum(ticks_per_touch)
    total_dwell_seconds = sum(dwell_per_touch)
    dwell_seconds_inside_zone = max(dwell_per_touch, default=0.0)
    raw_tick_count = max(ticks_per_touch, default=0)
    reaction_distance_pips = max(reaction_per_touch, default=0.0)
    rejection_distance_pips = reaction_distance_pips
    center_accepted = _center_accepted(history, zone_low, zone_high, current_price)
    center_penetration_ratio = _center_penetration_ratio(history, zone_low, zone_high, current_price)
    net_price_progress_pips = _net_progress_pips(history)

    prior_breakout = _has_prior_breakout(history)
    price_returns_to_zone = _price_returned_to_zone(history, zone_low, zone_high, current_price)
    retest_outcome = _retest_outcome(history)
    center_cross_count = _center_cross_count(history)
    max_distance_above_center = _max_distance(history, "max_distance_above_center", default=width_pips)
    max_distance_below_center = _max_distance(history, "max_distance_below_center", default=width_pips)
    directional_escape = _directional_escape(history)

    is_break_retest_zone = bool(
        prior_breakout and price_returns_to_zone and retest_outcome in {"ACCEPTED", "REJECTED", "FAILED"}
    )
    is_rotation_anchor_zone = bool(
        center_cross_count >= MIN_ROTATION_CENTER_CROSSES
        and max_distance_above_center <= width_pips * ROTATION_MAX_DISTANCE_FACTOR
        and max_distance_below_center <= width_pips * ROTATION_MAX_DISTANCE_FACTOR
        and not directional_escape
    )
    is_absorption_zone = bool(
        touch_count >= MIN_ABSORPTION_TOUCHES
        and total_ticks_inside >= MIN_ABSORPTION_TICKS
        and net_price_progress_pips <= MAX_LOW_PROGRESS
    )
    is_rejection_zone = bool(
        touch_zone and not center_accepted and rejection_distance_pips >= MIN_REACTION_PIPS
    )
    is_acceptance_zone = bool(
        touch_zone and center_accepted and dwell_seconds_inside_zone >= MIN_ACCEPTANCE_DWELL
    )

    if is_break_retest_zone:
        zone_role = ZONE_ROLE_BREAK_RETEST
    elif is_rotation_anchor_zone:
        zone_role = ZONE_ROLE_ROTATION_ANCHOR
    elif is_absorption_zone:
        zone_role = ZONE_ROLE_ABSORPTION
    elif is_rejection_zone:
        zone_role = ZONE_ROLE_REJECTION
    elif is_acceptance_zone:
        zone_role = ZONE_ROLE_ACCEPTANCE
    else:
        zone_role = ZONE_ROLE_UNDEFINED

    zone_was_stale = zone_bars_since_touch > STALE_BARS_THRESHOLD
    strong_single_reactivation = bool(
        touch_count == 1
        and dwell_seconds_inside_zone >= MIN_REACTIVATION_DWELL
        and reaction_distance_pips >= MIN_REACTION_PIPS
        and raw_tick_count >= MIN_TICKS
    )
    multi_touch_reactivation = bool(
        touch_count >= MIN_ABSORPTION_TOUCHES and total_dwell_seconds >= MIN_TOTAL_DWELL
    )
    reactivated = bool(zone_was_stale and (strong_single_reactivation or multi_touch_reactivation))

    if reactivated:
        zone_status = ZONE_STATUS_REACTIVATED
        reactivation_type = (
            REACTIVATION_SINGLE_STRONG if strong_single_reactivation else REACTIVATION_MULTI_TOUCH
        )
    elif zone_was_stale:
        zone_status = ZONE_STATUS_STALE
        reactivation_type = REACTIVATION_NONE
    elif zone_role == ZONE_ROLE_UNDEFINED and total_dwell_seconds >= MIN_TOTAL_DWELL and reaction_distance_pips < MIN_REACTION_PIPS:
        zone_status = ZONE_STATUS_CONSUMED
        reactivation_type = REACTIVATION_NONE
    else:
        zone_status = ZONE_STATUS_ACTIVE
        reactivation_type = REACTIVATION_NONE

    confidence = _confidence(
        touch_count=touch_count,
        total_ticks_inside=total_ticks_inside,
        total_dwell_seconds=total_dwell_seconds,
        zone_role=zone_role,
        zone_status=zone_status,
        source_stack=source_stack,
    )

    metrics = {
        "touch_count": touch_count,
        "ticks_inside_zone": total_ticks_inside,
        "raw_tick_count": raw_tick_count,
        "dwell_seconds": round(total_dwell_seconds, 3),
        "max_dwell_seconds": round(dwell_seconds_inside_zone, 3),
        "reaction_distance_pips": round(reaction_distance_pips, 3),
        "rejection_distance_pips": round(rejection_distance_pips, 3),
        "center_penetration_ratio": round(center_penetration_ratio, 3),
        "net_price_progress_pips": round(net_price_progress_pips, 3),
        "center_accepted": center_accepted,
        "prior_breakout": prior_breakout,
        "price_returns_to_zone": price_returns_to_zone,
        "retest_outcome": retest_outcome,
        "center_cross_count": center_cross_count,
    }

    return {
        "zone_role": zone_role,
        "zone_status": zone_status,
        "zone_memory_active": bool(zone_status in {ZONE_STATUS_ACTIVE, ZONE_STATUS_REACTIVATED} and zone_role != ZONE_ROLE_UNDEFINED),
        "reactivation_status": {
            "was_stale": zone_was_stale,
            "reactivated": reactivated,
            "reactivation_type": reactivation_type,
            "evidence": {
                "strong_single_reactivation": strong_single_reactivation,
                "multi_touch_reactivation": multi_touch_reactivation,
                "dwell_seconds_inside_zone": round(dwell_seconds_inside_zone, 3),
                "total_dwell_seconds": round(total_dwell_seconds, 3),
                "reaction_distance_pips": round(reaction_distance_pips, 3),
                "raw_tick_count": raw_tick_count,
                "touch_count": touch_count,
            },
        },
        "confidence": confidence,
        "source_stack": source_stack,
        "zone_bounds": {
            "zone_low": zone_low,
            "zone_high": zone_high,
            "center": center,
            "width_pips": round(width_pips, 3),
        },
        "microfilm_metrics": metrics,
    }


__all__ = [
    "read_zone_context",
    "MIN_REACTIVATION_DWELL",
    "MIN_REACTION_PIPS",
    "MIN_TICKS",
    "MIN_TOTAL_DWELL",
    "MIN_ACCEPTANCE_DWELL",
    "MAX_LOW_PROGRESS",
    "STALE_BARS_THRESHOLD",
]
