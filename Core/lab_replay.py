# lab_replay.py
from __future__ import annotations

import argparse
import logging
import sys
from typing import Sequence

from pf_replay_engine import ReplayEngineError, dumps_replay, replay_window, write_replay_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PowerFlow V7.1 Replay Engine — deterministic historical timeline export.",
    )
    parser.add_argument(
        "--db",
        default="powerflow.db",
        help="Path to SQLite DB. Default: powerflow.db",
    )
    parser.add_argument(
        "--symbol",
        required=True,
        help="Symbol to replay, e.g. GBPUSD.",
    )
    parser.add_argument(
        "--date",
        required=True,
        help="Replay date in YYYY-MM-DD format.",
    )
    parser.add_argument(
        "--start",
        required=True,
        help="Replay start time in HH:MM format.",
    )
    parser.add_argument(
        "--end",
        required=True,
        help="Replay end time in HH:MM format.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Output JSON path.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON.",
    )
    parser.add_argument(
        "--log-level",
        default="WARNING",
        choices=("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
        help="Logging level. Default: WARNING",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(levelname)s:%(name)s:%(message)s",
    )

    try:
        report = replay_window(
            db_path=args.db,
            symbol=args.symbol,
            date=args.date,
            start=args.start,
            end=args.end,
        )
        write_replay_json(report, args.output, pretty=args.pretty)
        return 0
    except (ReplayEngineError, OSError, ValueError) as exc:
        error_report = {
            "module": "lab_replay",
            "status": "FAIL",
            "technical_risks": ["REPLAY_ENGINE_ERROR"],
            "error": str(exc),
        }
        sys.stderr.write(dumps_replay(error_report, pretty=True) + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())