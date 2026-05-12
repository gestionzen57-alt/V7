#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize daily flow packets for dashboard.")
    parser.add_argument("--input", default="output/dashboard_surface/daily_flow_packets.json")
    parser.add_argument("--output", default="output/dashboard_surface/daily_flow_packet.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    data = load_json(Path(args.input))
    packets = data.get("packets", {}) if isinstance(data.get("packets"), dict) else {}
    symbols = []

    for symbol, packet in sorted(packets.items()):
        dp = packet.get("daily_packet", {})
        jl = dp.get("journal_levels", {})
        symbols.append({
            "symbol": symbol,
            "intent_detected": dp.get("intent_detected"),
            "prediction_next_session": dp.get("prediction_next_session"),
            "htf_read": dp.get("htf_read"),
            "mtf_day_plan": dp.get("mtf_day_plan"),
            "close_position": jl.get("close_position"),
            "high_of_day": jl.get("high_of_day"),
            "low_of_day": jl.get("low_of_day"),
            "tested_count": len(dp.get("tested_levels", [])),
            "rejected_count": len(dp.get("rejected_levels", [])),
            "sweep_count": len(dp.get("sweep_candidates", [])),
            "technical_risks": packet.get("technical_risks", []),
        })

    global_status = "READY" if symbols else "NO_PACKET"
    if symbols and all("NO_M1_OHLC_ROWS" in (s.get("technical_risks") or []) for s in symbols):
        global_status = "NO_OHLC_LEVEL_READING"
    elif any(s["sweep_count"] > 0 for s in symbols):
        global_status = "SWEEP_CONTEXT_PRESENT"
    elif any(s["rejected_count"] > 0 for s in symbols):
        global_status = "REJECTION_CONTEXT_PRESENT"

    critical_issues = []
    for s in symbols:
        for r in s.get("technical_risks", []):
            if r not in critical_issues:
                critical_issues.append(r)

    out = {
        "method": "DAILY_FLOW_PACKET_NORMALIZED_V731",
        "global_status": global_status,
        "symbols": symbols,
        "critical_issues": critical_issues,
        "source": args.input,
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    print(
        f"DAILY_FLOW_PACKET_NORMALIZE_OK | global_status={global_status} | symbols={len(symbols)} | out={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
