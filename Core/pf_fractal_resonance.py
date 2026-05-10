"""
pf_fractal_resonance.py
B7 — Fractal Resonance Detection for PowerFlow V7.1

Detects whether adjacent timeframes vibrate together, lag each other,
or remain dissonant/silent. This is a perception module: it measures and
qualifies synchronization; it does not decide trades.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np


RESONANT = "RESONANT"
LAGGED = "LAGGED"
DISSONANT = "DISSONANT"
SILENT = "SILENT"
INVALID = "INVALID"

INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
CORRELATION_UNSTABLE = "CORRELATION_UNSTABLE"
FLAT_SERIES = "FLAT_SERIES"
LAGGED_MULTIPLE_TF = "LAGGED_MULTIPLE_TF"
SILENT_HTF = "SILENT_HTF"
MISSING_TIMEFRAME = "MISSING_TIMEFRAME"


@dataclass(frozen=True)
class ResonanceThresholds:
    """PowerFlow B7 thresholds calibrated for Forex multi-timeframe resonance."""

    resonant: float = 0.80
    lagged: float = 0.60
    dissonant: float = 0.30
    high_lag_bars: int = 3


class FractalResonanceAnalyzer:
    """
    Detect synchronization between adjacent timeframes.

    Input expected by analyze_multi_tf:
        {
            1: np.array([...]),
            5: np.array([...]),
            15: np.array([...]),
            30: np.array([...]),
            60: np.array([...]),
            240: np.array([...]),
        }

    Output states:
        RESONANT  -> adjacent TFs vibrate together
        LAGGED    -> correlation exists but higher TF is trailing
        DISSONANT -> weak synchronization
        SILENT    -> no meaningful synchronization
    """

    DEFAULT_ADJACENT_PAIRS: Tuple[Tuple[int, int], ...] = (
        (1, 5),
        (5, 15),
        (15, 30),
        (30, 60),
        (60, 240),
    )

    def __init__(
        self,
        corr_window: int = 50,
        max_lag: int = 10,
        thresholds: Optional[ResonanceThresholds] = None,
    ) -> None:
        self.corr_window = int(corr_window)
        self.max_lag = int(max_lag)
        self.thresholds = thresholds or ResonanceThresholds()

        self.resonant_threshold = self.thresholds.resonant
        self.lagged_threshold = self.thresholds.lagged
        self.dissonant_threshold = self.thresholds.dissonant

    def analyze_pair(self, force_tf1: Sequence[float], force_tf2: Sequence[float]) -> Dict[str, object]:
        """
        Analyze resonance between two rolling force series.

        Args:
            force_tf1: lower timeframe rolling force series
            force_tf2: higher timeframe rolling force series

        Returns:
            {
                "correlation": float,
                "lag_detected": int,
                "xcorr_peak": float,
                "resonance_state": "RESONANT|LAGGED|DISSONANT|SILENT",
                "valid": bool,
                "technical_risks": list[str]
            }
        """
        s1, s2 = self._prepare_pair(force_tf1, force_tf2)
        risks: List[str] = []

        if len(s1) < self.corr_window or len(s2) < self.corr_window:
            risks.append(INSUFFICIENT_DATA)
            return {
                "correlation": 0.0,
                "lag_detected": 0,
                "xcorr_peak": 0.0,
                "resonance_state": SILENT,
                "valid": False,
                "technical_risks": risks,
            }

        std1 = float(np.std(s1))
        std2 = float(np.std(s2))
        if std1 < 1e-10 or std2 < 1e-10:
            risks.append(FLAT_SERIES)
            return {
                "correlation": 0.0,
                "lag_detected": 0,
                "xcorr_peak": 0.0,
                "resonance_state": SILENT,
                "valid": False,
                "technical_risks": risks,
            }

        s1_norm = self._zscore(s1)
        s2_norm = self._zscore(s2)

        corr = float(np.corrcoef(s1_norm, s2_norm)[0, 1])
        if not np.isfinite(corr):
            corr = 0.0
            risks.append(CORRELATION_UNSTABLE)

        lag_result = self._detect_lag_with_peak(s1_norm, s2_norm, self.max_lag)
        lag_bars = int(lag_result["lag_bars"])
        xcorr_peak = float(lag_result["xcorr_peak"])

        state = self._classify_pair(corr, lag_bars)
        if state == LAGGED and abs(lag_bars) >= self.thresholds.high_lag_bars:
            risks.append(LAGGED_MULTIPLE_TF)

        return {
            "correlation": round(corr, 6),
            "lag_detected": lag_bars,
            "xcorr_peak": round(xcorr_peak, 6),
            "resonance_state": state,
            "valid": True,
            "technical_risks": risks,
        }

    def detect_lag(self, force_tf1: Sequence[float], force_tf2: Sequence[float], max_lag: int = 10) -> int:
        """
        Detect whether TF2 trails TF1.

        Positive lag means the second series reacts after the first series.
        Negative lag means the second series appears ahead of the first series.
        """
        s1, s2 = self._prepare_pair(force_tf1, force_tf2)
        if len(s1) < 3 or len(s2) < 3 or np.std(s1) < 1e-10 or np.std(s2) < 1e-10:
            return 0
        return int(self._detect_lag_with_peak(self._zscore(s1), self._zscore(s2), int(max_lag))["lag_bars"])

    def analyze_multi_tf(
        self,
        angles_dict: Mapping[int, Sequence[float]],
        symbol: str = "GBPUSD",
        timestamp: Optional[str] = None,
        pairs: Optional[Iterable[Tuple[int, int]]] = None,
    ) -> Dict[str, object]:
        """
        Analyze multi-timeframe fractal resonance.

        The parameter name angles_dict is preserved for integration with B3,
        but the method accepts any rolling force/angle-like series per TF.
        """
        timestamp = timestamp or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        clean_inputs: Dict[int, np.ndarray] = {int(tf): self._to_float_array(series) for tf, series in angles_dict.items()}
        adjacent_pairs = list(pairs) if pairs is not None else self._select_available_pairs(clean_inputs)

        pair_correlations: Dict[str, float] = {}
        lag_detection: Dict[str, int] = {}
        pair_states: Dict[str, str] = {}
        pair_validity: Dict[str, bool] = {}
        pair_xcorr_peak: Dict[str, float] = {}
        technical_risks: List[str] = []

        valid_correlations: List[float] = []
        valid_positive_correlations: List[float] = []
        lagged_tfs_set = set()
        resonant_tfs_set = set()
        dissonant_tfs_set = set()

        if not adjacent_pairs:
            return self._invalid_multi_tf_result(
                symbol=symbol,
                timestamp=timestamp,
                reason=INSUFFICIENT_DATA,
                clean_inputs=clean_inputs,
            )

        for tf_low, tf_high in adjacent_pairs:
            key = self._pair_key(tf_low, tf_high)
            if tf_low not in clean_inputs or tf_high not in clean_inputs:
                pair_correlations[key] = 0.0
                lag_detection[key] = 0
                pair_states[key] = SILENT
                pair_validity[key] = False
                pair_xcorr_peak[key] = 0.0
                technical_risks.append(f"{MISSING_TIMEFRAME}:{key}")
                continue

            pair_result = self.analyze_pair(clean_inputs[tf_low], clean_inputs[tf_high])
            corr = float(pair_result["correlation"])
            lag = int(pair_result["lag_detected"])
            state = str(pair_result["resonance_state"])
            valid = bool(pair_result["valid"])

            pair_correlations[key] = corr
            lag_detection[key] = lag
            pair_states[key] = state
            pair_validity[key] = valid
            pair_xcorr_peak[key] = float(pair_result["xcorr_peak"])
            technical_risks.extend(str(r) for r in pair_result.get("technical_risks", []))

            if valid:
                valid_correlations.append(corr)
                valid_positive_correlations.append(max(0.0, corr))

            if state == RESONANT:
                resonant_tfs_set.update([tf_low, tf_high])
            elif state == LAGGED:
                resonant_tfs_set.add(tf_low)
                lagged_tfs_set.add(tf_high)
            elif state == DISSONANT:
                dissonant_tfs_set.update([tf_low, tf_high])
            else:
                dissonant_tfs_set.update([tf_low, tf_high])

        if not valid_correlations:
            return self._invalid_multi_tf_result(
                symbol=symbol,
                timestamp=timestamp,
                reason=INSUFFICIENT_DATA,
                clean_inputs=clean_inputs,
                pair_correlations=pair_correlations,
                lag_detection=lag_detection,
                pair_states=pair_states,
            )

        resonance_score = float(np.mean(valid_positive_correlations))
        avg_signed_corr = float(np.mean(valid_correlations))
        state = self.classify_resonance(valid_positive_correlations, lag_detection)

        if state == SILENT and any(tf >= 60 for tf in clean_inputs):
            technical_risks.append(SILENT_HTF)

        if len([lag for lag in lag_detection.values() if abs(lag) >= self.thresholds.high_lag_bars]) >= 2:
            technical_risks.append(LAGGED_MULTIPLE_TF)

        all_tfs = set(clean_inputs.keys())
        resonant_tfs = sorted(resonant_tfs_set)
        lagged_tfs = sorted(lagged_tfs_set - resonant_tfs_set)
        dissonant_tfs = sorted((dissonant_tfs_set | all_tfs) - resonant_tfs_set - lagged_tfs_set)

        expected_amplification = bool(
            state == RESONANT
            and resonance_score >= self.resonant_threshold
            and len([tf for tf in resonant_tfs if tf in (1, 5, 15, 30, 60)]) >= 3
        )

        return {
            "timestamp": timestamp,
            "symbol": symbol,
            "resonance_state": state,
            "resonance_score": round(resonance_score, 6),
            "avg_signed_correlation": round(avg_signed_corr, 6),
            "resonant_tfs": resonant_tfs,
            "lagged_tfs": lagged_tfs,
            "dissonant_tfs": dissonant_tfs,
            "pair_correlations": pair_correlations,
            "pair_states": pair_states,
            "lag_detection": lag_detection,
            "pair_xcorr_peak": pair_xcorr_peak,
            "expected_amplification": expected_amplification,
            "technical_risks": self._dedupe_risks(technical_risks),
            "method": "cross_correlation_multi_tf",
            "valid": True,
            "window_size": self.corr_window,
            "max_lag": self.max_lag,
            "thresholds": {
                "resonant": self.resonant_threshold,
                "lagged": self.lagged_threshold,
                "dissonant": self.dissonant_threshold,
            },
        }

    def classify_resonance(self, corr_values: Sequence[float], lag_detection: Optional[Mapping[str, int]] = None) -> str:
        """
        Classify global resonance state from correlation values.

        Uses positive signed correlations because B7 looks for same-direction
        vibration between adjacent TFs. Inverse movement remains visible through
        avg_signed_correlation and pair_correlations, but is not RESONANT.
        """
        values = np.asarray(list(corr_values), dtype=float)
        values = values[np.isfinite(values)]
        if values.size == 0:
            return SILENT

        avg_corr = float(np.mean(np.maximum(values, 0.0)))
        lags = list((lag_detection or {}).values())
        lag_pressure = bool(lags and np.mean([abs(int(lag)) for lag in lags]) >= 2.0)

        if avg_corr >= self.resonant_threshold and not lag_pressure:
            return RESONANT
        if avg_corr >= self.lagged_threshold:
            return LAGGED
        if avg_corr >= self.dissonant_threshold:
            return DISSONANT
        return SILENT

    def assess_technical_risks(self, correlations: Mapping[str, float]) -> List[str]:
        """Return technical risks from pair correlation map."""
        risks: List[str] = []
        finite_values = [float(v) for v in correlations.values() if np.isfinite(float(v))]
        if not finite_values:
            return [INSUFFICIENT_DATA]

        if float(np.std(finite_values)) > 0.35:
            risks.append(CORRELATION_UNSTABLE)
        if any(abs(v) < self.dissonant_threshold for v in finite_values):
            risks.append(SILENT_HTF)
        return self._dedupe_risks(risks)

    def _select_available_pairs(self, inputs: Mapping[int, np.ndarray]) -> List[Tuple[int, int]]:
        available = set(inputs.keys())
        return [(a, b) for a, b in self.DEFAULT_ADJACENT_PAIRS if a in available and b in available]

    def _classify_pair(self, corr: float, lag_bars: int) -> str:
        corr_pos = max(0.0, float(corr))
        abs_lag = abs(int(lag_bars))
        if corr_pos >= self.resonant_threshold and abs_lag < self.thresholds.high_lag_bars:
            return RESONANT
        if corr_pos >= self.lagged_threshold:
            return LAGGED
        if corr_pos >= self.dissonant_threshold:
            return DISSONANT
        return SILENT

    def _detect_lag_with_peak(self, s1: np.ndarray, s2: np.ndarray, max_lag: int) -> Dict[str, float]:
        best_lag = 0
        best_corr = -np.inf

        for lag in range(-max_lag, max_lag + 1):
            if lag < 0:
                a = s1[-lag:]
                b = s2[: len(a)]
            elif lag > 0:
                a = s1[: len(s1) - lag]
                b = s2[lag:]
            else:
                a = s1
                b = s2

            if len(a) < 3 or len(b) < 3:
                continue

            corr = float(np.mean(a * b))
            if abs(corr) > abs(best_corr) if np.isfinite(best_corr) else True:
                best_corr = corr
                best_lag = lag

        if not np.isfinite(best_corr):
            best_corr = 0.0
            best_lag = 0

        return {"lag_bars": int(best_lag), "xcorr_peak": float(best_corr)}

    def _prepare_pair(self, series1: Sequence[float], series2: Sequence[float]) -> Tuple[np.ndarray, np.ndarray]:
        s1 = self._to_float_array(series1)
        s2 = self._to_float_array(series2)
        n = min(len(s1), len(s2), self.corr_window)
        if n <= 0:
            return np.asarray([], dtype=float), np.asarray([], dtype=float)

        s1 = s1[-n:]
        s2 = s2[-n:]
        finite = np.isfinite(s1) & np.isfinite(s2)
        return s1[finite], s2[finite]

    @staticmethod
    def _to_float_array(series: Sequence[float]) -> np.ndarray:
        arr = np.asarray(series, dtype=float).reshape(-1)
        return arr[np.isfinite(arr)]

    @staticmethod
    def _zscore(series: np.ndarray) -> np.ndarray:
        std = float(np.std(series))
        return (series - float(np.mean(series))) / (std + 1e-10)

    @staticmethod
    def _pair_key(tf_low: int, tf_high: int) -> str:
        return f"({int(tf_low)}, {int(tf_high)})"

    @staticmethod
    def _dedupe_risks(risks: Sequence[str]) -> List[str]:
        seen = set()
        clean: List[str] = []
        for risk in risks:
            if not risk or risk in seen:
                continue
            seen.add(risk)
            clean.append(risk)
        return clean

    def _invalid_multi_tf_result(
        self,
        symbol: str,
        timestamp: str,
        reason: str,
        clean_inputs: Mapping[int, np.ndarray],
        pair_correlations: Optional[MutableMapping[str, float]] = None,
        lag_detection: Optional[MutableMapping[str, int]] = None,
        pair_states: Optional[MutableMapping[str, str]] = None,
    ) -> Dict[str, object]:
        return {
            "timestamp": timestamp,
            "symbol": symbol,
            "resonance_state": SILENT,
            "resonance_score": 0.0,
            "avg_signed_correlation": 0.0,
            "resonant_tfs": [],
            "lagged_tfs": [],
            "dissonant_tfs": sorted(clean_inputs.keys()),
            "pair_correlations": dict(pair_correlations or {}),
            "pair_states": dict(pair_states or {}),
            "lag_detection": dict(lag_detection or {}),
            "pair_xcorr_peak": {},
            "expected_amplification": False,
            "technical_risks": [reason],
            "method": "cross_correlation_multi_tf",
            "valid": False,
            "window_size": self.corr_window,
            "max_lag": self.max_lag,
            "thresholds": {
                "resonant": self.resonant_threshold,
                "lagged": self.lagged_threshold,
                "dissonant": self.dissonant_threshold,
            },
        }
