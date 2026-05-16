"""
Multi-component T009 score formulas validated for Phase 0.

These formulas qualify battlefield flux perception. They do not emit trading
instructions. Phase 1A consumers should keep confidence, data visibility and
source_mode separate from the raw score.
"""

from __future__ import annotations

from typing import Any, Mapping


BATTLE_LEVEL_BORN_THRESHOLD = 0.70
BATTLE_ACTIVITY_MIN = 0.55
BATTLE_COMPRESSION_MIN = 0.50

ABSORPTION_CLUSTER_THRESHOLD = 0.65
ABSORPTION_PRESSURE_MIN = 0.50
ABSORPTION_COMPRESSION_MIN = 0.55

BLOCKING_DATA_VISIBILITY = {"BLIND", "STALE"}


def clamp(value: float, lower: float = 0.0, upper: float = 1.0) -> float:
    """Clamp a numeric component to the normalized 0-1 score range."""
    return max(lower, min(upper, float(value)))


def safe_div(numerator: float, denominator: float, fallback: float = 0.0) -> float:
    """Divide with a deterministic fallback for zero denominators."""
    if denominator == 0:
        return fallback
    return float(numerator) / float(denominator)


def robust_normalize(value: float) -> float:
    """Phase 0 robust normalizer placeholder.

    Phase 1A may replace this by a session-baseline robust z-score mapping.
    For the schema/formula contract, values are clipped to 0-1.
    """
    return clamp(value)


def compute_activity_score(tick_count: int, session_baseline: float) -> float:
    """activity_score = robust_normalize(tick_count / session_baseline)."""
    return robust_normalize(safe_div(tick_count, max(session_baseline, 1.0)))


def compute_compression_score(price_range_pips: float, expected_range_pips: float) -> float:
    """compression_score = 1 - clamp(price_range_pips / expected_range_pips)."""
    return 1.0 - clamp(safe_div(price_range_pips, max(expected_range_pips, 1e-12)))


def compute_dwell_score(max_ticks_in_price_bucket: int, tick_count: int) -> float:
    """dwell_score = max_ticks_in_price_bucket / tick_count."""
    return clamp(safe_div(max_ticks_in_price_bucket, max(tick_count, 1)))


def compute_retest_score(zone_revisits_last_15m: int) -> float:
    """retest_score = clamp(zone_revisits_last_15m / 3)."""
    return clamp(safe_div(zone_revisits_last_15m, 3.0))


def compute_pressure_score(signed_delta: float, directional_ticks: int) -> float:
    """pressure_score = abs(signed_delta) / max(1, directional_ticks)."""
    return clamp(abs(float(signed_delta)) / max(1, int(directional_ticks)))


def compute_failed_displacement_score(
    close_mid: float,
    open_mid: float,
    price_range: float,
    pip_size: float,
) -> float:
    """failed_displacement_score = 1 - clamp(abs(close-open)/max(range,pip))."""
    denominator = max(float(price_range), float(pip_size), 1e-12)
    return 1.0 - clamp(abs(float(close_mid) - float(open_mid)) / denominator)


def compute_spread_stability_score(spread_volatility: float, normal_spread_volatility: float) -> float:
    """spread_stability_score = 1 - clamp(spread_volatility / normal_spread_volatility)."""
    return 1.0 - clamp(safe_div(spread_volatility, max(normal_spread_volatility, 1e-12)))


def compute_pressure_or_contention_score(
    signed_delta: float,
    directional_ticks: int,
    sign_changes: int,
) -> float:
    """pressure_or_contention_score = max(delta_imbalance, flip_rate)."""
    delta_imbalance = abs(float(signed_delta)) / max(1, int(directional_ticks))
    flip_rate = int(sign_changes) / max(1, int(directional_ticks) - 1)
    return clamp(max(delta_imbalance, flip_rate))


