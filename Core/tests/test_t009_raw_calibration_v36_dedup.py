# -*- coding: utf-8 -*-
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from Core.pf_t009_raw_calibration import (
    RAW_DEDUP_MODE,
    compute_raw_calibration_metrics,
    read_raw_ticks,
    calibrate_raw_window,
)


def _rows_without_duplicates():
    return [
        {"ts_utc": "2026-05-15T08:00:00Z", "bid": 1.1000, "ask": 1.1002, "mid": 1.1001, "spread": 0.0002},
        {"ts_utc": "2026-05-15T08:00:10Z", "bid": 1.1004, "ask": 1.1006, "mid": 1.1005, "spread": 0.0002},
        {"ts_utc": "2026-05-15T08:00:20Z", "bid": 1.1009, "ask": 1.1011, "mid": 1.1010, "spread": 0.0002},
    ]


def _rows_with_exact_duplicates():
    rows = _rows_without_duplicates()
    return [rows[0], rows[0].copy(), rows[1], rows[1].copy(), rows[2]]


def test_db_without_duplicates_keeps_same_metrics():
    metrics = compute_raw_calibration_metrics(_rows_without_duplicates())

    assert metrics["raw_dedup_mode"] == RAW_DEDUP_MODE
    assert metrics["raw_tick_count_raw"] == 3
    assert metrics["raw_tick_count_dedup"] == 3
    assert metrics["raw_duplicate_count"] == 0
    assert metrics["raw_duplicate_ratio"] == 0.0
    assert metrics["raw_delta_pips"] == pytest.approx(9.0)
    assert metrics["raw_range_pips"] == pytest.approx(9.0)


def test_db_with_exact_duplicates_reduces_raw_tick_count_dedup():
    metrics = compute_raw_calibration_metrics(_rows_with_exact_duplicates())

    assert metrics["raw_tick_count_raw"] == 5
    assert metrics["raw_tick_count_dedup"] == 3
    assert metrics["raw_duplicate_count"] == 2
    assert metrics["raw_delta_pips"] == pytest.approx(9.0)
    assert metrics["raw_range_pips"] == pytest.approx(9.0)


def test_duplicate_ratio_is_exposed():
    metrics = compute_raw_calibration_metrics(_rows_with_exact_duplicates())

    assert "raw_duplicate_ratio" in metrics
    assert metrics["raw_duplicate_ratio"] == pytest.approx(0.4)


def test_raw_delta_and_range_are_computed_on_deduplicated_ticks():
    rows = _rows_with_exact_duplicates()
    # Duplicate an internal extreme many times. It must not alter delta/range.
    rows.extend([rows[-1].copy() for _ in range(10)])
    metrics = compute_raw_calibration_metrics(rows)

    assert metrics["raw_tick_count_raw"] == 15
    assert metrics["raw_tick_count_dedup"] == 3
    assert metrics["raw_delta_pips"] == pytest.approx(9.0)
    assert metrics["raw_range_pips"] == pytest.approx(9.0)


def test_read_raw_ticks_sql_distinct(tmp_path: Path):
    db_path = tmp_path / "tick_archive.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE ticks (symbol TEXT, ts_utc TEXT, bid REAL, ask REAL, mid REAL, spread REAL)"
    )
    row = ("GBPUSD", "2026-05-15T08:00:00Z", 1.10, 1.1002, 1.1001, 0.0002)
    conn.execute("INSERT INTO ticks VALUES (?, ?, ?, ?, ?, ?)", row)
    conn.execute("INSERT INTO ticks VALUES (?, ?, ?, ?, ?, ?)", row)
    conn.execute(
        "INSERT INTO ticks VALUES (?, ?, ?, ?, ?, ?)",
        ("GBPUSD", "2026-05-15T08:00:05Z", 1.1003, 1.1005, 1.1004, 0.0002),
    )
    conn.commit()

    raw = read_raw_ticks(
        conn,
        symbol="GBPUSD",
        start_utc="2026-05-15T08:00:00Z",
        end_utc="2026-05-15T08:00:10Z",
        deduplicated=False,
    )
    dedup = read_raw_ticks(
        conn,
        symbol="GBPUSD",
        start_utc="2026-05-15T08:00:00Z",
        end_utc="2026-05-15T08:00:10Z",
        deduplicated=True,
    )

    assert len(raw) == 3
    assert len(dedup) == 2


def test_calibrate_raw_window_reports_dedup_sql_match(tmp_path: Path):
    db_path = tmp_path / "tick_archive.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        "CREATE TABLE ticks (symbol TEXT, ts_utc TEXT, bid REAL, ask REAL, mid REAL, spread REAL)"
    )
    for row in _rows_with_exact_duplicates():
        conn.execute(
            "INSERT INTO ticks VALUES (?, ?, ?, ?, ?, ?)",
            ("GBPUSD", row["ts_utc"], row["bid"], row["ask"], row["mid"], row["spread"]),
        )
    conn.commit()
    conn.close()

    metrics = calibrate_raw_window(
        db_path,
        symbol="GBPUSD",
        start_utc="2026-05-15T08:00:00Z",
        end_utc="2026-05-15T08:00:20Z",
    )

    assert metrics["source_mode"] == "HISTORICAL_RAW"
    assert metrics["data_visibility"] == "MT5_RAW_ALIGNED"
    assert metrics["raw_tick_count_raw"] == 5
    assert metrics["raw_tick_count_dedup"] == 3
    assert metrics["raw_tick_count_dedup_sql"] == 3
    assert metrics["raw_dedup_sql_matches_memory"] is True


def test_no_db_write_statements_in_raw_calibration_module():
    source = Path("Core/pf_t009_raw_calibration.py").read_text(encoding="utf-8")
    forbidden = ["INSERT ", "UPDATE ", "DELETE ", "REPLACE ", "DROP ", "ALTER ", "CREATE TABLE"]
    upper_source = source.upper()

    for token in forbidden:
        assert token not in upper_source


def test_no_decision_language_in_raw_calibration_report():
    report = Path("Core/docs/Reports/B9_RAW_CALIBRATION_V36_DEDUP_REPORT.md").read_text(encoding="utf-8")
    forbidden = ["BUY", "SELL", "ENTRY", "EXIT", "SIGNAL CONFIRMED", "FOOTPRINT EXACT"]
    upper_report = report.upper()

    for token in forbidden:
        assert token not in upper_report
