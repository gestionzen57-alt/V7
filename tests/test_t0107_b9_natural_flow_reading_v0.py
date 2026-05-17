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
    rows = []
    times = ["05:00:00", "05:00:10", "05:00:20", "05:00:30", "05:00:40", "05:01:00"]
    if mode == "rotation":
        mids = [1.1000, 1.1006, 1.0999, 1.1005, 1.1001, 1.1002]
    elif mode == "unstable":
        mids = [1.1000, 1.1004, 1.1008, 1.1010, 1.1012, 1.1013]
    else:
        mids = [1.1000, 1.1003, 1.1006, 1.1009, 1.1012, 1.1015]

    for i, (t, mid) in enumerate(zip(times, mids)):
        spread = 0.0015 if mode == "unstable" and i == 2 else 0.0002
        bid = mid - spread / 2
        ask = mid + spread / 2
        rows.append((f"2026-05-15T{t}Z", "GBPUSD", "HISTORICAL_RAW", bid, ask, mid, spread, i + 1, i + 1))
    rows.append(rows[0])
    conn.executemany("INSERT INTO tick_stream VALUES (?,?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()


def calibrate(tmp_path, mode="directional"):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    build_db(db, mode=mode)
    summary = {
        "moments": [
            {
                "moment_id": "m1",
                "moment_type": "T009_MOMENT_PROGRESSIVE_WAVE",
                "label_fr": "Vague progressive",
                "time_start": "2026-05-15T08:00:00Z",
                "time_end": "2026-05-15T08:01:00Z",
                "center_delta_pips": 12.0,
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


def test_t0107_fields_are_added(tmp_path):
    payload, m = calibrate(tmp_path)
    required = [
        "b9_natural_flow_version",
        "b9_directional_efficiency",
        "b9_effort_load",
        "b9_effort_result_ratio",
        "b9_flow_intent_state",
        "b9_absorption_like_state",
        "b9_exhaustion_like_state",
        "b9_initiative_response_state",
        "b9_auction_state",
        "b9_trap_risk_state",
        "b9_market_readability_state",
        "b9_natural_flow_reading_fr",
    ]
    for field in required:
        assert field in m, field
    assert payload["raw_calibration"]["version"] == "T0107_NATURAL_FLOW_READING_V0"


def test_directional_flow_can_be_detected(tmp_path):
    payload, m = calibrate(tmp_path, mode="directional")
    assert m["b9_flow_intent_state"] in {
        "FLOW_DIRECTIONAL_DISPLACEMENT",
        "FLOW_MIXED",
        "FLOW_UNSTABLE_QUOTE_TEXTURE",
    }
    assert 0.0 <= m["b9_directional_efficiency"] <= 1.0


def test_rotation_is_not_forced_into_directional_truth(tmp_path):
    payload, m = calibrate(tmp_path, mode="rotation")
    assert m["b9_flow_intent_state"] in {
        "FLOW_ROTATIONAL",
        "FLOW_BALANCED_AUCTION",
        "FLOW_MIXED",
        "FLOW_UNSTABLE_QUOTE_TEXTURE",
    }
    assert m["b9_trap_risk_state"] in {
        "TRAP_RISK_HIGH_PROGRESSIVE_ROTATIONAL",
        "TRAP_RISK_MEDIUM_EFFORT_WITHOUT_RESULT",
        "TRAP_RISK_MEDIUM_TEXTURE_CAUTION",
        "TRAP_RISK_LOW",
        "TRAP_RISK_DATA_TEXTURE_LIMIT",
    }


def test_unstable_spread_limits_reading(tmp_path):
    payload, m = calibrate(tmp_path, mode="unstable")
    assert m["b9_market_readability_state"] in {
        "READABILITY_LIMITED_BY_TEXTURE",
        "READABILITY_HIGH",
        "READABILITY_MEDIUM",
        "READABILITY_LOW",
        "READABILITY_VERY_LOW",
    }
    assert "broker-relative" in " ".join(m["b9_natural_flow_limits"])


def test_natural_flow_sentence_is_french_and_interpretive(tmp_path):
    payload, m = calibrate(tmp_path)
    text = m["b9_natural_flow_reading_fr"]
    assert isinstance(text, str)
    assert len(text) > 10
    assert "Flux" in text or "Lecture" in text or "Piège" in text or "Friction" in text


def test_no_external_temporality_dependency(tmp_path):
    payload, m = calibrate(tmp_path)
    assert payload["raw_calibration"]["external_temporality_dependency"] is False
    assert "external Temporalité brick is not used" in payload["raw_calibration"]["limits"]


def test_volume_policy_remains_broker_relative(tmp_path):
    payload, m = calibrate(tmp_path)
    assert payload["raw_calibration"]["volume_policy"] == "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL"
    assert "MT5 volume is not global Forex volume" in payload["raw_calibration"]["limits"]


def test_dedup_and_t0106_fields_survive(tmp_path):
    payload, m = calibrate(tmp_path)
    assert m["raw_tick_count_raw"] == 7
    assert m["raw_tick_count_dedup"] == 6
    assert "b9_microfilm_texture_score" in m
    assert "b9_volume_factor_state" in m


def test_report_and_contract_exist():
    assert (ROOT / "Docs" / "Reports" / "T0107_B9_NATURAL_FLOW_READING_V0_REPORT.md").exists()
    assert (ROOT / "Docs" / "Contracts" / "B9_NATURAL_FLOW_READING_V0_CONTRACT.md").exists()


def test_no_decision_language():
    combined = (
        (ROOT / "Docs" / "Reports" / "T0107_B9_NATURAL_FLOW_READING_V0_REPORT.md").read_text(encoding="utf-8")
        + "\n"
        + (ROOT / "Docs" / "Contracts" / "B9_NATURAL_FLOW_READING_V0_CONTRACT.md").read_text(encoding="utf-8")
    ).lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in combined
