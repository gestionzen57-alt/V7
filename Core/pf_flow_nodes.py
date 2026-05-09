#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — detect_flow_nodes_v1.py

Détecteur isolé de nœuds Flow fractals.
Objectif : reconnaître les singularités de forces avant qu'elles deviennent de simples croisements.

Patterns V1.1 :
- PRE_CROSS_COMPRESSION_NODE
  Deux devises synchronisées approchent une troisième devise résistante.
  L'alerte vise la compression temporelle avant la libération du croisement.

- TRIPLE_NODE_PREPARATION
  Deux devises se touchent / quasi-touchent / se rejettent dans une fenêtre triple.
  L'alerte vise le rejet et la première désynchronisation, pas seulement le cross.

- TRIPLE_CROSS_CLUSTER
  Plusieurs préparations triple-node apparaissent dans la même fenêtre fractale.
  L'alerte vise la grappe de nœuds et la charge d'énergie.

- EXTREME_BOUND_NODE
  Un nœud apparaît proche d'une zone extrême / retour d'extrême.
  L'alerte signale que le nœud est chargé par une mémoire d'extrême.

Principes :
- Multi-timeframe : M1/M5/M15/M30/H1/H4/D1/W1.
- Pas de BUY/SELL.
- Pas de Telegram direct.
- Sortie cockpit/backtest : score, intérêt, devises, message court.
"""

from __future__ import annotations

import argparse
import csv
import itertools
import json
import math
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

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

# Fenêtres fractales : même logique, durée différente selon TF.
TF_WINDOW_RANGE = {
    1: (2, 5),
    5: (2, 5),
    15: (2, 5),
    30: (2, 5),
    60: (2, 5),
    240: (2, 5),
    1440: (2, 5),
    10080: (2, 5),
}

# Seuils V1 volontairement lisibles. Ils seront calibrés ensuite par backtest.
TF_THRESHOLDS = {
    1:     {"near_touch": 5.0, "pair_near": 12.0, "tri_range": 24.0, "min_slope": 0.45, "release_delta": 5.0},
    5:     {"near_touch": 6.0, "pair_near": 13.0, "tri_range": 28.0, "min_slope": 0.40, "release_delta": 5.0},
    15:    {"near_touch": 7.0, "pair_near": 15.0, "tri_range": 32.0, "min_slope": 0.35, "release_delta": 5.0},
    30:    {"near_touch": 7.0, "pair_near": 16.0, "tri_range": 34.0, "min_slope": 0.30, "release_delta": 4.5},
    60:    {"near_touch": 8.0, "pair_near": 18.0, "tri_range": 36.0, "min_slope": 0.25, "release_delta": 4.0},
    240:   {"near_touch": 9.0, "pair_near": 20.0, "tri_range": 40.0, "min_slope": 0.20, "release_delta": 3.5},
    1440:  {"near_touch": 10.0, "pair_near": 22.0, "tri_range": 44.0, "min_slope": 0.15, "release_delta": 3.0},
    10080: {"near_touch": 10.0, "pair_near": 24.0, "tri_range": 48.0, "min_slope": 0.10, "release_delta": 2.5},
}

INTEREST_RANK = {
    "IGNORE": 0,
    "WATCH_ZONE": 1,
    "STRUCTURE_BUILDING": 2,
    "TACTICAL_READY": 3,
    "SIGNAL_VALIDATED": 4,
}


@dataclass
class FlowNode:
    detected_at: str
    display_time: str
    event_window: str
    symbol: str
    timeframe: int
    tf_label: str
    pattern_type: str
    interest: str
    score: int
    phase: str
    currencies: List[str]
    sync_pair: List[str]
    target_currency: Optional[str]
    leader_after_node: Optional[str]
    window_bars: int
    tri_range: Optional[float]
    pair_distance: Optional[float]
    direction: Optional[str]
    message: str
    note: str
    raw: Dict

    def to_dict(self) -> Dict:
        return asdict(self)


def tf_label(tf: int) -> str:
    return TF_LABELS.get(tf, f"M{tf}")


def display_time(value: str) -> str:
    text = str(value or "")
    if len(text) >= 16:
        return text[11:16]
    return text


def event_window(rows: Sequence[Tuple], start: int, end: int) -> str:
    start = max(0, min(len(rows) - 1, start))
    end = max(0, min(len(rows) - 1, end))
    return f"{display_time(rows[start][0])}->{display_time(rows[end][0])}"


def node_label(pattern_type: str) -> str:
    return {
        "PRE_CROSS_COMPRESSION_NODE": "PRE-CROSS",
        "TRIPLE_NODE_PREPARATION": "TRIPLE PREP",
        "TRIPLE_CROSS_CLUSTER": "TRIPLE CLUSTER",
        "EXTREME_BOUND_NODE": "EXTREME NODE",
    }.get(pattern_type, pattern_type)


def thresholds(tf: int) -> Dict[str, float]:
    return TF_THRESHOLDS.get(tf, TF_THRESHOLDS[60])


def interest_from_score(score: int, tf: int, confirmed: bool = False) -> str:
    # M1 seul reste volontairement plafonné : cockpit d'abord, pas signal trading.
    if score >= 85 and tf != 1 and confirmed:
        return "TACTICAL_READY"
    if score >= 68:
        return "STRUCTURE_BUILDING"
    if score >= 52:
        return "WATCH_ZONE"
    return "IGNORE"


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1", (name,)
    ).fetchone() is not None


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


def get_flow_rows(
    conn: sqlite3.Connection,
    symbol: str,
    tf: int,
    bars: int,
    devises: Sequence[str],
    end_bar: Optional[str] = None,
) -> Tuple[List[Tuple], List[Tuple[str, str]]]:
    if not devises:
        return [], []

    cols = [(d, f"force_{d}") for d in devises]
    select_cols = ",\n               ".join([f"AVG({col}) AS {dev}" for dev, col in cols])
    guard_cols = cols[: min(3, len(cols))]
    not_null_guard = " AND ".join([f"{col} IS NOT NULL" for _dev, col in guard_cols]) or "1=1"

    params: List[object] = [symbol.upper(), int(tf)]
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
    rows = conn.execute(sql, params).fetchall()
    rows.reverse()
    return rows, cols


def _values(rows: Sequence[Tuple], devise_cols: Sequence[Tuple[str, str]], bar_index: int, dev: str) -> Optional[float]:
    dev = dev.lower()
    for pos, (d, _c) in enumerate(devise_cols, start=1):
        if d == dev:
            v = rows[bar_index][pos]
            return None if v is None else float(v)
    return None


def _series(rows: Sequence[Tuple], devise_cols: Sequence[Tuple[str, str]], start: int, end: int, dev: str) -> List[float]:
    out: List[float] = []
    for i in range(max(0, start), min(len(rows) - 1, end) + 1):
        v = _values(rows, devise_cols, i, dev)
        if v is not None:
            out.append(v)
    return out


def _slope(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    den = sum((x - mx) ** 2 for x in xs) or 1.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, values)) / den


def _std(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    m = sum(values) / len(values)
    return math.sqrt(sum((v - m) ** 2 for v in values) / len(values))


def _sign(v: float, min_abs: float) -> int:
    if abs(v) < min_abs:
        return 0
    return 1 if v > 0 else -1


def _tri_values(rows: Sequence[Tuple], devise_cols: Sequence[Tuple[str, str]], idx: int, triplet: Sequence[str]) -> Optional[Dict[str, float]]:
    vals: Dict[str, float] = {}
    for d in triplet:
        v = _values(rows, devise_cols, idx, d)
        if v is None:
            return None
        vals[d] = float(v)
    return vals


def _tri_range(vals: Dict[str, float]) -> float:
    return max(vals.values()) - min(vals.values())


def _leader_after(
    rows: Sequence[Tuple],
    devise_cols: Sequence[Tuple[str, str]],
    bar_index: int,
    triplet: Sequence[str],
    release_delta: float,
    lookahead: int = 3,
) -> Tuple[Optional[str], Optional[float], str]:
    if bar_index >= len(rows) - 1:
        return None, None, "BUILDING"
    end = min(len(rows) - 1, bar_index + lookahead)
    deltas: Dict[str, float] = {}
    for d in triplet:
        v0 = _values(rows, devise_cols, bar_index, d)
        v1 = _values(rows, devise_cols, end, d)
        if v0 is None or v1 is None:
            continue
        deltas[d] = float(v1 - v0)
    if not deltas:
        return None, None, "BUILDING"
    leader = max(deltas, key=lambda d: abs(deltas[d]))
    delta = deltas[leader]
    if abs(delta) >= release_delta:
        return leader.upper(), round(delta, 2), "CONFIRMED"
    return leader.upper(), round(delta, 2), "BUILDING"


def _direction_from_slope(slope: float, min_slope: float) -> str:
    s = _sign(slope, min_slope)
    if s > 0:
        return "HAUSSE"
    if s < 0:
        return "BAISSE"
    return "PLATE"


def detect_pre_cross_compression(
    rows: Sequence[Tuple],
    devise_cols: Sequence[Tuple[str, str]],
    symbol: str,
    tf: int,
    bar_index: int,
    window: int,
    triplet: Sequence[str],
) -> List[FlowNode]:
    th = thresholds(tf)
    start = bar_index - window + 1
    if start < 0:
        return []

    vals_start = _tri_values(rows, devise_cols, start, triplet)
    vals_now = _tri_values(rows, devise_cols, bar_index, triplet)
    if vals_start is None or vals_now is None:
        return []

    # Séries, slopes et distances
    series = {d: _series(rows, devise_cols, start, bar_index, d) for d in triplet}
    if any(len(v) < 2 for v in series.values()):
        return []
    slopes = {d: _slope(series[d]) for d in triplet}
    signs = {d: _sign(slopes[d], th["min_slope"]) for d in triplet}

    tri_range_start = _tri_range(vals_start)
    tri_range_now = _tri_range(vals_now)

    out: List[FlowNode] = []

    for a, b in itertools.combinations(triplet, 2):
        c = [d for d in triplet if d not in (a, b)][0]

        if signs[a] == 0 or signs[b] == 0 or signs[a] != signs[b]:
            continue

        pair_dist_start = abs(vals_start[a] - vals_start[b])
        pair_dist_now = abs(vals_now[a] - vals_now[b])
        pair_dist_series = [abs(series[a][k] - series[b][k]) for k in range(len(series[a]))]

        avg_to_c_start = (abs(vals_start[a] - vals_start[c]) + abs(vals_start[b] - vals_start[c])) / 2.0
        avg_to_c_now = (abs(vals_now[a] - vals_now[c]) + abs(vals_now[b] - vals_now[c])) / 2.0

        pair_stable_or_tight = pair_dist_now <= max(th["pair_near"], pair_dist_start + 2.0) and _std(pair_dist_series) <= 6.5
        approach_target = avg_to_c_now <= avg_to_c_start - 2.0 or avg_to_c_now <= th["pair_near"]
        tri_compression = tri_range_now <= tri_range_start - 3.0 or tri_range_now <= th["tri_range"]
        c_resists = signs[c] == 0 or signs[c] != signs[a] or abs(slopes[c]) < 0.75 * ((abs(slopes[a]) + abs(slopes[b])) / 2.0)

        if not (pair_stable_or_tight and approach_target and tri_compression and c_resists):
            continue

        score = 0
        score += 25  # synchro positive
        score += 15 if pair_stable_or_tight else 0
        score += 20 if approach_target else 0
        score += 20 if tri_compression else 0
        score += 10 if c_resists else 0

        leader, release, phase = _leader_after(rows, devise_cols, bar_index, triplet, th["release_delta"], lookahead=3)
        if phase == "CONFIRMED":
            score += 10

        score = max(0, min(100, int(score)))
        interest = interest_from_score(score, tf, confirmed=(phase == "CONFIRMED"))
        if interest == "IGNORE":
            continue

        direction = _direction_from_slope((slopes[a] + slopes[b]) / 2.0, th["min_slope"])
        msg = (
            f"PRE-CROSS NODE {tf_label(tf)} — {a.upper()}/{b.upper()} synchronisés "
            f"vers {c.upper()} résistant"
        )
        note = (
            f"{a.upper()}+{b.upper()} sync {direction}; distance paire {pair_dist_now:.1f}; "
            f"range3 {tri_range_now:.1f}; target {c.upper()} résiste"
        )
        raw = {
            "slopes": {d.upper(): round(slopes[d], 3) for d in triplet},
            "signs": {d.upper(): signs[d] for d in triplet},
            "tri_range_start": round(tri_range_start, 2),
            "tri_range_now": round(tri_range_now, 2),
            "pair_dist_start": round(pair_dist_start, 2),
            "pair_dist_now": round(pair_dist_now, 2),
            "avg_to_target_start": round(avg_to_c_start, 2),
            "avg_to_target_now": round(avg_to_c_now, 2),
            "release_delta": release,
            "current_values": {d.upper(): round(vals_now[d], 2) for d in triplet},
        }
        out.append(
            FlowNode(
                detected_at=str(rows[bar_index][0]),
                display_time=display_time(rows[bar_index][0]),
                event_window=event_window(rows, start, bar_index),
                symbol=symbol.upper(),
                timeframe=tf,
                tf_label=tf_label(tf),
                pattern_type="PRE_CROSS_COMPRESSION_NODE",
                interest=interest,
                score=score,
                phase=phase,
                currencies=[d.upper() for d in triplet],
                sync_pair=[a.upper(), b.upper()],
                target_currency=c.upper(),
                leader_after_node=leader,
                window_bars=window,
                tri_range=round(tri_range_now, 2),
                pair_distance=round(pair_dist_now, 2),
                direction=direction,
                message=msg,
                note=note,
                raw=raw,
            )
        )

    return out


def detect_triple_node_preparation(
    rows: Sequence[Tuple],
    devise_cols: Sequence[Tuple[str, str]],
    symbol: str,
    tf: int,
    bar_index: int,
    window: int,
    triplet: Sequence[str],
) -> List[FlowNode]:
    th = thresholds(tf)
    start = bar_index - window + 1
    if start < 0:
        return []

    vals_now = _tri_values(rows, devise_cols, bar_index, triplet)
    if vals_now is None:
        return []

    tri_range_now = _tri_range(vals_now)
    if tri_range_now > th["tri_range"]:
        return []

    series = {d: _series(rows, devise_cols, start, bar_index, d) for d in triplet}
    if any(len(v) < 2 for v in series.values()):
        return []

    out: List[FlowNode] = []
    slopes = {d: _slope(series[d]) for d in triplet}

    for a, b in itertools.combinations(triplet, 2):
        pair_dist = [abs(series[a][k] - series[b][k]) for k in range(len(series[a]))]
        min_dist = min(pair_dist)
        min_pos = pair_dist.index(min_dist)
        now_dist = pair_dist[-1]

        touch = min_dist <= th["near_touch"]
        rejection = min_pos < len(pair_dist) - 1 and now_dist >= min_dist + 2.0

        # Rejet sans cross propre : si le signe relatif début/fin reste identique, c'est souvent un touch/reject.
        rel_start = series[a][0] - series[b][0]
        rel_end = series[a][-1] - series[b][-1]
        no_clean_cross = (rel_start == 0) or (rel_start * rel_end >= 0)

        if not (touch and rejection):
            continue

        score = 25  # contact/quasi-contact
        score += 25 if rejection else 0
        score += 20 if tri_range_now <= th["tri_range"] else 0
        score += 10 if no_clean_cross else 0

        leader, release, phase = _leader_after(rows, devise_cols, bar_index, triplet, th["release_delta"], lookahead=3)
        if phase == "CONFIRMED":
            score += 20

        score = max(0, min(100, int(score)))
        interest = interest_from_score(score, tf, confirmed=(phase == "CONFIRMED"))
        if interest == "IGNORE":
            continue

        direction = _direction_from_slope(slopes.get(leader.lower(), 0.0) if leader else max(slopes.values(), key=abs), th["min_slope"])
        msg = (
            f"TRIPLE NODE PREP {tf_label(tf)} — rejet {a.upper()}/{b.upper()}, "
            f"surveiller première désynchronisation"
        )
        note = (
            f"{a.upper()}/{b.upper()} touch/reject; min_dist {min_dist:.1f} -> {now_dist:.1f}; "
            f"range3 {tri_range_now:.1f}; leader={leader or '?'}"
        )
        raw = {
            "slopes": {d.upper(): round(slopes[d], 3) for d in triplet},
            "min_pair_distance": round(min_dist, 2),
            "now_pair_distance": round(now_dist, 2),
            "min_distance_pos": min_pos,
            "tri_range_now": round(tri_range_now, 2),
            "no_clean_cross": no_clean_cross,
            "release_delta": release,
            "current_values": {d.upper(): round(vals_now[d], 2) for d in triplet},
        }
        out.append(
            FlowNode(
                detected_at=str(rows[bar_index][0]),
                display_time=display_time(rows[bar_index][0]),
                event_window=event_window(rows, start, bar_index),
                symbol=symbol.upper(),
                timeframe=tf,
                tf_label=tf_label(tf),
                pattern_type="TRIPLE_NODE_PREPARATION",
                interest=interest,
                score=score,
                phase=phase,
                currencies=[d.upper() for d in triplet],
                sync_pair=[a.upper(), b.upper()],
                target_currency="TRIPLE",
                leader_after_node=leader,
                window_bars=window,
                tri_range=round(tri_range_now, 2),
                pair_distance=round(now_dist, 2),
                direction=direction,
                message=msg,
                note=note,
                raw=raw,
            )
        )

    return out



def _row_index_map(rows: Sequence[Tuple]) -> Dict[str, int]:
    return {str(r[0]): i for i, r in enumerate(rows)}


def _is_extreme_bound(node: FlowNode, low: float = 22.0, high: float = 78.0) -> bool:
    vals = (node.raw or {}).get("current_values") or {}
    if not vals:
        return False
    return any(float(v) <= low or float(v) >= high for v in vals.values())


def build_extreme_bound_nodes(nodes: Sequence[FlowNode], rows: Sequence[Tuple], index_map: Dict[str, int]) -> List[FlowNode]:
    out: List[FlowNode] = []
    for n in nodes:
        if n.pattern_type not in ("PRE_CROSS_COMPRESSION_NODE", "TRIPLE_NODE_PREPARATION"):
            continue
        if not _is_extreme_bound(n):
            continue
        raw = dict(n.raw or {})
        raw["source_pattern"] = n.pattern_type
        raw["lab"] = "LAB_ALERT_003"
        score = min(100, n.score + 8)
        out.append(
            FlowNode(
                detected_at=n.detected_at,
                display_time=n.display_time,
                event_window=n.event_window,
                symbol=n.symbol,
                timeframe=n.timeframe,
                tf_label=n.tf_label,
                pattern_type="EXTREME_BOUND_NODE",
                interest=interest_from_score(score, n.timeframe, confirmed=(n.phase == "CONFIRMED")),
                score=score,
                phase=n.phase,
                currencies=n.currencies,
                sync_pair=n.sync_pair,
                target_currency=n.target_currency,
                leader_after_node=n.leader_after_node,
                window_bars=n.window_bars,
                tri_range=n.tri_range,
                pair_distance=n.pair_distance,
                direction=n.direction,
                message=f"EXTREME NODE {n.tf_label} {n.display_time} — nœud chargé par zone extrême",
                note=f"Mémoire d'extrême autour de {n.display_time}; source={n.pattern_type}; {n.note}",
                raw=raw,
            )
        )
    return out


def build_triple_cross_clusters(nodes: Sequence[FlowNode], rows: Sequence[Tuple], tf: int, symbol: str) -> List[FlowNode]:
    idx_map = _row_index_map(rows)
    base = [n for n in nodes if n.pattern_type == "TRIPLE_NODE_PREPARATION" and n.detected_at in idx_map]
    if len(base) < 2:
        return []
    base.sort(key=lambda n: idx_map[n.detected_at])
    cluster_span = 4 if tf <= 15 else 3
    out: List[FlowNode] = []
    emitted_ends = set()
    for i, first in enumerate(base):
        start_i = idx_map[first.detected_at]
        group = [first]
        for other in base[i + 1:]:
            if idx_map[other.detected_at] - start_i <= cluster_span:
                group.append(other)
        if len(group) < 2:
            continue
        last = group[-1]
        end_i = idx_map[last.detected_at]
        if end_i in emitted_ends:
            continue
        emitted_ends.add(end_i)
        avg_score = int(round(sum(n.score for n in group) / len(group)))
        score = min(100, avg_score + 12 + min(8, 3 * (len(group) - 2)))
        has_extreme = any(_is_extreme_bound(n) for n in group)
        if has_extreme:
            score = min(100, score + 5)
        confirmed = any(n.phase == "CONFIRMED" for n in group)
        leaders = [n.leader_after_node for n in group if n.leader_after_node]
        leader = leaders[-1] if leaders else last.leader_after_node
        times = [n.display_time for n in group]
        raw = {
            "lab": "LAB_ALERT_003",
            "node_times": times,
            "cluster_span_bars": end_i - start_i + 1,
            "node_energy": score,
            "has_extreme_memory": has_extreme,
        }
        out.append(
            FlowNode(
                detected_at=last.detected_at,
                display_time=last.display_time,
                event_window=event_window(rows, start_i, end_i),
                symbol=symbol.upper(),
                timeframe=tf,
                tf_label=tf_label(tf),
                pattern_type="TRIPLE_CROSS_CLUSTER",
                interest=interest_from_score(score, tf, confirmed=confirmed),
                score=score,
                phase="CONFIRMED" if confirmed else "BUILDING",
                currencies=last.currencies,
                sync_pair=["TRIPLE", "CLUSTER"],
                target_currency="NODE_ENERGY",
                leader_after_node=leader,
                window_bars=end_i - start_i + 1,
                tri_range=last.tri_range,
                pair_distance=last.pair_distance,
                direction=last.direction,
                message=f"TRIPLE CLUSTER {tf_label(tf)} {event_window(rows, start_i, end_i)} — énergie de nœuds x{len(group)}",
                note=f"LAB3: {len(group)} triple-prep proches ({', '.join(times)}); énergie={score}; leader={leader or '?'}",
                raw=raw,
            )
        )
    return out

def _dedupe_nodes(nodes: List[FlowNode], cooldown_bars: int = 2) -> List[FlowNode]:
    # 1) garder la meilleure occurrence par timestamp/pattern.
    by_time: Dict[Tuple[str, str], FlowNode] = {}
    for n in nodes:
        key = (n.detected_at, n.pattern_type)
        if key not in by_time or n.score > by_time[key].score:
            by_time[key] = n

    ordered = sorted(by_time.values(), key=lambda n: (n.detected_at, -n.score))

    # 2) cooldown par pattern pour éviter le spam cockpit.
    out: List[FlowNode] = []
    last_index: Dict[str, int] = {}
    for idx, n in enumerate(ordered):
        key = n.pattern_type
        if key in last_index and idx - last_index[key] <= cooldown_bars:
            # Remplacer si le nouveau est nettement meilleur.
            prev_pos = len(out) - 1
            if out and out[prev_pos].pattern_type == key and n.score > out[prev_pos].score + 8:
                out[prev_pos] = n
                last_index[key] = idx
            continue
        out.append(n)
        last_index[key] = idx
    return out


def detect_flow_nodes_from_rows(
    rows: Sequence[Tuple],
    devise_cols: Sequence[Tuple[str, str]],
    symbol: str,
    tf: int,
    max_nodes: Optional[int] = None,
    dedupe: bool = True,
) -> List[FlowNode]:
    if len(rows) < 3 or len(devise_cols) < 3:
        return []

    devs = [d for d, _c in devise_cols]
    wmin, wmax = TF_WINDOW_RANGE.get(tf, (2, 5))
    all_nodes: List[FlowNode] = []

    for i in range(max(1, wmin - 1), len(rows)):
        for triplet in itertools.combinations(devs, 3):
            for w in range(wmin, min(wmax, i + 1) + 1):
                all_nodes.extend(detect_pre_cross_compression(rows, devise_cols, symbol, tf, i, w, triplet))
                all_nodes.extend(detect_triple_node_preparation(rows, devise_cols, symbol, tf, i, w, triplet))

    # Dédoublonnage base avant LAB3, sinon plusieurs fenêtres sur la même bougie créent du bruit.
    all_nodes.sort(key=lambda n: (n.detected_at, n.score), reverse=False)
    base_nodes = _dedupe_nodes(all_nodes) if dedupe else list(all_nodes)

    idx_map = _row_index_map(rows)
    lab3_nodes = build_triple_cross_clusters(base_nodes, rows, tf, symbol)
    lab3_nodes.extend(build_extreme_bound_nodes(base_nodes, rows, idx_map))

    all_nodes = base_nodes + lab3_nodes
    all_nodes.sort(key=lambda n: (n.detected_at, n.score), reverse=False)
    if dedupe:
        all_nodes = _dedupe_nodes(all_nodes)
    all_nodes.sort(key=lambda n: n.detected_at, reverse=True)
    if max_nodes:
        all_nodes = all_nodes[:max_nodes]
    return all_nodes


def detect_flow_nodes(
    symbol: str,
    tf: int,
    db_path: str = DB_PATH,
    bars: int = 120,
    devises_arg: str = "eur,gbp,usd",
    end_bar: Optional[str] = None,
    max_nodes: Optional[int] = None,
    dedupe: bool = True,
) -> List[Dict]:
    if not os.path.exists(db_path):
        return []
    conn = sqlite3.connect(db_path)
    try:
        if not _table_exists(conn, "force_snapshots"):
            return []
        available = get_available_devises(conn)
        devises = normalize_devises_arg(devises_arg, available)
        rows, cols = get_flow_rows(conn, symbol, tf, bars, devises, end_bar=end_bar)
    finally:
        conn.close()

    nodes = detect_flow_nodes_from_rows(rows, cols, symbol, tf, max_nodes=max_nodes, dedupe=dedupe)
    return [n.to_dict() for n in nodes]


def detect_flow_nodes_multi_tf(
    symbol: str,
    timeframes: Sequence[int],
    db_path: str = DB_PATH,
    bars: int = 120,
    devises_arg: str = "eur,gbp,usd",
    max_per_tf: int = 5,
) -> List[Dict]:
    out: List[Dict] = []
    for tf in timeframes:
        out.extend(
            detect_flow_nodes(
                symbol=symbol,
                tf=int(tf),
                db_path=db_path,
                bars=bars,
                devises_arg=devises_arg,
                max_nodes=max_per_tf,
                dedupe=True,
            )
        )
    out.sort(key=lambda n: (n.get("detected_at", ""), n.get("score", 0)), reverse=True)
    return out


def init_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS flow_nodes_v1 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            detected_at TEXT NOT NULL,
            symbol TEXT NOT NULL,
            timeframe INTEGER NOT NULL,
            pattern_type TEXT NOT NULL,
            interest TEXT,
            score INTEGER,
            phase TEXT,
            currencies TEXT,
            sync_pair TEXT,
            target_currency TEXT,
            leader_after_node TEXT,
            window_bars INTEGER,
            tri_range REAL,
            pair_distance REAL,
            direction TEXT,
            message TEXT,
            note TEXT,
            raw_json TEXT
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_flow_nodes_v1_sym_tf_time ON flow_nodes_v1(symbol, timeframe, detected_at)"
    )
    conn.commit()


def store_nodes(db_path: str, nodes: Sequence[Dict]) -> int:
    if not nodes:
        return 0
    conn = sqlite3.connect(db_path)
    try:
        init_table(conn)
        inserted = 0
        for n in nodes:
            exists = conn.execute(
                """
                SELECT 1 FROM flow_nodes_v1
                WHERE detected_at=? AND symbol=? AND timeframe=? AND pattern_type=? AND sync_pair=?
                LIMIT 1
                """,
                (
                    n["detected_at"],
                    n["symbol"],
                    int(n["timeframe"]),
                    n["pattern_type"],
                    json.dumps(n.get("sync_pair") or [], ensure_ascii=False),
                ),
            ).fetchone()
            if exists:
                continue
            conn.execute(
                """
                INSERT INTO flow_nodes_v1 (
                    detected_at, symbol, timeframe, pattern_type, interest, score, phase,
                    currencies, sync_pair, target_currency, leader_after_node, window_bars,
                    tri_range, pair_distance, direction, message, note, raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    n["detected_at"],
                    n["symbol"],
                    int(n["timeframe"]),
                    n["pattern_type"],
                    n["interest"],
                    int(n["score"]),
                    n["phase"],
                    json.dumps(n.get("currencies") or [], ensure_ascii=False),
                    json.dumps(n.get("sync_pair") or [], ensure_ascii=False),
                    n.get("target_currency"),
                    n.get("leader_after_node"),
                    int(n.get("window_bars") or 0),
                    n.get("tri_range"),
                    n.get("pair_distance"),
                    n.get("direction"),
                    n.get("message"),
                    n.get("note"),
                    json.dumps(n.get("raw") or {}, ensure_ascii=False),
                ),
            )
            inserted += 1
        conn.commit()
        return inserted
    finally:
        conn.close()


