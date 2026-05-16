# -*- coding: utf-8 -*-
"""
T009 Phase 2C.1 - Pair Driver Context

This module qualifies the driver of an FX pair as a relative base-vs-quote
relationship. It does not issue trading instructions. It translates force and
momentum readings into a compact driver context that can later enrich
Battlefield Flux packets, dashboard widgets, Telegram wording, and B8 context.

Core doctrine:
- A pair does not move only because its base currency moves.
- A pair moves when BASE outperforms QUOTE.
- A pair falls when QUOTE outperforms BASE.
- Absolute strength/weakness is useful only after relative pressure is computed.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict


@dataclass(frozen=True)
class PairDriverResult:
    """Result of pair driver analysis."""

    pair_pressure: float
    pair_momentum: float
    driver_type: str
    driver_label_fr: str
    base_contribution: float
    quote_contribution: float
    confidence: float


class PairDriverAnalyzer:
    """
    Analyze FX pair driver context.

    Metrics:
        pair_pressure = base_force - quote_force
            Positive: base stronger than quote.
            Negative: quote stronger than base.

        pair_momentum = base_delta - quote_delta
            Positive: base accelerates relative to quote.
            Negative: quote accelerates relative to base.

    The analyzer is intentionally pure and read-only:
    - no database write
    - no Telegram side effect
    - no engine mutation
    - no BUY/SELL semantics
    """

    PRESSURE_THRESHOLD = 0.30
    MOMENTUM_THRESHOLD = 0.10
    STRONG_FORCE_THRESHOLD = 0.70
    WEAK_FORCE_THRESHOLD = 0.20
    BOTH_UP_THRESHOLD = 0.60
    BOTH_DOWN_THRESHOLD = 0.40

    def analyze_pair_driver(
        self,
        base_force: float,
        quote_force: float,
        base_delta: float,
        quote_delta: float,
    ) -> Dict[str, Any]:
        """
        Analyze base-vs-quote driver.

        Args:
            base_force: Base currency force. Expected range 0.0-1.0.
            quote_force: Quote currency force. Expected range 0.0-1.0.
            base_delta: Base force momentum/change.
            quote_delta: Quote force momentum/change.

        Returns:
            Dict with pair_pressure, pair_momentum, driver_type,
            driver_label_fr, base_contribution, quote_contribution,
            confidence.
        """

        raw_base_force = self._safe_float(base_force)
        raw_quote_force = self._safe_float(quote_force)
        raw_base_delta = self._safe_float(base_delta)
        raw_quote_delta = self._safe_float(quote_delta)

        pair_pressure = raw_base_force - raw_quote_force
        pair_momentum = raw_base_delta - raw_quote_delta

        base_f = self._clamp(raw_base_force, 0.0, 1.0)
        quote_f = self._clamp(raw_quote_force, 0.0, 1.0)

        driver_type = self._classify_driver(
            base_f=base_f,
            quote_f=quote_f,
            pressure=pair_pressure,
            momentum=pair_momentum,
        )

        driver_label_fr = self._label_driver_fr(
            driver_type=driver_type,
            pressure=pair_pressure,
            momentum=pair_momentum,
            base_f=base_f,
            quote_f=quote_f,
        )

        total = base_f + quote_f
        if total <= 0.0:
            base_contribution = 0.0
            quote_contribution = 0.0
        else:
            base_contribution = base_f / total
            quote_contribution = quote_f / total

        confidence = self._confidence(
            pressure=pair_pressure,
            momentum=pair_momentum,
            driver_type=driver_type,
        )

        result = PairDriverResult(
            pair_pressure=round(pair_pressure, 4),
            pair_momentum=round(pair_momentum, 4),
            driver_type=driver_type,
            driver_label_fr=driver_label_fr,
            base_contribution=round(base_contribution, 2),
            quote_contribution=round(quote_contribution, 2),
            confidence=round(confidence, 2),
        )
        return asdict(result)

    def _classify_driver(
        self,
        base_f: float,
        quote_f: float,
        pressure: float,
        momentum: float,
    ) -> str:
        """
        Classify the pair driver.

        Driver types:
        - BASE_OUTRUNS_QUOTE
        - QUOTE_OUTRUNS_BASE
        - BASE_STRENGTH_DOMINANT
        - QUOTE_STRENGTH_DOMINANT
        - BASE_WEAKNESS_DOMINANT
        - QUOTE_WEAKNESS_DOMINANT
        - BOTH_UP_BASE_STRONGER
        - BOTH_UP_QUOTE_STRONGER
        - BOTH_DOWN_BASE_WEAKER
        - BOTH_DOWN_QUOTE_WEAKER
        - BASE_MOMENTUM_DOMINANT
        - QUOTE_MOMENTUM_DOMINANT
        - MIXED_DRIVER
        """

        pressure_threshold = self.PRESSURE_THRESHOLD
        momentum_threshold = self.MOMENTUM_THRESHOLD

        # Extreme weakness first. This catches cases where the pair is driven
        # less by absolute base power and more by the quote failing hard.
        if quote_f < self.WEAK_FORCE_THRESHOLD and base_f >= self.BOTH_UP_THRESHOLD:
            return "QUOTE_WEAKNESS_DOMINANT"
        if base_f < self.WEAK_FORCE_THRESHOLD and quote_f >= self.BOTH_UP_THRESHOLD:
            return "BASE_WEAKNESS_DOMINANT"

        # Clear both-up / both-down states are preserved as context instead of
        # being collapsed too early into generic outruns labels.
        if base_f > self.BOTH_UP_THRESHOLD and quote_f > self.BOTH_UP_THRESHOLD:
            if base_f >= quote_f:
                return "BOTH_UP_BASE_STRONGER"
            return "BOTH_UP_QUOTE_STRONGER"

        if base_f < self.BOTH_DOWN_THRESHOLD and quote_f < self.BOTH_DOWN_THRESHOLD:
            if base_f <= quote_f:
                return "BOTH_DOWN_BASE_WEAKER"
            return "BOTH_DOWN_QUOTE_WEAKER"

        # Relative pressure is the primary pair driver.
        if pressure > pressure_threshold:
            # Only call absolute dominance in an extreme and asymmetric case.
            if base_f >= 0.90 and quote_f <= 0.35:
                return "BASE_STRENGTH_DOMINANT"
            return "BASE_OUTRUNS_QUOTE"

        if pressure < -pressure_threshold:
            if quote_f >= 0.90 and base_f <= 0.35:
                return "QUOTE_STRENGTH_DOMINANT"
            return "QUOTE_OUTRUNS_BASE"

        # Momentum only dominates when force pressure is not clear.
        if momentum > momentum_threshold:
            return "BASE_MOMENTUM_DOMINANT"
        if momentum < -momentum_threshold:
            return "QUOTE_MOMENTUM_DOMINANT"

        if quote_f < self.WEAK_FORCE_THRESHOLD:
            return "QUOTE_WEAKNESS_DOMINANT"
        if base_f < self.WEAK_FORCE_THRESHOLD:
            return "BASE_WEAKNESS_DOMINANT"

        return "MIXED_DRIVER"

    def _label_driver_fr(
        self,
        driver_type: str,
        pressure: float,
        momentum: float,
        base_f: float,
        quote_f: float,
    ) -> str:
        """Generate trader-facing French label."""

        labels = {
            "BASE_OUTRUNS_QUOTE": f"Base surperforme cotation (pression {pressure:.2f})",
            "QUOTE_OUTRUNS_BASE": f"Cotation surperforme base (pression {pressure:.2f})",
            "BASE_STRENGTH_DOMINANT": "Base tres forte (dominance absolue)",
            "QUOTE_STRENGTH_DOMINANT": "Cotation tres forte (dominance absolue)",
            "BASE_WEAKNESS_DOMINANT": "Base tres faible (faiblesse dominante)",
            "QUOTE_WEAKNESS_DOMINANT": "Cotation tres faible (driver par faiblesse quote)",
            "BOTH_UP_BASE_STRONGER": "Les deux montent, base plus forte",
            "BOTH_UP_QUOTE_STRONGER": "Les deux montent, cotation plus forte",
            "BOTH_DOWN_BASE_WEAKER": "Les deux baissent, base plus faible",
            "BOTH_DOWN_QUOTE_WEAKER": "Les deux baissent, cotation plus faible",
            "BASE_MOMENTUM_DOMINANT": f"Base accelere relatif a cotation (momentum {momentum:.2f})",
            "QUOTE_MOMENTUM_DOMINANT": f"Cotation accelere relatif a base (momentum {momentum:.2f})",
            "MIXED_DRIVER": "Driver mixte ou peu clair",
        }
        return labels.get(driver_type, "Driver inconnu")

    def _confidence(self, pressure: float, momentum: float, driver_type: str) -> float:
        """
        Confidence proxy.

        Pressure is dominant. Momentum adds a small boost when pressure is weak.
        MIXED_DRIVER is deliberately capped to avoid false clarity.
        """

        pressure_component = min(1.0, abs(pressure))
        momentum_component = min(0.25, abs(momentum))
        confidence = pressure_component + momentum_component

        if driver_type == "MIXED_DRIVER":
            confidence = min(confidence, 0.25)

        return self._clamp(confidence, 0.0, 1.0)

    @staticmethod
    def _safe_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _clamp(value: float, low: float, high: float) -> float:
        return max(low, min(high, value))


__all__ = ["PairDriverAnalyzer", "PairDriverResult"]
