"""
pf_wavelet_density.py
Temporal Density B4 - Morlet CWT (robuste vs autocorr fragile)

PowerFlow V7.1 contract:
- pf_* moteur pur: no cockpit/dashboard/telegram dependency
- DB access is handled by runners, not by this analyzer
- perception only: no BUY/SELL, no trade decision
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, Optional, Tuple

import json
import numpy as np


CYCLE_COMPRESSING = "CYCLE_COMPRESSING"
CYCLE_EXPANDING = "CYCLE_EXPANDING"
CYCLE_STABLE = "CYCLE_STABLE"
CYCLE_NOISY = "CYCLE_NOISY"

VALID = "VALID"
INVALID = "INVALID"
INSUFFICIENT_DATA = "INSUFFICIENT_DATA"

DEFAULT_MIN_BARS = 50
DEFAULT_SCALES = np.arange(1, 65, dtype=int)
COMPRESSION_THRESHOLD = 0.75
STABLE_THRESHOLD = 0.50
EPSILON = 1e-12


class WaveletDensityAnalyzer:
    """B4 - Cycle density via Morlet Continuous Wavelet Transform."""

    def __init__(
        self,
        wavelet: str = "morlet",
        scales: Optional[Iterable[int]] = None,
        min_bars: int = DEFAULT_MIN_BARS,
    ) -> None:
        self.wavelet = wavelet
        self.pywt_wavelet = self._resolve_pywt_wavelet_name(wavelet)
        self.scales = np.asarray(list(scales) if scales is not None else DEFAULT_SCALES, dtype=int)
        self.min_bars = int(min_bars)

        if self.scales.ndim != 1 or self.scales.size == 0:
            raise ValueError("scales must be a non-empty 1D iterable")
        if np.any(self.scales <= 0):
            raise ValueError("scales must be strictly positive")

    def analyze_timeframe(self, symbol: str, timeframe: int, force_rolling: Iterable[float]) -> Dict[str, Any]:
        """
        Analyze temporal density via Morlet CWT.

        Args:
            symbol: Display symbol, e.g. "GBPUSD".
            timeframe: Timeframe in minutes: 1, 5, 15, 30, 60, 240, 1440.
            force_rolling: Chronological force series, usually last 100 bars.

        Returns:
            JSON-ready dict compatible with B4 autocorr shape.
        """
        clean_signal = self._as_clean_signal(force_rolling)

        if clean_signal.size < self.min_bars:
            return self._invalid_result(
                symbol=symbol,
                timeframe=timeframe,
                validity=INSUFFICIENT_DATA,
                reason=f"INSUFFICIENT_DATA: need >= {self.min_bars} bars, got {clean_signal.size}",
            )

        # Static/weekend guard. CWT on a flat field is technically computable but behaviorally blind.
        if float(np.std(clean_signal)) < EPSILON:
            return self._invalid_result(
                symbol=symbol,
                timeframe=timeframe,
                validity=INVALID,
                reason="STATIC_SIGNAL: dominant_period_bars forced to 1",
            )

        try:
            coeffs = self._compute_cwt(clean_signal)
        except Exception as exc:
            return self._invalid_result(
                symbol=symbol,
                timeframe=timeframe,
                validity=INVALID,
                reason=f"CWT_ERROR: {exc}",
            )

        power = np.abs(coeffs) ** 2
        power_by_scale = power.sum(axis=1)
        total_power = float(np.sum(power_by_scale))

        if not np.isfinite(total_power) or total_power <= EPSILON:
            return self._invalid_result(
                symbol=symbol,
                timeframe=timeframe,
                validity=INVALID,
                reason="ZERO_WAVELET_POWER",
            )

        dominant_index = int(np.argmax(power_by_scale))
        dominant_scale = int(self.scales[dominant_index])
        max_power_scale = float(power_by_scale[dominant_index])

        compression_ratio = max_power_scale / total_power
        compression_ratio = float(np.clip(compression_ratio, 0.0, 1.0))

        # Morlet approximation used by mission spec: period in bars ~= scale * 4.
        dominant_period_bars = max(1, int(round(dominant_scale * 4)))

        if dominant_period_bars == 1:
            cycle_state = CYCLE_NOISY
            validity = INVALID
        elif compression_ratio > COMPRESSION_THRESHOLD:
            cycle_state = CYCLE_COMPRESSING
            validity = VALID
        elif compression_ratio >= STABLE_THRESHOLD:
            cycle_state = CYCLE_STABLE
            validity = VALID
        else:
            cycle_state = CYCLE_EXPANDING
            validity = VALID

        autocorr_peak = self._compute_autocorr(clean_signal)
        wavelet_power_max = float(np.max(power))

        return {
            "symbol": str(symbol).upper(),
            "timeframe": int(timeframe),
            "timestamp": self._utc_timestamp(),
            "cycle_state": cycle_state,
            "compression_ratio": float(compression_ratio),
            "dominant_period_bars": int(dominant_period_bars),
            "autocorr_peak": float(autocorr_peak),
            "wavelet_power_max": wavelet_power_max,
            "method": "morlet_cwt",
            "validity": validity,
        }

    def _compute_cwt(self, signal: np.ndarray) -> np.ndarray:
        """Compute Morlet CWT. Prefer PyWavelets; fallback keeps local tests executable."""
        try:
            import pywt  # type: ignore
        except ModuleNotFoundError:
            return self._compute_cwt_numpy_fallback(signal)

        cwt_result = pywt.cwt(signal, self.scales, self.pywt_wavelet)
        coeffs = cwt_result[0] if isinstance(cwt_result, tuple) else cwt_result
        coeffs = np.asarray(coeffs)

        expected_shape = (self.scales.size, signal.size)
        if coeffs.shape != expected_shape:
            raise ValueError(f"unexpected CWT shape {coeffs.shape}, expected {expected_shape}")

        return coeffs

    def _compute_cwt_numpy_fallback(self, signal: np.ndarray) -> np.ndarray:
        """
        Lightweight Morlet CWT fallback for environments where PyWavelets is not installed.

        Production should install PyWavelets and use pywt.cwt. The fallback exists so py_compile,
        smoke tests, and sample outputs do not collapse when the dependency is absent.
        """
        coeffs = []
        centered = signal - float(np.mean(signal))
        omega0 = 6.0

        for scale in self.scales:
            radius = max(8, min(int(8 * int(scale)), max(8, centered.size - 1)))
            t = np.arange(-radius, radius + 1, dtype=float)
            x = t / float(scale)
            wavelet = (np.pi ** -0.25) * np.exp(1j * omega0 * x) * np.exp(-0.5 * x * x)
            wavelet = wavelet / np.sqrt(float(scale))
            conv = np.convolve(centered, np.conj(wavelet[::-1]), mode="same")

            # np.convolve(..., mode="same") returns max(len(signal), len(wavelet)). Center-crop if needed.
            if conv.size != centered.size:
                start = (conv.size - centered.size) // 2
                conv = conv[start : start + centered.size]

            coeffs.append(conv)

        return np.asarray(coeffs)

    def _compute_autocorr(self, signal: Iterable[float]) -> float:
        """Compute autocorrelation peak for comparison with legacy B4."""
        s = self._as_clean_signal(signal)
        if s.size < 3:
            return 0.0

        s = s - float(np.mean(s))
        denom_std = float(np.std(s))
        if denom_std < EPSILON:
            return 0.0

        acf = np.correlate(s, s, mode="full")
        acf = acf[acf.size // 2 :]
        denom = float(acf[0])
        if abs(denom) < EPSILON:
            return 0.0

        acf = acf / denom
        upper = min(20, acf.size)
        if upper <= 1:
            return 0.0

        peak = np.nanmax(acf[1:upper])
        if not np.isfinite(peak):
            return 0.0
        return float(peak)

    def _invalid_result(self, symbol: str, timeframe: int, validity: str, reason: str) -> Dict[str, Any]:
        """Format invalid result with the same JSON contract as valid outputs."""
        return {
            "symbol": str(symbol).upper(),
            "timeframe": int(timeframe),
            "timestamp": self._utc_timestamp(),
            "cycle_state": CYCLE_NOISY,
            "compression_ratio": 0.0,
            "dominant_period_bars": 1,
            "autocorr_peak": 0.0,
            "wavelet_power_max": 0.0,
            "method": "morlet_cwt",
            "validity": validity,
            "error": reason,
        }

    @staticmethod
    def _as_clean_signal(values: Iterable[float]) -> np.ndarray:
        arr = np.asarray(list(values), dtype=float).reshape(-1)
        return arr[np.isfinite(arr)]

    @staticmethod
    def _resolve_pywt_wavelet_name(wavelet: str) -> str:
        # PyWavelets names Morlet as "morl". The mission language calls it "morlet".
        aliases = {"morlet": "morl", "morl": "morl"}
        return aliases.get(str(wavelet).lower(), wavelet)

    @staticmethod
    def _utc_timestamp() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> None:
    """Smoke example: synthetic cycle field, no DB access."""
    analyzer = WaveletDensityAnalyzer()
    x = np.linspace(0, 12 * np.pi, 100)
    force = 50.0 + 10.0 * np.sin(x) + np.random.default_rng(7).normal(0.0, 0.8, 100)
    result = analyzer.analyze_timeframe("GBPUSD", 5, force)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
