"""
lab_elastic.py — PowerFlow V7
6 queries prêtes pour lab.py et film.py.
Read-only. Pas de side-effects.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import json

from pf_confluence_elastic import (
    CURRENCIES, compute_confluence_snapshot, compute_eie_state,
    query_eie_history, query_eie_sessions_summary,
)
from pf_confluence_gravity import compute_confluence_gravity

DB_DEFAULT = Path("powerflow.db")


def q_eie_snapshot(db_path: Path = DB_DEFAULT, zone_tf: int = 15, pretty: bool = True) -> dict:
    """Q1 — Snapshot EIE complet toutes devises."""
    snap = compute_confluence_snapshot(db_path=db_path, zone_tf=zone_tf)
    result = {
        "timestamp": snap.timestamp.isoformat(),
        "eie_active": snap.eie_currencies(),
        "fractal_alert": snap.fractal_alert(),
        "states": {
            c: {
                "zone_state": s.zone_state, "zone_z": round(s.zone_z, 3),
                "zone_dir": s.zone_dir, "elastic_tf1": s.elastic_label_tf1,
                "elastic_tf5": s.elastic_label_tf5, "eie": s.is_eie,
                "ewz": s.is_ewz, "enz": s.is_enz, "zne": s.is_zne,
                "fractal_score": s.fractal_score, "fractal_label": s.fractal_label,
            }
            for c, s in snap.states.items()
        },
    }
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def q_eie_gravity(currency: str, db_path: Path = DB_DEFAULT, zone_tf: int = 15, pretty: bool = True) -> dict:
    """Q2 — EIE state + gravity bridge V7 pour une devise."""
    state = compute_eie_state(db_path=db_path, currency=currency, zone_tf=zone_tf)
    cg = compute_confluence_gravity(currency=currency)
    result = {
        "currency": currency, "eie": state.is_eie,
        "zone_state": state.zone_state, "zone_z": round(state.zone_z, 3),
        "zone_dir": state.zone_dir, "elastic_tf1": state.elastic_label_tf1,
        "elastic_tf5": state.elastic_label_tf5, "fractal_score": state.fractal_score,
        "fractal_label": state.fractal_label, "fusion_state": cg.fusion_state,
        "confidence": cg.confidence, "regime": cg.regime,
        "regime_confidence": round(cg.regime_confidence, 3),
        "roles_by_tf": {str(k): v for k, v in cg.roles_by_tf.items()},
        "spearman_context": cg.spearman_context, "notes": cg.notes,
    }
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def q_eie_history(currency: str, db_path: Path = DB_DEFAULT, limit: int = 200,
                   only_eie: bool = False, pretty: bool = False) -> list:
    """Q3 — Historique EIE pour film.py (replay) ou lab.py (analyse)."""
    rows = query_eie_history(db_path=db_path, currency=currency, limit=limit)
    if only_eie:
        rows = [r for r in rows if r["eie"]]
    if pretty:
        print(json.dumps(rows, indent=2, ensure_ascii=False))
    return rows


def q_eie_day_summary(date_str: Optional[str] = None, db_path: Path = DB_DEFAULT,
                       min_persist: int = 2, zone_tf: int = 15, pretty: bool = True) -> dict:
    """Q4 — Distribution EIE par devise sur une journée."""
    result = query_eie_sessions_summary(db_path=db_path, date_str=date_str, zone_tf=zone_tf, min_persist=min_persist)
    if pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return result


def q_eie_top_active(db_path: Path = DB_DEFAULT, zone_tf: int = 15,
                      min_fractal: int = 2, pretty: bool = True) -> list:
    """Q5 — Top devises EIE actives maintenant (triées fractal_score)."""
    snap = compute_confluence_snapshot(db_path=db_path, zone_tf=zone_tf)
    actives = [
        {"currency": c, "fractal_score": s.fractal_score, "fractal_label": s.fractal_label,
         "zone_state": s.zone_state, "zone_z": round(s.zone_z, 3)}
        for c, s in snap.states.items()
        if s.is_eie and s.fractal_score >= min_fractal
    ]
    actives.sort(key=lambda x: -x["fractal_score"])
    if pretty:
        print(json.dumps(actives, indent=2, ensure_ascii=False))
    return actives


def q_read_behavioral_queue(queue_path: Path = Path("output/behavioral_alert_queue.json"),
                              freshness_seconds: int = 600, only_eie: bool = True,
                              pretty: bool = True) -> list:
    """Q6 — Événements récents behavioral_alert_queue."""
    if not queue_path.exists():
        if pretty:
            print("Queue vide ou absente.")
        return []
    try:
        events = json.loads(queue_path.read_text(encoding="utf-8"))
    except Exception:
        return []
    now = datetime.now(timezone.utc)
    fresh = []
    for e in events:
        if only_eie and e.get("type") != "ELASTIC_IN_EXTREME":
            continue
        try:
            ts = datetime.fromisoformat(e.get("timestamp", "").replace("Z", "+00:00"))
            if (now - ts).total_seconds() < freshness_seconds:
                fresh.append(e)
        except Exception:
            fresh.append(e)
    if pretty:
        print(json.dumps(fresh, indent=2, ensure_ascii=False))
    return fresh