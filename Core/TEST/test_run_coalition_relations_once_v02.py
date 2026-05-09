#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import tempfile
from pathlib import Path

from run_coalition_relations_once_v02 import run_latest, run_scan


def create_test_db(path: Path) -> None:
    conn = sqlite3.connect(path)
    conn.execute("""
    CREATE TABLE zone_diagnostics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        logged_at TEXT NOT NULL,
        source_created_at TEXT,
        source_snapshot_id INTEGER,
        symbol TEXT,
        timeframe INTEGER NOT NULL,
        currency TEXT NOT NULL,
        state TEXT NOT NULL,
        zone_level TEXT,
        z_current REAL,
        z_extreme_dir TEXT,
        bars_in_extreme INTEGER,
        pullback_count INTEGER,
        absorbed_pullback_count INTEGER,
        latest_pullback_depth REAL,
        latest_pullback_absorbed INTEGER,
        depth_slope REAL,
        depth_acceleration REAL,
        absorption_factor REAL,
        tension_score REAL,
        context_score REAL,
        profile_name TEXT,
        profile_horizon TEXT,
        session_phase TEXT,
        rank_position INTEGER,
        rank_total INTEGER,
        rank_duration_bars INTEGER,
        price_wall INTEGER NOT NULL DEFAULT 0,
        context_tags_json TEXT,
        pullbacks_json TEXT,
        note TEXT,
        raw_diagnosis_json TEXT
    );
    """)
    series = {
        "GBP": [-2.40, -2.30, -2.12],
        "EUR": [-2.20, -2.10, -1.95],
        "USD": [2.55, 2.40, 2.18],
        "JPY": [0.10, 0.05, 0.02],
    }
    times = [
        "2026-05-01T08:00:00+00:00",
        "2026-05-01T08:01:00+00:00",
        "2026-05-01T08:02:00+00:00",
    ]
    sid = 1
    for idx, t in enumerate(times):
        for cur, values in series.items():
            z = values[idx]
            state = "ACCUMULATING" if abs(z) >= 1.9 else "NEUTRAL"
            zone = "EXTREME" if abs(z) >= 1.9 else "NORMAL"
            conn.execute(
                """
                INSERT INTO zone_diagnostics (
                    logged_at, source_created_at, source_snapshot_id, symbol, timeframe, currency,
                    state, zone_level, z_current, z_extreme_dir, bars_in_extreme,
                    pullback_count, absorbed_pullback_count, latest_pullback_depth,
                    latest_pullback_absorbed, depth_slope, depth_acceleration,
                    absorption_factor, tension_score, context_score, profile_name,
                    profile_horizon, session_phase, rank_position, rank_total,
                    rank_duration_bars, price_wall, context_tags_json, pullbacks_json,
                    note, raw_diagnosis_json
                ) VALUES (
                    ?, ?, ?, 'GBPUSD', 1, ?, ?, ?, ?, 'LOW', 8,
                    0, 0, NULL, NULL, 0, 0, 1.0, 6.0, 7.0,
                    'SHORT', 'M1_SPECIAL_MICROFILM', 'LONDON', 1, 7, 8,
                    0, '["M1_SPECIAL_MICROFILM","LOCAL_ZONE_WORK"]', '[]', 'test', '{}'
                )
                """,
                (t, t, sid, cur, state, zone, z),
            )
            sid += 1
    conn.commit()
    conn.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "powerflow.db"
        create_test_db(db)
        latest = run_latest(str(db), timeframe=1, symbol=None, currencies=None, lookback_rows=100, slope_lag=1)
        assert latest["coalition_count"] >= 1, latest
        assert latest["relation_count"] >= 1, latest
        assert "vs USD" in latest["cockpit_sentence"], latest["cockpit_sentence"]

        scan = run_scan(str(db), timeframe=1, symbol=None, currencies=None, lookback_rows=100, slope_lag=1, scan=3, min_field_score=0.0)
        assert scan["window_count"] >= 1, scan

        print("OK run_coalition_relations_once V0.2")
        print(latest["cockpit_sentence"])
        print("scan windows:", scan["window_count"])


if __name__ == "__main__":
    main()
