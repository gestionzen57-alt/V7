"""
run_regime_engine_once.py — PowerFlow V6
Runner ponctuel pour pf_regime_engine.py.

Usage:
  python run_regime_engine_once.py --db powerflow.db --symbol GBPUSD
  python run_regime_engine_once.py --db powerflow.db --tfs "60,240,1440" --bars 80
  python run_regime_engine_once.py --db powerflow.db --out output/regime_state.json --pretty
"""

import argparse
import json
import sys
from pathlib import Path

# Allow running from any working directory
sys.path.insert(0, str(Path(__file__).parent))

from pf_regime_engine import compute_regime, regime_output_to_dict


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow HTF Regime Engine — single run")
    p.add_argument("--db",     default="powerflow.db", help="Path to powerflow.db")
    p.add_argument("--symbol", default="GBPUSD",       help="Symbol e.g. GBPUSD")
    p.add_argument("--tfs",    default="60,240,1440,10080",
                   help="Timeframe list in minutes, comma-separated")
    p.add_argument("--bars",   type=int, default=60,   help="Bars per TF lookback")
    p.add_argument("--out",    default=None,            help="JSON output path (optional)")
    p.add_argument("--pretty", action="store_true",     help="Pretty-print JSON")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    timeframes = [int(t.strip()) for t in args.tfs.split(",") if t.strip()]

    print(f"[regime] DB={args.db} symbol={args.symbol} tfs={timeframes} bars={args.bars}")

    result = compute_regime(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=timeframes,
        bars=args.bars,
    )

    data = regime_output_to_dict(result)

    indent = 2 if args.pretty else None
    output = json.dumps(data, indent=indent, ensure_ascii=False)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(output, encoding="utf-8")
        print(f"[regime] → {out_path}")
    else:
        print(output)

    # Summary
    print()
    print(f"  REGIME    : {result.dominant_regime}")
    print(f"  CONFIDENCE: {result.confidence:.2f}")
    print(f"  COLOR     : {result.regime_color}")
    print(f"  HTF STACK :")
    for k, v in result.htf_context_stack.items():
        print(f"    {k:4s} → {v}")
    if result.notes:
        print(f"  NOTES: {result.notes}")


if __name__ == "__main__":
    main()
