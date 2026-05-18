"""CLI runner for B9 raw calibration V3.2 -> V3.5.

Reads a B9 sequence summary JSON, enriches its moments from MT5 raw ticks in
``tick_archive.db`` using read-only SQLite mode, and writes calibrated JSON/MD.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from pf_t009_raw_calibration import (
    RawCalibrationConfig,
    calibrate_summary_with_raw,
    export_json,
    export_markdown,
    load_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="B9 raw calibration V3.2/V3.5")
    parser.add_argument("--summary-json", required=True, help="Input B9 t009_sequence_summary.json")
    parser.add_argument("--tick-db", required=True, help="Path to Core/tick_archive.db")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--broker", default="OneFunded Capital Ltd.")
    parser.add_argument("--broker-time-shift-min", type=int, default=180)
    parser.add_argument("--raw-source-mode", default="HISTORICAL_RAW")
    parser.add_argument("--raw-data-visibility", default="MT5_RAW_ALIGNED")
    parser.add_argument("--raw-confidence-cap", type=float, default=0.55)
    parser.add_argument("--pip-size", type=float, default=0.0001)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    summary = load_json(args.summary_json)
    cfg = RawCalibrationConfig(
        tick_db_path=args.tick_db,
        symbol=args.symbol,
        broker=args.broker,
        broker_time_shift_min=args.broker_time_shift_min,
        raw_source_mode=args.raw_source_mode,
        raw_data_visibility=args.raw_data_visibility,
        raw_confidence_cap=args.raw_confidence_cap,
        pip_size=args.pip_size,
    )
    calibrated = calibrate_summary_with_raw(summary, cfg)
    out = Path(args.output)
    json_path = export_json(calibrated, out / "t009_sequence_summary_raw_calibrated.json")
    md_path = export_markdown(calibrated, out / "t009_sequence_summary_raw_calibrated.md")
    print("B9 raw calibration V3.2/V3.5")
    print(f"Moments calibrated: {len(calibrated.get('moments', []))}")
    print(f"Output JSON: {json_path}")
    print(f"Output MD: {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
