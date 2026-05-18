from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_daily_replay_audit_report import VERSION, build_daily_replay_audit


def existing_or_none(text: str | None) -> Path | None:
    if not text:
        return None
    return Path(text)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0151 B9 Daily Replay Audit Report V0")
    parser.add_argument("--replay-results-csv", default=None)
    parser.add_argument("--session-scorecard-csv", default=None)
    parser.add_argument("--golden-cases-csv", default=None)
    parser.add_argument("--sequence-summary-json", default=None)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    audit = build_daily_replay_audit(
        replay_results_csv=existing_or_none(args.replay_results_csv),
        session_scorecard_csv=existing_or_none(args.session_scorecard_csv),
        golden_cases_csv=existing_or_none(args.golden_cases_csv),
        sequence_summary_json=existing_or_none(args.sequence_summary_json),
        output_dir=Path(args.output_dir),
    )
    counts = audit.get("counts", {})
    print(json.dumps({
        "version": VERSION,
        "audit_state": audit.get("audit_state"),
        "files_or_moments_processed": counts.get("files_or_moments_processed", 0),
        "seen_cleanly": counts.get("seen_cleanly", 0),
        "partial_or_fragile": counts.get("partial_or_fragile", 0),
        "rejected_or_unusable": counts.get("rejected_or_unusable", 0),
        "source_fragile": counts.get("source_fragile", 0),
        "retest_fragile": counts.get("retest_fragile", 0),
        "memory_helped": counts.get("memory_helped", 0),
        "forbidden_language_hits": audit.get("forbidden_language_hits", []),
        "zip": audit.get("output_files", {}).get("zip"),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
