#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists(): return {}
    try: return json.loads(path.read_text(encoding="utf-8"))
    except Exception: return {}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="output/dashboard_surface/daily_journal.json")
    parser.add_argument("--output", default="output/dashboard_surface/daily_journal_dashboard.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    data = load_json(Path(args.input))
    summaries = data.get("summaries") if isinstance(data.get("summaries"), list) else []
    symbols, issues = [], []
    for s in summaries:
        if not isinstance(s, dict): continue
        for r in s.get("technical_risks", []):
            if r not in issues: issues.append(r)
        symbols.append({"symbol": s.get("symbol"), "date_utc": s.get("date_utc"), "intent": s.get("intent_detected"), "prediction": s.get("prediction_next_session"), "close_position": s.get("close_position"), "tested": s.get("tested_count"), "rejected": s.get("rejected_count"), "accepted": s.get("accepted_count"), "sweeps": s.get("sweep_count"), "robustness": s.get("robustness"), "technical_risks": s.get("technical_risks", [])})
    out = {"method": "DAILY_JOURNAL_DASHBOARD_NORMALIZED_V732", "global_status": data.get("global_status") or ("JOURNAL_READY" if symbols else "NO_JOURNAL"), "symbols": symbols, "critical_issues": issues, "source": args.input}
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty: print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"DAILY_JOURNAL_NORMALIZE_OK | global_status={out['global_status']} | symbols={len(symbols)} | out={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
