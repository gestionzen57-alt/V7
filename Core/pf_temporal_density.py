# pf_temporal_density.py — PowerFlow V7 — B4 Temporal Density
# Autocorrélation rolling — détection compression de cycle
# Version : 1.0.0 — 2026-05-09
# Read-only DB. Pas de signal. Perception uniquement.

from __future__ import annotations
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np


CYCLE_STATES = {
    "CYCLE_COMPRESSING": "Oscillations se répètent plus vite → rupture imminente",
    "CYCLE_EXPANDING":   "Oscillations s'allongent → respiration / pullback",
    "CYCLE_STABLE":      "Fréquence stable → range / consolidation",
    "CYCLE_NOISY":       "Pas de cycle dominant → bruit ou transition",
}

# Seuils par TF (en barres)
COMPRESSION_THRESHOLD = {1: 0.65, 5: 0.60, 15: 0.55, 30: 0.50, 60: 0.45}
WINDOW_BARS = 30  # fenêtre autocorrélation


@dataclass
class TemporalDensityResult:
    currency: str
    timeframe: int
    compression_ratio: float   # 0.0 → 1.0 (1.0 = compression max)
    dominant_period_bars: int  # période dominante détectée
    cycle_state: str
    autocorr_peak: float       # valeur max autocorrélation
    bars_analyzed: int
    timestamp: str


def _fetch_series(
    db_path: str,
    col: str,
    timeframe: int,
    bars: int,
    lookback_min: Optional[int] = None,
) -> np.ndarray:
    """Fetch force series read-only."""
    uri = f"file:{db_path}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    try:
        if lookback_min:
            cutoff = (datetime.now(timezone.utc) - timedelta(minutes=lookback_min)).isoformat()
            rows = conn.execute(
                f"SELECT {col} FROM force_snapshots "
                f"WHERE timeframe=? AND created_at >= ? "
                f"ORDER BY created_at DESC LIMIT ?",
                (timeframe, cutoff, bars),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT {col} FROM force_snapshots "
                f"WHERE timeframe=? ORDER BY created_at DESC LIMIT ?",
                (timeframe, bars),
            ).fetchall()
        return np.array([r[0] for r in rows if r[0] is not None], dtype=float)
    finally:
        conn.close()


def _autocorr_rolling(series: np.ndarray, max_lag: int = 15) -> tuple[int, float, float]:
    """
    Autocorrélation sur série.
    Retourne : (dominant_period, peak_value, compression_ratio)
    """
    if len(series) < 10:
        return 0, 0.0, 0.0

    # Normaliser
    s = series - np.mean(series)
    std = np.std(s)
    if std < 1e-10:
        return 0, 0.0, 0.0
    s = s / std

    # Calculer autocorrélation lag 1..max_lag
    n = len(s)
    autocorrs = []
    for lag in range(1, min(max_lag + 1, n // 2)):
        c = np.corrcoef(s[:-lag], s[lag:])[0, 1]
        autocorrs.append((lag, abs(c)))

    if not autocorrs:
        return 0, 0.0, 0.0

    # Trouver le pic dominant
    best_lag, best_val = max(autocorrs, key=lambda x: x[1])

    # Compression ratio : ratio entre la période dominante et la fenêtre max
    # Plus la période est courte par rapport à max_lag → plus c'est comprimé
    compression = 1.0 - (best_lag / max_lag)
    compression = max(0.0, min(1.0, compression))

    return best_lag, best_val, compression


def compute_temporal_density(
    db_path: str,
    currency: str,
    timeframe: int,
    bars: int = WINDOW_BARS,
    lookback_min: Optional[int] = None,
) -> Optional[TemporalDensityResult]:
    """
    Compute cycle compression for one currency × timeframe.
    Returns None if insufficient data.
    """
    col = f"force_{currency.lower()}"
    series = _fetch_series(db_path, col, timeframe, bars, lookback_min)

    if len(series) < 10:
        return None

    # Inverser pour ordre chronologique
    series = series[::-1]

    dominant_period, peak_val, compression = _autocorr_rolling(series)

    # Déterminer état cycle
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
    )


def compute_temporal_density_multi(
    db_path: str,
    currencies: List[str],
    timeframes: List[int],
    bars: int = WINDOW_BARS,
    lookback_min: Optional[int] = None,
) -> Dict[str, Dict[int, Optional[TemporalDensityResult]]]:
    """
    Compute for all currencies × timeframes.
    Returns {currency: {tf: result}}
    """
    results = {}
    for ccy in currencies:
        results[ccy.upper()] = {}
        for tf in timeframes:
            results[ccy.upper()][tf] = compute_temporal_density(
                db_path, ccy, tf, bars, lookback_min
            )
    return results


def format_density_summary(results: Dict) -> dict:
    """Format pour cockpit JSON."""
    compressing = []
    expanding = []
    stable = []
    noisy = []

    flat = {}
    for ccy, tfs in results.items():
        for tf, r in tfs.items():
            if r is None:
                continue
            key = f"{ccy}_TF{tf}"
            flat[key] = {
                "currency": ccy,
                "timeframe": tf,
                "compression_ratio": r.compression_ratio,
                "dominant_period_bars": r.dominant_period_bars,
                "cycle_state": r.cycle_state,
                "autocorr_peak": r.autocorr_peak,
            }
            if r.cycle_state == "CYCLE_COMPRESSING":
                compressing.append(f"{ccy}_TF{tf}")
            elif r.cycle_state == "CYCLE_EXPANDING":
                expanding.append(f"{ccy}_TF{tf}")
            elif r.cycle_state == "CYCLE_STABLE":
                stable.append(f"{ccy}_TF{tf}")
            else:
                noisy.append(f"{ccy}_TF{tf}")

    return {
        "state": "TEMPORAL_DENSITY_ACTIVE",
        "compressing": compressing,
        "expanding": expanding,
        "stable": stable,
        "noisy": noisy,
        "details": flat,
        "compression_alert": len(compressing) >= 3,
        "compression_count": len(compressing),
    }
