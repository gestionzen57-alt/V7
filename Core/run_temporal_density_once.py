# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from pf_temporal_density import compute_temporal_density_multi, format_density_summary

CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]


def _default_out(symbol: str) -> str:
    return f"output/temporal_density_state_{symbol.upper()}.json"


def _legacy_alias(symbol: str, src: Path) -> None:
    if symbol.upper() != "GBPUSD" or not src.exists():
        return
    legacy = Path("output/temporal_density_state.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, legacy)


def main() -> int:
    p = argparse.ArgumentParser(description="PowerFlow V7.2 — B4 Temporal Density, symbol-parametric")
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--tfs", default="1,5,15")
    p.add_argument("--bars", type=int, default=30)
    p.add_argument("--lookback", type=int, default=None)
    p.add_argument("--out", default=None)
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--summary", action="store_true")
    args = p.parse_args()
    symbol = args.symbol.upper()
    tfs = [int(x) for x in args.tfs.split(",") if x.strip()]
    try:
        results = compute_temporal_density_multi(
            db_path=args.db,
            currencies=CURRENCIES,
            timeframes=tfs,
            bars=args.bars,
            lookback_min=args.lookback,
            symbol=symbol,
        )
        summary = format_density_summary(results, symbol=symbol)
    except TypeError:
        raise RuntimeError(
            "pf_temporal_density.py is not symbol-parametric yet. "
            "Deploy PATCHED_MODULES/pf_temporal_density.py before this runner."
        )
    out_path = Path(args.out or _default_out(symbol))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2 if args.pretty else None, ensure_ascii=False) + "\n", encoding="utf-8")
    _legacy_alias(symbol, out_path)
    if args.summary:
        print("TEMPORAL_DENSITY_OK")
        print(f"symbol={symbol}")
        print(f"compressing={summary.get('compression_count')}")
    print(f"out={out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
