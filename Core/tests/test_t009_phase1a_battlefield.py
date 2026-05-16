import sqlite3
import sys
from pathlib import Path

import pytest

_here = Path(__file__).resolve()
_candidates = [Path.cwd(), Path.cwd().parent, _here.parents[1]]
if len(_here.parents) > 2:
    _andidates_extra = _here.parents[2]
    _candidates.append(_andidates_extra)
for _path in _candidates:
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

try:
    from Core.pf_battlefield_flux import BattlefieldFlux
except ModuleNotFoundError:
    from pf_battlefield_flux import BattlefieldFlux


@pytest.fixture
def bf():
    return BattlefieldFlux(db_path=":memory:", fallback_db=":memory:")


def test_load_ticks_primary_empty(bf):
    ticks = bf.load_ticks_primary("GBPUSD", 30)
    assert ticks == []


def test_load_ticks_fallback_structure(bf):
    ticks = bf.load_ticks_fallback("GBPUSD", 30)
    assert isinstance(ticks, list)


def test_load_ticks_fallback_reconstruction(tmp_path):
    db_path = tmp_path / "powerflow.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        """
        CREATE TABLE bars_m1 (
            symbol TEXT,
            ts TEXT,
            ts_epoch INTEGER,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            spread REAL,
            tick_volume INTEGER
        )
        """
    )
    conn.execute(
        """
        INSERT INTO bars_m1 (symbol, ts, ts_epoch, open, high, low, close, spread, tick_volume)
        VALUES ('GBPUSD', '2999-05-15T12:00:00Z', 32515387200, 1.27040, 1.27080, 1.27010, 1.27070, 0.0002, 42)
        """
    )
    conn.commit()
    conn.close()

    module = BattlefieldFlux(db_path=":memory:", fallback_db=str(db_path))
    ticks = module.load_ticks_fallback("GBPUSD", 120)

    assert len(ticks) == 4
    assert [tick["mid"] for tick in ticks] == [1.27040, 1.27010, 1.27080, 1.27070]
    assert all(tick["source_mode"] == "M1_BAR_PROXY" for tick in ticks)
    assert all(tick["data_visibility"] == "RECONSTRUCTED" for tick in ticks)
    assert all(tick["confidence_cap"] == 0.35 for tick in ticks)
    assert all(tick["live_telegram_allowed"] is False for tick in ticks)


def test_build_clusters_simple(bf):
    ticks = [
        {"symbol": "GBPUSD", "ts_utc": "2026-05-15T12:00:00Z", "ts_epoch_ms": 1715782800000,
         "bid": 1.27040, "ask": 1.27042, "mid": 1.27041, "spread": 0.0002, "source_mode": "TIMER_1S_SAMPLE"},
        {"symbol": "GBPUSD", "ts_utc": "2026-05-15T12:00:01Z", "ts_epoch_ms": 1715782801000,
         "bid": 1.27041, "ask": 1.27043, "mid": 1.27042, "spread": 0.0002, "source_mode": "TIMER_1S_SAMPLE"},
    ]
    buckets = bf.build_time_price_buckets(ticks, time_bucket_sec=60, slide_step_sec=15)
    assert len(buckets) > 0
    assert "features" in buckets[0]


def test_score_battle_formula(bf):
    features = {"tick_count": 60, "price_range_pips": 1.0, "price_dwell_zone": True, "signed_delta": 10, "directional_ticks": 59}
    score = bf.score_battle(features)
    assert 0.0 <= score <= 1.0


def test_score_absorption_formula(bf):
    features = {"tick_count": 60, "price_range_pips": 1.0, "price_dwell_zone": True, "signed_delta": 10, "directional_ticks": 59}
    score = bf.score_absorption(features)
    assert 0.0 <= score <= 1.0


def test_evidence_packet_structure(bf):
    ticks = [
        {"symbol": "GBPUSD", "ts_utc": "2026-05-15T12:00:00Z", "ts_epoch_ms": 1715782800000,
         "bid": 1.27040, "ask": 1.27042, "mid": 1.27041, "spread": 0.0002,
         "source_mode": "TIMER_1S_SAMPLE", "data_visibility": "FRESH"}
    ]
    features = {"tick_count": 60, "price_range_pips": 1.0, "data_visibility": "FRESH"}
    packet = bf.build_event_evidence_packet("T009_BATTLE_LEVEL_BORN", (1.27040, 1.27050), {"battle_score": 0.75}, ticks, features)

    assert packet["event_type"] == "T009_BATTLE_LEVEL_BORN"
    assert packet["module"] == "pf_battlefield_flux"
    assert packet["source_mode"] == "TIMER_1S_SAMPLE"
    assert "zone" in packet
    assert "scores" in packet
    assert "reading" in packet
    assert "technical_risks" in packet
    assert "evidence" in packet
    assert "L1_raw" in packet["evidence"]
    assert "L2_features" in packet["evidence"]
    assert "L3_reading" in packet["evidence"]


def test_delta_flip_detection(bf):
    ticks = [
        {"mid": 1.27040, "ts_epoch_ms": 1, "ts_utc": "2026-05-15T12:00:00Z"},
        {"mid": 1.27041, "ts_epoch_ms": 2, "ts_utc": "2026-05-15T12:00:01Z"},
        {"mid": 1.27040, "ts_epoch_ms": 3, "ts_utc": "2026-05-15T12:00:02Z"},
        {"mid": 1.27041, "ts_epoch_ms": 4, "ts_utc": "2026-05-15T12:00:03Z"},
    ]
    events = bf.detect_delta_flip(ticks)
    assert len(events) > 0
    assert events[0]["type"] == "T009_CLUSTER_DELTA_FLIP"


def test_zone_break_detection(bf):
    event = bf.detect_zone_break(1.27040, 1.27050, 1.27045)
    assert event is None

    event = bf.detect_zone_break(1.27040, 1.27050, 1.27060)
    assert event is not None
    assert event["type"] == "T009_BATTLE_ZONE_BROKEN"


def test_compute_state_empty_safe(bf):
    state = bf.compute_state("GBPUSD", 30)
    assert state["module"] == "pf_battlefield_flux"
    assert state["phase"] == "T009_PHASE1A_STANDALONE_DRY_RUN"
    assert state["event_count"] == 0
    assert isinstance(state["events"], list)
