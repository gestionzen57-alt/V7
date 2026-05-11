# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from pf_regime_engine import compute_regime, regime_output_to_dict


def _default_out(symbol: str) -> str:
    return f"output/dashboard_surface/{symbol.upper()}/regime_legacy.json"


def _legacy_alias(symbol: str, src: Path) -> None:
    if symbol.upper() != "GBPUSD" or not src.exists():
        return
    legacy = Path("output/regime_legacy_state.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, legacy)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow HTF Regime Engine — single run")
    p.add_argument("--db", default="powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--tfs", default="60,240,1440,10080")
    p.add_argument("--bars", type=int, default=60)
    p.add_argument("--out", default=None)
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    symbol = args.symbol.upper()
    timeframes = [int(t.strip()) for t in args.tfs.split(",") if t.strip()]
    result = compute_regime(db_path=args.db, symbol=symbol, timeframes=timeframes, bars=args.bars)
    data = regime_output_to_dict(result)
    data.setdefault("meta", {})["symbol"] = symbol
    data.setdefault("meta", {})["method"] = "B1_LEGACY_HEURISTIC_SYMBOL_PARAMETRIC"
    data.setdefault("method", "B1_LEGACY_HEURISTIC")
    data.setdefault("symbol", symbol)
    out_path = Path(args.out or _default_out(symbol))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(data, indent=2 if args.pretty else None, ensure_ascii=False) + "\n", encoding="utf-8")
    _legacy_alias(symbol, out_path)
    print("REGIME_LEGACY_OK")
    print(f"symbol={symbol}")
    print(f"out={out_path}")
    print(f"regime={getattr(result, 'dominant_regime', None)}")
    print(f"confidence={getattr(result, 'confidence', None)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
