"""
pf_memory_engine.py
Memory Engine V1 — Pattern history indexing

PowerFlow role:
- index behavioral_alert_queue.json by behavioral pattern
- return historical occurrences and outcome frequencies
- never predict, never decide, only expose memory context
"""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, DefaultDict, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

PatternTuple = Tuple[str, str, str, str, str, str]
AlertDict = Dict[str, Any]


UNKNOWN = "UNKNOWN"
NEUTRAL = "NEUTRAL"
SMALL_SAMPLE_THRESHOLD = 5
INCOMPLETE_HISTORY_DAYS = 90


class MemoryEngine:
    """Index behavioral patterns and query historical outcomes.

    Pattern dimensions V1:
        alert_type, regime, session, EIE_state, B4_state, B5_direction

    Hash contract:
        deterministic unsigned 64-bit integer. Python's built-in hash() is not
        used because it is salted per process and would break stability tests.
    """

    def __init__(self, queue_path: str | Path = "output/behavioral_alert_queue.json"):
        self.module_dir = Path(__file__).resolve().parent
        self.project_root = self.module_dir.parent if self.module_dir.name.lower() == "core" else Path.cwd()
        self.queue_path = self._resolve_input_path(queue_path)
        self.queue_exists = self.queue_path.exists()
        self.queue = self._load_queue()
        self.index = self._build_index()

    def _resolve_input_path(self, path: str | Path) -> Path:
        """Resolve queue path from root or Core execution contexts.

        PowerFlow is often launched from either the repository root or from
        ``Core/``. In practice some workspaces are nested (for example
        ``.../IA/GPT/Core`` while ``output/`` may sit higher). This resolver
        therefore checks the direct candidates first, then walks upward from
        both the current working directory and this file location.
        """
        raw_path = Path(path)
        if raw_path.is_absolute():
            return raw_path

        candidates = [
            Path.cwd() / raw_path,
            self.project_root / raw_path,
            self.module_dir / raw_path,
            self.module_dir.parent / raw_path,
        ]

        search_bases = [Path.cwd(), self.module_dir, self.project_root]
        for base in search_bases:
            for parent in [base, *base.parents]:
                candidates.append(parent / raw_path)
                if raw_path.parts and raw_path.parts[0].lower() == "output":
                    candidates.append(parent / "output" / raw_path.name)

        seen = set()
        for candidate in candidates:
            candidate = candidate.resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.exists():
                return candidate

        # Default target when the queue does not exist yet.
        return (self.project_root / raw_path).resolve()

    def _load_queue(self) -> List[AlertDict]:
        """Load behavioral queue from JSON.

        Accepts either:
        - a direct list of alerts
        - a wrapper dict containing one of: alerts, queue, results, behavioral_alert_queue
        """
        try:
            if not self.queue_path.exists():
                return []
            with self.queue_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            return []

        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if isinstance(payload, dict):
            for key in ("behavioral_alert_queue", "alerts", "queue", "results"):
                value = payload.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]

        return []

    @staticmethod
    def _nested(alert: Mapping[str, Any], outer_key: str, inner_key: str, default: str) -> Any:
        container = alert.get(outer_key, {})
        if isinstance(container, Mapping):
            return container.get(inner_key, default)
        return default

    @staticmethod
    def _normalize_dimension(value: Any, default: str) -> str:
        if value is None:
            return default
        text = str(value).strip()
        if not text:
            return default
        return text.upper()

    def _pattern_tuple(self, alert: Mapping[str, Any]) -> PatternTuple:
        """Create normalized pattern tuple from the six V1 dimensions."""
        return (
            self._normalize_dimension(alert.get("alert_type"), UNKNOWN),
            self._normalize_dimension(self._nested(alert, "regime_context", "regime", UNKNOWN), UNKNOWN),
            self._normalize_dimension(self._nested(alert, "session_context", "session", UNKNOWN), UNKNOWN),
            self._normalize_dimension(alert.get("EIE_state"), NEUTRAL),
            self._normalize_dimension(alert.get("B4_state"), NEUTRAL),
            self._normalize_dimension(alert.get("B5_direction"), NEUTRAL),
        )

    def _pattern_hash(self, alert: Mapping[str, Any]) -> int:
        """Create deterministic unsigned 64-bit hash for an alert pattern."""
        pattern = self._pattern_tuple(alert)
        encoded = json.dumps(pattern, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
        digest = hashlib.blake2b(encoded, digest_size=8, person=b"PFMEMV1").digest()
        return int.from_bytes(digest, byteorder="big", signed=False)

    def _pattern_dict(self, alert: Mapping[str, Any]) -> Dict[str, str]:
        alert_type, regime, session, eie_state, b4_state, b5_direction = self._pattern_tuple(alert)
        return {
            "alert_type": alert_type,
            "regime": regime,
            "session": session,
            "eie_state": eie_state,
            "b4_state": b4_state,
            "b5_direction": b5_direction,
        }

    def _build_index(self) -> Dict[int, List[AlertDict]]:
        """Build index: pattern_hash -> list of alerts."""
        index: DefaultDict[int, List[AlertDict]] = defaultdict(list)
        for alert in self.queue:
            pattern_hash = self._pattern_hash(alert)
            index[pattern_hash].append(alert)
        return dict(index)

    def query_pattern(self, alert: Mapping[str, Any]) -> Dict[str, Any]:
        """Query historical context for a behavioral pattern."""
        pattern_hash = self._pattern_hash(alert)
        similar_alerts = self.index.get(pattern_hash, [])
        occurrences = len(similar_alerts)
        outcomes_data = self._analyze_outcomes(similar_alerts)
        risks = self._assess_technical_risks(occurrences, similar_alerts, current_alert=alert)

        return {
            "pattern": self._pattern_dict(alert),
            "pattern_hash": pattern_hash,
            "timestamp": self._timestamp_now(),
            "historical_context": {
                "occurrences": occurrences,
                "outcomes": outcomes_data["outcomes"],
                "outcome_distribution": outcomes_data["distribution"],
                "sample_size": occurrences,
                "median_bars_to_move": outcomes_data["median_bars"],
            },
            "technical_risks": risks,
        }

    def _analyze_outcomes(self, alerts: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
        """Analyze known outcome distribution.

        Alerts without outcome are ignored for outcome frequencies. They still
        count as occurrences/sample_size because the pattern did occur.
        """
        outcomes_bars: DefaultDict[str, List[int]] = defaultdict(list)

        for alert in alerts:
            outcome_raw = alert.get("outcome")
            if outcome_raw is None or str(outcome_raw).strip() == "":
                continue

            outcome = self._normalize_dimension(outcome_raw, UNKNOWN)
            bars = self._safe_int(alert.get("bars_to_move"), default=0)
            outcomes_bars[outcome].append(bars)

        known_outcome_total = sum(len(values) for values in outcomes_bars.values())
        outcomes = []

        for outcome in sorted(outcomes_bars.keys()):
            bars_list = outcomes_bars[outcome]
            outcomes.append(
                {
                    "outcome": outcome,
                    "count": len(bars_list),
                    "median_bars_to_move": self._median_int(bars_list),
                }
            )

        distribution = {
            outcome: round(len(bars_list) / known_outcome_total, 4) if known_outcome_total else 0
            for outcome, bars_list in sorted(outcomes_bars.items())
        }

        all_bars = [bars for bars_list in outcomes_bars.values() for bars in bars_list]

        return {
            "outcomes": outcomes,
            "distribution": distribution,
            "median_bars": self._median_int(all_bars),
        }

    def _assess_technical_risks(
        self,
        occurrences: int,
        alerts: Sequence[Mapping[str, Any]],
        current_alert: Optional[Mapping[str, Any]] = None,
    ) -> List[str]:
        """Assess statistical and memory-quality risks."""
        risks: List[str] = []

        if occurrences == 0:
            risks.append("NO_HISTORICAL_DATA")
        if occurrences < SMALL_SAMPLE_THRESHOLD:
            risks.append("SMALL_SAMPLE_SIZE")

        oldest_timestamp = self._oldest_timestamp(alerts)
        reference_timestamp = self._parse_timestamp((current_alert or {}).get("timestamp")) or self._latest_timestamp(alerts)

        if oldest_timestamp and reference_timestamp:
            if oldest_timestamp <= reference_timestamp - timedelta(days=INCOMPLETE_HISTORY_DAYS):
                risks.append("INCOMPLETE_HISTORY")

        return risks

    def batch_query(self, alerts_list: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
        """Query multiple alert patterns."""
        return [self.query_pattern(alert) for alert in alerts_list]

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            if value is None:
                return default
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _median_int(values: Sequence[int]) -> int:
        if not values:
            return 0
        return int(median(values))

    @staticmethod
    def _timestamp_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    @classmethod
    def _oldest_timestamp(cls, alerts: Sequence[Mapping[str, Any]]) -> Optional[datetime]:
        timestamps = [cls._parse_timestamp(alert.get("timestamp")) for alert in alerts]
        valid = [ts for ts in timestamps if ts is not None]
        return min(valid) if valid else None

    @classmethod
    def _latest_timestamp(cls, alerts: Sequence[Mapping[str, Any]]) -> Optional[datetime]:
        timestamps = [cls._parse_timestamp(alert.get("timestamp")) for alert in alerts]
        valid = [ts for ts in timestamps if ts is not None]
        return max(valid) if valid else None

    @staticmethod
    def _parse_timestamp(value: Any) -> Optional[datetime]:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        try:
            parsed = datetime.fromisoformat(text)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def diagnostics(self) -> Dict[str, Any]:
        """Return load/index diagnostics for runners and cockpit display."""
        return {
            "queue_path": str(self.queue_path),
            "queue_exists": bool(self.queue_exists),
            "queue_size": len(self.queue),
            "unique_patterns": len(self.index),
            "engine_version": "MemoryEngineV1.1-weekend-pathfix",
        }



def main() -> None:
    """Example usage."""
    engine = MemoryEngine("output/behavioral_alert_queue.json")
    test_alert = {
        "alert_type": "FIRST_DETACHMENT_MICRO",
        "regime_context": {"regime": "COMPRESSION"},
        "session_context": {"session": "LONDON"},
        "EIE_state": "ELASTIC_IN_EXTREME",
        "B4_state": "CYCLE_COMPRESSING",
        "B5_direction": "DIVERGENT",
    }
    result = engine.query_pattern(test_alert)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
