from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pf_b8_data_visibility import B8DataVisibilityChecker


MINIMUM_TFS = [5, 15, 30, 60, 240]
B8_13 = [
    "GBPUSD",
    "EURUSD",
    "AUDUSD",
    "NZDUSD",
    "USDJPY",
    "USDCAD",
    "USDCHF",
    "EURGBP",
    "GBPJPY",
    "GBPAUD",
    "GBPCAD",
    "GBPCHF",
    "GBPNZD",
]
B8_28 = [
    "EURUSD",
    "GBPUSD",
    "AUDUSD",
    "NZDUSD",
    "USDJPY",
    "USDCHF",
    "USDCAD",
    "EURGBP",
    "EURJPY",
    "EURCHF",
    "EURCAD",
    "EURAUD",
    "EURNZD",
    "GBPJPY",
    "GBPCHF",
    "GBPCAD",
    "GBPAUD",
    "GBPNZD",
    "AUDJPY",
    "AUDCHF",
    "AUDCAD",
    "AUDNZD",
    "NZDJPY",
    "NZDCHF",
    "NZDCAD",
    "CADJPY",
    "CADCHF",
    "CHFJPY",
]


def _create_snapshot_table(conn: sqlite3.Connection, table: str) -> None:
    conn.execute(
        f"""
        CREATE TABLE {table} (
            id INTEGER PRIMARY KEY,
            symbol TEXT NOT NULL,
            timeframe INTEGER NOT NULL,
            timestamp TEXT NOT NULL,
            angle_kalman REAL
        )
        """
    )


def _insert_rows(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    count: int,
    start_time: datetime,
    minute_step: int = 1,
    tfs=None,
) -> None:
    tfs = tfs or MINIMUM_TFS
    for i in range(count):
        ts = (start_time - timedelta(minutes=i * minute_step)).isoformat()
        tf = tfs[i % len(tfs)]
        conn.execute(
            f"INSERT INTO {table} (symbol, timeframe, timestamp, angle_kalman) VALUES (?, ?, ?, ?)",
            (symbol, tf, ts, 45.0 + i * 0.01),
        )


@pytest.fixture
def test_db_with_data(tmp_path: Path) -> str:
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(str(db_path))
    _create_snapshot_table(conn, "force_snapshots")

    now = datetime.now(timezone.utc)
    _insert_rows(conn, "force_snapshots", "GBPUSD", 250, now, minute_step=1)
    _insert_rows(conn, "force_snapshots", "EURUSD", 120, now, minute_step=2)
    _insert_rows(conn, "force_snapshots", "AUDUSD", 80, now, minute_step=2)
    _insert_rows(conn, "force_snapshots", "USDJPY", 20, now - timedelta(minutes=20), minute_step=2)
    _insert_rows(conn, "force_snapshots", "USDCAD", 20, now, minute_step=2)
    # NZDUSD deliberately missing.

    conn.commit()
    conn.close()
    return str(db_path)


@pytest.fixture
def test_db_with_v2_preferred(tmp_path: Path) -> str:
    db_path = tmp_path / "test_v2.db"
    conn = sqlite3.connect(str(db_path))
    _create_snapshot_table(conn, "force_snapshots")
    _create_snapshot_table(conn, "force_snapshots_v2")

    now = datetime.now(timezone.utc)
    _insert_rows(conn, "force_snapshots", "GBPUSD", 60, now, minute_step=1)
    _insert_rows(conn, "force_snapshots_v2", "GBPUSD", 250, now, minute_step=1)

    conn.commit()
    conn.close()
    return str(db_path)


def test_checker_init():
    checker = B8DataVisibilityChecker()
    assert checker is not None
    assert checker.last_checks == {}