def compute_battle_score(
    activity: float,
    compression: float,
    dwell: float,
    retest: float,
    pressure_contention: float,
) -> float:
    """
    Multi-component battle score, normalized 0-1.

    Formula:
        0.30*activity + 0.25*compression + 0.20*dwell
        + 0.15*retest + 0.10*pressure_contention
    """
    return clamp(
        0.30 * clamp(activity)
        + 0.25 * clamp(compression)
        + 0.20 * clamp(dwell)
        + 0.15 * clamp(retest)
        + 0.10 * clamp(pressure_contention)
    )


def compute_absorption_score(
    pressure: float,
    compression: float,
    failed_disp: float,
    dwell: float,
    activity: float,
    spread_stab: float,
) -> float:
    """
    Multi-component absorption score, normalized 0-1.

    Formula:
        0.35*pressure + 0.25*compression + 0.15*failed_displacement
        + 0.10*dwell + 0.10*activity + 0.05*spread_stability
    """
    return clamp(
        0.35 * clamp(pressure)
        + 0.25 * clamp(compression)
        + 0.15 * clamp(failed_disp)
        + 0.10 * clamp(dwell)
        + 0.10 * clamp(activity)
        + 0.05 * clamp(spread_stab)
    )


def is_battle_level_born(
    battle_score: float,
    activity_score: float,
    compression_score: float,
    data_visibility: str,
) -> bool:
    """Return True when Phase 1A BATTLE_LEVEL_BORN thresholds are met."""
    return (
        battle_score >= BATTLE_LEVEL_BORN_THRESHOLD
        and activity_score >= BATTLE_ACTIVITY_MIN
        and compression_score >= BATTLE_COMPRESSION_MIN
        and data_visibility not in BLOCKING_DATA_VISIBILITY
    )


def is_absorption_cluster(
    absorption_score: float,
    pressure_score: float,
    compression_score: float,
) -> bool:
    """Return True when Phase 1A ABSORPTION_CLUSTER thresholds are met."""
    return (
        absorption_score >= ABSORPTION_CLUSTER_THRESHOLD
        and pressure_score >= ABSORPTION_PRESSURE_MIN
        and compression_score >= ABSORPTION_COMPRESSION_MIN
    )


def compute_scores_from_components(components: Mapping[str, Any]) -> dict[str, float]:
    """Convenience adapter for Phase 1A modules that pass a component dict."""
    battle = compute_battle_score(
        components.get("activity_score", 0.0),
        components.get("compression_score", 0.0),
        components.get("dwell_score", 0.0),
        components.get("retest_score", 0.0),
        components.get("pressure_or_contention_score", 0.0),
    )
    absorption = compute_absorption_score(
        components.get("pressure_score", 0.0),
        components.get("compression_score", 0.0),
        components.get("failed_displacement_score", 0.0),
        components.get("dwell_score", 0.0),
        components.get("activity_score", 0.0),
        components.get("spread_stability_score", 0.0),
    )
    return {"battle_score": battle, "absorption_score": absorption}


COMPONENT_DOCUMENTATION = """
activity_score:
  Measures whether something is happening.
  robust_normalize(tick_count / session_baseline), range 0-1.

compression_score:
  Measures whether price remains confined.
  1.0 - clamp(price_range_pips / expected_range_pips), range 0-1.

dwell_score:
  Measures whether flow stays glued to a zone.
  max_ticks_in_price_bucket / tick_count, range 0-1.

retest_score:
  Measures whether the same zone returns in the film.
  clamp(zone_revisits_last_15m / 3.0), range 0-1.

pressure_or_contention_score:
  Measures unilateral pressure or two-way battle.
  max(delta_imbalance, flip_rate), range 0-1.

failed_displacement_score:
  Measures pressure that did not move price.
  1.0 - clamp(abs(close_mid - open_mid) / max(price_range, pip_size)), range 0-1.

spread_stability_score:
  Measures spread friction stability.
  1.0 - clamp(spread_volatility / normal_spread_volatility), range 0-1.
"""
