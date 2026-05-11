# -*- coding: utf-8 -*-
"""Runner one-shot — PowerFlow V7.2 Cross-Symbol Validation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_cross_symbol_validation import CrossSymbolValidator, write_cross_validation_state


def _parse_symbols(value: str) -> list[str]:
    return [s.strip().upper() for s in value.split(",") if s.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.2 — Cross-Symbol Validation")
    parser.add_argument("--db", default="powerflow.db", help="SQLite DB path")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY", help="CSV symbols")
    parser.add_argument("--timeframe", type=int, default=1, help="Primary TF in minutes")
    parser.add_argument("--bars", type=int, default=60, help="Bars per symbol")
    parser.add_argument("--out", default="output/dashboard_surface/cross_validation.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbols = _parse_symbols(args.symbols)
    validator = CrossSymbolValidator(timeframe=args.timeframe, bars=args.bars)
    state = validator.compute(args.db, symbols)
    write_cross_validation_state(state, args.out, pretty=args.pretty)
    cv = state.get("cross_validation", {})
    print("CROSS_SYMBOL_VALIDATION_OK")
    print(f"out={Path(args.out)}")
    print(f"symbols_used={cv.get('symbols_used')}")
    print(f"driver={cv.get('driver')}")
    print(f"confidence={cv.get('confidence')}")
    print(f"technical_risks={len(cv.get('technical_risks', []))}")
    if args.pretty:
        print(json.dumps(state, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
