#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — Flow Ontology cycle runner.

Purpose:
- Run ontology validator after behavioral alert mapping.
- Support MultiSymbol queue names.
- Keep output usable by dashboard.

No DB write. Reads queue JSON only.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    from pf_flow_ontology_validator import build_ontology_report, write_json
except Exception as exc:  # pragma: no cover
    print(f"FLOW_ONTOLOGY_IMPORT_FAILED: {exc}", file=sys.stderr)
    raise


def parse_symbols(text: str) -> List[str]:
    return [s.strip().upper() for s in str(text).split(",") if s.strip()]


def first_existing(paths: List[Path]) -> Path:
    for p in paths:
        if p.exists():
            return p
    return paths[0]


def queue_for_symbol(symbol: str, default_symbol: str) -> Path:
    paths = [
        Path("output") / f"behavioral_alert_queue_{symbol}.json",
        Path("output") / "dashboard_surface" / symbol / "behavioral_alert_queue.json",
    ]
    if symbol == default_symbol:
        paths.extend([
            Path("output") / "behavioral_alert_queue.json",
            Path("output") / "dashboard_surface" / "behavioral_alert_queue.json",
        ])
    else:
        paths.append(Path("output") / "behavioral_alert_queue.json")
    return first_existing(paths)


def write_symbol_outputs(symbol: str, report: Dict, primary: bool) -> List[str]:
    written: List[str] = []

    out1 = Path("output") / f"flow_ontology_report_{symbol}.json"
    write_json(report, str(out1))
    written.append(str(out1))

    out2 = Path("output") / "dashboard_surface" / symbol / "flow_ontology_report.json"
    write_json(report, str(out2))
    written.append(str(out2))

    if primary:
        out3 = Path("output") / "flow_ontology_report.json"
        write_json(report, str(out3))
        written.append(str(out3))

        out4 = Path("output") / "dashboard_surface" / "flow_ontology_report.json"
        write_json(report, str(out4))
        written.append(str(out4))

    return written


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Flow Ontology validation for one or multiple symbols.")
    parser.add_argument("--symbols", default="GBPUSD", help="Comma-separated symbols.")
    parser.add_argument("--default-symbol", default="GBPUSD")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols)
    default_symbol = args.default_symbol.upper()

    summary = {
        "method": "FLOW_ONTOLOGY_CYCLE",
        "symbols": symbols,
        "reports": [],
        "technical_risks": [],
    }

    for i, symbol in enumerate(symbols):
        queue = queue_for_symbol(symbol, default_symbol)
        report = build_ontology_report(str(queue))
        report["symbol"] = symbol
        report["cycle_queue_selected"] = str(queue)
        written = write_symbol_outputs(symbol, report, primary=(i == 0 or symbol == default_symbol))

        summary["reports"].append({
            "symbol": symbol,
            "queue": str(queue),
            "alerts_total": report.get("alerts_total"),
            "alerts_classified": report.get("alerts_classified"),
            "ontology_coverage": report.get("ontology_coverage"),
            "written": written,
            "technical_risks": report.get("technical_risks", []),
        })
        for risk in report.get("technical_risks", []):
            summary["technical_risks"].append(f"{symbol}:{risk}")

    summary_path = Path("output") / "dashboard_surface" / "flow_ontology_cycle_summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        compact = " | ".join(
            f"{r['symbol']} alerts={r['alerts_total']} coverage={r['ontology_coverage']}"
            for r in summary["reports"]
        )
        print(f"FLOW_ONTOLOGY_CYCLE_OK | {compact} | summary={summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
