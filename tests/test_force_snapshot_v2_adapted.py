import sqlite3
from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db.py"
spec = importlib.util.spec_from_file_location("db_under_test", DB_PATH)
db = importlib.util.module_from_spec(spec)
sys.modules["db_under_test"] = db
spec.loader.exec_module(db)


def make_snapshot():
    return {
        "symbol": "GBPUSD", "tf": 1, "tf_name": "M1",
        "bar_time": 1778025660.0, "bar_close_time": 1778025720.0,
        "server_time": 1778025721.0, "capture_time": 1778025722.0,
        "shift": 0, "is_closed_bar": True,
        "open": 1.3350, "high": 1.3360, "low": 1.3345, "close": 1.3355,
        "tick_volume": 123, "spread_points": 12, "spread_price": 0.00012,
        "bid": 1.33549, "ask": 1.33561, "mid": 1.33555,
        "aud": -0.1, "gbp": 0.7, "jpy": -0.2, "usd": -0.4,
        "cad": 0.1, "eur": 0.2, "chf": -0.3, "nzd": 0.05,
        "created_at": "2026-05-18T12:00:00+00:00",
    }


def test_current_schema_tf_compact_currency_names():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE force_snapshots_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT, tf INTEGER, tf_name TEXT,
            bar_time REAL, bar_close_time REAL, server_time REAL, capture_time REAL,
            shift INTEGER, is_closed_bar INTEGER,
            open REAL, high REAL, low REAL, close REAL, tick_volume REAL,
            spread_points REAL, spread_price REAL, bid REAL, ask REAL, mid REAL,
            aud REAL, gbp REAL, jpy REAL, usd REAL, cad REAL, eur REAL, chf REAL, nzd REAL,
            created_at TEXT,
            UNIQUE(symbol, tf, bar_time)
        )
    """)
    rowid = db.insert_force_snapshot_v2_adapted(conn, make_snapshot())
    assert rowid == 1
    row = conn.execute("SELECT symbol, tf, tf_name, gbp, usd, created_at FROM force_snapshots_v2").fetchone()
    assert row == ("GBPUSD", 1, "M1", 0.7, -0.4, "2026-05-18T12:00:00+00:00")


def test_legacy_schema_timeframe_force_currency_names():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE force_snapshots_v2 (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, symbol TEXT, timeframe INTEGER,
            bar_time REAL, bar_close_time REAL, server_time REAL, capture_time REAL,
            is_closed_bar INTEGER, bid REAL, ask REAL, mid REAL,
            spread REAL, spread_points REAL, spread_price REAL, spread_pips REAL,
            open REAL, high REAL, low REAL, close REAL, tick_volume REAL,
            pip_range REAL, pip_body REAL, pip_change REAL,
            force_gbp REAL, force_usd REAL, force_eur REAL, force_jpy REAL,
            force_cad REAL, force_chf REAL, force_aud REAL, force_nzd REAL,
            UNIQUE(symbol, timeframe, bar_time)
        )
    """)
    rowid = db.insert_force_snapshot_v2_adapted(conn, make_snapshot())
    assert rowid == 1
    row = conn.execute("SELECT symbol, timeframe, force_gbp, force_usd FROM force_snapshots_v2").fetchone()
    assert row == ("GBPUSD", 1, 0.7, -0.4)


def test_wrapper_does_not_crash_without_legacy_table():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE force_snapshots_v2 (id INTEGER PRIMARY KEY AUTOINCREMENT, symbol TEXT, tf INTEGER, gbp REAL, usd REAL, created_at TEXT)")
    rowid = db.insert_force_snapshot(conn, make_snapshot())
    assert rowid == 1
