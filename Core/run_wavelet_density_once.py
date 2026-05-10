"""Runner PowerFlow V7.2 — B4 Wavelet Density."""
from __future__ import annotations

import argparse
import json

from pf_wavelet_density import analyze_from_db, write_json

DEFAULT_DB = "Core/powerflow.db"
DEFAULT_OUTPUT = "output/wavelet_density.json"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow B4 Wavelet Density runner")
    p.add_argument("--db", default=DEFAULT_DB)
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--tf", "--timeframe", dest="timeframe", type=int, default=5)
    p.add_argument("--window", type=int, default=100)
    p.add_argument("--output", default=DEFAULT_OUTPUT)
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    payload = analyze_from_db(args.db, symbol=args.symbol, timeframe=args.timeframe, window=args.window)
    write_json(args.output, payload)
    if args.pretty:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
