"""
Runner — PowerFlow V6 FlowEventExtractor V0.2 Extended

Live V2 example:
    python run_flow_event_extractor_v02_extended_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --timeframes 1,5,15 --out flow_extended_v2_live.txt

Strict V2 only:
    python run_flow_event_extractor_v02_extended_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T18:00:00 --end 2026-05-04T21:15:00 --timeframes 1,5,15 --no-fallback-legacy
"""

from __future__ import annotations

from pf_flow_event_extractor_v02_extended import main

if __name__ == "__main__":
    raise SystemExit(main())
