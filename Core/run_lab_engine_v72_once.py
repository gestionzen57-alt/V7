#!/usr/bin/env python3
"""
Runner — PowerFlow V7.2 Lab Engine

Examples:
  python Core/run_lab_engine_v72_once.py --db Core/powerflow.db --symbol GBPUSD --date 2026-05-08 --start 09:00 --end 11:00 --pretty
  python Core/run_lab_engine_v72_once.py --self-test --pretty
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pf_lab_engine_v72 import LabConfig, parse_date_time, run_lab


def parse_tfs(raw: str) -> list[int]:
    out = []
    for part in str(raw).split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out or [1, 5, 15, 30, 60]


def create_selftest_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()

    conn = sqlite3.connect(path)
    try:
        conn.execute(
            """
            CREATE TABLE force_snapshots (
                timestamp TEXT,
                symbol TEXT,
                timeframe INTEGER,
                force_gbp REAL,
                force_usd REAL,
                force_eur REAL,
                force_jpy REAL,
                force_cad REAL,
                force_chf REAL,
                force_aud REAL
            )
            """
        )

        start = datetime(2026, 5, 8, 9, 0, tzinfo=timezone.utc)
        tfs = [1, 5, 15, 30, 60]

        for i in range(120):
            ts = start + timedelta(minutes=i)
            # Three regimes in one synthetic session:
            # 0-35 compressing, 36-75 release, 76-119 noisy/fade.
            if i < 36:
                amp = 2.0 - (i * 0.035)
                gbp = math.sin(i / 3.0) * amp + i * 0.01
                usd = -math.sin(i / 3.0) * amp * 0.75 - i * 0.006
            elif i < 76:
                gbp = 0.4 + (i - 36) * 0.20 + math.sin(i / 4.0) * 0.4
                usd = -0.2 - (i - 36) * 0.12 + math.cos(i / 5.0) * 0.25
            else:
                gbp = 8.0 - (i - 76) * 0.07 + math.sin(i * 1.7) * 1.2
                usd = -5.0 + (i - 76) * 0.04 + math.cos(i * 1.4) * 1.0

            for tf in tfs:
                if i % tf == 0 or tf == 1:
                    damp = 1.0 / max(1, tf ** 0.25)
                    conn.execute(
                        "INSERT INTO force_snapshots VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (
                            ts.isoformat().replace("+00:00", "Z"),
                            "GBPUSD",
                            tf,
                            gbp * damp,
                            usd * damp,
                            (gbp * 0.35) * damp,
                            (-usd * 0.22) * damp,
                            (usd * 0.18) * damp,
                            (-gbp * 0.15) * damp,
                            (gbp * 0.08) * damp,
                        ),
                    )
        conn.commit()
    finally:
        conn.close()


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="PowerFlow V7.2 Lab Engine")
    p.add_argument("--db", default="Core/powerflow.db")
    p.add_argument("--symbol", default="GBPUSD")
    p.add_argument("--date", default=None, help="YYYY-MM-DD")
    p.add_argument("--start", default=None, help="HH:MM")
    p.add_argument("--end", default=None, help="HH:MM")
    p.add_argument("--tfs", default="1,5,15,30,60")
    p.add_argument("--out-root", default="output")
    p.add_argument("--outcome-window", type=int, default=30)
    p.add_argument("--hypothesis", default="all", choices=["all", "compression_real_vs_fake", "second_leg"])
    p.add_argument("--table", default=None)
    p.add_argument("--pretty", action="store_true")
    p.add_argument("--self-test", action="store_true")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    if args.self_test:
        db_path = Path("output") / "lab_engine_v72_selftest.db"
        create_selftest_db(db_path)
        date_s = "2026-05-08"
        start_s = "09:00"
        end_s = "10:59"
    else:
        db_path = Path(args.db)
        if not args.date or not args.start or not args.end:
            raise SystemExit("--date, --start and --end are required unless --self-test is used")
        date_s = args.date
        start_s = args.start
        end_s = args.end

    config = LabConfig(
        db_path=db_path,
        symbol=args.symbol,
        start_dt=parse_date_time(date_s, start_s),
        end_dt=parse_date_time(date_s, end_s),
        tfs=parse_tfs(args.tfs),
        out_root=Path(args.out_root),
        outcome_window=args.outcome_window,
        hypothesis=args.hypothesis,
        table=args.table,
    )

    result = run_lab(config)
    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
