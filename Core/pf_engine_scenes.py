#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V5+ - pf_engine_scenes.py
(Fusion de flow_scene_engine_v5, aggregate_v5 et regimes)

Mission 5B & 3 : Moteur de scenes Flow et d'Agrégation structurelle.

Role :
- Consommer pf_relations.py et pf_core_metrics.py.
- Lire les pf_events (nodes) si disponibles.
- Calculer le score unifié de la bougie (Agrégation).
- Transformer les relations de force en une scene dominante par bougie (Scenes).
- Produire une lecture propre : scene, cause, reponse, confirmation.
"""

from __future__ import annotations

import argparse
import os
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Sequence, Tuple

import pf_relations as relations
import pf_core_metrics as core

try:
    import pf_events as nodes_v6
except Exception:
    nodes_v6 = None

DB_PATH = "powerflow.db"

# --- CONSTANTES AJOUTÉES DEPUIS AGGREGATE ---
DEFAULT_CORE_DEVISE = "eur"
DEFAULT_COALITION_A = "eur"
DEFAULT_COALITION_B = "gbp"
DEFAULT_CONTRE = "usd"

TF_WEIGHT = {
    1: 0.55,    # M1 = microfilm vivant : tres sensible, bruit filtre plus fort
    5: 0.80,    # M5 = fractale tactique
    15: 1.00,   # M15 = scenario court, base neutre du score
    30: 1.15,
    60: 1.35,
    240: 1.75,
}

# Version de la cible gardée car elle inclut D1 et W1
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

INTEREST_RANK = {
    "IGNORE": 0,
    "WATCH_ZONE": 1,
    "STRUCTURE_BUILDING": 2,
    "TACTICAL_READY": 3,
    "SIGNAL_VALIDATED": 4,
}

SCENE_PRIORITY = {
    "CHAOS_NO_TRADE": 0,
    "CENTER_BATTLE": 1,
    "COMPRESSION_BUILD": 2,
    "EXTREME_REJECTION": 3,
    "NEGATIVE_MIRROR_SYNC": 4,
    "OPPOSITION_REBALANCE": 5,
    "ROTATION_BUILDING": 6,
    "COALITION_PUSH": 7,
    "TREND_CONTINUATION": 8,
    "COMPRESSION_RELEASE": 9,
}


@dataclass
class FlowScene:
    timestamp: str
    symbol: str
    tf: int
    tf_label: str
    scene_type: str
    confidence: int
    interest: str
    relation_type: str
    leader: Optional[str]
    reaction: Optional[str]
    confirmation: Optional[str]
    cause: str
    response: str
    confirmation_note: str
    action: str
    nodes: List[str]
    note: str

    def to_dict(self) -> Dict:
        return asdict(self)


def tf_label(tf: int) -> str:
    return TF_LABELS.get(tf, f"M{tf}")


def parse_bar_time(value: str) -> datetime:
    """Accepte 'YYYY-MM-DD HH:MM', 'YYYY-MM-DD HH:MM:SS' ou format ISO avec T."""
    value = str(value).strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            pass
    raise ValueError(f"Format bar_time invalide: {value!r}. Attendu: YYYY-MM-DD HH:MM")


def fmt_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:00")


def fmt_space(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    cur = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    )
    return cur.fetchone() is not None


def ensure_nodes(conn: sqlite3.Connection, symbol: str, tf: int, rebuild: bool = False) -> None:
    """Fonction standard de FlowScene"""
    if nodes_v6 is None:
        return
    exists = table_exists(conn, "nodes_v6")
    if rebuild or not exists:
        nodes_v6.init_table(conn)
    cur = conn.execute("SELECT COUNT(*) FROM nodes_v6 WHERE symbol=? AND timeframe=?", (symbol.upper(), tf))
    count = int(cur.fetchone()[0])
    if rebuild or count == 0:
        nodes_v6.detect(conn, symbol.upper(), tf)
        conn.commit()


def ensure_nodes_v6(conn: sqlite3.Connection, symbol: str, tf: int, rebuild: bool = False) -> None:
    """Fonction issue de l'Agrégateur (idempotente)."""
    if nodes_v6 is None:
        return

    exists = table_exists(conn, "nodes_v6")
    if rebuild or not exists:
        nodes_v6.init_table(conn)
        exists = True

    cur = conn.execute(
        "SELECT COUNT(*) FROM nodes_v6 WHERE symbol=? AND timeframe=?",
        (symbol, tf),
    )
    count = int(cur.fetchone()[0])
    if rebuild or count == 0:
        nodes_v6.detect(conn, symbol, tf)
        conn.commit()


