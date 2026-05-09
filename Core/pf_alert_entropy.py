#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
pf_alert_entropy.py

PowerFlow V7.1 — Alert Entropy Engine.

Role:
    Measure alert saturation / alert fatigue over a rolling window.

Doctrine:
    - No alert censorship.
    - No trading decision.
    - Technical saturation metrics only.
    - Data-in / metrics-out.
    - No DB write.
    - No cockpit dependency.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from math import log2
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


DEFAULT_TIMESTAMP_FIELDS: Tuple[str, ...] = (
    "timestamp",
    "created_at",
    "time",
    "generated_at_utc",
)

DEFAULT_TYPE_FIELDS: Tuple[str, ...] = (
    "alert_type",
    "type",
    "event_type",
)

DEFAULT_ENTITY_FIELDS: Tuple[str, ...] = (
    "currency",
    "devise",
    "symbol",
    "pair",
    "leader",
)


@dataclass(frozen=True)
class AlertEntropyConfig:
    window_minutes: int = 5
    burst_threshold_count: int = 3
    duplicate_ratio_threshold: float = 0.50
    timestamp_fields: Tuple[str, ...] = DEFAULT_TIMESTAMP_FIELDS
    type_fields: Tuple[str, ...] = DEFAULT_TYPE_FIELDS
    entity_fields: Tuple[str, ...] = DEFAULT_ENTITY_FIELDS


@dataclass(frozen=True)
class AlertEntropyMetrics:
    window_minutes: int
    window_start_utc: Optional[str]
    window_end_utc: Optional[str]
    total_alerts: int
    unique_alert_keys: int
    duplicate_alerts: int
    duplication_ratio: float
    shannon_entropy: float
    normalized_entropy: float
    burst_detected: bool
    burst_score: float
    top_duplicates: List[Dict[str, Any]]
    alert_type_distribution: Dict[str, int]
    entity_distribution: Dict[str, int]
    technical_risks: List[str]


def parse_utc_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, str):
        normalized = value.strip()
        if not normalized:
            return None

        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"

        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError:
            return None
    else:
        return None

    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def extract_first(alert: Dict[str, Any], fields: Sequence[str]) -> Optional[Any]:
    for field in fields:
        value = alert.get(field)
        if value is not None and value != "":
            return value
    return None


def extract_timestamp(
    alert: Dict[str, Any],
    timestamp_fields: Sequence[str] = DEFAULT_TIMESTAMP_FIELDS,
) -> Optional[datetime]:
    value = extract_first(alert, timestamp_fields)
    return parse_utc_timestamp(value)


def extract_alert_type(
    alert: Dict[str, Any],
    type_fields: Sequence[str] = DEFAULT_TYPE_FIELDS,
) -> str:
    value = extract_first(alert, type_fields)
    return str(value) if value is not None else "UNKNOWN_ALERT_TYPE"


def extract_entity(
    alert: Dict[str, Any],
    entity_fields: Sequence[str] = DEFAULT_ENTITY_FIELDS,
) -> str:
    value = extract_first(alert, entity_fields)

    if value is not None:
        return str(value)

    for nested_key in ("kinematics", "regime_context", "session_context", "payload"):
        nested = alert.get(nested_key)
        if isinstance(nested, dict):
            nested_value = extract_first(nested, entity_fields)
            if nested_value is not None:
                return str(nested_value)

    return "UNKNOWN_ENTITY"


def alert_key(alert: Dict[str, Any], config: AlertEntropyConfig) -> str:
    """
    Duplication key:
        alert_type + entity + level + maturity

    This detects repeated same-type alerts on the same behavioral object.
    """
    alert_type = extract_alert_type(alert, config.type_fields)
    entity = extract_entity(alert, config.entity_fields)
    level = str(alert.get("level", "UNKNOWN_LEVEL"))
    maturity = str(alert.get("maturity", "UNKNOWN_MATURITY"))

    return f"{alert_type}|{entity}|{level}|{maturity}"


