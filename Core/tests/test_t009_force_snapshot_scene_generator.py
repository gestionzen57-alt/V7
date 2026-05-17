from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pf_t009_force_snapshot_scene_generator import GeneratorConfig, SUMMARY_RECOVERY_TYPE, generate


def make_db(path: Path) -> None:
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE force_snapshots_v2 (
        id INTEGER PRIMARY KEY,
        created_at TEXT,
        symbol TEXT,
        timeframe INTEGER,
        bar_time REAL,
        open REAL,
        high REAL,
        low REAL,
        close REAL,
        mid REAL,
        spread_pips REAL,
        tick_volume REAL,
        pip_range REAL,
        pip_body REAL,
        pip_change REAL,
        force_gbp REAL,
        force_usd REAL,
        force_eur REAL,
        force_jpy REAL,
        force_cad REAL,
        force_chf REAL,
        force_aud REAL,
        force_nzd REAL
    )
    """)
    base = datetime(2026, 5, 7, 0, 0, tzinfo=timezone.utc)
    price = 1.3500
    for i in range(90):
        ts = base + timedelta(minutes=i)
        close = price + (i * 0.00003)
        cur.execute("""
        INSERT INTO force_snapshots_v2 (
            created_at, symbol, timeframe, bar_time, open, high, low, close, mid, spread_pips,
            tick_volume, pip_range, pip_body, pip_change, force_gbp, force_usd, force_eur, force_jpy,
            force_cad, force_chf, force_aud, force_nzd
        ) VALUES (?, 'GBPUSD', 1, ?, ?, ?, ?, ?, ?, 0.2, ?, 1.0, 0.5, 0.3, ?, ?, 0, 0, 0, 0, 0, 0)
        """, (
            ts.isoformat(), ts.timestamp(), price, close + 0.00005, close - 0.00005, close, close,
            100 + i, i * 0.01, -i * 0.005,
        ))
    con.commit()
    con.close()


def test_generate_force_snapshot_summary_read_only(tmp_path: Path) -> None:
    db = tmp_path / "powerflow.db"
    out = tmp_path / "out"
    make_db(db)
    cfg = GeneratorConfig(db_path=db, output_dir=out, dates=("2026-05-07",), max_window_minutes=30)
    result = generate(cfg)
    assert result["generated_count"] >= 1
    files = list(out.rglob("t009_sequence_summary.json"))
    assert files
    data = json.loads(files[0].read_text(encoding="utf-8"))
    assert data["summary_recovery_type"] == SUMMARY_RECOVERY_TYPE
    assert data["metadata"]["read_only_db"] is True
    assert data["source_mode"] == "M1_BAR_PROXY"
    assert data["data_visibility"] == "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED"
    assert data["moments"]
    assert all(m.get("time_start") and m.get("time_end") for m in data["moments"])


def test_no_buy_sell_words_in_generated_summary(tmp_path: Path) -> None:
    db = tmp_path / "powerflow.db"
    out = tmp_path / "out"
    make_db(db)
    cfg = GeneratorConfig(db_path=db, output_dir=out, dates=("2026-05-07",))
    generate(cfg)
    text = "\n".join(p.read_text(encoding="utf-8") for p in out.rglob("*.json"))
    import re
    assert re.search(r"\b(BUY|SELL)\b", text.upper()) is None


def test_missing_date_reported_without_invention(tmp_path: Path) -> None:
    db = tmp_path / "powerflow.db"
    out = tmp_path / "out"
    make_db(db)
    cfg = GeneratorConfig(db_path=db, output_dir=out, dates=("2026-05-04",))
    result = generate(cfg)
    assert result["generated_count"] == 0
    missing = out / "B9_FORCE_SNAPSHOT_DERIVED_MISSING_20260504_20260514.md"
    assert missing.exists()
    assert "NO_FORCE_SNAPSHOT_PROXY_SOURCE_FOUND" in missing.read_text(encoding="utf-8")
