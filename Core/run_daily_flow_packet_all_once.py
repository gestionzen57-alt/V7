#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from pf_daily_flow_packet import build_daily_flow_packet, write_packet


def split_symbols(raw: str):
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build daily flow packets for multiple symbols.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--output", default="output/dashboard_surface/daily_flow_packets.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbols = split_symbols(args.symbols)
    packets = {}
    reports = []
    for symbol in symbols:
        packet = build_daily_flow_packet(Path(args.db), symbol)
        packets[symbol] = packet

        per_symbol_path = Path("output/dashboard_surface") / symbol / "daily_flow_packet.json"
        write_packet(packet, per_symbol_path, pretty=args.pretty)

        reports.append({
            "symbol": symbol,
            "intent_detected": packet.get("daily_packet", {}).get("intent_detected"),
            "sweeps": len(packet.get("daily_packet", {}).get("sweep_candidates", [])),
            "tested_levels": len(packet.get("daily_packet", {}).get("tested_levels", [])),
            "rejected_levels": len(packet.get("daily_packet", {}).get("rejected_levels", [])),
            "technical_risks": packet.get("technical_risks", []),
            "written": str(per_symbol_path),
        })

    out = {
        "method": "DAILY_FLOW_PACKET_ALL_V731",
        "symbols": symbols,
        "packets": packets,
        "reports": reports,
    }
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    print(
        "DAILY_FLOW_PACKET_ALL_OK | "
        + " | ".join(f"{r['symbol']} intent={r['intent_detected']} sweeps={r['sweeps']}" for r in reports)
        + f" | out={output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
