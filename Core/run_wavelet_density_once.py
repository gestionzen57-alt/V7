from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_wavelet_density import WaveletDensityEngine


def parse_tfs(raw: str):
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.2 B4+ Wavelet Morlet density snapshot")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--tfs", default="1,5,15")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", default="output/dashboard_surface/wavelet.json")
    args = parser.parse_args()

    result = WaveletDensityEngine().compute(args.db, args.symbol, parse_tfs(args.tfs))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
