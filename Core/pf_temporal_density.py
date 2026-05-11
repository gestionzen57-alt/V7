# -*- coding: utf-8 -*-
"""PowerFlow V7.2 — B4 Temporal Density, symbol-parametric patch.

Patch objectif:
  - Ajouter symbol comme paramètre.
  - Filtrer force_snapshots par UPPER(symbol)=?.
  - Conserver l'API existante autant que possible.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

import numpy as np

CYCLE_STATES = {
    "CYCLE_COMPRESSING": "Oscillations se répètent plus vite -> rupture imminente",
    "CYCLE_EXPANDING": "Oscillations s'allongent -> respiration / pullback",
    "CYCLE_STABLE": "Fréquence stable -> range / consolidation",
    "CYCLE_NOISY": "Pas de cycle dominant -> bruit ou transition",
}
COMPRESSION_THRESHOLD = {1: 0.65, 5: 0.60, 15: 0.55, 30: 0.50, 60: 0.45}
WINDOW_BARS = 30


@dataclass
class TemporalDensityResult:
    currency: str
    timeframe: int
    compression_ratio: float
    dominant_period_bars: int
    cycle_state: str
    autocorr_peak: float
    bars_analyzed: int
    timestamp: str
    symbol: str = "GBPUSD"


def _timestamp_col(conn: sqlite3.Connection) -> str:
    cols = [r[1] for r in conn.execute('PRAGMA table_info("force_snapshots")').fetchall()]
    if "created_at" in cols:
        return "created_at"
    if "timestamp" in cols:
        return "timestamp"
    return "created_at"


def _fetch_series(
    db_path: str,
    col: str,
    timeframe: int,
    bars: int,
    lookback_min: Optional[int] = None,
    symbol: str = "GBPUSD",
) -> np.ndarray:
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        ts_col = _timestamp_col(conn)
        if lookback_min:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=lookback_min)).isoformat()
            rows = conn.execute(
                f'SELECT "{col}" FROM force_snapshots WHERE UPPER(symbol)=? AND timeframe=? AND "{ts_col}" >= ? ORDER BY "{ts_col}" DESC LIMIT ?',
                (symbol.upper(), timeframe, cutoff, bars),
            ).fetchall()
        else:
            rows = conn.execute(
                f'SELECT "{col}" FROM force_snapshots WHERE UPPER(symbol)=? AND timeframe=? ORDER BY "{ts_col}" DESC LIMIT ?',
                (symbol.upper(), timeframe, bars),
            ).fetchall()
        return np.array([r[0] for r in rows if r[0] is not None], dtype=float)
    finally:
        conn.close()


def _autocorr_rolling(series: np.ndarray, max_lag: int = 15) -> tuple[int, float, float]:
    if len(series) < 10:
        return 0, 0.0, 0.0
    s = series - np.mean(series)
    std = np.std(s)
    if std < 1e-10:
        return 0, 0.0, 0.0
    s = s / std
    n = len(s)
    autocorrs = []
    for lag in range(1, min(max_lag + 1, n // 2)):
        c = np.corrcoef(s[:-lag], s[lag:])[0, 1]
        autocorrs.append((lag, abs(c)))
    if not autocorrs:
        return 0, 0.0, 0.0
    best_lag, best_val = max(autocorrs, key=lambda x: x[1])
    compression = max(0.0, min(1.0, 1.0 - (best_lag / max_lag)))
    return best_lag, float(best_val), float(compression)


def compute_temporal_density(
    db_path: str,
    currency: str,
    timeframe: int,
    bars: int = WINDOW_BARS,
    lookback_min: Optional[int] = None,
    symbol: str = "GBPUSD",
) -> Optional[TemporalDensityResult]:
    col = f"force_{currency.lower()}"
    series = _fetch_series(db_path, col, timeframe, bars, lookback_min, symbol=symbol)
    if len(series) < 10:
        return None
    series = series[::-1]
    dominant_period, peak_val, compression = _autocorr_rolling(series)
    threshold = COMPRESSION_THRESHOLD.get(timeframe, 0.55)
    if peak_val < 0.25:
        state = "CYCLE_NOISY"
    elif compression >= threshold:
        state = "CYCLE_COMPRESSING"
    elif compression <= (1.0 - threshold):
        state = "CYCLE_EXPANDING"
    else:
        state = "CYCLE_STABLE"
    return TemporalDensityResult(
        currency=currency.upper(),
        timeframe=timeframe,
        compression_ratio=round(compression, 3),
        dominant_period_bars=dominant_period,
        cycle_state=state,
        autocorr_peak=round(peak_val, 3),
        bars_analyzed=len(series),
        timestamp=datetime.now(timezone.utc).isoformat(),
        symbol=symbol.upper(),
    )


def compute_temporal_density_multi(
    db_path: str,
    currencies: List[str],
    timeframes: List[int],
    bars: int = WINDOW_BARS,
    lookback_min: Optional[int] = None,
    symbol: str = "GBPUSD",
) -> Dict[str, Dict[int, Optional[TemporalDensityResult]]]:
    results = {}
    for ccy in currencies:
        results[ccy.upper()] = {}
        for tf in timeframes:
            results[ccy.upper()][tf] = compute_temporal_density(
                db_path, ccy, tf, bars, lookback_min, symbol=symbol
            )
    return results


def format_density_summary(results: Dict, symbol: str = "GBPUSD") -> dict:
    compressing, expanding, stable, noisy = [], [], [], []
    flat = {}
    for ccy, tfs in results.items():
        for tf, r in tfs.items():
            if r is None:
                continue
            key = f"{ccy}_TF{tf}"
            flat[key] = {
                "symbol": getattr(r, "symbol", symbol.upper()),
                "currency": ccy,
                "timeframe": tf,
                "compression_ratio": r.compression_ratio,
                "dominant_period_bars": r.dominant_period_bars,
                "cycle_state": r.cycle_state,
                "autocorr_peak": r.autocorr_peak,
                "timestamp_utc": r.timestamp,
                "method": "B4_ROLLING_SYMBOL_PARAMETRIC",
            }
            if r.cycle_state == "CYCLE_COMPRESSING":
                compressing.append(key)
            elif r.cycle_state == "CYCLE_EXPANDING":
                expanding.append(key)
            elif r.cycle_state == "CYCLE_STABLE":
                stable.append(key)
            else:
                noisy.append(key)
    return {
        "state": "TEMPORAL_DENSITY_ACTIVE",
        "symbol": symbol.upper(),
        "method": "B4_ROLLING_SYMBOL_PARAMETRIC",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "compressing": compressing,
        "expanding": expanding,
        "stable": stable,
        "noisy": noisy,
        "details": flat,
        "compression_alert": len(compressing) >= 3,
        "compression_count": len(compressing),
    }
