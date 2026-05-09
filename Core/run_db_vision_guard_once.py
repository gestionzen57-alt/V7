"""
Runner — PowerFlow V6 DBVisionGuard V0.1

Usage:
    python run_db_vision_guard_once.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60,240 --recent-minutes 60
"""

from __future__ import annotations

from pf_db_vision_guard import main

if __name__ == "__main__":
    raise SystemExit(main())