def test_check_symbol_dense_live_primary(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("GBPUSD")

    assert result["coverage_state"] == "DENSE"
    assert result["freshness_state"] == "LIVE"
    assert result["role_allowed"] == "PRIMARY"
    assert result["source_table"] == "force_snapshots"
    assert result["b8_weight_cap"] == 1.0
    assert result["data_quality_score"] > 0.9


def test_check_symbol_normal_live_context_or_primary(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("EURUSD")

    assert result["coverage_state"] == "NORMAL"
    assert result["freshness_state"] == "LIVE"
    assert result["role_allowed"] == "CONTEXT_ONLY"
    assert result["b8_weight_cap"] == 0.6


def test_check_symbol_thin_stale_usdjpy_context_only(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("USDJPY")

    assert result["coverage_state"] == "THIN"
    assert result["freshness_state"] == "STALE"
    assert result["role_allowed"] == "CONTEXT_ONLY"
    assert "KNOWN_SPARSE_SYMBOL" in result["technical_risks"]
    assert "LOW_SAMPLE_COUNT" in result["technical_risks"]
    assert "FEED_INTERMITTENT" in result["technical_risks"]
    assert result["b8_weight_cap"] == 0.25


def test_check_symbol_missing_data_excluded(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("NZDUSD")

    assert result["coverage_state"] == "MISSING"
    assert result["freshness_state"] == "MISSING"
    assert result["role_allowed"] == "EXCLUDED"
    assert result["b8_weight_cap"] == 0.0


def test_source_table_detection_prefers_v2(test_db_with_v2_preferred):
    checker = B8DataVisibilityChecker(test_db_with_v2_preferred)
    result = checker.check_symbol_visibility("GBPUSD")

    assert result["source_table"] == "force_snapshots_v2"
    assert result["coverage_state"] == "DENSE"


def test_d1_w1_missing_is_risk_not_blocker(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("GBPUSD")

    assert "D1" in result["missing_tfs"]
    assert "W1" in result["missing_tfs"]
    assert "HTF_D1_W1_MISSING" in result["technical_risks"]
    assert result["role_allowed"] == "PRIMARY"


def test_incomplete_minimum_tf_excluded(tmp_path: Path):
    db_path = tmp_path / "tf_missing.db"
    conn = sqlite3.connect(str(db_path))
    _create_snapshot_table(conn, "force_snapshots")
    now = datetime.now(timezone.utc)
    _insert_rows(conn, "force_snapshots", "GBPJPY", 250, now, tfs=[5])
    conn.commit()
    conn.close()

    checker = B8DataVisibilityChecker(str(db_path))
    result = checker.check_symbol_visibility("GBPJPY")

    assert result["coverage_state"] == "DENSE"
    assert result["role_allowed"] == "EXCLUDED"
    assert "INCOMPLETE_TF_COVERAGE" in result["technical_risks"]


def test_b8_universe_visibility_current(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_b8_universe_visibility(B8_13)

    assert result["universe"] == "B8_13_CURRENT"
    assert "GBPUSD" in result["primary_symbols"]
    assert "USDJPY" in result["context_only_symbols"]
    assert "NZDUSD" in result["excluded_symbols"]
    assert result["field_visibility"] in {"STRONG", "TACTICAL_OK", "DEGRADED", "CRITICAL"}
    assert result["symbols_expected"] == 13


def test_b8_universe_custom_and_28_target(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)

    custom = checker.check_b8_universe_visibility(["GBPUSD", "USDJPY"])
    assert custom["universe"] == "B8_CUSTOM"

    target = checker.check_b8_universe_visibility(B8_28)
    assert target["universe"] == "B8_28_TARGET"


def test_technical_risks_generic_thin_not_only_usdjpy(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("USDCAD")

    assert result["coverage_state"] == "THIN"
    assert "LOW_SAMPLE_COUNT" in result["technical_risks"]
    assert "SPARSE_SYMBOL" in result["technical_risks"]
    assert "KNOWN_SPARSE_SYMBOL" not in result["technical_risks"]
    assert result["b8_weight_cap"] == 0.35


def test_last_update_age_calculation(test_db_with_data):
    checker = B8DataVisibilityChecker(test_db_with_data)
    result = checker.check_symbol_visibility("GBPUSD")

    assert result["last_update_age_sec"] >= 0
    assert result["last_update_age_sec"] < 300


def test_missing_db_path_returns_safe_state():
    checker = B8DataVisibilityChecker()
    result = checker.check_symbol_visibility("GBPUSD")

    assert result["coverage_state"] == "MISSING"
    assert result["role_allowed"] == "EXCLUDED"
    assert "DB_PATH_MISSING" in result["technical_risks"]
