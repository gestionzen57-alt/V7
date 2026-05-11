"""
PowerFlow V7.2 — B4+ Wavelet Morlet Density Engine
Dual architecture: standalone Morlet CWT density perception, never fused with B4 Rolling.
DB access is read-only only.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import math
import sqlite3
from typing import Dict, Iterable, List, Sequence, Tuple

try:
    import numpy as np
except Exception as exc:  # pragma: no cover
    raise RuntimeError("numpy is required for pf_wavelet_density.py") from exc

CURRENCIES: Tuple[str, ...] = ("gbp", "usd", "eur", "jpy", "chf", "cad", "aud", "nzd")
VALID_WAVELET_STATES: Tuple[str, ...] = (
    "WAVELET_COMPRESSING",
    "WAVELET_EXPANDING",
    "WAVELET_MULTI_SCALE",
    "WAVELET_TRANSITIONING",
    "WAVELET_SILENT",
)
VALID_DRIFT: Tuple[str, ...] = ("COMPRESSING", "EXPANDING", "STABLE")
MIN_TF5_ROWS = 30


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ro_connect(db_path: str) -> sqlite3.Connection:
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _safe_float(value: object) -> float:
    try:
        if value is None:
            return 0.0
        out = float(value)
        if math.isnan(out) or math.isinf(out):
            return 0.0
        return out
    except Exception:
        return 0.0


@dataclass(frozen=True)
class WaveletDensityEngine:
    """Standalone B4+ Morlet CWT temporal density perception."""

    min_tf5_rows: int = MIN_TF5_ROWS
    max_scale_cap: int = 64

    def compute(self, db_path: str, symbol: str = "GBPUSD", timeframes: Sequence[int] = (1, 5, 15)) -> Dict[str, object]:
        tf5_count = self._count_rows(db_path, symbol, 5)
        if tf5_count < self.min_tf5_rows:
            return {
                "status": "INSUFFICIENT_DATA",
                "fallback": "B4_ROLLING",
                "method": "CWT_MORLET",
                "symbol": symbol,
                "rows_tf5": tf5_count,
                "items": [],
                "timestamp": _utc_now(),
                "technical_risks": ["TF5_INSUFFICIENT_ROWS"],
            }

        items: List[Dict[str, object]] = []
        technical_risks: List[str] = []
        for tf in timeframes:
            rows = self._load_rows(db_path, symbol, int(tf))
            if not rows:
                technical_risks.append(f"TF{tf}_NO_ROWS")
                continue
            for currency in CURRENCIES:
                series = np.array([r[currency] for r in rows], dtype=float)
                item = self._compute_one(series, currency, int(tf))
                items.append(item)
                technical_risks.extend([r for r in item.get("technical_risks", []) if r not in technical_risks])

        return {
            "status": "ACTIVE",
            "fallback": None,
            "method": "CWT_MORLET",
            "symbol": symbol,
            "timeframes": [int(x) for x in timeframes],
            "items": items,
            "timestamp": _utc_now(),
            "technical_risks": technical_risks,
        }

    def _count_rows(self, db_path: str, symbol: str, timeframe: int) -> int:
        with _ro_connect(db_path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM force_snapshots WHERE timeframe = ? AND symbol = ?",
                (int(timeframe), symbol),
            ).fetchone()
        return int(row[0] if row else 0)

    def _load_rows(self, db_path: str, symbol: str, timeframe: int) -> List[Dict[str, float]]:
        columns = ", ".join(["timestamp", *CURRENCIES])
        query = f"""
            SELECT {columns}
            FROM force_snapshots
            WHERE timeframe = ? AND symbol = ?
            ORDER BY timestamp ASC
        """
        with _ro_connect(db_path) as conn:
            cur = conn.execute(query, (int(timeframe), symbol))
            rows: List[Dict[str, float]] = []
            for row in cur.fetchall():
                d = {"timestamp": row[0]}
                for idx, c in enumerate(CURRENCIES, start=1):
                    d[c] = _safe_float(row[idx])
                rows.append(d)
        return rows

    def _compute_one(self, series: np.ndarray, currency: str, timeframe: int) -> Dict[str, object]:
        technical_risks: List[str] = []
        n = int(series.size)
        if n < 8:
            return self._silent(currency, timeframe, 1, ["WINDOW_TOO_SHORT"])
        clean = series.astype(float)
        clean = clean - float(np.nanmean(clean))
        std = float(np.nanstd(clean))
        if std < 1e-9:
            return self._silent(currency, timeframe, 1, [])
        clean = clean / std

        scales = np.arange(2, max(3, min(self.max_scale_cap, n // 2)) + 1, dtype=float)
        try:
            power = self._cwt_power(clean, scales)
        except Exception:
            technical_risks.append("PYWT_FALLBACK_USED")
            power = self._fallback_scale_power(clean, scales)

        if power.size == 0 or float(np.max(power)) < 1e-9:
            return self._silent(currency, timeframe, 1, technical_risks)

        total_by_scale = np.mean(power, axis=1)
        dominant_idx = int(np.argmax(total_by_scale))
        dominant_scale = int(round(float(scales[dominant_idx])))
        max_energy = float(total_by_scale[dominant_idx])
        total_energy = float(np.sum(total_by_scale)) or 1.0

        short_mask = scales <= max(4.0, np.percentile(scales, 35))
        long_mask = scales >= max(5.0, np.percentile(scales, 65))
        high_frequency_energy = float(np.sum(total_by_scale[short_mask]))
        low_frequency_energy = float(np.sum(total_by_scale[long_mask]))
        wavelet_energy_ratio = low_frequency_energy / (high_frequency_energy + 1e-12)

        active_scale_count = int(np.sum(total_by_scale >= max_energy * 0.55))
        multi_scale_flag = bool(active_scale_count >= 2)

        time_dominant = scales[np.argmax(power, axis=0)]
        cut = max(3, min(10, len(time_dominant) // 3))
        early = float(np.mean(time_dominant[:cut]))
        recent = float(np.mean(time_dominant[-cut:]))
        if recent < early * 0.88:
            drift = "COMPRESSING"
        elif recent > early * 1.12:
            drift = "EXPANDING"
        else:
            drift = "STABLE"

        recent_short = float(np.mean(np.sum(power[short_mask, -cut:], axis=0)))
        prior_short = float(np.mean(np.sum(power[short_mask, max(0, power.shape[1] - 2 * cut): max(0, power.shape[1] - cut)], axis=0))) if power.shape[1] >= 2 * cut else 0.0
        compression_onset = bool(drift == "COMPRESSING" and recent_short > prior_short * 1.15)

        energy_norm = max_energy / (total_energy + 1e-12)
        if energy_norm < 0.03:
            state = "WAVELET_SILENT"
        elif multi_scale_flag and active_scale_count >= 3:
            state = "WAVELET_MULTI_SCALE"
        elif compression_onset or (drift == "COMPRESSING" and wavelet_energy_ratio < 0.85):
            state = "WAVELET_COMPRESSING"
        elif drift == "EXPANDING" or wavelet_energy_ratio > 1.25:
            state = "WAVELET_EXPANDING"
        elif drift != "STABLE":
            state = "WAVELET_TRANSITIONING"
        else:
            state = "WAVELET_SILENT" if energy_norm < 0.06 else "WAVELET_TRANSITIONING"

        return {
            "currency": currency.upper(),
            "timeframe": int(timeframe),
            "wavelet_state": state,
            "dominant_scale_bars": max(1, dominant_scale),
            "wavelet_energy_ratio": round(float(wavelet_energy_ratio), 6),
            "scale_drift_direction": drift,
            "multi_scale_flag": multi_scale_flag,
            "compression_onset": compression_onset,
            "method": "CWT_MORLET",
            "technical_risks": technical_risks,
            "timestamp": _utc_now(),
        }

    def _cwt_power(self, clean: np.ndarray, scales: np.ndarray) -> np.ndarray:
        import pywt  # type: ignore
        coeffs, _ = pywt.cwt(clean, scales, "morl")
        return np.abs(coeffs) ** 2

    def _fallback_scale_power(self, clean: np.ndarray, scales: np.ndarray) -> np.ndarray:
        x = np.arange(clean.size, dtype=float)
        power = np.zeros((len(scales), clean.size), dtype=float)
        for i, scale in enumerate(scales):
            width = max(3, int(round(scale)))
            t = np.arange(-3 * width, 3 * width + 1, dtype=float)
            wave = np.cos(5.0 * t / width) * np.exp(-(t ** 2) / (2.0 * width ** 2))
            wave = wave - np.mean(wave)
            norm = float(np.sqrt(np.sum(wave ** 2))) or 1.0
            wave = wave / norm
            conv = np.convolve(clean, wave, mode="same")
            if conv.size != clean.size:
                start = max(0, (conv.size - clean.size) // 2)
                conv = conv[start:start + clean.size]
            if conv.size < clean.size:
                conv = np.pad(conv, (0, clean.size - conv.size), mode="constant")
            power[i, :] = conv ** 2
        return power

    def _silent(self, currency: str, timeframe: int, dominant_scale: int, risks: Sequence[str]) -> Dict[str, object]:
        return {
            "currency": currency.upper(),
            "timeframe": int(timeframe),
            "wavelet_state": "WAVELET_SILENT",
            "dominant_scale_bars": max(1, int(dominant_scale)),
            "wavelet_energy_ratio": 0.0,
            "scale_drift_direction": "STABLE",
            "multi_scale_flag": False,
            "compression_onset": False,
            "method": "CWT_MORLET",
            "technical_risks": list(risks),
            "timestamp": _utc_now(),
        }


def compute(db_path: str, symbol: str = "GBPUSD", timeframes: Sequence[int] = (1, 5, 15)) -> Dict[str, object]:
    return WaveletDensityEngine().compute(db_path=db_path, symbol=symbol, timeframes=timeframes)
