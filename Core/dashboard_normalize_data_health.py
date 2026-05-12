#!/usr/bin/env python3
"""
Dashboard normalizer for DATA_HEALTH_MONITOR.

Input:
  output/data_health_monitor.json

Output:
  output/dashboard_surface/data_health.json

Contract:
{
  "global_status": "LIVE_OK",
  "symbols": [
    {"symbol": "GBPUSD", "status": "LIVE_OK", "last_update_age_min": 5}
  ],
  "critical_issues": ["USDJPY_STALE_DATA"]
}
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(data: Mapping[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def min_age_for_symbol(payload: Mapping[str, Any]) -> Optional[float]:
    explicit = payload.get("last_update_age_min")
    if explicit is not None:
        try:
            return round(float(explicit), 3)
        except Exception:
            pass

    ages: List[float] = []
    timeframes = payload.get("timeframes")
    if isinstance(timeframes, Mapping):
        for tf_payload in timeframes.values():
            if isinstance(tf_payload, Mapping) and tf_payload.get("age_minutes") is not None:
                try:
                    ages.append(float(tf_payload["age_minutes"]))
                except Exception:
                    pass
    return round(min(ages), 3) if ages else None


def detect_critical_issues(symbol: str, payload: Mapping[str, Any]) -> List[str]:
    issues: List[str] = []
    status = str(payload.get("status", "DATA_STALE")).upper()

    if status in {"DATA_STALE", "DATA_MISSING", "CRITICAL_STALE"}:
        issues.append(f"{symbol}_STALE_DATA")

    if status == "PARTIAL_STALE":
        issues.append(f"{symbol}_PARTIAL_STALE")

    timeframes = payload.get("timeframes")
    if isinstance(timeframes, Mapping):
        for htf in ("240", "1440"):
            tf_payload = timeframes.get(htf)
            if isinstance(tf_payload, Mapping):
                if int(tf_payload.get("row_count") or 0) < 50:
                    issue = f"{symbol}_HTF_INCOMPLETE"
                    if issue not in issues:
                        issues.append(issue)

        gap_count = 0
        for tf_payload in timeframes.values():
            if isinstance(tf_payload, Mapping):
                try:
                    gap_count += int(tf_payload.get("gap_count") or len(tf_payload.get("gaps") or []))
                except Exception:
                    pass
        if gap_count > 0:
            issues.append(f"{symbol}_TEMPORAL_GAPS")

    return issues


def normalize_data_health(input_path: str, output_path: str) -> Dict[str, Any]:
    src = read_json(input_path)
    symbols_obj = src.get("symbols") if isinstance(src.get("symbols"), Mapping) else {}

    symbols_list: List[Dict[str, Any]] = []
    critical_issues: List[str] = []

    for symbol in sorted(symbols_obj.keys()):
        payload = symbols_obj[symbol]
        if not isinstance(payload, Mapping):
            continue

        age = min_age_for_symbol(payload)
        status = str(payload.get("status", "DATA_STALE")).upper()
        issues = detect_critical_issues(symbol, payload)
        critical_issues.extend(issues)

        symbols_list.append({
            "symbol": symbol,
            "status": status,
            "last_update_age_min": age,
            "issues": issues,
        })

    normalized = {
        "timestamp_utc": src.get("timestamp_utc") or utc_now_iso(),
        "method": "DATA_HEALTH_MONITOR_NORMALIZED",
        "global_status": src.get("global_status", "CRITICAL_STALE"),
        "symbols": symbols_list,
        "critical_issues": sorted(set(critical_issues)),
        "source": input_path,
        "technical_risks": src.get("technical_risks", []),
    }

    if not src:
        normalized["global_status"] = "CRITICAL_STALE"
        normalized["technical_risks"] = ["DATA_HEALTH_INPUT_MISSING_OR_INVALID"]

    write_json(normalized, output_path)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize DATA_HEALTH_MONITOR for dashboard.")
    parser.add_argument("--input", default="output/data_health_monitor.json")
    parser.add_argument("--output", "--out", dest="output", default="output/dashboard_surface/data_health.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    result = normalize_data_health(args.input, args.output)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            "DATA_HEALTH_NORMALIZE_OK | "
            f"global_status={result.get('global_status')} | "
            f"symbols={len(result.get('symbols', []))} | "
            f"issues={len(result.get('critical_issues', []))} | "
            f"out={args.output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
