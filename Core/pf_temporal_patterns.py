"""
PowerFlow V6 - pf_temporal_patterns.py
Version: V0.1

Mission:
  Detecteurs de patterns temporels avances.

Architecture:
  pf_* = moteur pur.
  Ce module ne lit pas la DB.
  Ce module n'ecrit jamais en DB.
  Ce module ne depend pas du Cockpit.

Detections:
  - temporal_density
  - detect_angular_alignment
  - extreme_zone_breathing

Doctrine:
  Mesurer la compression du temps, les pullures internes,
  et les changements d'intention synchronises.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Tuple, Any


MIN_ALIGNED_DEVISES = 3
DEFAULT_ANGLE_LOOKBACK_BARS = 2
EPSILON = 1e-12


def _normalize_devise(devise: str) -> str:
    return str(devise).strip().upper()


def _resolve_col_index(devise: str, devise_cols: Sequence[Tuple[str, str]]) -> int:
    """
    Resolve l'index de colonne d'une devise dans rows.

    Formats acceptes pour devise_cols:
      1) [("GBP", "3"), ("USD", "4")]           -> index direct en string
      2) [("GBP", 3), ("USD", 4)]               -> index direct en int
      3) [("GBP", "force_gbp"), ...]            -> ordre de devise_cols = ordre des forces
      4) [("force_gbp", "GBP"), ...]            -> tolere inversion

    Si aucun index numerique n'est fourni, on utilise la position dans devise_cols.
    Cela permet un usage simple avec rows contenant uniquement les forces:
      rows = [(gbp, usd, eur, ...)]
      devise_cols = [("GBP", "force_gbp"), ("USD", "force_usd"), ...]
    """
    target = _normalize_devise(devise)

    for idx, pair in enumerate(devise_cols):
        if len(pair) < 2:
            continue
        a = str(pair[0]).strip()
        b = str(pair[1]).strip()
        a_u = _normalize_devise(a.replace("force_", ""))
        b_u = _normalize_devise(b.replace("force_", ""))

        if a_u == target or b_u == target:
            try:
                return int(b)
            except (TypeError, ValueError):
                pass
            try:
                return int(a)
            except (TypeError, ValueError):
                pass
            return idx

    raise KeyError(f"Devise not found in devise_cols: {devise}")


def _value_at(
    rows: Sequence[Tuple[Any, ...]],
    bar_index: int,
    devise: str,
    devise_cols: Sequence[Tuple[str, str]],
) -> float:
    col_index = _resolve_col_index(devise, devise_cols)
    return float(rows[bar_index][col_index])


def _bar_time(rows: Sequence[Tuple[Any, ...]], bar_index: int) -> str:
    if not rows:
        return ""
    row = rows[bar_index]
    if not row:
        return str(bar_index)
    first = row[0]
    if isinstance(first, (int, float)):
        return str(bar_index)
    return str(first)


def _safe_window_start(bar_index: int, window: int) -> int:
    if window <= 0:
        raise ValueError("window must be > 0")
    if bar_index < 0:
        raise ValueError("bar_index must be >= 0")
    return max(0, bar_index - window)


def _angle_from_delta(delta: float, bars: int = 1) -> float:
    bars = max(1, int(bars))
    slope = delta / bars
    return math.degrees(math.atan(slope))


def _stdev(values: Sequence[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean = sum(values) / len(values)
    variance = sum((v - mean) ** 2 for v in values) / len(values)
    return math.sqrt(variance)


def temporal_density(
    devise: str,
    rows: Sequence[Tuple[Any, ...]],
    bar_index: int,
    window: int,
    devise_cols: Sequence[Tuple[str, str]],
) -> float:
    """
    Mesure la densite de mouvement par barre.

    densite = sum(abs(delta_force)) / effective_window

    Lecture PowerFlow:
      densite haute = temps compresse / mouvement condense
      densite basse = temps etire / champ mou

    Note:
      effective_window = nombre reel de deltas disponibles.
      Cela evite de sous-estimer les premieres barres.
    """
    if not rows:
        return 0.0
    if bar_index <= 0:
        return 0.0
    if bar_index >= len(rows):
        raise IndexError("bar_index out of range")

    start = _safe_window_start(bar_index, window)
    deltas: List[float] = []

    prev = _value_at(rows, start, devise, devise_cols)
    for i in range(start + 1, bar_index + 1):
        current = _value_at(rows, i, devise, devise_cols)
        deltas.append(abs(current - prev))
        prev = current

    if not deltas:
        return 0.0

    return sum(deltas) / len(deltas)


def detect_angular_alignment(
    devises: List[str],
    rows: Sequence[Tuple[Any, ...]],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    angle_tolerance: float = 3.0,
) -> Optional[Dict[str, Any]]:
    """
    Detecte quand plusieurs devises changent de direction simultanement
    avec un angle proche.

    Retourne:
      {
        'aligned_devises': ['EUR', 'GBP', 'USD'],
        'common_angle': 45.2,
        'alignment_quality': 0.95,
        'bar_time': '2026-04-30 17:30',
        'tf': 15,
        'direction_changed_count': 3,
      }

    Logique:
      - calcule l'angle actuel sur DEFAULT_ANGLE_LOOKBACK_BARS
      - mesure si la pente precedente change de signe
      - groupe les devises dont l'angle est dans +/- angle_tolerance
      - retourne seulement si au moins 3 devises convergent
    """
    if not rows or not devises:
        return None
    if bar_index >= len(rows):
        raise IndexError("bar_index out of range")
    if angle_tolerance <= 0:
        raise ValueError("angle_tolerance must be > 0")

    lookback = DEFAULT_ANGLE_LOOKBACK_BARS
    min_required = min(MIN_ALIGNED_DEVISES, len(devises))
    if min_required < 2:
        return None

    if bar_index - lookback < 0:
        return None

    candidates: List[Dict[str, Any]] = []
    for devise in devises:
        d = _normalize_devise(devise)
        try:
            current = _value_at(rows, bar_index, d, devise_cols)
            previous = _value_at(rows, bar_index - lookback, d, devise_cols)
        except (KeyError, IndexError, ValueError):
            continue

        current_delta = current - previous
        current_angle = _angle_from_delta(current_delta, lookback)

        direction_changed = False
        if bar_index - (2 * lookback) >= 0:
            before = _value_at(rows, bar_index - (2 * lookback), d, devise_cols)
            previous_delta = previous - before
            direction_changed = (previous_delta * current_delta) < 0

        candidates.append({
            "devise": d,
            "angle": current_angle,
            "delta": current_delta,
            "direction_changed": direction_changed,
        })

    if len(candidates) < min_required:
        return None

    best_cluster: List[Dict[str, Any]] = []
    best_spread = float("inf")

    for pivot in candidates:
        cluster = [
            c for c in candidates
            if abs(c["angle"] - pivot["angle"]) <= angle_tolerance
        ]
        if len(cluster) < min_required:
            continue

        angles = [c["angle"] for c in cluster]
        spread = max(angles) - min(angles)
        if len(cluster) > len(best_cluster) or (len(cluster) == len(best_cluster) and spread < best_spread):
            best_cluster = cluster
            best_spread = spread

    if len(best_cluster) < min_required:
        return None

    angles = [c["angle"] for c in best_cluster]
    common_angle = sum(angles) / len(angles)
    dispersion = _stdev(angles)
    alignment_quality = max(0.0, min(1.0, 1.0 - (dispersion / max(angle_tolerance, EPSILON))))
    direction_changed_count = sum(1 for c in best_cluster if c["direction_changed"])

    has_direction_history = bar_index - (2 * lookback) >= 0
    if has_direction_history and direction_changed_count == 0:
        return None

    return {
        "aligned_devises": [c["devise"] for c in sorted(best_cluster, key=lambda x: x["devise"])],
        "common_angle": round(common_angle, 3),
        "alignment_quality": round(alignment_quality, 3),
        "bar_time": _bar_time(rows, bar_index),
        "tf": int(tf),
        "angle_tolerance": float(angle_tolerance),
        "direction_changed_count": int(direction_changed_count),
        "angles": {c["devise"]: round(c["angle"], 3) for c in best_cluster},
    }


def _detect_value_mode(values: Sequence[float]) -> str:
    """
    Detecte grossierement si la serie ressemble a:
      - zscore: valeurs autour de -3/+3
      - oscillator: valeurs type 0/100
    """
    if not values:
        return "zscore"
    max_abs = max(abs(v) for v in values)
    # Force/z-score PowerFlow est generalement dans une amplitude courte (-3/+3).
    # Les oscillateurs 0/100 depassent normalement 6 des qu'ils sont exploitables.
    if max_abs <= 6.0:
        return "zscore"
    return "oscillator"


def _extreme_side(current: float, mode: str) -> str:
    if mode == "zscore":
        return "HIGH" if current >= 0 else "LOW"
    return "HIGH" if current >= 50.0 else "LOW"


def _is_in_extreme(value: float, side: str, mode: str) -> bool:
    if mode == "zscore":
        return value >= 1.5 if side == "HIGH" else value <= -1.5
    return value >= 70.0 if side == "HIGH" else value <= 30.0


def _distance_from_neutral(value: float, mode: str) -> float:
    if mode == "zscore":
        return abs(value)
    return abs(value - 50.0) / 25.0


def extreme_zone_breathing(
    devise: str,
    rows: Sequence[Tuple[Any, ...]],
    bar_index: int,
    window: int,
    devise_cols: Sequence[Tuple[str, str]],
) -> Dict[str, Any]:
    """
    Mesure les micro-oscillations a l'interieur d'une zone extreme.

    Retourne:
      {
        'pullback_count': 3,
        'compression_count': 2,
        'breathing_density': 0.75,
        'energy_accumulation': 8.2,
        'side': 'LOW',
        'mode': 'zscore',
      }

    Lecture PowerFlow:
      pullure absorbee = tentative de sortie refusee.
      respiration dense = energie stockee.
    """
    if not rows:
        return {
            "pullback_count": 0,
            "compression_count": 0,
            "breathing_density": 0.0,
            "energy_accumulation": 0.0,
            "side": "NONE",
            "mode": "unknown",
            "bar_time": "",
        }
    if bar_index >= len(rows):
        raise IndexError("bar_index out of range")
    if window <= 0:
        raise ValueError("window must be > 0")

    start = _safe_window_start(bar_index, window)
    values = [_value_at(rows, i, devise, devise_cols) for i in range(start, bar_index + 1)]
    if len(values) < 3:
        current = values[-1] if values else 0.0
        mode = _detect_value_mode(values)
        side = _extreme_side(current, mode)
        return {
            "pullback_count": 0,
            "compression_count": 0,
            "breathing_density": 0.0,
            "energy_accumulation": round(_distance_from_neutral(current, mode), 3),
            "side": side,
            "mode": mode,
            "bar_time": _bar_time(rows, bar_index),
        }

    mode = _detect_value_mode(values)
    current = values[-1]
    side = _extreme_side(current, mode)

    pullback_count = 0
    compression_count = 0

    for i in range(1, len(values) - 1):
        prev_v = values[i - 1]
        mid_v = values[i]
        next_v = values[i + 1]

        if side == "LOW":
            is_pullure = prev_v < mid_v and next_v < mid_v and (_is_in_extreme(prev_v, side, mode) or _is_in_extreme(next_v, side, mode))
        else:
            is_pullure = prev_v > mid_v and next_v > mid_v and (_is_in_extreme(prev_v, side, mode) or _is_in_extreme(next_v, side, mode))

        if is_pullure:
            pullback_count += 1

    deltas = [abs(values[i] - values[i - 1]) for i in range(1, len(values))]
    for i in range(1, len(deltas)):
        if deltas[i] < deltas[i - 1] * 0.75:
            compression_count += 1

    bars_in_zone = sum(1 for v in values if _is_in_extreme(v, side, mode))
    breathing_events = pullback_count + compression_count
    breathing_density = breathing_events / max(1, len(values) - 2)

    distance = _distance_from_neutral(current, mode)
    energy_accumulation = distance * math.log1p(bars_in_zone + breathing_events) * (1.0 + breathing_density)

    return {
        "pullback_count": int(pullback_count),
        "compression_count": int(compression_count),
        "breathing_density": round(breathing_density, 3),
        "energy_accumulation": round(energy_accumulation, 3),
        "bars_in_zone": int(bars_in_zone),
        "side": side,
        "mode": mode,
        "bar_time": _bar_time(rows, bar_index),
        "current_value": round(current, 6),
    }


__all__ = [
    "temporal_density",
    "detect_angular_alignment",
    "extreme_zone_breathing",
]
