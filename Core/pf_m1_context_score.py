#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — M1_CONTEXT_SCORE

Final schema-flex version.

Mission:
- Qualify M1 contextual exploitability.
- M1 is never censored.
- Score is not financial risk.
- DB is read-only.
- No BUY/SELL.
- No cockpit/dashboard dependency from pf_*.

Inputs:
- powerflow.db / force_snapshots TF1
- output/force_kinematics_state.json
- output/dashboard_surface/{symbol}/node.json
- output/session_overlay.json
- output/dashboard_surface/{symbol}/regime_hmm.json or regime_legacy.json
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


CURRENCIES = ("GBP", "EUR", "USD", "JPY", "CAD", "CHF", "AUD", "NZD", "XAU")

CAPTURE_QUALITY_SCORE = {
    "FULL_STACK_VISIBLE": 1.0,
    "TACTICAL_OK": 0.8,
    "DEGRADED": 0.5,
    "MINIMAL": 0.3,
    "BLIND": 0.0,
}

RELAY_QUALITY_SCORE = {
    "M5_RELAY_CLEAN": 1.0,
    "CLEAN": 1.0,
    "M5_THIN": 0.6,
    "THIN": 0.6,
    "M5_MISSING": 0.3,
    "MISSING": 0.3,
}

SESSION_PHASE_SCORE = {
    "IGNITION": 1.0,
    "MID_SESSION": 0.7,
    "CLOSING": 0.5,
    "DEAD_ZONE": 0.3,
}

REGIME_SCORE = {
    "COMPRESSION": 1.0,
    "REGIME_COMPRESSION": 1.0,
    "TRANSITION": 0.7,
    "REGIME_TRANSITION": 0.7,
    "TENDANCE": 0.5,
    "REGIME_TENDANCE": 0.5,
    "TREND": 0.5,
    "RANGE": 0.4,
    "REGIME_RANGE": 0.4,
    "UNKNOWN": 0.4,
}

WEIGHTS = {
    "capture_quality": 0.30,
    "noise_ratio_score": 0.20,
    "relay_quality": 0.20,
    "session_phase_score": 0.15,
    "regime_score": 0.15,
}


@dataclass
class M1ContextInputs:
    db_path: str = "powerflow.db"
    symbol: str = "GBPUSD"
    kinematics_path: Optional[str] = None
    temporal_node_path: Optional[str] = None
    session_overlay_path: Optional[str] = None
    regime_hmm_path: Optional[str] = None
    regime_legacy_path: Optional[str] = None
    bars: int = 120


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def connect_readonly(db_path: str) -> sqlite3.Connection:
    uri = f"file:{Path(db_path).as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def read_json(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def default_paths(symbol: str) -> Dict[str, str]:
    surface = Path("output") / "dashboard_surface" / symbol.upper()
    return {
        "kinematics": str(Path("output") / "force_kinematics_state.json"),
        "temporal_node": str(surface / "node.json"),
        "session_overlay": str(Path("output") / "session_overlay.json"),
        "regime_hmm": str(surface / "regime_hmm.json"),
        "regime_legacy": str(surface / "regime_legacy.json"),
    }


def u(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text.upper() if text else None


def ci_get(mapping: Any, key: str, default: Any = None) -> Any:
    """Case-insensitive dict get."""
    if not isinstance(mapping, Mapping):
        return default
    if key in mapping:
        return mapping[key]
    lk = key.lower()
    for k, v in mapping.items():
        if str(k).lower() == lk:
            return v
    return default


def find_first_key(obj: Any, key_names: Iterable[str]) -> Any:
    targets = {k.lower() for k in key_names}
    if isinstance(obj, Mapping):
        for k, v in obj.items():
            if str(k).lower() in targets:
                return v
        for v in obj.values():
            found = find_first_key(v, key_names)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first_key(item, key_names)
            if found is not None:
                return found
    return None


def find_currency_section(obj: Any, currency: str) -> Optional[Mapping[str, Any]]:
    cur = currency.upper()
    keys = {
        cur,
        cur.lower(),
        f"force_{cur.lower()}",
        f"{cur.lower()}_force",
        f"{cur.lower()}_state",
    }

    if isinstance(obj, Mapping):
        for k in keys:
            v = obj.get(k)
            if isinstance(v, Mapping):
                return v

        for coll in ("currencies", "currency_states", "states", "nodes", "kinematics", "per_currency"):
            v = obj.get(coll)
            if isinstance(v, Mapping):
                for k in keys:
                    sec = v.get(k)
                    if isinstance(sec, Mapping):
                        return sec
            elif isinstance(v, list):
                for item in v:
                    if isinstance(item, Mapping) and u(item.get("currency")) == cur:
                        return item

        if u(obj.get("currency")) == cur:
            return obj

        for v in obj.values():
            sec = find_currency_section(v, cur)
            if sec:
                return sec

    elif isinstance(obj, list):
        for item in obj:
            sec = find_currency_section(item, cur)
            if sec:
                return sec

    return None


def scalar_for_currency(obj: Mapping[str, Any], currency: str, keys: Iterable[str]) -> Any:
    sec = find_currency_section(obj, currency)
    if isinstance(sec, Mapping):
        for k in keys:
            value = ci_get(sec, k)
            if value is not None:
                return value
        found = find_first_key(sec, keys)
        if found is not None:
            return found

    for k in keys:
        value = ci_get(obj, k)
        if value is not None:
            return value
    return find_first_key(obj, keys)


def detect_db_columns(cols: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, str]]:
    lower = {c.lower(): c for c in cols}

    symbol_col = lower.get("symbol")
    tf_col = lower.get("timeframe") or lower.get("tf")
    ts_col = (
        lower.get("timestamp")
        or lower.get("timestamp_utc")
        or lower.get("time")
        or lower.get("datetime")
        or lower.get("created_at")
        or lower.get("ts")
    )

    currency_cols: Dict[str, str] = {}
    for cur in CURRENCIES:
        candidates = [
            cur.lower(),
            cur.upper(),
            f"force_{cur.lower()}",
            f"{cur.lower()}_force",
            f"{cur.lower()}_zscore",
            f"z_{cur.lower()}",
        ]
        for cand in candidates:
            real = lower.get(cand.lower())
            if real:
                currency_cols[cur] = real
                break

    return symbol_col, tf_col, ts_col, currency_cols


