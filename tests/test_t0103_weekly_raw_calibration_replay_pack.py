# -*- coding: utf-8 -*-
from pathlib import Path
import py_compile

ROOT = Path(__file__).resolve().parents[1]
REPORT = ROOT / "Docs" / "Reports" / "T0103_WEEKLY_RAW_CALIBRATION_REPLAY_PACK.md"
RUNNER = ROOT / "scripts" / "RUN_T0103_WEEKLY_RAW_CALIBRATION_V36.ps1"
AGG = ROOT / "tools" / "make_t0103_weekly_raw_calibration_report.py"

def test_files_exist():
    assert REPORT.exists()
    assert RUNNER.exists()
    assert AGG.exists()

def test_dedup_doctrine_visible():
    text = REPORT.read_text(encoding="utf-8")
    assert "SELECT DISTINCT ts_utc, bid, ask, mid, spread" in text
    assert "raw_ts_mt5 + 180 minutes" in text

def test_lab_categories_visible():
    text = REPORT.read_text(encoding="utf-8")
    for item in ["PROGRESSIVE_WAVE_ROTATIONAL", "RAW_PROXY_DIVERGENCE", "MEMORY_SHIFTED", "COUNTER_BREATH_REJECTED"]:
        assert item in text

def test_no_db_write_language_in_scripts():
    text = (RUNNER.read_text(encoding="utf-8") + "\n" + AGG.read_text(encoding="utf-8")).upper()
    for token in ["INSERT INTO", "UPDATE ", "DELETE FROM", "DROP TABLE", "ALTER TABLE", "MODE=RW"]:
        assert token not in text

def test_no_decision_language():
    text = REPORT.read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in text

def test_aggregator_compiles():
    py_compile.compile(str(AGG), doraise=True)
