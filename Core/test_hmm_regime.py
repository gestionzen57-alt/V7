import os
import sqlite3
import tempfile
from pathlib import Path

from pf_hmm_regime_engine import HMMRegimeEngine


def make_db(path, rows=60, wide=True):
    conn = sqlite3.connect(path)
    if wide:
        conn.execute("CREATE TABLE force_snapshots (time TEXT, timeframe INTEGER, symbol TEXT, GBP REAL, USD REAL)")
        for tf in (60, 30, 15):
            for i in range(rows):
                conn.execute("INSERT INTO force_snapshots VALUES (?, ?, ?, ?, ?)", (f"t{i:04d}", tf, "GBPUSD", i * 0.1, -i * 0.05))
    else:
        conn.execute("CREATE TABLE force_snapshots (created_at TEXT, timeframe INTEGER, symbol TEXT, force_value REAL)")
        for tf in (60, 30, 15):
            for i in range(rows):
                conn.execute("INSERT INTO force_snapshots VALUES (?, ?, ?, ?)", (f"t{i:04d}", tf, "GBPUSD", i * 0.1))
    conn.commit()
    conn.close()


def test_mtf_active_without_tf1440_wide():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "pf.db")
        make_db(db, rows=20, wide=True)
        res = HMMRegimeEngine().compute(db, "GBPUSD", [60, 30, 15])
        assert res["status"] == "ACTIVE", res
        assert res["regime_hmm"] in {"COMPRESSION", "TENDANCE", "RANGE", "TRANSITION"}
        assert 0 <= res["regime_confidence_hmm"] <= 1


def test_generic_numeric_schema_active():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "pf.db")
        make_db(db, rows=20, wide=False)
        res = HMMRegimeEngine().compute(db, "GBPUSD", [60, 30, 15])
        assert res["status"] == "ACTIVE", res
        assert res["schema_mode"] == "generic_numeric_stream", res


def test_insufficient_guard():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "pf.db")
        make_db(db, rows=3, wide=True)
        res = HMMRegimeEngine().compute(db, "GBPUSD", [60, 30, 15])
        assert res["status"] == "INSUFFICIENT_DATA", res
        assert res["fallback"] == "B1_LEGACY", res


if __name__ == "__main__":
    test_mtf_active_without_tf1440_wide()
    test_generic_numeric_schema_active()
    test_insufficient_guard()
    print("test_hmm_regime PASS")
