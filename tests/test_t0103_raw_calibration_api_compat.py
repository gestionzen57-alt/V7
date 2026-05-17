# -*- coding: utf-8 -*-
from pathlib import Path
import importlib
import sys

ROOT = Path(__file__).resolve().parents[1]

def load_module():
    repo = str(ROOT)
    if repo not in sys.path:
        sys.path.insert(0, repo)
    if "pf_t009_raw_calibration" in sys.modules:
        del sys.modules["pf_t009_raw_calibration"]
    return importlib.import_module("pf_t009_raw_calibration")

def test_raw_calibration_config_importable():
    mod = load_module()
    assert hasattr(mod, "RawCalibrationConfig")

def test_raw_calibration_config_accepts_aliases():
    mod = load_module()
    cfg = mod.RawCalibrationConfig(
        summary_json="summary.json",
        tick_db="tick_archive.db",
        output="out",
        raw_time_shift_min=180,
        data_visibility="MT5_RAW_ALIGNED",
    )
    assert cfg.summary_json == "summary.json"
    assert cfg.tick_db == "tick_archive.db"
    assert cfg.output == "out"
    assert cfg.broker_time_shift_min == 180
    assert cfg.raw_data_visibility == "MT5_RAW_ALIGNED"

def test_raw_calibration_config_accepts_positional_args():
    mod = load_module()
    cfg = mod.RawCalibrationConfig("summary.json", "tick_archive.db", "out")
    assert cfg.summary_json == "summary.json"
    assert cfg.tick_db == "tick_archive.db"
    assert cfg.output == "out"
    assert cfg.symbol == "GBPUSD"

def test_t0103_runner_fails_fast_on_python_errors():
    runner = ROOT / "scripts" / "RUN_T0103_WEEKLY_RAW_CALIBRATION_V36.ps1"
    text = runner.read_text(encoding="utf-8")
    assert "$LASTEXITCODE -ne 0" in text
    assert "Raw calibration failed" in text
    assert "Weekly report aggregation failed" in text

def test_report_mentions_readonly_constraints():
    report = ROOT / "Docs" / "Reports" / "T0103_RAW_CALIBRATION_API_COMPAT_HOTFIX.md"
    text = report.read_text(encoding="utf-8")
    assert "no `powerflow.db` write" in text
    assert "no `tick_archive.db` write" in text

def test_no_decision_language():
    report = ROOT / "Docs" / "Reports" / "T0103_RAW_CALIBRATION_API_COMPAT_HOTFIX.md"
    text = report.read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in text
