#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence
from pf_daily_journal_builder import build_daily_journal


def split_symbols(raw: str):
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--output", default="output/dashboard_surface/daily_journal.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    symbols = split_symbols(args.symbols)
    symbol_reports, summaries = {}, []
    for symbol in symbols:
        report = build_daily_journal(Path(args.db), symbol)
        symbol_reports[symbol] = report
        per_symbol_path = Path("output/dashboard_surface") / symbol / "daily_journal.json"
        per_symbol_path.parent.mkdir(parents=True, exist_ok=True)
        per_symbol_path.write_text(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
        journal = report.get("journal", {})
        summaries.append({"symbol": symbol, "date_utc": report.get("date_utc"), "intent_detected": journal.get("intent_detected"), "prediction_next_session": journal.get("prediction_next_session"), "close_position": journal.get("close_position"), "tested_count": len(journal.get("levels_tested") or []), "rejected_count": len(journal.get("levels_rejected") or []), "accepted_count": len(journal.get("levels_accepted") or []), "sweep_count": len(journal.get("sweeps") or []), "robustness": report.get("robustness"), "technical_risks": report.get("technical_risks", []), "written": str(per_symbol_path)})
    if any(s["sweep_count"] > 0 for s in summaries): global_status = "SWEEP_CONTEXT_PRESENT"
    elif any(s["rejected_count"] > 0 for s in summaries): global_status = "REJECTION_CONTEXT_PRESENT"
    elif any(s["accepted_count"] > 0 for s in summaries): global_status = "BREAK_ACCEPTANCE_PRESENT"
    else: global_status = "JOURNAL_READY"
    out = {"method": "DAILY_JOURNAL_ALL_V732", "global_status": global_status, "symbols": symbols, "summaries": summaries, "journals": symbol_reports}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty: print(json.dumps(out, indent=2, ensure_ascii=False))
    print("DAILY_JOURNAL_ALL_OK | " + " | ".join(f"{s['symbol']} intent={s['intent_detected']} sweeps={s['sweep_count']}" for s in summaries) + f" | global_status={global_status} | out={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
