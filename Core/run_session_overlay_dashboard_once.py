#!/usr/bin/env python3
"""
PowerFlow V7.1 - Session Overlay runner
Standalone cockpit producer for output/session_overlay.json.

Computes the active FX session context from a UTC timestamp.
Does not read or write DB.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

DEFAULT_OUTPUT = Path("output") / "session_overlay.json"


def parse_timestamp(value: str) -> datetime:
    text = (value or "now").strip()
    if text.lower() in {"now", "utcnow"}:
        return datetime.now(timezone.utc)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def minutes_since(dt: datetime, hour: int, minute: int = 0, previous_day: bool = False) -> int:
    open_dt = dt.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if previous_day:
        open_dt -= timedelta(days=1)
    return int((dt - open_dt).total_seconds() // 60)


def session_phase(minutes: Optional[int], session: str) -> str:
    if session == "DEAD":
        return "DEAD_ZONE"
    if minutes is None:
        return "UNKNOWN"
    if -30 <= minutes < 0:
        return "PRE_OPEN"
    if 0 <= minutes < 60:
        return "IGNITION"
    return "MID_SESSION"


def compute_session(dt: datetime) -> Dict[str, Any]:
    h = dt.hour
    m = dt.minute
    minute_of_day = h * 60 + m

    # UTC session map aligned with V7.1 lexicon:
    # Asian 23:00-07:00, London 07:00-16:00, NY 12:00-21:00,
    # London/NY overlap 12:00-16:00, dead zone 21:00-23:00.
    if 12 * 60 <= minute_of_day < 16 * 60:
        session = "OVERLAP"
        overlap = "LONDON_NY"
        mins = minutes_since(dt, 12)
        bias = "EXPANSION_EXPECTED"
    elif 7 * 60 <= minute_of_day < 12 * 60:
        session = "LONDON"
        overlap = None
        mins = minutes_since(dt, 7)
        bias = "EXPANSION_EXPECTED"
    elif 16 * 60 <= minute_of_day < 21 * 60:
        session = "NY"
        overlap = None
        mins = minutes_since(dt, 12)
        bias = "ROTATION"
    elif minute_of_day >= 23 * 60:
        session = "ASIAN"
        overlap = None
        mins = minutes_since(dt, 23)
        bias = "COMPRESSION"
    elif minute_of_day < 7 * 60:
        session = "ASIAN"
        overlap = None
        mins = minutes_since(dt, 23, previous_day=True)
        bias = "COMPRESSION"
    else:
        session = "DEAD"
        overlap = None
        mins = minutes_since(dt, 21)
        bias = "COMPRESSION"

    phase = session_phase(mins, session)
    return {
        "engine": "pf_session_overlay_standalone",
        "version": "V7.1-runner-compat",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "timestamp_utc": dt.isoformat(),
        "session": session,
        "session_phase": phase,
        "minutes_since_open": mins,
        "session_bias": bias,
        "overlap": overlap,
        "technical_risks": [],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.1 session overlay runner")
    parser.add_argument("--timestamp", default="now")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = compute_session(parse_timestamp(args.timestamp))
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, ensure_ascii=False, indent=2 if args.pretty else None)
    output_path.write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
