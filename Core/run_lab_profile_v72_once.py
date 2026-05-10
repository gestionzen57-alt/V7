#!/usr/bin/env python3
"""
Runner — PowerFlow V7.2 Lab TF Profiles V0.3

Examples:
  python Core\run_lab_profile_v72_once.py --db Core\powerflow.db --symbol GBPUSD --date 2026-05-08 --start 09:00 --end 11:00 --tf-profile MTF --m1 off --pretty
  python Core\run_lab_profile_v72_once.py --db Core\powerflow.db --symbol GBPUSD --date 2026-05-08 --start 09:00 --end 11:00 --tf-profile LTF --m1 zoom --pretty
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from pf_lab_tf_profiles_v72 import ProfileLabConfig, run_profile_lab


def parse_dt(date_s: str, time_s: str) -> datetime:
    raw = f"{date_s}T{time_s}:00" if len(time_s.split(":")) == 2 else f"{date_s}T{time_s}"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_tfs(raw: str | None) -> list[int] | None:
    if not raw:
        return None
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow Lab TF Profiles V0.3")
    p.add_argument("--db", default="Core/powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--date", required=True)
    p.add_argument("--start", required=True)
    p.add_argument("--end", required=True)
    p.add_argument("--tf-profile", default="MTF", choices=["HTF", "MTF", "LTF", "LTF_NO_M1", "FULL", "CUSTOM"])
    p.add_argument("--custom-tfs", default=None, help="Comma-separated tfs for CUSTOM profile")
    p.add_argument("--m1", default="off", choices=["off", "zoom", "full"])
    p.add_argument("--out-root", default="output")
    p.add_argument("--outcome-window", type=int, default=30)
    p.add_argument("--hypothesis", default="all", choices=["all", "compression_real_vs_fake", "second_leg"])
    p.add_argument("--max-m1-zooms", type=int, default=5)
    p.add_argument("--zoom-before", type=int, default=5)
    p.add_argument("--zoom-after", type=int, default=10)
    p.add_argument("--selector-min-confidence", type=float, default=0.60)
    p.add_argument("--selector-warmup-index", type=int, default=15)
    p.add_argument("--pretty", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    cfg = ProfileLabConfig(
        db_path=Path(args.db),
        symbol=args.symbol,
        start_dt=parse_dt(args.date, args.start),
        end_dt=parse_dt(args.date, args.end),
        tf_profile=args.tf_profile,
        m1_mode=args.m1,
        custom_tfs=parse_tfs(args.custom_tfs),
        out_root=Path(args.out_root),
        outcome_window=args.outcome_window,
        hypothesis=args.hypothesis,
        max_m1_zooms=args.max_m1_zooms,
        zoom_before_minutes=args.zoom_before,
        zoom_after_minutes=args.zoom_after,
        selector_min_confidence=args.selector_min_confidence,
        selector_warmup_index=args.selector_warmup_index,
    )

    result = run_profile_lab(cfg)
    print(json.dumps(result, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
