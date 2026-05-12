#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_order_flow_proxy_lite import build


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    ap.add_argument("--lookback-rows", type=int, default=240)
    ap.add_argument("--window", type=int, default=20)
    ap.add_argument("--output", default="output/dashboard_surface/microstructure_states.json")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    states = {}
    reports = []

    for sym in symbols:
        try:
            state = build(Path(args.db), sym, args.lookback_rows, args.window)
            states[sym] = state
            m = state.get("microstructure", {})
            reports.append({
                "symbol": sym,
                "state": m.get("state"),
                "tension_score": m.get("tension_score"),
                "delta_cumulative": m.get("delta_cumulative"),
                "absorption_rate": (m.get("absorption") or {}).get("rate"),
                "alerts": len(m.get("alerts", [])),
                "technical_risks": state.get("technical_risks", []),
                "written": f"output/dashboard_surface/{sym}/microstructure_state.json",
            })
        except Exception as e:
            reports.append({
                "symbol": sym,
                "error": type(e).__name__,
                "message": str(e),
            })

    out = {
        "method": "B6_ORDER_FLOW_PROXY_ALL_LITE_V1",
        "symbols": symbols,
        "reports": reports,
        "states": states,
    }

    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.pretty:
        print(json.dumps(out, ensure_ascii=False, indent=2))

    summary = " | ".join(
        f"{r.get('symbol')} state={r.get('state')} tension={r.get('tension_score')} alerts={r.get('alerts')}"
        if not r.get("error") else f"{r.get('symbol')} ERR={r.get('error')}"
        for r in reports
    )
    print(f"B6_ORDER_FLOW_PROXY_ALL_OK | {summary} | out={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
