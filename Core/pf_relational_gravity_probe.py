"""
pf_relational_gravity_probe.py
PowerFlow V6 — Relational Gravity Probe V0.1

Mesure si plusieurs devises avancent ensemble, se rapprochent, s'étirent,
se suivent ou se désynchronisent dans le temps.

RELATIONAL_GRAVITY_STATE =
    same direction + internal distance + gap variation + persistence
    + leader/follower + antagonist context

READ-ONLY — Jamais d'écriture DB.
Aucune dépendance cockpit_* ou telegram_*.
"""

from __future__ import annotations

import sqlite3
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

VERSION = "0.1.1"

ALL_CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]

FORCE_COLUMNS = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
}

# Thresholds
MIN_BARS_REQUIRED = 5
DIRECTION_THRESHOLD = 0.0       # delta > 0 = UP, < 0 = DOWN
DIRECTION_MIN_DELTA = 0.02      # abs(delta) < this → devise trop plate, exclue du groupe
ALIGNMENT_MIN_RATIO = 0.5       # fraction of bars where currency moves with group
# Relative thresholds (slope / mean_distance)
# Typical range: 0.005 to 0.05 on real force_snapshots
COMPRESSION_RELATIVE_THRESHOLD = -0.008   # relative_slope < this = compressing
EXPANSION_RELATIVE_THRESHOLD = 0.008      # relative_slope > this = expanding
DESYNC_ANGLE_THRESHOLD = 30.0             # degrees — deviation triggers desync
LEADER_SPEED_MARGIN = 0.10           # leader must be this much faster than avg
MIN_GROUP_SIZE = 2
SCORE_CONFIDENCE_HIGH = 0.70
SCORE_CONFIDENCE_MEDIUM = 0.40


# ─────────────────────────────────────────────
# DATA CLASSES
# ─────────────────────────────────────────────

@dataclass
class CurrencyMetrics:
    name: str
    forces: list[float]
    force_now: float
    force_start: float
    delta_force: float
    speed: float          # mean absolute bar-to-bar change
    angle_deg: float      # linear regression slope → degrees
    direction: str        # "UP" / "DOWN" / "FLAT"
    persistence: float    # fraction of bars moving in dominant direction


@dataclass
class GravityWindow:
    start: str
    end: str
    bars: int


@dataclass
class RelationalGravityResult:
    status: str                          # OK / PARTIAL / NO_DATA
    version: str
    symbol: str
    timeframe: int
    window: GravityWindow
    primary_state: str
    group: list[str]
    direction: str
    angle_spread_deg: float
    gap_mode: str                        # COMPRESSING / EXPANDING / STABLE / DESYNC / UNKNOWN
    gap_slope: float
    distance_persistence_bars: int
    leader: str
    followers: list[str]
    antagonist: str
    score: float                         # 0.0 → 1.0
    confidence: str                      # HIGH / MEDIUM / LOW
    lab_signatures: list[str]
    interpretation: str
    errors: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────
# DB ACCESS
# ─────────────────────────────────────────────

def _open_readonly(db_path: str) -> sqlite3.Connection:
    uri = f"file:{db_path}?mode=ro"
    return sqlite3.connect(uri, uri=True, check_same_thread=False)


def fetch_force_series(
    db_path: str,
    symbol: str,
    timeframe: int,
    bars: int,
    currencies: list[str],
) -> tuple[dict[str, list[float]], list[str], str, str]:
    """
    Returns:
        series: {currency: [force_values oldest→newest]}
        timestamps: list of created_at strings
        ts_start: oldest timestamp
        ts_end: newest timestamp
    """
    columns = [FORCE_COLUMNS[c] for c in currencies if c in FORCE_COLUMNS]
    if not columns:
        return {}, [], "", ""

    col_str = ", ".join(["created_at"] + columns)
    query = f"""
        SELECT {col_str}
        FROM force_snapshots
        WHERE symbol = ? AND timeframe = ?
        ORDER BY created_at DESC
        LIMIT ?
    """

    try:
        conn = _open_readonly(db_path)
        cur = conn.cursor()
        cur.execute(query, (symbol, timeframe, bars))
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        raise RuntimeError(f"DB read error: {e}")

    if not rows:
        return {}, [], "", ""

    # Reverse to chronological order
    rows = list(reversed(rows))
    timestamps = [r[0] for r in rows]
    ts_start = timestamps[0]
    ts_end = timestamps[-1]

    series: dict[str, list[float]] = {}
    for i, c in enumerate(currencies):
        if c not in FORCE_COLUMNS:
            continue
        col_idx = i + 1  # +1 for created_at
        try:
            vals = [float(r[col_idx]) if r[col_idx] is not None else 0.0 for r in rows]
        except (IndexError, TypeError):
            vals = []
        series[c] = vals

    return series, timestamps, ts_start, ts_end


