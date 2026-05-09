# -*- coding: utf-8 -*-
"""
PowerFlow V6 - Temporal Node State (read-only)

Mission:
    Produce output/temporal_node_state.json without touching capture_bridge.py
    and without writing to powerflow.db.

Doctrine V3:
    - Temporal Nodes are central.
    - Early alerts are qualified, not censored.
    - This module perceives and names; Telegram filters later.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# --- kinematics_state imports (V0.8-B) — defensive ---
try:
    from pf_force_kinematics import kinematics_summary as _kin_summary
    _KIN_AVAILABLE = True
except ImportError:
    _KIN_AVAILABLE = False

try:
    from pf_force_angle_speed_probe import build_state as _fas_build_state
    _FAS_AVAILABLE = True
except ImportError:
    _FAS_AVAILABLE = False
# --- end kinematics_state imports ---

CURRENCIES: Tuple[str, ...] = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD", "NZD")

FORCE_TABLE_CANDIDATES: Tuple[str, ...] = (
    "force_snapshots",
    "force_snapshots_v2",
)

TIME_COLUMN_CANDIDATES: Tuple[str, ...] = (
    "created_at",
    "timestamp",
    "time",
    "datetime",
    "ts",
)

SYMBOL_COLUMN_CANDIDATES: Tuple[str, ...] = (
    "symbol",
    "pair",
    "instrument",
)

TIMEFRAME_COLUMN_CANDIDATES: Tuple[str, ...] = (
    "timeframe",
    "tf",
    "period",
)

PRICE_COLUMN_CANDIDATES: Tuple[str, ...] = (
    "bid",
    "close_price",
    "close",
    "price",
    "last",
    "ask",
)

SPREAD_COLUMN_CANDIDATES: Tuple[str, ...] = (
    "spread",
    "spread_points",
    "spread_pips",
)

TELEGRAM_LEVELS_BY_MODE: Dict[str, set[str]] = {
    "OFF": set(),
    "WATCH": {"NODE_WATCH", "NODE_BIRTH", "FAST_NODE_BIRTH", "NODE_REPULSION_CANDIDATE"},
    "SCALPING": {
        "FAST_NODE_BIRTH",
        "NODE_BIRTH",
        "NODE_REPULSION_CANDIDATE",
        "NODE_REPULSION",
        "NODE_ABSORPTION",
        "SECOND_LEG_NODE",
        "NODE_CONFIRMED",
        "HOT_NODE",
    },
    "HOT_ONLY": {"HOT_NODE", "NODE_CONFIRMED"},
}

LEVEL_PRIORITY: Dict[str, int] = {
    "NONE": 0,
    "NODE_WATCH": 1,
    "FAST_NODE_BIRTH": 2,
    "NODE_BIRTH": 3,
    "NODE_REPULSION_CANDIDATE": 4,
    "NODE_REPULSION": 5,
    "NODE_ABSORPTION": 6,
    "SECOND_LEG_NODE": 7,
    "NODE_CONFIRMED": 8,
    "HOT_NODE": 9,
    "LATE_NODE": 10,
}


@dataclass
class TemporalNode:
    id: str
    timestamp: str
    symbol: str
    timeframe: str
    tf_minutes: Optional[int]
    type: str
    level: str
    family: str = "TEMPORAL_NODE"
    direction_bias: Optional[str] = None
    maturity: str = "BIRTH"
    confidence: str = "EARLY"
    score: float = 0.0
    window: Optional[str] = None
    reasons: List[str] = field(default_factory=list)
    risks_technical: List[str] = field(default_factory=list)
    telegram_allowed: bool = False
    telegram_level: str = "WATCH"
    has_convergence: bool = False
    has_repulsion: bool = False
    has_cross: bool = False
    has_kiss_reject: bool = False
    has_compression: bool = False
    has_break: bool = False
    action: str = "WATCH"
    severity: str = "watch"
    node_tags: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    description: str = ""



# ---------------------------------------------------------------------------
# V0.8-B — kinematics_state builder (corrected: no wall clock, no direction_windows TF key)
# ---------------------------------------------------------------------------

def _build_kinematics_state(
    db_path: str,
    symbol: str,
    recent_minutes: int,
    timeframes: list,
    db_vision: dict,
    capture_quality: dict,
) -> dict:
    """
    Produit state["kinematics_state"] — bloc non destructif.
    Fenêtre temporelle : capture_quality.live_reference_timestamp
                         -> fallback db_vision.latest_timestamp
                         -> jamais datetime.now() / wall clock.
    Release relay : capture_quality.relay_quality / relay_sample_state.
    Ne modifie jamais la DB. N'appelle jamais capture_bridge.
    """
    from datetime import datetime, timezone, timedelta
    from pathlib import Path as _Path

    def _unavailable(reason: str) -> dict:
        return {
            "status": "UNAVAILABLE",
            "reason": reason,
            "angle_state": None,
            "speed_state": None,
            "acceleration_state": None,
            "same_angle_cluster": {},
            "tight_gravity_cluster": {},
            "first_detachment": {},
            "force_hold_with_acceleration_fade": {},
            "release_candidate": {},
            "lab_signatures": [],
        }

    def _normalize_timeframes(value: Any) -> List[int]:
        if value is None:
            return [1, 5, 15]
        if isinstance(value, str):
            raw_items = [item.strip() for item in value.split(",") if item.strip()]
        else:
            raw_items = list(value)
        out: List[int] = []
        for item in raw_items:
            try:
                out.append(int(item))
            except (TypeError, ValueError):
                continue
        return out or [1, 5, 15]

    # -----------------------------------------------------------------------
    # garde-fous DB
    # -----------------------------------------------------------------------
    if db_vision.get("freshness_gate") == "BLOCKED":
        return _unavailable("db_freshness_gate_blocked")
    if db_vision.get("status") in ("DATA_BLIND", "NO_ROWS"):
        return _unavailable("db_blind_or_no_rows")

    if not (_KIN_AVAILABLE and _FAS_AVAILABLE):
        missing = []
        if not _KIN_AVAILABLE:
            missing.append("pf_force_kinematics")
        if not _FAS_AVAILABLE:
            missing.append("pf_force_angle_speed_probe")
        return _unavailable("module_not_found:" + ",".join(missing))

    # -----------------------------------------------------------------------
    # FENETRE TEMPORELLE — référence live DB, jamais wall clock
    # Priorité : capture_quality.live_reference_timestamp
    #            -> db_vision.latest_timestamp
    #            -> UNAVAILABLE
    # -----------------------------------------------------------------------
    def _parse_ts(raw) -> datetime | None:
        if not raw:
            return None
        s = str(raw).replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            return None

    live_ref_raw = (capture_quality or {}).get("live_reference_timestamp")
    live_ref = _parse_ts(live_ref_raw)

    if live_ref is None:
        live_ref = _parse_ts((db_vision or {}).get("latest_timestamp"))

    if live_ref is None:
        return _unavailable("no_live_reference_timestamp:capture_quality_and_db_vision_both_missing")

    end_dt = live_ref
    start_dt = end_dt - timedelta(minutes=int(recent_minutes))
    start_str = start_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_str = end_dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    normalized_timeframes = _normalize_timeframes(timeframes)

    # -----------------------------------------------------------------------
    # PROBES
    # -----------------------------------------------------------------------
    try:
        fas_tfs = [tf for tf in normalized_timeframes if tf in (1, 5, 15)] or [1, 5, 15]
        fas_state = _fas_build_state(
            db_path=_Path(db_path),
            symbol=symbol.upper(),
            timeframes=fas_tfs,
            bars=5,
        )
    except Exception as exc:
        return _unavailable(f"fas_probe_error:{type(exc).__name__}:{exc}")

    kin_tfs = [tf for tf in normalized_timeframes if tf in (1, 5, 15)] or [1, 5, 15]
    try:
        kin_data = _kin_summary(db_path, symbol.upper(), start_str, end_str, kin_tfs)
    except Exception as exc:
        return _unavailable(f"kin_summary_error:{type(exc).__name__}:{exc}")

    # -----------------------------------------------------------------------
    # HELPERS
    # -----------------------------------------------------------------------
    def _get_fas_tf(tf_min: int) -> dict:
        label = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1"}.get(tf_min, f"M{tf_min}")
        return fas_state.get("timeframes", {}).get(label, {})

    def _get_kin_tf(tf_min: int) -> dict:
        for t in kin_data.get("timeframes", []):
            if t.get("timeframe") == tf_min:
                return t
        return {}

    def _currency_map(fas_tf: dict) -> dict:
        out = {}
        for m in fas_tf.get("metrics", []):
            cur = m.get("currency", "")
            if cur:
                out[cur] = m
        return out

    def _angle(cur_map: dict, currency: str):
        return cur_map.get(currency, {}).get("angle_deg")

    # -----------------------------------------------------------------------
    # FAS DATA PAR TF
    # -----------------------------------------------------------------------
    m1_fas  = _get_fas_tf(1)
    m5_fas  = _get_fas_tf(5)
    m15_fas = _get_fas_tf(15)

    m1_cur  = _currency_map(m1_fas)
    m5_cur  = _currency_map(m5_fas)
    m15_cur = _currency_map(m15_fas)

    m1_pair      = m1_fas.get("pair", {})
    m1_gbp_angle = _angle(m1_cur, "GBP")
    m1_usd_angle = _angle(m1_cur, "USD")
    m1_pair_bias = m1_pair.get("pair_bias", "")

    # -----------------------------------------------------------------------
    # ANGLE STATE
    # -----------------------------------------------------------------------
    angle_tags = []
    for tf_label, cur_map in [("M1", m1_cur), ("M5", m5_cur), ("M15", m15_cur)]:
        gbp_a = _angle(cur_map, "GBP")
        usd_a = _angle(cur_map, "USD")
        if gbp_a is not None and usd_a is not None:
            if gbp_a < -45 and usd_a < -45:
                angle_tags.append(f"{tf_label}_DUAL_DOWN_STEEP")
            elif gbp_a > 45 and usd_a > 45:
                angle_tags.append(f"{tf_label}_DUAL_UP_STEEP")
            elif abs(gbp_a - usd_a) > 30:
                angle_tags.append(f"{tf_label}_GBP_USD_DIVERGING")

    angle_state = "|".join(angle_tags) if angle_tags else "NEUTRAL"

    # -----------------------------------------------------------------------
    # SPEED STATE
    # -----------------------------------------------------------------------
    speed_tags = []
    for tf_label, cur_map in [("M1", m1_cur), ("M5", m5_cur)]:
        for cur in ("GBP", "USD"):
            spd = cur_map.get(cur, {}).get("speed_per_min")
            if spd is not None:
                if spd > 1.5:
                    speed_tags.append(f"{tf_label}_{cur}_FAST_UP")
                elif spd < -1.5:
                    speed_tags.append(f"{tf_label}_{cur}_FAST_DOWN")

    speed_state = "|".join(speed_tags) if speed_tags else "MODERATE"

    # -----------------------------------------------------------------------
    # ACCELERATION STATE — depuis kinematics_summary segments
    # -----------------------------------------------------------------------
    accel_tags = []
    m1_kin = _get_kin_tf(1)
    m5_kin = _get_kin_tf(5)

    for tf_label, kin_tf in [("M1", m1_kin), ("M5", m5_kin)]:
        accels = kin_tf.get("accelerations", [])
        if accels:
            acc_map = accels[-1].get("acceleration", {})
            for cur in ("GBP", "USD"):
                a = acc_map.get(cur)
                if a is not None:
                    if a > 1.0:
                        accel_tags.append(f"{tf_label}_{cur}_ACCEL_UP")
                    elif a < -1.0:
                        accel_tags.append(f"{tf_label}_{cur}_ACCEL_DOWN")

    m1_segs = m1_kin.get("segments", [])
    if len(m1_segs) >= 3:
        energies = [s.get("energy", 0) for s in m1_segs[-3:]]
        if energies[0] > energies[1] > energies[2]:
            accel_tags.append("M1_ENERGY_FADE_LAST3")
        elif energies[0] < energies[1] < energies[2]:
            accel_tags.append("M1_ENERGY_BUILD_LAST3")

    acceleration_state = "|".join(accel_tags) if accel_tags else "STABLE"

    # -----------------------------------------------------------------------
    # SAME_ANGLE_CLUSTER — M5 : >= 3 devises UP ou DOWN proches (spread <= 20)
    # -----------------------------------------------------------------------
    m5_angles = {
        cur: data.get("angle_deg")
        for cur, data in m5_cur.items()
        if data.get("angle_deg") is not None
    }

    def _tight_cluster(items: list, max_spread: float = 20.0) -> list:
        if len(items) < 3:
            return []
        items_sorted = sorted(items, key=lambda x: x[1])
        for i in range(len(items_sorted) - 2):
            window = items_sorted[i:i+3]
            if window[-1][1] - window[0][1] <= max_spread:
                return window
        return []

    cluster_up   = _tight_cluster([(c, a) for c, a in m5_angles.items() if a > 5])
    cluster_down = _tight_cluster([(c, a) for c, a in m5_angles.items() if a < -5])

    if cluster_up:
        same_angle_cluster = {
            "label": "M5_POLARIZED_SAME_ANGLE_UP",
            "currencies": [c for c, _ in cluster_up],
            "angles": {c: round(a, 2) for c, a in cluster_up},
            "spread_deg": round(cluster_up[-1][1] - cluster_up[0][1], 2),
        }
    elif cluster_down:
        same_angle_cluster = {
            "label": "M5_POLARIZED_SAME_ANGLE_DOWN",
            "currencies": [c for c, _ in cluster_down],
            "angles": {c: round(a, 2) for c, a in cluster_down},
            "spread_deg": round(abs(cluster_down[0][1] - cluster_down[-1][1]), 2),
        }
    else:
        same_angle_cluster = {"label": "NO_CLUSTER", "currencies": []}

    # -----------------------------------------------------------------------
    # TIGHT_GRAVITY_CLUSTER — M15 : forces absolues serrées (spread <= 15)
    # -----------------------------------------------------------------------
    m15_forces = {
        cur: data.get("latest_force")
        for cur, data in m15_cur.items()
        if data.get("latest_force") is not None
    }

    tight_gravity_cluster = {"label": "INSUFFICIENT_DATA", "currencies": []}
    if len(m15_forces) >= 3:
        sorted_forces = sorted(m15_forces.items(), key=lambda x: x[1])
        for i in range(len(sorted_forces) - 2):
            window = sorted_forces[i:i+3]
            spread = window[-1][1] - window[0][1]
            if spread <= 15.0:
                tight_gravity_cluster = {
                    "label": "M15_TIGHT_GRAVITY_GROUP",
                    "currencies": [c for c, _ in window],
                    "forces": {c: round(f, 2) for c, f in window},
                    "force_spread": round(spread, 2),
                }
                break
        else:
            tight_gravity_cluster = {"label": "NO_TIGHT_GRAVITY", "currencies": []}

    # -----------------------------------------------------------------------
    # FIRST_DETACHMENT — M1 : abs(angle GBP ou USD) >= 60 + prix cohérent
    # -----------------------------------------------------------------------
    detachment_found     = False
    detachment_currency  = None
    detachment_direction = None
    price_coherent       = False

    if m1_gbp_angle is not None and abs(m1_gbp_angle) >= 60:
        detachment_found     = True
        detachment_currency  = "GBP"
        detachment_direction = "DOWN" if m1_gbp_angle < 0 else "UP"
    elif m1_usd_angle is not None and abs(m1_usd_angle) >= 60:
        detachment_found     = True
        detachment_currency  = "USD"
        detachment_direction = "DOWN" if m1_usd_angle < 0 else "UP"

    if detachment_found:
        gap_delta = m1_pair.get("gbp_usd_gap_delta")
        if gap_delta is not None:
            if detachment_currency == "GBP" and detachment_direction == "DOWN":
                price_coherent = gap_delta < 0 or "USD_PULLING" in m1_pair_bias
            elif detachment_currency == "GBP" and detachment_direction == "UP":
                price_coherent = gap_delta > 0 or "GBP_PULLING" in m1_pair_bias
            elif detachment_currency == "USD" and detachment_direction == "DOWN":
                price_coherent = gap_delta > 0 or "GBP_PULLING" in m1_pair_bias
            elif detachment_currency == "USD" and detachment_direction == "UP":
                price_coherent = gap_delta < 0 or "USD_PULLING" in m1_pair_bias

        det_angle_val = m1_gbp_angle if detachment_currency == "GBP" else m1_usd_angle
        first_detachment = {
            "detected": True,
            "label": f"M1_FIRST_DETACHMENT_{detachment_currency}_{detachment_direction}",
            "currency": detachment_currency,
            "direction": detachment_direction,
            "angle_deg": round(det_angle_val, 2),
            "price_coherent": price_coherent,
            "pair_bias": m1_pair_bias,
            "gbp_usd_gap_delta": m1_pair.get("gbp_usd_gap_delta"),
        }
    else:
        first_detachment = {
            "detected": False,
            "label": "NO_DETACHMENT",
            "note": "no currency angle >= 60 on M1",
        }

    # -----------------------------------------------------------------------
    # FORCE_HOLD_WITH_ACCELERATION_FADE — M5 kinematics segments
    # -----------------------------------------------------------------------
    m5_segs    = m5_kin.get("segments", [])
    fade_note  = []
    energy_fade      = False
    angle_flattening = False

    if len(m5_segs) >= 3:
        last3_e = [s.get("energy", 0) for s in m5_segs[-3:]]
        if last3_e[0] > last3_e[1] > last3_e[2]:
            energy_fade = True
        else:
            fade_note.append(f"energy_not_monotone:{[round(e, 2) for e in last3_e]}")
    else:
        fade_note.append(f"not_enough_m5_segments:{len(m5_segs)}")

    if len(m5_segs) >= 2:
        prev_seg = m5_segs[-2]
        last_seg = m5_segs[-1]
        for cur in ("GBP", "USD"):
            prev_a = prev_seg.get("force_angle_deg", {}).get(cur)
            last_a = last_seg.get("force_angle_deg", {}).get(cur)
            if prev_a is not None and last_a is not None:
                if abs(last_a) < abs(prev_a):
                    angle_flattening = True
                    fade_note.append(f"{cur}_flattening:{round(prev_a, 2)}->{round(last_a, 2)}")
                    break

    fade_detected = energy_fade and angle_flattening
    force_hold_with_acceleration_fade = {
        "detected": fade_detected,
        "label": "M5_FORCE_HOLD_WITH_ACCELERATION_FADE" if fade_detected else "NO_FADE",
        "energy_fade": energy_fade,
        "angle_flattening": angle_flattening,
        "notes": fade_note,
    }

    # -----------------------------------------------------------------------
    # RELEASE_CANDIDATE
    # relay qualifié via capture_quality.relay_quality / relay_sample_state
    # jamais via direction_windows["M5"].
    # -----------------------------------------------------------------------
    rc_ok  = []
    rc_nok = []

    if first_detachment.get("detected"):
        rc_ok.append("first_detachment_confirmed")
    else:
        rc_nok.append("no_first_detachment")

    if price_coherent:
        rc_ok.append("price_coherent")
    elif first_detachment.get("detected"):
        rc_nok.append("price_not_coherent")

    if "M1_ENERGY_FADE_LAST3" in accel_tags:
        rc_ok.append("m1_energy_fade_relay")
    elif any("M1_GBP_ACCEL" in t or "M1_USD_ACCEL" in t for t in accel_tags):
        rc_ok.append("m1_acceleration_present")
    else:
        rc_nok.append("no_m1_energy_signal")

    cq = capture_quality or {}
    relay_quality      = cq.get("relay_quality", "")
    relay_sample_state = cq.get("relay_sample_state", "")

    relay_label = relay_quality or relay_sample_state

    if relay_label in ("CLEAN", "THIN"):
        rc_ok.append(f"relay_{relay_label.lower()}")
    elif relay_label in ("MISSING", "BLOCKED", "STALE"):
        rc_nok.append(f"relay_{relay_label.lower()}_degraded")

    is_release = len(rc_ok) >= 2 and len(rc_nok) == 0

    if is_release:
        rc_dir   = detachment_direction if detachment_found else "UNKNOWN"
        rc_label = f"COUNTER_RELEASE_ATTEMPT_{rc_dir}"
    else:
        rc_label = "NO_RELEASE"

    release_candidate = {
        "release": is_release,
        "label": rc_label,
        "relay_quality_used": relay_label or "UNKNOWN",
        "reasons_ok": rc_ok,
        "reasons_nok": rc_nok,
    }

    # -----------------------------------------------------------------------
    # LAB SIGNATURES
    # -----------------------------------------------------------------------
    lab_signatures = []
    if first_detachment.get("detected"):
        lab_signatures.append(first_detachment["label"])
    if same_angle_cluster.get("label", "").startswith("M5_POLARIZED"):
        lab_signatures.append("M5_POLARIZED_RELAY_FIELD")
    if force_hold_with_acceleration_fade.get("detected"):
        lab_signatures.append("M5_FORCE_HOLD_WITH_ACCELERATION_FADE")
    if "M1_ENERGY_FADE_LAST3" in accel_tags:
        lab_signatures.append("GLOBAL_ENERGY_FADE_WITH_LOCAL_ACCELERATION")
    m15_gbp_a = _angle(m15_cur, "GBP")
    m15_usd_a = _angle(m15_cur, "USD")
    if m15_gbp_a is not None and m15_usd_a is not None:
        if -15 <= m15_gbp_a < 0 and 0 < m15_usd_a <= 15:
            lab_signatures.append("M15_SLOW_COUNTER_BREATH")
    if is_release:
        lab_signatures.append(rc_label)

    return {
        "status": "OK",
        "live_reference_used": end_str,
        "window": f"{start_str} -> {end_str}",
        "angle_state": angle_state,
        "speed_state": speed_state,
        "acceleration_state": acceleration_state,
        "same_angle_cluster": same_angle_cluster,
        "tight_gravity_cluster": tight_gravity_cluster,
        "first_detachment": first_detachment,
        "force_hold_with_acceleration_fade": force_hold_with_acceleration_fade,
        "release_candidate": release_candidate,
        "lab_signatures": lab_signatures,
        "_debug": {
            "m1_angle_gbp": m1_gbp_angle,
            "m1_angle_usd": m1_usd_angle,
            "m1_pair_bias": m1_pair_bias,
            "m5_cluster_label": same_angle_cluster.get("label"),
            "accel_tags": accel_tags,
            "live_ref_source": "capture_quality" if _parse_ts(live_ref_raw) else "db_vision",
        },
    }



def build_temporal_node_state(
    db_path: str | Path,
    symbol: str = "GBPUSD",
    recent_minutes: int = 180,
    timeframes: Sequence[int] = (1, 5, 15, 30, 60),
    telegram_mode: str = "SCALPING",
    max_rows: int = 5000,
    min_score: float = 3.0,
    visual_htf_story: str = "unknown",
    include_extended: bool = True,
) -> Dict[str, Any]:
    """
    Build a read-only temporal node state.

    The module intentionally does not import cockpit_* or telegram_*.
    It reads SQLite, computes a small temporal state, and returns JSON-ready data.
    """
    generated_at = _utc_now_iso()
    symbol = symbol.upper().strip()
    telegram_mode = _normalize_telegram_mode(telegram_mode)
    visual_htf_story = _normalize_visual_htf_story(visual_htf_story)

    state: Dict[str, Any] = {
        "meta": {
            "generated_at": generated_at,
            "symbol": symbol,
            "recent_minutes": int(recent_minutes),
            "source": "pf_temporal_node_state",
            "version": "0.6-node-context",
            "visual_htf_story": visual_htf_story,
        },
        "db_vision": {
            "status": "UNKNOWN",
            "table": None,
            "rows_loaded": 0,
            "latest_timestamp": None,
            "data_age_minutes": None,
            "freshness_gate": "UNKNOWN",
            "telegram_live_allowed": False,
            "notes": [],
        },
        "node_summary": {
            "active_count": 0,
            "highest_level": "NONE",
            "dominant_direction": None,
            "telegram_mode": telegram_mode,
            "best_score": 0.0,
            "has_convergence": False,
            "has_repulsion": False,
            "fractal_score": 0,
            "best_interest": "NONE",
        },
        "nodes": [],
        "node_context": {
            "structure_label": "NONE",
            "fractal_state": "NONE",
            "trigger_tf": None,
            "m1_role": "UNKNOWN",
            "m5_role": "UNKNOWN",
            "m15_role": "UNKNOWN",
            "htf_role": "UNKNOWN",
            "visual_htf_story": visual_htf_story,
        },
        "extended": {
            "schema_state": "NOT_LOADED",
            "flags": [],
            "micro_window_state": "UNKNOWN",
        },
        "telegram_candidates": [],
        "next_watch": [],
    }

    db_path = Path(db_path)
    if not db_path.exists():
        state["db_vision"]["status"] = "DATA_BLIND"
        state["db_vision"]["notes"].append(f"db_not_found:{db_path}")
        return state

    try:
        with _connect_readonly(db_path) as conn:
            conn.row_factory = sqlite3.Row
            table = _find_force_table(conn)
            if not table:
                state["db_vision"]["status"] = "DATA_BLIND"
                state["db_vision"]["notes"].append("no_force_snapshots_table_found")
                return state

            columns = _table_columns(conn, table)
            time_col = _pick_column(columns, TIME_COLUMN_CANDIDATES)
            symbol_col = _pick_column(columns, SYMBOL_COLUMN_CANDIDATES)
            tf_col = _pick_column(columns, TIMEFRAME_COLUMN_CANDIDATES)
            price_col = _pick_column(columns, PRICE_COLUMN_CANDIDATES)
            spread_col = _pick_column(columns, SPREAD_COLUMN_CANDIDATES)
            force_cols = _detect_force_columns(columns)

            state["db_vision"]["table"] = table

            if not force_cols:
                state["db_vision"]["status"] = "DATA_BLIND"
                state["db_vision"]["notes"].append("no_force_columns_found")
                return state

            base, quote = _split_symbol(symbol)
            if base not in force_cols or quote not in force_cols:
                state["db_vision"]["status"] = "TACTICAL_PARTIAL"
                state["db_vision"]["notes"].append(
                    f"missing_force_columns_for_symbol:{base}/{quote}"
                )
                return state

            rows = _load_force_rows(
                conn=conn,
                table=table,
                columns=columns,
                time_col=time_col,
                symbol_col=symbol_col,
                tf_col=tf_col,
                price_col=price_col,
                spread_col=spread_col,
                force_cols=force_cols,
                symbol=symbol,
                max_rows=max_rows,
            )
    except sqlite3.Error as exc:
        state["db_vision"]["status"] = "DATA_BLIND"
        state["db_vision"]["notes"].append(f"sqlite_error:{exc}")
        return state

    parsed_rows = [_normalize_row(r, symbol, time_col=True) for r in rows]
    parsed_rows = [r for r in parsed_rows if r is not None]

    if not parsed_rows:
        state["db_vision"]["status"] = "DATA_BLIND"
        state["db_vision"]["notes"].append("no_rows_loaded")
        return state

    generated_dt = datetime.now(timezone.utc)
    latest_ts = max(r["ts"] for r in parsed_rows if r.get("ts"))
    age_minutes = max(0.0, (generated_dt - latest_ts).total_seconds() / 60.0)

    current_min_ts = generated_dt - timedelta(minutes=recent_minutes)
    filtered = [r for r in parsed_rows if r.get("ts") and r["ts"] >= current_min_ts]
    used_stale_fallback = False

    # Fallback: keep the last historical window around latest_ts, not the whole DB slice.
    # This preserves perception without inflating windows such as M5 02:40->20:50.
    if not filtered:
        stale_min_ts = latest_ts - timedelta(minutes=recent_minutes)
        filtered = [r for r in parsed_rows if r.get("ts") and r["ts"] >= stale_min_ts]
        used_stale_fallback = True
        state["db_vision"]["notes"].append("no_rows_in_recent_window_using_latest_historical_window")

    allowed_tfs = set(int(x) for x in timeframes)
    grouped: Dict[int, List[Dict[str, Any]]] = {}
    for row in filtered:
        tf_minutes = row.get("tf_minutes")
        if tf_minutes is None:
            continue
        if allowed_tfs and tf_minutes not in allowed_tfs:
            continue
        grouped.setdefault(tf_minutes, []).append(row)

    state["db_vision"]["tf_coverage"] = {
        _tf_label(tf): len(tf_rows) for tf, tf_rows in sorted(grouped.items())
    }

    nodes: List[TemporalNode] = []
    node_id = 1
    for tf_minutes, tf_rows in sorted(grouped.items()):
        tf_rows = sorted(tf_rows, key=lambda r: r["ts"])
        node = _detect_node_for_timeframe(
            rows=tf_rows,
            symbol=symbol,
            tf_minutes=tf_minutes,
            telegram_mode=telegram_mode,
            node_id=node_id,
            min_score=min_score,
        )
        if node is not None:
            nodes.append(node)
            node_id += 1

    # Fractal boost: multiple timeframes active around the same direction.
    nodes = _apply_fractal_context(nodes, telegram_mode)

    if include_extended:
        state["extended"] = _build_extended_layer(
            db_path=db_path,
            symbol=symbol,
            recent_minutes=recent_minutes,
            timeframes=timeframes,
            nodes=nodes,
        )

    state["node_context"] = _build_node_context(
        nodes=nodes,
        grouped=grouped,
        visual_htf_story=visual_htf_story,
        extended=state.get("extended", {}),
    )
    _apply_node_context_to_nodes(nodes, state["node_context"], state.get("extended", {}))

    state["db_vision"]["rows_loaded"] = len(filtered)
    state["db_vision"]["latest_timestamp"] = _iso(latest_ts)
    state["db_vision"]["data_age_minutes"] = round(age_minutes, 1)

    data_is_stale = bool(used_stale_fallback or age_minutes > recent_minutes)
    if data_is_stale:
        state["db_vision"]["status"] = "DATA_STALE"
        state["db_vision"]["freshness_gate"] = "STALE_HISTORICAL_PERCEPTION_ONLY"
        state["db_vision"]["telegram_live_allowed"] = False
        _disable_live_telegram(nodes, "stale_data")
    else:
        state["db_vision"]["status"] = _db_status_from_rows(filtered, grouped)
        state["db_vision"]["freshness_gate"] = "LIVE_PERCEPTION_OK"
        state["db_vision"]["telegram_live_allowed"] = True

    # Serialize only after freshness gate has potentially disabled live Telegram.
    state["nodes"] = [asdict(n) for n in sorted(nodes, key=lambda n: n.score, reverse=True)]
    state["telegram_candidates"] = _build_telegram_candidates(state)

    _fill_summary_and_watch(state)

    # PATCH P0 — quatre clés additionnelles (non-destructif)
    _capture_quality = _build_capture_quality(grouped, generated_dt)
    state["capture_quality"] = _capture_quality
    state["scene_structure"] = _build_scene_structure(
        nodes=nodes,
        node_context=state.get("node_context", {}),
        grouped=grouped,
    )
    _session_transition = _detect_daily_open_transition(
        capture_quality=_capture_quality,
        scene_structure=state["scene_structure"],
    )
    state["scene_structure"]["session_transition"] = _session_transition
    state["scene_structure"]["session_transition_state"] = _session_transition.get("state")
    state["scene_structure"]["transition_flags"] = _session_transition.get("flags", [])
    state["direction_windows"] = _build_direction_windows(nodes=nodes, symbol=symbol)
    state["telegram_gating"] = _build_telegram_gating(
        nodes=nodes,
        capture_quality=_capture_quality,
        db_vision=state.get("db_vision", {}),
        telegram_mode=telegram_mode,
    )

    # PATCH V0.7.2.1 — aligner node_context.m5_role sur relay_sample_state.
    # MISSING -> M5_RELAY_MISSING_IN_DB
    # THIN    -> M5_RELAY_THIN_SAMPLE
    # CLEAN   -> M5_RELAY_CLEAN
    _relay_sample_state = _capture_quality.get("relay_sample_state")
    if _relay_sample_state in {
        "M5_RELAY_MISSING_IN_DB",
        "M5_RELAY_THIN_SAMPLE",
        "M5_RELAY_CLEAN",
    }:
        state["node_context"]["m5_role"] = _relay_sample_state
    elif not _capture_quality.get("relay_tf_available", True):
        state["node_context"]["m5_role"] = "M5_RELAY_MISSING_IN_DB"

    # --- V0.8-B kinematics_state (non destructif) ---
    try:
        state["kinematics_state"] = _build_kinematics_state(
            db_path=db_path,
            symbol=symbol,
            recent_minutes=recent_minutes,
            timeframes=timeframes,
            db_vision=state.get("db_vision", {}),
            capture_quality=state.get("capture_quality", {}),
        )
    except Exception as _kin_exc:
        state["kinematics_state"] = {
            "status": "UNAVAILABLE",
            "reason": f"outer_exception:{type(_kin_exc).__name__}:{_kin_exc}",
            "angle_state": None,
            "speed_state": None,
            "acceleration_state": None,
            "same_angle_cluster": {},
            "tight_gravity_cluster": {},
            "first_detachment": {},
            "force_hold_with_acceleration_fade": {},
            "release_candidate": {},
            "lab_signatures": [],
        }
    # --- end V0.8-B ---

    return state


def write_temporal_node_state(
    state: Dict[str, Any],
    out_path: str | Path,
    pretty: bool = False,
) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(
        state,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=False,
    )
    out.write_text(text + "\n", encoding="utf-8")


def _detect_node_for_timeframe(
    rows: List[Dict[str, Any]],
    symbol: str,
    tf_minutes: int,
    telegram_mode: str,
    node_id: int,
    min_score: float,
) -> Optional[TemporalNode]:
    if len(rows) < 4:
        return None

    base, quote = _split_symbol(symbol)
    base_key = f"force_{base.lower()}"
    quote_key = f"force_{quote.lower()}"

    work = rows[-min(50, len(rows)) :]
    base_values = [_to_float(r.get(base_key)) for r in work]
    quote_values = [_to_float(r.get(quote_key)) for r in work]

    valid = [(b, q, r) for b, q, r in zip(base_values, quote_values, work) if b is not None and q is not None]
    if len(valid) < 4:
        return None

    base_values = [x[0] for x in valid]
    quote_values = [x[1] for x in valid]
    work = [x[2] for x in valid]

    gap = [b - q for b, q in zip(base_values, quote_values)]
    abs_gap = [abs(x) for x in gap]
    current_gap = gap[-1]
    previous_gap = gap[-2] if len(gap) >= 2 else current_gap

    # Local windows.
    recent_gap = gap[-min(12, len(gap)) :]
    recent_abs = [abs(x) for x in recent_gap]
    recent_min_abs = min(recent_abs)
    recent_mean_abs = _safe_mean(recent_abs)
    full_mean_abs = _safe_mean(abs_gap)
    full_std_abs = _safe_std(abs_gap)

    # Core signatures.
    has_cross = _has_sign_change(recent_gap)
    has_convergence = recent_min_abs <= max(0.10, full_mean_abs * 0.38)
    has_compression = _is_compression(gap)
    has_kiss_reject = has_convergence and abs(current_gap) > max(recent_min_abs * 1.8, full_mean_abs * 0.75)
    has_break = abs(current_gap) > (full_mean_abs + max(full_std_abs, 0.10) * 0.75)
    has_repulsion = _is_repulsion(gap)

    force_shift = _has_force_shift(base_values, quote_values)
    price_lag = _has_price_lag_then_catchup(work, gap)

    reasons: List[str] = []
    score = 0.0

    if has_compression:
        score += 1.0
        reasons.append("compression")
    if has_cross:
        score += 2.0
        reasons.append("cross")
    if has_break:
        score += 2.0
        reasons.append("break")
    if has_kiss_reject:
        score += 3.0
        reasons.append("kiss_reject")
    if has_repulsion:
        score += 4.0
        reasons.append("repulsion")
    if has_convergence:
        score += 5.0
        reasons.append("convergence")
    if force_shift:
        score += 1.0
        reasons.append("force_shift")
    if price_lag:
        score += 1.0
        reasons.append("price_lag_then_catchup")

    if tf_minutes == 1 and force_shift and score >= 2.0:
        # V3 doctrine: M1 birth is qualified, not censored.
        score += 0.5
        reasons.append("m1_microfilm_birth")

    if score < min_score:
        return None

    node_type = _classify_node_type(
        has_convergence=has_convergence,
        has_kiss_reject=has_kiss_reject,
        has_repulsion=has_repulsion,
        has_cross=has_cross,
        has_break=has_break,
        score=score,
    )
    level = _classify_level(node_type, score, tf_minutes, force_shift, has_repulsion, has_break)
    maturity = _classify_maturity(score, has_break, has_repulsion)
    confidence = _classify_confidence(score, tf_minutes)
    direction_bias = _direction_bias(symbol, current_gap)

    risks = _technical_risks(
        tf_minutes=tf_minutes,
        sample_size=len(work),
        has_repulsion=has_repulsion,
        has_break=has_break,
        score=score,
    )

    timestamp = work[-1]["ts"]
    start_time = work[0]["ts"]
    end_time = work[-1]["ts"]
    window = f"{_hhmm(start_time)}->{_hhmm(end_time)}"
    telegram_allowed = _telegram_allowed(telegram_mode, level)

    return TemporalNode(
        id=f"NODE_{node_id:03d}",
        timestamp=_iso(timestamp),
        symbol=symbol,
        timeframe=_tf_label(tf_minutes),
        tf_minutes=tf_minutes,
        type=node_type,
        level=level,
        direction_bias=direction_bias,
        maturity=maturity,
        confidence=confidence,
        score=round(float(score), 2),
        window=window,
        reasons=reasons,
        risks_technical=risks,
        telegram_allowed=telegram_allowed,
        telegram_level=_telegram_level_from_level(level),
        has_convergence=has_convergence,
        has_repulsion=has_repulsion,
        has_cross=has_cross,
        has_kiss_reject=has_kiss_reject,
        has_compression=has_compression,
        has_break=has_break,
        action=_action_from_level(level),
        description=_describe_node(node_type, level, direction_bias, reasons),
    )


def _apply_fractal_context(nodes: List[TemporalNode], telegram_mode: str) -> List[TemporalNode]:
    if len(nodes) < 2:
        return nodes

    # Same direction on at least two TFs increases interest without changing raw detection.
    directions: Dict[str, int] = {}
    for n in nodes:
        if n.direction_bias:
            directions[n.direction_bias] = directions.get(n.direction_bias, 0) + 1

    dominant = max(directions.items(), key=lambda kv: kv[1])[0] if directions else None
    if not dominant:
        return nodes

    count = directions.get(dominant, 0)
    if count < 2:
        return nodes

    for n in nodes:
        if n.direction_bias == dominant:
            n.score = round(n.score + min(1.5, 0.5 * count), 2)
            if "fractal_context" not in n.reasons:
                n.reasons.append("fractal_context")
            if n.level == "NODE_WATCH" and n.score >= 4:
                n.level = "NODE_BIRTH"
            if n.level == "NODE_BIRTH" and n.score >= 8:
                n.level = "NODE_CONFIRMED"
            n.telegram_allowed = _telegram_allowed(telegram_mode, n.level)
            n.telegram_level = _telegram_level_from_level(n.level)
    return nodes




def _normalize_visual_htf_story(value: str) -> str:
    value = (value or "unknown").strip().lower()
    if value in {"confirmed", "visual_confirmed", "yes", "true", "1"}:
        return "confirmed"
    if value in {"rejected", "none", "false", "0"}:
        return "rejected"
    return "unknown"


def _build_extended_layer(
    db_path: Path,
    symbol: str,
    recent_minutes: int,
    timeframes: Sequence[int],
    nodes: Sequence[TemporalNode],
) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "schema_state": "EXTENDED_MISSING",
        "table": "force_snapshots_v2",
        "rows_loaded": 0,
        "latest_timestamp": None,
        "tf_coverage": {},
        "flags": [],
        "micro_window_state": "INACTIVE",
        "metrics": {},
    }

    try:
        with _connect_readonly(db_path) as conn:
            conn.row_factory = sqlite3.Row
            tables = {
                r[0]
                for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            if "force_snapshots_v2" not in tables:
                return out

            cols = _table_columns(conn, "force_snapshots_v2")
            required = {"tick_volume", "pip_range", "pip_body", "pip_change", "spread_pips", "force_nzd"}
            present = {c.lower() for c in cols}
            out["schema_state"] = "EXTENDED_SCHEMA_OK" if required.intersection(present) else "EXTENDED_SCHEMA_PARTIAL"

            allowed = set(int(x) for x in timeframes)
            placeholders = ",".join("?" for _ in allowed) if allowed else ""
            params: List[Any] = [symbol.upper()]
            sql = 'SELECT * FROM "force_snapshots_v2" WHERE UPPER("symbol") = ?'
            if allowed:
                sql += f' AND "timeframe" IN ({placeholders})'
                params.extend(sorted(allowed))
            sql += ' ORDER BY "created_at" DESC LIMIT 500'

            raw_rows = conn.execute(sql, params).fetchall()
            rows = list(reversed(raw_rows))
    except sqlite3.Error as exc:
        out["schema_state"] = "EXTENDED_READ_ERROR"
        out["flags"].append(f"EXTENDED_ERROR:{exc}")
        return out

    if not rows:
        return out

    latest_dt = None
    parsed_rows: List[Dict[str, Any]] = []
    for row in rows:
        d = {k: row[k] for k in row.keys()}
        ts = _parse_datetime(d.get("created_at"))
        if not ts:
            continue
        d["_ts"] = ts
        parsed_rows.append(d)
        if latest_dt is None or ts > latest_dt:
            latest_dt = ts

    if not parsed_rows or latest_dt is None:
        return out

    # Keep last historical window around latest timestamp. This is robust with broker/local timestamps.
    min_ts = latest_dt - timedelta(minutes=recent_minutes)
    recent = [r for r in parsed_rows if r["_ts"] >= min_ts]

    out["rows_loaded"] = len(recent)
    out["latest_timestamp"] = _iso(latest_dt)

    tf_cov: Dict[str, int] = {}
    for r in recent:
        tf = _tf_to_minutes(r.get("timeframe"))
        if tf is not None:
            tf_cov[_tf_label(tf)] = tf_cov.get(_tf_label(tf), 0) + 1
    out["tf_coverage"] = dict(sorted(tf_cov.items()))

    spreads = [_to_float(r.get("spread_pips")) for r in recent]
    spreads = [x for x in spreads if x is not None]
    pip_ranges = [_to_float(r.get("pip_range")) for r in recent]
    pip_ranges = [x for x in pip_ranges if x is not None]
    volumes = [_to_float(r.get("tick_volume")) for r in recent]
    volumes = [x for x in volumes if x is not None]
    pip_changes = [_to_float(r.get("pip_change")) for r in recent]
    pip_changes = [x for x in pip_changes if x is not None]

    flags: List[str] = []
    if any(r.get("force_nzd") is not None for r in recent):
        flags.append("NZD_AVAILABLE")

    if spreads:
        spread_avg = _safe_mean(spreads)
        out["metrics"]["spread_pips_avg"] = round(spread_avg, 3)
        if spread_avg <= 2.5:
            flags.append("SPREAD_CLEAN_FIELD")
        else:
            flags.append("SPREAD_FRICTION_FIELD")

    if pip_ranges:
        last_range = pip_ranges[-1]
        avg_range = _safe_mean(pip_ranges[:-1] or pip_ranges)
        ratio = last_range / avg_range if avg_range else 0.0
        out["metrics"]["last_pip_range"] = round(last_range, 3)
        out["metrics"]["pip_range_expansion_ratio"] = round(ratio, 3)
        if ratio >= 1.5 and last_range >= 2.0:
            flags.append("PIP_RANGE_EXPANSION")

    if volumes:
        last_vol = volumes[-1]
        avg_vol = _safe_mean(volumes[:-1] or volumes)
        ratio = last_vol / avg_vol if avg_vol else 0.0
        out["metrics"]["last_tick_volume"] = round(last_vol, 3)
        out["metrics"]["volume_expansion_ratio"] = round(ratio, 3)
        if ratio >= 1.5 and last_vol >= 2.0:
            flags.append("VOLUME_PRESSURE_SPIKE")

    node_is_micro = any(n.tf_minutes in {1, 5} and n.level in {"NODE_BIRTH", "NODE_CONFIRMED", "HOT_NODE"} for n in nodes)
    node_has_price_lag = any("price_lag_then_catchup" in n.reasons for n in nodes)
    node_hot = any(n.level == "HOT_NODE" for n in nodes)

    if node_is_micro:
        if node_has_price_lag:
            flags.append("PRICE_LAG_AT_NODE")
        pressure_strong = "VOLUME_PRESSURE_SPIKE" in flags or "PIP_RANGE_EXPANSION" in flags
        if node_hot and (node_has_price_lag or pressure_strong):
            flags.append("MICRO_WINDOW_ACTIVE_STRONG" if pressure_strong else "MICRO_WINDOW_ACTIVE_WEAK")
        elif node_hot or node_has_price_lag:
            flags.append("MICRO_WINDOW_ACTIVE_WEAK")

    # Deduplicate while preserving order.
    out["flags"] = list(dict.fromkeys(flags))
    if "MICRO_WINDOW_ACTIVE_STRONG" in out["flags"]:
        out["micro_window_state"] = "MICRO_WINDOW_ACTIVE_STRONG"
    elif "MICRO_WINDOW_ACTIVE_WEAK" in out["flags"]:
        out["micro_window_state"] = "MICRO_WINDOW_ACTIVE_WEAK"
    elif node_is_micro:
        out["micro_window_state"] = "MICRO_NODE_PRESENT"
    else:
        out["micro_window_state"] = "INACTIVE"

    return out


def _build_node_context(
    nodes: Sequence[TemporalNode],
    grouped: Dict[int, List[Dict[str, Any]]],
    visual_htf_story: str,
    extended: Dict[str, Any],
) -> Dict[str, Any]:
    tf_set = set(grouped)
    node_tfs = {n.tf_minutes for n in nodes}
    hot_tfs = {n.tf_minutes for n in nodes if n.level == "HOT_NODE"}
    trigger = _pick_trigger_tf(nodes)

    if 1 in node_tfs:
        m1_role = "M1_NODE_ACTIVE"
    elif 1 in tf_set:
        if len(grouped.get(1, [])) <= 2:
            m1_role = "M1_MICROFILM_REJOINING"
        else:
            m1_role = "M1_MICROFILM_ACTIVE"
    else:
        m1_role = "M1_STANDBY_OR_MISSING"

    if 5 in hot_tfs:
        m5_role = "M5_HOT_TACTICAL_TRIGGER"
    elif 5 in node_tfs:
        m5_role = "M5_TACTICAL_NODE_BIRTH"
    elif 5 in tf_set:
        m5_role = "M5_FEED_PRESENT"
    else:
        m5_role = "M5_MISSING"

    if 15 in node_tfs:
        m15_role = "M15_NODE_ACTIVE"
    elif 15 in tf_set:
        m15_role = "M15_ENERGY_RELAY_WITHOUT_REQUIRED_CROSS"
    else:
        m15_role = "M15_MISSING"

    htf_present = bool(tf_set.intersection({30, 60, 240, 1440}))
    if visual_htf_story == "confirmed":
        htf_role = "VISUAL_HTF_BATTLE_CONFIRMED"
    elif htf_present:
        htf_role = "HTF_BATTLE_CONTEXT_DB_PARTIAL"
    else:
        htf_role = "HTF_SILENT_OR_MISSING"

    if trigger == 5 and 5 in hot_tfs and ("BATTLE" in htf_role or "VISUAL_HTF" in htf_role):
        if m1_role in {"M1_MICROFILM_REJOINING", "M1_MICROFILM_ACTIVE", "M1_NODE_ACTIVE"}:
            structure = "M5_HOT_NODE_WITH_M1_RESPRING_INSIDE_HTF_BATTLE"
        else:
            structure = "HOT_M5_NODE_INSIDE_HTF_BATTLE"
    elif trigger == 5 and m15_role in {"M15_ENERGY_RELAY_WITHOUT_REQUIRED_CROSS", "M15_NODE_ACTIVE"}:
        structure = "HOT_M5_NODE_WITH_M15_ENERGY_RELAY" if 5 in hot_tfs else "M5_NODE_WITH_M15_ENERGY_RELAY"
    elif trigger == 5:
        structure = "M5_TACTICAL_NODE_BIRTH"
    elif trigger == 1:
        structure = "M1_MICRO_NODE_BIRTH"
    else:
        structure = "TEMPORAL_NODE_CONTEXT"

    if visual_htf_story == "confirmed" and trigger in {1, 5}:
        fractal_state = "LTF_BIRTH_INSIDE_VISUAL_HTF_STORY"
    elif trigger in {1, 5} and ("BATTLE" in htf_role):
        fractal_state = "LTF_NODE_INSIDE_HTF_BATTLE_FIELD"
    elif trigger == 5 and m15_role.startswith("M15"):
        fractal_state = "M5_TRIGGER_WITH_M15_ENERGY_RELAY"
    else:
        fractal_state = "NODE_CONTEXT_PARTIAL"

    return {
        "structure_label": structure,
        "fractal_state": fractal_state,
        "trigger_tf": _tf_label(trigger) if trigger else None,
        "m1_role": m1_role,
        "m5_role": m5_role,
        "m15_role": m15_role,
        "htf_role": htf_role,
        "visual_htf_story": visual_htf_story,
        "extended_micro_window": extended.get("micro_window_state"),
        "extended_flags": extended.get("flags", []),
    }


def _apply_node_context_to_nodes(
    nodes: Sequence[TemporalNode],
    context: Dict[str, Any],
    extended: Dict[str, Any],
) -> None:
    tags: List[str] = []
    reasons: List[str] = []

    if context.get("trigger_tf") == "M5":
        tags.append("m5_tactical_trigger")
    if context.get("m1_role") in {"M1_MICROFILM_REJOINING", "M1_MICROFILM_ACTIVE", "M1_NODE_ACTIVE"}:
        tags.append("m1_microfilm_present")
        reasons.append("m1_microfilm_context")
    if context.get("m15_role") == "M15_ENERGY_RELAY_WITHOUT_REQUIRED_CROSS":
        tags.append("m15_energy_relay")
        tags.append("energy_node_without_cross")
        reasons.append("m15_energy_relay")
    if "BATTLE" in str(context.get("htf_role", "")) or "VISUAL_HTF" in str(context.get("htf_role", "")):
        tags.append("htf_battle_context")
        reasons.append("htf_battle_context")

    micro_state = extended.get("micro_window_state")
    if micro_state in {"MICRO_WINDOW_ACTIVE_WEAK", "MICRO_WINDOW_ACTIVE_STRONG"}:
        tags.append(micro_state.lower())
        reasons.append(micro_state.lower())

    for node in nodes:
        for tag in tags:
            if tag not in node.node_tags:
                node.node_tags.append(tag)
        for reason in reasons:
            if reason not in node.reasons:
                node.reasons.append(reason)
        node.context = dict(context)
        node.severity = _severity_for_node(node, context, extended)
        node.description = _describe_node(node.type, node.level, node.direction_bias, node.reasons)


def _pick_trigger_tf(nodes: Sequence[TemporalNode]) -> Optional[int]:
    if not nodes:
        return None
    # Prefer active LTF trigger, then highest score.
    for tf in (1, 5, 15):
        candidates = [n for n in nodes if n.tf_minutes == tf]
        if candidates:
            return max(candidates, key=lambda n: n.score).tf_minutes
    return max(nodes, key=lambda n: n.score).tf_minutes


def _severity_for_node(node: TemporalNode, context: Dict[str, Any], extended: Dict[str, Any]) -> str:
    if node.level == "HOT_NODE":
        return "hot"
    if node.level == "NODE_CONFIRMED":
        return "important"
    if node.level in {"NODE_BIRTH", "FAST_NODE_BIRTH", "NODE_REPULSION", "NODE_REPULSION_CANDIDATE"}:
        if context.get("fractal_state") in {"LTF_BIRTH_INSIDE_VISUAL_HTF_STORY", "LTF_NODE_INSIDE_HTF_BATTLE_FIELD"}:
            return "important"
        return "watch"
    return "watch"


def _build_telegram_candidates(state: Dict[str, Any]) -> List[Dict[str, Any]]:
    live_allowed = bool(state.get("db_vision", {}).get("telegram_live_allowed"))
    out: List[Dict[str, Any]] = []
    for node in state.get("nodes", []):
        should_send = bool(live_allowed and node.get("telegram_allowed"))
        severity = node.get("severity") or ("hot" if node.get("level") == "HOT_NODE" else "watch")
        msg = (
            f"{_emoji_for_severity(severity)} POWERFLOW NODE {severity.upper()}\\n"
            f"{node.get('symbol')} | {node.get('type')} | {node.get('level')} | {node.get('timeframe')}\\n"
            f"Bias: {node.get('direction_bias')}\\n"
            f"Window: {node.get('window')} | Score: {node.get('score')}\\n"
            f"Context: {state.get('node_context', {}).get('structure_label')}\\n"
            f"Next: {', '.join(state.get('next_watch', [])[:3]) if state.get('next_watch') else 'WATCH'}"
        )
        out.append({
            "node_id": node.get("id"),
            "severity": severity,
            "should_send": should_send,
            "dry_run_only": True,
            "telegram_level": node.get("telegram_level"),
            "dedupe_key_hint": f"{node.get('symbol')}|{node.get('timeframe')}|{node.get('type')}|{node.get('window')}",
            "message": msg,
        })
    return out


def _emoji_for_severity(severity: str) -> str:
    return {"hot": "🔥", "important": "🟠", "watch": "🟡"}.get(severity, "🟡")


# --- PATCH P0 : capture_quality / scene_structure / direction_windows / telegram_gating ---

def _build_capture_quality(
    grouped: Dict[int, List[Dict[str, Any]]],
    generated_dt: datetime,
) -> Dict[str, Any]:
    """
    Évalue la fraîcheur de capture par TF.

    V0.7.1 — la fraîcheur est calculée en temps RELATIF
    par rapport au TF le plus récent dans grouped (live_reference_ts),
    et non par rapport à l'horloge système (generated_dt).

    V0.7.2 — ajoute relay_quality / relay_sample_state :
    - MISSING si M5 absent/stale
    - THIN si M5 LIVE mais rows < 3
    - CLEAN si M5 LIVE et rows >= 3

    Règle M5 stale : relative_age_minutes > 10.0
    (équivalent à plus de 2 bougies M5 de retard sur le TF de référence).

    wall_clock_age_minutes est conservé à titre informatif uniquement.
    """
    # ── 1. Trouver le timestamp de référence live (le plus récent tous TF confondus) ──
    live_reference_ts: Optional[datetime] = None
    live_reference_tf_minutes: Optional[int] = None

    # Garde-fous V0.7.2 : valeurs par défaut si M5 absent ou grouped vide.
    relay_quality = "MISSING"
    relay_sample_state = "M5_RELAY_MISSING_IN_DB"

    for tf_minutes, tf_rows in grouped.items():
        for r in tf_rows:
            ts = r.get("ts")
            if ts is None:
                continue
            if live_reference_ts is None or ts > live_reference_ts:
                live_reference_ts = ts
                live_reference_tf_minutes = tf_minutes

    # Si aucun timestamp exploitable, fallback horloge système
    if live_reference_ts is None:
        live_reference_ts = generated_dt
        live_reference_tf_minutes = None

    live_reference_tf_label = (
        _tf_label(live_reference_tf_minutes)
        if live_reference_tf_minutes is not None
        else "UNKNOWN"
    )

    # ── 2. Évaluer chaque TF par rapport à live_reference_ts ──
    tf_freshness: Dict[str, Any] = {}
    relay_tf_available = True  # M5 est le relay TF clé

    for tf_minutes, tf_rows in sorted(grouped.items()):
        label = _tf_label(tf_minutes)
        valid_ts = [r["ts"] for r in tf_rows if r.get("ts")]
        if not tf_rows or not valid_ts:
            tf_freshness[label] = {
                "status": "ABSENT",
                "rows": 0,
                "relative_age_minutes": None,
                "wall_clock_age_minutes": None,
            }
            if tf_minutes == 5:
                relay_tf_available = False
                relay_quality = "MISSING"
                relay_sample_state = "M5_RELAY_MISSING_IN_DB"
            continue

        latest_tf_ts = max(valid_ts)

        # Âge relatif = écart par rapport au TF de référence (le plus frais)
        relative_age_sec = max(0.0, (live_reference_ts - latest_tf_ts).total_seconds())
        relative_age_min = relative_age_sec / 60.0

        # Âge horloge = informatif seulement
        wall_clock_age_sec = max(0.0, (generated_dt - latest_tf_ts).total_seconds())
        wall_clock_age_min = wall_clock_age_sec / 60.0

        if tf_minutes == 5:
            # Règle canonique M5 : stale si retard > 10 min sur le TF de référence
            stale = relative_age_min > 10.0
            if stale:
                relay_tf_available = False
                status = "STALE_RELATIVE_TO_LIVE_REFERENCE"
            else:
                status = "LIVE"

            # V0.7.2 — nuance sample quality (évaluée même si stale, pour trace)
            m5_rows_count = len(tf_rows)
            if stale:
                relay_quality = "MISSING"
                relay_sample_state = "M5_RELAY_MISSING_IN_DB"
            elif m5_rows_count < 3:
                relay_quality = "THIN"
                relay_sample_state = "M5_RELAY_THIN_SAMPLE"
            else:
                relay_quality = "CLEAN"
                relay_sample_state = "M5_RELAY_CLEAN"
        else:
            # Autres TF : seuil = max(10 min, 3 × durée TF)
            threshold = max(10.0, tf_minutes * 3.0)
            status = (
                "STALE_RELATIVE_TO_LIVE_REFERENCE"
                if relative_age_min > threshold
                else "LIVE"
            )

        tf_freshness[label] = {
            "status": status,
            "rows": len(tf_rows),
            "relative_age_minutes": round(relative_age_min, 1),
            "wall_clock_age_minutes": round(wall_clock_age_min, 1),
        }

    # ── 3. Cas M5 totalement absent de grouped ──
    if 5 not in grouped:
        tf_freshness["M5"] = {
            "status": "ABSENT_FROM_DB",
            "rows": 0,
            "relative_age_minutes": None,
            "wall_clock_age_minutes": None,
        }
        relay_tf_available = False
        relay_quality = "MISSING"
        relay_sample_state = "M5_RELAY_MISSING_IN_DB"

    return {
        "live_reference_tf": live_reference_tf_label,
        "live_reference_timestamp": _iso(live_reference_ts) if live_reference_ts != generated_dt else None,
        "tf_freshness": tf_freshness,
        "relay_tf_available": relay_tf_available,
        "relay_quality": relay_quality,
        "relay_sample_state": relay_sample_state,
        "m5_role_capture": (
            "M5_RELAY_MISSING_IN_DB"
            if not relay_tf_available
            else relay_sample_state
        ),
    }

def _build_scene_structure(
    nodes: List[TemporalNode],
    node_context: Dict[str, Any],
    grouped: Dict[int, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """Vue synthétique non destructive de la scène courante."""
    tf_set = set(grouped.keys())
    node_tfs = [n.tf_minutes for n in nodes]
    hot_nodes = [n for n in nodes if n.level == "HOT_NODE"]
    birth_nodes = [n for n in nodes if n.level in {"NODE_BIRTH", "FAST_NODE_BIRTH"}]
    confirmed_nodes = [n for n in nodes if n.level == "NODE_CONFIRMED"]

    if hot_nodes:
        scene_type = "HOT_SCENE"
    elif confirmed_nodes:
        scene_type = "CONFIRMED_SCENE"
    elif birth_nodes:
        scene_type = "BIRTH_SCENE"
    elif nodes:
        scene_type = "WATCH_SCENE"
    else:
        scene_type = "EMPTY_SCENE"

    tf_depth = len({n.tf_minutes for n in nodes})

    return {
        "scene_type": scene_type,
        "active_node_count": len(nodes),
        "hot_node_count": len(hot_nodes),
        "fractal_depth": tf_depth,
        "is_fractal": tf_depth >= 2,
        "structure_label": node_context.get("structure_label", "NONE"),
        "fractal_state": node_context.get("fractal_state", "NONE"),
        "trigger_tf": node_context.get("trigger_tf"),
        "active_tf_list": sorted({_tf_label(tf) for tf in node_tfs if tf is not None}),
        "db_tf_list": sorted({_tf_label(tf) for tf in tf_set}),
    }


def _detect_daily_open_transition(
    capture_quality: Dict[str, Any],
    scene_structure: Dict[str, Any],
) -> Dict[str, Any]:
    """
    V0.7.3 — détecte une phase d'ouverture Daily.

    Règle :
    - live_reference_ts dans les 30 premières minutes UTC/broker
    - au moins 2 TF supérieurs stale relativement au TF vivant
    => DAILY_OPEN_TRANSITION

    Cette information qualifie la scène. Elle ne décide pas le node et ne touche
    pas directement Telegram.
    """
    transition_window_minutes = 30
    live_reference_text = capture_quality.get("live_reference_timestamp")
    live_reference_dt = _parse_datetime(live_reference_text)

    minutes_from_daily_open = None
    in_daily_open_window = False
    if live_reference_dt is not None:
        minutes_from_daily_open = round(
            live_reference_dt.hour * 60
            + live_reference_dt.minute
            + live_reference_dt.second / 60.0,
            2,
        )
        in_daily_open_window = 0.0 <= minutes_from_daily_open <= transition_window_minutes

    tf_freshness = capture_quality.get("tf_freshness", {}) or {}
    htf_labels = ("M15", "M30", "H1", "H4", "D1")
    stale_htf = []
    live_htf = []

    for label in htf_labels:
        info = tf_freshness.get(label)
        if not isinstance(info, dict):
            continue
        status = info.get("status")
        if status == "STALE_RELATIVE_TO_LIVE_REFERENCE":
            stale_htf.append(label)
        elif status == "LIVE":
            live_htf.append(label)

    active = bool(in_daily_open_window and len(stale_htf) >= 2)

    flags: List[str] = []
    if in_daily_open_window:
        flags.append("DAILY_OPEN_WINDOW")
    if active:
        flags.extend([
            "DAILY_OPEN_CAPTURE_DESYNC",
            "HTF_REBUILDING_AFTER_DAILY_OPEN",
        ])

    state = "DAILY_OPEN_TRANSITION" if active else (
        "DAILY_OPEN_WINDOW" if in_daily_open_window else "NONE"
    )

    return {
        "active": active,
        "state": state,
        "transition_window_minutes": transition_window_minutes,
        "minutes_from_daily_open": minutes_from_daily_open,
        "live_reference_tf": capture_quality.get("live_reference_tf"),
        "live_reference_timestamp": live_reference_text,
        "stale_htf_count": len(stale_htf),
        "stale_htf_list": stale_htf,
        "live_htf_list": live_htf,
        "flags": flags,
        "note": (
            "Daily open capture desync: HTF rebuilding while LTF is live"
            if active else None
        ),
    }


def _build_direction_windows(
    nodes: List[TemporalNode],
    symbol: str,
) -> Dict[str, Any]:
    """Résumé des fenêtres directionnelles actives par TF."""
    windows: List[Dict[str, Any]] = []
    direction_counts: Dict[str, int] = {}

    for n in nodes:
        direction = n.direction_bias or "UNKNOWN"
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
        windows.append({
            "tf": n.timeframe,
            "tf_minutes": n.tf_minutes,
            "direction_bias": direction,
            "level": n.level,
            "score": n.score,
            "window": n.window,
        })

    dominant = (
        max(direction_counts.items(), key=lambda item: item[1])[0]
        if direction_counts else None
    )
    consensus = len(direction_counts) == 1 and bool(direction_counts)

    return {
        "symbol": symbol,
        "windows": windows,
        "dominant_direction": dominant,
        "direction_consensus": consensus,
        "direction_count": len(direction_counts),
    }


def _build_telegram_gating(
    nodes: List[TemporalNode],
    capture_quality: Dict[str, Any],
    db_vision: Dict[str, Any],
    telegram_mode: str,
) -> Dict[str, Any]:
    """
    État de gating Telegram effectif, tenant compte de la qualité relay TF.

    V0.7.2 : distingue relay MISSING de relay THIN.
    - MISSING => DEGRADED_WATCH
    - THIN + HOT fractal => HOT_WITH_THIN_RELAY
    - THIN sans structure forte => WATCH_THIN_RELAY
    """
    relay_available = bool(capture_quality.get("relay_tf_available", True))
    live_allowed = bool(db_vision.get("telegram_live_allowed", False))
    hot_candidates = [n for n in nodes if n.level == "HOT_NODE"]
    has_hot = bool(hot_candidates)

    relay_quality = capture_quality.get("relay_quality", "MISSING")
    relay_sample_state = capture_quality.get("relay_sample_state", "M5_RELAY_MISSING_IN_DB")

    # Détecter scène fractale forte : approximation via nodes multi-TF.
    node_tfs = {n.tf_minutes for n in nodes if n.tf_minutes is not None}
    is_fractal_scene = len(node_tfs) >= 2

    if not live_allowed:
        effective_state = "BLOCKED_STALE_DATA"
    elif not relay_available:
        # relay MISSING → toujours DEGRADED, peu importe le HOT
        effective_state = "DEGRADED_WATCH"
    elif relay_quality == "THIN":
        # relay LIVE mais échantillon insuffisant
        if has_hot and is_fractal_scene:
            effective_state = "HOT_WITH_THIN_RELAY"
        else:
            effective_state = "WATCH_THIN_RELAY"
    elif telegram_mode == "OFF":
        effective_state = "OFF"
    elif has_hot:
        effective_state = "HOT_READY"
    elif nodes:
        effective_state = "WATCH_READY"
    else:
        effective_state = "IDLE"

    degraded_reason = None
    if effective_state in {"DEGRADED_WATCH", "HOT_WITH_THIN_RELAY", "WATCH_THIN_RELAY"}:
        degraded_reason = relay_sample_state

    note = None
    if effective_state == "DEGRADED_WATCH" and has_hot:
        note = "HOT candidate present but relay TF missing — monitor only, do not send live"
    elif effective_state == "HOT_WITH_THIN_RELAY":
        note = "HOT fractal scene but M5 sample thin — treat as qualified watch, not confirmed"
    elif effective_state == "WATCH_THIN_RELAY":
        note = "M5 relay live but thin sample — reduce confidence"

    return {
        "effective_state": effective_state,
        "relay_tf_available": relay_available,
        "relay_quality": relay_quality,
        "relay_sample_state": relay_sample_state,
        "m5_role": capture_quality.get("m5_role_capture", "UNKNOWN"),
        "live_allowed": live_allowed,
        "telegram_mode": telegram_mode,
        "hot_node_count": len(hot_candidates),
        "degraded_reason": degraded_reason,
        "note": note,
    }

# --- FIN PATCH P0 ---

def _disable_live_telegram(nodes: List[TemporalNode], reason: str) -> None:
    for node in nodes:
        node.telegram_allowed = False
        node.action = "HISTORICAL_WATCH"
        if reason not in node.risks_technical:
            node.risks_technical.append(reason)
        if "historical_perception_only" not in node.reasons:
            node.reasons.append("historical_perception_only")
        if "historical perception only" not in node.description.lower():
            node.description = node.description + " — historical perception only"

def _fill_summary_and_watch(state: Dict[str, Any]) -> None:
    nodes = state.get("nodes", [])
    summary = state["node_summary"]

    summary["active_count"] = len(nodes)
    if not nodes:
        summary["highest_level"] = "NONE"
        summary["best_interest"] = "NONE"
        state["next_watch"] = ["WATCH_NODE_BIRTH"]
        return

    best = max(nodes, key=lambda n: n.get("score", 0.0))
    highest = max(nodes, key=lambda n: LEVEL_PRIORITY.get(n.get("level", "NONE"), 0))

    summary["highest_level"] = highest.get("level", "NONE")
    summary["best_score"] = best.get("score", 0.0)
    summary["has_convergence"] = any(n.get("has_convergence") for n in nodes)
    summary["has_repulsion"] = any(n.get("has_repulsion") for n in nodes)
    summary["fractal_score"] = len({n.get("timeframe") for n in nodes if n.get("score", 0.0) >= 4})
    summary["best_interest"] = best.get("type", "NONE")
    summary["structure_label"] = state.get("node_context", {}).get("structure_label")
    summary["fractal_state"] = state.get("node_context", {}).get("fractal_state")
    summary["extended_micro_window"] = state.get("extended", {}).get("micro_window_state")

    direction_weights: Dict[str, float] = {}
    for node in nodes:
        direction = node.get("direction_bias")
        if not direction:
            continue
        direction_weights[direction] = direction_weights.get(direction, 0.0) + float(node.get("score", 0.0))

    if direction_weights:
        summary["dominant_direction"] = max(direction_weights.items(), key=lambda kv: kv[1])[0]

    watch: List[str] = []
    if any(n.get("level") in {"NODE_WATCH", "FAST_NODE_BIRTH", "NODE_BIRTH"} for n in nodes):
        watch.append("WATCH_ABSORPTION")
    if any(n.get("has_repulsion") for n in nodes):
        watch.append("WATCH_REPULSION_CONTINUATION")
    if any("price_lag_then_catchup" in n.get("reasons", []) for n in nodes):
        watch.append("WATCH_PRICE_CATCHUP")
    if summary["fractal_score"] >= 2:
        watch.append("WATCH_FRACTAL_CONFIRMATION")
    ctx = state.get("node_context", {})
    if ctx.get("m1_role") in {"M1_MICROFILM_REJOINING", "M1_MICRO_RESPRING", "M1_NODE_ACTIVE"}:
        watch.append("WATCH_M1_RESPRING")
    if ctx.get("m15_role") in {"M15_ENERGY_RELAY_WITHOUT_REQUIRED_CROSS", "M15_NODE_ACTIVE"}:
        watch.append("WATCH_M15_ENERGY_RELAY")
    if "HTF_BATTLE" in str(ctx.get("htf_role", "")) or "VISUAL_HTF" in str(ctx.get("htf_role", "")):
        watch.append("WATCH_HTF_BATTLE_RESOLUTION")
    if state.get("extended", {}).get("micro_window_state") in {"MICRO_WINDOW_ACTIVE_WEAK", "MICRO_WINDOW_ACTIVE_STRONG"}:
        watch.append("WATCH_EXTENDED_MICRO_WINDOW")
    if not watch:
        watch.append("WATCH_NEXT_NODE")
    state["next_watch"] = list(dict.fromkeys(watch))


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    # Relative URI is robust on Windows PowerShell when launched from Core.
    if db_path.is_absolute():
        uri = db_path.as_uri() + "?mode=ro"
    else:
        uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _find_force_table(conn: sqlite3.Connection) -> Optional[str]:
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    for candidate in FORCE_TABLE_CANDIDATES:
        if candidate in tables:
            return candidate
    for table in sorted(tables):
        low = table.lower()
        if "force" in low and "snapshot" in low:
            return table
    return None


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [row[1] for row in conn.execute(f"PRAGMA table_info({_q(table)})").fetchall()]


def _pick_column(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    lookup = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _detect_force_columns(columns: Sequence[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for col in columns:
        low = col.lower()
        for cur in CURRENCIES:
            c = cur.lower()
            if low in {f"force_{c}", f"{c}_force", c}:
                out[cur] = col
    return out


def _load_force_rows(
    conn: sqlite3.Connection,
    table: str,
    columns: Sequence[str],
    time_col: Optional[str],
    symbol_col: Optional[str],
    tf_col: Optional[str],
    price_col: Optional[str],
    spread_col: Optional[str],
    force_cols: Dict[str, str],
    symbol: str,
    max_rows: int,
) -> List[sqlite3.Row]:
    selected: List[str] = []
    for col in [time_col, symbol_col, tf_col, price_col, spread_col, *force_cols.values()]:
        if col and col not in selected:
            selected.append(col)

    if not selected:
        selected = list(columns)

    where: List[str] = []
    params: List[Any] = []
    if symbol_col:
        where.append(f"UPPER({_q(symbol_col)}) = ?")
        params.append(symbol)

    sql = f"SELECT {', '.join(_q(c) for c in selected)} FROM {_q(table)}"
    if where:
        sql += " WHERE " + " AND ".join(where)
    if time_col:
        sql += f" ORDER BY {_q(time_col)} DESC"
    sql += " LIMIT ?"
    params.append(int(max_rows))

    rows = conn.execute(sql, params).fetchall()
    return list(reversed(rows))


def _normalize_row(row: sqlite3.Row, symbol: str, time_col: bool = True) -> Optional[Dict[str, Any]]:
    data = {k: row[k] for k in row.keys()}
    ts = _find_and_parse_time(data)
    if not ts:
        return None

    tf_minutes = _find_tf_minutes(data)
    normalized: Dict[str, Any] = {
        "ts": ts,
        "tf_minutes": tf_minutes,
        "symbol": symbol,
    }

    for cur in CURRENCIES:
        value = _find_force_value(data, cur)
        normalized[f"force_{cur.lower()}"] = value

    price = _find_first_numeric(data, PRICE_COLUMN_CANDIDATES)
    spread = _find_first_numeric(data, SPREAD_COLUMN_CANDIDATES)
    normalized["price"] = price
    normalized["spread"] = spread
    return normalized


def _find_and_parse_time(data: Dict[str, Any]) -> Optional[datetime]:
    for key in TIME_COLUMN_CANDIDATES:
        for actual in data:
            if actual.lower() == key:
                parsed = _parse_datetime(data[actual])
                if parsed:
                    return parsed
    # Last chance: any column containing time/date.
    for actual, value in data.items():
        low = actual.lower()
        if "time" in low or "date" in low or low.endswith("_at"):
            parsed = _parse_datetime(value)
            if parsed:
                return parsed
    return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        # Accept seconds or milliseconds.
        v = float(value)
        if v > 10_000_000_000:
            v /= 1000.0
        try:
            dt = datetime.fromtimestamp(v, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    else:
        text = str(value).strip()
        if not text:
            return None
        text = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y.%m.%d %H:%M:%S",
                "%d/%m/%Y %H:%M:%S",
            ):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _find_tf_minutes(data: Dict[str, Any]) -> Optional[int]:
    for key in TIMEFRAME_COLUMN_CANDIDATES:
        for actual, value in data.items():
            if actual.lower() == key:
                return _tf_to_minutes(value)
    return None


def _tf_to_minutes(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    text = str(value).strip().upper()
    if not text:
        return None
    if text.isdigit():
        return int(text)
    if text.startswith("M") and text[1:].isdigit():
        return int(text[1:])
    if text.startswith("H") and text[1:].isdigit():
        return int(text[1:]) * 60
    if text.startswith("D") and text[1:].isdigit():
        return int(text[1:]) * 1440
    return None


def _find_force_value(data: Dict[str, Any], cur: str) -> Optional[float]:
    cur_low = cur.lower()
    keys = {f"force_{cur_low}", f"{cur_low}_force", cur_low}
    for actual, value in data.items():
        if actual.lower() in keys:
            return _to_float(value)
    return None


def _find_first_numeric(data: Dict[str, Any], candidates: Sequence[str]) -> Optional[float]:
    for key in candidates:
        for actual, value in data.items():
            if actual.lower() == key:
                return _to_float(value)
    return None


def _split_symbol(symbol: str) -> Tuple[str, str]:
    symbol = symbol.upper().replace("/", "").replace("-", "").strip()
    if len(symbol) >= 6:
        return symbol[:3], symbol[3:6]
    return "GBP", "USD"


def _has_sign_change(values: Sequence[float]) -> bool:
    signs = [1 if v > 0 else -1 if v < 0 else 0 for v in values]
    signs = [s for s in signs if s != 0]
    if len(signs) < 2:
        return False
    return any(a != b for a, b in zip(signs, signs[1:]))


def _is_compression(gap: Sequence[float]) -> bool:
    if len(gap) < 8:
        return False
    recent = gap[-min(10, len(gap)) :]
    full_std = _safe_std(gap)
    recent_std = _safe_std(recent)
    return recent_std <= max(0.10, full_std * 0.55)


def _is_repulsion(gap: Sequence[float]) -> bool:
    if len(gap) < 6:
        return False
    recent = list(gap[-min(10, len(gap)) :])
    abs_recent = [abs(x) for x in recent]
    idx_min = abs_recent.index(min(abs_recent))
    # Contact or near-contact happened before current expansion.
    if idx_min >= len(recent) - 2:
        return False
    min_abs = abs_recent[idx_min]
    current_abs = abs_recent[-1]
    previous_abs = abs_recent[-2]
    return current_abs > max(min_abs * 2.2, _safe_mean(abs_recent) * 1.15) and current_abs > previous_abs


def _has_force_shift(base_values: Sequence[float], quote_values: Sequence[float]) -> bool:
    if len(base_values) < 4 or len(quote_values) < 4:
        return False
    base_slope_now = base_values[-1] - base_values[-3]
    quote_slope_now = quote_values[-1] - quote_values[-3]
    base_slope_prev = base_values[-3] - base_values[-5] if len(base_values) >= 5 else 0.0
    quote_slope_prev = quote_values[-3] - quote_values[-5] if len(quote_values) >= 5 else 0.0

    angle_change = abs(base_slope_now - base_slope_prev) + abs(quote_slope_now - quote_slope_prev)
    opposition = base_slope_now * quote_slope_now < 0
    return opposition or angle_change >= 0.6


def _has_price_lag_then_catchup(rows: Sequence[Dict[str, Any]], gap: Sequence[float]) -> bool:
    prices = [_to_float(r.get("price")) for r in rows]
    valid = [(p, g) for p, g in zip(prices, gap) if p is not None]
    if len(valid) < 6:
        return False
    p = [x[0] for x in valid]
    g = [x[1] for x in valid]
    force_move = abs(g[-3] - g[-6])
    price_move_early = abs(p[-3] - p[-6])
    price_move_late = abs(p[-1] - p[-3])
    if force_move <= 0:
        return False
    return price_move_early < price_move_late and abs(g[-1] - g[-3]) < max(force_move, 0.1)


def _classify_node_type(
    has_convergence: bool,
    has_kiss_reject: bool,
    has_repulsion: bool,
    has_cross: bool,
    has_break: bool,
    score: float,
) -> str:
    if has_convergence and has_kiss_reject and score >= 8:
        return "NODE_COMPLET_FULL"
    if has_convergence and score >= 6:
        return "NODE_COMPLET"
    if has_repulsion and has_break:
        return "NODE_REPULSION"
    if has_cross and has_break:
        return "NODE_CROSS"
    if score >= 4:
        return "NODE_WATCH"
    return "NODE_SIMPLE"


def _classify_level(
    node_type: str,
    score: float,
    tf_minutes: int,
    force_shift: bool,
    has_repulsion: bool,
    has_break: bool,
) -> str:
    if node_type == "NODE_COMPLET_FULL" or score >= 9:
        return "HOT_NODE"
    if node_type == "NODE_COMPLET" or score >= 8:
        return "NODE_CONFIRMED"
    if node_type == "NODE_REPULSION":
        return "NODE_REPULSION"
    if has_repulsion and not has_break:
        return "NODE_REPULSION_CANDIDATE"
    if tf_minutes == 1 and force_shift:
        return "FAST_NODE_BIRTH"
    if score >= 4:
        return "NODE_BIRTH"
    return "NODE_WATCH"


def _classify_maturity(score: float, has_break: bool, has_repulsion: bool) -> str:
    if score >= 8 or (has_break and has_repulsion):
        return "CONFIRMING"
    if score >= 5:
        return "FORMING"
    return "BIRTH"


def _classify_confidence(score: float, tf_minutes: int) -> str:
    if score >= 8:
        return "STRONG"
    if score >= 5:
        return "MEDIUM"
    if tf_minutes == 1:
        return "EARLY_M1"
    return "EARLY"


def _direction_bias(symbol: str, current_gap: float) -> str:
    base, quote = _split_symbol(symbol)
    if current_gap > 0:
        return f"{base} pressure up / {quote} pressure down"
    if current_gap < 0:
        return f"{base} pressure down / {quote} pressure up"
    return f"{base}/{quote} balanced"


def _technical_risks(
    tf_minutes: int,
    sample_size: int,
    has_repulsion: bool,
    has_break: bool,
    score: float,
) -> List[str]:
    risks: List[str] = []
    if tf_minutes == 1:
        risks.append("m1_noise")
    if sample_size < 12:
        risks.append("small_sample")
    if score < 5:
        risks.append("early_maturity")
    if has_repulsion and not has_break:
        risks.append("repulsion_without_break")
    return risks


def _telegram_allowed(mode: str, level: str) -> bool:
    return level in TELEGRAM_LEVELS_BY_MODE.get(mode, set())


def _telegram_level_from_level(level: str) -> str:
    if level in {"HOT_NODE", "NODE_CONFIRMED"}:
        return "HOT"
    if level in {"NODE_REPULSION", "NODE_ABSORPTION"}:
        return "ABSORBING"
    if level in {"FAST_NODE_BIRTH", "NODE_BIRTH"}:
        return "BIRTH"
    return "WATCH"


def _action_from_level(level: str) -> str:
    if level in {"HOT_NODE", "NODE_CONFIRMED"}:
        return "HOT"
    if level in {"NODE_REPULSION", "NODE_REPULSION_CANDIDATE"}:
        return "WATCH_REPULSION"
    if level in {"FAST_NODE_BIRTH", "NODE_BIRTH"}:
        return "WATCH_BIRTH"
    return "WATCH"


def _describe_node(node_type: str, level: str, direction: Optional[str], reasons: List[str]) -> str:
    direction_text = direction or "direction unclear"
    reasons_text = ", ".join(reasons) if reasons else "no reason"
    return f"{node_type} / {level} — {direction_text} — {reasons_text}"


def _db_status_from_rows(rows: List[Dict[str, Any]], grouped: Dict[int, List[Dict[str, Any]]]) -> str:
    if not rows:
        return "DATA_BLIND"

    tf_set = set(grouped)

    # Full scalping stack: M1 birth + M5/M15 tactical confirmation.
    if {1, 5, 15}.issubset(tf_set):
        return "TACTICAL_OK"

    # M1 + M5 only: still useful for very short tactical perception.
    if {1, 5}.issubset(tf_set):
        return "TACTICAL_PARTIAL"

    # M1 intentionally absent, but M5/M15/HTF are feeding.
    # This is the current test mode while EA M1 is in stand-by.
    if {5, 15}.issubset(tf_set):
        return "TACTICAL_PARTIAL_NO_M1"

    # Only higher structure, no tactical lower layer.
    if tf_set.intersection({30, 60, 240, 1440}) and not tf_set.intersection({1, 5, 15}):
        return "STRUCTURE_ONLY"

    if grouped:
        return "PARTIAL_FEED"

    return "DATA_STALE"


def _normalize_telegram_mode(mode: str) -> str:
    mode = (mode or "SCALPING").upper().strip()
    return mode if mode in TELEGRAM_LEVELS_BY_MODE else "SCALPING"


def _tf_label(minutes: Optional[int]) -> str:
    if minutes is None:
        return "M?"
    if minutes < 60:
        return f"M{minutes}"
    if minutes % 1440 == 0:
        return f"D{minutes // 1440}"
    if minutes % 60 == 0:
        return f"H{minutes // 60}"
    return f"M{minutes}"


def _safe_mean(values: Sequence[float]) -> float:
    clean = [float(v) for v in values if _is_finite(v)]
    return mean(clean) if clean else 0.0


def _safe_std(values: Sequence[float]) -> float:
    clean = [float(v) for v in values if _is_finite(v)]
    if len(clean) < 2:
        return 0.0
    return pstdev(clean)


def _is_finite(value: Any) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _utc_now_iso() -> str:
    return _iso(datetime.now(timezone.utc))


def _hhmm(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%H:%M")


def _q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
