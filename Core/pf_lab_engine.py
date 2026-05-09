# -*- coding: utf-8 -*-
"""
PowerFlow V6 — pf_lab_engine.py
Moteur pur du lab expérimental.

Règles :
  - Read-only SQLite (uri=ro)
  - Pas de DB write
  - Pas de Telegram
  - Pas de God File (pf_temporal_node_state)
  - TF libres : M1 → W1, pas de filtre hardcodé

Queries disponibles :
  kinematics   → angle/speed/accel brut multi-TF multi-devise
  zones        → zone_state cascade LTF→MTF→HTF
  nodes        → fractal nodes (pf_flow_nodes) + release state propre
  orchestra    → leader/follower/compression multi-TF (pf_orchestral_gravity_v02)
  relational   → gravity brut SANS filtre P1.2 (pf_relational_gravity_probe)
  fractal      → cohérence LTF/MTF/HTF (phase sync / divergence)

Usage depuis lab_powerflow.py ou directement :
  from pf_lab_engine import query_kinematics, query_nodes, query_zones
"""

from __future__ import annotations

import json
import logging
import math
import sqlite3
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, Dict, List, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL IMPORTS — COUCHES 10+11
# ─────────────────────────────────────────────────────────────────────────────

try:
    from pf_lab_coalitions import query_coalitions as _query_coalitions
    _COALITIONS_OK = True
except ImportError:
    _COALITIONS_OK = False

try:
    from pf_lab_tension import query_tension_signature as _query_tension
    _TENSION_OK = True
except ImportError:
    _TENSION_OK = False

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────────────

CURRENCIES: Tuple[str, ...] = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD", "NZD")

TF_LABEL: Dict[int, str] = {
    1: "M1", 5: "M5", 15: "M15", 30: "M30",
    60: "H1", 240: "H4", 1440: "D1", 10080: "W1",
}

# 3 horizons — M15 est pont LTF/MTF intentionnel
HORIZON_TFS: Dict[str, List[int]] = {
    "LTF": [1, 5, 15],
    "MTF": [15, 30, 60],
    "HTF": [60, 240, 1440],
}

# Seuils kinematics par TF (angle_deg pour first_detachment)
KIN_DETACHMENT_THRESHOLD: Dict[int, float] = {
    1: 55.0, 5: 45.0, 15: 35.0, 30: 28.0,
    60: 22.0, 240: 15.0, 1440: 10.0,
}

# Zones — 6 états PowerFlow
ZONE_STATES = ("NEUTRAL", "PRE_EXTREME", "EARLY_EXTREME", "ACCUMULATING", "LEAKING", "RUPTURE")

# Seuils z-score par zone (sur force brute)
ZONE_ZSCORE_THRESHOLDS = {
    "PRE_EXTREME":   1.2,
    "EARLY_EXTREME": 1.8,
    "ACCUMULATING":  2.2,
    "LEAKING":       2.5,
    "RUPTURE":       3.0,
}


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 0 — DB ACCESS
# ─────────────────────────────────────────────────────────────────────────────

def connect_readonly(db_path: str) -> sqlite3.Connection:
    """Connexion read-only SQLite."""
    path = Path(db_path).expanduser().resolve()
    if not path.exists():
        raise FileNotFoundError(f"DB introuvable: {path}")
    uri = f"file:{path.as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, timeout=3.0)
    conn.row_factory = sqlite3.Row
    return conn


def get_available_tfs(db_path: str, symbol: str) -> List[int]:
    """Retourne les TFs disponibles en DB pour ce symbol."""
    conn = connect_readonly(db_path)
    try:
        rows = conn.execute(
            "SELECT DISTINCT timeframe FROM force_snapshots WHERE symbol=? ORDER BY timeframe ASC",
            (symbol.upper(),),
        ).fetchall()
        return [int(r["timeframe"]) for r in rows if r["timeframe"] is not None]
    finally:
        conn.close()


