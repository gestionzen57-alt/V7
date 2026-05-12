#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Sequence


def now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def classify_sweep_from_interaction(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    name = str(item.get("level") or "")
    state = str(item.get("interaction_state") or "")
    if state.startswith("CONTEXT_") or state == "UNTESTED":
        return None
    price = item.get("price")
    robustness = float(item.get("robustness") or 0.0)
    is_high = "HIGH" in name
    is_low = "LOW" in name
    if not (is_high or is_low):
        return None

    if is_high and state == "REJECTED_FROM_ABOVE":
        status = "SWEEP_REJECTED_CONFIRMED" if robustness >= 0.55 else "SWEEP_CANDIDATE"
        return {"sweep_type": "HIGH_SWEEP", "status": status, "level": name, "price": price, "source": item.get("source"), "intent_hint": "SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP", "robustness": round(robustness, 3), "evidence": item}
    if is_low and state == "REJECTED_FROM_BELOW":
        status = "SWEEP_REJECTED_CONFIRMED" if robustness >= 0.55 else "SWEEP_CANDIDATE"
        return {"sweep_type": "LOW_SWEEP", "status": status, "level": name, "price": price, "source": item.get("source"), "intent_hint": "LONG_ACCUMULATION_OR_STOP_HUNT", "robustness": round(robustness, 3), "evidence": item}
    if is_high and state == "ACCEPTED_ABOVE":
        return {"sweep_type": "HIGH_BREAK", "status": "SWEEP_ACCEPTED_INVALIDATED", "level": name, "price": price, "source": item.get("source"), "intent_hint": "BREAK_ACCEPTANCE_ABOVE", "robustness": round(robustness, 3), "evidence": item}
    if is_low and state == "ACCEPTED_BELOW":
        return {"sweep_type": "LOW_BREAK", "status": "SWEEP_ACCEPTED_INVALIDATED", "level": name, "price": price, "source": item.get("source"), "intent_hint": "BREAK_ACCEPTANCE_BELOW", "robustness": round(robustness, 3), "evidence": item}
    if state in ("PIERCED", "TOUCHED"):
        return {"sweep_type": "HIGH_LEVEL_TEST" if is_high else "LOW_LEVEL_TEST", "status": "SWEEP_CANDIDATE", "level": name, "price": price, "source": item.get("source"), "intent_hint": "WAIT_FOR_REJECTION_OR_ACCEPTANCE", "robustness": round(robustness, 3), "evidence": item}
    return None


def build_sweep_report(level_report: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    sweeps = []
    for item in level_report.get("interactions") or []:
        if isinstance(item, dict):
            sweep = classify_sweep_from_interaction(item)
            if sweep:
                sweeps.append(sweep)
    confirmed = [s for s in sweeps if s.get("status") == "SWEEP_REJECTED_CONFIRMED"]
    invalidated = [s for s in sweeps if s.get("status") == "SWEEP_ACCEPTED_INVALIDATED"]
    candidates = [s for s in sweeps if s.get("status") == "SWEEP_CANDIDATE"]
    if confirmed:
        state = "CONFIRMED_SWEEP_PRESENT"
    elif invalidated:
        state = "BREAK_ACCEPTANCE_PRESENT"
    elif candidates:
        state = "SWEEP_CANDIDATES_ONLY"
    else:
        state = "NO_SWEEP_CONTEXT"
    return {"timestamp_utc": now_utc_iso(), "symbol": symbol.upper(), "method": "DAILY_SWEEP_CLASSIFIER_V732", "sweep_state": state, "sweeps": sweeps, "counts": {"confirmed": len(confirmed), "candidate": len(candidates), "invalidated": len(invalidated), "total": len(sweeps)}, "technical_risks": level_report.get("technical_risks", []), "note": "Sweep classifier separates candidate, confirmed rejection and accepted break."}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--level-report", default=None)
    parser.add_argument("--output", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)
    symbol = args.symbol.upper()
    level_path = Path(args.level_report) if args.level_report else Path("output/dashboard_surface") / symbol / "daily_level_interaction.json"
    out = Path(args.output) if args.output else Path("output/dashboard_surface") / symbol / "daily_sweep_report.json"
    report = build_sweep_report(load_json(level_path), symbol)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty: print(json.dumps(report, indent=2, ensure_ascii=False))
    print(f"DAILY_SWEEP_CLASSIFIER_OK | symbol={symbol} | state={report['sweep_state']} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
