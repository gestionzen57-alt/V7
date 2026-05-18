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
    rows = [
        ("2026-05-15T05:00:00Z", "GBPUSD", "HISTORICAL_RAW", 1.1000, 1.1002, 1.1001, 0.0002, 1, 1),
        ("2026-05-15T05:00:00Z", "GBPUSD", "HISTORICAL_RAW", 1.1000, 1.1002, 1.1001, 0.0002, 1, 2),
        ("2026-05-15T05:00:10Z", "GBPUSD", "HISTORICAL_RAW", 1.1003, 1.1006, 1.10045, 0.0003, 2, 3),
        ("2026-05-15T05:00:30Z", "GBPUSD", "HISTORICAL_RAW", 1.1008, 1.1014, 1.1011, 0.0006, 3, 4),
        ("2026-05-15T05:01:00Z", "GBPUSD", "HISTORICAL_RAW", 1.1012, 1.1018, 1.1015, 0.0006, 4, 5),
    ]
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
                "center_delta_pips": 10.0,
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
    return mod.calibrate_summary_with_raw(summary, cfg)["moments"][0]


def test_t0105_fields_are_added(tmp_path):
    m = calibrate(tmp_path)
    required = [
        "b9_dwell_seconds",
        "b9_microfilm_duration_seconds",
        "b9_center_migration_speed_pips_per_min",
        "raw_tick_density_per_second",
        "raw_tick_density_per_minute",
        "raw_gap_median_ms",
        "raw_gap_max_ms",
        "raw_activity_profile",
        "raw_spread_stability_state",
        "raw_volume_visibility_state",
    ]
    for field in required:
        assert field in m, field


def test_dedup_counts_still_preserved(tmp_path):
    m = calibrate(tmp_path)
    assert m["raw_tick_count_raw"] == 5
    assert m["raw_tick_count_dedup"] == 4
    assert m["raw_duplicate_count"] == 1
    assert m["raw_dedup_mode"] == "DISTINCT_TS_BID_ASK_MID_SPREAD"


def test_activity_metrics_values(tmp_path):
    m = calibrate(tmp_path)
    assert m["b9_dwell_seconds"] == 60.0
    assert m["raw_tick_density_per_minute"] == 4.0
    assert m["raw_gap_count"] == 3
    assert m["raw_gap_median_ms"] > 0
    assert m["raw_activity_profile"] in {
        "RAW_ACTIVITY_THIN",
        "RAW_ACTIVITY_NORMAL",
        "RAW_ACTIVITY_DENSE",
        "RAW_ACTIVITY_BURST",
        "RAW_ACTIVITY_GAPPY",
        "RAW_ACTIVITY_UNKNOWN",
    }


def test_spread_metrics_values(tmp_path):
    m = calibrate(tmp_path)
    assert m["raw_spread_mean_pips"] is not None
    assert m["raw_spread_max_pips"] >= m["raw_spread_min_pips"]
    assert m["raw_spread_stability_state"] in {
        "SPREAD_STABLE",
        "SPREAD_EXPANDING",
        "SPREAD_UNSTABLE",
        "SPREAD_THIN_DATA",
        "SPREAD_UNKNOWN",
    }


def test_volume_is_experimental_broker_relative(tmp_path):
    m = calibrate(tmp_path)
    assert m["raw_volume_visibility_state"] == "VOLUME_PRESENT_BROKER_RELATIVE"
    assert m["raw_volume_field"] == "tick_volume"
    assert m["raw_volume_confidence_cap"] == 0.20
    assert "global Forex volume claim" in " ".join(m["raw_activity_limits"])


def test_external_temporality_dependency_is_false(tmp_path):
    m = calibrate(tmp_path)
    assert m["external_temporality_dependency"] is False
    assert m["b9_intrinsic_temporality_scope"] == "MICROFILM_INTERNAL_ONLY"


def test_report_and_contract_exist():
    assert (ROOT / "Docs" / "Reports" / "T0105_B9_RAW_ACTIVITY_METRICS_V0_REPORT.md").exists()
    assert (ROOT / "Docs" / "Contracts" / "B9_RAW_ACTIVITY_METRICS_V0_CONTRACT.md").exists()


def test_no_decision_language():
    combined = (
        (ROOT / "Docs" / "Reports" / "T0105_B9_RAW_ACTIVITY_METRICS_V0_REPORT.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "Docs" / "Contracts" / "B9_RAW_ACTIVITY_METRICS_V0_CONTRACT.md").read_text(encoding="utf-8")
    ).lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in combined
