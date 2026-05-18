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


def calibrate(tmp_path, retest_status=None, zone_memory=None):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    build_db(db)
    moment = {
        "moment_id": "m1",
        "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
        "label_fr": "Vague progressive",
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": "2026-05-15T08:01:00Z",
        "center_delta_pips": 8.0,
    }
    if retest_status is not None:
        moment["retest_status"] = retest_status
    if zone_memory is not None:
        moment["zone_memory"] = zone_memory

    summary = {"moments": [moment]}
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


def test_t0110_fields_are_added(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="PENDING")
    for field in [
        "retest_source_fields_version",
        "retest_touch_count",
        "retest_first_touch_time",
        "retest_last_touch_time",
        "retest_delay_seconds",
        "retest_acceptance_dwell_seconds",
        "retest_rejection_speed_pips_per_min",
        "retest_zone_distance_pips",
        "retest_outcome_hint",
        "retest_source_field_confidence",
    ]:
        assert field in m, field
    assert payload["raw_calibration"]["version"] == "T0110_RETEST_SOURCE_FIELDS_V0"


def test_explicit_pending_creates_minimum_touch_and_feeds_t0109(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="PENDING")
    assert m["retest_touch_count"] == 1
    assert m["retest_outcome_hint"] == "RETEST_OUTCOME_PENDING"
    assert m["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_EXPLICIT"
    assert m["b9_retest_source_status"] == "RETEST_SOURCE_PENDING_EXPLICIT"


def test_zone_memory_fields_are_canonicalized(tmp_path):
    zone_memory = {
        "touch_count": 3,
        "last_tested": "2026-05-15T07:58:00Z",
        "retest_status": "ACCEPTED",
        "retest_first_touch_time": "2026-05-15T07:57:00Z",
    }
    payload, m = calibrate(tmp_path, zone_memory=zone_memory)
    assert m["retest_touch_count"] == 3
    assert m["retest_delay_seconds"] == 120.0
    assert m["retest_first_touch_time"].startswith("2026-05-15T07:57:00")
    assert m["retest_last_touch_time"].startswith("2026-05-15T07:58:00")
    assert m["retest_outcome_hint"] == "RETEST_OUTCOME_ACCEPTED"
    assert m["b9_retest_source_status"] == "RETEST_SOURCE_ACCEPTED_EXPLICIT"


def test_failed_retest_derives_rejection_fields(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="FAILED")
    assert m["retest_outcome_hint"] == "RETEST_OUTCOME_REJECTED_OR_FAILED"
    assert m["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_EXPLICIT"
    assert m["b9_retest_source_status"] == "RETEST_SOURCE_REJECTED_EXPLICIT"


def test_missing_source_remains_visible_as_silent(tmp_path):
    payload, m = calibrate(tmp_path)
    assert m["retest_outcome_hint"] == "RETEST_OUTCOME_NOT_VISIBLE"
    assert m["retest_source_field_confidence"] in {
        "RETEST_SOURCE_FIELDS_NOT_VISIBLE",
        "RETEST_SOURCE_FIELDS_INFERRED",
        "RETEST_SOURCE_FIELDS_PARTIAL",
    }
    assert "b9_retest_source_status" in m


def test_metadata_preserves_prior_layers(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="PENDING")
    raw = payload["raw_calibration"]
    assert "T0109_RETEST_SOURCE_SIGNALS_V0" in raw["parent_versions"]
    assert "retest_touch_count" in raw["retest_source_fields"]
    assert "b9_retest_source_status" in raw["retest_source_signals"]


def test_report_and_contract_exist():
    assert (ROOT / "Docs" / "Reports" / "T0110_B9_RETEST_SOURCE_FIELDS_V0_REPORT.md").exists()
    assert (ROOT / "Docs" / "Contracts" / "B9_RETEST_SOURCE_FIELDS_V0_CONTRACT.md").exists()


def test_no_decision_language():
    combined = (
        (ROOT / "Docs" / "Reports" / "T0110_B9_RETEST_SOURCE_FIELDS_V0_REPORT.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "Docs" / "Contracts" / "B9_RETEST_SOURCE_FIELDS_V0_CONTRACT.md").read_text(encoding="utf-8")
    ).lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in combined
