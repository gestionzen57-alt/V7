from __future__ import annotations

import math
import py_compile
import sqlite3
from pathlib import Path
import tempfile

from pf_hmm_regime_engine import HMMRegimeEngine, VALID_REGIMES

CURRENCIES = ("gbp", "usd", "eur", "jpy", "chf", "cad", "aud", "nzd")


def make_db(path: Path, counts_by_tf: dict[int, int]) -> None:
    conn = sqlite3.connect(path)
    cols = ", ".join(f"{c} REAL" for c in CURRENCIES)
    conn.execute(f"CREATE TABLE force_snapshots (timestamp TEXT, timeframe INTEGER, symbol TEXT, {cols})")
    for tf, n in counts_by_tf.items():
        for i in range(n):
            vals = [math.sin(i / 5.0 + k + tf / 100.0) * (1 + k * 0.1) + i * 0.01 for k in range(len(CURRENCIES))]
            conn.execute(
                f"INSERT INTO force_snapshots VALUES ({','.join(['?'] * (3 + len(CURRENCIES)))})",
                [f"2026-05-11T00:{i:02d}:00Z", tf, "GBPUSD", *vals],
            )
    conn.commit()
    conn.close()


def test_insufficient_data_guard_is_multitf_not_tf1440():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "pf.db"
        make_db(db, {60: 10, 30: 10, 15: 10})
        result = HMMRegimeEngine().compute(str(db), "GBPUSD", timeframes=[60, 30, 15])
        assert result["status"] == "INSUFFICIENT_DATA"
        assert result["fallback"] == "B1_LEGACY"
        assert "MULTI_TF_INSUFFICIENT_OBSERVATIONS" in result["technical_risks"]


def test_active_without_tf1440_or_h4_when_tactical_stack_has_50_observations():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "pf.db"
        make_db(db, {60: 20, 30: 20, 15: 20})
        result = HMMRegimeEngine().compute(str(db), "GBPUSD", timeframes=[60, 30, 15])
        assert result["status"] == "ACTIVE"
        assert result["fallback"] is None
        assert result["regime_scope"] == "MULTI_TF_TACTICAL"
        assert result["regime_hmm"] in VALID_REGIMES
        assert 1440 not in result["timeframes_used"]
        assert 240 not in result["timeframes_used"]


def test_active_state_and_confidence_range():
    with tempfile.TemporaryDirectory() as d:
        db = Path(d) / "pf.db"
        make_db(db, {60: 25, 30: 25, 15: 25})
        result = HMMRegimeEngine().compute(str(db), "GBPUSD", timeframes=[60, 30, 15])
        assert result["status"] == "ACTIVE"
        assert result["regime_hmm"] in VALID_REGIMES
        assert 0.0 <= result["regime_confidence_hmm"] <= 1.0
        assert set(result["state_probabilities"]) == set(VALID_REGIMES)


def test_py_compile():
    py_compile.compile("pf_hmm_regime_engine.py", doraise=True)


if __name__ == "__main__":
    test_insufficient_data_guard_is_multitf_not_tf1440()
    test_active_without_tf1440_or_h4_when_tactical_stack_has_50_observations()
    test_active_state_and_confidence_range()
    test_py_compile()
    print("test_hmm_regime.py PASS")
