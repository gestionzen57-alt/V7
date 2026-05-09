#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V5/V6 — pf_normalizer.py
(Fusion de detect_tf_normalizer_v1 et detect_tf_alignment_v6)

But : 
1. Normaliser la lecture de pente/angle par timeframe.
2. Mesurer l'alignement multi-timeframe (Mission 8) en consommant les scènes.

Usage :
    python pf_normalizer.py align GBPUSD --timeframes 5,15,30,60
    python pf_normalizer.py norm --symbol GBPUSD --timeframes 1,5,15
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pf_engine_scenes as scene_engine

DB_PATH = "powerflow.db"

ALL_DEVISES = ["gbp", "usd", "eur", "jpy", "cad", "chf", "aud", "nzd"]
DEFAULT_TIMEFRAMES = [1, 5, 15]

# =====================================================================
# CONSTANTES (Fusion Normalizer / Alignment)
# =====================================================================

TF_PROFILE: Dict[int, Dict[str, float]] = {
    1:  {"window": 12, "noise_deg": 2.0, "micro_deg": 4.0, "signal_deg": 7.0, "structure_deg": 11.0, "weight": 0.65},
    5:  {"window": 10, "noise_deg": 1.4, "micro_deg": 3.0, "signal_deg": 5.5, "structure_deg": 8.5,  "weight": 1.00},
    15: {"window": 8,  "noise_deg": 1.0, "micro_deg": 2.2, "signal_deg": 4.0, "structure_deg": 6.5,  "weight": 1.35},
    30: {"window": 8,  "noise_deg": 0.8, "micro_deg": 1.8, "signal_deg": 3.2, "structure_deg": 5.0,  "weight": 1.70},
    60: {"window": 6,  "noise_deg": 0.6, "micro_deg": 1.4, "signal_deg": 2.5, "structure_deg": 4.0,  "weight": 2.20},
    240:{"window": 5,  "noise_deg": 0.4, "micro_deg": 1.0, "signal_deg": 1.8, "structure_deg": 3.0,  "weight": 3.20},
}

TF_LABELS = {
    1:     "M1",
    5:     "M5",
    15:    "M15",
    30:    "M30",
    60:    "H1",
    240:   "H4",
    1440:  "D1",
    10080: "W1",
}
TF_NAME = TF_LABELS # Alias pour le code legacy du normalizer

TF_GROUP = {
    1:     "MICRO",
    5:     "COURT",
    15:    "COURT",
    30:    "MOYEN",
    60:    "MOYEN",
    240:   "LONG",
    1440:  "LONG",
    10080: "LONG",
}

TF_WEIGHT = {
    1:     0.5,
    5:     1.0,
    15:    1.4,
    30:    1.8,
    60:    2.5,
    240:   3.5,
    1440:  4.5,
    10080: 5.5,
}

SCENES_DIRECTIONNELLES = {
    "COALITION_PUSH",
    "TREND_CONTINUATION",
    "COMPRESSION_RELEASE",
    "ROTATION_BUILDING",
    "OPPOSITION_REBALANCE",
}

SCENES_NEUTRES = {
    "CENTER_BATTLE",
    "COMPRESSION_BUILD",
    "CHAOS_NO_TRADE",
    "NEGATIVE_MIRROR_SYNC",
}

INTEREST_RANK = {
    "IGNORE":              0,
    "WATCH_ZONE":          1,
    "STRUCTURE_BUILDING":  2,
    "TACTICAL_READY":      3,
    "SIGNAL_VALIDATED":    4,
}

VERDICT_COLOR = {
    "ALIGNEMENT_COMPLET":  "✅",
    "ALIGNEMENT_PARTIEL":  "🟡",
    "STRUCTURE_NAISSANTE": "🔵",
    "CONFLIT_STRUCTURE":   "🔴",
    "CONFLIT_DIRECT":      "⚠️",
    "NEUTRE":              "⚪",
}

INTEREST_COLOR = {
    "IGNORE":              "⚪",
    "WATCH_ZONE":          "🔵",
    "STRUCTURE_BUILDING":  "🟡",
    "TACTICAL_READY":      "🟠",
    "SIGNAL_VALIDATED":    "🔴",
}


# =====================================================================
# STRUCTURES DE DONNÉES
# =====================================================================

@dataclass
class Bar:
    bar_time: str
    values: Dict[str, Optional[float]]

