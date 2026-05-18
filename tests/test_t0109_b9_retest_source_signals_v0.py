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


def test_t0109_fields_are_added(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="PENDING")
    for field in [
        "b9_retest_source_version",
        "b9_retest_source_status",
        "b9_retest_touch_count_proxy",
        "b9_retest_delay_proxy_seconds",
        "b9_retest_source_visibility",
        "b9_retest_source_evidence_score",
        "b9_retest_source_signal_state",
        "b9_retest_source_readiness",
        "b9_retest_source_reading_fr",
    ]:
        assert field in m, field
    assert payload["raw_calibration"]["version"] in {"T0109_RETEST_SOURCE_SIGNALS_V0", "T0110_RETEST_SOURCE_FIELDS_V0"}


def test_explicit_accepted_retest_gets_source_evidence(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="ACCEPTED")
    assert m["b9_retest_source_status"] == "RETEST_SOURCE_ACCEPTED_EXPLICIT"
    assert m["b9_retest_source_signal_state"] in {
        "RETEST_SIGNAL_ACCEPTANCE_EVIDENCE",
        "RETEST_SIGNAL_FRICTION_EVIDENCE",
        "RETEST_SIGNAL_ROTATIONAL_CONTEXT",
    }
    assert m["b9_retest_source_evidence_score"] >= 0.4


def test_explicit_failed_retest_gets_rejection_evidence(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="FAILED")
    assert m["b9_retest_source_status"] == "RETEST_SOURCE_REJECTED_EXPLICIT"
    assert m["b9_retest_source_signal_state"] in {
        "RETEST_SIGNAL_REJECTION_EVIDENCE",
        "RETEST_SIGNAL_FRICTION_EVIDENCE",
        "RETEST_SIGNAL_TRAP_RISK_CONTEXT",
    }


def test_zone_memory_touch_count_and_delay_are_extracted(tmp_path):
    zone_memory = {
        "touch_count": 3,
        "last_tested": "2026-05-15T07:58:00Z",
        "retest_status": "PENDING",
    }
    payload, m = calibrate(tmp_path, zone_memory=zone_memory)
    assert m["b9_retest_touch_count_proxy"] == 3
    assert m["b9_retest_delay_proxy_seconds"] == 120.0
    assert m["b9_retest_source_visibility"] in {"RETEST_VISIBILITY_HIGH", "RETEST_VISIBILITY_MEDIUM"}


def test_not_visible_is_explicitly_declared(tmp_path):
    payload, m = calibrate(tmp_path)
    assert m["b9_retest_source_status"] in {
        "RETEST_SOURCE_NOT_VISIBLE",
        "RETEST_SOURCE_ACCEPTED_INFERRED",
        "RETEST_SOURCE_REJECTED_INFERRED",
        "RETEST_SOURCE_FRICTION_INFERRED",
        "RETEST_SOURCE_PENDING_INFERRED",
    }
    assert 0.0 <= m["b9_retest_source_evidence_score"] <= 1.0


def test_metadata_preserves_prior_layers(tmp_path):
    payload, m = calibrate(tmp_path, retest_status="PENDING")
    raw = payload["raw_calibration"]
    assert "T0108_RETEST_MIXED_SPLIT_V0" in raw["parent_versions"]
    assert "b9_flow_intent_state" in raw["natural_flow_factors"]
    assert "b9_retest_natural_state" in raw["retest_mixed_fields"]
    assert "b9_retest_source_status" in raw["retest_source_fields"]


def test_report_and_contract_exist():
    assert (ROOT / "Docs" / "Reports" / "T0109_B9_RETEST_SOURCE_SIGNALS_V0_REPORT.md").exists()
    assert (ROOT / "Docs" / "Contracts" / "B9_RETEST_SOURCE_SIGNALS_V0_CONTRACT.md").exists()


def test_no_decision_language():
    combined = (
        (ROOT / "Docs" / "Reports" / "T0109_B9_RETEST_SOURCE_SIGNALS_V0_REPORT.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "Docs" / "Contracts" / "B9_RETEST_SOURCE_SIGNALS_V0_CONTRACT.md").read_text(encoding="utf-8")
    ).lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in combined
