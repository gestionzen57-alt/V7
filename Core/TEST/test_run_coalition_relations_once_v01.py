#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import tempfile
from pathlib import Path

from run_coalition_relations_once import build_vectors_from_db, cockpit_sentence
from pf_coalitions import detect_currency_coalitions
from pf_coalition_relations import qualify_coalition_relations


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

    rows = [
        ("GBP", -2.24, 0.14, 0.04, "ACCUMULATING", "EXTREME"),
        ("EUR", -2.06, 0.11, 0.03, "ACCUMULATING", "EXTREME"),
        ("USD", 2.45, -0.18, -0.06, "LEAKING", "EXTREME"),
        ("JPY", 0.20, 0.01, 0.00, "NEUTRAL", "NORMAL"),
    ]

    for i, (cur, z, slope, curv, state, zone) in enumerate(rows, start=1):
        raw = f'{{"slope": {slope}, "curvature": {curv}, "phase": "{state}"}}'
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
                '2026-05-01T08:00:00+00:00', '2026-05-01T08:00:00+00:00',
                ?, 'GBPUSD', 1, ?, ?, ?, ?, 'LOW', 8,
                0, 0, NULL, NULL, ?, ?, 1.0, 6.0, 7.0,
                'SHORT', 'M1_SPECIAL_MICROFILM', 'LONDON', 1, 7, 8,
                0, '["M1_SPECIAL_MICROFILM","LOCAL_ZONE_WORK"]', '[]', 'test', ?
            )
            """,
            (i, cur, state, zone, z, slope, curv, raw),
        )
    conn.commit()
    conn.close()


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "powerflow.db"
        create_test_db(db)

        vectors = build_vectors_from_db(str(db), timeframe=1)
        assert len(vectors) == 4

        coalitions = detect_currency_coalitions(vectors)
        assert len(coalitions) == 1
        assert set(coalitions[0].members) == {"GBP", "EUR"}

        relations = qualify_coalition_relations(coalitions, vectors)
        assert len(relations) == 1
        assert relations[0].relation_type == "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING"

        sentence = cockpit_sentence(relations, coalitions)
        assert "EUR+GBP vs USD" in sentence or "GBP+EUR vs USD" in sentence

        print("OK run_coalition_relations_once")
        print(sentence)


if __name__ == "__main__":
    main()
