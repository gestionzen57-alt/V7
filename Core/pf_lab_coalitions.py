#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - pf_lab_coalitions.py
Version: V0.1.0
Layer: 10 — Coalition Detection (Lab Query Wrapper)

Mission:
    Wrapper couche 10 du lab PowerFlow.
    Reconstruit les CurrencyVectors depuis force_snapshots,
    détecte les coalitions via pf_coalitions,
    qualifie les relations battlefield via pf_coalition_relations,
    retourne dict structuré pour query_full_v3.

Doctrine:
    Read-only. No DB write. No Telegram. No Cockpit import.
    Alerter sans censure. Trader décide.
"""

from __future__ import annotations

import sqlite3
import statistics
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pf_coalitions import (
    CurrencyVector,
    detect_currency_coalitions,
    coalitions_to_dict,
    summarize_coalitions,
)
from pf_coalition_relations import (
    qualify_coalition_relations,
    relations_to_dict,
    summarize_relations,
)

# ──────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────

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

DEFAULT_BARS = 50
DEFAULT_MIN_COHESION = 0.62
DEFAULT_MIN_FIELD_SCORE = 0.45
EPSILON = 1e-9


# ──────────────────────────────────────────────────────────────
# DB HELPERS
# ──────────────────────────────────────────────────────────────

def _norm_dt(dt_str: str) -> str:
    """Normalize datetime string — strip timezone offset for SQLite comparison."""
    if not dt_str:
        return dt_str
    for sep in ("+00:00", "+0000", "Z"):
        if dt_str.endswith(sep):
            return dt_str[: -len(sep)]
    return dt_str


def _load_force_bars(
    db_path: str,
    symbol: str,
    tf: int,
    bars: int,
    start: Optional[str] = None,
    end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Load last N bars of force_snapshots for a given TF.
    Returns list of dicts with created_at + force per currency.
    Falls back to last N bars if datetime window yields 0 rows.
    """
    uri = f"file:{db_path}?mode=ro"
    cols = ", ".join(FORCE_COLS.values())

    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row

        if start and end:
            s = _norm_dt(start)
            e = _norm_dt(end)
            cur = conn.execute(
                f"""
                SELECT created_at, {cols}
                FROM force_snapshots
                WHERE symbol = ? AND timeframe = ?
                  AND created_at >= ? AND created_at <= ?
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (symbol, tf, s, e, bars),
            )
            rows = cur.fetchall()
        else:
            rows = []

        # Fallback to last N bars if window empty
        if not rows:
            cur = conn.execute(
                f"""
                SELECT created_at, {cols}
                FROM force_snapshots
                WHERE symbol = ? AND timeframe = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (symbol, tf, bars),
            )
            rows = list(reversed(cur.fetchall()))

    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────
# VECTOR BUILDER
# ──────────────────────────────────────────────────────────────

