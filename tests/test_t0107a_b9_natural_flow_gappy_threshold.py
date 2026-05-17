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


def build_db(path, mode="directional", hard_gappy=False):
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
    if hard_gappy:
        times = ["05:00:00", "05:00:05", "05:01:20", "05:01:50"]
    else:
        times = ["05:00:00", "05:00:10", "05:00:20", "05:00:40", "05:01:00"]

    if mode == "rotation":
        mids = [1.1000, 1.1006, 1.0999, 1.1005, 1.1002]
    else:
        mids = [1.1000, 1.1003, 1.1006, 1.1009, 1.1015]

    if hard_gappy:
        mids = mids[:len(times)]

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


def calibrate(tmp_path, mode="directional", hard_gappy=False):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    build_db(db, mode=mode, hard_gappy=hard_gappy)
    end = "2026-05-15T08:02:00Z" if hard_gappy else "2026-05-15T08:01:00Z"
    summary = {
        "moments": [
            {
                "moment_id": "m1",
                "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
                "label_fr": "Vague progressive",
                "time_start": "2026-05-15T08:00:00Z",
                "time_end": end,
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
    payload = mod.calibrate_summary_with_raw(summary, cfg)
    return payload, payload["moments"][0]


def test_moderate_gap_does_not_override_directional_reading(tmp_path):
    payload, m = calibrate(tmp_path, mode="directional")
    assert m["raw_activity_profile"] == "RAW_ACTIVITY_GAPPY"
    assert m["b9_flow_intent_state"] in {
        "FLOW_DIRECTIONAL_DISPLACEMENT",
        "FLOW_MIXED",
        "FLOW_UNSTABLE_QUOTE_TEXTURE",
    }


def test_moderate_gap_does_not_force_rotation_into_gappy_limit(tmp_path):
    payload, m = calibrate(tmp_path, mode="rotation")
    assert m["raw_activity_profile"] == "RAW_ACTIVITY_GAPPY"
    assert m["b9_flow_intent_state"] in {
        "FLOW_ROTATIONAL",
        "FLOW_BALANCED_AUCTION",
        "FLOW_MIXED",
        "FLOW_UNSTABLE_QUOTE_TEXTURE",
    }


def test_hard_gap_still_limits_reading(tmp_path):
    payload, m = calibrate(tmp_path, mode="directional", hard_gappy=True)
    assert m["raw_activity_profile"] == "RAW_ACTIVITY_GAPPY"
    assert m["b9_flow_intent_state"] == "FLOW_GAPPY_LIMIT"
    assert m["b9_market_readability_state"] == "READABILITY_LIMITED_BY_TEXTURE"


def test_hotfix_report_exists():
    assert (ROOT / "Docs" / "Reports" / "T0107A_B9_NATURAL_FLOW_GAPPY_THRESHOLD_HOTFIX.md").exists()


def test_no_decision_language():
    text = (ROOT / "Docs" / "Reports" / "T0107A_B9_NATURAL_FLOW_GAPPY_THRESHOLD_HOTFIX.md").read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in text