def infer_currencies_from_db(db_path: str, symbol: str, bars: int = 120) -> Tuple[List[str], Dict[str, Any], List[str]]:
    risks: List[str] = []
    try:
        conn = connect_readonly(db_path)
    except Exception as exc:
        return [], {}, [f"DB_OPEN_FAILED:{exc}"]

    try:
        cols = [row[1] for row in conn.execute("PRAGMA table_info(force_snapshots)").fetchall()]
        symbol_col, tf_col, ts_col, currency_map = detect_db_columns(cols)

        if not currency_map:
            risks.append("NO_CURRENCY_COLUMNS_DETECTED")
            return [], {}, risks

        select_cols = []
        if ts_col:
            select_cols.append(ts_col)
        select_cols.extend(currency_map.values())

        where = []
        params: List[Any] = []
        if symbol_col:
            where.append(f"UPPER({symbol_col}) = ?")
            params.append(symbol.upper())
        else:
            risks.append("SYMBOL_COLUMN_MISSING")

        if tf_col:
            where.append(f"{tf_col} = ?")
            params.append(1)
        else:
            risks.append("TIMEFRAME_COLUMN_MISSING")

        sql = f"SELECT {', '.join(select_cols)} FROM force_snapshots"
        if where:
            sql += " WHERE " + " AND ".join(where)
        if ts_col:
            sql += f" ORDER BY {ts_col} DESC"
        sql += " LIMIT ?"
        params.append(int(bars))

        old_factory = conn.row_factory
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(sql, tuple(params)).fetchall()
        finally:
            conn.row_factory = old_factory

        if not rows:
            risks.append("NO_TF1_ROWS_FOR_SYMBOL")
            return list(currency_map.keys()), {}, risks

        latest = dict(rows[0])
        currencies = []
        for cur, col in currency_map.items():
            if latest.get(col) is not None:
                currencies.append(cur)

        if len(rows) < 30:
            risks.append("THIN_TF1_WINDOW")

        return currencies, latest, risks

    except Exception as exc:
        return [], {}, [f"DB_QUERY_FAILED:{exc}"]
    finally:
        conn.close()


def infer_capture_from_dict(value: Mapping[str, Any]) -> str:
    relay_available = ci_get(value, "relay_tf_available", ci_get(value, "RELAY_TF_AVAILABLE"))

    tf_fresh = ci_get(value, "tf_freshness", ci_get(value, "TF_FRESHNESS", {}))
    if not isinstance(tf_fresh, Mapping):
        tf_fresh = {}

    def tf_status(tf: str) -> str:
        section = ci_get(tf_fresh, tf, {})
        if not isinstance(section, Mapping):
            return "MISSING"
        return u(ci_get(section, "status", ci_get(section, "STATUS", "MISSING"))) or "MISSING"

    def tf_rows(tf: str) -> int:
        section = ci_get(tf_fresh, tf, {})
        if not isinstance(section, Mapping):
            return 0
        try:
            return int(ci_get(section, "rows", ci_get(section, "ROWS", 0)) or 0)
        except Exception:
            return 0

    m1_live = tf_status("M1") == "LIVE"
    m5_live = tf_status("M5") == "LIVE"
    m15_live = tf_status("M15") == "LIVE"

    if m1_live and m5_live and m15_live and relay_available is True:
        return "FULL_STACK_VISIBLE"
    if m1_live and m5_live:
        return "TACTICAL_OK"
    if m1_live and tf_rows("M1") > 0:
        return "MINIMAL"
    return "DEGRADED"