@dataclass
class NormalizedSlope:
    symbol: str
    timeframe: int
    devise: str
    bars_used: int
    start_time: str
    end_time: str
    first_value: float
    last_value: float
    delta_total: float
    slope_per_bar: float
    raw_angle: float
    normalized_angle: float
    direction: str
    class_raw: str
    class_normalized: str
    tf_role: str
    note: str

@dataclass
class TFReading:
    tf: int
    tf_label: str
    group: str
    scene_type: str
    interest: str
    interest_rank: int
    confidence: int
    leader: Optional[str]
    weight: float
    has_data: bool
    note: str

@dataclass
class AlignmentResult:
    symbol: str
    timeframes_analyzed: List[int]
    tf_readings: List[TFReading]
    verdict: str
    alignment_score: float          # 0.0 a 1.0
    dominant_scene: Optional[str]
    dominant_leader: Optional[str]
    dominant_group: str             # COURT / MOYEN / LONG
    conflict_tfs: List[str]
    aligned_tfs: List[str]
    neutral_tfs: List[str]
    interest_level: str             # interet global Cockpit
    short_term_direction: Optional[str]
    medium_term_direction: Optional[str]
    long_term_direction: Optional[str]
    action: str
    note: str

    def to_dict(self) -> Dict:
        return asdict(self)


# =====================================================================
# UTILS BDD
# =====================================================================

