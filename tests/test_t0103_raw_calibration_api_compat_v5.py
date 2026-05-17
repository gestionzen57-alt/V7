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


def test_runner_expected_api_is_importable():
    mod = load_module()
    for name in [
        "RawCalibrationConfig",
        "calibrate_summary_with_raw",
        "export_json",
        "export_markdown",
        "load_json",
    ]:
        assert hasattr(mod, name), name


def test_raw_calibration_config_accepts_runner_arguments():
    mod = load_module()
    cfg = mod.RawCalibrationConfig(
        tick_db_path="tick_archive.db",
        symbol="GBPUSD",
        broker="OneFunded Capital Ltd.",
        broker_time_shift_min=180,
        raw_source_mode="HISTORICAL_RAW",
        raw_data_visibility="MT5_RAW_ALIGNED",
        raw_confidence_cap=0.55,
        pip_size=0.0001,
    )
    assert cfg.tick_db_path == "tick_archive.db"
    assert cfg.broker_time_shift_min == 180
    assert cfg.raw_data_visibility == "MT5_RAW_ALIGNED"
    assert cfg.pip_size == 0.0001


def test_calibrate_summary_with_raw_uses_dedup_read(tmp_path):
    mod = load_module()
    db = tmp_path / "tick_archive.db"
    conn = sqlite3.connect(db)
    conn.execute(
        "CREATE TABLE tick_stream (ts_utc TEXT, symbol TEXT, source_mode TEXT, bid REAL, ask REAL, mid REAL, spread REAL, capture_seq INTEGER)"
    )
    rows = [
        ("2026-05-15T05:00:00Z", "GBPUSD", "HISTORICAL_RAW", 1.1000, 1.1002, 1.1001, 0.0002, 1),
        ("2026-05-15T05:00:00Z", "GBPUSD", "HISTORICAL_RAW", 1.1000, 1.1002, 1.1001, 0.0002, 2),
        ("2026-05-15T05:00:30Z", "GBPUSD", "HISTORICAL_RAW", 1.1005, 1.1007, 1.1006, 0.0002, 3),
        ("2026-05-15T05:01:00Z", "GBPUSD", "HISTORICAL_RAW", 1.1008, 1.1010, 1.1009, 0.0002, 4),
    ]
    conn.executemany("INSERT INTO tick_stream VALUES (?,?,?,?,?,?,?,?)", rows)
    conn.commit()
    conn.close()

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
        broker_time_shift_min=180,
        raw_source_mode="HISTORICAL_RAW",
        raw_data_visibility="MT5_RAW_ALIGNED",
    )
    out = mod.calibrate_summary_with_raw(summary, cfg)
    m = out["moments"][0]
    assert m["raw_tick_count_raw"] == 4
    assert m["raw_tick_count_dedup"] == 3
    assert m["raw_duplicate_count"] == 1
    assert m["proxy_vs_raw_verdict"] in {"CONFIRMED_BY_RAW", "NUANCED_BY_RAW"}


def test_export_functions_write_files(tmp_path):
    mod = load_module()
    payload = {"moments": []}
    jp = mod.export_json(payload, tmp_path / "out.json")
    mp = mod.export_markdown(payload, tmp_path / "out.md")
    assert Path(jp).exists()
    assert Path(mp).exists()


def test_t0103_runner_fails_fast_on_python_errors():
    runner = ROOT / "scripts" / "RUN_T0103_WEEKLY_RAW_CALIBRATION_V36.ps1"
    text = runner.read_text(encoding="utf-8")
    assert "$LASTEXITCODE -ne 0" in text
    assert "Raw calibration failed" in text
    assert "Weekly report aggregation failed" in text


def test_hotfix_report_mentions_readonly_constraints():
    report = ROOT / "Docs" / "Reports" / "T0103_RAW_CALIBRATION_API_COMPAT_V5_REPORT.md"
    text = report.read_text(encoding="utf-8")
    assert "no `powerflow.db` write" in text
    assert "no `tick_archive.db` write" in text
    assert "rapport vide" in text.lower()


def test_no_decision_language_in_v5_report():
    report = ROOT / "Docs" / "Reports" / "T0103_RAW_CALIBRATION_API_COMPAT_V5_REPORT.md"
    text = report.read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in text
