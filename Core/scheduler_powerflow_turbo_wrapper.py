#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — Turbo cycle wrapper.

Runs:
1. scheduler_powerflow.py --once
2. data health monitor
3. flow ontology cycle
4. signal adaptive profiles
5. signal adaptive normalizer

This wrapper does not replace the existing scheduler unless you explicitly point
Windows Task Scheduler to it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List


def load_symbols(default: str) -> str:
    cfg = Path("scheduler_config.json")
    if not cfg.exists():
        return default
    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
        symbols = data.get("symbols")
        if isinstance(symbols, list) and symbols:
            return ",".join(str(s).upper() for s in symbols)
    except Exception:
        pass
    return default


def run(cmd: List[str]) -> int:
    print(">", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, text=True)
    return int(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run PowerFlow turbo scheduler cycle.")
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--skip-scheduler", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbols = args.symbols or load_symbols("GBPUSD,EURUSD,USDJPY")

    steps: List[List[str]] = []

    if not args.skip_scheduler:
        steps.append([sys.executable, "scheduler_powerflow.py", "--once", "--symbols", symbols])

    steps.extend([
        [sys.executable, "run_data_health_monitor_once.py", "--db", args.db, "--symbols", symbols, "--output", "output/data_health_monitor.json"],
        [sys.executable, "dashboard_normalize_data_health.py", "--input", "output/data_health_monitor.json", "--output", "output/dashboard_surface/data_health.json"],
        [sys.executable, "run_flow_ontology_cycle_once.py", "--symbols", symbols],
        [sys.executable, "run_signal_adaptive_all_once.py", "--symbols", symbols, "--data-health", "output/data_health_monitor.json"],
        [sys.executable, "dashboard_normalize_signal_adaptive.py", "--input", "output/dashboard_surface/signal_adaptive_profiles.json", "--output", "output/dashboard_surface/signal_adaptive.json"],
    ])

    for step in steps:
        if args.pretty:
            step.append("--pretty")
        code = run(step)
        if code != 0:
            print(f"TURBO_CYCLE_FAIL returncode={code} step={' '.join(step)}", file=sys.stderr)
            return code

    print(f"TURBO_CYCLE_OK | symbols={symbols}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
