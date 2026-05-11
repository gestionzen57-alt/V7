import sqlite3
import tempfile
from pathlib import Path

from pf_wavelet_density import WaveletDensityEngine


def make_db(path, rows=40, wide=True):
    conn = sqlite3.connect(path)
    if wide:
        conn.execute("CREATE TABLE force_snapshots (time TEXT, timeframe INTEGER, symbol TEXT, GBP REAL, USD REAL)")
        for tf in (1, 5, 15):
            for i in range(rows):
                conn.execute("INSERT INTO force_snapshots VALUES (?, ?, ?, ?, ?)", (f"t{i:04d}", tf, "GBPUSD", float((i % 7) - 3), float(i % 5)))
    else:
        conn.execute("CREATE TABLE force_snapshots (created_at TEXT, timeframe INTEGER, symbol TEXT, force_value REAL)")
        for tf in (1, 5, 15):
            for i in range(rows):
                conn.execute("INSERT INTO force_snapshots VALUES (?, ?, ?, ?)", (f"t{i:04d}", tf, "GBPUSD", float((i % 7) - 3)))
    conn.commit()
    conn.close()


def test_wavelet_valid_states_wide():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "pf.db")
        make_db(db, 40, True)
        res = WaveletDensityEngine().compute(db, "GBPUSD", [1, 5, 15])
        assert res["status"] == "ACTIVE", res
        for item in res["results"]:
            assert item["wavelet_state"] in {"WAVELET_COMPRESSING", "WAVELET_EXPANDING", "WAVELET_MULTI_SCALE", "WAVELET_TRANSITIONING", "WAVELET_SILENT"}
            assert item["dominant_scale_bars"] > 0


def test_generic_numeric_schema():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "pf.db")
        make_db(db, 40, False)
        res = WaveletDensityEngine().compute(db, "GBPUSD", [1, 5, 15])
        assert res["status"] == "ACTIVE", res
        assert res["schema_mode"] == "generic_numeric_stream", res


def test_tf5_guard_and_silent_valid():
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as d:
        db = str(Path(d) / "pf.db")
        make_db(db, 5, True)
        res = WaveletDensityEngine().compute(db, "GBPUSD", [1, 5, 15])
        assert res["status"] == "INSUFFICIENT_DATA", res
        for item in res["results"]:
            assert item["wavelet_state"] == "WAVELET_SILENT"


if __name__ == "__main__":
    test_wavelet_valid_states_wide()
    test_generic_numeric_schema()
    test_tf5_guard_and_silent_valid()
    print("test_wavelet_density PASS")
