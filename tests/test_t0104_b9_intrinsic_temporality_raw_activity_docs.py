# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "Docs" / "Contracts" / "B9_INTRINSIC_TEMPORALITY_RAW_ACTIVITY_CONTRACT.md"
REPORT = ROOT / "Docs" / "Reports" / "T0104_B9_INTRINSIC_TEMPORALITY_RAW_ACTIVITY_REPORT.md"

def test_contract_and_report_exist():
    assert CONTRACT.exists()
    assert REPORT.exists()

def test_b9_intrinsic_temporality_is_independent():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "B9 must not depend on the future external Temporalité brick" in text
    assert "B9 already has its own intrinsic temporality" in text
    assert "microfilm" in text

def test_required_b9_intrinsic_fields_are_present():
    text = CONTRACT.read_text(encoding="utf-8")
    required = [
        "b9_dwell_seconds",
        "b9_compression_seconds",
        "b9_release_seconds",
        "b9_retest_delay_seconds",
        "b9_center_migration_speed_pips_per_min",
    ]
    for item in required:
        assert item in text

def test_raw_activity_and_spread_are_prioritized():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "raw_tick_density_per_second" in text
    assert "raw_gap_median_ms" in text
    assert "raw_spread_mean" in text
    assert "raw_spread_stability_state" in text

def test_mt5_volume_is_experimental_only():
    text = CONTRACT.read_text(encoding="utf-8")
    assert "MT5 volume must not be treated as global Forex volume" in text
    assert "VOLUME_EXPERIMENTAL_ONLY" in text
    assert "raw_volume_visibility_state" in text

def test_forbidden_volume_claims_are_documented():
    text = CONTRACT.read_text(encoding="utf-8")
    forbidden_claims = [
        "real market volume confirms",
        "institutional absorption confirmed",
        "global Forex volume confirms",
    ]
    for item in forbidden_claims:
        assert item in text

def test_no_decision_language():
    combined = (CONTRACT.read_text(encoding="utf-8") + "\n" + REPORT.read_text(encoding="utf-8")).lower()
    forbidden = [
        "acheter maintenant",
        "vendre maintenant",
        "buy now",
        "sell now",
        "signal garanti",
    ]
    for phrase in forbidden:
        assert phrase not in combined

def test_constraints_visible():
    text = REPORT.read_text(encoding="utf-8")
    for item in ["no DB write", "no dashboard", "no Telegram", "no BUY/SELL"]:
        assert item in text
