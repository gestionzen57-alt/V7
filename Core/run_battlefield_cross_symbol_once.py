#!/usr/bin/env python3
"""
T009 Phase 2C.3 - Cross-symbol battlefield coalition detection.

Example:
python run_battlefield_cross_symbol_once.py --symbols GBPUSD,EURUSD,USDJPY --lookback-min 30 --output output
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pf_battlefield_flux_cross_symbol import CrossSymbolCoalitionDetector


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="T009 Phase 2C.3 - Cross-symbol coalition detection with pair driver context"
    )
    parser.add_argument(
        "--symbols",
        required=True,
        help="Comma-separated symbols, e.g. GBPUSD,EURUSD,USDJPY",
    )
    parser.add_argument("--lookback-min", type=int, default=30)
    parser.add_argument("--output", default="output")
    parser.add_argument("--db-path", default=None, help="Optional path to powerflow.db")

    args = parser.parse_args(argv)
    symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()]

    if len(symbols) < 2:
        print("ERROR: need at least 2 symbols for cross-symbol analysis")
        return 1

    detector = CrossSymbolCoalitionDetector(db_path=args.db_path)
    coalition_state = detector.detect_coalition(symbols, args.lookback_min)

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "battlefield_cross_symbol_coalition.json"
    output_path.write_text(
        json.dumps(coalition_state, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Coalition state: {output_path}")
    print(f"Coalition detected: {coalition_state['coalition_detected']}")
    print(f"Coalition strength: {coalition_state['coalition_strength']:.2f}")
    print(f"Leader: {coalition_state['leader']}")
    print(f"Convergence zones: {len(coalition_state['convergence_zones'])}")
    print(f"Data quality: {coalition_state['confidence']:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
