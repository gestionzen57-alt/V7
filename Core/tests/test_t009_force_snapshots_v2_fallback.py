import sqlite3
from datetime import datetime, timedelta, timezone

from Core.pf_battlefield_flux import BattlefieldFlux


def _iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def test_force_snapshots_v2_fallback_m1_proxy(tmp_path):
    db_path = tmp_path / "powerflow.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE force_snapshots_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            symbol TEXT,
            timeframe INTEGER,
            bid REAL,
            ask REAL,
            mid REAL,
            spread REAL,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            tick_volume INTEGER
        )
        """
    )

    now = datetime.now(timezone.utc)
    rows = [
        (_iso(now - timedelta(minutes=2)), "GBPUSD", 1, 1.2700, 1.2702, 1.2701, 0.0002, 1.2700, 1.2705, 1.2698, 1.2704, 100),
        (_iso(now - timedelta(minutes=1)), "GBPUSD", 1, 1.2704, 1.2706, 1.2705, 0.0002, 1.2704, 1.2707, 1.2702, 1.2703, 90),
        (_iso(now - timedelta(minutes=1)), "GBPUSD", 5, 1.2800, 1.2802, 1.2801, 0.0002, 1.2800, 1.2810, 1.2790, 1.2805, 50),
        (_iso(now - timedelta(minutes=1)), "EURUSD", 1, 1.1000, 1.1002, 1.1001, 0.0002, 1.1000, 1.1005, 1.0998, 1.1004, 100),
    ]
    conn.executemany(
        """
        INSERT INTO force_snapshots_v2
        (created_at, symbol, timeframe, bid, ask, mid, spread, open, high, low, close, tick_volume)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    conn.close()

    bf = BattlefieldFlux(db_path=str(tmp_path / "missing_tick_archive.db"), fallback_db=str(db_path))
    ticks = bf.load_ticks_fallback("GBPUSD", 10)

    assert len(ticks) == 8
    assert {tick["source_mode"] for tick in ticks} == {"M1_BAR_PROXY"}
    assert {tick["data_visibility"] for tick in ticks} == {"RECONSTRUCTED"}
    assert {tick["confidence_cap"] for tick in ticks} == {0.35}
    assert {tick["live_telegram_allowed"] for tick in ticks} == {False}
    assert all(tick["source"] == "powerflow_db_force_snapshots_v2" for tick in ticks)
    assert min(tick["mid"] for tick in ticks) < 1.2710
    assert max(tick["mid"] for tick in ticks) < 1.2710
