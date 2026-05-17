from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_raw_calibration import (  # noqa: E402
    RawCalibrationConfig,
    calibrate_summary_with_raw,
    classify_raw_texture,
    render_raw_calibration_markdown,
)


def make_db(path: Path) -> Path:
    con = sqlite3.connect(path)
    cur = con.cursor()
    cur.execute(
        """
        CREATE TABLE tick_stream (
            symbol TEXT,
            ts_utc TEXT,
            bid REAL,
            ask REAL,
            mid REAL,
            spread REAL,
            gap_ms INTEGER,
            time_msc INTEGER,
            source_mode TEXT,
            capture_seq INTEGER
        )
        """
    )
    con.commit()
    con.close()
    return path


def insert_ticks(path: Path, start_hour: str, mids: list[float], *, spread: float = 0.00002, gap_ms: int = 1000):
    con = sqlite3.connect(path)
    cur = con.cursor()
    base = start_hour  # e.g. 2026-05-15T05
    for idx, mid in enumerate(mids, start=1):
        minute = idx - 1
        ts = f"{base}:{minute:02d}:00.000Z"
        cur.execute(
            "INSERT INTO tick_stream VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                "GBPUSD",
                ts,
                mid - spread / 2,
                mid + spread / 2,
                mid,
                spread,
                gap_ms,
                1_768_000_000_000 + idx * gap_ms,
                "HISTORICAL_RAW",
                idx,
            ),
        )
    con.commit()
    con.close()


def moment(start="2026-05-15T08:00:00Z", end="2026-05-15T08:04:00Z", delta=5.0, kind="T009_MOMENT_PROGRESSIVE_WAVE"):
    return {
        "moment_id": "T009M-001",
        "moment_type": kind,
        "label_fr": "Vague progressive",
        "time_start": start,
        "time_end": end,
        "center_delta_pips": delta,
        "source_mode": "M1_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED",
        "confidence_cap": 0.35,
        "limits_fr": ["M1_BAR_PROXY", "RECONSTRUCTED", "confidence_cap=0.35"],
    }


def cfg(db: Path) -> RawCalibrationConfig:
    return RawCalibrationConfig(tick_db_path=str(db), broker_time_shift_min=180)


def test_raw_coverage_fields_present(tmp_path):
    db = make_db(tmp_path / "tick_archive.db")
    insert_ticks(db, "2026-05-15T05", [1.3300, 1.3302, 1.3304, 1.3306, 1.3308])
    summary = {"moments": [moment()]}
    out = calibrate_summary_with_raw(summary, cfg(db))
    m = out["moments"][0]
    assert m["raw_coverage"] in {"FULL", "PARTIAL"}
    assert m["raw_source_mode"] == "HISTORICAL_RAW"
    assert m["raw_data_visibility"] == "MT5_RAW_ALIGNED"
    assert m["raw_confidence_cap"] == 0.55
    assert "broker-relative" in m["raw_limits"]


def test_broker_offset_present_and_applied(tmp_path):
    db = make_db(tmp_path / "tick_archive.db")
    insert_ticks(db, "2026-05-15T05", [1.3300, 1.3302, 1.3304, 1.3306, 1.3308])
    out = calibrate_summary_with_raw({"moments": [moment()]}, cfg(db))
    m = out["moments"][0]
    assert m["broker_time_shift_min"] == 180
    assert m["raw_window_start_mt5"].startswith("2026-05-15T05:00")
    assert m["aligned_window_start_mt4_plus_3h"].startswith("2026-05-15T08:00")


def test_raw_texture_fields_present(tmp_path):
    db = make_db(tmp_path / "tick_archive.db")
    insert_ticks(db, "2026-05-15T05", [1.3300, 1.3303, 1.3306, 1.3309, 1.3311])
    out = calibrate_summary_with_raw({"moments": [moment()]}, cfg(db))
    m = out["moments"][0]
    assert m["raw_tick_count"] == 4
    assert m["raw_delta_pips"] is not None
    assert m["raw_range_pips"] is not None
    assert m["raw_spread_avg_pips"] is not None
    assert m["raw_gap_max_ms"] is not None
    assert m["raw_texture_role"] in {
        "RAW_PROGRESS_CONFIRMED",
        "RAW_DWELL_CONFIRMED",
        "RAW_ROTATION_CONFIRMED",
        "RAW_FRICTION_CONFIRMED",
        "RAW_PROXY_DIVERGENCE",
    }


def test_zero_duration_does_not_become_false_raw_missing(tmp_path):
    db = make_db(tmp_path / "tick_archive.db")
    zero = moment(start="2026-05-15T12:00:00Z", end="2026-05-15T12:00:00Z")
    out = calibrate_summary_with_raw({"moments": [zero]}, cfg(db))
    m = out["moments"][0]
    assert m["zero_duration_status"] == "ZERO_DURATION_MOMENT"
    assert m["raw_texture_role"] == "ZERO_DURATION_MOMENT"
    assert m["proxy_vs_raw_verdict"] == "ZERO_DURATION_MOMENT"
    assert m["raw_texture_role"] != "RAW_UNAVAILABLE"


def test_progressive_wave_divergent_becomes_weak_or_rotational(tmp_path):
    db = make_db(tmp_path / "tick_archive.db")
    insert_ticks(db, "2026-05-15T05", [1.3305, 1.3304, 1.3303, 1.3303, 1.33028])
    out = calibrate_summary_with_raw({"moments": [moment(delta=5.0)]}, cfg(db))
    m = out["moments"][0]
    assert m["progressive_wave_state"] in {"PROGRESSIVE_WAVE_WEAK_RAW", "PROGRESSIVE_WAVE_ROTATIONAL"}
    assert m["proxy_vs_raw_verdict"] == "NUANCED_BY_RAW"


def test_progressive_wave_rotational_state_direct_classifier():
    role, verdict, state = classify_raw_texture(
        moment(delta=4.05),
        raw_delta_pips=4.5,
        raw_range_pips=6.2,
        raw_spread_avg_pips=0.2,
        raw_gap_max_ms=1000,
        cfg=RawCalibrationConfig(),
    )
    assert role == "RAW_ROTATION_CONFIRMED"
    assert verdict == "NUANCED_BY_RAW"
    assert state == "PROGRESSIVE_WAVE_ROTATIONAL"


def test_no_buy_sell_and_no_dashboard_telegram_dependency(tmp_path):
    db = make_db(tmp_path / "tick_archive.db")
    insert_ticks(db, "2026-05-15T05", [1.3300, 1.3301, 1.3302])
    out = calibrate_summary_with_raw({"moments": [moment()]}, cfg(db))
    text = json.dumps(out, ensure_ascii=False) + render_raw_calibration_markdown(out)
    assert "BUY" not in text
    assert "SELL" not in text
    source = Path(ROOT / "pf_t009_raw_calibration.py").read_text(encoding="utf-8")
    import_lines = "\n".join(line for line in source.splitlines() if line.startswith("import ") or line.startswith("from "))
    assert "dashboard" not in import_lines
    assert "telegram" not in import_lines


def test_read_only_sqlite_does_not_create_db(tmp_path):
    missing = tmp_path / "missing.db"
    out = calibrate_summary_with_raw({"moments": [moment()]}, RawCalibrationConfig(tick_db_path=str(missing)))
    assert out["moments"][0]["raw_coverage"] == "MISSING"
    assert not missing.exists()