def export_csv(path: str, nodes: Sequence[Dict]) -> None:
    fields = [
        "detected_at", "display_time", "event_window", "symbol", "timeframe", "tf_label", "pattern_type", "interest",
        "score", "phase", "currencies", "sync_pair", "target_currency",
        "leader_after_node", "window_bars", "tri_range", "pair_distance",
        "direction", "message", "note",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for n in nodes:
            row = {k: n.get(k) for k in fields}
            row["currencies"] = ",".join(n.get("currencies") or [])
            row["sync_pair"] = ",".join(n.get("sync_pair") or [])
            w.writerow(row)


def print_nodes(nodes: Sequence[Dict]) -> None:
    if not nodes:
        print("Aucun Flow Node detecte.")
        return
    for n in nodes:
        print(
            f"[{n.get('display_time') or n['detected_at']}] {n['tf_label']:<4} {n['pattern_type']:<28} "
            f"{n['score']:>3}/100 {n['interest']:<18} {n['phase']:<9} | "
            f"{'+'.join(n.get('sync_pair') or [])} -> {n.get('target_currency') or '-'} "
            f"| leader={n.get('leader_after_node') or '-'} | win={n.get('event_window','?')} | {n.get('note')}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="PowerFlow V6 — Flow Node detector V1")
    parser.add_argument("symbol", help="Ex: GBPUSD")
    parser.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")
    parser.add_argument("--timeframes", default="1,5,15,30,60,240", help="Ex: 1,5,15,30,60,240,1440,10080")
    parser.add_argument("--devises", default="eur,gbp,usd", help="Ex: eur,gbp,usd ou all")
    parser.add_argument("--bars", type=int, default=160, help="Nombre de barres par TF")
    parser.add_argument("--max-per-tf", type=int, default=8, help="Nombre max de nodes affiches par TF")
    parser.add_argument("--json", action="store_true", help="Sortie JSON")
    parser.add_argument("--store", action="store_true", help="Stocker dans table flow_nodes_v1")
    parser.add_argument("--export", default=None, help="Exporter CSV")
    args = parser.parse_args()

    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]
    nodes = detect_flow_nodes_multi_tf(
        symbol=args.symbol,
        timeframes=tfs,
        db_path=args.db,
        bars=args.bars,
        devises_arg=args.devises,
        max_per_tf=args.max_per_tf,
    )

    if args.store:
        n = store_nodes(args.db, nodes)
        print(f"[OK] {n} nouveaux Flow Nodes stockes dans flow_nodes_v1")

    if args.export:
        export_csv(args.export, nodes)
        print(f"[OK] Export CSV: {args.export}")

    if args.json:
        print(json.dumps(nodes, ensure_ascii=False, indent=2))
    else:
        print_nodes(nodes)


if __name__ == "__main__":
    main()
