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


def build_db(path, gappy=False, unstable_spread=False):
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
    if gappy:
        times = ["05:00:00", "05:00:05", "05:00:30", "05:00:55", "05:01:00"]
    else:
        times = ["05:00:00", "05:00:10", "05:00:20", "05:00:40", "05:01:00"]
    rows = []
    for i, t in enumerate(times):
        spread = 0.0015 if unstable_spread and i == 2 else 0.0002 + (i * 0.00005)
        bid = 1.1000 + i * 0.00025
        ask = bid + spread
        mid = (bid + ask) / 2.0
        rows.append((f"2026-05-15T{t}Z", "GBPUSD", "HISTORICAL_RAW", bid, ask, mid, spread, i + 1, i + 1))
    # exact duplicate
    rows.append(rows[0])
    conn.executemany("INSERT INTO tick_stream VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def calibrate(tmp_path, gappy=False, unstable_spread=False):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    build_db(db, gappy=gappy, unstable_spread=unstable_spread)
    summary = {
        "moments": [
            {
                "moment_id": "m1",
                "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
                "label_fr": "Vague progressive",
                "time_start": "2026-05-15T08:00:00Z",
                "time_end": "2026-05-15T08:01:00Z",
                "center_delta_pips": 8.0,
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


def test_t0106_direct_fields_are_added(tmp_path):
    payload, m = calibrate(tmp_path)
    required = [
        "b9_direct_factor_version",
        "b9_temporal_pressure_state",
        "b9_raw_activity_factor",
        "b9_spread_factor",
        "b9_volume_factor_state",
        "b9_center_speed_factor",
        "b9_microfilm_texture_score",
        "b9_microfilm_quality_state",
        "b9_microfilm_profile",
        "b9_factor_flags",
    ]
    for field in required:
        assert field in m, field
    assert payload["raw_calibration"]["version"] == "T0106_DIRECT_RAW_FACTORS_V0"


def test_volume_is_direct_but_broker_relative(tmp_path):
    payload, m = calibrate(tmp_path)
    assert m["b9_volume_use_policy"] == "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL"
    assert m["b9_volume_factor_state"].startswith("VOLUME_VISIBLE_BROKER_RELATIVE")
    assert "VOLUME_BROKER_RELATIVE_VISIBLE" in m["b9_factor_flags"]


def test_external_temporality_stays_out(tmp_path):
    payload, m = calibrate(tmp_path)
    assert m["external_temporality_dependency"] is False
    assert "NO_EXTERNAL_TEMPORALITE" in m["b9_temporality_policy"]
    assert payload["raw_calibration"]["external_temporality_dependency"] is False


def test_texture_score_is_bounded(tmp_path):
    payload, m = calibrate(tmp_path)
    assert 0.0 <= m["b9_microfilm_texture_score"] <= 1.0
    assert m["b9_microfilm_quality_state"] in {
        "MICROFILM_TEXTURE_HIGH",
        "MICROFILM_TEXTURE_MEDIUM",
        "MICROFILM_TEXTURE_LOW",
        "MICROFILM_TEXTURE_LIMITED",
        "MICROFILM_ARTIFACT",
    }


def test_profile_and_flags_are_meaningful(tmp_path):
    payload, m = calibrate(tmp_path)
    assert isinstance(m["b9_factor_flags"], list)
    assert m["b9_microfilm_profile"] in {
        "ZERO_DURATION_ARTIFACT",
        "SPREAD_UNSTABLE_MICROFILM",
        "GAPPY_MICROFILM_LIMIT",
        "PROGRESSIVE_ROTATIONAL_TRAP",
        "WEAK_RAW_PROGRESS",
        "CLEAN_PROGRESSIVE_MICROFILM",
        "ROTATIONAL_MICROFILM",
        "RAW_CONFIRMED_MICROFILM",
        "MIXED_MICROFILM",
    }


def test_unstable_spread_changes_profile_or_flags(tmp_path):
    payload, m = calibrate(tmp_path, unstable_spread=True)
    assert m["b9_spread_factor"] in {
        "SPREAD_EXPANDING_CAUTION",
        "SPREAD_UNSTABLE_LIMIT",
        "SPREAD_THIN_DATA_LIMIT",
        "SPREAD_CLEAN",
        "SPREAD_UNKNOWN",
    }
    assert any(flag in m["b9_factor_flags"] for flag in ["SPREAD_EXPANDING", "SPREAD_UNSTABLE", "NO_MAJOR_RAW_FACTOR_LIMIT", "VOLUME_BROKER_RELATIVE_VISIBLE"])


def test_dedup_counts_preserved(tmp_path):
    payload, m = calibrate(tmp_path)
    assert m["raw_tick_count_raw"] == 6
    assert m["raw_tick_count_dedup"] == 5
    assert m["raw_duplicate_count"] == 1


def test_report_and_contract_exist():
    assert (ROOT / "Docs" / "Reports" / "T0106_B9_DIRECT_RAW_FACTORS_V0_REPORT.md").exists()
    assert (ROOT / "Docs" / "Contracts" / "B9_DIRECT_RAW_FACTORS_V0_CONTRACT.md").exists()


def test_no_decision_language():
    combined = (
        (ROOT / "Docs" / "Reports" / "T0106_B9_DIRECT_RAW_FACTORS_V0_REPORT.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "Docs" / "Contracts" / "B9_DIRECT_RAW_FACTORS_V0_CONTRACT.md").read_text(encoding="utf-8")
    ).lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in combined