def load_nodes(conn: sqlite3.Connection, symbol: str, tf: int, bar_time: str, window_bars: int = 3) -> List[Dict]:
    """
    Lit nodes_v6 dans la fenetre [bar_time - window_bars : bar_time].
    Fusion du load_nodes cible (qui utilise window_bars) et du to_merge (qui extrait plus de colonnes ID).
    """
    if not table_exists(conn, "nodes_v6"):
        return []
    
    end_dt = parse_bar_time(bar_time)
    start_dt = end_dt - timedelta(minutes=tf * window_bars)
    start_iso = fmt_iso(start_dt)
    end_iso = fmt_iso(end_dt)

    cur = conn.execute(
        """
        SELECT id, detected_at, symbol, timeframe, node_type,
               dev_a, dev_b, dev_c, ecart_max, delta, direction, pente,
               bars_count, bars_after, linked_node_id, note
        FROM nodes_v6
        WHERE symbol = ?
          AND timeframe = ?
          AND detected_at >= ?
          AND detected_at <= ?
        ORDER BY detected_at, id
        """,
        (symbol.upper(), tf, start_iso, end_iso),
    )
    
    nodes = []
    for r in cur.fetchall():
        nodes.append(
            {
                "id": r[0],
                "detected_at": r[1],
                "symbol": r[2],
                "timeframe": r[3],
                "node_type": r[4],
                "dev_a": r[5],
                "dev_b": r[6],
                "dev_c": r[7],
                "ecart_max": r[8],
                "delta": r[9],
                "direction": r[10],
                "pente": r[11],
                "bars_count": r[12],
                "bars_after": r[13],
                "linked_node_id": r[14],
                "note": r[15],
            }
        )
    return nodes


def node_types(nodes: Sequence[Dict]) -> List[str]:
    return [str(n.get("node_type")) for n in nodes if n.get("node_type")]


def has_extreme_zone(relation: Optional[Dict]) -> bool:
    if not relation:
        return False
    zmap = relation.get("zone_map") or {}
    return any(z in ("HAUT", "EXTREME_HAUT", "BAS", "EXTREME_BAS") for z in zmap.values())


def relation_devises(relation: Optional[Dict]) -> str:
    if not relation:
        return "-"
    return "+".join(relation.get("devises") or []) or "-"


