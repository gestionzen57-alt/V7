"""Unit tests for B8 Cross-Symbol Validation."""

from __future__ import annotations

import os
import sqlite3
import tempfile
from dataclasses import asdict

import pytest

from pf_cross_symbol_validation import (
    CrossValidationMetrics,
    CrossValidationState,
    DriverDetection,
    calculate_consistency_score,
    classify_global_strength,
    detect_driver,
    extract_angles_for_symbol,
    trigger_alert_if_needed,
    validate_cross_symbol,
)


def make_db(rows):
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    conn = sqlite3.connect(path)
    conn.execute(
        """
        CREATE TABLE force_snapshots (
            symbol TEXT,
            timeframe INTEGER,
            timestamp TEXT,
            angle_kalman REAL,
            open REAL,
            close REAL
        )
        """
    )
    conn.executemany(
        "INSERT INTO force_snapshots VALUES (?, ?, ?, ?, ?, ?)",
        rows,
    )
    conn.commit()
    conn.close()
    return path


def test_extract_angles_for_symbol():
    rows = [
        ("GBPUSD", 1, "2026-05-12T09:15:00Z", 65.0, 1.0, 1.1),
        ("GBPEUR", 1, "2026-05-12T09:15:00Z", 50.0, 1.0, 1.1),
        ("GBPJPY", 1, "2026-05-12T09:15:00Z", 45.0, 1.0, 1.1),
    ]
    path = make_db(rows)
    try:
        angles = extract_angles_for_symbol("GBP", path, 1)
        assert angles["GBPUSD"] == 65.0
        assert angles["GBPEUR"] == 50.0
        assert angles["GBPJPY"] == 45.0
    finally:
        os.remove(path)


def test_extract_angles_inverts_quote_currency():
    rows = [
        ("GBPUSD", 1, "2026-05-12T09:15:00Z", 65.0, 1.0, 1.1),
        ("EURUSD", 1, "2026-05-12T09:15:00Z", 40.0, 1.0, 1.1),
        ("USDJPY", 1, "2026-05-12T09:15:00Z", -10.0, 1.0, 1.1),
    ]
    path = make_db(rows)
    try:
        angles = extract_angles_for_symbol("USD", path, 1)
        assert angles["GBPUSD"] == -65.0
        assert angles["EURUSD"] == -40.0
        assert angles["USDJPY"] == -10.0
    finally:
        os.remove(path)


def test_consistency_score_high():
    angles = {
        "GBPUSD": 50,
        "GBPEUR": 50,
        "GBPJPY": 50,
        "GBPCHF": 50,
        "GBPCAD": 50,
        "GBPAUD": 50,
    }
    assert calculate_consistency_score(angles) > 0.98


def test_consistency_score_low():
    angles = {
        "GBPUSD": 80,
        "GBPEUR": -10,
        "GBPJPY": 20,
        "GBPCHF": -30,
        "GBPCAD": 60,
        "GBPAUD": -50,
    }
    assert calculate_consistency_score(angles) < 0.30


def test_classify_global_strength():
    assert classify_global_strength(65, 0.85) == "VERY_STRONG"
    assert classify_global_strength(52, 0.75) == "STRONG"
    assert classify_global_strength(5, 0.70) == "NEUTRAL"
    assert classify_global_strength(-65, 0.85) == "VERY_WEAK"


def test_driver_detection_gbp_strength():
    angles = {
        "GBPUSD": 65,
        "GBPEUR": 50,
        "GBPJPY": 45,
        "GBPCHF": 55,
        "GBPCAD": 48,
        "GBPAUD": 52,
    }
    driver = detect_driver("GBP", angles, 0.85)
    assert driver.primary_driver == "GBP_STRENGTH"
    assert driver.confidence > 0.80


def test_driver_detection_usd_weakness():
    angles = {
        "GBPUSD": 65,
        "GBPEUR": -15,
        "GBPJPY": -20,
        "GBPCHF": -10,
        "GBPCAD": -5,
        "GBPAUD": 25,
    }
    driver = detect_driver("GBP", angles, 0.45)
    assert driver.primary_driver == "USD_WEAKNESS"
    assert "GBPUSD outlier" in driver.evidence["reasoning"]


def test_alert_triggered_on_confirmed_driver():
    state = CrossValidationState(
        timestamp="2026-05-12T09:15:00Z",
        symbol="GBP",
        timeframe=1,
        metrics=CrossValidationMetrics(
            symbol="GBP",
            angles={"GBPUSD": 65, "GBPEUR": 50, "GBPJPY": 45},
            mean_angle=53.33,
            std_angle=8.5,
            consistency_score=0.85,
            global_strength="STRONG",
            confidence=0.87,
        ),
        driver_detection=DriverDetection(
            primary_driver="GBP_STRENGTH",
            secondary_driver=None,
            confidence=0.88,
            evidence={},
        ),
        cross_pair_details={"GBPUSD": 65, "GBPEUR": 50, "GBPJPY": 45},
        alert_triggered=True,
        alert_type="DRIVER_CONFIRMED",
    )
    alert = trigger_alert_if_needed(state)
    assert alert is not None
    assert alert["driver"] == "GBP_STRENGTH"
    assert alert["alert_type"] == "DRIVER_DETECTION_CONFIRMED"


def test_no_alert_on_mild_mixed_signal():
    state = CrossValidationState(
        timestamp="2026-05-12T09:15:00Z",
        symbol="GBP",
        timeframe=1,
        metrics=CrossValidationMetrics(
            symbol="GBP",
            angles={"GBPUSD": 25, "GBPEUR": 10, "GBPJPY": -5},
            mean_angle=10.0,
            std_angle=12.2,
            consistency_score=0.55,
            global_strength="MIXED_SIGNAL",
            confidence=0.45,
        ),
        driver_detection=DriverDetection(
            primary_driver="MIXED",
            secondary_driver=None,
            confidence=0.45,
            evidence={},
        ),
        cross_pair_details={"GBPUSD": 25, "GBPEUR": 10, "GBPJPY": -5},
        alert_triggered=False,
        alert_type=None,
    )
    assert trigger_alert_if_needed(state) is None


def test_validate_cross_symbol_pipeline():
    rows = [
        ("GBPUSD", 1, "2026-05-12T09:15:00Z", 65.0, 1.0, 1.1),
        ("GBPEUR", 1, "2026-05-12T09:15:00Z", 50.0, 1.0, 1.1),
        ("GBPJPY", 1, "2026-05-12T09:15:00Z", 45.0, 1.0, 1.1),
        ("GBPCHF", 1, "2026-05-12T09:15:00Z", 55.0, 1.0, 1.1),
    ]
    path = make_db(rows)
    try:
        state = validate_cross_symbol("GBP", path, 1)
        state_dict = asdict(state)
        assert state_dict["driver_detection"]["primary_driver"] == "GBP_STRENGTH"
        assert state_dict["metrics"]["global_strength"] in {"STRONG", "VERY_STRONG"}
    finally:
        os.remove(path)
