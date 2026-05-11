#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_cycle_orchestrator.py
PowerFlow V7.2 - Runner / Daemon for pf_cycle_orchestrator.py
"""

from __future__ import annotations

import argparse
import signal
import sys
import time
from pathlib import Path

CORE_DIR = Path(__file__).resolve().parent
if str(CORE_DIR) not in sys.path:
    sys.path.insert(0, str(CORE_DIR))

from pf_cycle_orchestrator import ORCHESTRATOR_VERSION, parse_tfs, normalize_symbols, run_cycle


RUNNER_VERSION = "1.0.1-p0"
DEFAULT_INTERVAL_SECONDS = 300
_running = True


def _handle_signal(signum, frame):
    global _running
    print(f"[RUN] signal={signum} received; stop requested after current cycle", flush=True)
    _running = False


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="PowerFlow V7.2 - Cycle Orchestrator Runner")
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--once", action="store_true")
    mode.add_argument("--daemon", action="store_true")
    p.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_SECONDS)
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--symbols", "--symbol", dest="symbols", default="GBPUSD")
    p.add_argument("--tfs", default="1,5,15,30,60,240")
    p.add_argument("--since", default=None)
    p.add_argument("--output-dir", default="output")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--pretty", action="store_true")
    return p.parse_args(argv)


def run_once(args, cycle_id):
    symbols = normalize_symbols(args.symbols)
    tfs = parse_tfs(args.tfs)
    print(f"[RUN] PowerFlow Orchestrator V{ORCHESTRATOR_VERSION} runner={RUNNER_VERSION} cycle={cycle_id} symbols={symbols} db={args.db}", flush=True)
    report = run_cycle(cycle_id=cycle_id, symbols=symbols, db_path=args.db, tfs=tfs, since=args.since, output_dir=args.output_dir, dry_run=args.dry_run, pretty=True)
    print(f"[RUN] cycle={cycle_id} status={report.cycle_status} ok={report.steps_ok} failed={report.steps_failed} skipped={report.steps_skipped} duration={report.total_duration_seconds:.2f}s", flush=True)
    return report


def main(argv=None):
    args = parse_args(argv)

    if args.once:
        report = run_once(args, cycle_id=1)
        return 0 if report.cycle_status in {"COMPLETE", "PARTIAL"} else 1

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    cycle_id = 1
    print(f"[RUN] daemon start interval={args.interval}s", flush=True)

    while _running:
        t0 = time.perf_counter()
        try:
            run_once(args, cycle_id=cycle_id)
        except Exception as exc:
            print(f"[RUN] CRITICAL cycle={cycle_id}: {type(exc).__name__}: {exc}", flush=True)

        cycle_id += 1
        elapsed = time.perf_counter() - t0
        wait = max(0.0, args.interval - elapsed)
        if wait > 0 and _running:
            print(f"[RUN] next cycle in {wait:.0f}s", flush=True)
            time.sleep(wait)

    print(f"[RUN] daemon stopped after {cycle_id - 1} cycle(s)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