def normalize_alerts(raw_alerts: Iterable[Any]) -> List[Dict[str, Any]]:
    alerts: List[Dict[str, Any]] = []

    for index, item in enumerate(raw_alerts):
        if isinstance(item, dict):
            alerts.append(item)
        else:
            alerts.append(
                {
                    "alert_type": "INVALID_ALERT_PAYLOAD",
                    "raw_value": item,
                    "source_index": index,
                    "technical_risks": ["NON_DICT_ALERT_PAYLOAD"],
                }
            )

    return alerts


def filter_alerts_by_window(
    alerts: Sequence[Dict[str, Any]],
    config: AlertEntropyConfig,
    reference_time_utc: Optional[datetime] = None,
) -> Tuple[List[Dict[str, Any]], Optional[datetime], Optional[datetime], List[str]]:
    """
    Filter alerts inside [reference - window, reference].

    If reference_time_utc is None:
        use max timestamp found in alerts.

    If no valid timestamp exists:
        return all alerts and expose MISSING_TIMESTAMPS_WINDOW_NOT_APPLIED.
    """
    technical_risks: List[str] = []
    stamped: List[Tuple[Dict[str, Any], Optional[datetime]]] = [
        (alert, extract_timestamp(alert, config.timestamp_fields))
        for alert in alerts
    ]

    valid_timestamps = [stamp for _, stamp in stamped if stamp is not None]

    if reference_time_utc is None:
        reference_time_utc = max(valid_timestamps) if valid_timestamps else None
    elif reference_time_utc.tzinfo is None:
        reference_time_utc = reference_time_utc.replace(tzinfo=timezone.utc)
    else:
        reference_time_utc = reference_time_utc.astimezone(timezone.utc)

    if reference_time_utc is None:
        technical_risks.append("MISSING_TIMESTAMPS_WINDOW_NOT_APPLIED")
        return list(alerts), None, None, technical_risks

    window_start = reference_time_utc - timedelta(minutes=config.window_minutes)

    filtered = [
        alert
        for alert, stamp in stamped
        if stamp is not None and window_start <= stamp <= reference_time_utc
    ]

    missing_count = sum(1 for _, stamp in stamped if stamp is None)
    if missing_count > 0:
        technical_risks.append("SOME_ALERTS_WITHOUT_VALID_TIMESTAMP")

    return filtered, window_start, reference_time_utc, technical_risks


def shannon_entropy_from_counts(counts: Sequence[int]) -> float:
    total = sum(counts)

    if total <= 0:
        return 0.0

    entropy = 0.0

    for count in counts:
        if count <= 0:
            continue

        probability = count / total
        entropy -= probability * log2(probability)

    return entropy


def normalized_entropy(entropy: float, categories_count: int) -> float:
    if categories_count <= 1:
        return 0.0

    max_entropy = log2(categories_count)
    if max_entropy <= 0.0:
        return 0.0

    return min(1.0, max(0.0, entropy / max_entropy))


