"""
Runner — PowerFlow V6 FractalWindowEngine V0.1

LAB_004:
    python run_fractal_window_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --ltf-timeframes 1,5,15 --htf-timeframes 30,60,240 --visual-htf-story confirmed --out fractal_window_lab004.txt
"""

from __future__ import annotations

from pf_fractal_window_engine import main

if __name__ == "__main__":
    raise SystemExit(main())