def _build_vectors(rows: List[Dict[str, Any]]) -> List[CurrencyVector]:
    """
    Build CurrencyVectors from force_snapshots rows.
    Computes z_basket (normalized position), slope, curvature per currency.
    """
    if len(rows) < 6:
        return []

    forces: Dict[str, List[float]] = {c: [] for c in CURRENCIES}
    for row in rows:
        for cur, col in FORCE_COLS.items():
            val = row.get(col)
            if val is not None:
                try:
                    forces[cur].append(float(val))
                except (TypeError, ValueError):
                    pass

    vectors: List[CurrencyVector] = []
    for cur in CURRENCIES:
        vals = forces[cur]
        if len(vals) < 6:
            continue

        # z_basket: position relative to all-currency mean, normalized by global std
        all_vals = [v for vlist in forces.values() for v in vlist]
        global_mean = statistics.mean(all_vals) if all_vals else 0.0
        global_std = statistics.stdev(all_vals) if len(all_vals) > 1 else EPSILON

        cur_mean = statistics.mean(vals)
        z_basket = (cur_mean - global_mean) / (global_std + EPSILON)

        # slope: linear regression slope (simplified delta mean)
        n = len(vals)
        half = max(n // 3, 2)
        recent_mean = statistics.mean(vals[-half:])
        early_mean = statistics.mean(vals[:half])
        slope = (recent_mean - early_mean) / (half + EPSILON)

        # curvature: change in slope (second derivative approximation)
        if n >= 9:
            third = max(n // 3, 3)
            s1 = (statistics.mean(vals[third:2*third]) - statistics.mean(vals[:third])) / (third + EPSILON)
            s2 = (statistics.mean(vals[2*third:]) - statistics.mean(vals[third:2*third])) / (third + EPSILON)
            curvature = s2 - s1
        else:
            curvature = 0.0

        # context_tags: simple heuristic from z_basket and slope
        context_tags: List[str] = []
        if abs(z_basket) >= 2.0:
            context_tags.append("EXTREME_ZONE")
        if abs(z_basket) >= 1.2:
            context_tags.append("SCENARIO_ZONE_WORK" if abs(z_basket) >= 1.8 else "LOCAL_ZONE_WORK")
        if slope > 0.05:
            context_tags.append("H1_SCENARIO_CURVE")
        elif slope < -0.05:
            context_tags.append("H1_SCENARIO_CURVE")

        # phase heuristic
        if z_basket < -1.5 and slope > 0:
            phase = "EARLY_RESPRING"
        elif z_basket > 1.5 and slope < 0:
            phase = "FOLDING_FROM_HIGH"
        elif z_basket < -0.5 and slope < 0:
            phase = "LOW_PRESSURE_EXPANDING"
        elif z_basket > 0.5 and slope > 0:
            phase = "HIGH_PRESSURE_EXPANDING"
        else:
            phase = "NEUTRAL_ZONE"

        vectors.append(CurrencyVector(
            currency=cur,
            z_basket=round(z_basket, 4),
            slope=round(slope, 6),
            curvature=round(curvature, 6),
            phase=phase,
            context_tags=tuple(context_tags),
        ))

    return vectors


# ──────────────────────────────────────────────────────────────
# MAIN QUERY
# ──────────────────────────────────────────────────────────────

def query_coalitions(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: Optional[str] = None,
    end: Optional[str] = None,
    bars: int = DEFAULT_BARS,
    min_cohesion: float = DEFAULT_MIN_COHESION,
    min_field_score: float = DEFAULT_MIN_FIELD_SCORE,
) -> Dict[str, Any]:
    """
    Coalition detection multi-TF — Layer 10 lab query.

    Args:
        db_path:        Path to powerflow.db
        symbol:         Symbol (ex: "GBPUSD")
        tfs:            List of timeframes (ex: [5, 15, 60])
        start:          ISO8601 datetime string (optional)
        end:            ISO8601 datetime string (optional)
        bars:           Max bars to load per TF
        min_cohesion:   Minimum coalition cohesion [0..1]
        min_field_score: Minimum field_score for active_relations

    Returns:
        {
            "timeframes": {
                "60": {
                    "vectors": [...],
                    "all_coalitions": [...],
                    "active_relations": [...],      # field_score >= min_field_score
                    "strong_coalitions": [...],     # cohesion >= 0.75, no antagonist active
                    "weak_field": [...],            # rest
                    "summary_coalitions": str,
                    "summary_relations": str,
                    "n_coalitions": int,
                    "n_active_relations": int,
                    "error": str or None,
                }
            },
            "cross_tf_summary": {
                "battlefield_windows": [...],       # TFs with BATTLEFIELD_WINDOW_OPENING+
                "dominant_coalition": str or None,
                "dominant_antagonist": str or None,
                "compression_detected": bool,
            },
            "error": str or None,
        }
    """
    result: Dict[str, Any] = {
        "timeframes": {},
        "cross_tf_summary": {
            "battlefield_windows": [],
            "dominant_coalition": None,
            "dominant_antagonist": None,
            "compression_detected": False,
        },
        "error": None,
    }

    all_tfs_active_relations = []
    coalition_member_counts: Dict[str, int] = {}
    antagonist_counts: Dict[str, int] = {}

    for tf in tfs:
        tf_key = str(tf)
        tf_result: Dict[str, Any] = {
            "vectors": [],
            "all_coalitions": [],
            "active_relations": [],
            "strong_coalitions": [],
            "weak_field": [],
            "summary_coalitions": "",
            "summary_relations": "",
            "n_coalitions": 0,
            "n_active_relations": 0,
            "error": None,
        }

        try:
            rows = _load_force_bars(db_path, symbol, tf, bars, start, end)

            if len(rows) < 6:
                tf_result["error"] = f"INSUFFICIENT_DATA ({len(rows)} rows)"
                result["timeframes"][tf_key] = tf_result
                continue

            vectors = _build_vectors(rows)
            if not vectors:
                tf_result["error"] = "VECTOR_BUILD_FAILED"
                result["timeframes"][tf_key] = tf_result
                continue

            tf_result["vectors"] = [
                {
                    "currency": v.currency,
                    "z_basket": v.z_basket,
                    "slope": v.slope,
                    "curvature": v.curvature,
                    "phase": v.phase,
                    "context_tags": list(v.context_tags),
                }
                for v in vectors
            ]

            # Detect coalitions
            coalitions = detect_currency_coalitions(
                vectors,
                min_members=2,
            )
            # Filter by min_cohesion
            coalitions = [c for c in coalitions if c.cohesion >= min_cohesion]

            tf_result["all_coalitions"] = coalitions_to_dict(coalitions)
            tf_result["n_coalitions"] = len(coalitions)
            tf_result["summary_coalitions"] = summarize_coalitions(coalitions)

            # Qualify battlefield relations
            vector_dicts = tf_result["vectors"]
            relations = qualify_coalition_relations(coalitions, vector_dicts)

            all_coalitions_dict = coalitions_to_dict(coalitions)
            tf_result["summary_relations"] = summarize_relations(relations)

            # Classify relations
            active: List[Dict] = []
            strong_no_ant: List[Dict] = []
            weak: List[Dict] = []

            rel_dicts = relations_to_dict(relations)
            for r_dict, r_obj in zip(rel_dicts, relations):
                if r_obj.field_score >= min_field_score:
                    active.append(r_dict)
                    all_tfs_active_relations.append({
                        "tf": tf,
                        "field_state": r_obj.field_state,
                        "field_score": r_obj.field_score,
                        "coalition_members": list(r_obj.coalition_members),
                        "antagonist": r_obj.antagonist,
                    })
                else:
                    weak.append(r_dict)

            for c_dict, c_obj in zip(all_coalitions_dict, coalitions):
                if c_obj.cohesion >= 0.75 and not c_obj.antagonist_candidates:
                    strong_no_ant.append(c_dict)
                # Track member/antagonist frequencies for cross-tf summary
                for m in c_obj.members:
                    coalition_member_counts[m] = coalition_member_counts.get(m, 0) + 1
                for a in c_obj.antagonist_candidates:
                    antagonist_counts[a] = antagonist_counts.get(a, 0) + 1

            tf_result["active_relations"] = active
            tf_result["strong_coalitions"] = strong_no_ant
            tf_result["weak_field"] = weak
            tf_result["n_active_relations"] = len(active)

        except Exception as exc:
            tf_result["error"] = f"TF_ERROR: {exc}"

        result["timeframes"][tf_key] = tf_result

    # Cross-TF summary
    battlefield_tfs = [
        r["tf"] for r in all_tfs_active_relations
        if r["field_state"] in ("BATTLEFIELD_WINDOW_OPENING", "FIELD_SIDE_SHIFT_ACTIVE")
    ]
    result["cross_tf_summary"]["battlefield_windows"] = sorted(set(battlefield_tfs))

    if coalition_member_counts:
        result["cross_tf_summary"]["dominant_coalition"] = max(
            coalition_member_counts, key=coalition_member_counts.get
        )
    if antagonist_counts:
        result["cross_tf_summary"]["dominant_antagonist"] = max(
            antagonist_counts, key=antagonist_counts.get
        )

    # Compression = 5+ currencies with small z_basket variance across any TF
    for tf_key, tf_data in result["timeframes"].items():
        if tf_data.get("error"):
            continue
        vecs = tf_data.get("vectors", [])
        z_vals = [v["z_basket"] for v in vecs if "z_basket" in v]
        if len(z_vals) >= 5:
            z_spread = max(z_vals) - min(z_vals)
            if z_spread < 1.5 and all(abs(z) < 1.0 for z in z_vals):
                result["cross_tf_summary"]["compression_detected"] = True
                break

    return result


# ──────────────────────────────────────────────────────────────
# CLI (standalone test)
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    import json

    parser = argparse.ArgumentParser(description="pf_lab_coalitions — standalone test")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--tfs", default="5,15,60")
    parser.add_argument("--bars", type=int, default=50)
    parser.add_argument("--start", default=None)
    parser.add_argument("--end", default=None)
    parser.add_argument("--min-cohesion", type=float, default=0.62)
    parser.add_argument("--min-field-score", type=float, default=0.45)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    tfs = [int(t) for t in args.tfs.split(",")]
    result = query_coalitions(
        db_path=args.db,
        symbol=args.symbol,
        tfs=tfs,
        start=args.start,
        end=args.end,
        bars=args.bars,
        min_cohesion=args.min_cohesion,
        min_field_score=args.min_field_score,
    )

    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent, default=str))
