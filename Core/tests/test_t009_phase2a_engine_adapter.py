from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from pf_engine_battlefield_adapter import (
    BattlefieldFluxAdapter,
    is_engine_integration_enabled,
    maybe_integrate_battlefield_events,
)


class DummyBattlefield:
    def __init__(self, events=None):
        self.events = events or []
        self.calls = []

    def compute_state(self, symbol, lookback_min):
        self.calls.append((symbol, lookback_min))
        return {"symbol": symbol, "events": self.events, "tick_count": 42}


def _tick():
    return {"symbol": "GBPUSD", "ts_utc": "2026-05-16T10:00:00Z"}


def test_adapter_init():
    adapter = BattlefieldFluxAdapter(lookback_min=30, battlefield=DummyBattlefield())
    assert adapter.lookback_min == 30
    assert adapter.last_state is None
    assert adapter.bf is not None


def test_integrate_battlefield_events_battle_born():
    event = {
        "event_type": "T009_BATTLE_LEVEL_BORN",
        "zone": {"low": 1.2648, "high": 1.2652, "level": 1.2650},
        "confidence": 0.78,
        "battle_score": 0.78,
        "absorption_score": 0.35,
        "timestamp": "2026-05-16T10:00:00Z",
        "source_mode": "TIMER_1S_SAMPLE",
        "data_visibility": "LIVE",
    }
    adapter = BattlefieldFluxAdapter(lookback_min=30, battlefield=DummyBattlefield([event]))
    engine_events = adapter.integrate_battlefield_events(_tick(), {})
    assert len(engine_events) == 1
    converted = engine_events[0]
    assert converted["event_type"] == "BATTLEFIELD_BATTLE_LEVEL_BORN"
    assert converted["symbol"] == "GBPUSD"
    assert converted["level"] == pytest.approx(1.2650)
    assert converted["confidence"] == pytest.approx(0.78)
    assert converted["source"] == "battlefield_flux"
    assert converted["zone"]["low"] == pytest.approx(1.2648)
    assert converted["zone"]["high"] == pytest.approx(1.2652)


def test_integrate_battlefield_events_absorption():
    event = {
        "event_type": "T009_ABSORPTION_CLUSTER",
        "zone": [1.2700, 1.2704],
        "scores": {"absorption_score": 0.82, "battle_score": 0.41},
        "timestamp": "2026-05-16T10:01:00Z",
        "source_mode": "TIMER_1S_SAMPLE",
        "data_visibility": "LIVE",
    }
    adapter = BattlefieldFluxAdapter(battlefield=DummyBattlefield([event]))
    converted = adapter.integrate_battlefield_events(_tick(), {})[0]
    assert converted["event_type"] == "BATTLEFIELD_ABSORPTION_CLUSTER"
    assert converted["zone"]["low"] == pytest.approx(1.2700)
    assert converted["zone"]["high"] == pytest.approx(1.2704)
    assert converted["level"] == pytest.approx(1.2702)
    assert converted["absorption_score"] == pytest.approx(0.82)
    assert converted["confidence"] == pytest.approx(0.82)


def test_engine_integration_flag_on():
    flags = {"ENABLE_ENGINE_INTEGRATION": True}
    event = {"event_type": "T009_BATTLE_LEVEL_BORN", "zone": {"level": 1.2650}, "confidence": 0.7}
    adapter = BattlefieldFluxAdapter(battlefield=DummyBattlefield([event]))
    queue = [{"event_type": "EXISTING_EVENT"}]
    result = maybe_integrate_battlefield_events(_tick(), {}, queue, adapter=adapter, flags=flags)
    assert result is queue
    assert [event["event_type"] for event in queue] == ["EXISTING_EVENT", "BATTLEFIELD_BATTLE_LEVEL_BORN"]


def test_engine_integration_flag_off():
    flags = {"ENABLE_ENGINE_INTEGRATION": False}
    event = {"event_type": "T009_BATTLE_LEVEL_BORN", "zone": {"level": 1.2650}, "confidence": 0.7}
    adapter = BattlefieldFluxAdapter(battlefield=DummyBattlefield([event]))
    queue = [{"event_type": "EXISTING_EVENT"}]
    maybe_integrate_battlefield_events(_tick(), {}, queue, adapter=adapter, flags=flags)
    assert queue == [{"event_type": "EXISTING_EVENT"}]


def test_no_regression_existing_events():
    flags = {"ENABLE_ENGINE_INTEGRATION": False}
    existing = [{"event_type": "LEGACY_A"}, {"event_type": "LEGACY_B"}]
    original_snapshot = list(existing)
    maybe_integrate_battlefield_events(_tick(), {"anything": True}, existing, flags=flags)
    assert existing == original_snapshot


def test_battlefield_event_queue_injection():
    events = [
        {"event_type": "T009_BATTLE_LEVEL_BORN", "zone": {"level": 1.2650}, "confidence": 0.75},
        {"event_type": "T009_ABSORPTION_CLUSTER", "zone": {"level": 1.2660}, "confidence": 0.68},
    ]
    adapter = BattlefieldFluxAdapter(battlefield=DummyBattlefield(events))
    queue = [{"event_type": "LEGACY_EVENT"}]
    maybe_integrate_battlefield_events(_tick(), {}, queue, adapter=adapter, flags={"ENABLE_ENGINE_INTEGRATION": True})
    assert len(queue) == 3
    assert queue[0]["event_type"] == "LEGACY_EVENT"
    assert queue[1]["source"] == "battlefield_flux"
    assert queue[2]["event_type"] == "BATTLEFIELD_ABSORPTION_CLUSTER"


def test_adapter_handles_empty_state():
    adapter = BattlefieldFluxAdapter(battlefield=DummyBattlefield([]))
    assert adapter.integrate_battlefield_events(_tick(), {}) == []
    assert adapter.last_state is not None
    assert adapter.last_state["events"] == []


def test_adapter_fail_closed_on_battlefield_exception():
    class FailingBattlefield:
        def compute_state(self, symbol, lookback_min):
            raise RuntimeError("boom")

    adapter = BattlefieldFluxAdapter(battlefield=FailingBattlefield())
    assert adapter.integrate_battlefield_events(_tick(), {}) == []
    assert adapter.last_state is not None
    assert "error" in adapter.last_state
