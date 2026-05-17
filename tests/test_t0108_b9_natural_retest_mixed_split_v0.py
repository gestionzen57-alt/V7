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


def build_db(path, mode="directional"):
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
    if mode == "rotation":
        mids = [1.1000, 1.1006, 1.0999, 1.1005, 1.1002, 1.1001]
    elif mode == "flat":
        mids = [1.1000, 1.1001, 1.0999, 1.1001, 1.1000, 1.1000]
    else:
        mids = [1.1000, 1.1003, 1.1006, 1.1009, 1.1012, 1.1015]
    times = ["05:00:00", "05:00:10", "05:00:20", "05:00:30", "05:00:40", "05:01:00"]
    rows = []
    for i, (t, mid) in enumerate(zip(times, mids)):
        spread = 0.0002
        bid = mid - spread / 2
        ask = mid + spread / 2
        rows.append((f"2026-05-15T{t}Z", "GBPUSD", "HISTORICAL_RAW", bid, ask, mid, spread, i + 1, i + 1))
    rows.append(rows[0])
    conn.executemany("INSERT INTO tick_stream VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def calibrate(tmp_path, mode="directional", retest_status=None, end="2026-05-15T08:01:00Z"):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    build_db(db, mode=mode)
    moment = {
        "moment_id": "m1",
        "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
        "label_fr": "Vague progressive",
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": end,
        "center_delta_pips": 8.0,
    }
    if retest_status is not None:
        moment["retest_status"] = retest_status

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


def test_t0108_fields_are_added(tmp_path):
    payload, m = calibrate(tmp_path)
    for field in [
        "b9_retest_mixed_split_version",
        "b9_mixed_split_state",
        "b9_retest_natural_state",
        "b9_retest_quality_state",
        "b9_context_resolution_state",
        "b9_retest_mixed_reading_fr",
    ]:
        assert field in m, field
    assert payload["raw_calibration"]["version"] in {"T0108_RETEST_MIXED_SPLIT_V0", "T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}


def test_retest_pending_after_displacement(tmp_path):
    payload, m = calibrate(tmp_path, mode="directional", retest_status="PENDING")
    assert m["b9_retest_natural_state"] in {
        "RETEST_PENDING_AFTER_DISPLACEMENT",
        "RETEST_PENDING_TEXTURE",
        "RETEST_PENDING_TRAP_RISK",
    }
    assert m["b9_retest_quality_state"] in {
        "RETEST_QUALITY_PENDING",
        "RETEST_QUALITY_RISK",
        "RETEST_QUALITY_UNREADABLE",
    }


def test_retest_accepted_state(tmp_path):
    payload, m = calibrate(tmp_path, mode="directional", retest_status="ACCEPTED")
    assert m["b9_retest_natural_state"] in {
        "RETEST_ACCEPTED",
        "RETEST_ACCEPTED_WITH_FRICTION",
        "RETEST_UNREADABLE_TEXTURE",
    }


def test_mixed_split_outputs_allowed_values(tmp_path):
    payload, m = calibrate(tmp_path, mode="flat", end="2026-05-15T08:10:00Z")
    assert m["b9_mixed_split_state"] in {
        "MIXED_SPLIT_NOT_MIXED",
        "MIXED_SPLIT_READ_LIMIT",
        "MIXED_SPLIT_TRAP_RISK",
        "MIXED_SPLIT_FRICTION",
        "MIXED_SPLIT_STRESS",
        "MIXED_SPLIT_BALANCED_AUCTION",
        "MIXED_SPLIT_TRANSITION",
        "MIXED_SPLIT_DIGESTION",
        "MIXED_SPLIT_CONTEXT",
        "MIXED_SPLIT_ARTIFACT",
    }


def test_context_resolution_is_interpretive(tmp_path):
    payload, m = calibrate(tmp_path, mode="rotation")
    assert m["b9_context_resolution_state"].startswith("CONTEXT_")
    assert isinstance(m["b9_retest_mixed_reading_fr"], str)
    assert len(m["b9_retest_mixed_reading_fr"]) > 10


def test_flags_preserve_t0107_and_add_t0108(tmp_path):
    payload, m = calibrate(tmp_path, mode="rotation", retest_status="FAILED")
    flags = m["b9_factor_flags"]
    assert m["b9_retest_natural_state"] in flags
    assert m["b9_context_resolution_state"] in flags
    assert "b9_flow_intent_state" in payload["raw_calibration"].get("natural_flow_factors", [])


def test_report_and_contract_exist():
    assert (ROOT / "Docs" / "Reports" / "T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_REPORT.md").exists()
    assert (ROOT / "Docs" / "Contracts" / "B9_NATURAL_RETEST_MIXED_SPLIT_V0_CONTRACT.md").exists()


def test_no_decision_language():
    combined = (
        (ROOT / "Docs" / "Reports" / "T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_REPORT.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "Docs" / "Contracts" / "B9_NATURAL_RETEST_MIXED_SPLIT_V0_CONTRACT.md").read_text(encoding="utf-8")
    ).lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in combined
