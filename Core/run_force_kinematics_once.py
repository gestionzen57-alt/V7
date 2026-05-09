#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_force_kinematics import kinematics_summary, make_markdown_report


def parse_timeframes(value: str):
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--timeframes", default="1,5,15,30,60")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"DB not found: {args.db}")

    tfs = parse_timeframes(args.timeframes)

    if args.json:
        result = kinematics_summary(args.db, args.symbol, args.start, args.end, tfs)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    report = make_markdown_report(args.db, args.symbol, args.start, args.end, tfs)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"OK wrote kinematics report: {args.out}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
