#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — M1_CONTEXT_SCORE

M1 is never censored.
This module qualifies contextual exploitability of M1 microfilm signals.

Architecture:
- pf_* module
- read-only DB access
- no BUY/SELL
- no DB writes
- no dependency on cockpit/dashboard/telegram
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


CURRENCY_COLUMNS = ("GBP", "EUR", "USD", "JPY", "CAD", "CHF", "AUD", "NZD", "XAU")

CAPTURE_QUALITY_SCORE = {
    "FULL_STACK_VISIBLE": 1.0,
    "TACTICAL_OK": 0.8,
    "DEGRADED": 0.5,
    "MINIMAL": 0.3,
    "BLIND": 0.0,
}

RELAY_QUALITY_SCORE = {
    "M5_RELAY_CLEAN": 1.0,
    "M5_THIN": 0.6,
    "M5_MISSING": 0.3,
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


def normalize_upper(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text.upper()


def nested_get(obj: Any, keys: Iterable[str]) -> Any:
    current = obj
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        if key not in current:
            return None
        current = current[key]
    return current


def find_first_key(obj: Any, key_names: Iterable[str]) -> Any:
    """Depth-first search for the first matching key."""
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


def currency_candidates(currency: str) -> List[str]:
    c = currency.upper()
    return [c, c.lower(), f"force_{c.lower()}", f"{c.lower()}_force"]


def find_currency_section(obj: Any, currency: str) -> Optional[Mapping[str, Any]]:
    """Find a dict section specific to a currency in heterogeneous PowerFlow JSON."""
    if not isinstance(obj, (Mapping, list)):
        return None

    cands = set(currency_candidates(currency))

    if isinstance(obj, Mapping):
        for key in cands:
            value = obj.get(key)
            if isinstance(value, Mapping):
                return value

        for collection_key in ("currencies", "currency_states", "states", "nodes", "kinematics"):
            value = obj.get(collection_key)
            if isinstance(value, Mapping):
                for key in cands:
                    section = value.get(key)
                    if isinstance(section, Mapping):
                        return section
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, Mapping) and normalize_upper(item.get("currency")) == currency.upper():
                        return item

        if normalize_upper(obj.get("currency")) == currency.upper():
            return obj

        for value in obj.values():
            section = find_currency_section(value, currency)
            if section:
                return section

    elif isinstance(obj, list):
        for item in obj:
            section = find_currency_section(item, currency)
            if section:
                return section

    return None


def scalar_for_currency(obj: Mapping[str, Any], currency: str, keys: Iterable[str]) -> Any:
    section = find_currency_section(obj, currency)
    if isinstance(section, Mapping):
        for key in keys:
            if key in section:
                return section[key]
        found = find_first_key(section, keys)
        if found is not None:
            return found

    # fallback global value
    for key in keys:
        if key in obj:
            return obj[key]
    return find_first_key(obj, keys)


def infer_currencies_from_db(db_path: str, symbol: str, bars: int = 120) -> Tuple[List[str], Dict[str, Any], List[str]]:
    """Read TF1 rows to infer available currency columns for the symbol."""
    risks: List[str] = []
    currencies: List[str] = []
    latest_row: Dict[str, Any] = {}

    try:
        conn = connect_readonly(db_path)
    except Exception as exc:
        return [], {}, [f"DB_OPEN_FAILED:{exc}"]

    try:
        columns = [row[1] for row in conn.execute("PRAGMA table_info(force_snapshots)").fetchall()]
        lower_to_real = {c.lower(): c for c in columns}

        currency_cols = []
        for c in CURRENCY_COLUMNS:
            real = lower_to_real.get(c.lower())
            if real:
                currency_cols.append(real)

        if not currency_cols:
            risks.append("NO_CURRENCY_COLUMNS_DETECTED")
            return [], {}, risks

        symbol_col = lower_to_real.get("symbol")
        timeframe_col = lower_to_real.get("timeframe")
        timestamp_col = lower_to_real.get("timestamp") or lower_to_real.get("timestamp_utc") or lower_to_real.get("time")

        select_cols = ", ".join([timestamp_col] + currency_cols) if timestamp_col else ", ".join(currency_cols)

        where = []
        params: List[Any] = []
        if symbol_col:
            where.append(f"UPPER({symbol_col}) = ?")
            params.append(symbol.upper())
        else:
            risks.append("SYMBOL_COLUMN_MISSING")

        if timeframe_col:
            where.append(f"{timeframe_col} = ?")
            params.append(1)
        else:
            risks.append("TIMEFRAME_COLUMN_MISSING")

        where_sql = " WHERE " + " AND ".join(where) if where else ""
        order_sql = f" ORDER BY {timestamp_col} DESC" if timestamp_col else ""
        sql = f"SELECT {select_cols} FROM force_snapshots{where_sql}{order_sql} LIMIT ?"
        params.append(int(bars))

        old_factory = conn.row_factory
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(sql, tuple(params)).fetchall()
        finally:
            conn.row_factory = old_factory

        if not rows:
            risks.append("NO_TF1_ROWS_FOR_SYMBOL")
            return [c.upper() for c in currency_cols], {}, risks

        latest_row = dict(rows[0])
        currencies = [c.upper() for c in currency_cols if latest_row.get(c) is not None]

        if len(rows) < 30:
            risks.append("THIN_TF1_WINDOW")

        return currencies, latest_row, risks

    except Exception as exc:
        return [], {}, [f"DB_QUERY_FAILED:{exc}"]
    finally:
        conn.close()


def score_capture_quality(value: Any) -> Tuple[float, str]:
    label = normalize_upper(value) or "MINIMAL"
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
    label = normalize_upper(value) or "M5_MISSING"
    return RELAY_QUALITY_SCORE.get(label, 0.3), label


def score_session_phase(value: Any) -> Tuple[float, str]:
    label = normalize_upper(value) or "DEAD_ZONE"
    return SESSION_PHASE_SCORE.get(label, 0.3), label


def score_regime(value: Any) -> Tuple[float, str]:
    label = normalize_upper(value) or "UNKNOWN"
    return REGIME_SCORE.get(label, 0.4), label


def exploitability_label(score: float) -> str:
    if score >= 0.7:
        return "HIGH"
    if score >= 0.4:
        return "MEDIUM"
    return "LOW"


def intervention_window(session_phase: str, noise_score: float, relay_label: str) -> str:
    phase = normalize_upper(session_phase) or "DEAD_ZONE"
    relay = normalize_upper(relay_label) or "M5_MISSING"

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
        # Pair fallback if DB is missing or no rows.
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
            "latest_row_timestamp": latest_row.get("timestamp") or latest_row.get("timestamp_utc") or latest_row.get("time"),
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

    for currency in currencies:
        crisk: List[str] = []

        capture_raw = scalar_for_currency(temporal_node, currency, ("capture_quality", "captureQuality"))
        capture_score, capture_label = score_capture_quality(capture_raw)
        if capture_raw is None:
            crisk.append("CAPTURE_QUALITY_MISSING_DEFAULT_MINIMAL")

        noise_raw = scalar_for_currency(kinematics, currency, ("noise_ratio", "noiseRatio", "kalman_noise_ratio"))
        noise_score, noise_ratio = score_noise_ratio(noise_raw)
        if noise_raw is None:
            crisk.append("NOISE_RATIO_MISSING_DEFAULT_0_4")

        first_detachment = scalar_for_currency(kinematics, currency, ("first_detachment", "firstDetachment"))
        relay_raw = scalar_for_currency(temporal_node, currency, ("relay_quality", "relayQuality"))
        relay_score, relay_label = score_relay_quality(relay_raw)
        if relay_raw is None:
            crisk.append("RELAY_QUALITY_MISSING_DEFAULT_M5_MISSING")

        session_raw = scalar_for_currency(session_overlay, currency, ("session_phase", "phase"))
        session_score, session_label = score_session_phase(session_raw)
        if session_raw is None:
            # fallback: global session field commonly used by session overlay.
            session_raw = find_first_key(session_overlay, ("session_phase", "phase"))
            session_score, session_label = score_session_phase(session_raw)
            if session_raw is None:
                crisk.append("SESSION_PHASE_MISSING_DEFAULT_DEAD_ZONE")

        regime_raw = scalar_for_currency(regime_source, currency, ("regime", "regime_state", "state"))
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


__all__ = [
    "M1ContextInputs",
    "compute_m1_context_score",
    "write_json",
]