# ─────────────────────────────────────────────
# MATH HELPERS
# ─────────────────────────────────────────────

def _linear_slope(values: list[float]) -> float:
    """Least-squares slope over index 0..n-1."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    den = sum((i - x_mean) ** 2 for i in range(n))
    if den == 0:
        return 0.0
    return num / den


def _slope_to_angle(slope: float) -> float:
    """Convert slope to degrees via atan."""
    return math.degrees(math.atan(slope))


def _persistence(values: list[float], direction: str) -> float:
    """Fraction of bars where bar-to-bar delta matches dominant direction."""
    deltas = [values[i + 1] - values[i] for i in range(len(values) - 1)]
    if not deltas:
        return 0.0
    if direction == "UP":
        matching = sum(1 for d in deltas if d > 0)
    elif direction == "DOWN":
        matching = sum(1 for d in deltas if d < 0)
    else:
        matching = sum(1 for d in deltas if abs(d) < 0.01)
    return matching / len(deltas)


def _speed(values: list[float]) -> float:
    """Mean absolute bar-to-bar change."""
    deltas = [abs(values[i + 1] - values[i]) for i in range(len(values) - 1)]
    return sum(deltas) / len(deltas) if deltas else 0.0


def _direction(delta: float) -> str:
    if delta > DIRECTION_THRESHOLD:
        return "UP"
    elif delta < -DIRECTION_THRESHOLD:
        return "DOWN"
    return "FLAT"


# ─────────────────────────────────────────────
# CURRENCY METRICS
# ─────────────────────────────────────────────

def compute_currency_metrics(
    name: str, forces: list[float]
) -> Optional[CurrencyMetrics]:
    if len(forces) < MIN_BARS_REQUIRED:
        return None

    force_now = forces[-1]
    force_start = forces[0]
    delta = force_now - force_start
    slope = _linear_slope(forces)
    angle = _slope_to_angle(slope)
    spd = _speed(forces)
    dirn = _direction(delta)
    pers = _persistence(forces, dirn)

    return CurrencyMetrics(
        name=name,
        forces=forces,
        force_now=force_now,
        force_start=force_start,
        delta_force=delta,
        speed=spd,
        angle_deg=angle,
        direction=dirn,
        persistence=pers,
    )


# ─────────────────────────────────────────────
# GROUP DETECTION
# ─────────────────────────────────────────────

def detect_group(
    metrics: dict[str, CurrencyMetrics],
) -> tuple[list[str], str, list[str]]:
    """
    Returns (group_currencies, dominant_direction, antagonist_currencies)
    Group = currencies sharing same direction with highest count.

    V0.1.1: currencies with abs(delta_force) < DIRECTION_MIN_DELTA are excluded
    from up/down candidates — they stay in metrics for debug but don't pollute groups.
    """
    eligible = [
        m for m in metrics.values()
        if abs(m.delta_force) >= DIRECTION_MIN_DELTA
    ]
    flat = [m.name for m in metrics.values() if abs(m.delta_force) < DIRECTION_MIN_DELTA]

    up_currencies = [m.name for m in eligible if m.direction == "UP"]
    down_currencies = [m.name for m in eligible if m.direction == "DOWN"]

    if flat:
        # flat currencies become neither group nor antagonist — absorbed as neutral
        pass

    if len(up_currencies) >= len(down_currencies) and len(up_currencies) >= MIN_GROUP_SIZE:
        return up_currencies, "UP", down_currencies
    elif len(down_currencies) >= MIN_GROUP_SIZE:
        return down_currencies, "DOWN", up_currencies

    # No clear group
    return [], "MIXED", []


# ─────────────────────────────────────────────
# GAP / DISTANCE ANALYSIS
# ─────────────────────────────────────────────

def compute_gap_metrics(
    group: list[str],
    series: dict[str, list[float]],
) -> tuple[float, float, str, int]:
    """
    Returns (gap_slope, angle_spread_deg, gap_mode, distance_persistence_bars)
    gap_slope: how the mean pairwise distance changes over time
    """
    if len(group) < 2:
        return 0.0, 0.0, "UNKNOWN", 0

    # Pairwise distances at each bar
    n_bars = min(len(series[c]) for c in group if c in series)
    if n_bars < 2:
        return 0.0, 0.0, "UNKNOWN", 0

    distances_per_bar: list[float] = []
    for bar_i in range(n_bars):
        vals = [series[c][bar_i] for c in group if c in series]
        if len(vals) < 2:
            distances_per_bar.append(0.0)
            continue
        # Mean absolute pairwise distance
        pairs = []
        for i in range(len(vals)):
            for j in range(i + 1, len(vals)):
                pairs.append(abs(vals[i] - vals[j]))
        distances_per_bar.append(sum(pairs) / len(pairs) if pairs else 0.0)

    gap_slope = _linear_slope(distances_per_bar)

    # Relative slope: normalize by mean distance — scale-invariant
    mean_distance = (
        sum(distances_per_bar) / len(distances_per_bar) if distances_per_bar else 1.0
    )
    relative_slope = gap_slope / mean_distance if mean_distance > 0 else 0.0

    # Angle spread: std of angles across group
    from statistics import stdev, mean
    angles = []
    for c in group:
        if c in series and len(series[c]) >= 2:
            s = _linear_slope(series[c])
            angles.append(_slope_to_angle(s))

    angle_spread = stdev(angles) if len(angles) >= 2 else 0.0

    # Gap mode — relative slope for scale-invariant detection
    if relative_slope < COMPRESSION_RELATIVE_THRESHOLD:
        gap_mode = "COMPRESSING"
    elif relative_slope > EXPANSION_RELATIVE_THRESHOLD:
        gap_mode = "EXPANDING"
    else:
        gap_mode = "STABLE"

    # Check desync: angle spread too large
    if angle_spread > DESYNC_ANGLE_THRESHOLD:
        gap_mode = "DESYNC"

    # Persistence: how many bars distance was shrinking/growing consistently
    if gap_mode == "COMPRESSING":
        persistence_bars = sum(
            1 for i in range(1, len(distances_per_bar))
            if distances_per_bar[i] < distances_per_bar[i - 1]
        )
    elif gap_mode == "EXPANDING":
        persistence_bars = sum(
            1 for i in range(1, len(distances_per_bar))
            if distances_per_bar[i] > distances_per_bar[i - 1]
        )
    else:
        persistence_bars = 0

    return gap_slope, angle_spread, gap_mode, persistence_bars


# ─────────────────────────────────────────────
# LEADER / FOLLOWER DETECTION
# ─────────────────────────────────────────────

def detect_leader_follower(
    group: list[str],
    metrics: dict[str, CurrencyMetrics],
) -> tuple[str, list[str]]:
    """
    Leader = highest speed + angle magnitude in the group.
    Followers = currencies reducing gap toward leader.
    """
    if not group:
        return "UNKNOWN", []

    group_metrics = [metrics[c] for c in group if c in metrics]
    if not group_metrics:
        return "UNKNOWN", []

    # Leader: max composite of speed + abs(delta)
    def leader_score(m: CurrencyMetrics) -> float:
        return m.speed * 0.5 + abs(m.delta_force) * 0.5

    group_metrics.sort(key=leader_score, reverse=True)
    leader = group_metrics[0].name

    avg_score = sum(leader_score(m) for m in group_metrics) / len(group_metrics)
    leader_s = leader_score(group_metrics[0])

    # Followers: others in group where speed < leader but delta moving toward leader level
    followers = []
    for m in group_metrics[1:]:
        # Follower if their delta is positive (catching up) relative to avg
        if leader_s > avg_score * (1 + LEADER_SPEED_MARGIN):
            followers.append(m.name)
        elif abs(m.delta_force) > 0:
            followers.append(m.name)

    return leader, followers


# ─────────────────────────────────────────────
# STATE CLASSIFICATION
# ─────────────────────────────────────────────

def classify_primary_state(
    group: list[str],
    group_direction: str,
    gap_mode: str,
    gap_slope: float,
    angle_spread: float,
    leader: str,
    followers: list[str],
    antagonists: list[str],
) -> tuple[str, list[str]]:
    """
    Returns (primary_state, lab_signatures)
    """
    signatures: list[str] = []

    if not group or len(group) < MIN_GROUP_SIZE:
        return "RELATIONAL_GRAVITY_NOISE", ["RELATIONAL_GRAVITY_NOISE"]

    # Base state from gap mode
    if gap_mode == "COMPRESSING":
        primary = "GRAVITY_COMPRESSION_CLUSTER"
        signatures.append("GRAVITY_COMPRESSION_CLUSTER")
    elif gap_mode == "EXPANDING":
        primary = "GRAVITY_EXPANSION_CLUSTER"
        signatures.append("GRAVITY_EXPANSION_CLUSTER")
    elif gap_mode == "STABLE":
        primary = "POSITIVE_DISTANCE_SYNC"
        signatures.append("POSITIVE_DISTANCE_SYNC")
    elif gap_mode == "DESYNC":
        primary = "DESYNC_TRIGGER"
        signatures.append("DESYNC_TRIGGER")
    else:
        primary = "RELATIONAL_GRAVITY_NOISE"
        signatures.append("RELATIONAL_GRAVITY_NOISE")

    # Leader pulling away
    if leader != "UNKNOWN" and gap_mode == "EXPANDING":
        primary = "LEADER_PULLING_AWAY"
        signatures.append("LEADER_PULLING_AWAY")

    # Follower catch-up
    if followers and gap_mode == "COMPRESSING":
        signatures.append("FOLLOWER_CATCH_UP")

    # Elastic stretch
    if gap_mode == "EXPANDING" and angle_spread > 10.0:
        signatures.append("ELASTIC_DISTANCE_STRETCH")

    # Coalition vs antagonist
    if antagonists and gap_mode in ("EXPANDING", "COMPRESSING"):
        signatures.append("COALITION_VS_ANTAGONIST_EXPANSION")

    # Mirror field: two groups moving in opposite directions symmetrically
    if gap_mode == "STABLE" and antagonists:
        signatures.append("MIRROR_GRAVITY_FIELD")

    # Deduplicate, preserve primary first
    seen = set()
    final_sigs = []
    for s in signatures:
        if s not in seen:
            seen.add(s)
            final_sigs.append(s)

    return primary, final_sigs


# ─────────────────────────────────────────────
# SCORE & CONFIDENCE
# ─────────────────────────────────────────────

def compute_score(
    group: list[str],
    gap_mode: str,
    persistence_bars: int,
    n_bars: int,
    angle_spread: float,
    mean_persistence: float,
) -> tuple[float, str]:
    """
    score 0→1 based on:
    - group size (more = stronger)
    - gap persistence (more consistent = stronger)
    - angle spread (tighter = stronger)
    - mean currency persistence
    """
    if not group:
        return 0.0, "LOW"

    # Group size score
    group_score = min(len(group) / len(ALL_CURRENCIES), 1.0)

    # Persistence score
    pers_score = persistence_bars / max(n_bars - 1, 1)

    # Angle tightness score (lower spread = higher score)
    angle_score = max(0.0, 1.0 - angle_spread / 90.0)

    # Currency persistence score
    curr_pers_score = mean_persistence

    # Gap mode bonus
    mode_bonus = 0.0
    if gap_mode in ("COMPRESSING", "EXPANDING"):
        mode_bonus = 0.15
    elif gap_mode == "STABLE":
        mode_bonus = 0.10

    score = (
        group_score * 0.25
        + pers_score * 0.30
        + angle_score * 0.20
        + curr_pers_score * 0.25
        + mode_bonus
    )
    score = min(score, 1.0)

    if score >= SCORE_CONFIDENCE_HIGH:
        confidence = "HIGH"
    elif score >= SCORE_CONFIDENCE_MEDIUM:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return round(score, 3), confidence


# ─────────────────────────────────────────────
# INTERPRETATION
# ─────────────────────────────────────────────

def build_interpretation(
    primary_state: str,
    group: list[str],
    group_direction: str,
    leader: str,
    followers: list[str],
    antagonists: list[str],
    gap_mode: str,
    confidence: str,
) -> str:
    if not group:
        return "Aucun groupe directionnel détecté. Champ sans gravité relationnelle claire."

    group_str = "/".join(group)
    antag_str = "/".join(antagonists) if antagonists else "aucun"
    follow_str = "/".join(followers) if followers else "aucun"

    direction_label = "haussière" if group_direction == "UP" else "baissière"

    if primary_state == "GRAVITY_COMPRESSION_CLUSTER":
        return (
            f"Cluster {direction_label} : {group_str} se rapprochent. "
            f"Leader : {leader}. Suiveurs : {follow_str}. "
            f"Antagoniste : {antag_str}. Compression active ({confidence})."
        )
    elif primary_state == "GRAVITY_EXPANSION_CLUSTER":
        return (
            f"Groupe {direction_label} en expansion : {group_str} s'écartent. "
            f"{leader} tire en avant. Antagoniste : {antag_str}. "
            f"Étirement actif ({confidence})."
        )
    elif primary_state == "LEADER_PULLING_AWAY":
        return (
            f"{leader} prend de l'avance sur {follow_str} ({direction_label}). "
            f"Antagoniste : {antag_str}. Risque de désynchro si suiveurs ne rattrapent pas ({confidence})."
        )
    elif primary_state == "POSITIVE_DISTANCE_SYNC":
        return (
            f"Groupe {direction_label} {group_str} avancent ensemble à distance stable. "
            f"Gravité cohésive. Leader : {leader}. Antagoniste : {antag_str} ({confidence})."
        )
    elif primary_state == "DESYNC_TRIGGER":
        return (
            f"Désynchronisation détectée dans {group_str}. "
            f"Angles divergents — cohésion en rupture. Attention aux faux groupes ({confidence})."
        )
    elif primary_state == "RELATIONAL_GRAVITY_NOISE":
        return "Signal gravitationnel faible. Pas de groupe cohérent détecté."
    else:
        return f"{primary_state} — groupe {group_str} ({confidence})."


# ─────────────────────────────────────────────
# MAIN PROBE FUNCTION
# ─────────────────────────────────────────────

def run_relational_gravity_probe(
    db_path: str,
    symbol: str,
    timeframe: int,
    bars: int,
    currencies: Optional[list[str]] = None,
) -> RelationalGravityResult:
    """
    Main entry point. Returns RelationalGravityResult.
    READ-ONLY. Never writes DB.
    """
    errors: list[str] = []

    if currencies is None:
        currencies = ALL_CURRENCIES

    # Validate currencies
    valid_currencies = [c for c in currencies if c in FORCE_COLUMNS]
    if len(valid_currencies) < MIN_GROUP_SIZE:
        return _error_result(symbol, timeframe, bars, "NOT_ENOUGH_CURRENCIES", errors)

    # Fetch data
    try:
        series, timestamps, ts_start, ts_end = fetch_force_series(
            db_path, symbol, timeframe, bars, valid_currencies
        )
    except RuntimeError as e:
        errors.append(str(e))
        return _error_result(symbol, timeframe, bars, "DB_ERROR", errors)

    if not series or not timestamps:
        return _error_result(symbol, timeframe, bars, "NO_DATA", errors)

    actual_bars = len(timestamps)
    if actual_bars < MIN_BARS_REQUIRED:
        errors.append(f"Only {actual_bars} bars found, min {MIN_BARS_REQUIRED} required.")
        return _error_result(symbol, timeframe, bars, "INSUFFICIENT_BARS", errors)

    window = GravityWindow(start=ts_start, end=ts_end, bars=actual_bars)

    # Compute per-currency metrics
    metrics: dict[str, CurrencyMetrics] = {}
    for c in valid_currencies:
        if c in series and len(series[c]) >= MIN_BARS_REQUIRED:
            m = compute_currency_metrics(c, series[c])
            if m:
                metrics[c] = m
        else:
            errors.append(f"Insufficient data for {c}")

    if len(metrics) < MIN_GROUP_SIZE:
        return _error_result(symbol, timeframe, actual_bars, "INSUFFICIENT_METRICS", errors)

    # Group detection
    group, group_direction, antagonists = detect_group(metrics)

    if len(group) < MIN_GROUP_SIZE:
        # Partial result: no group
        return RelationalGravityResult(
            status="PARTIAL",
            version=VERSION,
            symbol=symbol,
            timeframe=timeframe,
            window=window,
            primary_state="RELATIONAL_GRAVITY_NOISE",
            group=[],
            direction=group_direction,
            angle_spread_deg=0.0,
            gap_mode="UNKNOWN",
            gap_slope=0.0,
            distance_persistence_bars=0,
            leader="UNKNOWN",
            followers=[],
            antagonist="NONE",
            score=0.0,
            confidence="LOW",
            lab_signatures=["RELATIONAL_GRAVITY_NOISE"],
            interpretation="Aucun groupe directionnel cohérent détecté.",
            errors=errors,
        )

    # Gap metrics
    gap_slope, angle_spread, gap_mode, persistence_bars = compute_gap_metrics(
        group, series
    )

    # Leader / follower
    leader, followers = detect_leader_follower(group, metrics)

    # State classification
    primary_state, lab_signatures = classify_primary_state(
        group=group,
        group_direction=group_direction,
        gap_mode=gap_mode,
        gap_slope=gap_slope,
        angle_spread=angle_spread,
        leader=leader,
        followers=followers,
        antagonists=antagonists,
    )

    # Score
    mean_persistence = (
        sum(metrics[c].persistence for c in group if c in metrics) / len(group)
    )
    score, confidence = compute_score(
        group=group,
        gap_mode=gap_mode,
        persistence_bars=persistence_bars,
        n_bars=actual_bars,
        angle_spread=angle_spread,
        mean_persistence=mean_persistence,
    )

    # Antagonist string
    antagonist_str = "/".join(antagonists) if antagonists else "NONE"

    # Interpretation
    interpretation = build_interpretation(
        primary_state=primary_state,
        group=group,
        group_direction=group_direction,
        leader=leader,
        followers=followers,
        antagonists=antagonists,
        gap_mode=gap_mode,
        confidence=confidence,
    )

    return RelationalGravityResult(
        status="OK",
        version=VERSION,
        symbol=symbol,
        timeframe=timeframe,
        window=window,
        primary_state=primary_state,
        group=group,
        direction=group_direction,
        angle_spread_deg=round(angle_spread, 2),
        gap_mode=gap_mode,
        gap_slope=round(gap_slope, 4),
        distance_persistence_bars=persistence_bars,
        leader=leader,
        followers=followers,
        antagonist=antagonist_str,
        score=score,
        confidence=confidence,
        lab_signatures=lab_signatures,
        interpretation=interpretation,
        errors=errors,
    )


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def _error_result(
    symbol: str, timeframe: int, bars: int, reason: str, errors: list[str]
) -> RelationalGravityResult:
    errors.append(reason)
    return RelationalGravityResult(
        status="NO_DATA",
        version=VERSION,
        symbol=symbol,
        timeframe=timeframe,
        window=GravityWindow(start="", end="", bars=bars),
        primary_state="RELATIONAL_GRAVITY_NOISE",
        group=[],
        direction="UNKNOWN",
        angle_spread_deg=0.0,
        gap_mode="UNKNOWN",
        gap_slope=0.0,
        distance_persistence_bars=0,
        leader="UNKNOWN",
        followers=[],
        antagonist="NONE",
        score=0.0,
        confidence="LOW",
        lab_signatures=["RELATIONAL_GRAVITY_NOISE"],
        interpretation=f"Probe échouée : {reason}",
        errors=errors,
    )


def result_to_dict(r: RelationalGravityResult) -> dict:
    return {
        "status": r.status,
        "version": r.version,
        "symbol": r.symbol,
        "timeframe": r.timeframe,
        "window": {
            "start": r.window.start,
            "end": r.window.end,
            "bars": r.window.bars,
        },
        "primary_state": r.primary_state,
        "group": r.group,
        "direction": r.direction,
        "angle_spread_deg": r.angle_spread_deg,
        "gap_mode": r.gap_mode,
        "gap_slope": r.gap_slope,
        "distance_persistence_bars": r.distance_persistence_bars,
        "leader": r.leader,
        "followers": r.followers,
        "antagonist": r.antagonist,
        "score": r.score,
        "confidence": r.confidence,
        "lab_signatures": r.lab_signatures,
        "interpretation": r.interpretation,
        "errors": r.errors,
    }
