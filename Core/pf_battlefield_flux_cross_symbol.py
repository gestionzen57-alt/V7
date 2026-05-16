"""
T009 Phase 2C.3 - Battlefield Cross-Symbol Coalition Detection

Standalone multi-symbol battlefield perception layer.

Design goals:
- Combine BattlefieldFlux per-symbol states.
- Add pair driver context via PairDriverAnalyzer (Phase 2C.1).
- Add data visibility qualification via B8DataVisibilityChecker (Phase 2C.2).
- Keep this module read-only: no write to powerflow.db.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


try:
    from pf_battlefield_flux import BattlefieldFlux
except Exception:  # pragma: no cover - compatibility fallback for isolated tests
    class BattlefieldFlux:  # type: ignore
        def compute_state(self, symbol: str, lookback_min: int = 30) -> Dict[str, Any]:
            return {
                "symbol": symbol,
                "events": [],
                "tick_count": 0,
                "source_mode": "UNKNOWN",
                "data_visibility": "BLIND",
            }


try:
    from pf_pair_driver_context import PairDriverAnalyzer
except Exception:  # pragma: no cover - compatibility fallback if Phase 2C.1 absent
    class PairDriverAnalyzer:  # type: ignore
        def analyze_pair_driver(
            self,
            base_force: float,
            quote_force: float,
            base_delta: float,
            quote_delta: float,
        ) -> Dict[str, Any]:
            pressure = base_force - quote_force
            momentum = base_delta - quote_delta
            if pressure > 0.30:
                driver = "BASE_OUTRUNS_QUOTE"
                label = f"Base surperforme cotation (pression {pressure:.2f})"
            elif pressure < -0.30:
                driver = "QUOTE_OUTRUNS_BASE"
                label = f"Cotation surperforme base (pression {pressure:.2f})"
            else:
                driver = "MIXED_DRIVER"
                label = "Driver mixte ou peu clair"
            total = max(base_force + quote_force, 1.0)
            return {
                "pair_pressure": round(pressure, 4),
                "pair_momentum": round(momentum, 4),
                "driver_type": driver,
                "driver_label_fr": label,
                "base_contribution": round(base_force / total, 2),
                "quote_contribution": round(quote_force / total, 2),
                "confidence": round(min(abs(pressure), 1.0), 2),
            }


try:
    from pf_b8_data_visibility import B8DataVisibilityChecker
except Exception:  # pragma: no cover - compatibility fallback if Phase 2C.2 absent
    class B8DataVisibilityChecker:  # type: ignore
        """Minimal compatibility checker until Phase 2C.2 is present."""

        def __init__(self, db_path: Optional[str] = None):
            self.db_path = db_path

        def check_symbol_visibility(
            self,
            symbol: str,
            db_path: Optional[str] = None,
        ) -> Dict[str, Any]:
            symbol = (symbol or "").upper()
            if symbol == "USDJPY":
                return {
                    "symbol": symbol,
                    "coverage_state": "THIN",
                    "role_allowed": "CONTEXT_ONLY",
                    "visibility_quality": 0.50,
                    "technical_risks": ["THIN_SYMBOL_CONTEXT_ONLY"],
                }
            return {
                "symbol": symbol,
                "coverage_state": "FULL",
                "role_allowed": "PRIMARY",
                "visibility_quality": 1.0,
                "technical_risks": [],
            }


class CrossSymbolCoalitionDetector:
    """
    Detect multi-symbol battlefield coalitions.

    Revised doctrine:
    - Cross-symbol detection is not a simple directional validation.
    - Each pair needs a base/quote driver reading.
    - Data visibility limits must qualify role and confidence.
    - THIN symbols can support context, but should not drive PRIMARY verdicts.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        self.bf = BattlefieldFlux()
        self.driver_analyzer = PairDriverAnalyzer()
        self.visibility_checker = B8DataVisibilityChecker(db_path)
        self.states: Dict[str, Dict[str, Any]] = {}

    def detect_coalition(
        self,
        symbols: List[str],
        lookback_min: int = 30,
    ) -> Dict[str, Any]:
        """Detect coalition state across multiple symbols."""
        normalized_symbols = self._normalize_symbols(symbols)
        if len(normalized_symbols) < 2:
            return self._empty_coalition_state(normalized_symbols)

        self.states = {}
        for symbol in normalized_symbols:
            self.states[symbol] = self._safe_compute_state(symbol, lookback_min)

        visibility: Dict[str, Dict[str, Any]] = {}
        for symbol in normalized_symbols:
            visibility[symbol] = self._safe_visibility(symbol)

        pair_drivers = self._compute_pair_drivers(normalized_symbols)
        leadership = self._identify_leader_follower(normalized_symbols, visibility)
        convergence = self._detect_convergence_zones(normalized_symbols)
        divergence = self._detect_divergence_zones(normalized_symbols)
        coalition_strength, conf_factors = self._score_coalition_strength(
            leadership,
            convergence,
            divergence,
            visibility,
            pair_drivers,
        )

        confidence = round(coalition_strength * conf_factors.get("visibility_quality", 1.0), 2)

        return {
            "coalition_detected": coalition_strength >= 0.60,
            "coalition_strength": round(coalition_strength, 2),
            "leader": leadership.get("leader", "MIXED"),
            "follower": leadership.get("follower", []),
            "leadership": leadership,
            "pair_drivers": pair_drivers,
            "convergence_zones": convergence,
            "divergence_zones": divergence,
            "data_visibility": {
                symbol: {
                    "coverage_state": visibility.get(symbol, {}).get("coverage_state", "UNKNOWN"),
                    "role_allowed": visibility.get(symbol, {}).get("role_allowed", "UNKNOWN"),
                    "visibility_quality": visibility.get(symbol, {}).get("visibility_quality", 0.0),
                    "technical_risks": visibility.get(symbol, {}).get("technical_risks", []),
                }
                for symbol in normalized_symbols
            },
            "confidence": confidence,
            "confidence_factors": conf_factors,
            "timestamp": self._utc_now(),
            "symbols_analyzed": normalized_symbols,
        }

    def _safe_compute_state(self, symbol: str, lookback_min: int) -> Dict[str, Any]:
        try:
            state = self.bf.compute_state(symbol=symbol, lookback_min=lookback_min)
            if not isinstance(state, dict):
                raise TypeError("BattlefieldFlux.compute_state returned non-dict")
            state.setdefault("symbol", symbol)
            state.setdefault("events", [])
            return state
        except Exception as exc:
            return {
                "symbol": symbol,
                "events": [],
                "source_mode": "UNKNOWN",
                "data_visibility": "BLIND",
                "technical_risks": [f"BATTLEFIELD_STATE_ERROR:{type(exc).__name__}"],
            }

    def _safe_visibility(self, symbol: str) -> Dict[str, Any]:
        try:
            vis = self.visibility_checker.check_symbol_visibility(symbol, self.db_path)
            if not isinstance(vis, dict):
                raise TypeError("B8DataVisibilityChecker returned non-dict")
            return {
                "symbol": symbol,
                "coverage_state": vis.get("coverage_state", "UNKNOWN"),
                "role_allowed": vis.get("role_allowed", "PRIMARY"),
                "visibility_quality": float(vis.get("visibility_quality", self._visibility_quality_from_role(vis.get("role_allowed")))),
                "technical_risks": list(vis.get("technical_risks", [])),
            }
        except Exception as exc:
            return {
                "symbol": symbol,
                "coverage_state": "UNKNOWN",
                "role_allowed": "CONTEXT_ONLY",
                "visibility_quality": 0.35,
                "technical_risks": [f"VISIBILITY_CHECK_ERROR:{type(exc).__name__}"],
            }

    def _compute_pair_drivers(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """Compute pair driver context for each symbol."""
        pair_drivers: Dict[str, Dict[str, Any]] = {}

        for symbol in symbols:
            base, quote = self._split_symbol(symbol)
            state = self.states.get(symbol, {})
            events = state.get("events", []) or []

            base_force = self._estimate_base_force(events)
            quote_force = self._estimate_quote_force(events)
            base_delta = self._estimate_base_delta(events)
            quote_delta = self._estimate_quote_delta(events)

            driver = self.driver_analyzer.analyze_pair_driver(
                base_force=base_force,
                quote_force=quote_force,
                base_delta=base_delta,
                quote_delta=quote_delta,
            )

            pair_drivers[symbol] = {
                "base": base,
                "quote": quote,
                "base_force": round(base_force, 2),
                "quote_force": round(quote_force, 2),
                "base_delta": round(base_delta, 4),
                "quote_delta": round(quote_delta, 4),
                "driver_type": driver.get("driver_type", "MIXED_DRIVER"),
                "driver_label_fr": driver.get("driver_label_fr", "Driver mixte ou peu clair"),
                "pair_pressure": driver.get("pair_pressure", 0.0),
                "pair_momentum": driver.get("pair_momentum", 0.0),
                "confidence": driver.get("confidence", 0.0),
            }

        return pair_drivers

    def _estimate_base_force(self, events: List[Dict[str, Any]]) -> float:
        if not events:
            return 0.0
        values = []
        for event in events:
            scores = event.get("scores", {}) if isinstance(event.get("scores"), dict) else {}
            values.append(float(event.get("battle_score", scores.get("battle_score", 0.0)) or 0.0))
        return min(max(sum(values) / len(values), 0.0), 1.0)

    def _estimate_quote_force(self, events: List[Dict[str, Any]]) -> float:
        if not events:
            return 0.0
        values = []
        for event in events:
            scores = event.get("scores", {}) if isinstance(event.get("scores"), dict) else {}
            values.append(float(event.get("absorption_score", scores.get("absorption_score", 0.0)) or 0.0))
        return min(max(sum(values) / len(values), 0.0), 1.0)

    def _estimate_base_delta(self, events: List[Dict[str, Any]]) -> float:
        if len(events) < 2:
            return 0.0
        scores = [float(event.get("battle_score", 0.0) or 0.0) for event in events]
        return scores[-1] - scores[0]

    def _estimate_quote_delta(self, events: List[Dict[str, Any]]) -> float:
        if len(events) < 2:
            return 0.0
        scores = [float(event.get("absorption_score", 0.0) or 0.0) for event in events]
        return scores[-1] - scores[0]

    def _identify_leader_follower(
        self,
        symbols: List[str],
        visibility: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Identify leader currency while respecting data role qualification."""
        if not symbols:
            return {"leader": "MIXED", "follower": [], "leader_strength": 0.0, "confidence": 0.0}

        currencies = self._extract_currencies(symbols)
        currency_scores: Dict[str, List[float]] = {currency: [] for currency in currencies}

        for symbol in symbols:
            base, quote = self._split_symbol(symbol)
            state = self.states.get(symbol, {})
            events = state.get("events", []) or []
            role = visibility.get(symbol, {}).get("role_allowed", "PRIMARY")
            role_weight = self._role_weight(role)
            if role_weight <= 0.0:
                continue

            base_force = self._estimate_base_force(events)
            quote_force = self._estimate_quote_force(events)

            if base in currency_scores:
                currency_scores[base].append(base_force * role_weight)
            if quote in currency_scores:
                currency_scores[quote].append(quote_force * role_weight)

        currency_avg = {
            currency: (sum(values) / len(values) if values else 0.0)
            for currency, values in currency_scores.items()
        }

        sorted_currencies = sorted(currency_avg.items(), key=lambda item: item[1], reverse=True)
        if not sorted_currencies or sorted_currencies[0][1] <= 0:
            return {
                "leader": "MIXED",
                "follower": [],
                "leader_strength": 0.0,
                "follower_strength": 0.0,
                "confidence": 0.0,
                "currency_scores": currency_avg,
            }

        leader, leader_strength = sorted_currencies[0]
        followers = [currency for currency, _ in sorted_currencies[1:]]
        follower_strength = (
            sum(score for _, score in sorted_currencies[1:]) / max(len(sorted_currencies) - 1, 1)
        )
        confidence = max(0.0, min(1.0, leader_strength - follower_strength))

        return {
            "leader": leader,
            "follower": followers,
            "leader_strength": round(leader_strength, 2),
            "follower_strength": round(follower_strength, 2),
            "confidence": round(confidence, 2),
            "currency_scores": {k: round(v, 2) for k, v in currency_avg.items()},
        }

    def _detect_convergence_zones(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Detect same battlefield event type appearing across multiple symbols."""
        grouped: Dict[str, set] = {}
        strengths: Dict[str, List[float]] = {}

        for symbol in symbols:
            events = self.states.get(symbol, {}).get("events", []) or []
            for event in events:
                event_type = event.get("event_type", "UNKNOWN")
                grouped.setdefault(event_type, set()).add(symbol)
                strengths.setdefault(event_type, []).append(self._event_strength(event))

        convergence = []
        for event_type, symbol_set in grouped.items():
            if len(symbol_set) >= 2:
                avg_strength = sum(strengths.get(event_type, [0.0])) / max(len(strengths.get(event_type, [])), 1)
                convergence.append({
                    "event_type": event_type,
                    "symbols": sorted(symbol_set),
                    "count": len(symbol_set),
                    "strength": round(min(1.0, len(symbol_set) / max(len(symbols), 1)), 2),
                    "avg_event_strength": round(avg_strength, 2),
                })

        return sorted(convergence, key=lambda item: item["strength"], reverse=True)

    def _detect_divergence_zones(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """Detect primary event type disagreement across symbols."""
        event_map: Dict[str, str] = {}
        for symbol in symbols:
            events = self.states.get(symbol, {}).get("events", []) or []
            if events:
                event_map[symbol] = events[0].get("event_type", "UNKNOWN")

        unique_types = sorted(set(event_map.values()))
        if len(unique_types) <= 1:
            return []

        return [{
            "symbols": sorted(event_map.keys()),
            "event_types": unique_types,
            "strength": round(len(unique_types) / max(len(symbols), 1), 2),
        }]

    def _score_coalition_strength(
        self,
        leadership: Dict[str, Any],
        convergence: List[Dict[str, Any]],
        divergence: List[Dict[str, Any]],
        visibility: Dict[str, Dict[str, Any]],
        pair_drivers: Dict[str, Dict[str, Any]],
    ) -> Tuple[float, Dict[str, float]]:
        """Score coalition strength, with visibility and driver clarity qualification."""
        leader_conf = float(leadership.get("confidence", 0.0) or 0.0)
        convergence_ratio = (
            sum(item.get("strength", 0.0) for item in convergence) / len(convergence)
            if convergence else 0.0
        )
        divergence_ratio = (
            sum(item.get("strength", 0.0) for item in divergence) / len(divergence)
            if divergence else 0.0
        )
        driver_clarity = (
            sum(float(item.get("confidence", 0.0) or 0.0) for item in pair_drivers.values()) / len(pair_drivers)
            if pair_drivers else 0.0
        )

        base_strength = (
            0.30 * leader_conf
            + 0.30 * convergence_ratio
            + 0.20 * max(0.0, 1.0 - divergence_ratio)
            + 0.20 * driver_clarity
        )

        visibility_quality = self._visibility_quality(visibility)
        if visibility_quality <= 0.30:
            qualified = base_strength * 0.50
        else:
            qualified = base_strength * visibility_quality

        confidence_factors = {
            "base_coalition_strength": round(base_strength, 2),
            "visibility_quality": round(visibility_quality, 2),
            "event_alignment": round(convergence_ratio, 2),
            "divergence_resistance": round(max(0.0, 1.0 - divergence_ratio), 2),
            "driver_clarity": round(driver_clarity, 2),
        }
        return min(max(round(qualified, 2), 0.0), 1.0), confidence_factors

    def _event_strength(self, event: Dict[str, Any]) -> float:
        scores = event.get("scores", {}) if isinstance(event.get("scores"), dict) else {}
        battle = float(event.get("battle_score", scores.get("battle_score", 0.0)) or 0.0)
        absorption = float(event.get("absorption_score", scores.get("absorption_score", 0.0)) or 0.0)
        confidence = float(event.get("confidence", 0.0) or 0.0)
        return max(battle, absorption, confidence)

    def _visibility_quality(self, visibility: Dict[str, Dict[str, Any]]) -> float:
        if not visibility:
            return 0.0
        values = []
        for vis in visibility.values():
            if "visibility_quality" in vis:
                values.append(float(vis.get("visibility_quality", 0.0) or 0.0))
            else:
                values.append(self._visibility_quality_from_role(vis.get("role_allowed")))
        return max(0.0, min(1.0, sum(values) / len(values)))

    def _visibility_quality_from_role(self, role: Optional[str]) -> float:
        if role == "PRIMARY":
            return 1.0
        if role == "CONTEXT_ONLY":
            return 0.5
        if role == "EXCLUDED":
            return 0.0
        return 0.35

    def _role_weight(self, role: Optional[str]) -> float:
        if role == "PRIMARY":
            return 1.0
        if role == "CONTEXT_ONLY":
            return 0.5
        if role == "EXCLUDED":
            return 0.0
        return 0.35

    def _normalize_symbols(self, symbols: List[str]) -> List[str]:
        seen = set()
        normalized = []
        for symbol in symbols or []:
            item = str(symbol).strip().upper()
            if item and item not in seen:
                normalized.append(item)
                seen.add(item)
        return normalized

    def _extract_currencies(self, symbols: List[str]) -> List[str]:
        currencies = set()
        for symbol in symbols:
            base, quote = self._split_symbol(symbol)
            currencies.add(base)
            currencies.add(quote)
        return sorted(currencies)

    def _split_symbol(self, symbol: str) -> Tuple[str, str]:
        symbol = (symbol or "").upper().strip()
        if len(symbol) == 6:
            return symbol[:3], symbol[3:]
        return symbol, "USD"

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _empty_coalition_state(self, symbols: List[str]) -> Dict[str, Any]:
        return {
            "coalition_detected": False,
            "coalition_strength": 0.0,
            "leader": "MIXED",
            "follower": [],
            "leadership": {
                "leader": "MIXED",
                "follower": [],
                "leader_strength": 0.0,
                "confidence": 0.0,
            },
            "pair_drivers": {},
            "convergence_zones": [],
            "divergence_zones": [],
            "data_visibility": {},
            "confidence": 0.0,
            "confidence_factors": {},
            "timestamp": self._utc_now(),
            "symbols_analyzed": symbols or [],
        }
