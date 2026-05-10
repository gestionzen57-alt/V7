#!/usr/bin/env python3
"""
Runner — PowerFlow V7.2 M1 Episode Merger V0.4

Examples:
  python Core\run_lab_m1_episode_merger_v72_once.py --latest --pretty
  python Core\run_lab_m1_episode_merger_v72_once.py --lab-run output\lab_runs\20260510_145729_GBPUSD_0900_1100 --pretty
"""

from __future__ import annotations

from pf_lab_m1_episode_merger_v72 import main

if __name__ == "__main__":
    raise SystemExit(main())
