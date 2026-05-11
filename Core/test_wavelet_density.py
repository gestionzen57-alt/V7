from __future__ import annotations

import math
import py_compile
import sqlite3
from pathlib import Path
import tempfile

from pf_wavelet_density import WaveletDensityEngine, VALID_WAVELET_STATES

CURRENCIES = ("gbp", "usd", "eur", "jpy", "chf", "cad", "aud", "nzd")


def make_db(path: Path, n_tf5: int, flat: bool = False) -> None:
    conn = sqlite3.connect(path)
    cols = ", ".join(f"{c} REAL" for c in CURRENCIES)
    conn.execute(f"CREATE TABLE force_snapshots (timestamp TEXT, timeframe INTEGER, symbol TEXT, {cols})")
    for tf, count in [(1, max(n_tf5, 35)), (5, n_tf5), (15, max(n_tf5, 35))]:
        for i in range(count):
            if flat:
                vals = [1.0 for _ in CURRENCIES]
            else:
                vals = [math.sin(i / (2.0 + k * 0.2)) + 0.35 * math.sin(i / 9.0 + k) for k in range(len(CURRENCIES))]
            conn.execute(
                f"INSERT INTO force_snapshots VALUES ({','.join(['?'] * (3 + len(CURRENCIES)))})",
                [f"2026-05-11T00:{i:02d}:00Z", tf, "GBPUSD", *vals],
            )
    conn.commit()
    conn.close()


def test_tf5_guard():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "pf.db"
        make_db(db, 23)
        result = WaveletDensityEngine().compute(str(db), "GBPUSD", [1, 5, 15])
        assert result["status"] == "INSUFFICIENT_DATA"
        assert "TF5_INSUFFICIENT_ROWS" in result["technical_risks"]


def test_states_and_scale():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "pf.db"
        make_db(db, 45)
        result = WaveletDensityEngine().compute(str(db), "GBPUSD", [5])
        assert result["status"] == "ACTIVE"
        assert result["items"]
        for item in result["items"]:
            assert item["wavelet_state"] in VALID_WAVELET_STATES
            assert item["dominant_scale_bars"] > 0


def test_silent_is_valid_state():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "pf.db"
        make_db(db, 45, flat=True)
        result = WaveletDensityEngine().compute(str(db), "GBPUSD", [5])
        assert result["status"] == "ACTIVE"
        assert any(item["wavelet_state"] == "WAVELET_SILENT" for item in result["items"])


def test_py_compile():
    py_compile.compile("pf_wavelet_density.py", doraise=True)


if __name__ == "__main__":
    test_tf5_guard()
    test_states_and_scale()
    test_silent_is_valid_state()
    test_py_compile()
    print("test_wavelet_density.py PASS")
