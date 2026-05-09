"""
PowerFlow V5+ - detect_relations_v5.py
Mission 5A : lecture relationnelle des devises.

Role :
- Lire les relations entre courbes de force, sans modifier les fichiers existants.
- Detecter coalitions multiples, oppositions angulaires, reactions differees,
  distances, leader/follower, puis choisir la relation dominante.
- Rester compatible SQLite direct et DB force_snapshots.

Philosophie :
- detect_v5_core.py mesure les courbes individuellement.
- detect_relations_v5.py lit la bataille entre les courbes.

Execution :
    python detect_relations_v5.py GBPUSD 15 --db powerflow.db --bars 20
    python detect_relations_v5.py GBPUSD 1 --db powerflow.db --bars 50 --devises eur,gbp,usd
    python detect_relations_v5.py GBPUSD 60 --db powerflow.db --bars 30 --devises all
"""

from __future__ import annotations

import argparse
import itertools
import math
import sqlite3
from dataclasses import dataclass, asdict
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

DB_PATH = "powerflow.db"
ALL_DEVISES = ["gbp", "usd", "eur", "jpy", "cad", "chf", "aud", "nzd"]
DEFAULT_FOCUS = ["eur", "gbp", "usd"]

# Timeframes en minutes. Ajout D1/W1 pour compatibilite future.
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

TF_WINDOWS = {
    1: 10,
    5: 15,
    15: 20,
    30: 25,
    60: 30,
    240: 50,
    1440: 60,
    10080: 80,
}

# Seuils simples, volontairement lisibles.
ANGLE_MIN_DIRECT = 1.0
ANGLE_STRONG = 3.0
ANGLE_VERY_STRONG = 5.0
COALITION_MAX_ANGLE_DIFF_STRONG = 3.0
COALITION_MAX_ANGLE_DIFF_MEDIUM = 7.0
DELAY_MAX_BARS = 3
DISTANCE_STABLE_STD = 3.0
DISTANCE_STRETCH_DELTA = 6.0


@dataclass
class Relation:
    relation_type: str
    quality: str
    score: int
    bar_time: str
    symbol: str
    tf: int
    devises: List[str]
    leader: Optional[str]
    reaction: Optional[str]
    confirmation: Optional[str]
    delay_bars: int
    angle_map: Dict[str, Optional[float]]
    zone_map: Dict[str, str]
    note: str

    def to_dict(self) -> Dict:
        return asdict(self)


def tf_label(tf: int) -> str:
    return TF_LABELS.get(tf, f"M{tf}")


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


def get_relation_rows(
    conn: sqlite3.Connection,
    symbol: str,
    tf: int,
    end_bar: Optional[str],
    bars: int,
    devises: Sequence[str],
) -> Tuple[List[Tuple], List[Tuple[str, str]]]:
    """
    Lit les barres force_snapshots pour un symbole/timeframe.
    Retour : rows = [(bar_time, force_dev1, force_dev2, ...), ...]
    """
    if not devises:
        return [], []

    cols = [(d, f"force_{d}") for d in devises]
    select_cols = ",\n               ".join([f"AVG({col}) AS {dev}" for dev, col in cols])
    not_null_guard = " AND ".join([f"{col} IS NOT NULL" for _dev, col in cols[:3]])
    if not not_null_guard:
        not_null_guard = "1=1"

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


def _series(rows: Sequence[Tuple], col_idx: int, start: int, end: int) -> List[float]:
    start = max(0, start)
    end = min(len(rows) - 1, end)
    if start > end:
        return []
    values: List[float] = []
    for i in range(start, end + 1):
        v = rows[i][col_idx]
        if v is not None:
            values.append(float(v))
    return values


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
        return {"devise": devise.upper(), "status": "N/A", "angle": None, "slope": None, "direction": "N/A", "note": "devise indisponible"}
    w = int(window or TF_WINDOWS.get(tf, 20))
    vals = _series(rows, idx, bar_index - w + 1, bar_index)
    if len(vals) < 3:
        return {"devise": devise.upper(), "status": "N/A", "angle": None, "slope": None, "direction": "N/A", "note": f"pas assez de donnees ({len(vals)})"}
    sl = _slope(vals)
    if sl is None:
        return {"devise": devise.upper(), "status": "N/A", "angle": None, "slope": None, "direction": "N/A", "note": "slope N/A"}
    angle = _angle_from_slope(sl)
    if abs(angle) < 0.5:
        direction = "PLATE"
    elif angle > 0:
        direction = "HAUT"
    else:
        direction = "BAS"
    return {
        "devise": devise.upper(),
        "status": "OK",
        "angle": round(angle, 2),
        "slope": round(sl, 4),
        "direction": direction,
        "delta": round(vals[-1] - vals[0], 2),
        "window": len(vals),
        "note": f"{devise.upper()} angle {angle:+.2f} sur {len(vals)}b",
    }