def load_force_series(
    db_path: str,
    symbol: str,
    tf: int,
    start: str,
    end: str,
) -> List[Dict[str, Any]]:
    """
    Charge la série de forces pour un TF et une fenêtre temporelle.
    Retourne liste de dicts {ts, GBP, USD, EUR, JPY, CAD, CHF, AUD, NZD, bid, spread}.
    start/end : ISO8601 string ex "2026-05-07T07:00:00"
    """
    conn = connect_readonly(db_path)
    try:
        # Détecter colonnes disponibles
        cols_info = conn.execute("PRAGMA table_info(force_snapshots)").fetchall()
        available_cols = {r["name"] for r in cols_info}

        # Colonnes force disponibles
        force_cols = [f"force_{c.lower()}" for c in CURRENCIES if f"force_{c.lower()}" in available_cols]
        if not force_cols:
            return []

        # Colonne temps
        time_col = next(
            (c for c in ("created_at", "bar_time", "timestamp", "time", "ts") if c in available_cols),
            None,
        )
        if time_col is None:
            return []

        # Prix / spread optionnels
        price_col = next((c for c in ("bid", "price", "close") if c in available_cols), None)
        spread_col = "spread" if "spread" in available_cols else None

        select_parts = [time_col] + force_cols
        if price_col:
            select_parts.append(price_col)
        if spread_col:
            select_parts.append(spread_col)

        # Normaliser start/end pour SQLite
        # Accepte ISO8601 avec T, espace, Z, offset +XX:XX
        def _norm_dt(s: str) -> str:
            s = s.strip()
            # Supprimer offset timezone (+00:00, +02:00, etc.)
            for sep in ("+", "-"):
                # Chercher offset après HH:MM:SS (position >= 19)
                idx = s.find(sep, 19)
                if idx != -1:
                    s = s[:idx]
            s = s.replace("T", " ").replace("Z", "").strip()
            return s[:19]

        start_db = _norm_dt(start)
        end_db = _norm_dt(end)

        sql = f"""
            SELECT {', '.join(select_parts)}
            FROM force_snapshots
            WHERE symbol = ?
              AND timeframe = ?
              AND {time_col} >= ?
              AND {time_col} <= ?
            ORDER BY {time_col} ASC
        """
        rows = conn.execute(sql, (symbol.upper(), tf, start_db, end_db)).fetchall()

        # Fallback : si la fenêtre datetime ne matche rien (décalage UTC/local),
        # on charge les N dernières barres couvrant la même durée approximative.
        if not rows:
            from datetime import datetime as _dt
            try:
                t0 = _dt.fromisoformat(start_db)
                t1 = _dt.fromisoformat(end_db)
                duration_min = max(60, int((t1 - t0).total_seconds() / 60))
            except Exception:
                duration_min = 180
            # Nombre de barres pour couvrir la durée (1 barre = tf minutes)
            bars_needed = max(10, duration_min // max(tf, 1) + 10)
            sql_fallback = f"""
                SELECT {', '.join(select_parts)}
                FROM force_snapshots
                WHERE symbol = ?
                  AND timeframe = ?
                ORDER BY {time_col} DESC
                LIMIT ?
            """
            rows = conn.execute(sql_fallback, (symbol.upper(), tf, bars_needed)).fetchall()
            rows = list(reversed(rows))

        out = []
        for r in rows:
            row_dict: Dict[str, Any] = {"ts": str(r[time_col])}
            for fc in force_cols:
                currency = fc.replace("force_", "").upper()
                v = r[fc]
                row_dict[currency] = float(v) if v is not None else None
            if price_col and price_col in r.keys():
                row_dict["bid"] = float(r[price_col]) if r[price_col] is not None else None
            if spread_col and spread_col in r.keys():
                row_dict["spread"] = float(r[spread_col]) if r[spread_col] is not None else None
            out.append(row_dict)
        return out
    finally:
        conn.close()


def load_force_series_bars(
    db_path: str,
    symbol: str,
    tf: int,
    bars: int = 120,
    end: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Charge les N dernières barres pour un TF.
    Variante 'bars' de load_force_series — utile pour les nodes.
    """
    conn = connect_readonly(db_path)
    try:
        cols_info = conn.execute("PRAGMA table_info(force_snapshots)").fetchall()
        available_cols = {r["name"] for r in cols_info}
        force_cols = [f"force_{c.lower()}" for c in CURRENCIES if f"force_{c.lower()}" in available_cols]
        if not force_cols:
            return []
        time_col = next(
            (c for c in ("created_at", "bar_time", "timestamp", "time", "ts") if c in available_cols),
            None,
        )
        if time_col is None:
            return []

        select_parts = [time_col] + force_cols
        params: list = [symbol.upper(), tf]
        end_clause = ""
        if end:
            end_db = end.replace("T", " ").replace("Z", "")[:19]
            end_clause = f"AND {time_col} <= ?"
            params.append(end_db)
        params.append(bars)

        sql = f"""
            SELECT {', '.join(select_parts)}
            FROM force_snapshots
            WHERE symbol = ? AND timeframe = ?
            {end_clause}
            ORDER BY {time_col} DESC
            LIMIT ?
        """
        rows = conn.execute(sql, params).fetchall()
        rows = list(reversed(rows))

        out = []
        for r in rows:
            row_dict: Dict[str, Any] = {"ts": str(r[time_col])}
            for fc in force_cols:
                currency = fc.replace("force_", "").upper()
                v = r[fc]
                row_dict[currency] = float(v) if v is not None else None
            out.append(row_dict)
        return out
    finally:
        conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS MATH
# ─────────────────────────────────────────────────────────────────────────────

def _safe_mean(vals: Sequence[Optional[float]]) -> Optional[float]:
    clean = [v for v in vals if v is not None]
    return fmean(clean) if clean else None


def _safe_std(vals: Sequence[Optional[float]]) -> Optional[float]:
    clean = [v for v in vals if v is not None]
    return pstdev(clean) if len(clean) >= 2 else None


def _zscore(val: float, mean: float, std: float) -> float:
    if std == 0:
        return 0.0
    return (val - mean) / std


def _slope(values: Sequence[float]) -> float:
    """Régression linéaire simple — retourne la pente."""
    n = len(values)
    if n < 2:
        return 0.0
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(values) / n
    den = sum((x - mx) ** 2 for x in xs) or 1.0
    return sum((x - mx) * (y - my) for x, y in zip(xs, values)) / den


def _angle_from_slope(slope: float, scale: float = 10.0) -> float:
    """Convertit une pente en degrés (approx)."""
    return math.degrees(math.atan(slope / scale))


def _extract_series(rows: List[Dict], currency: str) -> List[float]:
    return [r[currency] for r in rows if r.get(currency) is not None]


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 1 — KINEMATICS BRUT (sans filtre God File)
# ─────────────────────────────────────────────────────────────────────────────

def _kinematics_for_tf(
    rows: List[Dict[str, Any]],
    tf: int,
    currencies: Sequence[str],
    bars_angle: int = 5,
) -> Dict[str, Any]:
    """
    Calcule kinematics (angle, speed, accel, first_detachment) pour un TF.
    Directement depuis rows DB — sans passer par pf_temporal_node_state.
    bars_angle : fenêtre de calcul de l'angle (dernières N barres).
    """
    if not rows:
        return {"status": "NO_DATA", "tf": tf, "tf_label": TF_LABEL.get(tf, f"M{tf}")}

    tf_label = TF_LABEL.get(tf, f"M{tf}")
    detachment_threshold = KIN_DETACHMENT_THRESHOLD.get(tf, 30.0)
    result: Dict[str, Any] = {
        "tf": tf,
        "tf_label": tf_label,
        "bars": len(rows),
        "window_start": rows[0]["ts"] if rows else None,
        "window_end": rows[-1]["ts"] if rows else None,
        "currencies": {},
        "first_detachment": {"detected": False, "currencies": []},
        "same_angle_cluster": {"detected": False},
        "tight_gravity_cluster": {"detected": False},
        "angle_state": "NEUTRAL",
        "speed_state": "MODERATE",
    }

    cur_data: Dict[str, Dict] = {}

    for currency in currencies:
        series = _extract_series(rows, currency)
        if len(series) < 3:
            cur_data[currency] = {"status": "INSUFFICIENT_DATA"}
            continue

        # Dernières N barres pour angle
        recent = series[-bars_angle:] if len(series) >= bars_angle else series
        slope = _slope(recent)
        angle = _angle_from_slope(slope)

        # Speed : delta entre dernière et avant-dernière barre
        speed = series[-1] - series[-2] if len(series) >= 2 else 0.0

        # Acceleration : delta de speed sur 3 barres
        if len(series) >= 3:
            speed_prev = series[-2] - series[-3]
            accel = speed - speed_prev
        else:
            accel = 0.0

        # Z-score de la force actuelle
        mean_f = _safe_mean(series)
        std_f = _safe_std(series)
        zscore_f = _zscore(series[-1], mean_f, std_f) if (mean_f is not None and std_f is not None) else None

        cur_data[currency] = {
            "latest_force": round(series[-1], 3),
            "angle_deg": round(angle, 2),
            "slope": round(slope, 4),
            "speed": round(speed, 3),
            "acceleration": round(accel, 3),
            "zscore": round(zscore_f, 3) if zscore_f is not None else None,
            "bars_used": len(series),
        }

        # First detachment : angle absolu dépasse le seuil du TF
        if abs(angle) >= detachment_threshold:
            result["first_detachment"]["detected"] = True
            result["first_detachment"]["currencies"].append({
                "currency": currency,
                "angle_deg": round(angle, 2),
                "direction": "UP" if angle > 0 else "DOWN",
                "label": f"{tf_label}_FIRST_DETACHMENT_{currency}_{'UP' if angle > 0 else 'DOWN'}",
            })

    result["currencies"] = cur_data

    # Same angle cluster : >= 3 devises même direction, spread d'angle <= seuil
    angles_valid = [(c, d["angle_deg"]) for c, d in cur_data.items() if "angle_deg" in d]
    up_angles = [(c, a) for c, a in angles_valid if a > 5]
    down_angles = [(c, a) for c, a in angles_valid if a < -5]

    cluster_spread_threshold = max(15.0, 5.0 * (tf / 5))  # plus large pour HTF

    for direction, angle_list in [("UP", up_angles), ("DOWN", down_angles)]:
        if len(angle_list) >= 3:
            sorted_a = sorted(angle_list, key=lambda x: x[1])
            for i in range(len(sorted_a) - 2):
                w = sorted_a[i:i + 3]
                if abs(w[-1][1] - w[0][1]) <= cluster_spread_threshold:
                    result["same_angle_cluster"] = {
                        "detected": True,
                        "label": f"{tf_label}_SAME_ANGLE_CLUSTER_{direction}",
                        "direction": direction,
                        "currencies": [c for c, _ in w],
                        "angles": {c: round(a, 2) for c, a in w},
                        "spread_deg": round(abs(w[-1][1] - w[0][1]), 2),
                    }
                    break

    # Tight gravity cluster : forces absolues serrées (spread <= 15)
    forces_valid = [(c, d["latest_force"]) for c, d in cur_data.items() if "latest_force" in d]
    if len(forces_valid) >= 3:
        sorted_f = sorted(forces_valid, key=lambda x: x[1])
        for i in range(len(sorted_f) - 2):
            w = sorted_f[i:i + 3]
            spread_f = w[-1][1] - w[0][1]
            if spread_f <= 15.0:
                result["tight_gravity_cluster"] = {
                    "detected": True,
                    "label": f"{tf_label}_TIGHT_GRAVITY_CLUSTER",
                    "currencies": [c for c, _ in w],
                    "forces": {c: round(f, 2) for c, f in w},
                    "force_spread": round(spread_f, 2),
                }
                break

    # Angle state résumé
    if result["first_detachment"]["detected"]:
        det_currencies = result["first_detachment"]["currencies"]
        dirs = [d["direction"] for d in det_currencies]
        result["angle_state"] = f"DETACHMENT_{'_'.join(dirs[:2])}"
    elif result["same_angle_cluster"].get("detected"):
        result["angle_state"] = result["same_angle_cluster"]["label"]

    # Speed state résumé
    speeds = [d.get("speed", 0) for d in cur_data.values() if "speed" in d]
    if speeds:
        max_speed = max(abs(s) for s in speeds)
        # Seuil speed relatif au TF (LTF plus sensible)
        speed_threshold = max(0.5, 2.0 / max(1, tf / 5))
        if max_speed > speed_threshold * 2:
            result["speed_state"] = "FAST"
        elif max_speed > speed_threshold:
            result["speed_state"] = "ACTIVE"

    return result


def query_kinematics(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    currencies: Optional[List[str]] = None,
    bars_angle: int = 5,
) -> Dict[str, Any]:
    """
    Kinematics brut multi-TF.
    Pas de filtre [1,5,15] — TFs libres.
    currencies : si None, utilise toutes les devises disponibles dans les rows.
    """
    if currencies is None:
        currencies = list(CURRENCIES)

    result: Dict[str, Any] = {
        "query": "kinematics",
        "symbol": symbol,
        "tfs_requested": tfs,
        "start": start,
        "end": end,
        "timeframes": {},
        "summary": {},
    }

    all_detachments = []
    all_clusters = []

    for tf in tfs:
        try:
            rows = load_force_series(db_path, symbol, tf, start, end)
            if not rows:
                result["timeframes"][tf] = {
                    "status": "NO_DATA",
                    "tf": tf,
                    "tf_label": TF_LABEL.get(tf, f"M{tf}"),
                }
                continue
            tf_result = _kinematics_for_tf(rows, tf, currencies, bars_angle)
            result["timeframes"][tf] = tf_result

            if tf_result.get("first_detachment", {}).get("detected"):
                for det in tf_result["first_detachment"]["currencies"]:
                    all_detachments.append({**det, "tf": tf, "tf_label": TF_LABEL.get(tf, f"M{tf}")})

            if tf_result.get("same_angle_cluster", {}).get("detected"):
                all_clusters.append({
                    **tf_result["same_angle_cluster"],
                    "tf": tf,
                })

        except Exception as exc:
            logger.warning(f"kinematics tf={tf} error: {exc}")
            result["timeframes"][tf] = {
                "status": "ERROR",
                "error": str(exc),
                "tf": tf,
                "tf_label": TF_LABEL.get(tf, f"M{tf}"),
            }

    result["summary"] = {
        "detachments_detected": all_detachments,
        "clusters_detected": all_clusters,
        "tfs_computed": [tf for tf, v in result["timeframes"].items() if v.get("status") != "NO_DATA"],
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 2 — ZONES DYNAMICS (LTF→MTF→HTF)
# ─────────────────────────────────────────────────────────────────────────────

def _zone_state_from_zscore(zscore: float) -> str:
    """Détermine zone_state depuis z-score absolu."""
    az = abs(zscore)
    if az >= ZONE_ZSCORE_THRESHOLDS["RUPTURE"]:
        return "RUPTURE"
    if az >= ZONE_ZSCORE_THRESHOLDS["LEAKING"]:
        return "LEAKING"
    if az >= ZONE_ZSCORE_THRESHOLDS["ACCUMULATING"]:
        return "ACCUMULATING"
    if az >= ZONE_ZSCORE_THRESHOLDS["EARLY_EXTREME"]:
        return "EARLY_EXTREME"
    if az >= ZONE_ZSCORE_THRESHOLDS["PRE_EXTREME"]:
        return "PRE_EXTREME"
    return "NEUTRAL"


def _zones_for_tf(
    rows: List[Dict[str, Any]],
    tf: int,
    currencies: Sequence[str],
) -> Dict[str, Any]:
    """Zone state per devise pour un TF."""
    if not rows:
        return {"status": "NO_DATA", "tf": tf, "tf_label": TF_LABEL.get(tf, f"M{tf}")}

    tf_label = TF_LABEL.get(tf, f"M{tf}")
    result: Dict[str, Any] = {
        "tf": tf,
        "tf_label": tf_label,
        "bars": len(rows),
        "window_start": rows[0]["ts"] if rows else None,
        "window_end": rows[-1]["ts"] if rows else None,
        "currencies": {},
        "zone_summary": {},
    }

    rupture_currencies = []
    accumulating_currencies = []
    neutral_currencies = []

    for currency in currencies:
        series = _extract_series(rows, currency)
        if len(series) < 5:
            result["currencies"][currency] = {"status": "INSUFFICIENT_DATA"}
            continue

        mean_f = _safe_mean(series)
        std_f = _safe_std(series)
        if mean_f is None or std_f is None:
            result["currencies"][currency] = {"status": "CALC_ERROR"}
            continue

        latest = series[-1]
        zscore = _zscore(latest, mean_f, std_f)
        zone_state = _zone_state_from_zscore(zscore)
        direction = "UP" if latest > mean_f else "DOWN"

        # Tension trend : est-ce que le z-score augmente (accumulation) ou diminue (leakage) ?
        zscores_recent = [_zscore(v, mean_f, std_f) for v in series[-5:]]
        tension_trend = "BUILDING" if abs(zscores_recent[-1]) > abs(zscores_recent[0]) else "FADING"

        result["currencies"][currency] = {
            "latest_force": round(latest, 3),
            "zscore": round(zscore, 3),
            "zone_state": zone_state,
            "direction": direction,
            "tension_trend": tension_trend,
            "mean_force": round(mean_f, 3),
            "std_force": round(std_f, 3) if std_f else None,
        }

        if zone_state in ("RUPTURE", "LEAKING"):
            rupture_currencies.append(currency)
        elif zone_state in ("ACCUMULATING", "EARLY_EXTREME"):
            accumulating_currencies.append(currency)
        elif zone_state == "NEUTRAL":
            neutral_currencies.append(currency)

    result["zone_summary"] = {
        "rupture_or_leaking": rupture_currencies,
        "accumulating_or_extreme": accumulating_currencies,
        "neutral": neutral_currencies,
        "compression_detected": len(neutral_currencies) >= 5,
        "dominant_zone": (
            "RUPTURE" if len(rupture_currencies) >= 2
            else "ACCUMULATING" if len(accumulating_currencies) >= 2
            else "NEUTRAL"
        ),
    }

    return result


def query_zones(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    currencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Zone dynamics cascade multi-TF.
    Calcule zone_state per devise per TF, puis cascade HTF→LTF.
    """
    if currencies is None:
        currencies = list(CURRENCIES)

    result: Dict[str, Any] = {
        "query": "zones",
        "symbol": symbol,
        "tfs_requested": tfs,
        "start": start,
        "end": end,
        "timeframes": {},
        "cascade": {},
        "turning_points": [],
    }

    for tf in tfs:
        try:
            rows = load_force_series(db_path, symbol, tf, start, end)
            if not rows:
                result["timeframes"][tf] = {"status": "NO_DATA", "tf": tf}
                continue
            result["timeframes"][tf] = _zones_for_tf(rows, tf, currencies)
        except Exception as exc:
            logger.warning(f"zones tf={tf} error: {exc}")
            result["timeframes"][tf] = {"status": "ERROR", "error": str(exc), "tf": tf}

    # Cascade : comparer zone states entre TFs adjacents
    sorted_tfs = sorted([tf for tf in tfs if result["timeframes"].get(tf, {}).get("status") != "NO_DATA"])
    for i in range(len(sorted_tfs) - 1):
        tf_low = sorted_tfs[i]
        tf_high = sorted_tfs[i + 1]
        z_low = result["timeframes"].get(tf_low, {})
        z_high = result["timeframes"].get(tf_high, {})

        if not z_low.get("currencies") or not z_high.get("currencies"):
            continue

        cascade_key = f"{TF_LABEL.get(tf_low, tf_low)}_vs_{TF_LABEL.get(tf_high, tf_high)}"
        alignments = []
        divergences = []

        for currency in currencies:
            state_low = z_low["currencies"].get(currency, {}).get("zone_state")
            state_high = z_high["currencies"].get(currency, {}).get("zone_state")
            if state_low is None or state_high is None:
                continue

            if state_low == state_high:
                alignments.append(currency)
            elif (state_high in ("RUPTURE", "LEAKING") and state_low in ("NEUTRAL", "PRE_EXTREME")):
                # HTF en rupture mais LTF pas encore — fenêtre de catchup
                result["turning_points"].append({
                    "type": "HTF_RUPTURE_LTF_LAGGING",
                    "currency": currency,
                    "tf_low": tf_low,
                    "tf_high": tf_high,
                    "state_low": state_low,
                    "state_high": state_high,
                    "label": f"HTF_WINDOW_LTF_CATCHUP_{currency}",
                })
            elif (state_low in ("RUPTURE", "LEAKING") and state_high in ("NEUTRAL", "ACCUMULATING")):
                # LTF explose — HTF pas encore confirmé
                result["turning_points"].append({
                    "type": "LTF_RUPTURE_HTF_BUILDING",
                    "currency": currency,
                    "tf_low": tf_low,
                    "tf_high": tf_high,
                    "state_low": state_low,
                    "state_high": state_high,
                    "label": f"LTF_IGNITION_HTF_CONTEXT_{currency}",
                })
            else:
                divergences.append(currency)

        result["cascade"][cascade_key] = {
            "tf_low": tf_low,
            "tf_high": tf_high,
            "aligned_currencies": alignments,
            "divergent_currencies": divergences,
        }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 3 — NODES (fractal nodes + release state propre)
# ─────────────────────────────────────────────────────────────────────────────

def _nodes_from_flow_nodes(
    db_path: str,
    symbol: str,
    tfs: List[int],
    end: str,
    bars: int = 160,
    devises_arg: str = "eur,gbp,usd,jpy,cad,chf,aud",
    max_per_tf: int = 5,
) -> List[Dict[str, Any]]:
    """
    Appelle pf_flow_nodes.detect_flow_nodes_multi_tf.
    Retourne les fractal nodes détectés (PRE_CROSS, TRIPLE, EXTREME_BOUND).
    """
    try:
        from pf_flow_nodes import detect_flow_nodes_multi_tf
        nodes = detect_flow_nodes_multi_tf(
            symbol=symbol,
            timeframes=tfs,
            db_path=db_path,
            bars=bars,
            devises_arg=devises_arg,
            max_per_tf=max_per_tf,
        )
        # Enrichir avec horizon
        for node in nodes:
            tf = node.get("timeframe", 0)
            if tf in HORIZON_TFS["LTF"]:
                node["horizon"] = "LTF"
            elif tf in HORIZON_TFS["MTF"]:
                node["horizon"] = "MTF"
            elif tf in HORIZON_TFS["HTF"]:
                node["horizon"] = "HTF"
            else:
                node["horizon"] = "UNKNOWN"
        return nodes
    except ImportError:
        logger.warning("pf_flow_nodes non disponible — fractal nodes skipped")
        return []
    except Exception as exc:
        logger.warning(f"flow_nodes error: {exc}")
        return []


def _release_state_for_tf(
    rows: List[Dict[str, Any]],
    tf: int,
    symbol: str,
) -> Dict[str, Any]:
    """
    Calcule release_state proprement depuis rows, sans passer par le God File.
    Logique simplifiée mais directe :
      - first_detachment depuis kinematics
      - m_relay depuis bars adjacentes
      - release_state typé
    """
    if len(rows) < 4:
        return {"status": "INSUFFICIENT_DATA", "tf": tf}

    base = symbol[:3].upper()
    quote = symbol[3:].upper() if len(symbol) >= 6 else "USD"

    base_series = _extract_series(rows, base)
    quote_series = _extract_series(rows, quote)

    if len(base_series) < 4 or len(quote_series) < 4:
        return {"status": "MISSING_PAIR_DATA", "tf": tf, "base": base, "quote": quote}

    # Gap base - quote
    gap = [b - q for b, q in zip(base_series[-len(quote_series):], quote_series)]

    # Kinematics de base pour ce TF
    kin = _kinematics_for_tf(rows, tf, [base, quote], bars_angle=5)
    first_det = kin.get("first_detachment", {})

    # Relay : cohérence des 3 dernières barres du gap
    relay_consistent = False
    if len(gap) >= 3:
        last3 = gap[-3:]
        signs = [1 if g > 0 else -1 if g < 0 else 0 for g in last3]
        relay_consistent = len(set(signs)) == 1 and signs[0] != 0

    # Release state logic (adapté depuis V0.8.1)
    det_detected = first_det.get("detected", False)
    det_currencies = first_det.get("currencies", [])
    det_direction = det_currencies[0]["direction"] if det_currencies else None

    # Price coherence : gap delta cohérent avec direction
    gap_delta = gap[-1] - gap[-2] if len(gap) >= 2 else 0
    price_coherent = False
    if det_direction == "UP" and gap_delta > 0:
        price_coherent = True
    elif det_direction == "DOWN" and gap_delta < 0:
        price_coherent = True

    if not det_detected:
        release_state = "RELEASE_REJECTED"
        release_confidence = "LOW"
    elif not price_coherent:
        release_state = "FAKE_RELEASE"
        release_confidence = "LOW"
    elif det_detected and price_coherent and relay_consistent:
        release_state = "RELEASE_CONFIRMED"
        release_confidence = "STRONG"
    elif det_detected and price_coherent and not relay_consistent:
        release_state = "COUNTER_RELEASE_ATTEMPT"
        release_confidence = "MEDIUM"
    else:
        release_state = "RELEASE_ATTEMPT"
        release_confidence = "LOW"

    return {
        "tf": tf,
        "tf_label": TF_LABEL.get(tf, f"M{tf}"),
        "release_state": release_state,
        "release_confidence": release_confidence,
        "first_detachment": first_det,
        "price_coherent": price_coherent,
        "relay_consistent": relay_consistent,
        "gap_delta": round(gap_delta, 3),
        "gap_current": round(gap[-1], 3) if gap else None,
        "label": f"{TF_LABEL.get(tf, tf)}_{release_state}",
    }


def query_nodes(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    horizons: Optional[List[str]] = None,
    bars: int = 160,
    devises_arg: str = "eur,gbp,usd,jpy,cad,chf,aud",
    max_per_tf: int = 5,
) -> Dict[str, Any]:
    """
    Node layer complet :
      - Variant A : fractal nodes (pf_flow_nodes) sur 3 horizons
      - Variant B : release_state propre (sans God File) per TF
    """
    if horizons is None:
        horizons = ["LTF", "MTF", "HTF"]

    # TFs par horizon
    horizon_tfs: List[int] = []
    for h in horizons:
        for tf in HORIZON_TFS.get(h, []):
            if tf in tfs and tf not in horizon_tfs:
                horizon_tfs.append(tf)
    if not horizon_tfs:
        horizon_tfs = tfs

    result: Dict[str, Any] = {
        "query": "nodes",
        "symbol": symbol,
        "tfs_requested": tfs,
        "horizons": horizons,
        "start": start,
        "end": end,
        "fractal_nodes": [],
        "release_states": {},
        "node_summary": {},
    }

    # Variant A — Fractal Nodes
    result["fractal_nodes"] = _nodes_from_flow_nodes(
        db_path=db_path,
        symbol=symbol,
        tfs=horizon_tfs,
        end=end,
        bars=bars,
        devises_arg=devises_arg,
        max_per_tf=max_per_tf,
    )

    # Variant B — Release State per TF
    for tf in horizon_tfs:
        try:
            rows = load_force_series(db_path, symbol, tf, start, end)
            if not rows:
                result["release_states"][tf] = {"status": "NO_DATA", "tf": tf}
                continue
            result["release_states"][tf] = _release_state_for_tf(rows, tf, symbol)
        except Exception as exc:
            logger.warning(f"release_state tf={tf} error: {exc}")
            result["release_states"][tf] = {"status": "ERROR", "error": str(exc), "tf": tf}

    # Summary
    patterns = [n.get("pattern_type") for n in result["fractal_nodes"]]
    release_states_list = [
        v.get("release_state")
        for v in result["release_states"].values()
        if v.get("release_state")
    ]
    confirmed = [r for r in release_states_list if r == "RELEASE_CONFIRMED"]

    result["node_summary"] = {
        "fractal_node_count": len(result["fractal_nodes"]),
        "patterns_detected": list(set(patterns)),
        "release_states_summary": release_states_list,
        "confirmed_releases": len(confirmed),
        "has_pre_cross": "PRE_CROSS_COMPRESSION_NODE" in patterns,
        "has_triple_node": "TRIPLE_NODE_PREPARATION" in patterns or "TRIPLE_CROSS_CLUSTER" in patterns,
        "has_extreme_bound": "EXTREME_BOUND_NODE" in patterns,
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 4 — ORCHESTRA (wrapper pf_orchestral_gravity_v02)
# ─────────────────────────────────────────────────────────────────────────────

def query_orchestra(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    avg_bars: int = 3,
) -> Dict[str, Any]:
    """
    Wrapper orchestral_gravity multi-TF.
    Appelle compute_orchestra_multi_tf (déjà validé en production).
    """
    result: Dict[str, Any] = {
        "query": "orchestra",
        "symbol": symbol,
        "tfs_requested": tfs,
        "start": start,
        "end": end,
    }
    try:
        from pf_orchestral_gravity_v02 import compute_orchestra_multi_tf
        orch = compute_orchestra_multi_tf(
            db_path=db_path,
            symbol=symbol,
            start=start,
            end=end,
            timeframes=tfs,
            avg_bars=avg_bars,
        )
        result.update(orch if isinstance(orch, dict) else {"raw": orch})
        result["status"] = "ORCHESTRAL_ACTIVE"
    except ImportError:
        result["status"] = "ORCHESTRAL_UNAVAILABLE"
        result["note"] = "pf_orchestral_gravity_v02 non disponible"
    except Exception as exc:
        result["status"] = "ORCHESTRAL_ERROR"
        result["error"] = str(exc)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 5 — RELATIONAL (brut, sans P1.2 bridge guard)
# ─────────────────────────────────────────────────────────────────────────────

def query_relational(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    show_mixed: bool = True,
    bars: int = 50,
) -> Dict[str, Any]:
    """
    Relational gravity brut — bypass pf_relational_gravity_bridge.
    Appelle directement pf_relational_gravity_probe per TF.
    show_mixed=True → expose états MIXED SANS censure.
    """
    result: Dict[str, Any] = {
        "query": "relational",
        "symbol": symbol,
        "tfs_requested": tfs,
        "start": start,
        "end": end,
        "show_mixed": show_mixed,
        "timeframes": {},
    }
    try:
        from pf_relational_gravity_probe import analyze_relational_gravity
        for tf in tfs:
            try:
                rg = analyze_relational_gravity(
                    db_path=db_path,
                    symbol=symbol,
                    timeframe=tf,
                    bars=bars,
                )
                # Si MIXED et show_mixed=False, on le filtre
                if not show_mixed:
                    state = rg.get("primary_state", "")
                    if "MIXED" in str(state):
                        result["timeframes"][tf] = {
                            "status": "MIXED_FILTERED",
                            "tf": tf,
                            "note": "MIXED state filtered (show_mixed=False)",
                        }
                        continue
                result["timeframes"][tf] = rg
            except Exception as exc:
                logger.warning(f"relational tf={tf} error: {exc}")
                result["timeframes"][tf] = {"status": "ERROR", "error": str(exc), "tf": tf}
    except ImportError:
        result["status"] = "RELATIONAL_UNAVAILABLE"
        result["note"] = "pf_relational_gravity_probe non disponible"
    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 6 — FRACTAL COHERENCE (LTF/MTF/HTF phase sync)
# ─────────────────────────────────────────────────────────────────────────────

def query_fractal_coherence(
    db_path: str,
    symbol: str,
    main_tf: int,
    sub_tfs: List[int],
    start: str,
    end: str,
    currencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyse comment sub_tfs reflètent ou divergent de main_tf.
    Mesure : phase_sync / phase_opposition / lag / catchup.
    """
    if currencies is None:
        currencies = list(CURRENCIES)

    result: Dict[str, Any] = {
        "query": "fractal_coherence",
        "symbol": symbol,
        "main_tf": main_tf,
        "main_tf_label": TF_LABEL.get(main_tf, f"M{main_tf}"),
        "sub_tfs": sub_tfs,
        "start": start,
        "end": end,
        "coherence": {},
        "summary": {},
    }

    # Charger main_tf
    try:
        main_rows = load_force_series(db_path, symbol, main_tf, start, end)
        if not main_rows:
            result["status"] = "MAIN_TF_NO_DATA"
            return result
    except Exception as exc:
        result["status"] = f"MAIN_TF_ERROR:{exc}"
        return result

    # Direction du main_tf par devise
    main_directions: Dict[str, str] = {}
    main_slopes: Dict[str, float] = {}
    for currency in currencies:
        series = _extract_series(main_rows, currency)
        if len(series) < 3:
            continue
        slope = _slope(series[-5:] if len(series) >= 5 else series)
        main_slopes[currency] = slope
        main_directions[currency] = "UP" if slope > 0 else "DOWN" if slope < 0 else "FLAT"

    result["main_tf_directions"] = main_directions

    sync_scores: List[float] = []

    for sub_tf in sub_tfs:
        if sub_tf == main_tf:
            continue
        try:
            sub_rows = load_force_series(db_path, symbol, sub_tf, start, end)
            if not sub_rows:
                result["coherence"][sub_tf] = {"status": "NO_DATA", "tf": sub_tf}
                continue

            alignments = []
            oppositions = []
            lags = []
            currency_details: Dict[str, Dict] = {}

            for currency in currencies:
                main_series = _extract_series(main_rows, currency)
                sub_series = _extract_series(sub_rows, currency)
                if len(main_series) < 3 or len(sub_series) < 3:
                    continue

                main_slope = _slope(main_series[-5:] if len(main_series) >= 5 else main_series)
                sub_slope = _slope(sub_series[-5:] if len(sub_series) >= 5 else sub_series)

                main_dir = "UP" if main_slope > 0.01 else "DOWN" if main_slope < -0.01 else "FLAT"
                sub_dir = "UP" if sub_slope > 0.01 else "DOWN" if sub_slope < -0.01 else "FLAT"

                # Phase relation
                if main_dir == sub_dir and main_dir != "FLAT":
                    phase = "SYNC"
                    alignments.append(currency)
                elif main_dir != "FLAT" and sub_dir != "FLAT" and main_dir != sub_dir:
                    phase = "OPPOSITION"
                    oppositions.append(currency)
                else:
                    phase = "NEUTRAL"

                # Lag détection : sub_tf angle plus faible que main_tf
                slope_ratio = abs(sub_slope) / max(abs(main_slope), 0.001)
                lag_detected = phase == "SYNC" and slope_ratio < 0.5
                if lag_detected:
                    lags.append(currency)

                currency_details[currency] = {
                    "main_direction": main_dir,
                    "sub_direction": sub_dir,
                    "phase": phase,
                    "lag": lag_detected,
                    "slope_ratio": round(slope_ratio, 3),
                }

            total = len(currency_details)
            sync_pct = len(alignments) / total if total > 0 else 0.0
            sync_scores.append(sync_pct)

            # Cohérence globale
            if sync_pct >= 0.75:
                coherence_label = "STRONG_SYNC"
            elif sync_pct >= 0.5:
                coherence_label = "PARTIAL_SYNC"
            elif len(oppositions) / max(total, 1) >= 0.5:
                coherence_label = "PHASE_OPPOSITION"
            else:
                coherence_label = "MIXED_FIELD"

            result["coherence"][sub_tf] = {
                "tf": sub_tf,
                "tf_label": TF_LABEL.get(sub_tf, f"M{sub_tf}"),
                "coherence_label": coherence_label,
                "sync_pct": round(sync_pct, 3),
                "aligned_currencies": alignments,
                "opposed_currencies": oppositions,
                "lagging_currencies": lags,
                "currencies": currency_details,
            }

        except Exception as exc:
            logger.warning(f"fractal_coherence sub_tf={sub_tf} error: {exc}")
            result["coherence"][sub_tf] = {"status": "ERROR", "error": str(exc), "tf": sub_tf}

    # Summary global
    global_sync = fmean(sync_scores) if sync_scores else 0.0
    result["summary"] = {
        "global_sync_score": round(global_sync, 3),
        "global_coherence": (
            "FRACTAL_ALIGNED" if global_sync >= 0.7
            else "FRACTAL_PARTIAL" if global_sync >= 0.4
            else "FRACTAL_DIVERGENT"
        ),
        "sub_tfs_computed": [tf for tf in sub_tfs if tf != main_tf and result["coherence"].get(tf, {}).get("status") != "NO_DATA"],
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 7 — ZONE TURNING POINTS (croisement zones + nodes + fractal)
# ─────────────────────────────────────────────────────────────────────────────

def query_zone_turning_points(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
) -> Dict[str, Any]:
    """
    Détecte naissances de mouvement depuis zone.
    Croise : zone_state + kinematics first_detachment + fractal coherence.
    """
    result: Dict[str, Any] = {
        "query": "turning_points",
        "symbol": symbol,
        "tfs_requested": tfs,
        "start": start,
        "end": end,
        "events": [],
        "summary": {},
    }

    # Calcul zones et kinematics en parallèle
    zones = query_zones(db_path, symbol, tfs, start, end)
    kin = query_kinematics(db_path, symbol, tfs, start, end)

    sorted_tfs = sorted(tfs)

    for i, tf in enumerate(sorted_tfs):
        tf_zone = zones["timeframes"].get(tf, {})
        tf_kin = kin["timeframes"].get(tf, {})

        if tf_zone.get("status") in ("NO_DATA", "ERROR"):
            continue

        zone_summary = tf_zone.get("zone_summary", {})
        first_det = tf_kin.get("first_detachment", {})

        # TURNING_POINT_BIRTH : ACCUMULATING/RUPTURE + first_detachment détecté
        has_extreme = bool(zone_summary.get("rupture_or_leaking") or zone_summary.get("accumulating_or_extreme"))
        has_detachment = bool(first_det.get("detected"))

        if has_extreme and has_detachment:
            det_currencies = first_det.get("currencies", [])
            event: Dict[str, Any] = {
                "type": "TURNING_POINT_BIRTH",
                "tf": tf,
                "tf_label": TF_LABEL.get(tf, f"M{tf}"),
                "timestamp_end": end,
                "detachment_currencies": det_currencies,
                "zone_rupture_currencies": zone_summary.get("rupture_or_leaking", []),
                "zone_accumulating_currencies": zone_summary.get("accumulating_or_extreme", []),
                "label": f"TURNING_POINT_BIRTH_{TF_LABEL.get(tf, tf)}",
            }

            # Si TF supérieur existe, qualifier
            if i + 1 < len(sorted_tfs):
                tf_next = sorted_tfs[i + 1]
                tf_next_zone = zones["timeframes"].get(tf_next, {})
                next_summary = tf_next_zone.get("zone_summary", {})
                next_has_extreme = bool(
                    next_summary.get("rupture_or_leaking")
                    or next_summary.get("accumulating_or_extreme")
                )
                if next_has_extreme:
                    event["type"] = "TURNING_POINT_CONFIRMED"
                    event["label"] = f"TURNING_POINT_CONFIRMED_{TF_LABEL.get(tf, tf)}_PLUS_{TF_LABEL.get(tf_next, tf_next)}"
                    event["higher_tf_zone"] = tf_next
                else:
                    event["note"] = f"HTF {TF_LABEL.get(tf_next, tf_next)} not yet extreme — watch"

            result["events"].append(event)

        elif has_extreme and not has_detachment:
            # Zone chargée mais pas encore d'ignition LTF
            result["events"].append({
                "type": "TURNING_POINT_WATCH",
                "tf": tf,
                "tf_label": TF_LABEL.get(tf, f"M{tf}"),
                "timestamp_end": end,
                "zone_accumulating": zone_summary.get("accumulating_or_extreme", []),
                "zone_rupture": zone_summary.get("rupture_or_leaking", []),
                "label": f"TURNING_POINT_WATCH_{TF_LABEL.get(tf, tf)}_ZONE_LOADED",
                "note": "zone charged but no LTF ignition yet",
            })

    # Cascade turning points depuis zones
    for tp in zones.get("turning_points", []):
        result["events"].append(tp)

    # Summary
    births = [e for e in result["events"] if e["type"] == "TURNING_POINT_BIRTH"]
    confirmed = [e for e in result["events"] if e["type"] == "TURNING_POINT_CONFIRMED"]
    watches = [e for e in result["events"] if e["type"] == "TURNING_POINT_WATCH"]

    result["summary"] = {
        "total_events": len(result["events"]),
        "confirmed_count": len(confirmed),
        "birth_count": len(births),
        "watch_count": len(watches),
        "priority": (
            "CONFIRMED" if confirmed
            else "BIRTH" if births
            else "WATCH" if watches
            else "NONE"
        ),
    }

    return result


# ─────────────────────────────────────────────────────────────────────────────
# QUERY FULL — toutes les couches en une passe
# ─────────────────────────────────────────────────────────────────────────────

def query_full(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    horizons: Optional[List[str]] = None,
    currencies: Optional[List[str]] = None,
    avg_bars: int = 3,
    show_mixed: bool = True,
    main_tf_for_fractal: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Full lab session : toutes les couches en une passe.
    main_tf_for_fractal : TF de référence pour fractal coherence (défaut = max(tfs))
    """
    if main_tf_for_fractal is None:
        main_tf_for_fractal = max(tfs)
    sub_tfs = [tf for tf in tfs if tf != main_tf_for_fractal]

    result: Dict[str, Any] = {
        "query": "full",
        "symbol": symbol,
        "tfs": tfs,
        "horizons": horizons or ["LTF", "MTF", "HTF"],
        "start": start,
        "end": end,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    queries = [
        ("kinematics", lambda: query_kinematics(db_path, symbol, tfs, start, end, currencies)),
        ("zones", lambda: query_zones(db_path, symbol, tfs, start, end, currencies)),
        ("nodes", lambda: query_nodes(db_path, symbol, tfs, start, end, horizons)),
        ("turning_points", lambda: query_zone_turning_points(db_path, symbol, tfs, start, end)),
        ("orchestra", lambda: query_orchestra(db_path, symbol, tfs, start, end, avg_bars)),
        ("relational", lambda: query_relational(db_path, symbol, tfs, start, end, show_mixed)),
        ("fractal", lambda: query_fractal_coherence(db_path, symbol, main_tf_for_fractal, sub_tfs, start, end, currencies)),
    ]

    for name, fn in queries:
        try:
            result[name] = fn()
        except Exception as exc:
            logger.error(f"query_full {name} error: {exc}")
            result[name] = {"status": "ERROR", "error": str(exc)}

    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 8 — RELATIONAL GRAVITY DIRECT (probe, bypass bridge P1.2)
# ─────────────────────────────────────────────────────────────────────────────

def query_relational_gravity(
    db_path: str,
    symbol: str,
    tfs: List[int],
    bars: int = 30,
    show_mixed: bool = True,
) -> Dict[str, Any]:
    """
    Relational gravity probe direct — run_relational_gravity_probe per TF.
    Bypass total du bridge P1.2 — expose les états MIXED sans censure.
    """
    result: Dict[str, Any] = {
        "query": "relational_gravity",
        "symbol": symbol,
        "tfs_requested": tfs,
        "bars": bars,
        "show_mixed": show_mixed,
        "timeframes": {},
        "cross_tf_summary": {},
    }
    try:
        from pf_relational_gravity_probe import run_relational_gravity_probe, result_to_dict
    except ImportError:
        result["status"] = "RELATIONAL_UNAVAILABLE"
        result["note"] = "pf_relational_gravity_probe non disponible"
        return result

    leaders: List[str] = []
    antagonists: List[str] = []
    states: List[str] = []

    for tf in tfs:
        try:
            rg = run_relational_gravity_probe(db_path=db_path, symbol=symbol, timeframe=tf, bars=bars)
            rg_dict = result_to_dict(rg)
            if not show_mixed and "MIXED" in str(rg_dict.get("primary_state", "")):
                rg_dict["_mixed_filtered"] = True
            result["timeframes"][tf] = rg_dict
            leaders.append(rg_dict.get("leader", "?"))
            antagonists.append(rg_dict.get("antagonist", "?"))
            states.append(rg_dict.get("primary_state", "?"))
        except Exception as exc:
            logger.warning(f"relational_gravity tf={tf} error: {exc}")
            result["timeframes"][tf] = {"status": "ERROR", "error": str(exc), "tf": tf}

    from collections import Counter
    leader_counts = Counter(leaders)
    dominant_leader = leader_counts.most_common(1)[0][0] if leader_counts else "?"
    mixed = len(set(leaders)) > 1
    result["cross_tf_summary"] = {
        "dominant_leader": dominant_leader if not mixed else "MIXED",
        "leader_by_tf": dict(zip(tfs, leaders)),
        "antagonist_by_tf": dict(zip(tfs, antagonists)),
        "states_by_tf": dict(zip(tfs, states)),
        "leader_conflict": mixed,
        "topline_reliable": not mixed,
    }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 9 — TEMPORAL DENSITY
# ─────────────────────────────────────────────────────────────────────────────

def query_temporal_density(
    db_path: str,
    symbol: str,
    tfs: List[int],
    window: int = 20,
    currencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Temporal density multi-TF.
    Mesure COMPRESSED / ACTIVE / NEUTRAL / HOLLOW / DEAD per devise per TF.
    """
    result: Dict[str, Any] = {
        "query": "temporal_density",
        "symbol": symbol,
        "tfs_requested": tfs,
        "window": window,
        "timeframes": {},
        "summary": {},
    }
    try:
        from pf_temporal_density import scan_all_currencies
    except ImportError:
        result["status"] = "TEMPORAL_DENSITY_UNAVAILABLE"
        result["note"] = "pf_temporal_density non disponible"
        return result

    all_active: List[Dict] = []
    all_dead: List[Dict] = []

    for tf in tfs:
        try:
            results = scan_all_currencies(
                db_path=db_path, symbol=symbol, timeframe=tf,
                window=window, currencies=currencies,
            )
            by_currency = {r["currency"]: r for r in results}
            result["timeframes"][tf] = {
                "tf_label": TF_LABEL.get(tf, f"M{tf}"),
                "currencies": by_currency,
                "sorted": results,
            }
            all_active.extend([{**r, "tf": tf} for r in results if r["state"] in ("COMPRESSED", "ACTIVE")])
            all_dead.extend([{**r, "tf": tf} for r in results if r["state"] in ("DEAD", "HOLLOW")])
        except Exception as exc:
            logger.warning(f"temporal_density tf={tf} error: {exc}")
            result["timeframes"][tf] = {"status": "ERROR", "error": str(exc), "tf": tf}

    result["summary"] = {
        "most_active": [
            {"currency": r["currency"], "tf": r["tf"], "state": r["state"], "score": r["density_score"]}
            for r in sorted(all_active, key=lambda x: x["density_score"], reverse=True)[:8]
        ],
        "dead_or_hollow": [
            {"currency": r["currency"], "tf": r["tf"], "state": r["state"]}
            for r in all_dead[:5]
        ],
        "most_active_currency": all_active[0]["currency"] if all_active else None,
    }
    return result


# ─────────────────────────────────────────────────────────────────────────────
# QUERY FULL V2 — toutes les couches + density + relational_gravity
# ─────────────────────────────────────────────────────────────────────────────

def query_full_v2(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    horizons: Optional[List[str]] = None,
    currencies: Optional[List[str]] = None,
    avg_bars: int = 3,
    show_mixed: bool = True,
    main_tf_for_fractal: Optional[int] = None,
    density_window: int = 20,
    relational_bars: int = 30,
) -> Dict[str, Any]:
    """
    Full lab session V2 : toutes les couches + temporal_density + relational_gravity.
    """
    if main_tf_for_fractal is None:
        main_tf_for_fractal = max(tfs)
    sub_tfs = [tf for tf in tfs if tf != main_tf_for_fractal]

    result: Dict[str, Any] = {
        "query": "full_v2",
        "symbol": symbol,
        "tfs": tfs,
        "horizons": horizons or ["LTF", "MTF", "HTF"],
        "start": start,
        "end": end,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    queries = [
        ("kinematics",        lambda: query_kinematics(db_path, symbol, tfs, start, end, currencies)),
        ("zones",             lambda: query_zones(db_path, symbol, tfs, start, end, currencies)),
        ("nodes",             lambda: query_nodes(db_path, symbol, tfs, start, end, horizons)),
        ("turning_points",    lambda: query_zone_turning_points(db_path, symbol, tfs, start, end)),
        ("orchestra",         lambda: query_orchestra(db_path, symbol, tfs, start, end, avg_bars)),
        ("relational_gravity",lambda: query_relational_gravity(db_path, symbol, tfs, relational_bars, show_mixed)),
        ("temporal_density",  lambda: query_temporal_density(db_path, symbol, tfs, density_window, currencies)),
        ("fractal",           lambda: query_fractal_coherence(db_path, symbol, main_tf_for_fractal, sub_tfs, start, end, currencies)),
    ]

    for name, fn in queries:
        try:
            result[name] = fn()
        except Exception as exc:
            logger.error(f"query_full_v2 {name} error: {exc}")
            result[name] = {"status": "ERROR", "error": str(exc)}

    return result


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 10 — COALITION DETECTION (wrapper)
# ─────────────────────────────────────────────────────────────────────────────

def query_coalitions(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: Optional[str] = None,
    end: Optional[str] = None,
    bars: int = 50,
    min_cohesion: float = 0.62,
    min_field_score: float = 0.45,
) -> Dict[str, Any]:
    """
    Layer 10 — Coalition detection multi-TF.
    Delegates to pf_lab_coalitions.query_coalitions().
    Returns active_relations / strong_coalitions / weak_field + cross_tf_summary.
    """
    if not _COALITIONS_OK:
        return {"status": "ERROR", "error": "pf_lab_coalitions not available — check import"}
    return _query_coalitions(
        db_path=db_path,
        symbol=symbol,
        tfs=tfs,
        start=start,
        end=end,
        bars=bars,
        min_cohesion=min_cohesion,
        min_field_score=min_field_score,
    )


# ─────────────────────────────────────────────────────────────────────────────
# COUCHE 11 — TENSION SIGNATURE (wrapper)
# ─────────────────────────────────────────────────────────────────────────────

def query_tension_signature(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: Optional[str] = None,
    end: Optional[str] = None,
    bars: int = 30,
    window: int = 5,
) -> Dict[str, Any]:
    """
    Layer 11 — Tension Signature multi-TF per devise.
    ELASTIC_LOADED / DIRECTIONAL_MOVE / DEAD_CURRENCY per devise per TF.
    Delegates to pf_lab_tension.query_tension_signature().
    """
    if not _TENSION_OK:
        return {"status": "ERROR", "error": "pf_lab_tension not available — check import"}
    return _query_tension(
        db_path=db_path,
        symbol=symbol,
        tfs=tfs,
        start=start,
        end=end,
        bars=bars,
        window=window,
    )


# ─────────────────────────────────────────────────────────────────────────────
# QUERY FULL V3 — toutes couches 1-11 (coalitions + tension)
# ─────────────────────────────────────────────────────────────────────────────

def query_full_v3(
    db_path: str,
    symbol: str,
    tfs: List[int],
    start: str,
    end: str,
    horizons: Optional[List[str]] = None,
    currencies: Optional[List[str]] = None,
    avg_bars: int = 3,
    show_mixed: bool = True,
    main_tf_for_fractal: Optional[int] = None,
    density_window: int = 20,
    relational_bars: int = 30,
    coalition_bars: int = 50,
    coalition_cohesion: float = 0.62,
    coalition_field_score: float = 0.45,
    tension_bars: int = 30,
    tension_window: int = 5,
) -> Dict[str, Any]:
    """
    Full lab session V3 : couches 1-11.
    Ajoute coalitions (layer 10) + tension_signature (layer 11) à full_v2.
    """
    if main_tf_for_fractal is None:
        main_tf_for_fractal = max(tfs)
    sub_tfs = [tf for tf in tfs if tf != main_tf_for_fractal]

    result: Dict[str, Any] = {
        "query": "full_v3",
        "symbol": symbol,
        "tfs": tfs,
        "horizons": horizons or ["LTF", "MTF", "HTF"],
        "start": start,
        "end": end,
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }

    queries = [
        ("kinematics",        lambda: query_kinematics(db_path, symbol, tfs, start, end, currencies)),
        ("zones",             lambda: query_zones(db_path, symbol, tfs, start, end, currencies)),
        ("nodes",             lambda: query_nodes(db_path, symbol, tfs, start, end, horizons)),
        ("turning_points",    lambda: query_zone_turning_points(db_path, symbol, tfs, start, end)),
        ("orchestra",         lambda: query_orchestra(db_path, symbol, tfs, start, end, avg_bars)),
        ("relational_gravity",lambda: query_relational_gravity(db_path, symbol, tfs, relational_bars, show_mixed)),
        ("temporal_density",  lambda: query_temporal_density(db_path, symbol, tfs, density_window, currencies)),
        ("fractal",           lambda: query_fractal_coherence(db_path, symbol, main_tf_for_fractal, sub_tfs, start, end, currencies)),
        ("coalitions",        lambda: query_coalitions(db_path, symbol, tfs, start, end, coalition_bars, coalition_cohesion, coalition_field_score)),
        ("tension_signature", lambda: query_tension_signature(db_path, symbol, tfs, start, end, tension_bars, tension_window)),
    ]

    for name, fn in queries:
        try:
            result[name] = fn()
        except Exception as exc:
            logger.error(f"query_full_v3 {name} error: {exc}")
            result[name] = {"status": "ERROR", "error": str(exc)}

    return result
