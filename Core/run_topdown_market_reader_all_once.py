#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from pf_daily_market_reader import build_daily_market_reader, write_daily_market_outputs, today_utc_date
from pf_price_schema_probe import probe_price_schema


def parse_symbols(raw: str) -> list[str]:
    return [s.strip().upper() for s in raw.split(",") if s.strip()]


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run PowerFlow V7.3 top-down market reader for multiple symbols.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--date", default=None)
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output", default="output/dashboard_surface/topdown_market_reader.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbols = parse_symbols(args.symbols)
    date = args.date or today_utc_date()
    schema = probe_price_schema(args.db, symbols=symbols)
    results = []
    for sym in symbols:
        state = build_daily_market_reader(args.db, symbol=sym, date=date, base_dir=args.base_dir, schema=schema)
        symbol_json = f"output/dashboard_surface/{sym}/topdown_market_reading.json"
        symbol_md = f"output/daily_journal/{sym}/{date}_topdown_market_reading.md"
        write_daily_market_outputs(state, output_json=symbol_json, output_md=symbol_md, pretty=True)
        archive_json = Path("output") / "daily_journal" / sym / f"{date}_topdown_market_reading.json"
        archive_json.parent.mkdir(parents=True, exist_ok=True)
        archive_json.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
        results.append(state)

    summary = {
        "timestamp_utc": results[0].get("timestamp_utc") if results else None,
        "method": "TOPDOWN_MARKET_READER_ALL_V73",
        "date": date,
        "symbols": {r["symbol"]: r for r in results},
        "technical_risks": sorted(set(x for r in results for x in r.get("technical_risks", []))),
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        status = " | ".join(
            f"{r['symbol']} window={r.get('surface_reading',{}).get('window')} flux={r.get('surface_reading',{}).get('flux')}"
            for r in results
        )
        print(f"TOPDOWN_MARKET_READER_ALL_OK | {status} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
