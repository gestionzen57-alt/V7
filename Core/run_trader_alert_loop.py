#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.6 — Trader Alert Loop

Runs the perception stack, then the alert gate.

Use this when trading:
    python run_trader_alert_loop.py --symbols GBPUSD,EURUSD,USDJPY --interval 20 --send-telegram

This does not spam:
- stack refreshes every interval
- alert gate emits only on meaningful transition / release / score jump / cooldown expiry
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _run(cmd: list[str], cwd: Path, *, echo: bool = False) -> int:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if echo and proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip(), file=sys.stderr)
    return proc.returncode


def run_once(args: argparse.Namespace, core: Path) -> int:
    py = sys.executable
    symbols = args.symbols

    stack_cmd = [
        py,
        "run_trader_perception_stack_once.py",
        "--symbols",
        symbols,
        "--table",
    ]

    gate_cmd = [
        py,
        "pf_trader_attention_alert_gate_once.py",
        "--symbols",
        symbols,
        "--cooldown-seconds",
        str(args.cooldown_seconds),
        "--repeat-after-seconds",
        str(args.repeat_after_seconds),
        "--release-threshold",
        str(args.release_threshold),
        "--loading-threshold",
        str(args.loading_threshold),
        "--score-jump",
        str(args.score_jump),
        "--pretty",
    ]

    if args.send_telegram:
        gate_cmd.append("--send-telegram")
    if args.bot_token:
        gate_cmd += ["--bot-token", args.bot_token]
    if args.chat_id:
        gate_cmd += ["--chat-id", args.chat_id]

    if args.show_table:
        print(f"POWERFLOW ALERT LOOP | {_stamp()} | symbols={symbols}")
        rc_stack = _run(stack_cmd, core, echo=True)
    else:
        rc_stack = _run(stack_cmd, core, echo=False)

    rc_gate = _run(gate_cmd, core, echo=True)
    return 0 if rc_stack == 0 and rc_gate == 0 else 1


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PowerFlow trader alert loop.")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--interval", type=int, default=20)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--send-telegram", action="store_true")
    parser.add_argument("--bot-token", default=None)
    parser.add_argument("--chat-id", default=None)
    parser.add_argument("--show-table", action="store_true")
    parser.add_argument("--cooldown-seconds", type=int, default=180)
    parser.add_argument("--repeat-after-seconds", type=int, default=900)
    parser.add_argument("--release-threshold", type=float, default=70.0)
    parser.add_argument("--loading-threshold", type=float, default=78.0)
    parser.add_argument("--score-jump", type=float, default=5.0)
    parser.add_argument("--core", default=None)
    args = parser.parse_args(list(argv) if argv is not None else None)

    core = Path(args.core).resolve() if args.core else Path(__file__).resolve().parent

    if args.once:
        return run_once(args, core)

    cycle = 0
    last_rc = 0
    try:
        while True:
            cycle += 1
            print(f"\n--- ALERT_LOOP_CYCLE {cycle} | {_stamp()} ---")
            last_rc = run_once(args, core)
            print("Ctrl+C to stop.")
            time.sleep(max(1, int(args.interval)))
    except KeyboardInterrupt:
        print(f"\nALERT_LOOP_STOPPED cycles={cycle}")
        return last_rc


if __name__ == "__main__":
    raise SystemExit(main())
