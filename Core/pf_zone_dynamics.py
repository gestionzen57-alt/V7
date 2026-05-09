"""
PowerFlow V6 - pf_zone_dynamics.py
Version: V0.2.2 contextual profiles

Mission:
    Read the internal respiration of a currency in a dynamic zone.

Doctrine:
    A zone is not a fixed line. It is a behavioral field.
    The module measures:
      - statistical extreme: PRE_EXTREME / EXTREME
      - pullback respiration: absorbed / leaking / rupture
      - contextual profile: short / medium / long horizon, with M1 as special microfilm
      - time/session/rank hints without forcing a direction

Compatibility:
    Existing call stays valid:
        analyze_zone_dynamics(z_series)

V0.2.3:
  - Ajout EARLY_EXTREME : zone EXTREME réelle, mais pas assez mature
    pour ACCUMULATING / LEAKING / RUPTURE.

    Contextual call is optional:
        analyze_zone_dynamics(
            z_series,
            timeframe=5,
            currency="GBP",
            session_phase="LONDON",
            rank_position=8,
            rank_total=8,
            rank_duration_bars=30,
        )
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple, Union


# ==========================================================================
# CONSTANTS - LEGACY DEFAULTS
# ==========================================================================

DEFAULT_LOOKBACK: int = 20

TF_LOOKBACKS: Dict[int, int] = {
    1: 60,
    5: 50,
    15: 30,
    30: 25,
    60: 20,
    240: 20,
    1440: 20,
    10080: 20,
}

EXTREME_THRESHOLD: float = 2.0
NEAR_EXTREME_THRESHOLD: float = 1.5
MIN_PULLBACK_AMPLITUDE: float = 0.15
MIN_BARS_FOR_DIAGNOSIS: int = 5
MIN_PULLBACKS_FOR_TREND: int = 2
LEAK_SLOPE_THRESHOLD: float = 0.08
RUPTURE_ACCELERATION_THRESHOLD: float = 0.15
EPSILON: float = 1e-9


# ==========================================================================
# PROFILES - CONTEXTUAL SENSITIVITY
# ==========================================================================

@dataclass(frozen=True)
class ZoneProfile:
    """Contextual calibration for one horizon/timeframe family."""

    name: str
    horizon: str
    lookback: int
    pre_extreme_threshold: float
    extreme_threshold: float
    min_bars_for_diagnosis: int
    min_pullbacks_for_trend: int
    min_pullback_amplitude: float
    leak_slope_threshold: float
    rupture_acceleration_threshold: float
    pre_extreme_factor: float = 0.5
    early_extreme_factor: float = 0.8
    accumulation_factor: float = 1.5
    neutral_factor: float = 1.0
    leaking_factor: float = 0.6
    rupture_factor: float = 0.2
    disorder_factor: float = 0.75
    max_tolerated_out_bars: int = 2

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "horizon": self.horizon,
            "lookback": self.lookback,
            "pre_extreme_threshold": self.pre_extreme_threshold,
            "extreme_threshold": self.extreme_threshold,
            "min_bars_for_diagnosis": self.min_bars_for_diagnosis,
            "min_pullbacks_for_trend": self.min_pullbacks_for_trend,
            "min_pullback_amplitude": self.min_pullback_amplitude,
            "leak_slope_threshold": self.leak_slope_threshold,
            "rupture_acceleration_threshold": self.rupture_acceleration_threshold,
            "pre_extreme_factor": self.pre_extreme_factor,
            "early_extreme_factor": self.early_extreme_factor,
            "accumulation_factor": self.accumulation_factor,
            "neutral_factor": self.neutral_factor,
            "leaking_factor": self.leaking_factor,
            "rupture_factor": self.rupture_factor,
            "disorder_factor": self.disorder_factor,
            "max_tolerated_out_bars": self.max_tolerated_out_bars,
        }


SHORT_PROFILE = ZoneProfile(
    name="SHORT",
    horizon="M1_M5_M15_SHORT_TERM",
    lookback=50,
    pre_extreme_threshold=1.45,
    extreme_threshold=1.90,
    min_bars_for_diagnosis=3,
    min_pullbacks_for_trend=2,
    min_pullback_amplitude=0.12,
    leak_slope_threshold=0.06,
    rupture_acceleration_threshold=0.12,
)

MEDIUM_PROFILE = ZoneProfile(
    name="MEDIUM",
    horizon="M15_M30_H1_SCENARIO",
    lookback=30,
    pre_extreme_threshold=1.50,
    extreme_threshold=2.00,
    min_bars_for_diagnosis=5,
    min_pullbacks_for_trend=2,
    min_pullback_amplitude=0.15,
    leak_slope_threshold=0.08,
    rupture_acceleration_threshold=0.15,
)

LONG_PROFILE = ZoneProfile(
    name="LONG",
    horizon="H4_D1_W_GRAVITY",
    lookback=20,
    pre_extreme_threshold=1.60,
    extreme_threshold=2.10,
    min_bars_for_diagnosis=4,
    min_pullbacks_for_trend=2,
    min_pullback_amplitude=0.20,
    leak_slope_threshold=0.10,
    rupture_acceleration_threshold=0.18,
)

PROFILE_BY_TIMEFRAME: Dict[int, ZoneProfile] = {
    # SHORT has nuance:
    #   M1  = special microfilm chapter, very reactive.
    #   M5/M15 = intermediate short-term battlefield/release profile.
    # M15 can still be forced into MEDIUM by passing profile="MEDIUM"
    # when the caller wants scenario-level reading.
    1: replace(
        SHORT_PROFILE,
        horizon="M1_SPECIAL_MICROFILM",
        lookback=TF_LOOKBACKS[1],
        min_bars_for_diagnosis=3,
        min_pullback_amplitude=0.10,
        leak_slope_threshold=0.055,
        rupture_acceleration_threshold=0.11,
    ),
    5: replace(
        SHORT_PROFILE,
        horizon="M5_M15_INTERMEDIATE_RELEASE",
        lookback=TF_LOOKBACKS[5],
        min_pullback_amplitude=0.12,
    ),
    15: replace(
        SHORT_PROFILE,
        horizon="M5_M15_INTERMEDIATE_RELEASE",
        lookback=TF_LOOKBACKS[15],
        pre_extreme_threshold=1.48,
        extreme_threshold=1.95,
        min_bars_for_diagnosis=4,
        min_pullback_amplitude=0.13,
        leak_slope_threshold=0.07,
        rupture_acceleration_threshold=0.13,
    ),
    30: replace(MEDIUM_PROFILE, lookback=TF_LOOKBACKS[30]),
    60: replace(MEDIUM_PROFILE, lookback=TF_LOOKBACKS[60]),
    240: replace(LONG_PROFILE, lookback=TF_LOOKBACKS[240]),
    1440: replace(LONG_PROFILE, lookback=TF_LOOKBACKS[1440]),
    10080: replace(LONG_PROFILE, lookback=TF_LOOKBACKS[10080]),
}

# Small character adjustments. They are deliberately conservative.
CURRENCY_ADJUSTMENTS: Dict[str, Dict[str, float]] = {
    "JPY": {"pre": 0.05, "extreme": 0.05, "pullback": 0.03},
    "CHF": {"pre": -0.05, "extreme": -0.05, "pullback": 0.00},
    "GBP": {"pre": 0.00, "extreme": 0.00, "pullback": 0.00},
    "EUR": {"pre": 0.00, "extreme": 0.00, "pullback": 0.00},
    "USD": {"pre": 0.00, "extreme": 0.00, "pullback": 0.00},
    "CAD": {"pre": 0.00, "extreme": 0.00, "pullback": 0.00},
    "AUD": {"pre": 0.00, "extreme": 0.00, "pullback": 0.00},
    "NZD": {"pre": 0.00, "extreme": 0.00, "pullback": 0.00},
}


ProfileInput = Union[None, str, Mapping[str, Any], ZoneProfile]


def get_lookback_for_timeframe(timeframe: Optional[int]) -> int:
    """Return the calibrated lookback for a timeframe."""
    try:
        tf = int(timeframe) if timeframe is not None else 0
    except (TypeError, ValueError):
        return DEFAULT_LOOKBACK
    return TF_LOOKBACKS.get(tf, DEFAULT_LOOKBACK)


def get_available_profiles_for_timeframe(timeframe: Optional[int]) -> List[str]:
    """Return profile families that make sense for a timeframe.

    M15 is intentionally a bridge: it can be read as SHORT for local
    release/battlefield work, or as MEDIUM for scenario work.
    """
    try:
        tf = int(timeframe) if timeframe is not None else 0
    except (TypeError, ValueError):
        return ["MEDIUM"]

    if tf == 1:
        return ["SHORT", "M1_SPECIAL"]
    if tf in (5,):
        return ["SHORT"]
    if tf == 15:
        return ["SHORT", "MEDIUM", "BRIDGE"]
    if tf in (30, 60):
        return ["MEDIUM"]
    if tf in (240, 1440, 10080):
        return ["LONG"]
    return ["MEDIUM"]


def get_zone_profile(
    timeframe: Optional[int] = None,
    currency: Optional[str] = None,
    session_phase: Optional[str] = None,
    profile: ProfileInput = None,
) -> ZoneProfile:
    """Resolve the contextual profile used by the zone engine.

    profile may be:
      - None: infer from timeframe
      - "SHORT" / "MEDIUM" / "LONG"
      - ZoneProfile instance
      - dict overriding fields of the inferred profile
    """
    if isinstance(profile, ZoneProfile):
        base = profile
    elif isinstance(profile, str):
        key = profile.upper().strip()
        if key == "SHORT":
            base = SHORT_PROFILE
        elif key == "LONG":
            base = LONG_PROFILE
        else:
            base = MEDIUM_PROFILE
    else:
        try:
            tf = int(timeframe) if timeframe is not None else 0
        except (TypeError, ValueError):
            tf = 0
        base = PROFILE_BY_TIMEFRAME.get(tf, MEDIUM_PROFILE)

    # Override from dict after choosing base.
    if isinstance(profile, Mapping):
        allowed = set(ZoneProfile.__dataclass_fields__.keys())
        updates = {k: v for k, v in profile.items() if k in allowed}
        base = replace(base, **updates)

    # Currency tempo adjustment.
    cur = (currency or "").upper().strip()
    adj = CURRENCY_ADJUSTMENTS.get(cur)
    if adj:
        base = replace(
            base,
            pre_extreme_threshold=max(0.5, base.pre_extreme_threshold + adj.get("pre", 0.0)),
            extreme_threshold=max(0.6, base.extreme_threshold + adj.get("extreme", 0.0)),
            min_pullback_amplitude=max(0.01, base.min_pullback_amplitude + adj.get("pullback", 0.0)),
        )

    # Session phase stays light here: it creates tags later, not hidden thresholds.
    _ = session_phase
    return base


# ==========================================================================
# OUTPUT STRUCTURES
# ==========================================================================

@dataclass(frozen=True)
class Pullback:
    start_idx: int
    peak_idx: int
    end_idx: int
    depth: float
    duration_bars: int
    direction: str
    absorbed: bool

    def to_dict(self) -> dict:
        return {
            "start_idx": self.start_idx,
            "peak_idx": self.peak_idx,
            "end_idx": self.end_idx,
            "depth": self.depth,
            "duration_bars": self.duration_bars,
            "direction": self.direction,
            "absorbed": self.absorbed,
        }


@dataclass(frozen=True)
class ZoneDiagnosis:
    state: str
    bars_in_extreme: int
    z_current: float
    z_extreme_dir: str
    pullbacks: List[Pullback]
    depth_slope: float
    depth_acceleration: float
    absorption_factor: float
    tension_score: float
    note: str
    zone_level: str = "NORMAL"
    profile_name: str = "MEDIUM"
    profile_horizon: str = "M15_M30_SCENARIO"
    timeframe: Optional[int] = None
    currency: Optional[str] = None
    session_phase: Optional[str] = None
    context_score: float = 0.0
    contextual_tags: Tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "bars_in_extreme": self.bars_in_extreme,
            "z_current": self.z_current,
            "z_extreme_dir": self.z_extreme_dir,
            "zone_level": self.zone_level,
            "pullbacks": [p.to_dict() for p in self.pullbacks],
            "depth_slope": self.depth_slope,
            "depth_acceleration": self.depth_acceleration,
            "absorption_factor": self.absorption_factor,
            "tension_score": self.tension_score,
            "note": self.note,
            "profile_name": self.profile_name,
            "profile_horizon": self.profile_horizon,
            "timeframe": self.timeframe,
            "currency": self.currency,
            "session_phase": self.session_phase,
            "context_score": self.context_score,
            "contextual_tags": list(self.contextual_tags),
        }


# ==========================================================================
# LOW LEVEL HELPERS
# ==========================================================================

def _as_float_list(z_series: Sequence[Optional[float]]) -> List[Optional[float]]:
    out: List[Optional[float]] = []
    for z in z_series:
        if z is None:
            out.append(None)
            continue
        try:
            out.append(float(z))
        except (TypeError, ValueError):
            out.append(None)
    return out


def _is_extreme(z: Optional[float], direction: str = "ANY", profile: ProfileInput = None) -> bool:
    prof = get_zone_profile(profile=profile)
    if z is None:
        return False
    if direction == "HIGH":
        return z >= prof.extreme_threshold
    if direction == "LOW":
        return z <= -prof.extreme_threshold
    return abs(z) >= prof.extreme_threshold


def _zone_level_for_z(z: Optional[float], prof: ZoneProfile) -> str:
    if z is None:
        return "NORMAL"
    abs_z = abs(z)
    if abs_z >= prof.extreme_threshold:
        return "EXTREME"
    if abs_z >= prof.pre_extreme_threshold:
        return "PRE_EXTREME"
    return "NORMAL"


def _direction_from_current_z(z: Optional[float], prof: ZoneProfile) -> str:
    if z is None or abs(z) < prof.pre_extreme_threshold:
        return "NONE"
    return "HIGH" if z > 0 else "LOW"


def _detect_extreme_direction(z_series: Sequence[Optional[float]], prof: ZoneProfile) -> str:
    valid = [z for z in z_series if z is not None]
    if not valid:
        return "NONE"
    recent = valid[-min(5, len(valid)):]
    n_high = sum(1 for z in recent if z >= prof.pre_extreme_threshold)
    n_low = sum(1 for z in recent if z <= -prof.pre_extreme_threshold)
    if n_high >= 2 and n_high > n_low:
        return "HIGH"
    if n_low >= 2 and n_low > n_high:
        return "LOW"
    return "NONE"


def _count_bars_in_extreme(
    z_series: Sequence[Optional[float]],
    direction: str,
    prof: ZoneProfile,
) -> int:
    """Count recent bars belonging to the current zone influence field."""
    if direction not in ("HIGH", "LOW"):
        return 0
    sign = 1 if direction == "HIGH" else -1
    threshold = prof.pre_extreme_threshold
    consecutive_out = 0
    count = 0
    started = False

    for z in reversed(z_series):
        if z is None:
            consecutive_out += 1
            if consecutive_out > prof.max_tolerated_out_bars:
                break
            continue
        in_zone = (z * sign) >= threshold
        if in_zone:
            count += 1
            consecutive_out = 0
            started = True
        else:
            if not started:
                continue
            consecutive_out += 1
            if consecutive_out > prof.max_tolerated_out_bars:
                break
    return count


# ==========================================================================
# PULLBACK DETECTION
# ==========================================================================

def detect_pullbacks(
    z_series: Sequence[Optional[float]],
    direction: str,
    profile: ProfileInput = None,
) -> List[Pullback]:
    """Detect pullbacks from an extreme zone and their absorption."""
    prof = get_zone_profile(profile=profile)
    series = _as_float_list(z_series)

    if direction not in ("HIGH", "LOW"):
        return []

    pullbacks: List[Pullback] = []
    in_pullback = False
    pb_start_idx = 0
    pb_peak_idx = 0
    pb_peak_z = 0.0
    z_at_extreme_before = 0.0
    bars_far_from_zone = 0
    sign = 1 if direction == "HIGH" else -1

    def _close_pullback_now(end_idx: int, absorbed: bool) -> None:
        depth = abs(z_at_extreme_before - pb_peak_z)
        if depth >= prof.min_pullback_amplitude:
            pullbacks.append(Pullback(
                start_idx=pb_start_idx,
                peak_idx=pb_peak_idx,
                end_idx=end_idx,
                depth=round(depth, 3),
                duration_bars=max(0, end_idx - pb_start_idx),
                direction="FROM_HIGH" if direction == "HIGH" else "FROM_LOW",
                absorbed=absorbed,
            ))

    for i, z in enumerate(series):
        if z is None:
            if in_pullback:
                _close_pullback_now(i - 1 if i > 0 else 0, absorbed=False)
                in_pullback = False
                bars_far_from_zone = 0
            continue

        z_signed = z * sign

        if not in_pullback:
            if z_signed >= prof.extreme_threshold:
                continue
            if z_signed >= prof.pre_extreme_threshold or z_signed > -prof.pre_extreme_threshold:
                if i > 0 and series[i - 1] is not None:
                    z_prev = series[i - 1]
                    if z_prev is not None and z_prev * sign >= prof.extreme_threshold:
                        in_pullback = True
                        pb_start_idx = i
                        pb_peak_idx = i
                        pb_peak_z = z
                        z_at_extreme_before = z_prev
                        bars_far_from_zone = 0 if z_signed >= prof.pre_extreme_threshold else 1
        else:
            if z_signed >= prof.extreme_threshold:
                _close_pullback_now(i, absorbed=True)
                in_pullback = False
                bars_far_from_zone = 0
            else:
                if direction == "HIGH" and z < pb_peak_z:
                    pb_peak_z = z
                    pb_peak_idx = i
                elif direction == "LOW" and z > pb_peak_z:
                    pb_peak_z = z
                    pb_peak_idx = i

                if z_signed < prof.pre_extreme_threshold:
                    bars_far_from_zone += 1
                else:
                    bars_far_from_zone = 0

                if bars_far_from_zone >= 3:
                    _close_pullback_now(i, absorbed=False)
                    in_pullback = False
                    bars_far_from_zone = 0

    if in_pullback:
        _close_pullback_now(len(series) - 1, absorbed=False)
    return pullbacks


# ==========================================================================
# TOPOLOGICAL DIAGNOSIS
# ==========================================================================

def _compute_depth_derivatives(
    pullbacks: Sequence[Pullback],
    profile: ProfileInput = None,
) -> Tuple[float, float]:
    prof = get_zone_profile(profile=profile)
    if len(pullbacks) < prof.min_pullbacks_for_trend:
        return 0.0, 0.0

    depths = [p.depth for p in pullbacks]
    n = len(depths)
    xs = list(range(n))
    mean_x = sum(xs) / n
    mean_y = sum(depths) / n
    num = sum((xs[i] - mean_x) * (depths[i] - mean_y) for i in range(n))
    den = sum((xs[i] - mean_x) ** 2 for i in range(n))
    slope = num / den if abs(den) > EPSILON else 0.0

    if n < 3:
        acceleration = 0.0
    else:
        mid = n // 2
        first_half = depths[:mid]
        second_half = depths[mid:]
        slope_1 = (first_half[-1] - first_half[0]) / (len(first_half) - 1) if len(first_half) >= 2 else 0.0
        slope_2 = (second_half[-1] - second_half[0]) / (len(second_half) - 1) if len(second_half) >= 2 else 0.0
        acceleration = slope_2 - slope_1

    return round(slope, 4), round(acceleration, 4)


def _looks_like_disorder(
    z_series: Sequence[Optional[float]],
    direction: str,
    bars_in_extreme: int,
    pullbacks: Sequence[Pullback],
    slope: float,
    prof: ZoneProfile,
) -> bool:
    """Detect active but unstable field without forcing a clean label."""
    valid = [z for z in z_series if z is not None]
    if len(valid) < prof.min_bars_for_diagnosis:
        return False

    recent = valid[-min(12, len(valid)):]
    active_count = sum(1 for z in recent if abs(z) >= prof.pre_extreme_threshold)
    if active_count < max(3, prof.min_bars_for_diagnosis):
        return False

    # Direction keeps switching in the active area.
    signs = [1 if z > 0 else -1 for z in recent if abs(z) >= prof.pre_extreme_threshold]
    sign_flips = sum(1 for i in range(1, len(signs)) if signs[i] != signs[i - 1])
    if sign_flips >= 2:
        return True

    if len(pullbacks) >= 3:
        absorbed = sum(1 for p in pullbacks if p.absorbed)
        depths = [p.depth for p in pullbacks]
        depth_range = max(depths) - min(depths)
        mixed_absorption = 0 < absorbed < len(pullbacks)
        no_clean_trend = abs(slope) < prof.leak_slope_threshold
        if mixed_absorption and no_clean_trend and depth_range >= 0.35:
            return True

    _ = direction, bars_in_extreme
    return False


def _classify_state(
    bars_in_extreme: int,
    pullbacks: Sequence[Pullback],
    slope: float,
    acceleration: float,
    z_series: Sequence[Optional[float]],
    direction: str,
    profile: ProfileInput = None,
) -> str:
    prof = get_zone_profile(profile=profile)
    if bars_in_extreme < prof.min_bars_for_diagnosis:
        return "NEUTRAL"

    if _looks_like_disorder(z_series, direction, bars_in_extreme, pullbacks, slope, prof):
        return "DISORDER_FIELD"

    if acceleration >= prof.rupture_acceleration_threshold and slope >= prof.leak_slope_threshold:
        return "RUPTURE"

    if pullbacks and not pullbacks[-1].absorbed and len(pullbacks) >= 2:
        last_depth = pullbacks[-1].depth
        avg_prev = sum(p.depth for p in pullbacks[:-1]) / max(1, len(pullbacks) - 1)
        if last_depth > avg_prev * 1.5 and last_depth > prof.min_pullback_amplitude * 2.5:
            return "RUPTURE"

    if slope >= prof.leak_slope_threshold:
        return "LEAKING"

    n_absorbed = sum(1 for p in pullbacks if p.absorbed)
    if n_absorbed >= 1 or len(pullbacks) == 0:
        return "ACCUMULATING"

    return "NEUTRAL"


def _absorption_factor(state: str, profile: ProfileInput = None) -> float:
    prof = get_zone_profile(profile=profile)
    return {
        "ACCUMULATING": prof.accumulation_factor,
        "PRE_EXTREME": prof.pre_extreme_factor,
        "EARLY_EXTREME": prof.early_extreme_factor,
        "NEUTRAL": prof.neutral_factor,
        "LEAKING": prof.leaking_factor,
        "RUPTURE": prof.rupture_factor,
        "DISORDER_FIELD": prof.disorder_factor,
    }.get(state, prof.neutral_factor)


# ==========================================================================
# CONTEXT TAGS
# ==========================================================================

def _normalize_session(session_phase: Optional[str]) -> Optional[str]:
    if not session_phase:
        return None
    s = str(session_phase).upper().replace(" ", "_").strip()
    aliases = {
        "ASIA": "ASIA",
        "ASIAN": "ASIA",
        "LONDON": "LONDON",
        "LONDON_OPEN": "LONDON_OPEN",
        "PRE_US": "PRE_US",
        "US": "US",
        "NEW_YORK": "US",
    }
    return aliases.get(s, s)


def _build_context_tags(
    state: str,
    zone_level: str,
    prof: ZoneProfile,
    z_current: float,
    timeframe: Optional[int],
    currency: Optional[str],
    session_phase: Optional[str],
    rank_position: Optional[int],
    rank_total: Optional[int],
    rank_duration_bars: Optional[int],
    price_wall: bool,
) -> Tuple[str, ...]:
    tags: List[str] = []

    try:
        tf = int(timeframe) if timeframe is not None else None
    except (TypeError, ValueError):
        tf = None

    # Profile extreme means the profile sees an extreme before the global hard 2.0 line.
    if zone_level == "EXTREME" and abs(z_current) < EXTREME_THRESHOLD:
        tags.append("PROFILE_EXTREME")

    if state in ("PRE_EXTREME", "EARLY_EXTREME", "ACCUMULATING", "LEAKING", "RUPTURE"):
        if state == "EARLY_EXTREME":
            tags.append("EARLY_EXTREME")
        if tf == 1:
            tags.append("LOCAL_ZONE_WORK")
            tags.append("M1_SPECIAL_MICROFILM")
        elif tf in (5, 15) and prof.name == "SHORT":
            tags.append("LOCAL_ZONE_WORK")
            tags.append("M5_M15_INTERMEDIATE_FIELD")
            if tf == 15:
                tags.append("M15_BRIDGE_TF")
        elif tf == 15 and prof.name == "MEDIUM":
            tags.append("SCENARIO_ZONE_WORK")
            tags.append("M15_BRIDGE_TF")
        elif tf in (30, 60):
            tags.append("SCENARIO_ZONE_WORK")
            if tf == 60:
                tags.append("H1_SCENARIO_CURVE")
        elif tf in (240, 1440, 10080):
            tags.append("HTF_ZONE_ANCHOR")

    # Session rank memory: a currency can be neutral in value but extreme in role.
    if rank_position is not None and rank_total is not None:
        try:
            rp = int(rank_position)
            rt = int(rank_total)
            rd = int(rank_duration_bars or 0)
        except (TypeError, ValueError):
            rp = rt = rd = 0
        if rt > 0 and rp >= rt - 1 and rd >= max(3, prof.min_bars_for_diagnosis):
            tags.append("SESSION_RANK_MEMORY")
            tags.append("LOW_RANK_ACCUMULATION")
        if rt > 0 and rp <= 2 and rd >= max(3, prof.min_bars_for_diagnosis):
            tags.append("HIGH_RANK_ACCUMULATION")
        if rd >= max(8, prof.lookback // 2):
            tags.append("SESSION_CARRIED_TENSION")

    session = _normalize_session(session_phase)
    if session in ("LONDON", "LONDON_OPEN") and tags:
        tags.append("LONDON_LIQUIDITY_FORGE")
    if session == "PRE_US" and tags:
        tags.append("PRE_US_ROTATION_WINDOW")

    if price_wall:
        tags.append("PRICE_WALL_FIELD")

    if currency:
        tags.append(f"CURRENCY_{str(currency).upper()}")

    # Stable unique order.
    unique: List[str] = []
    for tag in tags:
        if tag not in unique:
            unique.append(tag)
    return tuple(unique)


def _compute_context_score(tension_score: float, tags: Sequence[str]) -> float:
    if tension_score <= 0:
        return 0.0
    bonus = 0.0
    weighted = {
        "PROFILE_EXTREME": 0.10,
        "EARLY_EXTREME": 0.06,
        "LOCAL_ZONE_WORK": 0.08,
        "M1_SPECIAL_MICROFILM": 0.05,
        "M5_M15_INTERMEDIATE_FIELD": 0.08,
        "M15_BRIDGE_TF": 0.05,
        "SCENARIO_ZONE_WORK": 0.10,
        "H1_SCENARIO_CURVE": 0.10,
        "HTF_ZONE_ANCHOR": 0.15,
        "SESSION_RANK_MEMORY": 0.12,
        "LOW_RANK_ACCUMULATION": 0.12,
        "HIGH_RANK_ACCUMULATION": 0.12,
        "SESSION_CARRIED_TENSION": 0.18,
        "LONDON_LIQUIDITY_FORGE": 0.10,
        "PRE_US_ROTATION_WINDOW": 0.15,
        "PRICE_WALL_FIELD": 0.15,
    }
    for tag in tags:
        bonus += weighted.get(tag, 0.0)
    multiplier = 1.0 + min(0.75, bonus)
    return round(tension_score * multiplier, 3)


# ==========================================================================
# PUBLIC API
# ==========================================================================

def analyze_zone_dynamics(
    z_series: Sequence[Optional[float]],
    timeframe: Optional[int] = None,
    currency: Optional[str] = None,
    session_phase: Optional[str] = None,
    rank_position: Optional[int] = None,
    rank_total: Optional[int] = None,
    rank_duration_bars: Optional[int] = None,
    price_wall: bool = False,
    profile: ProfileInput = None,
) -> ZoneDiagnosis:
    """Analyze the dynamic zone respiration of a Z-score series.

    The old call remains valid. Context parameters are optional and only enrich
    the diagnosis with profile tags and context_score.
    """
    prof = get_zone_profile(timeframe, currency, session_phase, profile)
    series = _as_float_list(z_series)

    if not series:
        return _empty_diagnosis(0.0, "NONE", "Serie vide.", prof, timeframe, currency, session_phase)

    valid = [z for z in series if z is not None]
    if not valid:
        return _empty_diagnosis(0.0, "NONE", "Aucune valeur valide dans la serie.", prof, timeframe, currency, session_phase)

    z_current = valid[-1]
    zone_level = _zone_level_for_z(z_current, prof)
    direction = _detect_extreme_direction(series, prof)
    if direction == "NONE":
        direction = _direction_from_current_z(z_current, prof)

    if direction == "NONE":
        return _finish_diagnosis(
            ZoneDiagnosis(
                state="NEUTRAL",
                bars_in_extreme=0,
                z_current=round(z_current, 4),
                z_extreme_dir="NONE",
                pullbacks=[],
                depth_slope=0.0,
                depth_acceleration=0.0,
                absorption_factor=prof.neutral_factor,
                tension_score=0.0,
                note="Devise hors zone dynamique active.",
                zone_level="NORMAL",
                profile_name=prof.name,
                profile_horizon=prof.horizon,
                timeframe=timeframe,
                currency=currency,
                session_phase=_normalize_session(session_phase),
            ),
            prof,
            z_current,
            timeframe,
            currency,
            session_phase,
            rank_position,
            rank_total,
            rank_duration_bars,
            price_wall,
        )

    bars_in_zone = _count_bars_in_extreme(series, direction, prof)
    if bars_in_zone <= 0:
        bars_in_zone = 1

    # POST_ZONE: the current value has left the influence area, but the recent
    # field can still contain a leaking/rupture event. This avoids erasing the
    # release just because the last bar is already back under the threshold.
    if zone_level == "NORMAL":
        pullbacks = detect_pullbacks(series, direction, prof)
        slope, acceleration = _compute_depth_derivatives(pullbacks, prof)
        state = _classify_state(bars_in_zone, pullbacks, slope, acceleration, series, direction, prof)
        if state in ("RUPTURE", "LEAKING", "DISORDER_FIELD"):
            abs_factor = _absorption_factor(state, prof)
            tension = calculate_tension_score(z_current, bars_in_zone, abs_factor)
            note = _build_note(state, direction, bars_in_zone, pullbacks, slope, acceleration)
            diag = ZoneDiagnosis(
                state=state,
                bars_in_extreme=bars_in_zone,
                z_current=round(z_current, 4),
                z_extreme_dir=direction,
                pullbacks=pullbacks,
                depth_slope=slope,
                depth_acceleration=acceleration,
                absorption_factor=abs_factor,
                tension_score=tension,
                note=note,
                zone_level="POST_ZONE",
                profile_name=prof.name,
                profile_horizon=prof.horizon,
                timeframe=timeframe,
                currency=currency,
                session_phase=_normalize_session(session_phase),
            )
            return _finish_diagnosis(diag, prof, z_current, timeframe, currency, session_phase,
                                     rank_position, rank_total, rank_duration_bars, price_wall)

        return _finish_diagnosis(
            ZoneDiagnosis(
                state="NEUTRAL",
                bars_in_extreme=0,
                z_current=round(z_current, 4),
                z_extreme_dir="NONE",
                pullbacks=[],
                depth_slope=0.0,
                depth_acceleration=0.0,
                absorption_factor=prof.neutral_factor,
                tension_score=0.0,
                note="Devise sortie de zone dynamique sans fuite lisible.",
                zone_level="NORMAL",
                profile_name=prof.name,
                profile_horizon=prof.horizon,
                timeframe=timeframe,
                currency=currency,
                session_phase=_normalize_session(session_phase),
            ),
            prof,
            z_current,
            timeframe,
            currency,
            session_phase,
            rank_position,
            rank_total,
            rank_duration_bars,
            price_wall,
        )

    if bars_in_zone <= 0:
        bars_in_zone = 1

    if zone_level == "PRE_EXTREME":
        abs_factor = _absorption_factor("PRE_EXTREME", prof)
        tension = calculate_tension_score(z_current, bars_in_zone, abs_factor)
        dir_label = "haut" if direction == "HIGH" else "bas"
        diag = ZoneDiagnosis(
            state="PRE_EXTREME",
            bars_in_extreme=bars_in_zone,
            z_current=round(z_current, 4),
            z_extreme_dir=direction,
            pullbacks=[],
            depth_slope=0.0,
            depth_acceleration=0.0,
            absorption_factor=abs_factor,
            tension_score=tension,
            note=(
                f"Pre-extreme {dir_label} actif depuis {bars_in_zone}b - "
                f"tension partielle, approche de bassin dynamique."
            ),
            zone_level="PRE_EXTREME",
            profile_name=prof.name,
            profile_horizon=prof.horizon,
            timeframe=timeframe,
            currency=currency,
            session_phase=_normalize_session(session_phase),
        )
        return _finish_diagnosis(diag, prof, z_current, timeframe, currency, session_phase,
                                 rank_position, rank_total, rank_duration_bars, price_wall)

    pullbacks = detect_pullbacks(series, direction, prof)
    slope, acceleration = _compute_depth_derivatives(pullbacks, prof)
    state = _classify_state(bars_in_zone, pullbacks, slope, acceleration, series, direction, prof)
    if state == "NEUTRAL" and zone_level == "EXTREME" and bars_in_zone > 0:
        state = "EARLY_EXTREME"
    abs_factor = _absorption_factor(state, prof)
    tension = calculate_tension_score(z_current, bars_in_zone, abs_factor)
    note = _build_note(state, direction, bars_in_zone, pullbacks, slope, acceleration)

    diag = ZoneDiagnosis(
        state=state,
        bars_in_extreme=bars_in_zone,
        z_current=round(z_current, 4),
        z_extreme_dir=direction,
        pullbacks=pullbacks,
        depth_slope=slope,
        depth_acceleration=acceleration,
        absorption_factor=abs_factor,
        tension_score=tension,
        note=note,
        zone_level="EXTREME",
        profile_name=prof.name,
        profile_horizon=prof.horizon,
        timeframe=timeframe,
        currency=currency,
        session_phase=_normalize_session(session_phase),
    )
    return _finish_diagnosis(diag, prof, z_current, timeframe, currency, session_phase,
                             rank_position, rank_total, rank_duration_bars, price_wall)


def calculate_tension_score(
    z_current: float,
    bars_in_extreme: int,
    absorption_factor: float = 1.0,
) -> float:
    if bars_in_extreme <= 0:
        return 0.0
    score = abs(float(z_current)) * math.log1p(int(bars_in_extreme)) * float(absorption_factor)
    return round(score, 3)


# ==========================================================================
# FINALIZATION / NOTES
# ==========================================================================

def _empty_diagnosis(
    z_current: float,
    direction: str,
    note: str,
    prof: Optional[ZoneProfile] = None,
    timeframe: Optional[int] = None,
    currency: Optional[str] = None,
    session_phase: Optional[str] = None,
) -> ZoneDiagnosis:
    prof = prof or MEDIUM_PROFILE
    return ZoneDiagnosis(
        state="NEUTRAL",
        bars_in_extreme=0,
        z_current=round(z_current, 4),
        z_extreme_dir=direction,
        pullbacks=[],
        depth_slope=0.0,
        depth_acceleration=0.0,
        absorption_factor=prof.neutral_factor,
        tension_score=0.0,
        note=note,
        zone_level="NORMAL",
        profile_name=prof.name,
        profile_horizon=prof.horizon,
        timeframe=timeframe,
        currency=currency,
        session_phase=_normalize_session(session_phase),
        context_score=0.0,
        contextual_tags=(),
    )


def _finish_diagnosis(
    diag: ZoneDiagnosis,
    prof: ZoneProfile,
    z_current: float,
    timeframe: Optional[int],
    currency: Optional[str],
    session_phase: Optional[str],
    rank_position: Optional[int],
    rank_total: Optional[int],
    rank_duration_bars: Optional[int],
    price_wall: bool,
) -> ZoneDiagnosis:
    tags = _build_context_tags(
        state=diag.state,
        zone_level=diag.zone_level,
        prof=prof,
        z_current=z_current,
        timeframe=timeframe,
        currency=currency,
        session_phase=session_phase,
        rank_position=rank_position,
        rank_total=rank_total,
        rank_duration_bars=rank_duration_bars,
        price_wall=price_wall,
    )
    context_score = _compute_context_score(diag.tension_score, tags)
    note = diag.note
    if tags:
        note = f"{note} Tags: {', '.join(tags)}."
    return replace(diag, contextual_tags=tags, context_score=context_score, note=note)


def _build_note(
    state: str,
    direction: str,
    bars_in_extreme: int,
    pullbacks: Sequence[Pullback],
    slope: float,
    acceleration: float,
) -> str:
    n_pb = len(pullbacks)
    n_abs = sum(1 for p in pullbacks if p.absorbed)
    dir_label = "haut" if direction == "HIGH" else "bas"

    if state == "ACCUMULATING":
        return (f"Zone {dir_label} active depuis {bars_in_extreme}b - "
                f"{n_abs}/{n_pb} pullbacks absorbes, pente {slope:+.3f}. "
                f"Elastique en charge.")
    if state == "LEAKING":
        return (f"Zone {dir_label} en fuite douce depuis {bars_in_extreme}b - "
                f"profondeur des pullbacks augmente (pente {slope:+.3f}).")
    if state == "RUPTURE":
        return (f"Zone {dir_label} en rupture - acceleration {acceleration:+.3f}, "
                f"pente {slope:+.3f}.")
    if state == "EARLY_EXTREME":
        return (f"Zone {dir_label} extreme naissante depuis {bars_in_extreme}b - "
                f"pas encore assez mature pour accumulation/fuite/rupture.")
    if state == "DISORDER_FIELD":
        return (f"Zone {dir_label} en turbulence - activite presente mais grammaire instable, "
                f"pente {slope:+.3f}, acceleration {acceleration:+.3f}.")
    return f"Zone {dir_label}: etat neutre, {bars_in_extreme}b, {n_pb} pullback(s)."


# ==========================================================================
# INTEGRATED TESTS
# ==========================================================================

if __name__ == "__main__":
    print("=" * 84)
    print("PowerFlow V6 - pf_zone_dynamics.py - V0.2 contextual profile tests")
    print("=" * 84)

    def print_diagnosis(label: str, z_series: List[Optional[float]], diag: ZoneDiagnosis) -> None:
        print(f"\n[{label}]")
        print("-" * 84)
        z_str = " ".join(f"{z:+.2f}" if z is not None else " N/A" for z in z_series)
        print(f"  Serie Z            : {z_str}")
        print(f"  State              : {diag.state}")
        print(f"  Zone level         : {diag.zone_level}")
        print(f"  Direction          : {diag.z_extreme_dir}")
        print(f"  Z current          : {diag.z_current:+.3f}")
        print(f"  Bars in zone       : {diag.bars_in_extreme}")
        print(f"  Pullbacks          : {len(diag.pullbacks)} ({sum(1 for p in diag.pullbacks if p.absorbed)} absorbed)")
        print(f"  Slope / accel      : {diag.depth_slope:+.4f} / {diag.depth_acceleration:+.4f}")
        print(f"  Factor             : {diag.absorption_factor:.2f}")
        print(f"  Tension            : {diag.tension_score:.3f}")
        print(f"  Context score      : {diag.context_score:.3f}")
        print(f"  Profile            : {diag.profile_name} / {diag.profile_horizon}")
        print(f"  Tags               : {', '.join(diag.contextual_tags) if diag.contextual_tags else '-'}")
        print(f"  Note               : {diag.note}")

    tests: List[Tuple[str, List[Optional[float]], Dict[str, Any], str]] = [
        ("Neutral", [0.2, -0.5, 0.1, 0.8, -0.3, 0.0, 0.4], {}, "NEUTRAL"),
        ("Pre-extreme EUR M15", [-0.8, -1.1, -1.35, -1.52, -1.68, -1.82, -1.923], {"timeframe": 15, "currency": "EUR"}, "PRE_EXTREME"),
        ("M5 profile extreme before hard 2.0", [-1.2, -1.46, -1.63, -1.80, -1.92], {"timeframe": 5, "currency": "GBP"}, "ACCUMULATING"),
        ("H1 stricter pre-extreme", [-1.2, -1.55, -1.72, -1.88, -1.96], {"timeframe": 60, "currency": "GBP"}, "PRE_EXTREME"),
        ("Accumulating low", [-1.0, -1.6, -2.0, -2.4, -2.3, -1.7, -2.1, -2.4, -2.5, -1.85, -2.45, -2.5], {}, "ACCUMULATING"),
        ("Leaking low", [-1.5, -2.1, -2.5, -2.6, -2.55, -2.15, -2.4, -2.45, -1.75, -2.15, -2.3, -1.2, -2.05], {}, "LEAKING"),
        ("Rupture low", [-1.6, -2.2, -2.5, -2.45, -2.1, -2.35, -2.4, -1.6, -2.2, -2.35, -0.5, -1.0], {}, "RUPTURE"),
        ("Session carried tension", [-1.4, -1.55, -1.70, -1.82, -1.92], {"timeframe": 5, "currency": "GBP", "session_phase": "PRE_US", "rank_position": 8, "rank_total": 8, "rank_duration_bars": 30, "price_wall": True}, "ACCUMULATING"),
        ("Early extreme immature", [0.2, 1.92], {"timeframe": 1, "currency": "GBP"}, "EARLY_EXTREME"),
    ]

    ok = 0
    for label, series, kwargs, expected in tests:
        diag = analyze_zone_dynamics(series, **kwargs)
        print_diagnosis(label, series, diag)
        if diag.state != expected:
            raise AssertionError(f"{label}: expected {expected}, got {diag.state}")
        ok += 1

    print("\n" + "=" * 84)
    print(f"Validation OK: {ok} tests passed.")
    print("=" * 84)
