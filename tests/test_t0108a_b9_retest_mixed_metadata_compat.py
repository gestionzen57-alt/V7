# -*- coding: utf-8 -*-
from pathlib import Path
import importlib
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]


def load_module():
    repo = str(ROOT)
    if repo not in sys.path:
        sys.path.insert(0, repo)
    if "pf_t009_raw_calibration" in sys.modules:
        del sys.modules["pf_t009_raw_calibration"]
    return importlib.import_module("pf_t009_raw_calibration")


def build_db(path):
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE tick_stream (
            ts_utc TEXT,
            symbol TEXT,
            source_mode TEXT,
            bid REAL,
            ask REAL,
            mid REAL,
            spread REAL,
            tick_volume REAL,
            capture_seq INTEGER
        )
        """
    )
    rows = []
    times = ["05:00:00", "05:00:10", "05:00:20", "05:00:30", "05:00:40", "05:01:00"]
    mids = [1.1000, 1.1003, 1.1006, 1.1009, 1.1012, 1.1015]
    for i, (t, mid) in enumerate(zip(times, mids)):
        spread = 0.0002
        bid = mid - spread / 2
        ask = mid + spread / 2
        rows.append((f"2026-05-15T{t}Z", "GBPUSD", "HISTORICAL_RAW", bid, ask, mid, spread, i + 1, i + 1))
    conn.executemany("INSERT INTO tick_stream VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def calibrate(tmp_path):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    build_db(db)
    summary = {
        "moments": [
            {
                "moment_id": "m1",
                "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
                "label_fr": "Vague progressive",
                "time_start": "2026-05-15T08:00:00Z",
                "time_end": "2026-05-15T08:01:00Z",
                "center_delta_pips": 8.0,
                "retest_status": "PENDING",
            }
        ]
    }
    cfg = mod.RawCalibrationConfig(
        tick_db_path=str(db),
        symbol="GBPUSD",
        broker="UnitTest",
        broker_time_shift_min=180,
        raw_source_mode="HISTORICAL_RAW",
        raw_data_visibility="MT5_RAW_ALIGNED",
        pip_size=0.0001,
    )
    payload = mod.calibrate_summary_with_raw(summary, cfg)
    return payload, payload["moments"][0]


def test_t0108_preserves_t0107_metadata(tmp_path):
    payload, m = calibrate(tmp_path)
    raw = payload["raw_calibration"]
    assert raw["version"] in {"T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}
    assert "T0107_NATURAL_FLOW_READING_V0" in raw["parent_versions"]
    assert "b9_flow_intent_state" in raw["natural_flow_factors"]
    assert "b9_retest_natural_state" in raw["retest_mixed_fields"]


def test_t0107_and_t0108_fields_coexist(tmp_path):
    payload, m = calibrate(tmp_path)
    assert "b9_natural_flow_version" in m
    assert "b9_flow_intent_state" in m
    assert "b9_retest_mixed_split_version" in m
    assert "b9_retest_natural_state" in m
    assert "b9_context_resolution_state" in m


def test_report_exists_and_no_decision_language():
    path = ROOT / "Docs" / "Reports" / "T0108A_B9_RETEST_MIXED_METADATA_COMPAT_HOTFIX.md"
    assert path.exists()
    text = path.read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in text
