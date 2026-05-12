#!/usr/bin/env python3
"""
Run SIGNAL_ADAPTIVE_PROFILE for multiple symbols.

Writes:
- output/dashboard_surface/{symbol}/signal_adaptive_profile.json
- output/dashboard_surface/signal_adaptive_profiles.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_signal_adaptive_profile import compute_profiles, parse_symbols, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Run SIGNAL_ADAPTIVE_PROFILE for multiple symbols.")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--data-health", default="output/data_health_monitor.json")
    parser.add_argument("--output", "--out", dest="output", default="output/dashboard_surface/signal_adaptive_profiles.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbols = parse_symbols(args.symbols)
    multi = compute_profiles(data_health_path=args.data_health, symbols=symbols)

    for symbol, profile in multi["symbols"].items():
        write_json(profile, Path("output") / "dashboard_surface" / symbol / "signal_adaptive_profile.json")

    write_json(multi, args.output)

    if args.pretty:
        print(json.dumps(multi, indent=2, ensure_ascii=False))
    else:
        compact = " | ".join(
            f"{s} mode={p.get('mode')} conf={p.get('context_confidence')}"
            for s, p in multi["symbols"].items()
        )
        print(f"SIGNAL_ADAPTIVE_ALL_OK | {compact} | out={args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
