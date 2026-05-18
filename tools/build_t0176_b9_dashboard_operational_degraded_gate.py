from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t0176_b9_dashboard_operational_degraded_gate import build_operational_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-root", default=".")
    parser.add_argument("--t0175-contract-json", default=None)
    parser.add_argument("--t0175-missing-csv", default=None)
    parser.add_argument("--output-dir", default="outputs/t0176_b9_dashboard_operational_degraded_gate_v0")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    payload = build_operational_gate(
        core_root=Path(args.core_root),
        t0175_contract_json=Path(args.t0175_contract_json) if args.t0175_contract_json else None,
        t0175_missing_csv=Path(args.t0175_missing_csv) if args.t0175_missing_csv else None,
        output_dir=Path(args.output_dir),
        allow_degraded=not args.strict,
    )
    if args.print_json:
        print(json.dumps({
            "version": payload["version"],
            "surface_state": payload["surface_state"],
            "lock_state_in": payload["lock_state_in"],
            "required_missing_count": payload["required_missing_count"],
            "optional_missing_count": payload["optional_missing_count"],
            "hard_block_reasons": payload["hard_block_reasons"],
            "forbidden_language_hits": payload["forbidden_language_hits"],
            "output_dir": str(Path(args.output_dir)),
        }, ensure_ascii=False, indent=2))
    return 1 if payload["surface_state"].startswith("DASHBOARD_OPERATIONAL_BLOCKED_HARD") else 0


if __name__ == "__main__":
    raise SystemExit(main())
