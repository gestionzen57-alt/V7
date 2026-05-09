#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — pf_orchestral_gravity.py V0.2

Read-only module.

Purpose:
    Measure the ORCHESTRAL GRAVITY of a currency field:
    who leads, who follows, who is lagging, who crosses whom,
    and what coalitions are pulling/pushing.

    This is NOT a signal module.
    This is a PERCEPTION module: it reads the living relationships
    between currencies across timeframes and names them.

    Core concepts:
        LEADER      = currency with strongest angle, moving first
        FOLLOWER    = currency moving in same direction, lagging
        ANTAGONIST  = currency moving in opposite direction
        SYNCHRO     = two currencies with nearly identical angles
        LAG         = follower is N bars behind leader (detected by correlation)
        CROSSING    = two currencies approaching each other (force levels converging)
        ATTRACTION  = over time, follower is being pulled toward leader's trajectory

    Orchestral patterns:
        JPY_LEADER_GRAVITY      : JPY high angle, GBP/EUR/CHF converging upward
        USD_CAD_SYNCHRO_DOWN    : USD and CAD descending in coalition
        GBP_EUR_RECOVERY_WAVE   : GBP leads recovery, EUR follows with lag
        ANTAGONIST_CROSSING     : USD rising vs GBP falling, crossing imminent

    Architecture:
        - Read-only (no DB writes)
        - Uses force levels (position) for crossing detection
        - Uses force angles (velocity) for leader/follower detection
        - Uses multi-bar series for lag detection
        - Input: DB + window + timeframes
        - Output: OrchestraState