def extract_global_capture_dict(temporal_node: Mapping[str, Any]) -> Optional[Mapping[str, Any]]:
    value = ci_get(temporal_node, "capture_quality")
    if isinstance(value, Mapping):
        return value
    value = find_first_key(temporal_node, ("capture_quality", "CAPTURE_QUALITY"))
    if isinstance(value, Mapping):
        return value
    return None


def score_capture_quality(value: Any) -> Tuple[float, str]:
    if isinstance(value, Mapping):
        label = infer_capture_from_dict(value)
    else:
        label = u(value) or "MINIMAL"
    return CAPTURE_QUALITY_SCORE.get(label, 0.3), label


def score_noise_ratio(value: Any) -> Tuple[float, Optional[float]]:
    try:
        nr = float(value)
        if math.isnan(nr):
            raise ValueError("nan")
    except Exception:
        return 0.4, None

    if nr < 0.1:
        return 1.0, nr
    if nr <= 0.2:
        return 0.7, nr
    if nr <= 0.3:
        return 0.4, nr
    return 0.2, nr


def score_relay_quality(value: Any) -> Tuple[float, str]:
    if isinstance(value, Mapping):
        raw = (
            ci_get(value, "relay_sample_state")
            or ci_get(value, "RELAY_SAMPLE_STATE")
            or ci_get(value, "m5_role_capture")
            or ci_get(value, "M5_ROLE_CAPTURE")
            or ci_get(value, "relay_quality")
            or ci_get(value, "RELAY_QUALITY")
        )
    else:
        raw = value

    label = u(raw) or "M5_MISSING"
    if label == "CLEAN":
        label = "M5_RELAY_CLEAN"
    elif label == "THIN":
        label = "M5_THIN"
    elif label == "MISSING":
        label = "M5_MISSING"

    return RELAY_QUALITY_SCORE.get(label, 0.3), label


def score_session_phase(value: Any) -> Tuple[float, str]:
    label = u(value) or "DEAD_ZONE"
    return SESSION_PHASE_SCORE.get(label, 0.3), label


def score_regime(value: Any) -> Tuple[float, str]:
    label = u(value) or "UNKNOWN"
    return REGIME_SCORE.get(label, 0.4), label


def exploitability_label(score: float) -> str:
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


def intervention_window(session_phase: str, noise_score: float, relay_label: str) -> str:
    phase = u(session_phase) or "DEAD_ZONE"
    relay = u(relay_label) or "M5_MISSING"
    if phase == "DEAD_ZONE":
        return "DEAD_ZONE"
    if phase == "IGNITION" and noise_score >= 0.7 and relay == "M5_RELAY_CLEAN":
        return "IGNITION_CLEAN"
    if phase == "IGNITION" and noise_score >= 0.7:
        return "IGNITION_TACTICAL"
    if phase == "IGNITION":
        return "IGNITION_NOISY"
    if phase == "MID_SESSION" and noise_score < 0.7:
        return "MID_SESSION_NOISY"
    if phase == "MID_SESSION":
        return "MID_SESSION_TACTICAL"
    return f"{phase}_CONTEXT"


