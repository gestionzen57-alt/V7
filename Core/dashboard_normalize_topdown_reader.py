#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize(input_path: str | Path) -> Dict[str, Any]:
    raw = load_json(input_path)
    symbols_payload = raw.get("symbols", {})
    if isinstance(symbols_payload, list):
        symbols_iter = {str(x.get("symbol", "UNKNOWN")): x for x in symbols_payload}
    else:
        symbols_iter = symbols_payload
    rows = []
    critical = []
    windows = []
    for sym, state in symbols_iter.items():
        surf = state.get("surface_reading", {})
        day = state.get("day_profile", {})
        stack = state.get("reading_stack", {})
        mtf = stack.get("mtf_day_plan", {})
        ltf = stack.get("ltf_execution_conditions", {})
        risks = state.get("technical_risks", [])
        if risks:
            critical.extend([f"{sym}:{r}" for r in risks[:8]])
        window = surf.get("window", "UNKNOWN")
        windows.append(window)
        rows.append({
            "symbol": sym,
            "window": window,
            "flux": surf.get("flux", "UNKNOWN"),
            "zone": surf.get("zone", "UNKNOWN"),
            "driver": surf.get("driver", "UNKNOWN"),
            "condition": surf.get("condition", "UNKNOWN"),
            "machine_intention": surf.get("machine_intention", "UNKNOWN"),
            "close_position": day.get("close_position", "UNKNOWN"),
            "mtf_plan": mtf.get("plan_bias", "UNKNOWN"),
            "ltf_sweep": ltf.get("sweep_state", "UNKNOWN"),
            "technical_fragility": surf.get("technical_fragility", [])[:10],
        })
    if any(w == "HOT" for w in windows):
        global_window = "HOT"
    elif any(w == "WATCH" for w in windows):
        global_window = "WATCH"
    else:
        global_window = "WAIT"
    return {
        "timestamp_utc": utc_now_iso(),
        "method": "TOPDOWN_MARKET_READER_NORMALIZED_V73",
        "global_window": global_window,
        "symbols": rows,
        "critical_issues": sorted(set(critical)),
        "source": str(input_path),
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize V7.3 top-down market reader output for dashboard.")
    parser.add_argument("--input", default="output/dashboard_surface/topdown_market_reader.json")
    parser.add_argument("--output", default="output/dashboard_surface/topdown_reader.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    state = normalize(args.input)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        print(f"TOPDOWN_READER_NORMALIZE_OK | global_window={state.get('global_window')} | symbols={len(state.get('symbols',[]))} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
