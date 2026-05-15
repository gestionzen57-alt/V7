from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_t002_v6_core_process_tick_exists_and_is_pure_surface():
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_core as core

    assert callable(core.process_tick)

    tick = SimpleNamespace(
        symbol="GBPUSD",
        timestamp="2026-05-15T20:00:00Z",
        timeframe="M1",
        val_a=1.2500,
        val_b=1.2490,
        dev_a=0.2,
        dev_b=-0.1,
        spread=0.0002,
    )
    prev = SimpleNamespace(
        symbol="GBPUSD",
        timestamp="2026-05-15T19:59:00Z",
        timeframe="M1",
        val_a=1.2495,
        val_b=1.2491,
        dev_a=0.1,
        dev_b=-0.2,
        spread=0.0003,
    )

    calls = []

    def fake_transport(*args, **kwargs):
        calls.append((args, kwargs))

    brain = {"existing": True}
    result = core.process_tick(tick, prev, brain, fake_transport)

    assert result["route"] == "v6_core"
    assert result["engine"] == "pf_engine_v6_core"
    assert result["event_type"] == "V6_CORE_TICK_SURFACE"
    assert result["symbol"] == "GBPUSD"
    assert result["surface"]["gap"] == result["surface"]["val_a"] - result["surface"]["val_b"]
    assert result["delta"]["val_a"] == 0.0004999999999999449
    assert result["alerts"] == []
    assert result["side_effects"] is False
    assert result["brain_mutated"] is False
    assert brain == {"existing": True}
    assert calls == []


def test_t002_v6_core_accepts_dict_ticks():
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_core as core

    tick = {"symbol": "USDJPY", "timestamp": "t1", "timeframe": "M1", "val_a": 156.2, "val_b": 156.1}
    prev = {"symbol": "USDJPY", "timestamp": "t0", "timeframe": "M1", "val_a": 156.0, "val_b": 156.0}

    result = core.process_tick(tick, prev, {}, lambda *_: None)

    assert result["symbol"] == "USDJPY"
    assert result["surface"]["gap"] == 0.09999999999999432
    assert result["delta"]["val_a"] == 0.19999999999998863


def test_t002_adapter_reaches_real_v6_core_under_flag(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    monkeypatch.setenv(adapter.ENV_FLAG, "1")
    monkeypatch.delenv(adapter.STRICT_ENV_FLAG, raising=False)

    tick = {"symbol": "EURUSD", "timestamp": "t1", "timeframe": "M1", "val_a": 1.1, "val_b": 1.0}
    prev = {"symbol": "EURUSD", "timestamp": "t0", "timeframe": "M1", "val_a": 1.0, "val_b": 1.0}

    result = adapter.process_tick(tick, prev, {}, lambda *_: None)

    assert result["route"] == "v6_core"
    assert result["symbol"] == "EURUSD"


def test_t002_v6_core_entrypoint_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T002_V6_CORE_RUNTIME_ENTRYPOINT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_V6_CORE_RUNTIME_ENTRYPOINT"
    assert data["status"] == "V6_CORE_PROCESS_TICK_ENTRYPOINT_ADDED"
    assert data["side_effects"] is False
    assert data["db_writes"] is False
    assert data["default_live_behavior_changed"] is False


def test_t002_readiness_now_sees_runtime_entrypoint():
    path = _repo() / "Docs" / "Contracts" / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["status"] in {"FEATURE_FLAG_REPLAY_READY", "FEATURE_FLAG_REPLAY_PASSED"}
    assert "process_tick" in data["runtime_candidates_detected"]
