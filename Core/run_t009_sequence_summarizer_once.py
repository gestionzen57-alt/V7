"""CLI runner for T009 Sequence Summarizer V3.2.0_T0111 / B9."""

from __future__ import annotations

import argparse
from pathlib import Path

from pf_t009_sequence_summarizer import summarize_files


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="T009 Sequence Summarizer V3.2.0_T0111")
    parser.add_argument("--state", required=True, help="Path to battlefield_flux_state.json")
    parser.add_argument("--events", required=True, help="Path to battlefield_flux_events.json")
    parser.add_argument("--output", required=True, help="Output directory for t009_sequence_summary artifacts")
    parser.add_argument("--max-gap-sec", type=int, default=300, help="Max seconds between events in one moment")
    parser.add_argument("--price-merge-pips", type=float, default=5.0, help="Max center distance in pips inside one moment")
    parser.add_argument("--pip-size", type=float, default=0.0001, help="Pip size used for center migration")
    parser.add_argument("--replay-report", default=None, help="Optional replay report JSON with shifted_start_utc/original_start_utc")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    result = summarize_files(
        state_file=args.state,
        events_file=args.events,
        output_dir=args.output,
        max_gap_sec=args.max_gap_sec,
        price_merge_pips=args.price_merge_pips,
        pip_size=args.pip_size,
        replay_report_file=args.replay_report,
    )
    summary = result["summary"]
    source = summary.get("source", {})
    moments = summary.get("moments", [])

    print("T009 Sequence Summarizer V3.2.0_T0111")
    print(f"Events loaded: {source.get('event_count', 0)}")
    print(f"Moments detected: {len(moments)}")
    print(f"Output JSON: {Path(result['json_path'])}")
    print(f"Output MD: {Path(result['markdown_path'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

