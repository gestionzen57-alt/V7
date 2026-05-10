#!/usr/bin/env python3
"""
PowerFlow V7.2 — Alert Observability Metrics

IMPORTANT:
This module does not validate trades.
This module does not filter alerts.
This module does not suppress early signals.
This module does not decide whether an alert is good or bad.

It only measures alert coverage, distribution, completeness, duplication,
and technical observability.

The machine measures.
The trader decides.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


VERSION = "AlertObservabilityMetricsV0.1"
METHOD = "alert_observability_metrics_non_blocking"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    raw = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_nested(obj: Dict[str, Any], path: Sequence[str], default: Any = None) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def normalize_label(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def ensure_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def safe_ratio(num: float, den: float) -> float:
    if den <= 0:
        return 0.0
    return float(num) / float(den)


def stable_alert_key(alert: Dict[str, Any]) -> str:
    alert_type = extract_alert_type(alert)
    symbol = extract_symbol(alert)
    level = extract_level(alert)
    maturity = extract_maturity(alert)
    regime = extract_regime(alert)
    session = extract_session(alert)
    return "|".join([alert_type, symbol, level, maturity, regime, session])


def extract_alert_type(alert: Dict[str, Any]) -> str:
    return normalize_label(
        alert.get("alert_type")
        or alert.get("type")
        or alert.get("event_type")
        or alert.get("name")
    )


def extract_level(alert: Dict[str, Any]) -> str:
    return normalize_label(alert.get("level") or alert.get("severity") or alert.get("priority"))


def extract_maturity(alert: Dict[str, Any]) -> str:
    return normalize_label(alert.get("maturity") or alert.get("stage"))


def extract_symbol(alert: Dict[str, Any]) -> str:
    return normalize_label(
        alert.get("symbol")
        or alert.get("pair")
        or alert.get("instrument")
        or alert.get("currency")
        or get_nested(alert, ["context", "symbol"])
    )


def extract_regime(alert: Dict[str, Any]) -> str:
    return normalize_label(
        get_nested(alert, ["regime_context", "regime"])
        or get_nested(alert, ["regime", "regime"])
        or alert.get("regime")
    )


def extract_session(alert: Dict[str, Any]) -> str:
    return normalize_label(
        get_nested(alert, ["session_context", "session"])
        or get_nested(alert, ["session", "session"])
        or alert.get("session")
    )


def extract_timestamp(alert: Dict[str, Any]) -> Optional[datetime]:
    for key in ("timestamp", "time", "created_at", "generated_at", "ts"):
        dt = parse_timestamp(alert.get(key))
        if dt is not None:
            return dt
    return None


def extract_technical_risks(alert: Dict[str, Any]) -> List[str]:
    candidates = []
    candidates.extend(ensure_list(alert.get("technical_risks")))
    candidates.extend(ensure_list(alert.get("risks")))
    candidates.extend(ensure_list(get_nested(alert, ["quality", "technical_risks"])))
    out: List[str] = []
    for item in candidates:
        label = normalize_label(item, default="")
        if label:
            out.append(label)
    return out


def load_queue(path: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    risks: List[str] = []

    if not path.exists():
        return [], ["QUEUE_NOT_FOUND"]

    raw = path.read_text(encoding="utf-8", errors="replace").strip()
    if not raw:
        return [], ["QUEUE_EMPTY_FILE"]

    data: Any
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Fallback JSONL / append-only queue style.
        alerts: List[Dict[str, Any]] = []
        malformed = 0
        for line in raw.splitlines():
            line = line.strip().rstrip(",")
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(obj, dict):
                alerts.append(obj)
        if malformed:
            risks.append("MALFORMED_JSONL_ENTRIES")
        return alerts, risks

    if isinstance(data, list):
        alerts = [x for x in data if isinstance(x, dict)]
        if len(alerts) != len(data):
            risks.append("NON_OBJECT_ALERT_ENTRIES_IGNORED")
        return alerts, risks

    if isinstance(data, dict):
        for key in ("alerts", "events", "queue", "items", "results", "data"):
            value = data.get(key)
            if isinstance(value, list):
                alerts = [x for x in value if isinstance(x, dict)]
                if len(alerts) != len(value):
                    risks.append("NON_OBJECT_ALERT_ENTRIES_IGNORED")
                return alerts, risks

        # A single alert object.
        if any(k in data for k in ("alert_type", "type", "event_type", "level", "maturity")):
            return [data], risks

        return [], ["NO_ALERT_LIST_FOUND_IN_JSON"]

    return [], ["UNSUPPORTED_QUEUE_FORMAT"]


@dataclass
class AlertMetricsConfig:
    queue_path: Path
    window_minutes: Optional[int] = 180


class AlertObservabilityMetrics:
    def __init__(self, config: AlertMetricsConfig):
        self.config = config

    def compute(self) -> Dict[str, Any]:
        alerts_raw, load_risks = load_queue(self.config.queue_path)
        now = datetime.now(timezone.utc)

        alerts = self._filter_window(alerts_raw, now)
        total = len(alerts)

        by_type = Counter(extract_alert_type(a) for a in alerts)
        by_level = Counter(extract_level(a) for a in alerts)
        by_maturity = Counter(extract_maturity(a) for a in alerts)
        by_symbol = Counter(extract_symbol(a) for a in alerts)
        by_regime = Counter(extract_regime(a) for a in alerts)
        by_session = Counter(extract_session(a) for a in alerts)

        risk_counter = Counter()
        for alert in alerts:
            risk_counter.update(extract_technical_risks(alert))

        keys = [stable_alert_key(a) for a in alerts]
        unique_keys = len(set(keys))
        duplicate_ratio = 1.0 - safe_ratio(unique_keys, total) if total else 0.0

        coverage = self._coverage(alerts)
        quality_flags = self._quality_flags(total, coverage, duplicate_ratio, load_risks)

        result = {
            "valid": True,
            "method": METHOD,
            "version": VERSION,
            "generated_at": utc_now_iso(),
            "metrics_only": True,
            "no_filtering": True,
            "no_trade_decision": True,
            "queue_path": str(self.config.queue_path),
            "window_minutes": self.config.window_minutes,
            "total_alerts": total,
            "total_alerts_raw": len(alerts_raw),
            "distribution": {
                "by_alert_type": dict(by_type),
                "by_level": dict(by_level),
                "by_maturity": dict(by_maturity),
                "by_symbol": dict(by_symbol),
                "by_regime": dict(by_regime),
                "by_session": dict(by_session),
                "technical_risks": dict(risk_counter),
            },
            "coverage": coverage,
            "duplicates": {
                "unique_alert_keys": unique_keys,
                "duplicate_ratio": round(duplicate_ratio, 6),
                "top_duplicate_keys": self._top_duplicates(keys),
            },
            "technical_notes": quality_flags,
            "technical_risks": quality_flags,
        }

        if total == 0:
            result["technical_notes"].append("NO_ALERTS_IN_WINDOW")
            result["technical_risks"].append("NO_ALERTS_IN_WINDOW")

        # Preserve uniqueness after possible append.
        result["technical_notes"] = list(dict.fromkeys(result["technical_notes"]))
        result["technical_risks"] = list(dict.fromkeys(result["technical_risks"]))

        return result

    def _filter_window(self, alerts: List[Dict[str, Any]], now: datetime) -> List[Dict[str, Any]]:
        if self.config.window_minutes is None:
            return alerts

        lower = now - timedelta(minutes=self.config.window_minutes)
        filtered: List[Dict[str, Any]] = []
        without_ts: List[Dict[str, Any]] = []

        for alert in alerts:
            ts = extract_timestamp(alert)
            if ts is None:
                without_ts.append(alert)
                continue
            if ts >= lower:
                filtered.append(alert)

        # If no timestamps exist, keep queue measurable instead of hiding it.
        if not filtered and without_ts and len(without_ts) == len(alerts):
            return alerts

        return filtered

    def _coverage(self, alerts: List[Dict[str, Any]]) -> Dict[str, float]:
        total = len(alerts)

        def present(fn) -> float:
            if total == 0:
                return 0.0
            count = sum(1 for alert in alerts if fn(alert) != "UNKNOWN")
            return round(safe_ratio(count, total), 6)

        tech_count = sum(1 for alert in alerts if extract_technical_risks(alert))

        return {
            "alert_type_present_ratio": present(extract_alert_type),
            "level_present_ratio": present(extract_level),
            "maturity_present_ratio": present(extract_maturity),
            "symbol_present_ratio": present(extract_symbol),
            "regime_context_present_ratio": present(extract_regime),
            "session_context_present_ratio": present(extract_session),
            "technical_risks_present_ratio": round(safe_ratio(tech_count, total), 6) if total else 0.0,
        }

    def _quality_flags(self, total: int, coverage: Dict[str, float], duplicate_ratio: float, load_risks: List[str]) -> List[str]:
        flags = list(load_risks)

        # These are observability notes, not blocking filters.
        if total == 0:
            flags.append("NO_ALERTS_IN_WINDOW")
        if coverage.get("regime_context_present_ratio", 0.0) < 0.8 and total > 0:
            flags.append("REGIME_CONTEXT_PARTIAL")
        if coverage.get("session_context_present_ratio", 0.0) < 0.8 and total > 0:
            flags.append("SESSION_CONTEXT_PARTIAL")
        if coverage.get("maturity_present_ratio", 0.0) < 0.8 and total > 0:
            flags.append("MATURITY_PARTIAL")
        if coverage.get("technical_risks_present_ratio", 0.0) < 0.5 and total > 0:
            flags.append("TECHNICAL_RISKS_PARTIAL")
        if duplicate_ratio > 0.5 and total >= 5:
            flags.append("HIGH_DUPLICATE_RATIO")
        if total < 5 and total > 0:
            flags.append("LOW_ALERT_SAMPLE")

        return list(dict.fromkeys(flags))

    def _top_duplicates(self, keys: List[str], limit: int = 10) -> List[Dict[str, Any]]:
        counts = Counter(keys)
        return [
            {"alert_key": key, "count": count}
            for key, count in counts.most_common(limit)
            if count > 1
        ]


def write_markdown_report(metrics: Dict[str, Any], path: Path) -> None:
    dist = metrics.get("distribution", {})
    coverage = metrics.get("coverage", {})
    duplicates = metrics.get("duplicates", {})

    lines = [
        "# PowerFlow V7.2 — Alert Observability Metrics",
        "",
        f"**Generated at:** {metrics.get('generated_at')}",
        f"**Queue:** `{metrics.get('queue_path')}`",
        f"**Window minutes:** `{metrics.get('window_minutes')}`",
        f"**Total alerts:** **{metrics.get('total_alerts')}**",
        "",
        "## Doctrine",
        "",
        "This report is metrics-only.",
        "",
        "- It does not filter alerts.",
        "- It does not validate trades.",
        "- It does not suppress early signals.",
        "- It does not decide.",
        "- The trader decides.",
        "",
        "## Distribution",
        "",
        "### By level",
        "",
    ]

    for key, value in sorted(dist.get("by_level", {}).items()):
        lines.append(f"- `{key}`: {value}")

    lines += ["", "### By maturity", ""]
    for key, value in sorted(dist.get("by_maturity", {}).items()):
        lines.append(f"- `{key}`: {value}")

    lines += ["", "### By alert type", ""]
    for key, value in dist.get("by_alert_type", {}).items():
        lines.append(f"- `{key}`: {value}")

    lines += ["", "### Technical risks", ""]
    risks = dist.get("technical_risks", {})
    if risks:
        for key, value in sorted(risks.items()):
            lines.append(f"- `{key}`: {value}")
    else:
        lines.append("- No technical risks observed in alert queue.")

    lines += ["", "## Coverage", ""]
    for key, value in sorted(coverage.items()):
        lines.append(f"- `{key}`: {value}")

    lines += [
        "",
        "## Duplicates",
        "",
        f"- Unique alert keys: `{duplicates.get('unique_alert_keys')}`",
        f"- Duplicate ratio: `{duplicates.get('duplicate_ratio')}`",
        "",
        "## Technical notes",
        "",
    ]

    notes = metrics.get("technical_notes", [])
    if notes:
        for note in notes:
            lines.append(f"- `{note}`")
    else:
        lines.append("- No technical notes.")

    lines += [
        "",
        "## Verdict",
        "",
        "This brique is an observability mirror. It is non-blocking by design.",
        "",
        "The machine measures. The trader decides.",
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def compute_alert_observability(
    queue_path: str | Path,
    window_minutes: Optional[int] = 180,
) -> Dict[str, Any]:
    config = AlertMetricsConfig(queue_path=Path(queue_path), window_minutes=window_minutes)
    return AlertObservabilityMetrics(config).compute()
