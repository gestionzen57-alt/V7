#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — pf_currency_energy_probe.py
Version : 0.2

Mission :
    Mesurer la force vivante contextualisée (Currency Energy) de chaque devise
    à partir de force_snapshots.

Doctrine :
    Energy ≠ direction.
    Energy ≠ signal BUY/SELL.
    Energy = intensité comportementale d'une devise dans son champ actuel.

    Une devise peut avoir une énergie élevée dans n'importe quelle direction.
    Ce module ne dit pas où aller. Il dit qui est vivant.

Architecture :
    Lecture seule sur force_snapshots.
    Imports :
        pf_personalities   → behavioral_zscore, DEVISE_PROFILES
        pf_zone_dynamics   → zone_tension, absorption_escape_state, persistence
        pf_force_kinematics → speed, angle, acceleration
        pf_db_freshness_probe → capture_quality_penalty

Interdits :
    - Aucune écriture dans powerflow.db
    - Ne pas toucher capture_bridge.py
    - Pas de Telegram
    - Pas de signal directionnel
    - Ne pas refactoriser les modules importés

Sortie :
    output/currency_energy_state.json

Formule V0.1 :
    energy_raw =
        0.25 × zone_tension_norm
      + 0.20 × behavioral_zscore_norm
      + 0.15 × speed_norm
      + 0.10 × angle_norm
      + 0.10 × acceleration_norm
      + 0.10 × persistence_norm
      + 0.05 × basket_deviation_norm
      + 0.05 × htf_context_norm

    energy_score = clip(energy_raw, 0.0, 1.0) × (1.0 - capture_quality_penalty)

JSON produit :
    output/currency_energy_state.json
"""

from __future__ import annotations

import json
import math
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# ── Imports PowerFlow (lecture seule, aucun refactor) ─────────────────────────
try:
    from pf_personalities import (
        DEVISE_PROFILES,
        behavioral_index,
        DevisePersonality,
    )
    _HAS_PERSONALITIES = True
except ImportError:
    _HAS_PERSONALITIES = False

try:
    from pf_zone_dynamics import analyze_zone_dynamics, ZoneDiagnosis
    _HAS_ZONE = True
except ImportError:
    _HAS_ZONE = False

try:
    from pf_force_kinematics import (
        load_rows as kin_load_rows,
        build_segments,
        acceleration_table,
    )
    _HAS_KINEMATICS = True
except ImportError:
    _HAS_KINEMATICS = False

try:
    from pf_db_freshness_probe import build_db_freshness_state
    _HAS_FRESHNESS = True
except ImportError:
    _HAS_FRESHNESS = False

try:
    from pf_tension_signature import compute_tension_signature
    _HAS_TENSION_SIGNATURE = True
except ImportError:
    _HAS_TENSION_SIGNATURE = False


# ═══════════════════════════════════════════════════════════════════════════════
#  CONSTANTES
# ═══════════════════════════════════════════════════════════════════════════════

VERSION = "0.2"
MODULE_NAME = "pf_currency_energy_probe"

CURRENCIES: Tuple[str, ...] = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD", "NZD")

FORCE_COLS: Dict[str, str] = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
    "NZD": "force_nzd",
}

FORCE_TABLE_CANDIDATES: Tuple[str, ...] = ("force_snapshots", "force_snapshots_v2")

# Poids de la formule V0.1
WEIGHTS: Dict[str, float] = {
    "zone_tension":       0.25,
    "behavioral_zscore":  0.20,
    "speed":              0.15,
    "angle":              0.10,
    "acceleration":       0.10,
    "persistence":        0.10,
    "basket_deviation":   0.05,
    "htf_context":        0.05,
    "elastic_tension":    0.10,
}

# Capture quality : pénalité max 0.80 (jamais annulation totale)
PENALTY_MAX = 0.80
PENALTY_STALE_MINUTES = 30.0

# HTF timeframes pour htf_context_score
DEFAULT_HTF_TFS: Tuple[int, ...] = (15, 30, 60)

# Seuils energy labels
ENERGY_HIGH_THRESHOLD   = 0.75
ENERGY_MEDIUM_THRESHOLD = 0.50
ENERGY_LOW_THRESHOLD    = 0.25

# Confidence : dégradée si composantes manquantes
CONFIDENCE_FULL    = "HIGH"
CONFIDENCE_PARTIAL = "MEDIUM"
CONFIDENCE_LOW     = "LOW"


# ═══════════════════════════════════════════════════════════════════════════════
#  DATACLASSES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class EnergyComponents:
    """Composantes normalisées [0.0, 1.0] de l'énergie d'une devise."""
    zone_tension_norm:      float = 0.0
    behavioral_zscore_norm: float = 0.0
    speed_norm:             float = 0.0
    angle_norm:             float = 0.0
    acceleration_norm:      float = 0.0
    persistence_norm:       float = 0.0
    basket_deviation_norm:  float = 0.0
    htf_context_norm:       float = 0.0
    elastic_tension_score:  float = 0.0

    def to_dict(self) -> Dict[str, float]:
        return {
            "zone_tension_norm":      round(self.zone_tension_norm, 4),
            "behavioral_zscore_norm": round(self.behavioral_zscore_norm, 4),
            "speed_norm":             round(self.speed_norm, 4),
            "angle_norm":             round(self.angle_norm, 4),
            "acceleration_norm":      round(self.acceleration_norm, 4),
            "persistence_norm":       round(self.persistence_norm, 4),
            "basket_deviation_norm":  round(self.basket_deviation_norm, 4),
            "htf_context_norm":       round(self.htf_context_norm, 4),
            "elastic_tension_score":  round(self.elastic_tension_score, 4),
        }


@dataclass
class EnergyResult:
    """Résultat complet d'énergie pour une devise sur un TF."""
    currency:                  str
    timeframe:                 int
    energy_raw_score:          float
    energy_score:              float
    energy_label:              str
    energy_confidence:         str
    capture_quality_penalty:   float
    components:                EnergyComponents
    raw_signed:                Dict[str, Any]
    absorption_escape_state:   str
    contextual_tags:           List[str]
    energy_context:            List[str]
    elastic_tension_score:     float
    elastic_tension_label:     str
    missing_modules:           List[str]
    notes:                     str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "currency":                self.currency,
            "timeframe":               self.timeframe,
            "energy_raw_score":        round(self.energy_raw_score, 4),
            "energy_score":            round(self.energy_score, 4),
            "energy_label":            self.energy_label,
            "energy_confidence":       self.energy_confidence,
            "capture_quality_penalty": round(self.capture_quality_penalty, 4),
            "components":              self.components.to_dict(),
            "raw_signed":              self.raw_signed,
            "absorption_escape_state": self.absorption_escape_state,
            "contextual_tags":         self.contextual_tags,
            "energy_context":          self.energy_context,
            "elastic_tension_score":   round(self.elastic_tension_score, 4),
            "elastic_tension_label":   self.elastic_tension_label,
            "missing_modules":         self.missing_modules,
            "notes":                   self.notes,
        }


