from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_chain_orchestrator_dry_run import DEFAULT_RELATIVE_INPUTS, run


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="T0171 B9 Live Chain Orchestrator Dry Run V0")
    p.add_argument("--core-root", default=".")
    p.add_argument("--output-dir", default="outputs/b9_live_chain_orchestrator_dry_run_v0")
    p.add_argument("--strict", action="store_true", help="Exit non-zero when critical chain is blocked")
    for key in DEFAULT_RELATIVE_INPUTS:
        p.add_argument(f"--{key.replace('_','-')}-json", default="")
    p.add_argument("--print-json", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    overrides = {}
    for key in DEFAULT_RELATIVE_INPUTS:
        value = getattr(args, key + "_json")
        if value:
            overrides[key] = value
    summary = run(Path(args.core_root), Path(args.output_dir), overrides, strict=args.strict)
    if args.print_json:
        print(json.dumps({
            "version": summary["version"],
            "orchestrator_state": summary["orchestrator_state"],
            "candidate_id": summary.get("candidate_id", ""),
            "match_count": summary.get("match_count", 0),
            "top_match_film_id": summary.get("top_match_film_id", ""),
            "missing_steps": summary.get("missing_steps", []),
            "review_steps": summary.get("review_steps", []),
            "forbidden_language_hits": summary.get("forbidden_language_hits", []),
            "zip": summary.get("zip", ""),
        }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
