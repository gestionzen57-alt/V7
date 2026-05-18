from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_chain_contract_validator import run


def main() -> int:
    parser = argparse.ArgumentParser(description="T0172 B9 Live Chain Contract Validator V0")
    parser.add_argument("--core-root", default=".")
    parser.add_argument("--output-dir", default="outputs/b9_live_chain_contract_validator_v0")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    summary = run(args)
    if args.print_json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    state = summary.get("contract_state", "")
    if state.startswith("B9_LIVE_CHAIN_CONTRACT_BLOCKED_FORBIDDEN_LANGUAGE"):
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