def latest_bar_time(db_path: str, symbol: str, tf: int) -> Optional[str]:
    """Recupere la date la plus recente dans la DB."""
    conn = sqlite3.connect(db_path)
    cur = conn.execute(
        """
        SELECT strftime('%Y-%m-%d %H:%M', datetime(created_at))
        FROM force_snapshots
        WHERE symbol=? AND timeframe=?
        ORDER BY datetime(created_at) DESC
        LIMIT 1
        """,
        (symbol, tf),
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


# =====================================================================
# LOGIQUE D'AGRÉGATION (Issue de aggregate_v5.py)
# =====================================================================

def normalize_pente_strength(pente: Dict, tf: int) -> Dict:
    angle = float(pente.get("angle") or 0.0)
    weighted_angle = abs(angle) * TF_WEIGHT.get(tf, 1.0)

    if weighted_angle >= 7.0:
        niveau = "FORT"
    elif weighted_angle >= 4.0:
        niveau = "MOYEN"
    elif weighted_angle >= 1.5:
        niveau = "FAIBLE"
    else:
        niveau = "BRUIT"

    return {
        "angle_brut": round(angle, 1),
        "angle_normalise": round(weighted_angle, 1),
        "niveau": niveau,
    }


def score_signal(pente: Dict, courbure: Dict, fatigue: Dict, coalition: Dict, nodes: List[Dict]) -> Dict:
    score = 0
    composantes = []

    pente_norm = pente.get("normalisation", {})
    if pente_norm.get("niveau") == "FORT":
        score += 25
        composantes.append(f"pente forte +25(angle_norm={pente_norm.get('angle_normalise')})")
    elif pente_norm.get("niveau") == "MOYEN":
        score += 12
        composantes.append(f"pente moyenne +12(angle_norm={pente_norm.get('angle_normalise')})")

    coalition_score = coalition.get("score")
    if coalition_score == "FORTE":
        score += 20
        composantes.append("coalition forte +20")
    elif coalition_score == "MOYENNE":
        score += 10
        composantes.append("coalition moyenne +10")

    node_types_list = [n.get("node_type") for n in nodes]
    if "LIBERATION" in node_types_list:
        score += 20
        composantes.append("liberation recente +20")

    if courbure.get("courbure") == "CREUX":
        score += 15
        composantes.append("creux/rebond +15")

    fatigue_statut = fatigue.get("statut")
    if fatigue_statut in ("ENERGIE_STABLE", "FATIGUE_NAISSANTE"):
        score += 10
        if fatigue_statut == "ENERGIE_STABLE":
            composantes.append("energie stable +10")
        else:
            composantes.append("fatigue naissante tolerable +10")

    if "CROISEMENT_TRIPLE" in node_types_list:
        score += 10
        composantes.append("cross triple +10")

    if fatigue_statut == "FATIGUE_FORTE":
        score -= 15
        composantes.append("fatigue forte -15")

    score = max(0, min(100, score))

    if score < 25:
        niveau = "BRUIT"
    elif score < 50:
        niveau = "SURVEILLER"
    elif score < 75:
        niveau = "SIGNAL"
    else:
        niveau = "FORT"

    if not composantes:
        composantes.append("aucune confluence majeure")

    return {"score": score, "composantes": composantes, "niveau": niveau}


def build_line(bar_time: str, signal: Dict, pente: Dict, courbure: Dict, fatigue: Dict, coalition: Dict, nodes: List[Dict]) -> str:
    node_tags = sorted(set(n.get("node_type", "") for n in nodes if n.get("node_type")))
    keys = []
    keys.append(f"pente={pente.get('normalisation', {}).get('niveau', 'N/A')}:{pente.get('angle', 'N/A')}deg")
    keys.append(f"courbure={courbure.get('courbure', 'N/A')}")
    keys.append(f"fatigue={fatigue.get('statut', 'N/A')}")
    keys.append(f"coalition={coalition.get('score', 'N/A')}")
    if node_tags:
        keys.append("nodes=" + "+".join(node_tags))
    else:
        keys.append("nodes=aucun")

    comps = "; ".join(signal["composantes"])
    return f"[{bar_time}] SCORE:{signal['score']:02d}/100 ({signal['niveau']}) | " + " | ".join(keys) + f" | {comps}"


def produce_aggregate_report(
    symbol: str,
    tf: int,
    bar_time: str,
    db_path: str = DB_PATH,
    bars: int = 40,
    core_devise: str = DEFAULT_CORE_DEVISE,
    coalition_a: str = DEFAULT_COALITION_A,
    coalition_b: str = DEFAULT_COALITION_B,
    contre: str = DEFAULT_CONTRE,
    rebuild_nodes: bool = False,
) -> None:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    ensure_nodes_v6(conn, symbol, tf, rebuild=rebuild_nodes)

    rows, devise_cols = core.get_devise_forces(conn, symbol, tf, bar_time, window=bars)
    print("=" * 92)
    print("PowerFlow V5 Aggregate - structure + evenements")
    print(f"Symbol={symbol} | TF={TF_LABELS.get(tf, 'M' + str(tf))} | End={bar_time} | Bars={len(rows)}")
    print(f"Devise core={core_devise.upper()} | Coalition={coalition_a.upper()}+{coalition_b.upper()} vs {contre.upper()}")
    print(f"Colonnes forces detectees: {[d for d, _c in devise_cols]}")
    print("=" * 92)

    if not rows:
        print("Aucune bougie disponible pour cette periode.")
        conn.close()
        return

    for i, row in enumerate(rows):
        current_bar = row[0]
        pente = core.calc_pente(core_devise, rows, i, tf, devise_cols)
        pente["normalisation"] = normalize_pente_strength(pente, tf)
        courbure = core.detect_courbure(core_devise, rows, i, devise_cols)
        fatigue = core.detect_fatigue(core_devise, rows, i, tf, devise_cols)
        coalition = core.detect_coalition(coalition_a, coalition_b, contre, rows, i, tf, devise_cols)
        active_nodes = load_nodes(conn, symbol, tf, current_bar)
        signal = score_signal(pente, courbure, fatigue, coalition, active_nodes)
        print(build_line(current_bar, signal, pente, courbure, fatigue, coalition, active_nodes))

    print("=" * 92)
    print("FIN AGGREGATE V5")
    print("=" * 92)
    conn.close()


# =====================================================================
# LOGIQUE DES SCÈNES FLOW
# =====================================================================

def build_action(scene_type: str, interest: str, tf: int) -> str:
    label = tf_label(tf)
    if interest == "IGNORE":
        return "Ignorer. Flux trop faible ou chaotique."
    if scene_type == "COMPRESSION_BUILD":
        return f"Surveiller la sortie de compression sur {label}; attendre liberation."
    if scene_type in ("ROTATION_BUILDING", "OPPOSITION_REBALANCE", "NEGATIVE_MIRROR_SYNC"):
        if tf >= 60:
            return "Surveiller confirmation M15/M5 avant action."
        return "Surveiller prochaine bougie et confirmation du camp oppose."
    if scene_type == "COALITION_PUSH":
        return "Chercher timing tactique seulement si le prix confirme."
    if scene_type == "COMPRESSION_RELEASE":
        return "Alerte exploitable si le sens prix confirme la liberation."
    if scene_type == "CENTER_BATTLE":
        return "Attendre qu'un camp gagne le centre."
    if scene_type == "TREND_CONTINUATION":
        return "Flux propre; chercher continuation apres respiration."
    return "Surveiller, pas d'entree automatique."


def interest_from(scene_type: str, confidence: int) -> str:
    if scene_type == "CHAOS_NO_TRADE":
        return "IGNORE"
    if scene_type in ("COMPRESSION_RELEASE",) and confidence >= 70:
        return "SIGNAL_VALIDATED"
    if scene_type in ("COALITION_PUSH", "TREND_CONTINUATION") and confidence >= 65:
        return "TACTICAL_READY"
    if scene_type in ("ROTATION_BUILDING", "OPPOSITION_REBALANCE", "NEGATIVE_MIRROR_SYNC") and confidence >= 55:
        return "STRUCTURE_BUILDING"
    if scene_type in ("COMPRESSION_BUILD", "CENTER_BATTLE", "EXTREME_REJECTION"):
        return "WATCH_ZONE"
    if confidence >= 70:
        return "TACTICAL_READY"
    if confidence >= 50:
        return "STRUCTURE_BUILDING"
    if confidence >= 35:
        return "WATCH_ZONE"
    return "IGNORE"


def classify_scene(best_relation: Optional[Dict], nodes: Sequence[Dict]) -> Tuple[str, int, str]:
    ntypes = node_types(nodes)
    rel_type = (best_relation or {}).get("relation_type") or "NONE"
    rel_score = int((best_relation or {}).get("score") or 0)
    confidence = rel_score
    rationale = "relation dominante"

    if "LIBERATION" in ntypes:
        confidence = max(confidence, 70)
        if rel_score >= 55:
            confidence = min(100, confidence + 10)
        return "COMPRESSION_RELEASE", confidence, "liberation recente + relation active"

    if "COMPRESSION" in ntypes and rel_score < 60:
        return "COMPRESSION_BUILD", max(45, min(70, rel_score + 15)), "compression recente sans camp clair"

    if rel_type == "COALITION_PUSH":
        return "COALITION_PUSH", confidence, "coalition directionnelle"

    if rel_type == "OPPOSITION_REBALANCE":
        return "OPPOSITION_REBALANCE", confidence, "opposition depuis zones extremes"

    if rel_type == "OPPOSITION_DIFFEREE":
        return "ROTATION_BUILDING", confidence, "reaction differee entre devises"

    if rel_type == "OPPOSITION_DIRECTE":
        if has_extreme_zone(best_relation):
            return "OPPOSITION_REBALANCE", min(100, confidence + 5), "opposition directe avec zone extreme"
        return "NEGATIVE_MIRROR_SYNC", confidence, "angles opposes"

    if rel_type in ("CONVERGENCE", "DISTANCE_TENSION"):
        return "CENTER_BATTLE", confidence, "distance/convergence au centre"

    if rel_type == "DIVERGENCE_DISTANCE":
        return "ROTATION_BUILDING", confidence, "distance qui s'ouvre"

    if rel_type == "POSITIVE_DISTANCE_SYNC":
        return "TREND_CONTINUATION", confidence, "distance stable meme direction"

    if rel_type == "LEADER_FOLLOWER":
        conf = (best_relation or {}).get("confirmation")
        react = (best_relation or {}).get("reaction")
        if conf and not react:
            return "TREND_CONTINUATION", confidence, "leader suivi par confirmation"
        if react:
            return "ROTATION_BUILDING", confidence, "leader avec opposition"
        return "EXTREME_REJECTION" if has_extreme_zone(best_relation) else "CENTER_BATTLE", confidence, rationale

    if "CROISEMENT_TRIPLE" in ntypes:
        return "CENTER_BATTLE", max(50, confidence), "triple cross recent"

    if "CROISEMENT_DOUBLE" in ntypes:
        return "CENTER_BATTLE", max(40, confidence), "cross double recent"

    if confidence < 35:
        return "CHAOS_NO_TRADE", confidence, "aucune relation exploitable"

    return "CENTER_BATTLE", confidence, rationale


def build_scene(symbol: str, tf: int, bar_time: str, relation_pack: Dict, nodes: Sequence[Dict]) -> FlowScene:
    best = relation_pack.get("best")
    scene_type, confidence, rationale = classify_scene(best, nodes)
    confidence = max(0, min(100, int(confidence)))
    interest = interest_from(scene_type, confidence)

    leader = (best or {}).get("leader")
    reaction = (best or {}).get("reaction")
    confirmation = (best or {}).get("confirmation")
    rel_type = (best or {}).get("relation_type") or "NONE"
    ntypes = node_types(nodes)

    if best:
        cause = f"{leader or relation_devises(best)} domine la relation {rel_type}."
        response = f"Reaction: {reaction}." if reaction else "Reaction: pas encore nette."
        confirmation_note = f"Confirmation: {confirmation}." if confirmation else "Confirmation: a attendre."
        base_note = best.get("note") or "relation active"
    else:
        cause = "Aucune relation dominante propre."
        response = "Reaction: non lisible."
        confirmation_note = "Confirmation: absente."
        base_note = "flux non exploitable"

    if scene_type == "COMPRESSION_RELEASE":
        cause = "Compression recente liberee."
        response = f"Relation active: {relation_devises(best)}." if best else "Relation active faible."
    elif scene_type == "COMPRESSION_BUILD":
        cause = "Forces regroupees / compression active."
        response = "Pas de camp gagnant clair."
    elif scene_type == "OPPOSITION_REBALANCE":
        cause = f"{leader or '-'} quitte une zone de force ou prend l'angle dominant."
        response = f"{reaction or '-'} repond en angle oppose."
    elif scene_type == "ROTATION_BUILDING":
        cause = f"{leader or '-'} declenche le changement de flux."
        response = f"{reaction or '-'} repond ou s'oppose avec retard." if reaction else "Reponse encore incomplete."
    elif scene_type == "COALITION_PUSH":
        devs = best.get("devises") if best else []
        if devs and len(devs) >= 3:
            cause = f"{devs[0]}+{devs[1]} poussent ensemble."
            response = f"{devs[2]} sert de contre-force."
        else:
            cause = "Coalition directionnelle active."
    elif scene_type == "CENTER_BATTLE":
        cause = "Bataille autour du centre / croisements ou convergence."
        response = "Attendre qu'un camp gagne."
    elif scene_type == "TREND_CONTINUATION":
        cause = f"{leader or relation_devises(best)} garde une direction propre."
        response = "Respiration controlee ou distance stable."
    elif scene_type == "CHAOS_NO_TRADE":
        cause = "Relations trop faibles ou contradictoires."
        response = "Pas de lecture exploitable."

    action = build_action(scene_type, interest, tf)
    note = f"{rationale} | {base_note}"

    return FlowScene(
        timestamp=bar_time,
        symbol=symbol.upper(),
        tf=tf,
        tf_label=tf_label(tf),
        scene_type=scene_type,
        confidence=confidence,
        interest=interest,
        relation_type=rel_type,
        leader=leader,
        reaction=reaction,
        confirmation=confirmation,
        cause=cause,
        response=response,
        confirmation_note=confirmation_note,
        action=action,
        nodes=ntypes,
        note=note,
    )


def scene_compact(scene: FlowScene) -> str:
    return (
        f"[{scene.timestamp}] {scene.scene_type} {scene.confidence}/100 | "
        f"{scene.interest} | leader={scene.leader or '-'} reaction={scene.reaction or '-'} | "
        f"nodes={','.join(scene.nodes) if scene.nodes else 'aucun'} | {scene.action}"
    )


def scene_block(scene: FlowScene) -> str:
    return (
        f"\n🎬 {scene.symbol} {scene.tf_label} — {scene.scene_type}\n"
        f"Interet: {scene.interest} | Confiance: {scene.confidence}/100\n"
        f"Cause: {scene.cause}\n"
        f"Reponse: {scene.response}\n"
        f"Confirmation: {scene.confirmation_note}\n"
        f"Action: {scene.action}\n"
        f"Note: {scene.note}"
    )


def produce_scene_report(
    symbol: str,
    tf: int,
    db_path: str = DB_PATH,
    bars: int = 30,
    devises_arg: str = "eur,gbp,usd",
    end_bar: Optional[str] = None,
    rebuild_nodes: bool = False,
    only_interest: bool = False,
    verbose: bool = False,
) -> List[Dict]:
    conn = sqlite3.connect(db_path)
    ensure_nodes(conn, symbol, tf, rebuild=rebuild_nodes)
    available = relations.get_available_devises(conn)
    devises = relations.normalize_devises_arg(devises_arg, available)
    rows, devise_cols = relations.get_relation_rows(conn, symbol, tf, end_bar, bars, devises)

    print("=" * 96)
    print(f"PowerFlow V5+ Flow Scene Engine - {symbol.upper()} {tf_label(tf)} | bars={len(rows)} | devises={','.join([d.upper() for d in devises])}")
    print("=" * 96)

    if len(rows) < 3:
        print("Pas assez de donnees pour construire une scene Flow.")
        conn.close()
        return []

    outputs: List[Dict] = []
    for i, row in enumerate(rows):
        bar_time = str(row[0])
        rel_pack = relations.detect_best_force_relation(rows, i, tf, devise_cols, symbol=symbol, devises=devises)
        active_nodes = load_nodes(conn, symbol, tf, bar_time, window_bars=3)
        scene = build_scene(symbol, tf, bar_time, rel_pack, active_nodes)
        outputs.append(scene.to_dict())

        if only_interest and scene.interest in ("IGNORE", "WATCH_ZONE"):
            continue
        if verbose:
            print(scene_block(scene))
        else:
            print(scene_compact(scene))

    print("=" * 96)
    print("FIN SCENES")
    print("=" * 96)
    conn.close()
    return outputs


def main_aggregate() -> None:
    """Ancien entry point de aggregate_v5.py."""
    parser = argparse.ArgumentParser(description="PowerFlow V5 aggregate scoring")
    parser.add_argument("symbol", nargs="?", default="GBPUSD", help="Ex: GBPUSD")
    parser.add_argument("tf", nargs="?", type=int, default=15, help="Timeframe minutes: 1,5,15,30,60,240")
    parser.add_argument("bar_time", nargs="?", default=None, help="End bar time: 'YYYY-MM-DD HH:MM'")
    parser.add_argument("--db", default=DB_PATH, help="SQLite DB path")
    parser.add_argument("--bars", type=int, default=40, help="Nombre de bougies a charger")
    parser.add_argument("--core-devise", default=DEFAULT_CORE_DEVISE)
    parser.add_argument("--coalition-a", default=DEFAULT_COALITION_A)
    parser.add_argument("--coalition-b", default=DEFAULT_COALITION_B)
    parser.add_argument("--contre", default=DEFAULT_CONTRE)
    parser.add_argument("--rebuild-nodes", action="store_true", help="Reconstruit nodes_v6 avant scoring")
    args = parser.parse_args()

    db_path = args.db
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"DB introuvable: {db_path}")

    end_bar = args.bar_time or latest_bar_time(db_path, args.symbol.upper(), args.tf)
    if not end_bar:
        raise RuntimeError(f"Aucune bougie trouvee pour {args.symbol.upper()} M{args.tf}")

    produce_aggregate_report(
        symbol=args.symbol.upper(),
        tf=args.tf,
        bar_time=end_bar,
        db_path=db_path,
        bars=args.bars,
        core_devise=args.core_devise.lower(),
        coalition_a=args.coalition_a.lower(),
        coalition_b=args.coalition_b.lower(),
        contre=args.contre.lower(),
        rebuild_nodes=args.rebuild_nodes,
    )


