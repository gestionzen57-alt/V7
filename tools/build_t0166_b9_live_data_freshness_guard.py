from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_data_freshness_guard import build_and_write


def main() -> int:
    parser = argparse.ArgumentParser(description="T0166 — B9 Live Data Freshness Guard V0")
    parser.add_argument("--core-root", default=".")
    parser.add_argument("--powerflow-db", default="")
    parser.add_argument("--tick-archive-db", default="")
    parser.add_argument("--live-candidate-json", default="")
    parser.add_argument("--output-dir", default="outputs/b9_live_data_freshness_guard_v0")
    parser.add_argument("--freshness-seconds", type=int, default=300)
    parser.add_argument("--now-iso", default="")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args()

    result, paths = build_and_write(
        core_root=Path(args.core_root),
        output_dir=Path(args.output_dir),
        powerflow_db=Path(args.powerflow_db) if args.powerflow_db else None,
        tick_archive_db=Path(args.tick_archive_db) if args.tick_archive_db else None,
        live_candidate_json=Path(args.live_candidate_json) if args.live_candidate_json else None,
        freshness_seconds=args.freshness_seconds,
        now_iso=args.now_iso or None,
    )
    summary = {
        "version": result.version,
        "guard_state": result.guard_state,
        "force_snapshots_v2_rows": result.force_snapshots_v2_rows,
        "tick_stream_rows": result.tick_stream_rows,
        "live_candidate_state": result.live_candidate_state,
        "live_candidate_source_quality_state": result.live_candidate_source_quality_state,
        "live_candidate_raw_texture_state": result.live_candidate_raw_texture_state,
        "forbidden_language_hits": result.forbidden_language_hits,
        "zip": paths["zip"],
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    if result.forbidden_language_hits:
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
