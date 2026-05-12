#!/usr/bin/env python3
"""Fast validation for Commando P2 M1 noise + context + dashboard output."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def run(cmd):
    print(">", " ".join(cmd))
    p = subprocess.run(cmd, text=True, capture_output=True)
    print(p.stdout)
    if p.stderr:
        print(p.stderr)
    if p.returncode != 0:
        raise SystemExit(p.returncode)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    args = parser.parse_args()

    run([sys.executable, "-m", "py_compile", "pf_m1_noise_ratio_probe.py", "run_m1_noise_ratio_once.py", "run_usdjpy_capture_diagnostic_once.py", "dashboard_inject_m1_context_card.py"])
    run([sys.executable, "run_m1_noise_ratio_once.py", "--db", args.db, "--symbol", args.symbol, "--output", "output/force_kinematics_state.json"])
    run([sys.executable, "run_m1_context_score_once.py", "--db", args.db, "--symbol", args.symbol, "--output", "output/m1_context_score.json"])
    run([sys.executable, "dashboard_normalize_m1_context.py", "--input", "output/m1_context_score.json", "--output", "output/dashboard_surface/m1_context_score.json"])
    run([sys.executable, "run_usdjpy_capture_diagnostic_once.py", "--db", args.db, "--symbol", "USDJPY", "--output", "output/usdjpy_capture_thin_diagnostic.json"])

    state = json.loads(Path("output/m1_context_score.json").read_text(encoding="utf-8"))
    print("M1_CONTEXT_SUMMARY")
    for cur, payload in state.get("currencies", {}).items():
        print(cur, payload.get("m1_context_score"), payload.get("exploitability"), payload.get("intervention_window"), payload.get("raw_context", {}).get("noise_ratio"))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
