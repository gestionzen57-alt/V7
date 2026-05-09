"""
PowerFlow V5+ - detect_zones_v5.py
Mission 6A : zones dynamiques, temps de zone, phase, sortie/cross.

Role :
- Lire les zones comme des champs de reaction, pas comme des lignes fixes.
- Mesurer ou se trouve une devise, combien de temps elle y reste,
  comment elle en sort, et si une confirmation par cross/ranking apparait.
- Garder le fichier autonome, SQLite direct, sans modifier les fichiers existants.

Execution Windows :
    python detect_zones_v5.py GBPUSD 5 --db powerflow.db --bars 60 --devises eur,gbp,usd
    python detect_zones_v5.py GBPUSD 15 --db powerflow.db --bars 40 --devises eur,gbp,usd --show-all
    python detect_zones_v5.py GBPUSD 10080 --db powerflow.db --bars 20 --devises eur,gbp,usd

Lecture :
- ZONE_TOUCH : zone touchee, peu de temps.
- ZONE_WORK : zone travaillee, plusieurs bougies.
- ZONE_HOLD : zone tenue, domination/faiblesse maintenue.
- ZONE_REJECTION : sortie/rejet d'une zone haute ou basse.
- LOW_ZONE_RELEASE_TO_CENTER : sortie de cave vers centre.
- HIGH_ZONE_DOMINANCE_LOSS : perte de domination haute.
- ZONE_EXIT_CROSS_CONFIRMATION : sortie confirmee par cross/ranking.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

DB_PATH = "powerflow.db"
ALL_DEVISES = ["gbp", "usd", "eur", "jpy", "cad", "chf", "aud", "nzd"]
DEFAULT_FOCUS = ["eur", "gbp", "usd"]

TF_LABELS = {
    1: "M1",
    5: "M5",
    15: "M15",
    30: "M30",
    60: "H1",
    240: "H4",
    1440: "D1",
    10080: "W1",
}

TF_MINUTES = {
    1: 1,
    5: 5,
    15: 15,
    30: 30,
    60: 60,
    240: 240,
    1440: 1440,
    10080: 10080,
}

# Fenetres par defaut pour les angles/phase.
TF_WINDOWS = {
    1: 10,
    5: 12,
    15: 16,
    30: 20,
    60: 24,
    240: 30,
    1440: 40,
    10080: 52,
}

# Bandes de base. Elles restent des reperes, pas des verites fixes.
BASE_BANDS = {
    "extreme_low_max": 20.0,
    "low_max": 35.0,
    "center_low": 45.0,
    "center_high": 60.0,
    "high_min": 65.0,
    "extreme_high_min": 80.0,
}

ANGLE_EXIT_STRONG = 2.5
ANGLE_EXIT_MEDIUM = 1.2
MIN_ZONE_WORK_BARS = 3
DOUBLE_PATTERN_MIN_SWING = 4.0
CENTER_REENTRY_MIN = 42.0
CENTER_REENTRY_MAX = 62.0


@dataclass
class ZoneStory:
    story_type: str
    quality: str
    score: int
    bar_time: str
    symbol: str
    tf: int
    devise: str
    current_value: Optional[float]
    current_zone: str
    zone_phase: str
    bars_in_zone: int
    minutes_in_zone: int
    entry_time: Optional[str]
    entry_session: Optional[str]
    current_session: Optional[str]
    exit_from_zone: Optional[str]
    velocity_profile: str
    pattern: str
    crossed: Optional[str]
    rank_before: Optional[int]
    rank_now: Optional[int]
    opposite_tension: Optional[str]
    note: str

    def to_dict(self) -> Dict:
        return asdict(self)


def tf_label(tf: int) -> str:
    return TF_LABELS.get(tf, f"M{tf}")


def tf_minutes(tf: int) -> int:
    return TF_MINUTES.get(tf, max(1, int(tf)))


def parse_bar_time(value: str) -> Optional[datetime]:
    if not value:
        return None
    text = value.replace("T", " ").replace("Z", "+00:00")
    try:
        if "+" in text[-6:] or "-" in text[-6:]:
            return datetime.fromisoformat(text)
        return datetime.strptime(text[:16], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    except Exception:
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except Exception:
            return None


def fmt_dt(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d %H:%M")


def get_session_name(bar_time: str, offset_hours: int = 0) -> str:
    dt = parse_bar_time(bar_time)
    if dt is None:
        return "UNKNOWN_SESSION"
    dt = dt + timedelta(hours=offset_hours)
    h = dt.hour
    # Grille volontairement simple : ajustable selon broker plus tard.
    if 0 <= h < 7:
        return "ASIA_SESSION"
    if 7 <= h < 12:
        return "LONDON_SESSION"
    if 12 <= h < 16:
        return "LONDON_NY_OVERLAP"
    if 16 <= h < 21:
        return "US_SESSION"
    return "LOW_LIQUIDITY"


def get_available_columns(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("PRAGMA table_info(force_snapshots)")
    return [r[1] for r in cur.fetchall()]


def get_available_devises(conn: sqlite3.Connection) -> List[str]:
    cols = set(get_available_columns(conn))
    return [d for d in ALL_DEVISES if f"force_{d}" in cols]


def normalize_devises_arg(value: str, available: Sequence[str]) -> List[str]:
    available_set = set(available)
    if value.lower().strip() == "all":
        return list(available)
    requested = [x.strip().lower() for x in value.split(",") if x.strip()]
    return [d for d in requested if d in available_set]


def get_zone_rows(
    conn: sqlite3.Connection,
    symbol: str,
    tf: int,
    end_bar: Optional[str],
    bars: int,
    devises: Sequence[str],
) -> Tuple[List[Tuple], List[Tuple[str, str]]]:
    if not devises:
        return [], []
    cols = [(d, f"force_{d}") for d in devises]
    select_cols = ",\n               ".join([f"AVG({col}) AS {dev}" for dev, col in cols])
    guard_cols = cols[: min(3, len(cols))]
    not_null_guard = " AND ".join([f"{col} IS NOT NULL" for _dev, col in guard_cols]) or "1=1"

    params: List[object] = [symbol.upper(), tf]
    end_clause = ""
    if end_bar:
        end_clause = "AND strftime('%Y-%m-%d %H:%M', datetime(created_at)) <= ?"
        params.append(end_bar[:16].replace("T", " "))
    params.append(int(bars))

    sql = f"""
        SELECT strftime('%Y-%m-%d %H:%M', datetime(created_at)) AS bar_time,
               {select_cols}
        FROM force_snapshots
        WHERE symbol = ?
          AND timeframe = ?
          AND {not_null_guard}
          {end_clause}
        GROUP BY bar_time
        ORDER BY bar_time DESC
        LIMIT ?
    """
    cur = conn.execute(sql, params)
    rows = cur.fetchall()
    rows.reverse()
    return rows, cols


def _col_idx(devise: str, devise_cols: Sequence[Tuple[str, str]]) -> Optional[int]:
    devise = devise.lower()
    for idx, (d, _c) in enumerate(devise_cols):
        if d == devise:
            return idx + 1
    return None


def _value(rows: Sequence[Tuple], index: int, col_idx: int) -> Optional[float]:
    if index < 0 or index >= len(rows):
        return None
    v = rows[index][col_idx]
    if v is None:
        return None
    return float(v)


def _series(rows: Sequence[Tuple], col_idx: int, start: int, end: int) -> List[float]:
    start = max(0, start)
    end = min(len(rows) - 1, end)
    if start > end:
        return []
    out: List[float] = []
    for i in range(start, end + 1):
        v = _value(rows, i, col_idx)
        if v is not None:
            out.append(v)
    return out


def _slope(values: Sequence[float]) -> Optional[float]:
    if len(values) < 3:
        return None
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    return float(np.polyfit(x, y, 1)[0])


def _angle_from_slope(slope: float) -> float:
    return float(np.degrees(np.arctan(slope / 10.0)))


def calc_angle(devise: str, rows: Sequence[Tuple], bar_index: int, tf: int, devise_cols: Sequence[Tuple[str, str]], window: Optional[int] = None) -> Dict:
    idx = _col_idx(devise, devise_cols)
    if idx is None or bar_index >= len(rows):
        return {"status": "N/A", "angle": None, "direction": "N/A", "note": "devise indisponible"}
    w = int(window or TF_WINDOWS.get(tf, 20))
    vals = _series(rows, idx, bar_index - w + 1, bar_index)
    if len(vals) < 3:
        return {"status": "N/A", "angle": None, "direction": "N/A", "note": f"pas assez de donnees ({len(vals)})"}
    sl = _slope(vals)
    if sl is None:
        return {"status": "N/A", "angle": None, "direction": "N/A", "note": "slope N/A"}
    angle = _angle_from_slope(sl)
    if abs(angle) < 0.5:
        direction = "PLATE"
    elif angle > 0:
        direction = "HAUT"
    else:
        direction = "BAS"
    return {
        "status": "OK",
        "angle": round(angle, 2),
        "slope": round(sl, 4),
        "direction": direction,
        "delta": round(vals[-1] - vals[0], 2),
        "window": len(vals),
        "note": f"{devise.upper()} angle {angle:+.2f} sur {len(vals)}b",
    }


def dynamic_bands(tf: int, session: Optional[str] = None) -> Dict[str, float]:
    """
    Bandes dynamiques V0 : base + leger ajustement TF/session.
    Plus le TF est lourd, plus on accepte une zone de travail large.
    """
    b = dict(BASE_BANDS)
    if tf >= 60:
        b["low_max"] += 2.0
        b["high_min"] -= 2.0
        b["center_low"] -= 2.0
        b["center_high"] += 2.0
    if tf >= 240:
        b["low_max"] += 2.0
        b["high_min"] -= 2.0
    if session in ("LONDON_NY_OVERLAP", "US_SESSION"):
        # Sessions actives : les rejets peuvent se declencher sans attendre les extremes exacts.
        b["low_max"] += 1.0
        b["high_min"] -= 1.0
    return b


def classify_zone(value: Optional[float], tf: int, session: Optional[str] = None) -> str:
    if value is None:
        return "ZONE_NA"
    b = dynamic_bands(tf, session)
    if value <= b["extreme_low_max"]:
        return "EXTREME_LOW_ZONE"
    if value <= b["low_max"]:
        return "LOW_WORK_ZONE"
    if b["center_low"] <= value <= b["center_high"]:
        return "CENTER_ZONE"
    if value >= b["extreme_high_min"]:
        return "EXTREME_HIGH_ZONE"
    if value >= b["high_min"]:
        return "HIGH_WORK_ZONE"
    if value < b["center_low"]:
        return "LOW_MID_ZONE"
    return "HIGH_MID_ZONE"


def zone_family(zone: str) -> str:
    if zone in ("EXTREME_LOW_ZONE", "LOW_WORK_ZONE"):
        return "LOW"
    if zone in ("EXTREME_HIGH_ZONE", "HIGH_WORK_ZONE"):
        return "HIGH"
    if zone == "CENTER_ZONE":
        return "CENTER"
    if zone == "LOW_MID_ZONE":
        return "LOW_MID"
    if zone == "HIGH_MID_ZONE":
        return "HIGH_MID"
    return "NA"


def is_low_family(family: str) -> bool:
    return family == "LOW"


def is_high_family(family: str) -> bool:
    return family == "HIGH"


def is_centerish_family(family: str) -> bool:
    return family in ("CENTER", "LOW_MID", "HIGH_MID")


def rank_map_for_bar(rows: Sequence[Tuple], bar_index: int, devise_cols: Sequence[Tuple[str, str]]) -> Dict[str, int]:
    vals = []
    for pos, (dev, _col) in enumerate(devise_cols, start=1):
        v = _value(rows, bar_index, pos)
        if v is not None:
            vals.append((dev, v))
    vals_sorted = sorted(vals, key=lambda x: x[1], reverse=True)
    return {dev: rank + 1 for rank, (dev, _v) in enumerate(vals_sorted)}


def find_current_episode(
    rows: Sequence[Tuple],
    bar_index: int,
    col_idx: int,
    tf: int,
    family: str,
    session_offset: int = 0,
) -> Tuple[int, int, List[float]]:
    """Episode contigu finissant sur bar_index dans la meme famille."""
    if bar_index < 0 or bar_index >= len(rows):
        return bar_index, bar_index, []
    start = bar_index
    values: List[float] = []
    i = bar_index
    while i >= 0:
        session = get_session_name(rows[i][0], session_offset)
        z = classify_zone(_value(rows, i, col_idx), tf, session)
        if zone_family(z) != family:
            break
        start = i
        i -= 1
    values = _series(rows, col_idx, start, bar_index)
    return start, bar_index, values


def find_previous_episode(
    rows: Sequence[Tuple],
    bar_index: int,
    col_idx: int,
    tf: int,
    target_family: str,
    session_offset: int = 0,
) -> Tuple[Optional[int], Optional[int], List[float]]:
    """Dernier episode contigu target_family avant bar_index."""
    i = min(bar_index - 1, len(rows) - 1)
    while i >= 0:
        session = get_session_name(rows[i][0], session_offset)
        fam = zone_family(classify_zone(_value(rows, i, col_idx), tf, session))
        if fam == target_family:
            end = i
            start = i
            i -= 1
            while i >= 0:
                session2 = get_session_name(rows[i][0], session_offset)
                fam2 = zone_family(classify_zone(_value(rows, i, col_idx), tf, session2))
                if fam2 != target_family:
                    break
                start = i
                i -= 1
            return start, end, _series(rows, col_idx, start, end)
        i -= 1
    return None, None, []


def count_turns(values: Sequence[float], mode: str) -> int:
    """Compte sommets/creux locaux significatifs dans un petit episode."""
    if len(values) < 3:
        return 0
    count = 0
    for i in range(1, len(values) - 1):
        prev_v, cur_v, next_v = values[i - 1], values[i], values[i + 1]
        if mode == "top" and cur_v >= prev_v and cur_v >= next_v:
            if (cur_v - min(prev_v, next_v)) >= DOUBLE_PATTERN_MIN_SWING / 2:
                count += 1
        elif mode == "bottom" and cur_v <= prev_v and cur_v <= next_v:
            if (max(prev_v, next_v) - cur_v) >= DOUBLE_PATTERN_MIN_SWING / 2:
                count += 1
    return count


def detect_pattern_for_episode(family: str, values: Sequence[float]) -> str:
    if len(values) < 4:
        return "NO_PATTERN"
    if family == "HIGH":
        tops = count_turns(values, "top")
        if tops >= 2:
            return "DOUBLE_TOP_HIGH_ZONE"
        if tops == 1:
            return "HIGH_ZONE_BOSSE"
    if family == "LOW":
        bottoms = count_turns(values, "bottom")
        if bottoms >= 2:
            return "DOUBLE_BOTTOM_LOW_ZONE"
        if bottoms == 1:
            return "LOW_ZONE_CREUX"
    return "NO_PATTERN"


def detect_cross_confirmation(
    devise: str,
    rows: Sequence[Tuple],
    bar_index: int,
    devise_cols: Sequence[Tuple[str, str]],
    previous_family: Optional[str],
    episode_start: Optional[int],
    episode_end: Optional[int],
) -> Tuple[Optional[str], Optional[int], Optional[int], Optional[str]]:
    """
    Detecte si la devise sort d'un statut extreme :
    - LOW : elle n'est plus derniere / croise quelqu'un vers le haut.
    - HIGH : elle n'est plus premiere / se fait croiser vers le bas.
    """
    idx = _col_idx(devise, devise_cols)
    if idx is None or bar_index <= 0 or bar_index >= len(rows):
        return None, None, None, None

    rank_now_map = rank_map_for_bar(rows, bar_index, devise_cols)
    rank_prev_map = rank_map_for_bar(rows, max(0, bar_index - 1), devise_cols)
    rank_now = rank_now_map.get(devise)
    rank_prev = rank_prev_map.get(devise)

    crossed: Optional[str] = None
    v_prev = _value(rows, bar_index - 1, idx)
    v_now = _value(rows, bar_index, idx)
    if v_prev is None or v_now is None:
        return None, rank_prev, rank_now, None

    for other, _col in devise_cols:
        if other == devise:
            continue
        oidx = _col_idx(other, devise_cols)
        if oidx is None:
            continue
        o_prev = _value(rows, bar_index - 1, oidx)
        o_now = _value(rows, bar_index, oidx)
        if o_prev is None or o_now is None:
            continue
        if previous_family == "LOW":
            if v_prev <= o_prev and v_now > o_now:
                crossed = other.upper()
                return "ZONE_EXIT_CROSS_CONFIRMATION", rank_prev, rank_now, crossed
        if previous_family == "HIGH":
            if v_prev >= o_prev and v_now < o_now:
                crossed = other.upper()
                return "ZONE_LOSS_CROSS_CONFIRMATION", rank_prev, rank_now, crossed

    if previous_family == "LOW" and rank_now is not None and len(devise_cols) >= 2:
        # Plus la plus faible = confirmation faible mais utile.
        if rank_now < len(rank_now_map):
            return "LOW_ZONE_EXIT_RANK_CONFIRMATION", rank_prev, rank_now, None
    if previous_family == "HIGH" and rank_now is not None:
        if rank_now > 1:
            return "HIGH_ZONE_LOSS_RANK_CONFIRMATION", rank_prev, rank_now, None
    return None, rank_prev, rank_now, None


def detect_opposite_zone_tension(
    devise: str,
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    session_offset: int = 0,
) -> Optional[str]:
    idx = _col_idx(devise, devise_cols)
    if idx is None or bar_index >= len(rows):
        return None
    session = get_session_name(rows[bar_index][0], session_offset)
    z = classify_zone(_value(rows, bar_index, idx), tf, session)
    fam = zone_family(z)
    if fam not in ("LOW", "HIGH"):
        return None
    for other, _col in devise_cols:
        if other == devise:
            continue
        oidx = _col_idx(other, devise_cols)
        if oidx is None:
            continue
        oz = classify_zone(_value(rows, bar_index, oidx), tf, session)
        ofam = zone_family(oz)
        if fam == "LOW" and ofam == "HIGH":
            return f"HIGH_LOW_ZONE_OPPOSITION vs {other.upper()}"
        if fam == "HIGH" and ofam == "LOW":
            return f"HIGH_LOW_ZONE_OPPOSITION vs {other.upper()}"
    return None


def detect_zone_story(
    devise: str,
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    symbol: str,
    session_offset: int = 0,
) -> ZoneStory:
    bar_time = rows[bar_index][0] if 0 <= bar_index < len(rows) else ""
    current_session = get_session_name(bar_time, session_offset)
    idx = _col_idx(devise, devise_cols)
    if idx is None or bar_index >= len(rows):
        return ZoneStory(
            story_type="ZONE_NA",
            quality="N/A",
            score=0,
            bar_time=bar_time,
            symbol=symbol.upper(),
            tf=tf,
            devise=devise.upper(),
            current_value=None,
            current_zone="ZONE_NA",
            zone_phase="N/A",
            bars_in_zone=0,
            minutes_in_zone=0,
            entry_time=None,
            entry_session=None,
            current_session=current_session,
            exit_from_zone=None,
            velocity_profile="N/A",
            pattern="NO_PATTERN",
            crossed=None,
            rank_before=None,
            rank_now=None,
            opposite_tension=None,
            note="Devise indisponible",
        )

    cur_val = _value(rows, bar_index, idx)
    cur_zone = classify_zone(cur_val, tf, current_session)
    cur_family = zone_family(cur_zone)
    angle_info = calc_angle(devise, rows, bar_index, tf, devise_cols, window=min(TF_WINDOWS.get(tf, 20), max(3, bar_index + 1)))
    angle = angle_info.get("angle")

    score = 0
    quality = "FAIBLE"
    story_type = "ZONE_NEUTRAL"
    zone_phase = "ZONE_NEUTRAL"
    velocity_profile = "NO_VELOCITY"
    pattern = "NO_PATTERN"
    exit_from_zone: Optional[str] = None
    entry_time: Optional[str] = None
    entry_session: Optional[str] = None
    bars_in_zone = 0
    minutes_in_zone = 0
    crossed: Optional[str] = None
    rank_before: Optional[int] = None
    rank_now: Optional[int] = None

    if cur_family in ("LOW", "HIGH", "CENTER"):
        start, end, episode_values = find_current_episode(rows, bar_index, idx, tf, cur_family, session_offset)
        bars_in_zone = len(episode_values)
        minutes_in_zone = bars_in_zone * tf_minutes(tf)
        entry_time = rows[start][0] if episode_values else None
        entry_session = get_session_name(entry_time, session_offset) if entry_time else None
        pattern = detect_pattern_for_episode(cur_family, episode_values)

        if cur_family == "LOW":
            if bars_in_zone <= 2:
                story_type = "LOW_ZONE_TOUCH"
                zone_phase = "ZONE_TOUCH"
                score += 15
            elif bars_in_zone >= MIN_ZONE_WORK_BARS:
                story_type = "LOW_ZONE_WORK"
                zone_phase = "ZONE_WORK"
                score += 35
                if pattern == "DOUBLE_BOTTOM_LOW_ZONE":
                    score += 15
            if angle is not None and angle > ANGLE_EXIT_MEDIUM:
                story_type = "LOW_ZONE_REBUILD"
                zone_phase = "ZONE_REBUILD"
                velocity_profile = "SLOW_BOTTOM_REBUILD" if angle < ANGLE_EXIT_STRONG else "LOW_ZONE_REACCELERATION"
                score += 20
        elif cur_family == "HIGH":
            if bars_in_zone <= 2:
                story_type = "HIGH_ZONE_TOUCH"
                zone_phase = "ZONE_TOUCH"
                score += 15
            elif bars_in_zone >= MIN_ZONE_WORK_BARS:
                story_type = "HIGH_ZONE_HOLD"
                zone_phase = "ZONE_HOLD"
                score += 35
                if pattern == "DOUBLE_TOP_HIGH_ZONE":
                    score += 15
            if angle is not None and angle < -ANGLE_EXIT_MEDIUM:
                story_type = "HIGH_ZONE_DECELERATION"
                zone_phase = "ZONE_DECELERATION"
                velocity_profile = "FAST_TOP_REJECTION_SETUP" if abs(angle) >= ANGLE_EXIT_STRONG else "ZONE_DECELERATION"
                score += 15
        elif cur_family == "CENTER":
            story_type = "CENTER_BATTLE_ZONE"
            zone_phase = "CENTER_WORK"
            score += 20
    else:
        # Possibilite importante : vient de sortir d'une zone LOW/HIGH vers centre/milieu.
        low_start, low_end, low_vals = find_previous_episode(rows, bar_index + 1, idx, tf, "LOW", session_offset)
        high_start, high_end, high_vals = find_previous_episode(rows, bar_index + 1, idx, tf, "HIGH", session_offset)

        # On ne prend que l'episode qui se termine juste avant ou tres proche.
        recent_low = low_end is not None and (bar_index - low_end) <= 2
        recent_high = high_end is not None and (bar_index - high_end) <= 2

        if recent_low and low_start is not None and low_end is not None:
            bars_in_zone = len(low_vals)
            minutes_in_zone = bars_in_zone * tf_minutes(tf)
            entry_time = rows[low_start][0]
            entry_session = get_session_name(entry_time, session_offset)
            exit_from_zone = "LOW"
            pattern = detect_pattern_for_episode("LOW", low_vals)
            cross_type, rank_before, rank_now, crossed = detect_cross_confirmation(
                devise, rows, bar_index, devise_cols, "LOW", low_start, low_end
            )
            if cur_val is not None and CENTER_REENTRY_MIN <= cur_val <= CENTER_REENTRY_MAX:
                story_type = "LOW_ZONE_RELEASE_TO_CENTER"
            else:
                story_type = "LOW_ZONE_EXIT"
            zone_phase = "ZONE_RELEASE"
            velocity_profile = "LOW_ZONE_REACCELERATION" if angle is not None and angle >= ANGLE_EXIT_STRONG else "SLOW_BOTTOM_REBUILD"
            score += 50
            if bars_in_zone >= MIN_ZONE_WORK_BARS:
                score += 15
            if pattern == "DOUBLE_BOTTOM_LOW_ZONE":
                score += 15
            if cross_type:
                story_type = cross_type
                score += 20
        elif recent_high and high_start is not None and high_end is not None:
            bars_in_zone = len(high_vals)
            minutes_in_zone = bars_in_zone * tf_minutes(tf)
            entry_time = rows[high_start][0]
            entry_session = get_session_name(entry_time, session_offset)
            exit_from_zone = "HIGH"
            pattern = detect_pattern_for_episode("HIGH", high_vals)
            cross_type, rank_before, rank_now, crossed = detect_cross_confirmation(
                devise, rows, bar_index, devise_cols, "HIGH", high_start, high_end
            )
            story_type = "HIGH_ZONE_DOMINANCE_LOSS"
            zone_phase = "ZONE_REJECTION"
            velocity_profile = "FAST_TOP_REJECTION" if angle is not None and angle <= -ANGLE_EXIT_STRONG else "HIGH_ZONE_DECELERATION"
            score += 50
            if bars_in_zone >= MIN_ZONE_WORK_BARS:
                score += 15
            if pattern == "DOUBLE_TOP_HIGH_ZONE":
                score += 15
            if cross_type:
                story_type = cross_type
                score += 20
        else:
            score += 5

    # Session memory : tenir une zone active longtemps a du poids.
    if bars_in_zone >= 4 and entry_session and current_session and entry_session != current_session:
        score += 10
        if story_type in ("HIGH_ZONE_DOMINANCE_LOSS", "ZONE_LOSS_CROSS_CONFIRMATION"):
            story_type = "SESSION_HIGH_HOLD_THEN_FADE"
        elif story_type in ("LOW_ZONE_RELEASE_TO_CENTER", "ZONE_EXIT_CROSS_CONFIRMATION", "LOW_ZONE_EXIT_RANK_CONFIRMATION"):
            story_type = "SESSION_LOW_HOLD_THEN_RELEASE"

    opposite = detect_opposite_zone_tension(devise, rows, bar_index, tf, devise_cols, session_offset)
    if opposite:
        score += 10

    score = int(max(0, min(100, score)))
    if score >= 80:
        quality = "FORTE"
    elif score >= 55:
        quality = "MOYENNE"
    elif score >= 30:
        quality = "FAIBLE_PLUS"

    note_parts = [f"{devise.upper()} {cur_zone} phase={zone_phase}"]
    if bars_in_zone:
        note_parts.append(f"temps_zone={bars_in_zone}b/{minutes_in_zone}min")
    if pattern != "NO_PATTERN":
        note_parts.append(pattern)
    if exit_from_zone:
        note_parts.append(f"sortie_{exit_from_zone}")
    if crossed:
        note_parts.append(f"cross {crossed}")
    elif rank_before is not None and rank_now is not None and rank_before != rank_now:
        note_parts.append(f"rang {rank_before}->{rank_now}")
    if velocity_profile != "NO_VELOCITY":
        note_parts.append(velocity_profile)
    if opposite:
        note_parts.append(opposite)

    return ZoneStory(
        story_type=story_type,
        quality=quality,
        score=score,
        bar_time=bar_time,
        symbol=symbol.upper(),
        tf=tf,
        devise=devise.upper(),
        current_value=round(cur_val, 2) if cur_val is not None else None,
        current_zone=cur_zone,
        zone_phase=zone_phase,
        bars_in_zone=bars_in_zone,
        minutes_in_zone=minutes_in_zone,
        entry_time=entry_time,
        entry_session=entry_session,
        current_session=current_session,
        exit_from_zone=exit_from_zone,
        velocity_profile=velocity_profile,
        pattern=pattern,
        crossed=crossed,
        rank_before=rank_before,
        rank_now=rank_now,
        opposite_tension=opposite,
        note=" | ".join(note_parts),
    )


def detect_all_zone_stories(
    rows: Sequence[Tuple],
    devise_cols: Sequence[Tuple[str, str]],
    bar_index: int,
    tf: int,
    symbol: str,
    session_offset: int = 0,
) -> List[ZoneStory]:
    stories: List[ZoneStory] = []
    for dev, _col in devise_cols:
        stories.append(detect_zone_story(dev, rows, bar_index, tf, devise_cols, symbol, session_offset))
    stories.sort(key=lambda s: s.score, reverse=True)
    return stories


def detect_best_zone_story(
    rows: Sequence[Tuple],
    devise_cols: Sequence[Tuple[str, str]],
    bar_index: int,
    tf: int,
    symbol: str,
    session_offset: int = 0,
) -> Optional[ZoneStory]:
    stories = detect_all_zone_stories(rows, devise_cols, bar_index, tf, symbol, session_offset)
    return stories[0] if stories else None


def build_zone_report(
    symbol: str,
    tf: int,
    db_path: str = DB_PATH,
    bars: int = 50,
    devises_arg: str = "eur,gbp,usd",
    end_bar: Optional[str] = None,
    show_all: bool = False,
    only_interest: bool = False,
    session_offset: int = 0,
) -> List[ZoneStory]:
    conn = sqlite3.connect(db_path)
    try:
        available = get_available_devises(conn)
        devises = normalize_devises_arg(devises_arg, available)
        rows, cols = get_zone_rows(conn, symbol, tf, end_bar, bars, devises)
    finally:
        conn.close()

    if len(rows) < 2 or not cols:
        print("Pas assez de donnees pour lire les zones dynamiques.")
        return []

    print(f"PowerFlow V5 Zones - {symbol.upper()} {tf_label(tf)} | bars={len(rows)} | devises={[d for d,_ in cols]}")
    print("Lecture: zone + phase + temps + sortie/cross")
    print()

    emitted: List[ZoneStory] = []
    for i in range(len(rows)):
        stories = detect_all_zone_stories(rows, cols, i, tf, symbol, session_offset)
        if not stories:
            continue
        best = stories[0]
        if only_interest and best.score < 45:
            continue
        emitted.append(best)
        print_zone_line(best)
        if show_all:
            for s in stories[1:]:
                if only_interest and s.score < 45:
                    continue
                print_zone_line(s, prefix="  - ")
    return emitted


def print_zone_line(story: ZoneStory, prefix: str = "") -> None:
    cross = f" cross={story.crossed}" if story.crossed else ""
    rank = ""
    if story.rank_before is not None and story.rank_now is not None and story.rank_before != story.rank_now:
        rank = f" rank={story.rank_before}->{story.rank_now}"
    opp = f" | {story.opposite_tension}" if story.opposite_tension else ""
    print(
        f"{prefix}[{story.bar_time}] {story.devise} {story.story_type} "
        f"{story.score}/100 {story.quality} | {story.current_zone} {story.zone_phase} | "
        f"{story.bars_in_zone}b/{story.minutes_in_zone}m | {story.velocity_profile}{cross}{rank}{opp}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="PowerFlow V5+ dynamic zone detector")
    parser.add_argument("symbol", help="Symbole, ex: GBPUSD")
    parser.add_argument("tf", type=int, help="Timeframe en minutes: 1,5,15,30,60,240,1440,10080")
    parser.add_argument("--db", default=DB_PATH, help="Chemin DB SQLite")
    parser.add_argument("--bars", type=int, default=50, help="Nombre de bougies a lire")
    parser.add_argument("--devises", default="eur,gbp,usd", help="eur,gbp,usd ou all")
    parser.add_argument("--end", default=None, help="Fin de lecture YYYY-MM-DD HH:MM")
    parser.add_argument("--show-all", action="store_true", help="Afficher toutes les devises, pas seulement la meilleure")
    parser.add_argument("--only-interest", action="store_true", help="Masquer les faibles lectures")
    parser.add_argument("--session-offset", type=int, default=0, help="Decalage heures pour classer les sessions")
    args = parser.parse_args()

    build_zone_report(
        symbol=args.symbol,
        tf=args.tf,
        db_path=args.db,
        bars=args.bars,
        devises_arg=args.devises,
        end_bar=args.end,
        show_all=args.show_all,
        only_interest=args.only_interest,
        session_offset=args.session_offset,
    )


if __name__ == "__main__":
    main()