"""

from __future__ import annotations

import math
import sqlite3
import statistics
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Optional zone dynamics integration
try:
    from pf_zone_dynamics import analyze_zone_dynamics
    ZONE_DYNAMICS_AVAILABLE = True
except ImportError:
    ZONE_DYNAMICS_AVAILABLE = False


CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]

FORCE_COLS = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
}

# Angle thresholds for role classification
LEADER_ANGLE_MIN    = 5.0    # degrees — must be actively moving
SYNCHRO_ANGLE_GAP   = 3.0    # degrees — two currencies are "synchro"
FOLLOWER_ANGLE_MIN  = 1.5    # degrees — weak but same direction
NEUTRAL_ANGLE_MAX   = 2.0    # degrees — not really moving

# Crossing proximity threshold (force units)
CROSSING_PROXIMITY  = 8.0    # currencies this close are "crossing territory"
CROSSING_IMMINENT   = 4.0    # currencies this close are about to cross

# Lag detection: how many bars correlation window
LAG_WINDOW          = 5

# Attraction threshold: if follower angle is > this fraction of leader angle
ATTRACTION_RATIO    = 0.35

# Z-score lookback for zone dynamics
ZONE_LOOKBACK = 20


# ==========================================================================
# DATA STRUCTURES
# ==========================================================================

@dataclass
class ZoneQuality:
    """Zone behavioral quality from pf_zone_dynamics."""
    state: str           # ACCUMULATING / LEAKING / RUPTURE / PRE_EXTREME / NEUTRAL / EARLY_EXTREME
    zone_level: str      # EXTREME / PRE_EXTREME / NORMAL
    tension_score: float # 0.0 to ~15.0
    z_current: float     # current z-score
    z_direction: str     # HIGH / LOW / NONE
    available: bool      # False if zone_dynamics not installed

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "zone_level": self.zone_level,
            "tension_score": round(self.tension_score, 3),
            "z_current": round(self.z_current, 3),
            "z_direction": self.z_direction,
            "available": self.available,
        }


@dataclass
class CurrencyRole:
    """Role of one currency in the orchestral field at one moment."""
    currency: str
    force_level: float          # absolute force (0-100)
    avg_angle: float            # average angle over recent bars
    role: str                   # LEADER / FOLLOWER / ANTAGONIST / NEUTRAL / LAGGING
    direction: str              # UP / DOWN / FLAT
    attraction_to: Optional[str]    # which leader is pulling this currency
    attraction_strength: float  # 0.0 to 1.0
    lag_bars: int               # estimated lag vs leader (0 = synchronous)
    zone_quality: Optional["ZoneQuality"] = None  # zone behavioral context

    def to_dict(self) -> dict:
        return {
            "currency": self.currency,
            "force_level": self.force_level,
            "avg_angle": self.avg_angle,
            "role": self.role,
            "direction": self.direction,
            "attraction_to": self.attraction_to,
            "attraction_strength": round(self.attraction_strength, 3),
            "lag_bars": self.lag_bars,
            "zone_quality": self.zone_quality.to_dict() if self.zone_quality else None,
        }


@dataclass
class CrossingEvent:
    """Two currencies converging or crossing."""
    currency_a: str
    currency_b: str
    timestamp: str
    force_a: float
    force_b: float
    distance: float             # |force_a - force_b|
    crossing_type: str          # CROSSING_IMMINENT / CROSSING_ZONE / POST_CROSS
    direction_a: str            # UP / DOWN
    direction_b: str            # UP / DOWN
    converging: bool            # True if they are approaching each other

    def to_dict(self) -> dict:
        return {
            "currency_a": self.currency_a,
            "currency_b": self.currency_b,
            "timestamp": self.timestamp,
            "force_a": self.force_a,
            "force_b": self.force_b,
            "distance": round(self.distance, 2),
            "crossing_type": self.crossing_type,
            "direction_a": self.direction_a,
            "direction_b": self.direction_b,
            "converging": self.converging,
        }


@dataclass
class CoalitionGroup:
    """A group of currencies moving together."""
    members: List[str]
    direction: str              # UP / DOWN
    cohesion: float             # 0.0 to 1.0 (how similar the angles are)
    avg_angle: float
    coalition_type: str         # STRONG_SYNCHRO / LOOSE_ALLIANCE / POLARIZED_FIELD

    def to_dict(self) -> dict:
        return {
            "members": self.members,
            "direction": self.direction,
            "cohesion": round(self.cohesion, 3),
            "avg_angle": round(self.avg_angle, 2),
            "coalition_type": self.coalition_type,
        }


@dataclass
class OrchestraState:
    """Complete orchestral state for one TF at one moment in time."""
    timeframe: int
    timestamp: str

    # Roles
    roles: Dict[str, CurrencyRole] = field(default_factory=dict)

    # Leaders (sorted by angle strength)
    leaders: List[str] = field(default_factory=list)
    antagonists: List[str] = field(default_factory=list)
    followers: List[str] = field(default_factory=list)
    neutral: List[str] = field(default_factory=list)

    # Coalitions
    up_coalition: Optional[CoalitionGroup] = None
    down_coalition: Optional[CoalitionGroup] = None

    # Crossings (at this moment)
    crossings: List[CrossingEvent] = field(default_factory=list)

    # Named patterns
    patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "leaders": self.leaders,
            "antagonists": self.antagonists,
            "followers": self.followers,
            "neutral": self.neutral,
            "roles": {c: r.to_dict() for c, r in self.roles.items()},
            "up_coalition": self.up_coalition.to_dict() if self.up_coalition else None,
            "down_coalition": self.down_coalition.to_dict() if self.down_coalition else None,
            "crossings": [x.to_dict() for x in self.crossings],
            "patterns": self.patterns,
        }


# ==========================================================================
# DB ACCESS
# ==========================================================================

def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _load_rows(db_path: str, symbol: str, tf: int, start: str, end: str) -> List[dict]:
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cols = ["created_at", "bid"] + list(FORCE_COLS.values())
    cur.execute(
        f"SELECT {', '.join(cols)} FROM force_snapshots "
        "WHERE symbol = ? AND timeframe = ? AND created_at >= ? AND created_at <= ? "
        "ORDER BY created_at ASC",
        (symbol, tf, start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


# ==========================================================================
# Z-SCORE AND ZONE QUALITY
# ==========================================================================

def _compute_zscore_series(forces: List[float], lookback: int = ZONE_LOOKBACK) -> List[Optional[float]]:
    """Rolling z-score from raw force series."""
    result: List[Optional[float]] = []
    for i in range(len(forces)):
        window = forces[max(0, i - lookback): i + 1]
        if len(window) < 3:
            result.append(None)
            continue
        m = statistics.mean(window)
        s = statistics.stdev(window)
        result.append((forces[i] - m) / s if s > 1e-6 else 0.0)
    return result


def _compute_zone_qualities(
    db_path: str,
    symbol: str,
    timeframe: int,
    start: str,
    end: str,
    lookback: int = ZONE_LOOKBACK,
    currencies: Optional[List[str]] = None,
) -> Dict[str, ZoneQuality]:
    """
    Compute ZoneQuality per currency using pf_zone_dynamics.
    Returns empty dict if zone_dynamics unavailable.
    """
    if not ZONE_DYNAMICS_AVAILABLE:
        return {}

    targets = currencies or CURRENCIES

    # Load a wider window to compute meaningful z-scores
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cols = ["created_at"] + list(FORCE_COLS.values())
    cur.execute(
        f"SELECT {', '.join(cols)} FROM force_snapshots "
        "WHERE symbol = ? AND timeframe = ? AND created_at <= ? "
        f"ORDER BY created_at DESC LIMIT {lookback * 3}",
        (symbol, timeframe, end),
    )
    raw_rows = list(reversed(cur.fetchall()))
    con.close()

    if len(raw_rows) < 5:
        return {}

    # Build force series per currency
    force_series: Dict[str, List[float]] = {c: [] for c in targets}
    for r in raw_rows:
        for c in targets:
            col = FORCE_COLS.get(c)
            if col:
                v = r[col]
                if v is not None:
                    force_series[c].append(float(v))

    result: Dict[str, ZoneQuality] = {}
    for c in targets:
        series = force_series.get(c, [])
        if len(series) < 5:
            result[c] = ZoneQuality(
                state="NEUTRAL", zone_level="NORMAL",
                tension_score=0.0, z_current=0.0,
                z_direction="NONE", available=False
            )
            continue

        z_series_list = _compute_zscore_series(series, lookback)
        z_valid = [z for z in z_series_list if z is not None]

        if not z_valid:
            result[c] = ZoneQuality(
                state="NEUTRAL", zone_level="NORMAL",
                tension_score=0.0, z_current=0.0,
                z_direction="NONE", available=True
            )
            continue

        try:
            diag = analyze_zone_dynamics(
                z_valid,
                timeframe=timeframe,
                currency=c,
            )
            z_curr = z_valid[-1]
            z_dir = "HIGH" if z_curr >= 1.5 else ("LOW" if z_curr <= -1.5 else "NONE")
            result[c] = ZoneQuality(
                state=diag.state,
                zone_level=diag.zone_level,
                tension_score=diag.tension_score,
                z_current=round(z_curr, 3),
                z_direction=z_dir,
                available=True,
            )
        except Exception:
            result[c] = ZoneQuality(
                state="NEUTRAL", zone_level="NORMAL",
                tension_score=0.0, z_current=0.0,
                z_direction="NONE", available=True
            )

    return result


# ==========================================================================
# ANGLE COMPUTATION
# ==========================================================================

def _compute_angles_for_rows(rows: List[dict]) -> List[Tuple[str, Dict[str, float], Dict[str, float]]]:
    """
    Returns list of (timestamp, {currency: force_level}, {currency: angle_deg}).
    """
    if len(rows) < 2:
        return []

    result = []
    for a, b in zip(rows, rows[1:]):
        ts_a = _parse_dt(str(a["created_at"]))
        ts_b = _parse_dt(str(b["created_at"]))
        seconds = (ts_b - ts_a).total_seconds()
        if seconds <= 0:
            continue
        minutes = seconds / 60.0

        angles: Dict[str, float] = {}
        forces: Dict[str, float] = {}

        for c, col in FORCE_COLS.items():
            va = _safe_float(a.get(col))
            vb = _safe_float(b.get(col))
            if va is None or vb is None:
                continue
            velocity = (vb - va) / minutes
            angles[c] = round(math.degrees(math.atan(velocity)), 2)
            forces[c] = round(vb, 2)

        result.append((str(b["created_at"]), forces, angles))

    return result


# ==========================================================================
# ROLE CLASSIFICATION
# ==========================================================================

def _classify_roles(
    forces: Dict[str, float],
    avg_angles: Dict[str, float],
    zone_qualities: Optional[Dict[str, "ZoneQuality"]] = None,
) -> Dict[str, CurrencyRole]:
    """
    Classify each currency's role based on angle + zone quality.
    Leader = strongest angle.
    Zone tension amplifies/confirms attraction_strength.
    """
    if not avg_angles:
        return {}

    roles: Dict[str, CurrencyRole] = {}

    # Find strongest upward angle
    up_currencies = [(c, a) for c, a in avg_angles.items() if a >= LEADER_ANGLE_MIN]
    down_currencies = [(c, a) for c, a in avg_angles.items() if a <= -LEADER_ANGLE_MIN]

    up_currencies.sort(key=lambda x: x[1], reverse=True)
    down_currencies.sort(key=lambda x: x[1])

    # Primary leader (strongest up)
    primary_leader_up = up_currencies[0][0] if up_currencies else None
    primary_leader_down = down_currencies[0][0] if down_currencies else None

    for c, angle in avg_angles.items():
        force_level = forces.get(c, 50.0)

        if angle >= LEADER_ANGLE_MIN:
            direction = "UP"
            if c == primary_leader_up:
                role = "LEADER"
                attraction_to = None
                attraction_strength = 0.0
                lag_bars = 0
            else:
                # Follower or synchro with leader
                leader_angle = up_currencies[0][1] if up_currencies else 1.0
                ratio = angle / leader_angle if leader_angle != 0 else 0.0
                # Zone tension boosts attraction_strength
                zone_boost = 0.0
                if zone_qualities and c in zone_qualities:
                    zq = zone_qualities[c]
                    zone_boost = min(zq.tension_score / 10.0, 0.3)
                if ratio >= ATTRACTION_RATIO:
                    role = "FOLLOWER"
                    attraction_to = primary_leader_up
                    attraction_strength = min(ratio + zone_boost, 1.0)
                    lag_bars = 0  # Will be computed separately
                else:
                    role = "LAGGING"
                    attraction_to = primary_leader_up
                    attraction_strength = min(ratio + zone_boost * 0.5, 1.0)
                    lag_bars = 2

        elif angle <= -LEADER_ANGLE_MIN:
            direction = "DOWN"
            if c == primary_leader_down:
                role = "LEADER"
                attraction_to = None
                attraction_strength = 0.0
                lag_bars = 0
            else:
                leader_angle = down_currencies[0][1] if down_currencies else -1.0
                ratio = angle / leader_angle if leader_angle != 0 else 0.0
                zone_boost = 0.0
                if zone_qualities and c in zone_qualities:
                    zq = zone_qualities[c]
                    zone_boost = min(zq.tension_score / 10.0, 0.3)
                if ratio >= ATTRACTION_RATIO:
                    role = "FOLLOWER"
                    attraction_to = primary_leader_down
                    attraction_strength = min(ratio + zone_boost, 1.0)
                    lag_bars = 0
                else:
                    role = "LAGGING"
                    attraction_to = primary_leader_down
                    attraction_strength = min(ratio + zone_boost * 0.5, 1.0)
                    lag_bars = 2

            # Check if this down-currency is antagonist to up-leader
            if primary_leader_up:
                role = "ANTAGONIST"
                attraction_to = None
                attraction_strength = 0.0
                lag_bars = 0

        else:
            direction = "FLAT"
            role = "NEUTRAL"
            attraction_to = None
            attraction_strength = 0.0
            lag_bars = 0

        zq = zone_qualities.get(c) if zone_qualities else None
        roles[c] = CurrencyRole(
            currency=c,
            force_level=force_level,
            avg_angle=angle,
            role=role,
            direction=direction,
            attraction_to=attraction_to,
            attraction_strength=attraction_strength,
            lag_bars=lag_bars,
            zone_quality=zq,
        )

    return roles


def _build_coalition(
    currencies_with_angles: List[Tuple[str, float]],
    direction: str,
) -> Optional[CoalitionGroup]:
    """Build a coalition group if at least 2 currencies share direction."""
    if len(currencies_with_angles) < 2:
        return None

    angles = [a for _, a in currencies_with_angles]
    avg = sum(angles) / len(angles)

    # Cohesion = 1 - (std_dev / |avg|)
    variance = sum((a - avg) ** 2 for a in angles) / len(angles)
    std = math.sqrt(variance)
    cohesion = max(0.0, 1.0 - std / (abs(avg) + 1e-6))

    # Coalition type
    if cohesion >= 0.85:
        ctype = "STRONG_SYNCHRO"
    elif cohesion >= 0.60:
        ctype = "LOOSE_ALLIANCE"
    else:
        ctype = "POLARIZED_FIELD"

    return CoalitionGroup(
        members=[c for c, _ in currencies_with_angles],
        direction=direction,
        cohesion=cohesion,
        avg_angle=round(avg, 2),
        coalition_type=ctype,
    )


def _detect_crossings(
    forces: Dict[str, float],
    avg_angles: Dict[str, float],
    timestamp: str,
) -> List[CrossingEvent]:
    """Detect pairs of currencies converging or in crossing territory."""
    events = []
    currencies = list(forces.keys())

    for i, c1 in enumerate(currencies):
        for c2 in currencies[i+1:]:
            f1 = forces.get(c1)
            f2 = forces.get(c2)
            a1 = avg_angles.get(c1, 0.0)
            a2 = avg_angles.get(c2, 0.0)

            if f1 is None or f2 is None:
                continue

            distance = abs(f1 - f2)

            # Are they converging? (moving toward each other)
            if f1 > f2:
                converging = a1 < 0 and a2 > 0  # c1 going down, c2 going up
            else:
                converging = a1 > 0 and a2 < 0  # c1 going up, c2 going down

            if distance <= CROSSING_IMMINENT:
                ctype = "CROSSING_IMMINENT"
            elif distance <= CROSSING_PROXIMITY:
                ctype = "CROSSING_ZONE"
            else:
                continue  # too far, skip

            d1 = "UP" if a1 > 0 else ("DOWN" if a1 < 0 else "FLAT")
            d2 = "UP" if a2 > 0 else ("DOWN" if a2 < 0 else "FLAT")

            events.append(CrossingEvent(
                currency_a=c1,
                currency_b=c2,
                timestamp=timestamp,
                force_a=round(f1, 2),
                force_b=round(f2, 2),
                distance=round(distance, 2),
                crossing_type=ctype,
                direction_a=d1,
                direction_b=d2,
                converging=converging,
            ))

    return events


def _detect_patterns(
    roles: Dict[str, CurrencyRole],
    coalitions_up: Optional[CoalitionGroup],
    coalitions_down: Optional[CoalitionGroup],
    crossings: List[CrossingEvent],
) -> List[str]:
    """Name known orchestral patterns."""
    patterns = []

    leaders = [c for c, r in roles.items() if r.role == "LEADER"]
    antagonists = [c for c, r in roles.items() if r.role == "ANTAGONIST"]
    followers = [c for c, r in roles.items() if r.role == "FOLLOWER"]

    # JPY leading others upward
    if "JPY" in leaders:
        jpy_angle = roles["JPY"].avg_angle
        pulled = [c for c in followers if roles[c].direction == "UP"]
        if len(pulled) >= 2:
            patterns.append(f"JPY_GRAVITY_PULLING_{'_'.join(pulled)}")
        # Zone quality check: JPY in ACCUMULATING = gravity confirmed
        jpy_zq = roles["JPY"].zone_quality
        if jpy_zq and jpy_zq.state in ("ACCUMULATING", "EARLY_EXTREME"):
            patterns.append("JPY_LEADER_ZONE_CONFIRMED")

    # Leader in ACCUMULATING zone = most reliable
    for c in leaders:
        zq = roles[c].zone_quality
        if zq and zq.state == "ACCUMULATING":
            patterns.append(f"LEADER_{c}_ACCUMULATING_ZONE")
        elif zq and zq.state == "RUPTURE":
            patterns.append(f"LEADER_{c}_RUPTURE_BREAKOUT")

    # Antagonist in RUPTURE = breaking out hard
    for c in antagonists:
        zq = roles[c].zone_quality
        if zq and zq.state == "RUPTURE":
            patterns.append(f"ANTAGONIST_{c}_RUPTURE")

    # GBP recovery lead
    if "GBP" in leaders and roles["GBP"].avg_angle > 8.0:
        if "EUR" in followers:
            patterns.append("GBP_EUR_RECOVERY_WAVE")

    # USD/CAD synchro coalition
    if coalitions_down and "USD" in coalitions_down.members and "CAD" in coalitions_down.members:
        if coalitions_down.cohesion >= 0.70:
            patterns.append("USD_CAD_SYNCHRO_DOWN_COALITION")

    if coalitions_up and "USD" in coalitions_up.members and "CAD" in coalitions_up.members:
        if coalitions_up.cohesion >= 0.70:
            patterns.append("USD_CAD_SYNCHRO_UP_COALITION")

    # Crossing pattern
    imminent = [x for x in crossings if x.crossing_type == "CROSSING_IMMINENT" and x.converging]
    for cross in imminent:
        patterns.append(
            f"CROSSING_IMMINENT_{cross.currency_a}_{cross.currency_b}"
        )

    # Bipolar field (strong up vs strong down)
    if leaders and antagonists:
        if len(leaders) >= 2 or len(antagonists) >= 2:
            patterns.append("BIPOLAR_FIELD_ACTIVE")

    # Compression: all currencies clustered (neutral zone)
    neutral_count = sum(1 for r in roles.values() if r.role == "NEUTRAL")
    if neutral_count >= 5:
        patterns.append("ORCHESTRAL_COMPRESSION")

    return patterns


# ==========================================================================
# MAIN ANALYSIS
# ==========================================================================

def compute_orchestra_state(
    db_path: str,
    symbol: str,
    timeframe: int,
    start: str,
    end: str,
    avg_bars: int = 3,
) -> Optional[OrchestraState]:
    """
    Compute the orchestral state for one TF over the given window.

    avg_bars: how many bars to average for role classification.
    Uses the LAST avg_bars segments.
    """
    rows = _load_rows(db_path, symbol, timeframe, start, end)
    if len(rows) < avg_bars + 2:
        return None

    computed = _compute_angles_for_rows(rows)
    if len(computed) < avg_bars:
        return None

    # Use last avg_bars segments for average
    recent = computed[-avg_bars:]
    last_ts = recent[-1][0]

    # Average forces and angles over recent bars
    avg_forces: Dict[str, List[float]] = {c: [] for c in CURRENCIES}
    avg_angles_map: Dict[str, List[float]] = {c: [] for c in CURRENCIES}

    for ts, forces, angles in recent:
        for c in CURRENCIES:
            if c in forces:
                avg_forces[c].append(forces[c])
            if c in angles:
                avg_angles_map[c].append(angles[c])

    forces_avg = {
        c: round(sum(v) / len(v), 2)
        for c, v in avg_forces.items() if v
    }
    angles_avg = {
        c: round(sum(v) / len(v), 2)
        for c, v in avg_angles_map.items() if v
    }

    # Compute zone qualities (uses pf_zone_dynamics if available)
    zone_qualities = _compute_zone_qualities(
        db_path, symbol, timeframe, start, end
    )

    # Classify roles (with zone context)
    roles = _classify_roles(forces_avg, angles_avg, zone_qualities)

    # Sort into lists
    leaders_list = sorted(
        [c for c, r in roles.items() if r.role == "LEADER"],
        key=lambda c: abs(roles[c].avg_angle), reverse=True
    )
    antagonists_list = sorted(
        [c for c, r in roles.items() if r.role == "ANTAGONIST"],
        key=lambda c: abs(roles[c].avg_angle), reverse=True
    )
    followers_list = [c for c, r in roles.items() if r.role in ("FOLLOWER", "LAGGING")]
    neutral_list   = [c for c, r in roles.items() if r.role == "NEUTRAL"]

    # Build coalitions
    up_items   = [(c, r.avg_angle) for c, r in roles.items() if r.direction == "UP"]
    down_items = [(c, r.avg_angle) for c, r in roles.items() if r.direction == "DOWN"]
    up_coal   = _build_coalition(up_items, "UP")
    down_coal = _build_coalition(down_items, "DOWN")

    # Detect crossings
    crossings = _detect_crossings(forces_avg, angles_avg, last_ts)

    # Name patterns
    patterns = _detect_patterns(roles, up_coal, down_coal, crossings)

    return OrchestraState(
        timeframe=timeframe,
        timestamp=last_ts,
        roles=roles,
        leaders=leaders_list,
        antagonists=antagonists_list,
        followers=followers_list,
        neutral=neutral_list,
        up_coalition=up_coal,
        down_coalition=down_coal,
        crossings=crossings,
        patterns=patterns,
    )


def compute_orchestra_multi_tf(
    db_path: str,
    symbol: str,
    timeframes: List[int],
    start: str,
    end: str,
    avg_bars: int = 3,
) -> Dict[int, Optional[OrchestraState]]:
    """Run orchestral analysis over multiple timeframes."""
    return {
        tf: compute_orchestra_state(db_path, symbol, tf, start, end, avg_bars)
        for tf in timeframes
    }


def orchestra_markdown_report(
    states: Dict[int, Optional[OrchestraState]],
    symbol: str,
    start: str,
    end: str,
) -> str:
    """Format orchestral states as readable markdown."""
    lines = [
        "# ORCHESTRAL GRAVITY REPORT",
        "",
        f"**Symbol:** {symbol}",
        f"**Window:** {start} → {end}",
        "",
    ]

    tf_labels = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4"}

    for tf in sorted(states.keys()):
        state = states[tf]
        label = tf_labels.get(tf, f"TF{tf}")
        lines.append(f"## {label}")
        lines.append("")

        if state is None:
            lines.append("*Insufficient data.*")
            lines.append("")
            continue

        lines.append(f"**As of:** {state.timestamp[-14:-6]}")
        lines.append("")

        def _fmt_role(c: str) -> str:
            r = state.roles[c]
            zq = r.zone_quality
            zone_str = ""
            if zq and zq.available:
                zone_str = f" [{zq.state} z={zq.z_current:+.2f} t={zq.tension_score:.1f}]"
            return f"{c} ({r.avg_angle:+.1f}°{zone_str})"

        if state.leaders:
            lines.append(f"**LEADERS:** {', '.join(_fmt_role(c) for c in state.leaders)}")

        if state.antagonists:
            lines.append(f"**ANTAGONISTS:** {', '.join(_fmt_role(c) for c in state.antagonists)}")

        if state.followers:
            fol_str = ", ".join(
                f"{c} ({state.roles[c].avg_angle:+.1f}°, attr={state.roles[c].attraction_strength:.2f})"
                for c in state.followers
            )
            lines.append(f"**FOLLOWERS:** {fol_str}")

        if state.neutral:
            lines.append(f"**NEUTRAL:** {', '.join(state.neutral)}")

        if state.up_coalition:
            coa = state.up_coalition
            lines.append(
                f"**UP COALITION:** {'+'.join(coa.members)} "
                f"[{coa.coalition_type}, cohesion={coa.cohesion:.2f}]"
            )

        if state.down_coalition:
            coa = state.down_coalition
            lines.append(
                f"**DOWN COALITION:** {'+'.join(coa.members)} "
                f"[{coa.coalition_type}, cohesion={coa.cohesion:.2f}]"
            )

        if state.crossings:
            for x in state.crossings:
                conv = "→ CONVERGING" if x.converging else ""
                lines.append(
                    f"**CROSSING:** {x.currency_a}({x.force_a}) ↔ "
                    f"{x.currency_b}({x.force_b}) "
                    f"[dist={x.distance}, {x.crossing_type}] {conv}"
                )

        if state.patterns:
            lines.append(f"**PATTERNS:** {', '.join(state.patterns)}")

        lines.append("")

    return "\n".join(lines)
