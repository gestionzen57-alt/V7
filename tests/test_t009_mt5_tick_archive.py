from __future__ import annotations

import csv
import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from import_mt5_ticks_csv import import_csv
from tick_archive_writer import TickArchiveWriter, utc_now_ms


@pytest.fixture
def writer(tmp_path: Path) -> TickArchiveWriter:
    return TickArchiveWriter(tmp_path / "tick_archive.db")


def base_tick(**overrides):
    tick = {
        "symbol": "GBPUSD",
        "time_msc": 1_800_000_000_000,
        "bid": 1.25000,
        "ask": 1.25010,
        "last": 1.25005,
        "volume": 1,
        "volume_real": 1.0,
        "flags": 6,
        "source": "MT5",
        "source_mode": "ONTICK_RAW",
        "broker": "UnitTestBroker",
        "server_time": "2026.05.16 10:00:00",
        "capture_seq": 1,
    }
    tick.update(overrides)
    return tick


def test_insert_raw_tick(writer: TickArchiveWriter):
    result = writer.insert_tick(base_tick())
    assert result.inserted == 1
    rows = writer.query_lookback("GBPUSD", lookback_sec=10, end_epoch_ms=1_800_000_000_500)
    assert len(rows) == 1
    assert rows[0]["symbol"] == "GBPUSD"
    assert rows[0]["source_mode"] == "ONTICK_RAW"


def test_duplicate_same_ms_capture_seq(writer: TickArchiveWriter):
    t1 = base_tick(capture_seq=1)
    t2 = base_tick(capture_seq=2)
    duplicate = base_tick(capture_seq=1)
    assert writer.insert_tick(t1).inserted == 1
    assert writer.insert_tick(t2).inserted == 1
    assert writer.insert_tick(duplicate).ignored == 1
    assert writer.count_ticks("GBPUSD") == 2


def test_gap_ms(writer: TickArchiveWriter):
    writer.insert_tick(base_tick(time_msc=1_800_000_000_000, capture_seq=1))
    writer.insert_tick(base_tick(time_msc=1_800_000_000_125, capture_seq=2))
    rows = writer.query_lookback("GBPUSD", lookback_sec=10, end_epoch_ms=1_800_000_001_000)
    assert rows[0]["gap_ms"] == 0
    assert rows[1]["gap_ms"] == 125


def test_source_mode_historical_raw(writer: TickArchiveWriter):
    writer.insert_tick(base_tick(source_mode="HISTORICAL_RAW"))
    rows = writer.query_lookback(
        "GBPUSD", lookback_sec=10, source_mode="HISTORICAL_RAW", end_epoch_ms=1_800_000_000_500
    )
    assert len(rows) == 1
    assert rows[0]["source_mode"] == "HISTORICAL_RAW"


def test_quality_flags(writer: TickArchiveWriter):
    writer.insert_tick(base_tick(bid="", ask="", last=1.25005, quality_flags="CUSTOM_FLAG"))
    rows = writer.query_lookback("GBPUSD", lookback_sec=10, end_epoch_ms=1_800_000_000_500)
    flags = rows[0]["quality_flags"]
    assert "CUSTOM_FLAG" in flags
    assert "BID_ASK_MISSING" in flags
    assert "MID_FROM_LAST" in flags


def test_query_lookback(writer: TickArchiveWriter):
    writer.insert_tick(base_tick(time_msc=1_800_000_000_000, capture_seq=1))
    writer.insert_tick(base_tick(time_msc=1_800_000_010_000, capture_seq=2))
    rows = writer.query_lookback("GBPUSD", lookback_sec=2, end_epoch_ms=1_800_000_010_500)
    assert len(rows) == 1
    assert rows[0]["capture_seq"] == 2


def test_wal_enabled(writer: TickArchiveWriter):
    assert writer.journal_mode() == "WAL"


def test_mid_spread_calculation(writer: TickArchiveWriter):
    writer.insert_tick(base_tick(bid=1.1000, ask=1.1004, mid="", spread=""))
    row = writer.query_lookback("GBPUSD", lookback_sec=10, end_epoch_ms=1_800_000_000_500)[0]
    assert row["mid"] == pytest.approx(1.1002)
    assert row["spread"] == pytest.approx(0.0004)
    assert "MID_RECONSTRUCTED" in row["quality_flags"]
    assert "SPREAD_RECONSTRUCTED" in row["quality_flags"]


def test_import_mt5_csv(tmp_path: Path):
    csv_path = tmp_path / "ticks.csv"
    db_path = tmp_path / "tick_archive.db"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer_csv = csv.DictWriter(
            handle,
            fieldnames=[
                "symbol",
                "time_msc",
                "bid",
                "ask",
                "last",
                "volume",
                "volume_real",
                "flags",
                "source_mode",
                "broker",
                "server_time",
                "capture_seq",
                "quality_flags",
            ],
        )
        writer_csv.writeheader()
        writer_csv.writerow(
            {
                "symbol": "GBPUSD",
                "time_msc": "1800000000000",
                "bid": "1.25",
                "ask": "1.2501",
                "last": "1.25005",
                "volume": "1",
                "volume_real": "1.0",
                "flags": "6",
                "source_mode": "HISTORICAL_RAW",
                "broker": "UnitTestBroker",
                "server_time": "2026.05.16 10:00:00",
                "capture_seq": "1",
                "quality_flags": "OK",
            }
        )
    summary = import_csv(csv_path, db_path)
    assert summary["inserted"] == 1
    assert TickArchiveWriter(db_path).count_ticks("GBPUSD") == 1


def test_powerflow_db_protection(tmp_path: Path):
    with pytest.raises(ValueError):
        TickArchiveWriter(tmp_path / "powerflow.db")
