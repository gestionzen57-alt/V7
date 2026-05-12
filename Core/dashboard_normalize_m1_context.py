#!/usr/bin/env python3
"""
Normalize M1_CONTEXT_SCORE for dashboard contract.

Input:
  output/m1_context_score.json

Output:
  output/dashboard_surface/m1_context_score.json

Contract:
{
  "currencies": [
    {
      "currency": "GBP",
      "m1_score": 0.82,
      "exploitability": "HIGH",
      "intervention_window": "IGNITION_CLEAN"
    }
  ]
}
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict


def normalize_m1_context(state: Dict[str, Any]) -> Dict[str, Any]:
    currencies = []
    for currency, payload in (state.get("currencies") or {}).items():
        currencies.append({
            "currency": currency,
            "m1_score": payload.get("m1_context_score"),
            "exploitability": payload.get("exploitability"),
            "intervention_window": payload.get("intervention_window"),
            "breakdown": payload.get("breakdown", {}),
            "technical_risks": payload.get("technical_risks", []),
        })

    currencies.sort(key=lambda item: item["currency"])

    return {
        "timestamp_utc": state.get("timestamp_utc"),
        "symbol": state.get("symbol"),
        "method": "M1_CONTEXT_SCORE_NORMALIZED",
        "currencies": currencies,
        "technical_risks": state.get("technical_risks", []),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize M1 context score for dashboard.")
    parser.add_argument("--input", default="output/m1_context_score.json")
    parser.add_argument("--output", default="output/dashboard_surface/m1_context_score.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise FileNotFoundError(f"Input not found: {src}")

    state = json.loads(src.read_text(encoding="utf-8"))
    normalized = normalize_m1_context(state)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(normalized, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(normalized, indent=2, ensure_ascii=False))
    else:
        print(f"M1_CONTEXT_DASHBOARD_NORMALIZED_OK | input={args.input} | output={args.output} | currencies={len(normalized['currencies'])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
