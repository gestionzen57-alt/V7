from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pf_telegram_battlefield


@pytest.fixture(autouse=True)
def reset_rate_limit_and_env(monkeypatch):
    pf_telegram_battlefield.reset_rate_limiter()
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "unit-test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "unit-test-chat")
    yield
    pf_telegram_battlefield.reset_rate_limiter()


def _live_packet(symbol="GBPUSD", confidence=0.78, event_type="T009_BATTLE_LEVEL_BORN"):
    return {
        "event_type": event_type,
        "symbol": symbol,
        "zone": {"level": 1.2650, "low": 1.2648, "high": 1.2652},
        "confidence": confidence,
        "battle_score": 0.78,
        "absorption_score": 0.35,
        "data_visibility": "LIVE",
        "live_telegram_allowed": True,
        "source_mode": "TIMER_1S_SAMPLE",
    }


def _live_flags():
    return {"POWERFLOW_T009_ENABLE_TELEGRAM": 1, "POWERFLOW_T009_DRY_RUN": 0}


def test_telegram_message_template_battle():
    msg = pf_telegram_battlefield.format_telegram_message_fr(_live_packet())
    assert "BATTLE_LEVEL_BORN" in msg
    assert "1.26500" in msg
    assert "GBPUSD" in msg
    assert "haute confiance" in msg
    assert "battle=0.78" in msg


def test_telegram_message_template_absorption():
    packet = _live_packet(event_type="T009_ABSORPTION_CLUSTER")
    packet["absorption_score"] = 0.85
    packet["confidence"] = 0.85
    msg = pf_telegram_battlefield.format_telegram_message_fr(packet)
    assert "ABSORPTION_CLUSTER" in msg
    assert "cluster d'absorption" in msg
    assert "haute confiance" in msg


def test_send_battlefield_alert_live_mode(monkeypatch):
    calls = []

    def fake_send(chat_id, message, parse_mode="Markdown"):
        calls.append((chat_id, message, parse_mode))
        return True

    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", fake_send)
    result = pf_telegram_battlefield.send_battlefield_alert(_live_packet(), _live_flags())
    assert result["sent"] is True
    assert "success" in result["reason"]
    assert result["attempts"] == 1
    assert calls and calls[0][0] == "unit-test-chat"


def test_send_battlefield_alert_dry_run(monkeypatch):
    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", lambda *a, **kw: True)
    flags = {"POWERFLOW_T009_ENABLE_TELEGRAM": 1, "POWERFLOW_T009_DRY_RUN": 1}
    result = pf_telegram_battlefield.send_battlefield_alert(_live_packet(), flags)
    assert result["sent"] is False
    assert "DRY_RUN=1" in result["reason"]
    assert result["attempts"] == 0


def test_reconstructed_data_blocked(monkeypatch):
    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", lambda *a, **kw: True)
    packet = _live_packet(confidence=0.90)
    packet["data_visibility"] = "RECONSTRUCTED"
    packet["live_telegram_allowed"] = False
    packet["source_mode"] = "M1_BAR_PROXY"
    result = pf_telegram_battlefield.send_battlefield_alert(packet, _live_flags())
    assert result["sent"] is False
    assert "RECONSTRUCTED" in result["reason"]


def test_confidence_filter_min_050(monkeypatch):
    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", lambda *a, **kw: True)
    result = pf_telegram_battlefield.send_battlefield_alert(_live_packet(confidence=0.49), _live_flags())
    assert result["sent"] is False
    assert "0.50 threshold" in result["reason"]


def test_rate_limiting_10s(monkeypatch):
    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", lambda *a, **kw: True)
    packet = _live_packet(symbol="GBPUSD")
    first = pf_telegram_battlefield.send_battlefield_alert(packet, _live_flags())
    second = pf_telegram_battlefield.send_battlefield_alert(packet, _live_flags())
    assert first["sent"] is True
    assert second["sent"] is False
    assert "rate limit" in second["reason"]


def test_retry_logic_3_attempts(monkeypatch):
    attempts = {"count": 0}

    def flaky_send(*args, **kwargs):
        attempts["count"] += 1
        raise RuntimeError("temporary telegram failure")

    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", flaky_send)
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    result = pf_telegram_battlefield.send_battlefield_alert(_live_packet(symbol="EURUSD"), _live_flags())
    assert result["sent"] is False
    assert result["attempts"] == 3
    assert attempts["count"] == 3
    assert "failed after 3 attempts" in result["reason"]


def test_retry_logic_success_after_two_failures(monkeypatch):
    attempts = {"count": 0}

    def eventually_ok(*args, **kwargs):
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("temporary telegram failure")
        return True

    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", eventually_ok)
    monkeypatch.setattr(time, "sleep", lambda *_: None)
    result = pf_telegram_battlefield.send_battlefield_alert(_live_packet(symbol="USDJPY"), _live_flags())
    assert result["sent"] is True
    assert result["attempts"] == 3


def test_telegram_flag_enforcement(monkeypatch):
    monkeypatch.setattr(pf_telegram_battlefield, "_send_telegram_api", lambda *a, **kw: True)
    flags = {"POWERFLOW_T009_ENABLE_TELEGRAM": 0, "POWERFLOW_T009_DRY_RUN": 0}
    result = pf_telegram_battlefield.send_battlefield_alert(_live_packet(), flags)
    assert result["sent"] is False
    assert "POWERFLOW_T009_ENABLE_TELEGRAM=0" in result["reason"]


def test_cli_safety_checks():
    script = Path(__file__).resolve().parent.parent / "run_telegram_battlefield_cycle.py"
    env = os.environ.copy()
    env["POWERFLOW_T009_ENABLE_TELEGRAM"] = "0"
    env["POWERFLOW_T009_DRY_RUN"] = "0"
    result = subprocess.run(
        [sys.executable, str(script), "--symbol", "GBPUSD", "--enable-telegram"],
        env=env,
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 1
    assert "POWERFLOW_T009_ENABLE_TELEGRAM=1" in result.stdout


def test_cli_dry_run_no_events_safe():
    script = Path(__file__).resolve().parent.parent / "run_telegram_battlefield_cycle.py"
    result = subprocess.run(
        [sys.executable, str(script), "--symbol", "GBPUSD", "--lookback-min", "1"],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    assert "No battlefield events detected" in result.stdout or "Event" in result.stdout