# ═══════════════════════════════════════════════════════════════════════════════
#  UTILITAIRES BAS NIVEAU
# ═══════════════════════════════════════════════════════════════════════════════

def _clip(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _norm(v: float, scale: float) -> float:
    """Normalise |v| / scale → [0.0, 1.0]."""
    if scale <= 0:
        return 0.0
    return _clip(abs(v) / scale, 0.0, 1.0)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _now_iso() -> str:
    return _iso(datetime.now(timezone.utc))


def _safe_float(v: Any) -> Optional[float]:
    if v is None:
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _energy_label(score: float) -> str:
    if score >= ENERGY_HIGH_THRESHOLD:
        return "ENERGY_HIGH"
    if score >= ENERGY_MEDIUM_THRESHOLD:
        return "ENERGY_MEDIUM"
    if score >= ENERGY_LOW_THRESHOLD:
        return "ENERGY_LOW"
    return "ENERGY_WEAK"


def _confidence(missing: List[str]) -> str:
    n = len(missing)
    if n == 0:
        return CONFIDENCE_FULL
    if n <= 2:
        return CONFIDENCE_PARTIAL
    return CONFIDENCE_LOW


# ═══════════════════════════════════════════════════════════════════════════════
#  LECTURE DB — READ-ONLY
# ═══════════════════════════════════════════════════════════════════════════════

def _connect_ro(db_path: Path) -> sqlite3.Connection:
    uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _pick_table(conn: sqlite3.Connection) -> str:
    tables = {r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()}
    for candidate in FORCE_TABLE_CANDIDATES:
        if candidate in tables:
            return candidate
    raise RuntimeError("Aucune table force_snapshots trouvée dans la DB.")


def _available_force_cols(conn: sqlite3.Connection, table: str) -> Dict[str, str]:
    """Retourne le sous-ensemble de FORCE_COLS effectivement présent dans la table."""
    cols = {r[1].lower() for r in conn.execute(
        f'PRAGMA table_info("{table}")'
    ).fetchall()}
    return {c: col for c, col in FORCE_COLS.items() if col in cols}


def _load_force_rows(
    db_path: Path,
    symbol: str,
    timeframe: int,
    bars: int,
    available_cols: Dict[str, str],
    table: str,
) -> List[Dict[str, Any]]:
    """
    Charge les N dernières barres de force_snapshots pour un symbol/TF.
    Retourne une liste de dicts {currency: force_value, 'created_at': str}.
    Lecture seule.
    """
    select_cols = ["created_at"] + list(available_cols.values())
    col_list = ", ".join(f'"{c}"' for c in select_cols)

    sql = (
        f'SELECT {col_list} FROM "{table}" '
        f'WHERE UPPER(symbol)=? AND timeframe=? '
        f'ORDER BY created_at DESC LIMIT ?'
    )
    with _connect_ro(db_path) as conn:
        conn.row_factory = sqlite3.Row
        raw = conn.execute(sql, (symbol.upper(), timeframe, bars)).fetchall()

    rows: List[Dict[str, Any]] = []
    for r in reversed(raw):
        d: Dict[str, Any] = {"created_at": str(r["created_at"])}
        for currency, col in available_cols.items():
            d[currency] = _safe_float(r[col])
        rows.append(d)
    return rows


def _build_devise_cols(available: Dict[str, str]) -> List[Tuple[str, str]]:
    """Construit le format devise_cols attendu par pf_personalities."""
    return [(c.lower(), col) for c, col in available.items()]


def _build_rows_for_behavioral(
    force_rows: List[Dict[str, Any]],
    available: Dict[str, str],
) -> List[Tuple]:
    """
    Reconstruit les tuples (bar_time, val1, val2, ...) dans l'ordre de devise_cols,
    compatibles avec pf_personalities.behavioral_index().
    """
    devise_cols = _build_devise_cols(available)
    out: List[Tuple] = []
    for row in force_rows:
        vals = [row["created_at"]]
        for currency, _ in devise_cols:
            vals.append(row.get(currency.upper()))
        out.append(tuple(vals))
    return out


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPOSANTE : BASKET DEVIATION
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_basket_deviation(force_rows: List[Dict[str, Any]], available: Dict[str, str]) -> Dict[str, float]:
    """
    Écart signé de chaque devise par rapport à la moyenne du panier sur la dernière barre.
    Retourne dict {CURRENCY: deviation_signed}.
    """
    if not force_rows:
        return {}
    last = force_rows[-1]
    values: Dict[str, float] = {}
    for c in available:
        v = last.get(c)
        if v is not None:
            values[c] = v
    if not values:
        return {}
    mean_val = sum(values.values()) / len(values)
    return {c: round(v - mean_val, 4) for c, v in values.items()}


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPOSANTE : ELASTIC TENSION SIGNATURE — P_NEXT_1
# ═══════════════════════════════════════════════════════════════════════════════

def _fetch_force_series_ro(
    db_path: Path,
    symbol: str,
    timeframe: int,
    force_col: str,
    bars: int,
    table: str,
) -> List[Optional[float]]:
    """Charge une série force_* brute en lecture seule, ordre chronologique."""
    sql = (
        f'SELECT "{force_col}" FROM "{table}" '
        f'WHERE UPPER(symbol)=? AND timeframe=? '
        f'ORDER BY created_at DESC LIMIT ?'
    )
    try:
        with _connect_ro(db_path) as conn:
            rows = conn.execute(sql, (symbol.upper(), timeframe, bars)).fetchall()
        return [_safe_float(row[0]) for row in reversed(rows)]
    except Exception:
        return []


def _compute_elastic_tension_component(
    db_path: Path,
    symbol: str,
    currency: str,
    available_cols: Dict[str, str],
    table: str,
    bars: int,
) -> Tuple[float, str, Dict[str, Any]]:
    """
    P_NEXT_1 : composante élastique observationnelle.

    Guard dur : si len(series_tf5) < 20 -> score 0.0.
    Energy != signal : cette composante qualifie l'énergie, elle ne décide pas.
    """
    if currency not in available_cols:
        return 0.0, "NO_FORCE_COLUMN", {"tf": 5, "n_bars": 0}
    if not _HAS_TENSION_SIGNATURE:
        return 0.0, "MODULE_UNAVAILABLE", {"tf": 5, "n_bars": 0}

    series_tf5 = _fetch_force_series_ro(
        db_path=db_path,
        symbol=symbol,
        timeframe=5,
        force_col=available_cols[currency],
        bars=max(20, bars),
        table=table,
    )
    if len(series_tf5) < 20:
        return 0.0, "INSUFFICIENT_DATA", {"tf": 5, "n_bars": len(series_tf5)}

    sig = compute_tension_signature(series_tf5)
    score = _safe_float(getattr(sig, "score", 0.0)) or 0.0
    label = str(getattr(sig, "label", "UNKNOWN"))
    return round(score, 4), label, sig.to_dict() if hasattr(sig, "to_dict") else {"tf": 5}


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPOSANTE : HTF CONTEXT SCORE
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_htf_context_score(
    db_path: Path,
    symbol: str,
    currency: str,
    htf_tfs: Sequence[int],
    bars: int,
    available_cols: Dict[str, str],
    table: str,
) -> float:
    """
    Mesure la convergence de l'état Zone sur plusieurs TF pour une devise.

    Règle :
        NEUTRAL sur tous TF              → 0.0
        1 TF non-NEUTRAL                 → 0.3
        2 TF non-NEUTRAL cohérents dir.  → 0.6
        3+ TF cohérents même direction   → 1.0

    Retourne float [0.0, 1.0].
    """
    if not _HAS_ZONE or not _HAS_PERSONALITIES:
        return 0.0

    active_tfs: List[str] = []
    directions: List[str] = []

    for tf in htf_tfs:
        try:
            rows_raw = _load_force_rows(db_path, symbol, tf, bars, available_cols, table)
            if len(rows_raw) < 5:
                continue
            devise_cols = _build_devise_cols(available_cols)
            behavioral_rows = _build_rows_for_behavioral(rows_raw, available_cols)
            bar_idx = len(behavioral_rows) - 1

            z_series: List[Optional[float]] = []
            for i in range(len(behavioral_rows)):
                z = behavioral_index(currency, behavioral_rows, i, devise_cols, lookback=20)
                z_series.append(z)

            if not any(z is not None for z in z_series):
                continue

            diag: ZoneDiagnosis = analyze_zone_dynamics(
                z_series,
                timeframe=tf,
                currency=currency,
            )

            if diag.state not in ("NEUTRAL",):
                active_tfs.append(str(tf))
                directions.append(diag.z_extreme_dir)

        except Exception:
            continue

    n_active = len(active_tfs)
    if n_active == 0:
        return 0.0
    if n_active == 1:
        return 0.3

    # Cohérence directionnelle
    non_none_dirs = [d for d in directions if d and d != "NONE"]
    if non_none_dirs:
        dominant = max(set(non_none_dirs), key=non_none_dirs.count)
        coherent = sum(1 for d in non_none_dirs if d == dominant)
        if n_active >= 3 and coherent >= 3:
            return 1.0
        if coherent >= 2:
            return 0.6

    return 0.3


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPOSANTE : KINEMATICS (speed, angle, acceleration)
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_kinematics(
    db_path: Path,
    symbol: str,
    timeframe: int,
    start: str,
    end: str,
    currency: str,
    amplitude_norm: float,
) -> Dict[str, Optional[float]]:
    """
    Extrait speed_per_min, angle_deg, acceleration pour la devise donnée.
    Utilise pf_force_kinematics si disponible, sinon retourne des None.
    """
    result: Dict[str, Optional[float]] = {
        "speed_per_min": None,
        "angle_deg": None,
        "acceleration": None,
    }

    if not _HAS_KINEMATICS:
        return result

    try:
        rows = kin_load_rows(str(db_path), symbol, timeframe, start, end)
        if len(rows) < 2:
            return result

        segments = build_segments(rows)
        if not segments:
            return result

        # Dernière vélocité disponible pour la devise
        last_seg = segments[-1]
        v = last_seg.force_velocity_per_min.get(currency)
        a_deg = last_seg.force_angle_deg.get(currency)
        result["speed_per_min"] = v
        result["angle_deg"] = a_deg

        # Accélération : delta vitesse entre avant-dernier et dernier segment
        accs = acceleration_table(segments)
        if accs:
            last_acc = accs[-1]
            acc_val = last_acc["acceleration"].get(currency)
            result["acceleration"] = acc_val

    except Exception:
        pass

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  COMPOSANTE : CAPTURE QUALITY PENALTY
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_capture_penalty(db_path: Path, symbol: str) -> Tuple[float, str, Optional[float]]:
    """
    Retourne (penalty, status_label, data_age_minutes).
    penalty ∈ [0.0, PENALTY_MAX].
    """
    if not _HAS_FRESHNESS:
        return 0.0, "UNKNOWN", None

    try:
        state = build_db_freshness_state(str(db_path), symbol=symbol)
        verdict = state.get("verdict", {})
        status = verdict.get("status", "UNKNOWN")
        age = verdict.get("data_age_minutes")
        if age is None:
            return 0.0, status, None
        penalty = _clip(float(age) / PENALTY_STALE_MINUTES, 0.0, PENALTY_MAX)
        return round(penalty, 4), status, round(float(age), 1)
    except Exception:
        return 0.0, "ERROR", None


# ═══════════════════════════════════════════════════════════════════════════════
#  MOTEUR PRINCIPAL — CURRENCY ENERGY
# ═══════════════════════════════════════════════════════════════════════════════

def compute_currency_energy(
    db_path: Path,
    symbol: str,
    timeframe: int,
    bars: int,
    htf_tfs: Sequence[int],
    capture_penalty: float,
    available_cols: Dict[str, str],
    table: str,
) -> List[EnergyResult]:
    """
    Calcule l'énergie pour toutes les devises disponibles sur un TF.
    Retourne une liste de EnergyResult triée par energy_score décroissant.
    """
    force_rows = _load_force_rows(db_path, symbol, timeframe, bars, available_cols, table)
    if not force_rows:
        return []

    devise_cols = _build_devise_cols(available_cols)
    behavioral_rows = _build_rows_for_behavioral(force_rows, available_cols)
    bar_idx = len(behavioral_rows) - 1

    basket_devs = _compute_basket_deviation(force_rows, available_cols)

    # Timestamps pour kinematics
    ts_start = force_rows[0]["created_at"]
    ts_end   = force_rows[-1]["created_at"]

    results: List[EnergyResult] = []

    for currency in CURRENCIES:
        if currency not in available_cols:
            continue

        missing_modules: List[str] = []
        comp = EnergyComponents()
        raw_signed: Dict[str, Any] = {}
        absorption_escape = "NEUTRAL"
        ctx_tags: List[str] = []
        energy_context: List[str] = []
        elastic_tension_score = 0.0
        elastic_tension_label = "INACTIVE"
        notes_parts: List[str] = []

        # ── 1. behavioral_zscore ─────────────────────────────────────────────
        z_score: Optional[float] = None
        if _HAS_PERSONALITIES:
            z_score = behavioral_index(
                currency, behavioral_rows, bar_idx, devise_cols, lookback=min(20, max(5, bars // 2))
            )
        else:
            missing_modules.append("pf_personalities")

        if z_score is not None:
            comp.behavioral_zscore_norm = _norm(z_score, 3.0)
            raw_signed["behavioral_zscore"] = round(z_score, 4)
        else:
            raw_signed["behavioral_zscore"] = None
            if _HAS_PERSONALITIES:
                notes_parts.append("zscore_insufficient_data")

        # ── 2. Zone Dynamics (tension, persistence, absorption) ──────────────
        zone_diag: Optional[ZoneDiagnosis] = None
        if _HAS_ZONE and _HAS_PERSONALITIES:
            # Construire la z_series complète
            z_series: List[Optional[float]] = []
            for i in range(len(behavioral_rows)):
                z = behavioral_index(currency, behavioral_rows, i, devise_cols, lookback=20)
                z_series.append(z)

            try:
                zone_diag = analyze_zone_dynamics(
                    z_series,
                    timeframe=timeframe,
                    currency=currency,
                )
            except Exception as e:
                notes_parts.append(f"zone_error:{e}")
        else:
            if not _HAS_ZONE:
                missing_modules.append("pf_zone_dynamics")

        if zone_diag is not None:
            # zone_tension_norm
            comp.zone_tension_norm = _norm(zone_diag.tension_score, 2.0)
            # persistence_norm : bars_in_extreme normalisé / 20
            comp.persistence_norm = _norm(float(zone_diag.bars_in_extreme), 20.0)
            absorption_escape = zone_diag.state
            ctx_tags = list(zone_diag.contextual_tags)

            raw_signed["z_current"]        = zone_diag.z_current
            raw_signed["zone_state"]       = zone_diag.state
            raw_signed["zone_level"]       = zone_diag.zone_level
            raw_signed["z_extreme_dir"]    = zone_diag.z_extreme_dir
            raw_signed["bars_in_extreme"]  = zone_diag.bars_in_extreme
            raw_signed["absorption_factor"]= round(zone_diag.absorption_factor, 4)
            raw_signed["tension_score"]    = round(zone_diag.tension_score, 4)
            raw_signed["depth_slope"]      = round(zone_diag.depth_slope, 4)
            raw_signed["depth_acceleration"]= round(zone_diag.depth_acceleration, 4)
            raw_signed["context_score"]    = round(zone_diag.context_score, 4)
        else:
            raw_signed["z_current"]     = None
            raw_signed["zone_state"]    = "UNAVAILABLE"
            raw_signed["tension_score"] = None

        # ── 3. Kinematics (speed, angle, acceleration) ───────────────────────
        profile = DEVISE_PROFILES.get(currency) if _HAS_PERSONALITIES else None
        amplitude_norm = profile.amplitude_norm if profile else 5.0

        kin: Dict[str, Optional[float]] = {"speed_per_min": None, "angle_deg": None, "acceleration": None}
        if _HAS_KINEMATICS:
            kin = _compute_kinematics(db_path, symbol, timeframe, ts_start, ts_end, currency, amplitude_norm)
        else:
            missing_modules.append("pf_force_kinematics")

        if kin["speed_per_min"] is not None:
            comp.speed_norm = _norm(kin["speed_per_min"], amplitude_norm)
        if kin["angle_deg"] is not None:
            comp.angle_norm = _norm(kin["angle_deg"], 80.0)
        if kin["acceleration"] is not None:
            comp.acceleration_norm = _norm(kin["acceleration"], amplitude_norm)

        raw_signed["speed_per_min"]    = round(kin["speed_per_min"], 4) if kin["speed_per_min"] is not None else None
        raw_signed["angle_deg"]        = round(kin["angle_deg"], 2)     if kin["angle_deg"] is not None else None
        raw_signed["acceleration_raw"] = round(kin["acceleration"], 4)  if kin["acceleration"] is not None else None
        raw_signed["amplitude_norm_ref"] = amplitude_norm

        # ── 4. Basket deviation ──────────────────────────────────────────────
        basket_dev = basket_devs.get(currency)
        if basket_dev is not None:
            comp.basket_deviation_norm = _norm(basket_dev, 10.0)
        raw_signed["basket_deviation"] = basket_dev

        # ── 5. HTF context score ─────────────────────────────────────────────
        htf_score = _compute_htf_context_score(
            db_path, symbol, currency, htf_tfs, bars, available_cols, table
        )
        comp.htf_context_norm = htf_score
        raw_signed["htf_context_score"] = round(htf_score, 3)
        raw_signed["htf_tfs_scanned"]   = list(htf_tfs)

        # ── 6. Elastic tension signature — TF5 observationnel ────────────────
        elastic_tension_score, elastic_tension_label, elastic_debug = _compute_elastic_tension_component(
            db_path=db_path,
            symbol=symbol,
            currency=currency,
            available_cols=available_cols,
            table=table,
            bars=bars,
        )
        comp.elastic_tension_score = _clip(elastic_tension_score, 0.0, 1.0)
        raw_signed["elastic_tension_score"] = round(elastic_tension_score, 4)
        raw_signed["elastic_tension_label"] = elastic_tension_label
        raw_signed["elastic_tension_tf"] = 5
        raw_signed["elastic_tension_debug"] = elastic_debug

        if elastic_tension_label == "ELASTIC_LOADED":
            energy_context.append("ELASTIC_COMPONENT_ACTIVE")
        elif elastic_tension_score > 0.0:
            energy_context.append("ELASTIC_COMPONENT_PRESENT")

        # ── 7. Personality metadata ──────────────────────────────────────────
        if profile:
            raw_signed["role"]           = profile.role
            raw_signed["volatility_class"] = profile.volatility_class
            raw_signed["tempo_tf"]       = profile.tempo_tf
        else:
            raw_signed["role"]           = None
            raw_signed["volatility_class"] = None
            raw_signed["tempo_tf"]       = None

        if absorption_escape in ("ACCUMULATING", "EXTREME", "EARLY_EXTREME", "LEAKING", "RUPTURE"):
            energy_context.insert(0, "ZONE_ACTIVE")

        # ── 8. Formule energy_raw ────────────────────────────────────────────
        energy_raw = (
            WEIGHTS["zone_tension"]      * comp.zone_tension_norm
          + WEIGHTS["behavioral_zscore"] * comp.behavioral_zscore_norm
          + WEIGHTS["speed"]             * comp.speed_norm
          + WEIGHTS["angle"]             * comp.angle_norm
          + WEIGHTS["acceleration"]      * comp.acceleration_norm
          + WEIGHTS["persistence"]       * comp.persistence_norm
          + WEIGHTS["basket_deviation"]  * comp.basket_deviation_norm
          + WEIGHTS["htf_context"]       * comp.htf_context_norm
          + WEIGHTS["elastic_tension"]   * comp.elastic_tension_score
        )
        energy_raw = _clip(energy_raw, 0.0, 1.0)
        energy_raw = round(energy_raw, 4)

        # ── 9. Pénalité capture quality ───────────────────────────────────────
        energy_score = round(_clip(energy_raw * (1.0 - capture_penalty), 0.0, 1.0), 4)

        # ── 10. Label et confidence ──────────────────────────────────────────
        label = _energy_label(energy_score)
        confidence = _confidence(missing_modules)

        # ── 11. Notes contextuelles ──────────────────────────────────────────
        if absorption_escape == "ACCUMULATING":
            notes_parts.append("Champ chargé. Énergie potentielle. Surveiller LEAKING.")
        elif absorption_escape == "LEAKING":
            notes_parts.append("Zone en fuite. Énergie en transition.")
        elif absorption_escape == "RUPTURE":
            notes_parts.append("Rupture de zone. Énergie libérée.")
        elif absorption_escape in ("PRE_EXTREME", "EARLY_EXTREME"):
            notes_parts.append("Zone approche extrême. Tension naissante.")

        if profile and timeframe != profile.tempo_tf:
            notes_parts.append(
                f"TF={timeframe} hors tempo natif {profile.tempo_tf} pour {currency}."
            )
        if missing_modules:
            notes_parts.append(f"Modules manquants: {', '.join(missing_modules)}.")

        note_str = " ".join(notes_parts) if notes_parts else f"Lecture normale {currency} TF{timeframe}."

        results.append(EnergyResult(
            currency=currency,
            timeframe=timeframe,
            energy_raw_score=energy_raw,
            energy_score=energy_score,
            energy_label=label,
            energy_confidence=confidence,
            capture_quality_penalty=capture_penalty,
            components=comp,
            raw_signed=raw_signed,
            absorption_escape_state=absorption_escape,
            contextual_tags=ctx_tags,
            energy_context=energy_context,
            elastic_tension_score=elastic_tension_score,
            elastic_tension_label=elastic_tension_label,
            missing_modules=missing_modules,
            notes=note_str,
        ))

    results.sort(key=lambda r: r.energy_score, reverse=True)
    return results


# ═══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS SYNTHÈSE
# ═══════════════════════════════════════════════════════════════════════════════

def _build_ranking(results: List[EnergyResult]) -> List[Dict[str, Any]]:
    return [
        {
            "rank":         i + 1,
            "currency":     r.currency,
            "energy_score": round(r.energy_score, 4),
            "label":        r.energy_label,
            "absorption":   r.absorption_escape_state,
        }
        for i, r in enumerate(results)
    ]


def _build_top_energy(results: List[EnergyResult]) -> Dict[str, Any]:
    if not results:
        return {}
    in_transition = [r.currency for r in results if r.absorption_escape_state in ("LEAKING", "RUPTURE")]
    weak_field    = [r.currency for r in results if r.energy_label == "ENERGY_WEAK"]
    high_field    = [r.currency for r in results if r.energy_label == "ENERGY_HIGH"]

    top = results[0]
    return {
        "highest":        top.currency,
        "highest_score":  round(top.energy_score, 4),
        "high_field":     high_field,
        "in_transition":  in_transition,
        "weak_field":     weak_field,
    }


def _build_field_summary(results: List[EnergyResult]) -> str:
    if not results:
        return "Aucune donnée disponible."
    parts: List[str] = []
    top = results[0]
    parts.append(f"{top.currency} dominant ({top.energy_label}, {top.absorption_escape_state}).")
    transitioning = [r.currency for r in results if r.absorption_escape_state in ("LEAKING", "RUPTURE")]
    if transitioning:
        parts.append(f"En transition : {'+'.join(transitioning)}.")
    weak = [r.currency for r in results if r.energy_label == "ENERGY_WEAK"]
    if weak:
        parts.append(f"Faibles : {'+'.join(weak)}.")
    return " ".join(parts)


# ═══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PUBLIC
# ═══════════════════════════════════════════════════════════════════════════════

def build_currency_energy_state(
    db_path: str | Path = "powerflow.db",
    symbol: str = "GBPUSD",
    timeframe: int = 15,
    bars: int = 50,
    htf_tfs: Sequence[int] = DEFAULT_HTF_TFS,
) -> Dict[str, Any]:
    """
    Construit le dictionnaire complet currency_energy_state.

    Params :
        db_path   : Chemin vers powerflow.db (lecture seule).
        symbol    : Paire de trading (ex: "GBPUSD").
        timeframe : TF principal de lecture (minutes).
        bars      : Nombre de barres à charger.
        htf_tfs   : TF supérieurs pour htf_context_score.

    Returns :
        Dict JSON-serialisable.
    """
    db_path = Path(db_path)
    now_str = _now_iso()

    state: Dict[str, Any] = {
        "meta": {
            "generated_at":     now_str,
            "source":           MODULE_NAME,
            "version":          VERSION,
            "symbol":           symbol.upper(),
            "timeframe":        timeframe,
            "bars":             bars,
            "htf_tfs_scanned":  list(htf_tfs),
            "formula_version":  "V0.2_P_NEXT_1",
            "weights":          WEIGHTS,
            "modules_available": {
                "pf_personalities":    _HAS_PERSONALITIES,
                "pf_zone_dynamics":    _HAS_ZONE,
                "pf_force_kinematics": _HAS_KINEMATICS,
                "pf_db_freshness_probe": _HAS_FRESHNESS,
                "pf_tension_signature": _HAS_TENSION_SIGNATURE,
            },
        },
        "capture": {
            "data_age_minutes":      None,
            "capture_status":        "UNKNOWN",
            "capture_quality_penalty": 0.0,
        },
        "currencies": {},
        "ranking": [],
        "top_energy": {},
        "energy_field_summary": "",
    }

    # ── Vérification DB ───────────────────────────────────────────────────────
    if not db_path.exists():
        state["meta"]["error"] = f"DB non trouvée : {db_path}"
        state["energy_field_summary"] = "ERREUR : powerflow.db introuvable."
        return state

    # ── Capture quality penalty ───────────────────────────────────────────────
    penalty, cap_status, age = _compute_capture_penalty(db_path, symbol)
    state["capture"]["capture_quality_penalty"] = round(penalty, 4)
    state["capture"]["capture_status"]          = cap_status
    state["capture"]["data_age_minutes"]        = age

    # ── Détection table et colonnes disponibles ───────────────────────────────
    try:
        with _connect_ro(db_path) as conn:
            table = _pick_table(conn)
            available_cols = _available_force_cols(conn, table)
    except Exception as e:
        state["meta"]["error"] = f"Erreur DB : {e}"
        state["energy_field_summary"] = f"ERREUR lecture DB : {e}"
        return state

    state["meta"]["db_table"] = table
    state["meta"]["force_cols_found"] = list(available_cols.keys())

    if not available_cols:
        state["meta"]["error"] = "Aucune colonne force_* trouvée."
        state["energy_field_summary"] = "ERREUR : colonnes force absentes."
        return state

    # ── Calcul énergie par devise ─────────────────────────────────────────────
    results = compute_currency_energy(
        db_path=db_path,
        symbol=symbol,
        timeframe=timeframe,
        bars=bars,
        htf_tfs=htf_tfs,
        capture_penalty=penalty,
        available_cols=available_cols,
        table=table,
    )

    # ── Assemblage JSON ───────────────────────────────────────────────────────
    for r in results:
        state["currencies"][r.currency] = r.to_dict()

    state["ranking"]              = _build_ranking(results)
    state["top_energy"]           = _build_top_energy(results)
    state["energy_field_summary"] = _build_field_summary(results)

    return state


def write_currency_energy_state(
    state: Dict[str, Any],
    out_path: str | Path,
    pretty: bool = True,
) -> None:
    """Écrit le state JSON dans le fichier de sortie."""
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(state, ensure_ascii=False, indent=2 if pretty else None) + "\n",
        encoding="utf-8",
    )