def main() -> None:
    """Entry point principal pour generer les Scenes."""
    parser = argparse.ArgumentParser(description="PowerFlow V5+ flow scene engine")
    parser.add_argument("symbol", help="Ex: GBPUSD")
    parser.add_argument("tf", type=int, help="Timeframe en minutes: 1,5,15,30,60,240,1440,10080")
    parser.add_argument("--db", default=DB_PATH, help="Chemin powerflow.db")
    parser.add_argument("--bars", type=int, default=30, help="Nombre de bougies a lire")
    parser.add_argument("--devises", default="eur,gbp,usd", help="Ex: eur,gbp,usd ou all")
    parser.add_argument("--end", default=None, help="Fin optionnelle: YYYY-MM-DD HH:MM")
    parser.add_argument("--rebuild-nodes", action="store_true", help="Reconstruire nodes_v6 avant lecture")
    parser.add_argument("--only-interest", action="store_true", help="Masquer IGNORE/WATCH_ZONE")
    parser.add_argument("--verbose", action="store_true", help="Afficher le bloc Cockpit complet")
    args = parser.parse_args()

    produce_scene_report(
        symbol=args.symbol,
        tf=args.tf,
        db_path=args.db,
        bars=args.bars,
        devises_arg=args.devises,
        end_bar=args.end,
        rebuild_nodes=args.rebuild_nodes,
        only_interest=args.only_interest,
        verbose=args.verbose,
    )


if __name__ == "__main__":
    main()
