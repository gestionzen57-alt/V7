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


def deep_get(data: Dict[str, Any], *paths: str, default: Any = None) -> Any:
    for path in paths:
        obj: Any = data
        ok = True
        for part in path.split("."):
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                ok = False
                break
        if ok and obj not in (None, ""):
            return obj
    return default


def normalize_symbol(symbol: str) -> Dict[str, Any]:
    root = Path("output/dashboard_surface") / symbol
    brief = load_json(root / "powerflow_live_brief.json")
    decision = load_json(root / "live_decision.json")
    cockpit_txt = root / "cockpit_live_status.txt"
    brief_txt = root / "powerflow_live_brief.txt"

    txt_preview = brief_txt.read_text(encoding="utf-8", errors="replace")[:1200] if brief_txt.exists() else ""

    status = deep_get(brief, "status", "action", "state", default=None)
    synthesis = deep_get(brief, "synthesis", "reading_state", default=None)
    reading = deep_get(brief, "reading", default=None)

    packet = deep_get(brief, "live.packet", "packet", default=deep_get(decision, "packet", "memory.packet", default=None))
    level = deep_get(brief, "live.level", "level", default=deep_get(decision, "level", "memory.level", default=None))
    bias = deep_get(brief, "live.bias", "bias", default=deep_get(decision, "bias", "memory.bias", default=None))
    tf = deep_get(brief, "live.tf", "tf", default=deep_get(decision, "tf", "memory.tf", default=None))
    score = deep_get(brief, "live.score", "score", default=deep_get(decision, "score", "memory.score", default=None))
    live_count = deep_get(brief, "live.live", "live_count", default=deep_get(decision, "live_count", default=None))
    old_count = deep_get(brief, "live.old", "old_count", "expired_count", default=deep_get(decision, "expired_count", default=None))

    if not status and "ALERT_READY" in txt_preview:
        status = "ALERT_READY"
    if not synthesis:
        first_line = txt_preview.splitlines()[0] if txt_preview else ""
        parts = [p.strip() for p in first_line.split("|")]
        if len(parts) >= 3:
            status = status or parts[1]
            synthesis = parts[2]

    risks = deep_get(brief, "technical_risks", "risks", default=[])
    if not isinstance(risks, list):
        risks = [str(risks)]

    cockpit_status = cockpit_txt.read_text(encoding="utf-8", errors="replace") if cockpit_txt.exists() else ""

    return {
        "symbol": symbol,
        "status": status or "UNKNOWN",
        "synthesis": synthesis or "UNKNOWN",
        "reading": reading or "",
        "packet": packet or "NONE",
        "level": level or "NONE",
        "bias": bias or "NONE",
        "tf": tf,
        "score": score,
        "live_count": live_count,
        "old_count": old_count,
        "risks": risks,
        "cockpit_status_preview": cockpit_status[:500],
        "brief_preview": txt_preview,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="GBPUSD")
    parser.add_argument("--output", default="output/dashboard_surface/live_brief_dashboard.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    rows = [normalize_symbol(symbol) for symbol in symbols]

    if any(str(r.get("status")).upper() in {"WAKE_TRADER", "ALERT_READY", "HOT", "ACTIVE"} for r in rows):
        global_status = "LIVE_ATTENTION_PRESENT"
    elif any(str(r.get("level")).upper() == "HOT" for r in rows):
        global_status = "HOT_PACKET_MEMORY_PRESENT"
    else:
        global_status = "NO_LIVE_ALERT"

    issues = []
    for row in rows:
        for r in row.get("risks", []):
            if r not in issues:
                issues.append(r)

    out = {
        "method": "LIVE_BRIEF_DASHBOARD_NORMALIZED_V733",
        "global_status": global_status,
        "symbols": rows,
        "critical_issues": issues,
        "source": "output/dashboard_surface/<SYMBOL>/powerflow_live_brief.json",
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"LIVE_BRIEF_NORMALIZE_OK | global_status={global_status} | symbols={len(rows)} | out={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
