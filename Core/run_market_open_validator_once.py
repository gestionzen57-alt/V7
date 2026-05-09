# run_market_open_validator_once.py
"""
CLI runner for pf_market_open_validator.py.

Examples:
    python run_market_open_validator_once.py --db powerflow.db --since 2026-05-12 --pretty
    python run_market_open_validator_once.py --db powerflow.db --recent-minutes 240 --output output/market_open_validator.json --pretty

Optional JSON mode:
    python run_market_open_validator_once.py --db powerflow.db --b4-json output/b4.json --b5-json output/b5.json --eie-json output/eie.json --pretty
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Sequence

from pf_market_open_validator import (
    DEFAULT_TABLE,
    DEFAULT_TIMEFRAMES,
    MarketOpenValidatorError,
    dumps_report,
    parse_timeframes,
    validate_market_open,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="PowerFlow V7.1 market-open validator - B4/B5/EIE liveness.",
    )
    parser.add_argument(
        "--db",
        default="powerflow.db",
        help="Path to SQLite DB. Default: powerflow.db",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Optional lower bound date/timestamp, e.g. 2026-05-12",
    )
    parser.add_argument(
        "--tfs",
        default=",".join(str(tf) for tf in DEFAULT_TIMEFRAMES),
        help="Comma-separated timeframes in minutes. Default: 1,5,15",
    )
    parser.add_argument(
        "--symbol",
        default=None,
        help="Optional symbol filter if force_snapshots has a symbol column.",
    )
    parser.add_argument(
        "--table",
        default=DEFAULT_TABLE,
        help="SQLite table to inspect. Default: force_snapshots",
    )
    parser.add_argument(
        "--recent-minutes",
        type=int,
        default=180,
        help="Recent DB window used for proxy validation. Default: 180",
    )
    parser.add_argument(
        "--max-market-stale-minutes",
        type=int,
        default=15,
        help="Max age of latest DB timestamp for market-open freshness. Default: 15",
    )
    parser.add_argument(
        "--b4-json",
        default=None,
        help="Optional B4 output JSON path. If omitted, DB proxy validation is used.",
    )
    parser.add_argument(
        "--b5-json",
        default=None,
        help="Optional B5 output JSON path. If omitted, DB proxy validation is used.",
    )
    parser.add_argument(
        "--eie-json",
        default=None,
        help="Optional EIE output JSON path. If omitted, DB proxy validation is used.",
    )
    parser.add_argument(
        "--b4-window",
        type=int,
        default=48,
        help="Rolling window length for DB proxy B4. Default: 48",
    )
    parser.add_argument(
        "--b5-window",
        type=int,
        default=48,
        help="Rolling window length for DB proxy B5. Default: 48",
    )
    parser.add_argument(
        "--step",
        type=int,
        default=6,
        help="Rolling window step for DB proxy metrics. Default: 6",
    )
    parser.add_argument(
        "--b4-static-threshold",
        type=float,
        default=0.95,
        help="Static ratio threshold for B4 dominant_period_bars. Default: 0.95",
    )
    parser.add_argument(
        "--b5-min-rho-std",
        type=float,
        default=0.02,
        help="Minimum rho std-dev for B5 fluctuation. Default: 0.02",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON.",
    )
    parser.add_argument(
        "--output",
        default=None,
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
        report = validate_market_open(
            db_path=args.db,
            since=args.since,
            timeframes=timeframes,
            symbol=args.symbol,
            table=args.table,
            recent_minutes=args.recent_minutes,
            max_market_stale_minutes=args.max_market_stale_minutes,
            b4_json_path=args.b4_json,
            b5_json_path=args.b5_json,
            eie_json_path=args.eie_json,
            b4_window=args.b4_window,
            b5_window=args.b5_window,
            step=args.step,
            b4_static_threshold=args.b4_static_threshold,
            b5_min_rho_std=args.b5_min_rho_std,
        )
        payload = dumps_report(report, pretty=args.pretty)
        write_or_stdout(payload, args.output)
        return 0 if report.get("overall_status") == "PASS" else 2
    except (MarketOpenValidatorError, ValueError, OSError) as exc:
        error_payload = dumps_report(
            {
                "module": "run_market_open_validator_once",
                "overall_status": "FAIL",
                "technical_risks": ["MARKET_OPEN_VALIDATOR_ERROR"],
                "error": str(exc),
            },
            pretty=True,
        )
        sys.stderr.write(error_payload + "\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
