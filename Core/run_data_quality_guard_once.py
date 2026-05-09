# run_data_quality_guard_once.py
"""
CLI runner for pf_data_quality_guard.py.

Examples:
    python run_data_quality_guard_once.py --db powerflow.db --since 2026-05-06 --pretty
    python run_data_quality_guard_once.py --db powerflow.db --since 2026-05-06 --output output/data_quality.json --pretty
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from pf_data_quality_guard import (
    DEFAULT_TABLE,
    DEFAULT_TIMEFRAMES,
    DataQualityGuardError,
    dumps_report,
    parse_timeframes,
    scan_data_quality,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PowerFlow V7.1 data quality guard - read-only DB scanner.",
    )
    parser.add_argument(
        "--db",
        default="powerflow.db",
        help="Path to SQLite DB. Default: powerflow.db",
    )
    parser.add_argument(
        "--since",
        required=True,
        help="Scan lower bound date/timestamp, e.g. 2026-05-06",
    )
    parser.add_argument(
        "--tfs",
        default=",".join(str(tf) for tf in DEFAULT_TIMEFRAMES),
        help="Comma-separated timeframes in minutes. Default: 1,5,15,30,60,240,1440",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help="SQLite table to inspect. Default: force_snapshots",
    )
    parser.add_argument(
        "--stale-multiplier",
        type=float,
        default=2.5,
        help="Stale threshold = timeframe seconds x multiplier. Default: 2.5",
    )
    parser.add_argument(
        "--gap-tolerance",
        type=float,
        default=1.05,
        help="Gap threshold = timeframe seconds x tolerance. Default: 1.05",
    )
    parser.add_argument(
        "--max-gaps-sample",
        type=int,
        default=20,
        help="Max gap records retained per timeframe in report. Default: 20",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    parser.add_argument(
        "--output",
        help="Optional output JSON file path.",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Logging level. Default: WARNING",
    )
    return parser


def write_or_stdout(payload: str, output: str | None) -> None:
    if output:
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload + "\n", encoding="utf-8")
        return
    sys.stdout.write(payload + "\n")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s:%(name)s:%(message)s",
    )

    try:
        timeframes = parse_timeframes(args.tfs)
        report = scan_data_quality(
            db_path=args.db,
            since=args.since,
            timeframes=timeframes,
            table=args.table,
            stale_multiplier=args.stale_multiplier,
            gap_tolerance=args.gap_tolerance,
            max_gaps_sample=args.max_gaps_sample,
        )
        payload = dumps_report(report, pretty=args.pretty)
        write_or_stdout(payload, args.output)
        return 0 if report.get("overall_status") in {"PASS", "WARN"} else 2
    except (DataQualityGuardError, ValueError, OSError) as exc:
        error_payload = dumps_report(
            {
                "module": "run_data_quality_guard_once",
                "status": "FAIL",
                "technical_risks": ["DATA_QUALITY_GUARD_ERROR"],
                "error": str(exc),
            },
            pretty=True,
        )
        sys.stderr.write(error_payload + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
