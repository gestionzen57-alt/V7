from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from pf_t009_live_data_freshness_guard import build_and_write, build_guard, LIVE_FRESH_WITH_LIMITS, DB_EMPTY


def test_t0166_fresh_db_with_unqualified_candidate(tmp_path: Path):
    db = tmp_path / "powerflow.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE force_snapshots_v2 (time TEXT, symbol TEXT, value REAL)")
        conn.execute("INSERT INTO force_snapshots_v2 VALUES (?, ?, ?)", ("2026-05-18T12:00:00+00:00", "GBPUSD", 1.0))
    cand = tmp_path / "candidate.json"
    cand.write_text(json.dumps({"candidate_id": "B9LSC_SAMPLE", "source_quality_gate_state": "SOURCE_LIVE_UNQUALIFIED"}), encoding="utf-8")
    result = build_guard(tmp_path, powerflow_db=db, live_candidate_json=cand, freshness_seconds=300, now_iso="2026-05-18T12:02:00+00:00")
    assert result.force_snapshots_v2_rows == 1
    assert result.guard_state == LIVE_FRESH_WITH_LIMITS
    assert result.forbidden_language_hits == []
    assert result.no_decision_guard is True


def test_t0166_empty_db_blocks_active_raw_claim(tmp_path: Path):
    db = tmp_path / "powerflow.db"
    with sqlite3.connect(db) as conn:
        conn.execute("CREATE TABLE force_snapshots_v2 (time TEXT, symbol TEXT)")
    result = build_guard(tmp_path, powerflow_db=db, tick_archive_db=tmp_path/"missing_tick_archive.db", freshness_seconds=300, now_iso="2026-05-18T12:02:00+00:00")
    assert result.guard_state == DB_EMPTY
    assert result.force_snapshots_v2_rows == 0
    assert any("force_snapshots_v2" in x for x in result.technical_limits)


def test_t0166_writes_expected_outputs(tmp_path: Path):
    out = tmp_path / "out"
    result, paths = build_and_write(tmp_path, out, now_iso="2026-05-18T12:02:00+00:00")
    for p in paths.values():
        assert Path(p).exists()
    data = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert data["version"] == "T0166_B9_LIVE_DATA_FRESHNESS_GUARD_V0"
    assert data["no_decision_guard"] is True