def current_value(devise: str, rows: Sequence[Tuple], bar_index: int, devise_cols: Sequence[Tuple[str, str]]) -> Optional[float]:
    idx = _col_idx(devise, devise_cols)
    if idx is None or bar_index >= len(rows):
        return None
    v = rows[bar_index][idx]
    return None if v is None else float(v)


def zone_label(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    if value >= 85:
        return "EXTREME_HAUT"
    if value >= 70:
        return "HAUT"
    if value >= 55:
        return "MEDIANE_HAUTE"
    if value >= 45:
        return "CENTRE"
    if value >= 30:
        return "MEDIANE_BASSE"
    if value >= 15:
        return "BAS"
    return "EXTREME_BAS"


def angle_map_for(devises: Sequence[str], rows: Sequence[Tuple], bar_index: int, tf: int, devise_cols: Sequence[Tuple[str, str]]) -> Dict[str, Optional[float]]:
    result: Dict[str, Optional[float]] = {}
    for d in devises:
        a = calc_angle(d, rows, bar_index, tf, devise_cols)
        result[d.upper()] = a.get("angle")
    return result


def zone_map_for(devises: Sequence[str], rows: Sequence[Tuple], bar_index: int, devise_cols: Sequence[Tuple[str, str]]) -> Dict[str, str]:
    return {d.upper(): zone_label(current_value(d, rows, bar_index, devise_cols)) for d in devises}


def _sign(angle: Optional[float]) -> int:
    if angle is None or abs(angle) < 0.5:
        return 0
    return 1 if angle > 0 else -1


def _quality_from_score(score: int) -> str:
    if score >= 75:
        return "FORTE"
    if score >= 55:
        return "MOYENNE"
    if score >= 35:
        return "FAIBLE"
    return "N/A"


def detect_all_coalitions(
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    devises: Optional[Sequence[str]] = None,
) -> List[Relation]:
    """
    Teste toutes les coalitions A+B vs C.
    Par defaut : les devises fournies dans devise_cols.
    """
    available = [d for d, _c in devise_cols]
    scope = [d.lower() for d in (devises or available) if d.lower() in available]
    if len(scope) < 3:
        return []

    bar_time = str(rows[bar_index][0])
    relations: List[Relation] = []

    for contre in scope:
        allies = [d for d in scope if d != contre]
        for a, b in itertools.combinations(allies, 2):
            pa = calc_angle(a, rows, bar_index, tf, devise_cols)
            pb = calc_angle(b, rows, bar_index, tf, devise_cols)
            pc = calc_angle(contre, rows, bar_index, tf, devise_cols)
            aa, ab, ac = pa.get("angle"), pb.get("angle"), pc.get("angle")
            if aa is None or ab is None or ac is None:
                continue

            sign_a, sign_b, sign_c = _sign(aa), _sign(ab), _sign(ac)
            same_allies = sign_a != 0 and sign_a == sign_b
            opposed = same_allies and sign_c == -sign_a
            if not opposed:
                continue

            angle_diff = abs(aa - ab)
            ally_power = (abs(aa) + abs(ab)) / 2.0
            contre_power = abs(ac)
            score = 30
            score += min(25, int(ally_power * 4))
            score += min(20, int(contre_power * 3))
            if angle_diff <= COALITION_MAX_ANGLE_DIFF_STRONG:
                score += 20
            elif angle_diff <= COALITION_MAX_ANGLE_DIFF_MEDIUM:
                score += 10
            else:
                score -= 10
            score = max(0, min(100, score))
            quality = _quality_from_score(score)

            zmap = zone_map_for([a, b, contre], rows, bar_index, devise_cols)
            amap = {a.upper(): round(aa, 2), b.upper(): round(ab, 2), contre.upper(): round(ac, 2)}
            note = (
                f"{a.upper()}+{b.upper()} synchronisees ({aa:+.1f}/{ab:+.1f}) "
                f"contre {contre.upper()} ({ac:+.1f}) | ecart allies {angle_diff:.1f}"
            )
            relations.append(
                Relation(
                    relation_type="COALITION_PUSH",
                    quality=quality,
                    score=score,
                    bar_time=bar_time,
                    symbol="",
                    tf=tf,
                    devises=[a.upper(), b.upper(), contre.upper()],
                    leader=max([a, b, contre], key=lambda d: abs(amap[d.upper()])).upper(),
                    reaction=contre.upper(),
                    confirmation=None,
                    delay_bars=0,
                    angle_map=amap,
                    zone_map=zmap,
                    note=note,
                )
            )

    relations.sort(key=lambda r: r.score, reverse=True)
    return relations


def _zone_rejection_bonus(devise: str, angle: float, rows: Sequence[Tuple], bar_index: int, devise_cols: Sequence[Tuple[str, str]]) -> Tuple[int, str]:
    value = current_value(devise, rows, bar_index, devise_cols)
    z = zone_label(value)
    if z in ("HAUT", "EXTREME_HAUT") and angle < -ANGLE_MIN_DIRECT:
        return 15, f"{devise.upper()} rejet haut"
    if z in ("BAS", "EXTREME_BAS") and angle > ANGLE_MIN_DIRECT:
        return 15, f"{devise.upper()} rebond bas"
    return 0, ""


def detect_opposition_angle(
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    devises: Optional[Sequence[str]] = None,
    max_delay_bars: int = DELAY_MAX_BARS,
) -> List[Relation]:
    """
    Detecte les oppositions angulaires directes ou differees.
    Directe : angles actuels opposes.
    Differee : angle A fort il y a 1-3 bougies, angle B oppose maintenant.
    """
    available = [d for d, _c in devise_cols]
    scope = [d.lower() for d in (devises or available) if d.lower() in available]
    if len(scope) < 2:
        return []

    bar_time = str(rows[bar_index][0])
    relations: List[Relation] = []

    for a, b in itertools.combinations(scope, 2):
        pa = calc_angle(a, rows, bar_index, tf, devise_cols)
        pb = calc_angle(b, rows, bar_index, tf, devise_cols)
        aa, ab = pa.get("angle"), pb.get("angle")
        if aa is None or ab is None:
            continue
        if _sign(aa) * _sign(ab) == -1 and min(abs(aa), abs(ab)) >= ANGLE_MIN_DIRECT:
            score = 35 + min(25, int(min(abs(aa), abs(ab)) * 5)) + min(20, int(abs(abs(aa) - abs(ab)) <= 3) * 20)
            ba, na = _zone_rejection_bonus(a, aa, rows, bar_index, devise_cols)
            bb, nb = _zone_rejection_bonus(b, ab, rows, bar_index, devise_cols)
            score += ba + bb
            score = max(0, min(100, score))
            extras = "; ".join([x for x in (na, nb) if x])
            relation_type = "OPPOSITION_DIRECTE"
            if extras:
                relation_type = "OPPOSITION_REBALANCE"
            zmap = zone_map_for([a, b], rows, bar_index, devise_cols)
            amap = {a.upper(): round(aa, 2), b.upper(): round(ab, 2)}
            leader = a.upper() if abs(aa) >= abs(ab) else b.upper()
            reaction = b.upper() if leader == a.upper() else a.upper()
            note = f"{a.upper()} {aa:+.1f} vs {b.upper()} {ab:+.1f} | angles opposes"
            if extras:
                note += f" | {extras}"
            relations.append(
                Relation(
                    relation_type=relation_type,
                    quality=_quality_from_score(score),
                    score=score,
                    bar_time=bar_time,
                    symbol="",
                    tf=tf,
                    devises=[a.upper(), b.upper()],
                    leader=leader,
                    reaction=reaction,
                    confirmation=None,
                    delay_bars=0,
                    angle_map=amap,
                    zone_map=zmap,
                    note=note,
                )
            )

        # Reaction differee : A avant, B maintenant ou inversement.
        for delay in range(1, max_delay_bars + 1):
            past_idx = bar_index - delay
            if past_idx < 2:
                continue
            a_past = calc_angle(a, rows, past_idx, tf, devise_cols).get("angle")
            b_past = calc_angle(b, rows, past_idx, tf, devise_cols).get("angle")
            candidates = [
                (a, a_past, b, ab),
                (b, b_past, a, aa),
            ]
            for trigger, trig_angle, response, resp_angle in candidates:
                if trig_angle is None or resp_angle is None:
                    continue
                if abs(trig_angle) < ANGLE_STRONG or abs(resp_angle) < ANGLE_MIN_DIRECT:
                    continue
                if _sign(trig_angle) * _sign(resp_angle) != -1:
                    continue
                score = 45 + min(25, int(min(abs(trig_angle), abs(resp_angle)) * 5)) - (delay - 1) * 5
                bt, nt = _zone_rejection_bonus(trigger, trig_angle, rows, past_idx, devise_cols)
                br, nr = _zone_rejection_bonus(response, resp_angle, rows, bar_index, devise_cols)
                score += bt + br
                score = max(0, min(100, score))
                extras = "; ".join([x for x in (nt, nr) if x])
                zmap = zone_map_for([trigger, response], rows, bar_index, devise_cols)
                amap = {trigger.upper(): round(trig_angle, 2), response.upper(): round(resp_angle, 2)}
                note = (
                    f"{trigger.upper()} declenche {trig_angle:+.1f} puis {response.upper()} repond {resp_angle:+.1f} "
                    f"avec {delay} bougie(s) de retard"
                )
                if extras:
                    note += f" | {extras}"
                relations.append(
                    Relation(
                        relation_type="OPPOSITION_DIFFEREE",
                        quality=_quality_from_score(score),
                        score=score,
                        bar_time=bar_time,
                        symbol="",
                        tf=tf,
                        devises=[trigger.upper(), response.upper()],
                        leader=trigger.upper(),
                        reaction=response.upper(),
                        confirmation=None,
                        delay_bars=delay,
                        angle_map=amap,
                        zone_map=zmap,
                        note=note,
                    )
                )

    # Dedup : garder la meilleure relation par type/devise set/delay.
    best: Dict[Tuple, Relation] = {}
    for r in relations:
        key = (r.relation_type, tuple(sorted(r.devises)), r.delay_bars)
        if key not in best or r.score > best[key].score:
            best[key] = r
    result = list(best.values())
    result.sort(key=lambda r: r.score, reverse=True)
    return result


def detect_distance_behavior(
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    devises: Optional[Sequence[str]] = None,
) -> List[Relation]:
    """
    Lit la distance entre deux devises : parallele propre, convergence, divergence, tension.
    """
    available = [d for d, _c in devise_cols]
    scope = [d.lower() for d in (devises or available) if d.lower() in available]
    if len(scope) < 2:
        return []

    bar_time = str(rows[bar_index][0])
    relations: List[Relation] = []
    window = max(5, min(12, TF_WINDOWS.get(tf, 20) // 2))

    for a, b in itertools.combinations(scope, 2):
        ia = _col_idx(a, devise_cols)
        ib = _col_idx(b, devise_cols)
        if ia is None or ib is None:
            continue
        distances: List[float] = []
        start = max(0, bar_index - window + 1)
        for i in range(start, bar_index + 1):
            va, vb = rows[i][ia], rows[i][ib]
            if va is not None and vb is not None:
                distances.append(abs(float(va) - float(vb)))
        if len(distances) < 4:
            continue
        dist_delta = distances[-1] - distances[0]
        dist_std = float(np.std(distances))
        pa = calc_angle(a, rows, bar_index, tf, devise_cols)
        pb = calc_angle(b, rows, bar_index, tf, devise_cols)
        aa, ab = pa.get("angle"), pb.get("angle")
        if aa is None or ab is None:
            continue
        same_direction = _sign(aa) != 0 and _sign(aa) == _sign(ab)
        opposite_direction = _sign(aa) * _sign(ab) == -1

        relation_type = "DISTANCE_NEUTRE"
        score = 20
        if same_direction and dist_std <= DISTANCE_STABLE_STD:
            relation_type = "POSITIVE_DISTANCE_SYNC"
            score = 55 + min(20, int((DISTANCE_STABLE_STD - dist_std) * 6))
        elif dist_delta <= -DISTANCE_STRETCH_DELTA:
            relation_type = "CONVERGENCE"
            score = 45 + min(20, int(abs(dist_delta)))
        elif dist_delta >= DISTANCE_STRETCH_DELTA:
            relation_type = "DIVERGENCE_DISTANCE"
            score = 45 + min(20, int(abs(dist_delta)))
        elif opposite_direction and dist_std >= DISTANCE_STABLE_STD:
            relation_type = "DISTANCE_TENSION"
            score = 40 + min(20, int(dist_std))

        if relation_type == "DISTANCE_NEUTRE":
            continue
        score = max(0, min(100, score))
        zmap = zone_map_for([a, b], rows, bar_index, devise_cols)
        amap = {a.upper(): round(aa, 2), b.upper(): round(ab, 2)}
        note = (
            f"{a.upper()}/{b.upper()} distance {distances[0]:.1f}->{distances[-1]:.1f} "
            f"std={dist_std:.1f} | angles {aa:+.1f}/{ab:+.1f}"
        )
        relations.append(
            Relation(
                relation_type=relation_type,
                quality=_quality_from_score(score),
                score=score,
                bar_time=bar_time,
                symbol="",
                tf=tf,
                devises=[a.upper(), b.upper()],
                leader=a.upper() if abs(aa) >= abs(ab) else b.upper(),
                reaction=b.upper() if abs(aa) >= abs(ab) else a.upper(),
                confirmation=None,
                delay_bars=0,
                angle_map=amap,
                zone_map=zmap,
                note=note,
            )
        )

    relations.sort(key=lambda r: r.score, reverse=True)
    return relations


def detect_leader_follower(
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    devises: Optional[Sequence[str]] = None,
) -> Optional[Relation]:
    available = [d for d, _c in devise_cols]
    scope = [d.lower() for d in (devises or available) if d.lower() in available]
    if len(scope) < 2:
        return None

    angle_infos = []
    for d in scope:
        p = calc_angle(d, rows, bar_index, tf, devise_cols)
        a = p.get("angle")
        if a is not None:
            angle_infos.append((d, float(a)))
    if len(angle_infos) < 2:
        return None
    angle_infos.sort(key=lambda x: abs(x[1]), reverse=True)
    leader, leader_angle = angle_infos[0]
    followers = [d for d, a in angle_infos[1:] if _sign(a) == _sign(leader_angle) and abs(a) >= ANGLE_MIN_DIRECT]
    opposants = [d for d, a in angle_infos[1:] if _sign(a) == -_sign(leader_angle) and abs(a) >= ANGLE_MIN_DIRECT]
    if abs(leader_angle) < ANGLE_STRONG:
        return None

    score = 40 + min(30, int(abs(leader_angle) * 5)) + min(15, 5 * len(followers)) + min(15, 5 * len(opposants))
    score = max(0, min(100, score))
    devs = [leader.upper()] + [d.upper() for d in followers + opposants]
    amap = {d.upper(): round(a, 2) for d, a in angle_infos}
    zmap = zone_map_for(scope, rows, bar_index, devise_cols)
    note = f"Leader {leader.upper()} angle {leader_angle:+.1f} | suit: {','.join([d.upper() for d in followers]) or '-'} | oppose: {','.join([d.upper() for d in opposants]) or '-'}"
    return Relation(
        relation_type="LEADER_FOLLOWER",
        quality=_quality_from_score(score),
        score=score,
        bar_time=str(rows[bar_index][0]),
        symbol="",
        tf=tf,
        devises=devs,
        leader=leader.upper(),
        reaction=opposants[0].upper() if opposants else None,
        confirmation=followers[0].upper() if followers else None,
        delay_bars=0,
        angle_map=amap,
        zone_map=zmap,
        note=note,
    )


def detect_best_force_relation(
    rows: Sequence[Tuple],
    bar_index: int,
    tf: int,
    devise_cols: Sequence[Tuple[str, str]],
    symbol: str = "",
    devises: Optional[Sequence[str]] = None,
) -> Dict:
    """
    Orchestre les detecteurs relationnels et retourne la meilleure relation.
    """
    candidates: List[Relation] = []
    candidates.extend(detect_all_coalitions(rows, bar_index, tf, devise_cols, devises=devises))
    candidates.extend(detect_opposition_angle(rows, bar_index, tf, devise_cols, devises=devises))
    candidates.extend(detect_distance_behavior(rows, bar_index, tf, devise_cols, devises=devises))
    leader = detect_leader_follower(rows, bar_index, tf, devise_cols, devises=devises)
    if leader:
        candidates.append(leader)

    for c in candidates:
        c.symbol = symbol.upper()

    candidates.sort(key=lambda r: r.score, reverse=True)
    best = candidates[0] if candidates else None
    return {
        "best": best.to_dict() if best else None,
        "all": [c.to_dict() for c in candidates],
        "count": len(candidates),
    }


def relation_summary(relation: Optional[Dict]) -> str:
    if not relation:
        return "RELATION: aucune relation exploitable"
    devs = "+".join(relation.get("devises") or [])
    return (
        f"{relation['relation_type']} {relation['quality']} score={relation['score']} | "
        f"{devs} | leader={relation.get('leader') or '-'} reaction={relation.get('reaction') or '-'} | "
        f"{relation.get('note') or ''}"
    )


def produce_relations_report(
    symbol: str,
    tf: int,
    db_path: str = DB_PATH,
    bars: int = 30,
    devises_arg: str = "eur,gbp,usd",
    end_bar: Optional[str] = None,
    show_all: bool = False,
) -> List[Dict]:
    conn = sqlite3.connect(db_path)
    available = get_available_devises(conn)
    devises = normalize_devises_arg(devises_arg, available)
    rows, devise_cols = get_relation_rows(conn, symbol, tf, end_bar, bars, devises)
    conn.close()

    print("=" * 90)
    print(f"PowerFlow V5+ Relations - {symbol.upper()} {tf_label(tf)} | bars={len(rows)} | devises={','.join([d.upper() for d in devises])}")
    print("=" * 90)

    if len(rows) < 3:
        print("Pas assez de donnees pour lire les relations.")
        return []

    outputs: List[Dict] = []
    for i, row in enumerate(rows):
        rel = detect_best_force_relation(rows, i, tf, devise_cols, symbol=symbol, devises=devises)
        outputs.append({"bar_time": row[0], **rel})
        best = rel.get("best")
        print(f"[{row[0]}] {relation_summary(best)}")
        if show_all and rel.get("all"):
            for item in rel["all"][1:5]:
                print(f"  - {relation_summary(item)}")

    print("=" * 90)
    print("FIN RELATIONS")
    print("=" * 90)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="PowerFlow V5+ relation engine")
    parser.add_argument("symbol", help="Ex: GBPUSD")
    parser.add_argument("tf", type=int, help="Timeframe en minutes: 1,5,15,30,60,240,1440,10080")
    parser.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")
    parser.add_argument("--bars", type=int, default=30, help="Nombre de bougies a lire")
    parser.add_argument("--devises", default="eur,gbp,usd", help="Ex: eur,gbp,usd ou all")
    parser.add_argument("--end", default=None, help="Fin optionnelle: YYYY-MM-DD HH:MM")
    parser.add_argument("--show-all", action="store_true", help="Afficher aussi les relations secondaires")
    args = parser.parse_args()

    produce_relations_report(
        symbol=args.symbol,
        tf=args.tf,
        db_path=args.db,
        bars=args.bars,
        devises_arg=args.devises,
        end_bar=args.end,
        show_all=args.show_all,
    )


if __name__ == "__main__":
    main()
