from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_hmm_regime_engine import DEFAULT_HMM_TIMEFRAMES, HMMRegimeEngine


def _parse_tfs(raw: str):
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.2 B1+ HMM multi-timeframe regime snapshot")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--tfs", default=",".join(str(x) for x in DEFAULT_HMM_TIMEFRAMES), help="Comma-separated tactical TF stack. Default: 60,30,15")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", default="output/dashboard_surface/regime_hmm.json")
    args = parser.parse_args()

    result = HMMRegimeEngine().compute(args.db, args.symbol, timeframes=_parse_tfs(args.tfs))
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
