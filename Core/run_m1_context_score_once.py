#!/usr/bin/env python3
"""Run PowerFlow M1_CONTEXT_SCORE once."""

from __future__ import annotations

import argparse
import json

from pf_m1_context_score import M1ContextInputs, compute_m1_context_score, write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute PowerFlow M1_CONTEXT_SCORE once.")
    parser.add_argument("--db", default="powerflow.db", help="SQLite DB path")
    parser.add_argument("--symbol", default="GBPUSD", help="Symbol, e.g. GBPUSD")
    parser.add_argument("--output", "--out", dest="output", default="output/m1_context_score.json")
    parser.add_argument("--kinematics", default=None, help="force_kinematics_state.json path")
    parser.add_argument("--temporal-node", default=None, help="temporal_node_state/node.json path")
    parser.add_argument("--session-overlay", default=None, help="session_overlay.json path")
    parser.add_argument("--regime-hmm", default=None, help="regime_hmm.json path")
    parser.add_argument("--regime-legacy", default=None, help="regime_legacy.json path")
    parser.add_argument("--bars", type=int, default=120)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    inputs = M1ContextInputs(
        db_path=args.db,
        symbol=args.symbol,
        kinematics_path=args.kinematics,
        temporal_node_path=args.temporal_node,
        session_overlay_path=args.session_overlay,
        regime_hmm_path=args.regime_hmm,
        regime_legacy_path=args.regime_legacy,
        bars=args.bars,
    )

    state = compute_m1_context_score(inputs)
    write_json(state, args.output)

    if args.pretty:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        currencies = state.get("currencies", {})
        labels = ",".join(f"{c}:{v.get('exploitability')}" for c, v in currencies.items())
        print(f"M1_CONTEXT_SCORE_OK | symbol={args.symbol.upper()} | out={args.output} | currencies={labels}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
