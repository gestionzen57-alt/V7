"""
Runner — PowerFlow V6 SceneNamer V0.1

LAB_004 example:
    python run_scene_report_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --timeframes 1,5,15 --out scene_report_lab004.txt
"""

from __future__ import annotations

from pf_scene_namer import main

if __name__ == "__main__":
    raise SystemExit(main())
