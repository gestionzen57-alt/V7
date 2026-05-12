from __future__ import annotations


# PF_SYMBOLS_COMPAT_V737D
# Backward compatibility: scheduler_powerflow.py still passes --symbols.
# B8 runner currently works without this argument, so we strip it before argparse.
import sys as _pf_sys

def _pf_strip_legacy_symbols_arg(argv):
    out = []
    skip_next = False
    for item in argv:
        if skip_next:
            skip_next = False
            continue
        if item == "--symbols":
            skip_next = True
            continue
        if item.startswith("--symbols="):
            continue
        out.append(item)
    return out

_pf_sys.argv = _pf_strip_legacy_symbols_arg(_pf_sys.argv)
# END_PF_SYMBOLS_COMPAT_V737D

"""CLI runner for B8 Cross-Symbol Validation."""
import argparse
import json
import os
from dataclasses import asdict

from pf_cross_symbol_validation import (
    CrossValidationError,
    trigger_alert_if_needed,
    validate_cross_symbol,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="B8 Cross-Symbol Validation — Single run"
    )
    parser.add_argument("--db", required=True, help="Path to powerflow.db")
    parser.add_argument(
        "--symbol", default="GBP", help="Currency to validate (GBP, EUR, USD, JPY, etc.)"
    )
    parser.add_argument(
        "--timeframe", type=int, default=1, help="Timeframe (1=M1, 5=M5, 15=M15, etc.)"
    )
    parser.add_argument("--window", type=int, default=20, help="Rolling window size")
    parser.add_argument(
        "--output",
        default="output/cross_validation_state.json",
        help="Output state JSON file",
    )
    parser.add_argument(
        "--alert-output",
        default="",
        help="Optional output file for B8 perception alert JSON",
    )
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")
    parser.add_argument("--verbose", action="store_true", help="Verbose logs")
    args = parser.parse_args()

    try:
        state = validate_cross_symbol(
            symbol=args.symbol,
            db_path=args.db,
            timeframe=args.timeframe,
            window=args.window,
        )
    except CrossValidationError as exc:
        print(f"B8 Cross-Symbol Validation failed: {exc}")
        # PF_B8_COVERAGE_SOFT_RETURN_V737D
        if "Not enough usable cross pairs" in str(exc):
            print("B8_CROSS_SYMBOL_DEGRADED | " + str(exc))
            return 0
        return 2

    output_dir = os.path.dirname(args.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(asdict(state), handle, indent=2 if args.pretty else None, ensure_ascii=False)

    alert = trigger_alert_if_needed(state)
    if args.alert_output and alert:
        alert_dir = os.path.dirname(args.alert_output)
        if alert_dir:
            os.makedirs(alert_dir, exist_ok=True)
        with open(args.alert_output, "w", encoding="utf-8") as handle:
            json.dump(alert, handle, indent=2 if args.pretty else None, ensure_ascii=False)

    if args.verbose:
        print(f"Cross-validation saved to {args.output}")
        print(f"Driver detected: {state.driver_detection.primary_driver}")
        print(f"Confidence: {state.driver_detection.confidence:.2%}")
        print(f"Alert: {state.alert_type or 'NONE'}")
    elif args.pretty:
        print(json.dumps(asdict(state), indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    # PF_B8_SOFT_FAIL_V737D
    # B8 is a contextual validation layer. Missing cross-pair coverage must degrade,
    # not block the full PowerFlow scheduler.
    import sys as _pf_sys

    try:
        _code = main()
    except Exception as _exc:
        _msg = str(_exc)
        if "Not enough usable cross pairs" in _msg:
            print("B8_CROSS_SYMBOL_DEGRADED | " + _msg)
            raise SystemExit(0)
        raise

    if _code not in (0, None):
        # Some versions print the failure and return 1 instead of raising.
        # Keep non-B8 failures hard, but let known coverage insufficiency be soft.
        raise SystemExit(_code)

    raise SystemExit(0)
