#!/usr/bin/env python3
"""
PowerFlow V7.1 - Entropy Engine runner
Standalone cockpit producer for output/entropy_engine.json.

Reads behavioral alert queue JSON, measures alert dispersion, duplication and burst activity.
Does not write to DB. The --db argument is accepted for scheduler compatibility only.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_QUEUE = Path("output") / "behavioral_alert_queue.json"
DEFAULT_OUTPUT = Path("output") / "entropy_engine.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # Last-resort common formats used in logs.
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(text[:19], fmt)
                break
            except ValueError:
                dt = None  # type: ignore[assignment]
        else:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_json(path: Path) -> Any:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return []


def extract_alerts(raw: Any) -> List[Dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in ("alerts", "items", "events", "queue", "behavioral_alert_queue"):
            value = raw.get(key)
            if isinstance(value, list):
                return [x for x in value if isinstance(x, dict)]
        # Single alert object fallback.
        if any(k in raw for k in ("alert_type", "type", "timestamp")):
            return [raw]
    return []


def get_timestamp(alert: Dict[str, Any]) -> Optional[datetime]:
    for key in ("timestamp", "created_at", "time", "ts", "event_time"):
        dt = parse_dt(alert.get(key))
        if dt is not None:
            return dt
    return None


def alert_key(alert: Dict[str, Any]) -> str:
    parts = [
        alert.get("alert_type") or alert.get("type") or alert.get("event_type") or "UNKNOWN",
        alert.get("currency") or alert.get("ccy") or alert.get("asset") or alert.get("symbol") or "GLOBAL",
        alert.get("level") or alert.get("severity") or "INFO",
        alert.get("maturity") or "NA",
    ]
    return "|".join(str(p).upper() for p in parts)


def shannon_normalized(counts: Counter[str]) -> float:
    total = sum(counts.values())
    if total <= 1 or len(counts) <= 1:
        return 0.0
    entropy = -sum((c / total) * math.log(c / total) for c in counts.values() if c > 0)
    return max(0.0, min(1.0, entropy / math.log(len(counts))))


def compute_entropy(alerts: List[Dict[str, Any]], window_minutes: int, now: datetime) -> Dict[str, Any]:
    cutoff = now - timedelta(minutes=window_minutes)
    burst_cutoff = now - timedelta(minutes=5)

    timestamped = []
    untimestamped = []
    for alert in alerts:
        dt = get_timestamp(alert)
        if dt is None:
            untimestamped.append(alert)
        else:
            timestamped.append((dt, alert))

    if timestamped:
        window_alerts = [a for dt, a in timestamped if dt >= cutoff]
        burst_alerts = [a for dt, a in timestamped if dt >= burst_cutoff]
    else:
        # If legacy queue has no timestamps, use the available list as a static field sample.
        window_alerts = alerts
        burst_alerts = alerts[-5:]

    keys = [alert_key(a) for a in window_alerts]
    counts: Counter[str] = Counter(keys)
    total = len(keys)
    unique = len(counts)

    normalized_entropy = shannon_normalized(counts)
    duplication_ratio = 0.0 if total == 0 else max(0.0, min(1.0, 1.0 - (unique / total)))
    burst_score = max(0.0, min(1.0, len(burst_alerts) / 3.0))

    if total >= 3 and burst_score >= 1.0 and duplication_ratio >= 0.50:
        state = "SATURATED_DUPLICATE_BURST"
    elif total >= 5 and duplication_ratio >= 0.65:
        state = "SATURATED"
    elif burst_score >= 1.0:
        state = "BURST_ACTIVE"
    else:
        state = "NORMAL_ALERT_FLOW"

    return {
        "engine": "pf_entropy_engine_standalone",
        "version": "V7.1-runner-compat",
        "generated_at": now.isoformat(),
        "window_minutes": window_minutes,
        "alert_entropy_state": state,
        "normalized_entropy": round(normalized_entropy, 4),
        "duplication_ratio": round(duplication_ratio, 4),
        "burst_score": round(burst_score, 4),
        "alerts_count": total,
        "unique_alert_keys": unique,
        "top_alert_keys": [
            {"alert_key": key, "count": count}
            for key, count in counts.most_common(8)
        ],
        "technical_risks": [] if total > 0 else ["NO_ALERTS_IN_WINDOW"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.1 entropy runner")
    parser.add_argument("--db", default="powerflow.db", help="Accepted for scheduler compatibility; not used.")
    parser.add_argument("--symbol", default="GBPUSD", help="Accepted for scheduler compatibility.")
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE), help="Alert queue JSON path.")
    parser.add_argument("--window-minutes", type=int, default=30)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    raw = load_json(Path(args.queue))
    alerts = extract_alerts(raw)
    report = compute_entropy(alerts, args.window_minutes, utc_now())
    report["symbol"] = args.symbol
    report["source_queue"] = str(Path(args.queue))

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
