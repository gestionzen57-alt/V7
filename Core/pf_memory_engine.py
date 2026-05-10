"""PowerFlow V7.2 — B6 Memory Engine V1.

Behavioral pattern indexing over alert queue JSON.
No prediction. Only observed frequency context. No DB writes.
"""
from __future__ import annotations

import hashlib
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "MemoryEngineV1PatternIndexing"
METHOD = "behavioral_pattern_memory"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_alert_list(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        for key in ("alerts", "queue", "items", "events", "data"):
            value = payload.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        # Single alert dict fallback.
        if "alert_type" in payload:
            return [payload]
    return []


def load_queue(queue_path: Optional[str]) -> Tuple[List[Dict[str, Any]], List[str]]:
    risks: List[str] = []
    if not queue_path:
        candidates = [
            Path("output/behavioral_alert_queue.json"),
            Path("Core/output/behavioral_alert_queue.json"),
            Path("behavioral_alert_queue.json"),
        ]
        found = next((p for p in candidates if p.exists()), None)
        if found is None:
            return [], ["NO_ALERTS_IN_QUEUE"]
        queue_path = str(found)

    path = Path(queue_path)
    if not path.exists():
        return [], ["NO_ALERTS_IN_QUEUE"]

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        alerts = _as_alert_list(payload)
        if not alerts:
            risks.append("NO_ALERTS_IN_QUEUE")
        return alerts, risks
    except Exception as exc:
        return [], ["QUEUE_READ_ERROR", str(exc)]


class MemoryEngine:
    def __init__(self, queue_path: Optional[str] = None, alerts: Optional[List[Dict[str, Any]]] = None):
        if alerts is not None:
            self.queue = alerts
            self.load_risks: List[str] = []
        else:
            self.queue, self.load_risks = load_queue(queue_path)
        self.index: DefaultDict[int, List[Dict[str, Any]]] = defaultdict(list)
        self._build_index()

    def _pattern_tuple(self, alert: Dict[str, Any]) -> Tuple[str, str, str, str, str, str]:
        return (
            str(alert.get("alert_type", "UNKNOWN")),
            str(alert.get("regime_context", {}).get("regime", alert.get("regime", "UNKNOWN"))),
            str(alert.get("session_context", {}).get("session", alert.get("session", "UNKNOWN"))),
            str(alert.get("EIE_state", alert.get("eie_state", alert.get("elastic_state", "NEUTRAL")))),
            str(alert.get("B4_state", alert.get("b4_state", alert.get("cycle_state", "NEUTRAL")))),
            str(alert.get("B5_direction", alert.get("b5_direction", alert.get("direction", "NEUTRAL")))),
        )

    def _pattern_hash(self, pattern_tuple: Sequence[str]) -> int:
        joined = json.dumps(list(pattern_tuple), ensure_ascii=False, separators=(",", ":"))
        digest = hashlib.blake2b(joined.encode("utf-8"), digest_size=8).hexdigest()
        return int(digest, 16)

    def _build_index(self) -> None:
        for alert in self.queue:
            pattern = self._pattern_tuple(alert)
            ph = self._pattern_hash(pattern)
            self.index[ph].append(alert)

    def _compute_distribution(self, alerts: Sequence[Dict[str, Any]]) -> Dict[str, float]:
        if not alerts:
            return {}
        counts = Counter(str(a.get("outcome", "UNKNOWN")) for a in alerts)
        total = sum(counts.values()) or 1
        return {k: round(v / total, 4) for k, v in sorted(counts.items())}

    def _median_duration(self, alerts: Sequence[Dict[str, Any]]) -> Optional[float]:
        values: List[float] = []
        for a in alerts:
            for key in ("bars_to_move", "duration_bars", "median_bars_to_move", "bars_until_outcome"):
                value = a.get(key)
                if isinstance(value, (int, float)):
                    values.append(float(value))
                    break
        if not values:
            return None
        return float(statistics.median(values))

    def _assess_risks(self, alerts: Sequence[Dict[str, Any]]) -> List[str]:
        risks = list(self.load_risks)
        if len(alerts) == 0:
            risks.append("NO_HISTORICAL_DATA")
        if len(alerts) < 5:
            risks.append("SMALL_SAMPLE_SIZE")
        return sorted(set(risks))

    def query_pattern(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        pattern = self._pattern_tuple(alert)
        ph = self._pattern_hash(pattern)
        similar = self.index.get(ph, [])
        return {
            "timestamp": utc_now_iso(),
            "pattern": {
                "alert_type": pattern[0],
                "regime": pattern[1],
                "session": pattern[2],
                "eie_state": pattern[3],
                "b4_state": pattern[4],
                "b5_direction": pattern[5],
            },
            "pattern_tuple": list(pattern),
            "pattern_hash": ph,
            "historical_context": {
                "occurrences": len(similar),
                "outcomes": [str(a.get("outcome", "UNKNOWN")) for a in similar],
                "outcome_distribution": self._compute_distribution(similar),
                "median_bars_to_move": self._median_duration(similar),
                "sample_size": len(similar),
            },
            "technical_risks": self._assess_risks(similar),
            "method": METHOD,
            "version": VERSION,
            "valid": True,
        }

    def query_last(self, limit: int = 5) -> List[Dict[str, Any]]:
        if not self.queue:
            dummy = {
                "alert_type": "UNKNOWN",
                "regime_context": {"regime": "UNKNOWN"},
                "session_context": {"session": "UNKNOWN"},
                "EIE_state": "NEUTRAL",
                "B4_state": "NEUTRAL",
                "B5_direction": "NEUTRAL",
            }
            return [self.query_pattern(dummy)]
        return [self.query_pattern(a) for a in self.queue[-max(1, int(limit)):]]


def build_self_test_alerts() -> List[Dict[str, Any]]:
    base = {
        "alert_type": "FIRST_DETACHMENT_MICRO",
        "regime_context": {"regime": "COMPRESSION"},
        "session_context": {"session": "LONDON"},
        "EIE_state": "ELASTIC_IN_EXTREME",
        "B4_state": "CYCLE_COMPRESSING",
        "B5_direction": "DIVERGENT",
    }
    alerts: List[Dict[str, Any]] = []
    outcomes = ["RELEASE_CONFIRMED", "RELEASE_CONFIRMED", "RELEASE_CONFIRMED", "REJECTION", "RELEASE_CONFIRMED", "REJECTION", "RELEASE_CONFIRMED"]
    bars = [9, 11, 13, 18, 12, 21, 14]
    for i, outcome in enumerate(outcomes):
        item = dict(base)
        item["timestamp"] = f"2026-05-10T00:{i:02d}:00Z"
        item["outcome"] = outcome
        item["bars_to_move"] = bars[i]
        alerts.append(item)
    # Add a different pattern to verify indexing isolation.
    other = dict(base)
    other["B4_state"] = "CYCLE_STABLE"
    other["outcome"] = "UNKNOWN"
    alerts.append(other)
    return alerts


def write_json(path: str, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
