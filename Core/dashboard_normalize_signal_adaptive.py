#!/usr/bin/env python3
"""
Dashboard normalizer for SIGNAL_ADAPTIVE_PROFILE.

Input:
  output/dashboard_surface/signal_adaptive_profiles.json

Output:
  output/dashboard_surface/signal_adaptive.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(data: Mapping[str, Any], path: str | Path) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize(input_path: str, output_path: str) -> Dict[str, Any]:
    src = read_json(input_path)
    symbols_obj = src.get("symbols")
    if not isinstance(symbols_obj, Mapping):
        symbols_obj = {}

    rows: List[Dict[str, Any]] = []
    critical: List[str] = []

    for symbol in sorted(symbols_obj.keys()):
        profile = symbols_obj[symbol]
        if not isinstance(profile, Mapping):
            continue

        risks = list(profile.get("technical_risks") or [])
        if profile.get("mode") == "DATA_NOT_READY":
            critical.append(f"{symbol}_DATA_NOT_READY")
        for risk in risks:
            if "NOT_READY" in str(risk) or "NOT_LIVE" in str(risk) or "STALE" in str(risk):
                critical.append(f"{symbol}_{risk}")

        rows.append({
            "symbol": symbol,
            "mode": profile.get("mode", "DATA_NOT_READY"),
            "signal_permission": profile.get("signal_permission", "HOLD_PERCEPTION_ONLY"),
            "context_confidence": profile.get("context_confidence", 0.0),
            "enabled_layers": profile.get("enabled_layers", {}),
            "disabled_or_degraded_layers": profile.get("disabled_or_degraded_layers", []),
            "technical_risks": risks,
        })

    out = {
        "timestamp_utc": src.get("timestamp_utc") or utc_now_iso(),
        "method": "SIGNAL_ADAPTIVE_PROFILE_NORMALIZED",
        "global_mode": src.get("global_mode", "DATA_NOT_READY"),
        "symbols": rows,
        "critical_issues": sorted(set(critical)),
        "source": input_path,
        "technical_risks": src.get("technical_risks", []),
    }

    if not src:
        out["global_mode"] = "DATA_NOT_READY"
        out["technical_risks"] = ["SIGNAL_ADAPTIVE_INPUT_MISSING_OR_INVALID"]

    write_json(out, output_path)
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize SIGNAL_ADAPTIVE_PROFILE for dashboard.")
    parser.add_argument("--input", default="output/dashboard_surface/signal_adaptive_profiles.json")
    parser.add_argument("--output", "--out", dest="output", default="output/dashboard_surface/signal_adaptive.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    out = normalize(args.input, args.output)

    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        print(
            "SIGNAL_ADAPTIVE_NORMALIZE_OK | "
            f"global_mode={out.get('global_mode')} | "
            f"symbols={len(out.get('symbols', []))} | "
            f"out={args.output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
