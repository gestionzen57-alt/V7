import sqlite3
import time
from pathlib import Path

import pytest


SCHEMA_PATH = Path("tick_archive_schema.sql")


def _create_db(tmp_path: Path) -> tuple[sqlite3.Connection, Path]:
    db_path = tmp_path / "test_tick_archive.db"
    conn = sqlite3.connect(str(db_path))
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn, db_path


def test_schema_creation(tmp_path):
    """Schema tick_archive.db created without error."""
    conn, _ = _create_db(tmp_path)

    tables = conn.execute(
        """
        SELECT name FROM sqlite_master WHERE type='table'
        """
    ).fetchall()

    table_names = [t[0] for t in tables]
    assert "tick_stream" in table_names
    assert "tick_archive_metadata" in table_names
    assert "tick_rotation_log" in table_names

    conn.close()


def test_schema_constraints(tmp_path):
    """bid/ask/mid/spread constraints are enforced."""
    conn, _ = _create_db(tmp_path)

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode)
            VALUES ('GBPUSD', '2026-05-15T12:00:00Z', 1715782800000, 0, 1.27042, 1.27041, 0.0002, 'TIMER_1S_SAMPLE')
            """
        )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode)
            VALUES ('GBPUSD', '2026-05-15T12:00:01Z', 1715782801000, 1.27043, 1.27042, 1.27041, 0.0002, 'TIMER_1S_SAMPLE')
            """
        )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode)
            VALUES ('GBPUSD', '2026-05-15T12:00:02Z', 1715782802000, 1.27040, 1.27042, 1.27041, -0.0001, 'TIMER_1S_SAMPLE')
            """
        )

    conn.close()


def test_unique_index(tmp_path):
    """Unique index rejects duplicate tick identity."""
    conn, _ = _create_db(tmp_path)

    conn.execute(
        """
        INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode, capture_seq)
        VALUES ('GBPUSD', '2026-05-15T12:00:00Z', 1715782800000, 1.27040, 1.27042, 1.27041, 0.0002, 'TIMER_1S_SAMPLE', 0)
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode, capture_seq)
            VALUES ('GBPUSD', '2026-05-15T12:00:00Z', 1715782800000, 1.27041, 1.27043, 1.27042, 0.0002, 'TIMER_1S_SAMPLE', 0)
            """
        )

    conn.close()


def test_source_mode_constraint(tmp_path):
    """source_mode accepts only valid Phase 0 source modes."""
    conn, _ = _create_db(tmp_path)

    conn.execute(
        """
        INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode)
        VALUES ('GBPUSD', '2026-05-15T12:00:00Z', 1715782800000, 1.27040, 1.27042, 1.27041, 0.0002, 'TIMER_1S_SAMPLE')
        """
    )

    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            """
            INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode)
            VALUES ('GBPUSD', '2026-05-15T12:00:01Z', 1715782801000, 1.27040, 1.27042, 1.27041, 0.0002, 'INVALID_MODE')
            """
        )

    conn.close()


def test_query_performance_120min(tmp_path):
    """Query 120 minutes of 1 Hz data in less than 1 second."""
    conn, _ = _create_db(tmp_path)

    base_epoch = 1715782800000
    rows_to_insert = []
    for i in range(7200):
        rows_to_insert.append(
            (
                "GBPUSD",
                f"2026-05-15T12:{i // 60:02d}:{i % 60:02d}Z",
                base_epoch + i * 1000,
                1.27040,
                1.27042,
                1.27041,
                0.0002,
                "TIMER_1S_SAMPLE",
            )
        )

    conn.executemany(
        """
        INSERT INTO tick_stream (symbol, ts_utc, ts_epoch_ms, bid, ask, mid, spread, source_mode)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()

    start = time.time()
    cursor = conn.execute(
        """
        SELECT * FROM tick_stream
        WHERE symbol = 'GBPUSD'
        AND ts_epoch_ms >= ?
        AND ts_epoch_ms <= ?
        """,
        (base_epoch, base_epoch + 7200 * 1000),
    )

    rows = cursor.fetchall()
    duration = time.time() - start

    assert len(rows) == 7200
    assert duration < 1.0

    conn.close()
