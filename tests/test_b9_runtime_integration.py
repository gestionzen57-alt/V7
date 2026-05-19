from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "Core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))

from pf_b9_runtime_bridge import (  # noqa: E402
    B9RuntimeBridge,
    B9RuntimeIntegrationError,
    attach_b9_to_existing_process_tick_window,
    build_b9_window,
    build_engine_config,
    infer_symbol_and_window_from_call,
    normalize_raw_bias,
    sample_runtime_window,
    validate_window_data,
)


class FakeEngine:
    def __init__(self, config, status="NODE_CREATED"):
        self.config = config
        self.status = status
        self.windows = []

    def process_window(self, window):
        self.windows.append(window)
        if self.status == "NODE_CREATED":
            return {"status": "NODE_CREATED", "node": {"symbol": window["symbol"], "timestamp": window["timestamp"]}, "requalified": {}}
        return {"status": self.status, "node": None}


def test_build_engine_config_default_dryrun(monkeypatch):
    monkeypatch.delenv("B9_ENABLE_TELEGRAM", raising=False)
    config = build_engine_config()
    assert config["ENABLE_TELEGRAM"] is False
    assert config["DB_PATH"] == "powerflow.db"


def test_build_engine_config_env_enables_telegram(monkeypatch):
    monkeypatch.setenv("B9_ENABLE_TELEGRAM", "true")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    config = build_engine_config()
    assert config["ENABLE_TELEGRAM"] is True
    assert config["TELEGRAM_CONFIG"]["bot_token"] == "token"
    assert config["TELEGRAM_CONFIG"]["chat_id"] == "chat"


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("BEARISH", "DOWN"),
        ("BULLISH", "UP"),
        ("PAIR_DOWN", "DOWN"),
        ("PAIR_UP", "UP"),
        ("MIXED", "NEUTRAL"),
        ("unknown-label", "NEUTRAL"),
        (None, "NEUTRAL"),
    ],
)
def test_normalize_raw_bias(raw, expected):
    assert normalize_raw_bias(raw) == expected


def test_validate_window_data_missing_fields_raises():
    with pytest.raises(B9RuntimeIntegrationError):
        validate_window_data({"timestamp": "x"})


def test_build_b9_window_maps_runtime_fields():
    data = sample_runtime_window()
    window = build_b9_window("GBPUSD", data)
    assert window["symbol"] == "GBPUSD"
    assert window["raw_bias"] == "DOWN"
    assert window["price_path"]["ticks_total"] == 150
    assert window["price_path"]["rejection_distance_pips"] == 8.5
    assert window["packet_strength"] == 0.72


def test_bridge_process_pushes_node_when_created():
    pushed = []
    fake = FakeEngine
    bridge = B9RuntimeBridge(engine_factory=fake, push_node=lambda node: pushed.append(node), enable_telegram=False)
    result = bridge.process_tick_window("GBPUSD", sample_runtime_window())
    assert result["status"] == "NODE_CREATED"
    assert pushed == [{"symbol": "GBPUSD", "timestamp": "2026-05-19T14:30:00"}]
    assert bridge.engine.windows[0]["raw_bias"] == "DOWN"


def test_bridge_does_not_push_when_suppressed():
    pushed = []
    bridge = B9RuntimeBridge(
        engine_factory=lambda cfg: FakeEngine(cfg, status="NODE_SUPPRESSED"),
        push_node=lambda node: pushed.append(node),
    )
    result = bridge.process_tick_window("GBPUSD", sample_runtime_window())
    assert result["status"] == "NODE_SUPPRESSED"
    assert pushed == []


def test_bridge_fail_soft_returns_error(tmp_path):
    class BadEngine:
        def process_window(self, window):
            raise RuntimeError("boom")

    bridge = B9RuntimeBridge(engine_factory=lambda cfg: BadEngine(), log_path=tmp_path / "b9.log")
    result = bridge.process_tick_window("GBPUSD", sample_runtime_window())
    assert result["status"] == "B9_RUNTIME_ERROR"
    assert "boom" in result["error"]
    assert (tmp_path / "b9.log").exists()


def test_bridge_fail_hard_raises():
    class BadEngine:
        def process_window(self, window):
            raise RuntimeError("boom")

    bridge = B9RuntimeBridge(engine_factory=lambda cfg: BadEngine(), fail_soft=False)
    with pytest.raises(RuntimeError):
        bridge.process_tick_window("GBPUSD", sample_runtime_window())


def test_infer_symbol_and_window_from_two_args():
    data = sample_runtime_window()
    symbol, window = infer_symbol_and_window_from_call(("GBPUSD", data), {})
    assert symbol == "GBPUSD"
    assert window is data


def test_infer_symbol_and_window_from_one_mapping():
    data = sample_runtime_window()
    symbol, window = infer_symbol_and_window_from_call((data,), {})
    assert symbol == "GBPUSD"
    assert window is data


def test_attach_wrapper_adds_b9_result_to_dict():
    calls = []

    def process_tick_window(symbol, window_data):
        return {"base": "ok"}

    bridge = B9RuntimeBridge(engine_factory=FakeEngine, push_node=lambda node: calls.append(node))
    g = {"process_tick_window": process_tick_window}
    applied = attach_b9_to_existing_process_tick_window(g, bridge)
    result = g["process_tick_window"]("GBPUSD", sample_runtime_window())
    assert applied is True
    assert result["base"] == "ok"
    assert result["b9_runtime_result"]["status"] == "NODE_CREATED"
    assert calls


def test_attach_wrapper_is_idempotent():
    def process_tick_window(symbol, window_data):
        return {"base": "ok"}

    bridge = B9RuntimeBridge(engine_factory=FakeEngine)
    g = {"process_tick_window": process_tick_window}
    assert attach_b9_to_existing_process_tick_window(g, bridge) is True
    assert attach_b9_to_existing_process_tick_window(g, bridge) is False
