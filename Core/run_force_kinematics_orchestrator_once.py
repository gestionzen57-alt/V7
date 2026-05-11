#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_force_kinematics_orchestrator_once.py
Compatibility wrapper for PowerFlow V7.2 orchestrator.

Why:
- run_force_kinematics_once.py requires --start and --end.
- pf_cycle_orchestrator.py expects a runner that can be called with --db/--symbol/--output.
- This wrapper computes a tactical UTC window and delegates to the real runner.

No DB write. No capture_bridge modification.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


CORE_DIR = Path(__file__).resolve().parent
REAL_RUNNER = CORE_DIR / "run_force_kinematics_once.py"


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "+00:00")


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="PowerFlow B3 Kinematics orchestrator wrapper")
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--lookback-minutes", type=int, default=180)
    p.add_argument("--timeframes", default="1,5,15,30,60")
    p.add_argument("--output", "--out", dest="out", default="output/kinematics_GBPUSD.json")
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args(argv)

    if not REAL_RUNNER.exists():
        print(f"MISSING_REAL_RUNNER: {REAL_RUNNER}", file=sys.stderr)
        return 2

    end = datetime.now(timezone.utc)
    start = end - timedelta(minutes=max(1, args.lookback_minutes))

    out_path = args.out.replace("{symbol}", args.symbol)

    cmd = [
        sys.executable,
        str(REAL_RUNNER),
        "--db", args.db,
        "--symbol", args.symbol,
        "--start", iso_utc(start),
        "--end", iso_utc(end),
        "--timeframes", args.timeframes,
        "--out", out_path,
        "--json",
    ]

    proc = subprocess.run(
        cmd,
        cwd=str(CORE_DIR),
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