def compute_alert_entropy(
    alerts: Sequence[Dict[str, Any]] | Sequence[Any],
    window_minutes: int = 5,
    reference_time_utc: str | datetime | None = None,
    burst_threshold_count: int = 3,
    duplicate_ratio_threshold: float = 0.50,
) -> Dict[str, Any]:
    """
    Compute saturation metrics over a rolling window.

    Output:
        {
            "total_alerts": int,
            "duplication_ratio": float,
            "burst_detected": bool,
            ...
        }
    """
    config = AlertEntropyConfig(
        window_minutes=window_minutes,
        burst_threshold_count=burst_threshold_count,
        duplicate_ratio_threshold=duplicate_ratio_threshold,
    )

    normalized = normalize_alerts(alerts)

    if isinstance(reference_time_utc, str):
        parsed_reference = parse_utc_timestamp(reference_time_utc)
        if parsed_reference is None:
            raise ValueError(f"Invalid reference_time_utc: {reference_time_utc!r}")
    elif isinstance(reference_time_utc, datetime):
        parsed_reference = parse_utc_timestamp(reference_time_utc)
    elif reference_time_utc is None:
        parsed_reference = None
    else:
        raise TypeError(
            "reference_time_utc must be str, datetime or None, "
            f"got {type(reference_time_utc).__name__}"
        )

    recent_alerts, window_start, window_end, technical_risks = filter_alerts_by_window(
        normalized,
        config=config,
        reference_time_utc=parsed_reference,
    )

    total_alerts = len(recent_alerts)
    keys = [alert_key(alert, config) for alert in recent_alerts]
    key_counts = Counter(keys)

    unique_alert_keys = len(key_counts)
    duplicate_alerts = sum(count - 1 for count in key_counts.values() if count > 1)

    duplication_ratio = duplicate_alerts / total_alerts if total_alerts > 0 else 0.0

    alert_type_counts = Counter(
        extract_alert_type(alert, config.type_fields)
        for alert in recent_alerts
    )

    entity_counts = Counter(
        extract_entity(alert, config.entity_fields)
        for alert in recent_alerts
    )

    entropy = shannon_entropy_from_counts(list(key_counts.values()))
    norm_entropy = normalized_entropy(entropy, unique_alert_keys)

    burst_score = (
        total_alerts / config.burst_threshold_count
        if config.burst_threshold_count > 0
        else 0.0
    )

    burst_detected = (
        total_alerts >= config.burst_threshold_count
        or duplication_ratio >= config.duplicate_ratio_threshold
    )

    if total_alerts >= config.burst_threshold_count:
        technical_risks.append("ALERT_BURST_DETECTED")

    if duplication_ratio >= config.duplicate_ratio_threshold and total_alerts > 0:
        technical_risks.append("HIGH_DUPLICATION_RATIO")

    if total_alerts == 0:
        technical_risks.append("NO_RECENT_ALERTS")

    top_duplicates = [
        {
            "alert_key": key,
            "count": count,
        }
        for key, count in key_counts.most_common()
        if count > 1
    ]

    metrics = AlertEntropyMetrics(
        window_minutes=config.window_minutes,
        window_start_utc=window_start.isoformat() if window_start else None,
        window_end_utc=window_end.isoformat() if window_end else None,
        total_alerts=total_alerts,
        unique_alert_keys=unique_alert_keys,
        duplicate_alerts=duplicate_alerts,
        duplication_ratio=round(duplication_ratio, 6),
        shannon_entropy=round(entropy, 6),
        normalized_entropy=round(norm_entropy, 6),
        burst_detected=burst_detected,
        burst_score=round(burst_score, 6),
        top_duplicates=top_duplicates,
        alert_type_distribution=dict(alert_type_counts),
        entity_distribution=dict(entity_counts),
        technical_risks=technical_risks,
    )

    return asdict(metrics)


def summarize_entropy_state(metrics: Dict[str, Any]) -> str:
    """
    Human-readable technical saturation label.
    This is never used to suppress alerts.
    """
    total_alerts = int(metrics.get("total_alerts", 0))
    duplication_ratio = float(metrics.get("duplication_ratio", 0.0))
    burst_detected = bool(metrics.get("burst_detected", False))

    if total_alerts == 0:
        return "ALERT_FIELD_EMPTY"

    if burst_detected and duplication_ratio >= 0.50:
        return "SATURATED_DUPLICATE_BURST"

    if burst_detected:
        return "BURST_ACTIVE"

    if duplication_ratio >= 0.50:
        return "DUPLICATION_ACTIVE"

    return "NORMAL_ALERT_FLOW"


if __name__ == "__main__":
    import json

    sample_alerts = [
        {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "alert_type": "FIRST_DETACHMENT_MICRO",
            "currency": "GBP",
            "level": "HOT",
            "maturity": "EARLY",
        }
    ]

    result = compute_alert_entropy(sample_alerts)
    result["entropy_state"] = summarize_entropy_state(result)
    print(json.dumps(result, indent=2, ensure_ascii=False))
