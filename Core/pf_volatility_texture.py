"""
pf_volatility_texture.py
B7+ Volatility Texture Engine — behavioral volatility nature classifier.

PowerFlow doctrine:
- Texture qualifies the nature of movement.
- Texture does not predict a trade.
- Texture does not filter alerts.
- Technical risks only.

Version: VolatilityTextureV0.1Standalone
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

ENGINE_VERSION = "VolatilityTextureV0.1Standalone"
EPSILON = 1e-9

TEXTURE_STRUCTURAL = "STRUCTURAL"
TEXTURE_NEWS_SPIKE = "NEWS_SPIKE"
TEXTURE_SESSION_FRICTION = "SESSION_FRICTION"
TEXTURE_MM_NOISE = "MM_NOISE"

SPREAD_WIDENING = "WIDENING"
SPREAD_STABLE = "STABLE"
SPREAD_TIGHTENING = "TIGHTENING"
SPREAD_TIGHT = "TIGHT"
SPREAD_UNKNOWN = "UNKNOWN"


@dataclass
class VolatilitySignature:
    """Compact volatility texture signature for alert enrichment."""

    texture_type: str
    micro_macro_ratio: float
    spread_behavior: str
    pattern_consistency: float
    confidence: float
    technical_risks: List[str]


class VolatilityTextureEngine:
    """
    Detect volatility texture from force series, optional spread data and session context.

    Inputs:
      - force_series: numeric force/price-like sequence.
      - spread_series: optional bid/ask spread sequence.
      - session_context: optional PowerFlow session block.

    Output:
      - volatility_texture context for behavioral alerts / cockpit.

    The engine is deliberately standalone. It uses numpy only and never writes to DB.
    """

    def __init__(
        self,
        window_micro: int = 5,
        window_macro: int = 20,
        min_bars: int = 8,
    ) -> None:
        self.window_micro = max(2, int(window_micro))
        self.window_macro = max(self.window_micro + 1, int(window_macro))
        self.min_bars = max(5, int(min_bars))

    @staticmethod
    def utc_now_iso() -> str:
        """Return UTC timestamp without microseconds."""
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @staticmethod
    def _to_float_array(values: Optional[Sequence[Any]]) -> np.ndarray:
        """Convert a sequence to a clean finite float array."""
        if values is None:
            return np.asarray([], dtype=float)
        cleaned: List[float] = []
        for value in values:
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue
            if math.isfinite(number):
                cleaned.append(number)
        return np.asarray(cleaned, dtype=float)

    @staticmethod
    def _round(value: float, ndigits: int = 6) -> float:
        if not math.isfinite(float(value)):
            return 0.0
        return round(float(value), ndigits)

    @staticmethod
    def _rolling_mean(series: np.ndarray, window: int) -> np.ndarray:
        if len(series) == 0:
            return np.asarray([], dtype=float)
        if len(series) < window:
            return np.asarray([float(np.mean(series))], dtype=float)
        kernel = np.ones(window, dtype=float) / float(window)
        return np.convolve(series, kernel, mode="valid")

    def calculate_micro_variance(self, force_series: Sequence[Any], window: Optional[int] = None) -> float:
        """
        High-frequency agitation proxy.

        Formula:
            micro_var = mean(abs(diff(force[-window:])))

        High value means local bar-to-bar agitation. Low value means smooth movement.
        """
        force = self._to_float_array(force_series)
        if len(force) < 2:
            return 0.0
        w = max(2, int(window or self.window_micro))
        segment = force[-min(len(force), w) :]
        diffs = np.diff(segment)
        return float(np.mean(np.abs(diffs))) if len(diffs) else 0.0

    def calculate_macro_variance(self, force_series: Sequence[Any], window: Optional[int] = None) -> float:
        """
        Low-frequency directional volatility proxy.

        Formula:
            macro_var = std(rolling_mean(force, window=window/4)) over last macro window.
        """
        force = self._to_float_array(force_series)
        if len(force) < 3:
            return 0.0
        w = max(3, int(window or self.window_macro))
        segment = force[-min(len(force), w) :]
        smooth_window = max(2, min(5, len(segment) // 2))
        smoothed = self._rolling_mean(segment, smooth_window)
        if len(smoothed) < 2:
            return 0.0
        return float(np.std(smoothed))

    @staticmethod
    def micro_macro_ratio(micro_var: float, macro_var: float) -> float:
        """Return micro/macro variance ratio with epsilon protection."""
        return float(micro_var) / (float(macro_var) + EPSILON)

    def calculate_directional_efficiency(self, force_series: Sequence[Any]) -> float:
        """
        Measure how much total movement converts into net direction.

        1.0 = one-way motion. 0.0 = full churn around the same level.
        """
        force = self._to_float_array(force_series)
        if len(force) < 2:
            return 0.0
        path = float(np.sum(np.abs(np.diff(force))))
        net = float(abs(force[-1] - force[0]))
        return max(0.0, min(1.0, net / (path + EPSILON)))

    def calculate_force_spike_score(self, force_series: Sequence[Any]) -> float:
        """
        Detect sudden shock in bar-to-bar force changes.

        score = max(abs(diff)) / median(abs(diff)). A high value means one shock bar.
        """
        force = self._to_float_array(force_series)
        if len(force) < 4:
            return 0.0
        diffs = np.abs(np.diff(force))
        if len(diffs) == 0:
            return 0.0
        baseline = float(np.median(diffs))
        max_diff = float(np.max(diffs))
        if baseline <= EPSILON:
            non_zero = diffs[diffs > EPSILON]
            if len(non_zero) == 0:
                return 0.0
            baseline = float(np.median(non_zero)) if len(non_zero) else EPSILON
        return max_diff / (baseline + EPSILON)

    def calculate_recent_expansion_score(self, force_series: Sequence[Any]) -> float:
        """Compare recent agitation to earlier agitation."""
        force = self._to_float_array(force_series)
        if len(force) < 8:
            return 1.0
        split = max(3, len(force) // 2)
        early = force[:split]
        late = force[split:]
        early_micro = self.calculate_micro_variance(early, window=min(self.window_micro, len(early)))
        late_micro = self.calculate_micro_variance(late, window=min(self.window_micro, len(late)))
        return late_micro / (early_micro + EPSILON)

    def analyze_spread_pattern(self, spread_series: Optional[Sequence[Any]], window: int = 10) -> Dict[str, Any]:
        """
        Analyze spread behavior.

        Returns:
          mean/std, spike flag and behavior label.
        """
        spread = self._to_float_array(spread_series)
        if len(spread) == 0:
            return {
                "mean": 0.0,
                "std": 0.0,
                "last": 0.0,
                "spike_detected": False,
                "behavior": SPREAD_UNKNOWN,
                "samples": 0,
            }

        w = max(3, min(int(window), len(spread)))
        recent = spread[-w:]
        previous = spread[:-w] if len(spread) > w else spread[: max(1, len(spread) // 2)]
        recent_mean = float(np.mean(recent))
        previous_mean = float(np.mean(previous)) if len(previous) else recent_mean
        spread_std = float(np.std(recent))
        last = float(recent[-1])

        baseline = float(np.median(spread)) if len(spread) else recent_mean
        max_spread = float(np.max(recent))
        spike_detected = bool(max_spread > baseline + 3.0 * (float(np.std(spread)) + EPSILON))
        if baseline > EPSILON and max_spread / baseline >= 1.8:
            spike_detected = True

        if recent_mean > previous_mean * 1.25 + EPSILON:
            behavior = SPREAD_WIDENING
        elif recent_mean < previous_mean * 0.75:
            behavior = SPREAD_TIGHTENING
        elif recent_mean <= 1.0 and spread_std <= 0.25:
            behavior = SPREAD_TIGHT
        else:
            behavior = SPREAD_STABLE

        return {
            "mean": self._round(recent_mean),
            "std": self._round(spread_std),
            "last": self._round(last),
            "spike_detected": bool(spike_detected),
            "behavior": behavior,
            "samples": int(len(spread)),
        }

    def calculate_pattern_consistency(self, force_series: Sequence[Any], window: int = 50) -> float:
        """
        Score 0..1 describing stability of the volatility pattern.

        Method:
          - split into chunks
          - calculate micro/macro ratio per chunk
          - low variance of chunk ratios => high consistency
        """
        force = self._to_float_array(force_series)
        if len(force) < self.min_bars:
            return 0.0

        segment = force[-min(len(force), max(self.min_bars, int(window))) :]
        chunk_count = min(5, max(2, len(segment) // max(3, self.window_micro)))
        chunks = [chunk for chunk in np.array_split(segment, chunk_count) if len(chunk) >= 3]
        if len(chunks) < 2:
            return 0.5

        ratios: List[float] = []
        for chunk in chunks:
            micro = self.calculate_micro_variance(chunk, window=min(self.window_micro, len(chunk)))
            macro = self.calculate_macro_variance(chunk, window=max(3, min(self.window_macro, len(chunk))))
            ratio = min(10.0, self.micro_macro_ratio(micro, macro))
            ratios.append(ratio)

        if len(ratios) < 2:
            return 0.5
        ratio_std = float(np.std(ratios))
        ratio_mean = float(np.mean(np.abs(ratios)))
        normalized = ratio_std / (ratio_mean + 1.0)
        consistency = 1.0 / (1.0 + normalized)
        return max(0.0, min(1.0, float(consistency)))

    def inject_session_context(
        self,
        texture_type: str,
        session_context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Qualify texture against session expectation."""
        ctx = dict(session_context or {})
        session = str(ctx.get("session", ctx.get("primary_session", "UNKNOWN"))).upper()
        phase = str(ctx.get("phase", ctx.get("session_phase", "UNKNOWN"))).upper()

        expected = "STRUCTURAL"
        expected_set = {TEXTURE_STRUCTURAL}
        if session in {"ASIAN", "DEAD", "DEAD_ZONE"}:
            expected = "MM_NOISE_OR_COMPRESSION"
            expected_set = {TEXTURE_MM_NOISE, TEXTURE_STRUCTURAL}
        elif "LONDON" in session and phase in {"IGNITION", "OPEN", "PRE_OPEN"}:
            expected = "SESSION_FRICTION_TO_STRUCTURAL"
            expected_set = {TEXTURE_SESSION_FRICTION, TEXTURE_STRUCTURAL}
        elif session in {"OVERLAP", "LONDON_NY_OVERLAP"}:
            expected = "STRUCTURAL_OR_NEWS_SPIKE"
            expected_set = {TEXTURE_STRUCTURAL, TEXTURE_NEWS_SPIKE, TEXTURE_SESSION_FRICTION}
        elif "NY" in session and phase in {"IGNITION", "OPEN"}:
            expected = "SESSION_FRICTION_OR_NEWS_SPIKE"
            expected_set = {TEXTURE_SESSION_FRICTION, TEXTURE_NEWS_SPIKE, TEXTURE_STRUCTURAL}

        alignment = bool(texture_type in expected_set)
        return {
            "session": session,
            "phase": phase,
            "expected_nature": expected,
            "alignment": alignment,
            "provided": bool(session_context),
        }

    def _detect_texture_type(
        self,
        ratio: float,
        spread_behavior: str,
        spread_spike_detected: bool,
        pattern_consistency: float,
        session_context: Optional[Dict[str, Any]],
        force_spike_score: float,
        directional_efficiency: float,
        recent_expansion_score: float,
    ) -> Tuple[str, float, List[str]]:
        """Classify the volatility texture and return technical risks."""
        risks: List[str] = []
        session = str((session_context or {}).get("session", (session_context or {}).get("primary_session", ""))).upper()
        phase = str((session_context or {}).get("phase", (session_context or {}).get("session_phase", ""))).upper()
        is_ignition = phase in {"IGNITION", "OPEN", "PRE_OPEN"}

        # Session transition should beat generic spike logic when the expansion is orderly.
        if is_ignition and recent_expansion_score >= 2.5 and directional_efficiency >= 0.35:
            confidence = 0.76 + min(0.14, (recent_expansion_score - 2.5) * 0.03)
            if spread_behavior == SPREAD_WIDENING:
                risks.append("SESSION_SPREAD_WIDENING")
                confidence -= 0.08
            return TEXTURE_SESSION_FRICTION, max(0.60, min(0.90, confidence)), risks

        # Sudden shock / news-like volatility. Spread widens if available, but force shock is enough.
        if force_spike_score >= 6.0 or spread_spike_detected:
            if spread_behavior == SPREAD_WIDENING or spread_spike_detected or pattern_consistency < 0.70:
                confidence = 0.80 + min(0.15, (force_spike_score - 6.0) * 0.01)
                if spread_behavior == SPREAD_UNKNOWN:
                    risks.append("NO_SPREAD_DATA_CONFIRMATION")
                    confidence -= 0.06
                if pattern_consistency > 0.85:
                    risks.append("PERSISTENT_SPIKE_PATTERN")
                    confidence -= 0.05
                return TEXTURE_NEWS_SPIKE, max(0.60, min(0.95, confidence)), risks

        # Market-maker agitation: path churns but net direction does not leave the zone.
        if directional_efficiency < 0.35 and ratio >= 1.20:
            confidence = 0.72 + min(0.18, (ratio - 1.2) * 0.05)
            if spread_behavior in {SPREAD_TIGHT, SPREAD_STABLE, SPREAD_UNKNOWN}:
                confidence += 0.05
            if pattern_consistency < 0.35:
                risks.append("LOW_PATTERN_CONSISTENCY")
                confidence -= 0.08
            return TEXTURE_MM_NOISE, max(0.55, min(0.92, confidence)), risks

        # Structural: direction is building or volatility is coherent enough.
        confidence = 0.70
        if directional_efficiency >= 0.65:
            confidence += 0.12
        if pattern_consistency >= 0.75:
            confidence += 0.08
        if spread_behavior in {SPREAD_STABLE, SPREAD_TIGHT, SPREAD_UNKNOWN}:
            confidence += 0.04
        if spread_behavior == SPREAD_WIDENING:
            risks.append("STRUCTURAL_WITH_SPREAD_WIDENING")
            confidence -= 0.10
        if pattern_consistency < 0.30:
            risks.append("LOW_PATTERN_CONSISTENCY")
            confidence -= 0.12
        if session in {"ASIAN", "DEAD", "DEAD_ZONE"} and ratio > 1.5:
            risks.append("ASIAN_TEXTURE_AMBIGUITY")
            confidence -= 0.06
        return TEXTURE_STRUCTURAL, max(0.50, min(0.94, confidence)), risks

    def analyze_texture(
        self,
        force_series: Sequence[Any],
        spread_series: Optional[Sequence[Any]] = None,
        session_context: Optional[Dict[str, Any]] = None,
        symbol: str = "GBPUSD",
        timeframe: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Analyze complete volatility texture."""
        force = self._to_float_array(force_series)
        timestamp = self.utc_now_iso()
        risks: List[str] = []

        if len(force) < self.min_bars:
            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "timestamp": timestamp,
                "engine_version": ENGINE_VERSION,
                "valid": False,
                "error": "INSUFFICIENT_FORCE_BARS",
                "technical_risks": ["INSUFFICIENT_FORCE_BARS"],
                "volatility_texture": {
                    "type": None,
                    "confidence": 0.0,
                    "micro_macro_ratio": 0.0,
                    "spread_behavior": SPREAD_UNKNOWN,
                    "pattern_consistency": 0.0,
                },
                "spread_context": self.analyze_spread_pattern(spread_series),
                "session_context": self.inject_session_context("UNKNOWN", session_context),
            }

        if float(np.std(force)) <= EPSILON:
            risks.append("FLAT_FORCE_SERIES")

        micro_var = self.calculate_micro_variance(force, self.window_micro)
        macro_var = self.calculate_macro_variance(force, self.window_macro)
        ratio = self.micro_macro_ratio(micro_var, macro_var)
        consistency = self.calculate_pattern_consistency(force, window=max(self.window_macro, min(50, len(force))))
        force_spike_score = self.calculate_force_spike_score(force)
        directional_efficiency = self.calculate_directional_efficiency(force)
        recent_expansion_score = self.calculate_recent_expansion_score(force)
        spread_context = self.analyze_spread_pattern(spread_series, window=10)

        if spread_context["behavior"] == SPREAD_UNKNOWN:
            risks.append("NO_SPREAD_DATA")
        if consistency < 0.30:
            risks.append("LOW_PATTERN_CONSISTENCY")

        texture_type, confidence, classifier_risks = self._detect_texture_type(
            ratio=ratio,
            spread_behavior=spread_context["behavior"],
            spread_spike_detected=bool(spread_context["spike_detected"]),
            pattern_consistency=consistency,
            session_context=session_context,
            force_spike_score=force_spike_score,
            directional_efficiency=directional_efficiency,
            recent_expansion_score=recent_expansion_score,
        )
        risks.extend(classifier_risks)

        session_block = self.inject_session_context(texture_type, session_context)
        if session_context and not session_block["alignment"]:
            risks.append("TEXTURE_SESSION_MISALIGNMENT")
        elif not session_context:
            risks.append("SESSION_CONTEXT_MISSING")

        # Deduplicate while preserving order.
        deduped_risks = list(dict.fromkeys(risks))

        signature = VolatilitySignature(
            texture_type=texture_type,
            micro_macro_ratio=self._round(ratio),
            spread_behavior=spread_context["behavior"],
            pattern_consistency=self._round(consistency),
            confidence=self._round(confidence),
            technical_risks=deduped_risks,
        )

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "timestamp": timestamp,
            "engine_version": ENGINE_VERSION,
            "valid": True,
            "error": None,
            "volatility_texture": {
                "type": signature.texture_type,
                "confidence": signature.confidence,
                "micro_macro_ratio": signature.micro_macro_ratio,
                "micro_variance": self._round(micro_var),
                "macro_variance": self._round(macro_var),
                "spread_behavior": signature.spread_behavior,
                "pattern_consistency": signature.pattern_consistency,
                "directional_efficiency": self._round(directional_efficiency),
                "force_spike_score": self._round(force_spike_score),
                "recent_expansion_score": self._round(recent_expansion_score),
                "technical_risks": deduped_risks,
            },
            "spread_context": spread_context,
            "session_context": session_block,
            "technical_risks": deduped_risks,
            "signature": asdict(signature),
        }


def qualify_signal_quality(
    alert: Dict[str, Any],
    regime_context: Optional[Dict[str, Any]] = None,
    fractal_context: Optional[Dict[str, Any]] = None,
    texture_context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Combine regime/fractal/texture into a non-decisional signal quality qualifier.

    This function qualifies technical signal quality. It does not decide or filter trades.
    """
    regime = regime_context or {}
    fractal = fractal_context or {}
    texture = texture_context or {}
    vt = texture.get("volatility_texture", texture)

    score = 0
    reasons: List[str] = []

    if float(regime.get("confidence", 0.0) or 0.0) >= 0.80:
        score += 1
        reasons.append("REGIME_CLEAR")
    if str(fractal.get("state", fractal.get("fractal_resonance", ""))).upper() == "RESONANT":
        score += 1
        reasons.append("FRACTAL_RESONANT")
    if vt.get("type") in {TEXTURE_STRUCTURAL, TEXTURE_SESSION_FRICTION}:
        score += 1
        reasons.append(f"TEXTURE_{vt.get('type')}")
    if float(vt.get("pattern_consistency", 0.0) or 0.0) >= 0.80:
        score += 1
        reasons.append("PATTERN_CONSISTENT")
    if vt.get("type") == TEXTURE_NEWS_SPIKE:
        score -= 1
        reasons.append("NEWS_SPIKE_TECHNICAL_RISK")
    if vt.get("type") == TEXTURE_MM_NOISE:
        score -= 1
        reasons.append("MM_NOISE_TECHNICAL_RISK")

    if score >= 3:
        quality = "HIGH"
    elif score >= 1:
        quality = "MEDIUM"
    else:
        quality = "LOW"

    return {
        "signal_quality": quality,
        "score": int(score),
        "justification": reasons,
        "amplification_expected": quality == "HIGH" and vt.get("type") == TEXTURE_STRUCTURAL,
        "technical_risks": list(vt.get("technical_risks", [])),
        "doctrine": "QUALIFY_ONLY_TRADER_DECIDES",
    }
