# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from pf_temporal_node_state import build_temporal_node_state, write_temporal_node_state


def _parse_timeframes(value: str) -> list[int]:
    out: list[int] = []
    for part in value.split(","):
        part = part.strip().upper()
        if not part:
            continue
        if part.startswith("M") and part[1:].isdigit():
            out.append(int(part[1:]))
        elif part.startswith("H") and part[1:].isdigit():
            out.append(int(part[1:]) * 60)
        elif part.isdigit():
            out.append(int(part))
        else:
            raise argparse.ArgumentTypeError(f"Invalid timeframe: {part}")
    return out


def _default_out(symbol: str) -> str:
    return f"output/dashboard_surface/{symbol.upper()}/node.json"


def _write_legacy_alias(symbol: str, src: Path) -> None:
    if symbol.upper() != "GBPUSD" or not src.exists():
        return
    legacy = Path("output/temporal_node_state.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, legacy)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PowerFlow temporal node state, symbol-parametric")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--recent-minutes", type=int, default=180)
    parser.add_argument("--timeframes", type=_parse_timeframes, default=_parse_timeframes("1,5,15,30,60"))
    parser.add_argument("--telegram-mode", default="SCALPING", choices=["OFF", "WATCH", "SCALPING", "HOT_ONLY"])
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-rows", type=int, default=5000)
    parser.add_argument("--min-score", type=float, default=3.0)
    parser.add_argument("--visual-htf-story", default="unknown", choices=["unknown", "confirmed", "rejected"])
    parser.add_argument("--no-extended", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    out_path = Path(args.out or _default_out(symbol))
    state = build_temporal_node_state(
        db_path=args.db,
        symbol=symbol,
        recent_minutes=args.recent_minutes,
        timeframes=args.timeframes,
        telegram_mode=args.telegram_mode,
        max_rows=args.max_rows,
        min_score=args.min_score,
        visual_htf_story=args.visual_htf_story,
        include_extended=not args.no_extended,
    )
    state.setdefault("meta", {})["symbol"] = symbol
    state.setdefault("meta", {})["method"] = "TEMPORAL_NODE_SYMBOL_PARAMETRIC"
    write_temporal_node_state(state, out_path, pretty=args.pretty)
    _write_legacy_alias(symbol, out_path)
    summary = state.get("node_summary", {})
    print("TEMPORAL_NODE_STATE_OK")
    print(f"symbol={symbol}")
    print(f"out={out_path}")
    print(f"active_count={summary.get('active_count')}")
    print(f"highest_level={summary.get('highest_level')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