def connect(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB introuvable: {db_path}")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
    return cur.fetchone() is not None

def get_available_devises(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("PRAGMA table_info(force_snapshots)")
    cols = {row[1] for row in cur.fetchall()}
    return [d for d in ALL_DEVISES if f"force_{d}" in cols]

def get_available_symbols(conn: sqlite3.Connection) -> List[str]:
    cur = conn.execute("SELECT DISTINCT symbol FROM force_snapshots ORDER BY symbol")
    return [str(r[0]) for r in cur.fetchall()]

def get_available_timeframes(conn: sqlite3.Connection, symbol: str) -> List[int]:
    cur = conn.execute(
        "SELECT DISTINCT timeframe FROM force_snapshots WHERE symbol=? ORDER BY timeframe",
        (symbol,),
    )
    return [int(r[0]) for r in cur.fetchall()]

def latest_snapshot(conn: sqlite3.Connection, symbol: str, timeframe: int) -> Optional[str]:
    cur = conn.execute(
        "SELECT MAX(datetime(created_at)) FROM force_snapshots WHERE symbol=? AND timeframe=?",
        (symbol, timeframe),
    )
    row = cur.fetchone()
    return row[0] if row and row[0] else None

def count_rows(conn: sqlite3.Connection, symbol: str, timeframe: int) -> int:
    cur = conn.execute(
        "SELECT COUNT(*) FROM force_snapshots WHERE symbol=? AND timeframe=?",
        (symbol, timeframe),
    )
    return int(cur.fetchone()[0])

def fetch_bars(
    conn: sqlite3.Connection,
    symbol: str,
    timeframe: int,
    devises: Sequence[str],
    limit: int,
) -> List[Bar]:
    select_cols = [f"force_{d} AS {d}" for d in devises]
    sql = f"""
        SELECT created_at AS bar_time, {', '.join(select_cols)}
        FROM force_snapshots
        WHERE symbol = ?
          AND timeframe = ?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
    """
    cur = conn.execute(sql, (symbol, timeframe, limit))
    rows = cur.fetchall()
    bars = []
    for row in reversed(rows):
        values = {d: row[d] for d in devises}
        bars.append(Bar(bar_time=row["bar_time"], values=values))
    return bars


# =====================================================================
# LOGIQUE 1 : PENTE NORMALISÉE (L'Ancien detect_tf_normalizer)
# =====================================================================

def linear_slope(values: Sequence[float]) -> float:
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    num = 0.0
    den = 0.0
    for i, y in enumerate(values):
        dx = i - x_mean
        num += dx * (y - y_mean)
        den += dx * dx
    if den == 0:
        return 0.0
    return num / den

def raw_angle_from_slope(slope: float) -> float:
    return math.degrees(math.atan(slope / 10.0))

def classify_angle(abs_angle: float, tf: int) -> str:
    profile = TF_PROFILE.get(tf, TF_PROFILE[15])
    if abs_angle < profile["noise_deg"]:
        return "BRUIT"
    if abs_angle < profile["micro_deg"]:
        return "MICRO"
    if abs_angle < profile["signal_deg"]:
        return "SIGNAL"
    if abs_angle < profile["structure_deg"]:
        return "STRUCTURE"
    return "IMPULSION"

def tf_role(tf: int) -> str:
    if tf == 1:
        return "MICROFILM_VIVANT"
    if tf == 5:
        return "FRACTALE_TACTIQUE"
    if tf == 15:
        return "FRACTALE_SCENARIO"
    if tf in (30, 60):
        return "STRUCTURE_SUPERIEURE"
    return "GRAVITE_HTF"

def normalize_one(
    symbol: str,
    tf: int,
    devise: str,
    bars: Sequence[Bar],
) -> Optional[NormalizedSlope]:
    values_with_time: List[Tuple[str, float]] = []
    for bar in bars:
        value = bar.values.get(devise)
        if value is not None:
            values_with_time.append((bar.bar_time, float(value)))

    if len(values_with_time) < 3:
        return None

    values = [v for _, v in values_with_time]
    slope = linear_slope(values)
    raw_angle = raw_angle_from_slope(slope)
    profile = TF_PROFILE.get(tf, TF_PROFILE[15])
    normalized_angle = raw_angle * profile["weight"]
    delta_total = values[-1] - values[0]

    if abs(normalized_angle) < profile["noise_deg"]:
        direction = "PLATE"
    elif normalized_angle > 0:
        direction = "HAUT"
    else:
        direction = "BAS"

    class_raw = classify_angle(abs(raw_angle), tf)
    class_norm = classify_angle(abs(normalized_angle), tf)
    note = (
        f"{devise.upper()} {TF_NAME.get(tf, 'M'+str(tf))}: "
        f"angle brut {raw_angle:+.2f} deg -> normalise {normalized_angle:+.2f} deg | "
        f"{class_norm} | delta {delta_total:+.2f} pts/{len(values)}b"
    )

    return NormalizedSlope(
        symbol=symbol,
        timeframe=tf,
        devise=devise,
        bars_used=len(values),
        start_time=values_with_time[0][0],
        end_time=values_with_time[-1][0],
        first_value=values[0],
        last_value=values[-1],
        delta_total=delta_total,
        slope_per_bar=slope,
        raw_angle=raw_angle,
        normalized_angle=normalized_angle,
        direction=direction,
        class_raw=class_raw,
        class_normalized=class_norm,
        tf_role=tf_role(tf),
        note=note,
    )


# =====================================================================
# LOGIQUE 2 : ALIGNEMENT MULTI-TF (L'Ancien tf_alignment)
# =====================================================================

def get_last_scene(
    symbol: str,
    tf: int,
    db_path: str,
    bars: int,
    devises_arg: str,
) -> Optional[Dict]:
    """Appelle pf_engine_scenes et retourne la derniere scene produite pour ce TF."""
    try:
        scenes = scene_engine.produce_scene_report(
            symbol=symbol,
            tf=tf,
            db_path=db_path,
            bars=bars,
            devises_arg=devises_arg,
            only_interest=False,
            verbose=False,
        )
        if not scenes:
            return None
        return scenes[-1]
    except Exception as e:
        return {"_error": str(e)}


def build_tf_reading(symbol: str, tf: int, db_path: str, bars: int, devises_arg: str) -> TFReading:
    label = TF_LABELS.get(tf, f"M{tf}")
    group = TF_GROUP.get(tf, "LONG")
    weight = TF_WEIGHT.get(tf, 1.0)

    scene = get_last_scene(symbol, tf, db_path, bars, devises_arg)

    if scene is None or "_error" in (scene or {}):
        return TFReading(
            tf=tf, tf_label=label, group=group,
            scene_type="NO_DATA", interest="IGNORE", interest_rank=0,
            confidence=0, leader=None, weight=weight,
            has_data=False,
            note=str((scene or {}).get("_error", "pas de donnees")),
        )

    scene_type  = scene.get("scene_type", "UNKNOWN")
    interest    = scene.get("interest", "IGNORE")
    confidence  = int(scene.get("confidence", 0))
    leader      = scene.get("leader")
    note        = scene.get("note", "")

    return TFReading(
        tf=tf, tf_label=label, group=group,
        scene_type=scene_type,
        interest=interest,
        interest_rank=INTEREST_RANK.get(interest, 0),
        confidence=confidence,
        leader=leader,
        weight=weight,
        has_data=True,
        note=note,
    )

def _direction_from_scene(reading: TFReading) -> Optional[str]:
    if not reading.has_data or reading.scene_type in SCENES_NEUTRES:
        return None
    if reading.scene_type in SCENES_DIRECTIONNELLES and reading.leader:
        return f"LEADER:{reading.leader.upper()}"
    return None

def _group_readings(readings: List[TFReading]) -> Dict[str, List[TFReading]]:
    groups: Dict[str, List[TFReading]] = {"MICRO": [], "COURT": [], "MOYEN": [], "LONG": []}
    for r in readings:
        g = r.group
        if g in groups:
            groups[g].append(r)
    return groups

def _dominant_leader(readings: List[TFReading]) -> Optional[str]:
    from collections import Counter
    leaders = [r.leader for r in readings if r.has_data and r.leader]
    if not leaders:
        return None
    return Counter(leaders).most_common(1)[0][0]

def _weighted_interest(readings: List[TFReading]) -> float:
    total_weight = sum(r.weight for r in readings if r.has_data)
    if total_weight == 0:
        return 0.0
    weighted = sum(r.interest_rank * r.weight for r in readings if r.has_data)
    return weighted / total_weight

def _scene_consistency(readings: List[TFReading]) -> Tuple[float, List[str], List[str], List[str]]:
    active = [r for r in readings if r.has_data and r.scene_type not in ("NO_DATA",)]
    if not active:
        return 0.0, [], [], []

    directional = [r for r in active if r.scene_type in SCENES_DIRECTIONNELLES]
    neutral_r   = [r for r in active if r.scene_type in SCENES_NEUTRES]

    from collections import Counter
    leader_counts = Counter(r.leader for r in directional if r.leader)
    dominant = leader_counts.most_common(1)[0][0] if leader_counts else None

    aligned   = []
    conflicted = []
    neutral_l  = [r.tf_label for r in neutral_r]

    for r in directional:
        if dominant and r.leader == dominant:
            aligned.append(r.tf_label)
        elif r.leader and r.leader != dominant:
            conflicted.append(r.tf_label)
        else:
            aligned.append(r.tf_label)

    total_w = sum(r.weight for r in active)
    aligned_w = sum(r.weight for r in active if r.tf_label in aligned)
    score = aligned_w / total_w if total_w > 0 else 0.0

    return round(score, 3), aligned, conflicted, neutral_l

def _build_verdict(
    readings: List[TFReading],
    alignment_score: float,
    groups: Dict[str, List[TFReading]],
    conflict_tfs: List[str],
    aligned_tfs: List[str],
) -> str:
    active = [r for r in readings if r.has_data]
    if len(active) < 2:
        return "NEUTRE"

    court  = [r for r in groups.get("COURT", [])  if r.has_data]
    moyen  = [r for r in groups.get("MOYEN", [])  if r.has_data]
    long_g = [r for r in groups.get("LONG", [])   if r.has_data]

    has_court = len(court) > 0
    has_long  = len(long_g) > 0

    if conflict_tfs and alignment_score < 0.4:
        court_leaders = set(r.leader for r in court if r.leader)
        long_leaders  = set(r.leader for r in long_g if r.leader)
        if court_leaders and long_leaders and court_leaders.isdisjoint(long_leaders):
            return "CONFLIT_STRUCTURE"
        return "CONFLIT_DIRECT"

    if alignment_score >= 0.80 and len(aligned_tfs) >= 2:
        return "ALIGNEMENT_COMPLET"

    if alignment_score >= 0.60:
        return "ALIGNEMENT_PARTIEL"

    if has_court and not has_long:
        court_directional = [r for r in court if r.scene_type in SCENES_DIRECTIONNELLES]
        if len(court_directional) >= 1:
            return "STRUCTURE_NAISSANTE"

    if has_court and has_long:
        court_scenes = set(r.scene_type for r in court if r.scene_type in SCENES_DIRECTIONNELLES)
        long_scenes  = set(r.scene_type for r in long_g)
        if court_scenes and all(s in SCENES_NEUTRES for s in long_scenes):
            return "STRUCTURE_NAISSANTE"

    return "NEUTRE"

def _interest_from_verdict(verdict: str, weighted_interest: float) -> str:
    if verdict == "ALIGNEMENT_COMPLET" and weighted_interest >= 3.0:
        return "SIGNAL_VALIDATED"
    if verdict == "ALIGNEMENT_COMPLET" and weighted_interest >= 2.0:
        return "TACTICAL_READY"
    if verdict == "ALIGNEMENT_PARTIEL" and weighted_interest >= 2.5:
        return "TACTICAL_READY"
    if verdict in ("ALIGNEMENT_PARTIEL", "STRUCTURE_NAISSANTE") and weighted_interest >= 1.5:
        return "STRUCTURE_BUILDING"
    if verdict == "STRUCTURE_NAISSANTE":
        return "WATCH_ZONE"
    if verdict in ("CONFLIT_STRUCTURE", "CONFLIT_DIRECT"):
        return "WATCH_ZONE"
    return "IGNORE"

def _action_from_verdict(verdict: str, interest: str, dominant_leader: Optional[str], dominant_group: str) -> str:
    leader_txt = f"{dominant_leader} " if dominant_leader else ""
    if verdict == "ALIGNEMENT_COMPLET":
        return f"Flux {leader_txt}aligne sur plusieurs TF. Chercher timing tactique sur M5/M15."
    if verdict == "ALIGNEMENT_PARTIEL":
        return f"Majorite alignee {leader_txt}— attendre TF retardataire pour confirmer."
    if verdict == "STRUCTURE_NAISSANTE":
        return f"Structure visible sur TF courts ({dominant_group}). Attendre confirmation TF moyen/long."
    if verdict == "CONFLIT_STRUCTURE":
        return "Conflit TF courts vs longs. Ne pas agir. Attendre resolution structurelle."
    if verdict == "CONFLIT_DIRECT":
        return "Conflit entre TF actifs. Patience — ne pas forcer une direction."
    return "Pas de structure exploitable. Observer."

def _direction_by_group(
    groups: Dict[str, List[TFReading]],
    dominant_leader: Optional[str],
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    def group_leader(group_key: str) -> Optional[str]:
        tfs = [r for r in groups.get(group_key, []) if r.has_data and r.leader]
        if not tfs:
            return None
        from collections import Counter
        return Counter(r.leader for r in tfs).most_common(1)[0][0]

    court_dir = group_leader("COURT") or group_leader("MICRO")
    moyen_dir = group_leader("MOYEN")
    long_dir  = group_leader("LONG")
    return court_dir, moyen_dir, long_dir

def detect_tf_alignment(
    symbol: str,
    timeframes: List[int],
    db_path: str = "powerflow.db",
    bars: int = 25,
    devises_arg: str = "eur,gbp,usd",
) -> AlignmentResult:
    readings: List[TFReading] = []
    for tf in sorted(timeframes):
        reading = build_tf_reading(symbol, tf, db_path, bars, devises_arg)
        readings.append(reading)

    groups = _group_readings(readings)
    alignment_score, aligned_tfs, conflict_tfs, neutral_tfs = _scene_consistency(readings)
    weighted_int = _weighted_interest(readings)
    dominant_leader = _dominant_leader(readings)

    active = [r for r in readings if r.has_data and r.scene_type not in SCENES_NEUTRES]
    if active:
        best = max(active, key=lambda r: r.confidence * r.weight)
        dominant_scene = best.scene_type
        dominant_group = best.group
    else:
        dominant_scene = None
        dominant_group = "NEUTRE"

    verdict = _build_verdict(readings, alignment_score, groups, conflict_tfs, aligned_tfs)
    interest_level = _interest_from_verdict(verdict, weighted_int)
    action = _action_from_verdict(verdict, interest_level, dominant_leader, dominant_group)
    court_dir, moyen_dir, long_dir = _direction_by_group(groups, dominant_leader)

    nb_active = sum(1 for r in readings if r.has_data)
    note = (
        f"{nb_active}/{len(readings)} TF actifs | "
        f"score={alignment_score:.2f} | "
        f"interet_pondere={weighted_int:.1f} | "
        f"aligne=[{','.join(aligned_tfs)}] conflit=[{','.join(conflict_tfs)}]"
    )

    return AlignmentResult(
        symbol=symbol.upper(),
        timeframes_analyzed=sorted(timeframes),
        tf_readings=readings,
        verdict=verdict,
        alignment_score=alignment_score,
        dominant_scene=dominant_scene,
        dominant_leader=dominant_leader,
        dominant_group=dominant_group,
        conflict_tfs=conflict_tfs,
        aligned_tfs=aligned_tfs,
        neutral_tfs=neutral_tfs,
        interest_level=interest_level,
        short_term_direction=court_dir,
        medium_term_direction=moyen_dir,
        long_term_direction=long_dir,
        action=action,
        note=note,
    )


# =====================================================================
# AFFICHAGE ET EXECUTION
# =====================================================================

def render_alignment(result: AlignmentResult, verbose: bool = False) -> str:
    lines = []
    lines.append("=" * 70)
    lines.append(f"🧬 PowerFlow V6 — Alignement Multi-Timeframe")
    lines.append(f"   {result.symbol} | TF: {[TF_LABELS.get(t, str(t)) for t in result.timeframes_analyzed]}")
    lines.append("=" * 70)
    lines.append("")

    v_icon = VERDICT_COLOR.get(result.verdict, "⚪")
    i_icon = INTEREST_COLOR.get(result.interest_level, "⚪")
    lines.append(f"  {v_icon} Verdict     : {result.verdict}")
    lines.append(f"  {i_icon} Interet     : {result.interest_level}")
    lines.append(f"  📊 Score       : {result.alignment_score:.0%}")
    lines.append(f"  🎬 Scene dom.  : {result.dominant_scene or 'aucune'}")
    lines.append(f"  👑 Leader dom. : {result.dominant_leader or 'aucun'}")
    lines.append("")

    lines.append("  HORIZONS :")
    lines.append(f"    Court  terme : {result.short_term_direction  or '—'}")
    lines.append(f"    Moyen  terme : {result.medium_term_direction or '—'}")
    lines.append(f"    Long   terme : {result.long_term_direction   or '—'}")
    lines.append("")

    lines.append("  GRILLE MULTI-TF :")
    lines.append(f"  {'TF':<6} {'Groupe':<7} {'Scene':<25} {'Interet':<20} {'Conf':>4} {'Leader':<8}")
    lines.append("  " + "-" * 74)
    for r in result.tf_readings:
        if not r.has_data:
            lines.append(f"  {r.tf_label:<6} {r.group:<7} {'[pas de données]':<25} {'—':<20} {'—':>4} {'—':<8}")
        else:
            i_ic = INTEREST_COLOR.get(r.interest, "⚪")
            lines.append(
                f"  {r.tf_label:<6} {r.group:<7} {r.scene_type:<25} "
                f"{i_ic} {r.interest:<18} {r.confidence:>3}% {r.leader or '—':<8}"
            )
    lines.append("")

    if result.aligned_tfs:
        lines.append(f"  ✅ Alignes  : {', '.join(result.aligned_tfs)}")
    if result.conflict_tfs:
        lines.append(f"  ⚠️  Conflits : {', '.join(result.conflict_tfs)}")
    if result.neutral_tfs:
        lines.append(f"  ⚪ Neutres  : {', '.join(result.neutral_tfs)}")
    lines.append("")
    lines.append(f"  🎯 Action : {result.action}")
    lines.append("")
    if verbose:
        lines.append(f"  📝 Note   : {result.note}")
        lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def print_header(title: str) -> None:
    print("=" * 88)
    print(title)
    print("=" * 88)

def print_result(r: NormalizedSlope) -> None:
    tf_label = TF_NAME.get(r.timeframe, f"M{r.timeframe}")
    print(
        f"{tf_label:<4} | {r.tf_role:<18} | {r.devise.upper():<3} | "
        f"{r.direction:<5} | brut={r.raw_angle:+6.2f} deg {r.class_raw:<9} | "
        f"norm={r.normalized_angle:+6.2f} deg {r.class_normalized:<9} | "
        f"delta={r.delta_total:+6.2f} | {r.bars_used:>2}b | {r.start_time[11:16]}->{r.end_time[11:16]}"
    )

def run_normalizer(db_path: str, symbol: str, timeframes: Sequence[int], devises: Sequence[str], bars_limit: int) -> int:
    conn = connect(db_path)
    try:
        if not table_exists(conn, "force_snapshots"):
            raise RuntimeError("Table force_snapshots introuvable")

        available_devises = get_available_devises(conn)
        if not available_devises:
            raise RuntimeError("Aucune colonne force_* exploitable")

        available_symbols = get_available_symbols(conn)
        if symbol not in available_symbols:
            print(f"Symbole indisponible: {symbol}")
            return 2

        selected_devises = [d for d in devises if d in available_devises]
        available_tfs = get_available_timeframes(conn, symbol)
        selected_tfs = [tf for tf in timeframes if tf in available_tfs]

        print_header("PowerFlow V5/6 — TF Normalizer")
        
        if not selected_tfs:
            print("Aucun timeframe exploitable pour ce symbole.")
            return 3

        total_results = 0
        for tf in selected_tfs:
            latest = latest_snapshot(conn, symbol, tf)
            total = count_rows(conn, symbol, tf)
            profile = TF_PROFILE.get(tf, TF_PROFILE[15])
            fetch_limit = max(int(profile["window"]), min(bars_limit, total))
            fetch_limit = min(fetch_limit, bars_limit)
            bars = fetch_bars(conn, symbol, tf, selected_devises, fetch_limit)

            print_header(f"{symbol} {TF_NAME.get(tf, 'M'+str(tf))} | lignes={total} | latest={latest} | window={len(bars)}")
            if len(bars) < 3:
                continue

            results: List[NormalizedSlope] = []
            for devise in selected_devises:
                r = normalize_one(symbol, tf, devise, bars)
                if r is not None:
                    results.append(r)

            results.sort(key=lambda x: abs(x.normalized_angle), reverse=True)
            for r in results:
                print_result(r)
                total_results += 1
            print()

        return 0 if total_results else 4
    finally:
        conn.close()

def parse_timeframes(raw: str) -> List[int]:
    out = []
    for part in raw.split(","):
        part = part.strip().upper().replace("M", "")
        if part == "H1":
            out.append(60)
        elif part == "H4":
            out.append(240)
        elif part:
            out.append(int(part))
    return out

def parse_devises(raw: str) -> List[str]:
    return [p.strip().lower() for p in raw.split(",") if p.strip()]

def main() -> None:
    parser = argparse.ArgumentParser(description="PowerFlow V6 — Normalizer & Alignment")
    subparsers = parser.add_subparsers(dest="command", help="Commande a executer: 'align' ou 'norm'")
    
    # Commande Alignment
    parser_align = subparsers.add_parser("align", help="Alignement Multi-Timeframe")
    parser_align.add_argument("symbol", help="Symbole ex: GBPUSD")
    parser_align.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")
    parser_align.add_argument("--timeframes", default="5,15,30,60,240", help="Ex: 5,15,30,60,240")
    parser_align.add_argument("--devises", default="eur,gbp,usd", help="Ex: eur,gbp,usd")
    parser_align.add_argument("--bars", type=int, default=25, help="Bougies a analyser par TF")
    parser_align.add_argument("--verbose", action="store_true", help="Affichage detaille")
    parser_align.add_argument("--json", action="store_true", help="Sortie JSON brute")

    # Commande Normalizer
    parser_norm = subparsers.add_parser("norm", help="Pondération mathématique des angles")
    parser_norm.add_argument("--symbol", default="GBPUSD", help="Symbole ex: GBPUSD")
    parser_norm.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")
    parser_norm.add_argument("--timeframes", default="1,5,15", help="Ex: 1,5,15")
    parser_norm.add_argument("--devises", default=",".join(ALL_DEVISES), help="Devises ex: gbp,usd,eur")
    parser_norm.add_argument("--bars", type=int, default=30, help="Maximum de bougies recentes par TF")

    args = parser.parse_args()

    if args.command == "align":
        tfs = parse_timeframes(args.timeframes)
        result = detect_tf_alignment(
            symbol=args.symbol,
            timeframes=tfs,
            db_path=args.db,
            bars=args.bars,
            devises_arg=args.devises,
        )
        if args.json:
            print(json.dumps(result.to_dict(), indent=2, ensure_ascii=False))
        else:
            print(render_alignment(result, verbose=args.verbose))

    elif args.command == "norm":
        run_normalizer(
            db_path=args.db,
            symbol=args.symbol.upper(),
            timeframes=parse_timeframes(args.timeframes),
            devises=parse_devises(args.devises),
            bars_limit=max(3, args.bars),
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
