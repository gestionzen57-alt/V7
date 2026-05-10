"""PowerFlow V7.2 — B4 Wavelet Density.

Morlet CWT cycle-density perception. Read-only DB. No cockpit/telegram imports.
"""
from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np

try:
    import pywt  # type: ignore
except Exception:  # pragma: no cover - handled at runtime
    pywt = None

VERSION = "WaveletDensityV0.1Standalone"
METHOD = "morlet_cwt"
DEFAULT_SCALES = np.array([2, 3, 5, 8, 13, 21, 34, 55], dtype=int)

KNOWN_META_COLUMNS = {
    "id", "timestamp", "time", "datetime", "created_at", "updated_at",
    "symbol", "timeframe", "tf", "bid", "ask", "spread", "price",
    "open", "high", "low", "close", "volume", "tick_volume",
}

CURRENCY_COLUMNS = {
    "EUR": ["force_eur", "eur", "EUR"],
    "GBP": ["force_gbp", "gbp", "GBP"],
    "USD": ["force_usd", "usd", "USD"],
    "JPY": ["force_jpy", "jpy", "JPY"],
    "CHF": ["force_chf", "chf", "CHF"],
    "CAD": ["force_cad", "cad", "CAD"],
    "AUD": ["force_aud", "aud", "AUD"],
    "NZD": ["force_nzd", "nzd", "NZD"],
    "XAU": ["force_xau", "xau", "XAU"],
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def connect_readonly(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)


def normalize_wavelet_name(name: str) -> str:
    n = (name or "morl").lower().strip()
    if n in {"morlet", "morl"}:
        return "morl"
    return n


def clean_signal(signal: Sequence[float]) -> np.ndarray:
    x = np.asarray(signal, dtype=float)
    x = np.nan_to_num(x, nan=0.0, posinf=0.0, neginf=0.0)
    if x.size == 0:
        return x
    x = x - float(np.nanmean(x))
    std = float(np.nanstd(x))
    if std > 1e-12:
        x = x / std
    return x


def wavelet_compression_ratio(
    signal: Sequence[float],
    mother: str = "morl",
    scales: Optional[Sequence[int]] = None,
) -> Tuple[float, Dict[str, Any]]:
    """Calculate CWT Morlet concentration ratio.

    Metric:
        dominant_scale_power / total_power

    Higher ratio = energy concentrated on a narrow temporal scale = cycle compression.
    """
    if pywt is None:
        return 0.0, {"technical_risks": ["PYWAVELETS_MISSING"], "power_by_scale": {}}

    x = clean_signal(signal)
    if x.size < 16:
        return 0.0, {"technical_risks": ["INSUFFICIENT_DATA_WAVELET"], "power_by_scale": {}}
    if float(np.nanstd(x)) <= 1e-12:
        return 0.0, {"technical_risks": ["STATIC_SIGNAL_WAVELET"], "power_by_scale": {}}

    s = np.asarray(scales if scales is not None else DEFAULT_SCALES, dtype=int)
    s = s[(s >= 1) & (s <= max(2, x.size // 2))]
    if s.size == 0:
        s = np.arange(1, min(16, x.size // 2) + 1, dtype=int)

    wavelet_name = normalize_wavelet_name(mother)
    coeffs, freqs = pywt.cwt(x, s, wavelet_name)
    power = np.abs(coeffs) ** 2
    power_by_scale = power.sum(axis=1)
    total_power = float(power_by_scale.sum())

    if total_power <= 1e-12:
        return 0.0, {"technical_risks": ["ZERO_WAVELET_POWER"], "power_by_scale": {}}

    dominant_idx = int(np.argmax(power_by_scale))
    compression_ratio = float(power_by_scale[dominant_idx] / total_power)

    # Secondary quality: whether the dominant scale is gaining power in the last third.
    last_third = max(1, power.shape[1] // 3)
    dominant_power_series = power[dominant_idx]
    early = float(np.mean(dominant_power_series[:-last_third])) if dominant_power_series.size > last_third else 0.0
    late = float(np.mean(dominant_power_series[-last_third:]))
    power_slope = float((late - early) / (abs(early) + 1e-12))

    details = {
        "technical_risks": [],
        "wavelet": wavelet_name,
        "dominant_scale": int(s[dominant_idx]),
        "dominant_period_bars_wavelet": int(s[dominant_idx]),
        "dominant_power": float(power_by_scale[dominant_idx]),
        "total_power": total_power,
        "power_slope_late_vs_early": power_slope,
        "power_by_scale": {str(int(scale)): float(power_by_scale[i]) for i, scale in enumerate(s)},
        "frequencies": {str(int(scale)): float(freqs[i]) for i, scale in enumerate(s)},
    }
    return compression_ratio, details


def classify_cycle_state(compression_ratio: float, power_slope: float = 0.0, min_ratio: float = 0.40, max_ratio: float = 0.75) -> str:
    if not math.isfinite(compression_ratio):
        return "CYCLE_NOISY"
    if compression_ratio >= max_ratio or (compression_ratio >= 0.62 and power_slope > 0.25):
        return "CYCLE_COMPRESSING"
    if compression_ratio <= min_ratio and power_slope < -0.10:
        return "CYCLE_EXPANDING"
    if compression_ratio <= 0.08:
        return "CYCLE_NOISY"
    return "CYCLE_STABLE"


def _table_columns(conn: sqlite3.Connection) -> List[str]:
    return [str(r[1]) for r in conn.execute("PRAGMA table_info(force_snapshots)").fetchall()]


def _exists(cols: Sequence[str], name: str) -> bool:
    return any(c.lower() == name.lower() for c in cols)


def _resolve_symbol_columns(symbol: str, cols: Sequence[str]) -> Tuple[Optional[str], Optional[str], List[str]]:
    symbol = (symbol or "GBPUSD").upper().replace("/", "")
    base = symbol[:3]
    quote = symbol[3:6]
    lower_map = {c.lower(): c for c in cols}

    def find(cur: str) -> Optional[str]:
        for cand in CURRENCY_COLUMNS.get(cur, []):
            hit = lower_map.get(cand.lower())
            if hit:
                return hit
        return None

    base_col = find(base)
    quote_col = find(quote)
    force_cols = [c for c in cols if c.lower().startswith("force_")]
    if not force_cols:
        force_cols = [c for c in cols if c.lower() not in KNOWN_META_COLUMNS]
    return base_col, quote_col, force_cols


def load_force_window(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframe: int = 5,
    window: int = 100,
) -> Tuple[np.ndarray, Dict[str, Any]]:
    meta: Dict[str, Any] = {
        "db_path": db_path,
        "symbol": symbol,
        "timeframe": timeframe,
        "window": window,
        "rows": 0,
        "force_source": "UNKNOWN",
        "technical_risks": [],
    }
    try:
        conn = connect_readonly(db_path)
    except Exception as exc:
        meta["technical_risks"].append("DB_READ_ERROR")
        meta["error"] = str(exc)
        return np.asarray([], dtype=float), meta

    try:
        cols = _table_columns(conn)
        if not cols:
            meta["technical_risks"].append("FORCE_SNAPSHOTS_SCHEMA_MISSING")
            return np.asarray([], dtype=float), meta

        base_col, quote_col, force_cols = _resolve_symbol_columns(symbol, cols)
        has_symbol = _exists(cols, "symbol")
        has_tf = _exists(cols, "timeframe")
        has_ts = _exists(cols, "timestamp")

        if base_col and quote_col:
            select_cols = [base_col, quote_col]
            meta["force_source"] = f"{base_col}-{quote_col}"
        else:
            select_cols = force_cols[:8]
            meta["force_source"] = "mean_force_columns"

        if not select_cols:
            meta["technical_risks"].append("NO_FORCE_COLUMNS")
            return np.asarray([], dtype=float), meta

        where = []
        params: List[Any] = []
        if has_tf:
            where.append("timeframe = ?")
            params.append(int(timeframe))
        if has_symbol:
            where.append("symbol = ?")
            params.append(symbol)
        where_sql = (" WHERE " + " AND ".join(where)) if where else ""
        order_sql = " ORDER BY timestamp DESC" if has_ts else ""
        col_sql = ", ".join([f'"{c}"' for c in select_cols])
        rows = conn.execute(f"SELECT {col_sql} FROM force_snapshots{where_sql}{order_sql} LIMIT ?", params + [int(window)]).fetchall()
        rows = list(reversed(rows))
        meta["rows"] = len(rows)
        if len(rows) < 16:
            meta["technical_risks"].append("INSUFFICIENT_DATA_WAVELET")
            return np.asarray([], dtype=float), meta

        arr = np.asarray(rows, dtype=float)
        if arr.ndim == 1:
            force = arr
        elif base_col and quote_col and arr.shape[1] >= 2:
            force = arr[:, 0] - arr[:, 1]
        else:
            force = np.nanmean(arr, axis=1)
        return force.astype(float), meta
    except Exception as exc:
        meta["technical_risks"].append("WAVELET_DB_LOAD_ERROR")
        meta["error"] = str(exc)
        return np.asarray([], dtype=float), meta
    finally:
        conn.close()


def analyze_wavelet_density(
    signal: Sequence[float],
    symbol: str = "GBPUSD",
    timeframe: int = 5,
    scales: Optional[Sequence[int]] = None,
) -> Dict[str, Any]:
    ratio, details = wavelet_compression_ratio(signal, scales=scales)
    state = classify_cycle_state(ratio, float(details.get("power_slope_late_vs_early", 0.0)))
    return {
        "timestamp": utc_now_iso(),
        "symbol": symbol,
        "timeframe": int(timeframe),
        "cycle_state": state,
        "compression_ratio": float(ratio),
        "dominant_scales": [int(x) for x in (scales if scales is not None else DEFAULT_SCALES)],
        "power_spectrum": details.get("power_by_scale", {}),
        "wavelet_details": details,
        "method": METHOD,
        "version": VERSION,
        "valid": True,
        "technical_risks": details.get("technical_risks", []),
    }


def analyze_from_db(db_path: str, symbol: str = "GBPUSD", timeframe: int = 5, window: int = 100) -> Dict[str, Any]:
    signal, meta = load_force_window(db_path, symbol=symbol, timeframe=timeframe, window=window)
    if signal.size == 0:
        payload = analyze_wavelet_density([], symbol=symbol, timeframe=timeframe)
        payload["data_meta"] = meta
        payload["technical_risks"] = sorted(set(payload.get("technical_risks", []) + meta.get("technical_risks", [])))
        return payload
    payload = analyze_wavelet_density(signal, symbol=symbol, timeframe=timeframe)
    payload["data_meta"] = meta
    payload["technical_risks"] = sorted(set(payload.get("technical_risks", []) + meta.get("technical_risks", [])))
    return payload


def write_json(path: str, payload: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
