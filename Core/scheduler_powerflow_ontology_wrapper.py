#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — Scheduler wrapper with Flow Ontology integration.

Safe integration strategy:
- Run existing scheduler_powerflow.py in --once mode.
- Then run run_flow_ontology_cycle_once.py.
- Designed for Windows Task Scheduler every 5 minutes.

This avoids brittle direct patching of scheduler_powerflow.py.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import List


def load_config_symbols(default: str) -> str:
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
    parser = argparse.ArgumentParser(description="Run PowerFlow scheduler once, then Flow Ontology cycle.")
    parser.add_argument("--symbols", default=None, help="Comma-separated symbols. Defaults to scheduler_config.json.")
    parser.add_argument("--skip-scheduler", action="store_true", help="Only run ontology cycle.")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbols = args.symbols or load_config_symbols("GBPUSD,EURUSD,USDJPY")

    if not args.skip_scheduler:
        code = run([sys.executable, "scheduler_powerflow.py", "--once", "--symbols", symbols])
        if code != 0:
            print(f"SCHEDULER_WRAPPER_SCHEDULER_FAIL returncode={code}", file=sys.stderr)
            return code

    cmd = [sys.executable, "run_flow_ontology_cycle_once.py", "--symbols", symbols]
    if args.pretty:
        cmd.append("--pretty")
    code = run(cmd)
    if code != 0:
        print(f"SCHEDULER_WRAPPER_ONTOLOGY_FAIL returncode={code}", file=sys.stderr)
        return code

    print(f"SCHEDULER_WITH_ONTOLOGY_OK | symbols={symbols}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
