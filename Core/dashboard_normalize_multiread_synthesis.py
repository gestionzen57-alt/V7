#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="output/dashboard_surface/powerflow_multiread_synthesis.json")
    parser.add_argument("--output", default="output/dashboard_surface/multiread_synthesis_dashboard.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    src = load_json(Path(args.input))
    symbols = []
    for item in src.get("symbols", []):
        if not isinstance(item, dict):
            continue
        symbols.append({
            "symbol": item.get("symbol"),
            "attention": item.get("attention"),
            "synthesis": item.get("synthesis"),
            "alignment": item.get("alignment"),
            "daily_intent": (item.get("daily") or {}).get("intent"),
            "topdown_intention": (item.get("topdown") or {}).get("machine_intention"),
            "live_brief": (item.get("live_brief") or {}).get("synthesis"),
            "b6_state": (item.get("b6") or {}).get("state"),
            "b6_bias": (item.get("b6") or {}).get("bias"),
            "b6_action": (item.get("b6") or {}).get("action_level"),
            "reading": item.get("reading"),
            "technical_risks": item.get("technical_risks", []),
        })

    out = {
        "method": "MULTIREAD_SYNTHESIS_DASHBOARD_NORMALIZED_V734",
        "global_status": src.get("global_status", "MULTIREAD_UNKNOWN"),
        "symbols": symbols,
        "critical_issues": src.get("critical_issues", []),
        "source": args.input,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"MULTIREAD_SYNTHESIS_NORMALIZE_OK | global_status={out['global_status']} | symbols={len(symbols)} | out={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
