from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_chain_runtime_missing_input_resolver import run


def main() -> int:
    parser = argparse.ArgumentParser(description="T0173 B9 live chain missing input resolver")
    parser.add_argument("--core-root", default=".")
    parser.add_argument("--contract-json", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()
    summary = run(core_root=args.core_root, contract_json=args.contract_json, output_dir=args.output_dir)
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
