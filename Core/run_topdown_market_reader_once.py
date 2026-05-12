#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional, Sequence

from pf_daily_market_reader import build_daily_market_reader, write_daily_market_outputs, today_utc_date


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Run PowerFlow V7.3 top-down market reader once for one symbol.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--date", default=None, help="UTC date YYYY-MM-DD. Default: today UTC.")
    parser.add_argument("--base-dir", default=".")
    parser.add_argument("--output", default=None)
    parser.add_argument("--markdown-output", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbol = args.symbol.upper()
    date = args.date or today_utc_date()
    output = args.output or f"output/dashboard_surface/{symbol}/topdown_market_reading.json"
    markdown_output = args.markdown_output or f"output/daily_journal/{symbol}/{date}_topdown_market_reading.md"

    state = build_daily_market_reader(args.db, symbol=symbol, date=date, base_dir=args.base_dir)
    write_daily_market_outputs(state, output_json=output, output_md=markdown_output, pretty=True)
    # Also write canonical daily JSON for archive.
    archive_json = Path("output") / "daily_journal" / symbol / f"{date}_topdown_market_reading.json"
    archive_json.parent.mkdir(parents=True, exist_ok=True)
    archive_json.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        surf = state.get("surface_reading", {})
        print(
            f"TOPDOWN_MARKET_READER_OK | symbol={symbol} | window={surf.get('window')} | "
            f"flux={surf.get('flux')} | out={output} | md={markdown_output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
