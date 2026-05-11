#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from pf_currency_energy_probe import build_currency_energy_state, write_currency_energy_state


def _default_out(symbol: str) -> str:
    return f"output/dashboard_surface/{symbol.upper()}/energy.json"


def _legacy_alias(symbol: str, src: Path) -> None:
    if symbol.upper() != "GBPUSD" or not src.exists():
        return
    legacy = Path("output/currency_energy_state.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, legacy)


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow — Currency Energy Probe, symbol-parametric")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframe", type=int, default=15)
    parser.add_argument("--bars", type=int, default=50)
    parser.add_argument("--htf", default="15,30,60")
    parser.add_argument("--out", default=None)
    parser.add_argument("--pretty", action="store_true", default=True)
    parser.add_argument("--no-pretty", dest="pretty", action="store_false")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    try:
        htf_tfs = [int(x.strip()) for x in args.htf.split(",") if x.strip()]
    except ValueError:
        print(f"ERREUR --htf invalide: {args.htf}", file=sys.stderr)
        return 1
    if not htf_tfs:
        htf_tfs = [15, 30, 60]

    out_path = Path(args.out or _default_out(symbol))
    state = build_currency_energy_state(
        db_path=Path(args.db),
        symbol=symbol,
        timeframe=args.timeframe,
        bars=args.bars,
        htf_tfs=htf_tfs,
    )
    state.setdefault("meta", {})["symbol"] = symbol
    state.setdefault("meta", {})["method"] = "P1_ENERGY_SYMBOL_PARAMETRIC"
    write_currency_energy_state(state, out_path, pretty=args.pretty)
    _legacy_alias(symbol, out_path)
    print("CURRENCY_ENERGY_OK")
    print(f"symbol={symbol}")
    print(f"out={out_path}")
    if args.summary:
        print(f"top_energy={state.get('top_energy', {})}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