def compute_m1_context_score(inputs: M1ContextInputs) -> Dict[str, Any]:
    symbol = inputs.symbol.upper()
    paths = default_paths(symbol)

    kinematics_path = inputs.kinematics_path or paths["kinematics"]
    temporal_node_path = inputs.temporal_node_path or paths["temporal_node"]
    session_overlay_path = inputs.session_overlay_path or paths["session_overlay"]
    regime_hmm_path = inputs.regime_hmm_path or paths["regime_hmm"]
    regime_legacy_path = inputs.regime_legacy_path or paths["regime_legacy"]

    kinematics = read_json(kinematics_path)
    temporal_node = read_json(temporal_node_path)
    session_overlay = read_json(session_overlay_path)
    regime_hmm = read_json(regime_hmm_path)
    regime_legacy = read_json(regime_legacy_path)
    regime_source = regime_hmm if regime_hmm else regime_legacy
    regime_source_name = "regime_hmm" if regime_hmm else "regime_legacy"

    currencies, latest_row, db_risks = infer_currencies_from_db(inputs.db_path, symbol, inputs.bars)
    if not currencies:
        currencies = sorted(set([symbol[:3], symbol[3:]]))

    report: Dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "symbol": symbol,
        "method": "M1_CONTEXT_SCORE",
        "db_mode": "READ_ONLY",
        "weights": WEIGHTS,
        "input_paths": {
            "kinematics": kinematics_path,
            "temporal_node": temporal_node_path,
            "session_overlay": session_overlay_path,
            "regime_source": regime_source_name,
            "regime_hmm": regime_hmm_path,
            "regime_legacy": regime_legacy_path,
        },
        "db_snapshot": {
            "timeframe": 1,
            "latest_row_timestamp": latest_row.get("timestamp") or latest_row.get("timestamp_utc") or latest_row.get("time") or latest_row.get("datetime"),
            "currencies_detected": currencies,
        },
        "currencies": {},
        "technical_risks": list(db_risks),
        "note": "M1 is qualified, never censored. Score measures contextual exploitability, not financial risk.",
    }

    if not kinematics:
        report["technical_risks"].append("KINEMATICS_JSON_MISSING")
    if not temporal_node:
        report["technical_risks"].append("TEMPORAL_NODE_JSON_MISSING")
    if not session_overlay:
        report["technical_risks"].append("SESSION_OVERLAY_JSON_MISSING")
    if not regime_source:
        report["technical_risks"].append("REGIME_JSON_MISSING")

    global_capture = extract_global_capture_dict(temporal_node)

    for currency in currencies:
        crisk: List[str] = []

        capture_raw = scalar_for_currency(temporal_node, currency, (
            "capture_quality", "captureQuality", "CAPTURE_QUALITY",
            "capture", "CAPTURE", "capture_state", "CAPTURE_STATE",
        ))
        if not isinstance(capture_raw, Mapping) and global_capture is not None:
            capture_raw = global_capture

        capture_score, capture_label = score_capture_quality(capture_raw)
        if capture_raw is None:
            crisk.append("CAPTURE_QUALITY_MISSING_DEFAULT_MINIMAL")

        noise_raw = scalar_for_currency(kinematics, currency, (
            "noise_ratio", "noiseRatio", "kalman_noise_ratio", "NOISE_RATIO",
        ))
        noise_score, noise_ratio = score_noise_ratio(noise_raw)
        if noise_raw is None:
            crisk.append("NOISE_RATIO_MISSING_DEFAULT_0_4")

        first_detachment = scalar_for_currency(kinematics, currency, (
            "first_detachment", "firstDetachment", "FIRST_DETACHMENT",
        ))

        relay_raw = scalar_for_currency(temporal_node, currency, (
            "relay_quality", "relayQuality", "RELAY_QUALITY",
            "RELAY_SAMPLE_STATE", "relay_sample_state",
            "M5_ROLE_CAPTURE", "m5_role_capture",
            "relay",
        ))
        if relay_raw is None and isinstance(capture_raw, Mapping):
            relay_raw = capture_raw

        relay_score, relay_label = score_relay_quality(relay_raw)
        if relay_raw is None:
            crisk.append("RELAY_QUALITY_MISSING_DEFAULT_M5_MISSING")

        session_raw = scalar_for_currency(session_overlay, currency, ("session_phase", "phase", "SESSION_PHASE"))
        if session_raw is None:
            session_raw = find_first_key(session_overlay, ("session_phase", "phase", "SESSION_PHASE"))
        session_score, session_label = score_session_phase(session_raw)
        if session_raw is None:
            crisk.append("SESSION_PHASE_MISSING_DEFAULT_DEAD_ZONE")

        regime_raw = scalar_for_currency(regime_source, currency, ("regime", "regime_state", "state", "REGIME"))
        regime_score, regime_label = score_regime(regime_raw)
        if regime_raw is None:
            crisk.append("REGIME_MISSING_DEFAULT_UNKNOWN")

        score = (
            capture_score * WEIGHTS["capture_quality"]
            + noise_score * WEIGHTS["noise_ratio_score"]
            + relay_score * WEIGHTS["relay_quality"]
            + session_score * WEIGHTS["session_phase_score"]
            + regime_score * WEIGHTS["regime_score"]
        )
        score = round(max(0.0, min(1.0, score)), 4)

        report["currencies"][currency] = {
            "m1_context_score": score,
            "breakdown": {
                "capture_quality": capture_score,
                "noise_ratio_score": noise_score,
                "relay_quality": relay_score,
                "session_phase_score": session_score,
                "regime_score": regime_score,
            },
            "raw_context": {
                "capture_quality": capture_label,
                "noise_ratio": noise_ratio,
                "first_detachment": bool(first_detachment) if first_detachment is not None else None,
                "relay_quality": relay_label,
                "session_phase": session_label,
                "regime": regime_label,
            },
            "exploitability": exploitability_label(score),
            "intervention_window": intervention_window(session_label, noise_score, relay_label),
            "technical_risks": crisk,
        }

    return report


def write_json(data: Mapping[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


__all__ = ["M1ContextInputs", "compute_m1_context_score", "write_json"]
