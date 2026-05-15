from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_adapter_signature_matches_frozen_engine_contract():
    sys.path.insert(0, str(_core()))

    import pf_engine_v6_adapter as adapter

    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert str(inspect.signature(adapter.process_tick)) == contract["signature"]


def test_adapter_delegates_to_legacy_engine(monkeypatch):
    sys.path.insert(0, str(_core()))

    import pf_engine_v6_adapter as adapter

    calls = []

    def fake_process_tick(tick, prev, brain, send_alert):
        calls.append((tick, prev, brain, send_alert))
        return {"delegated": True}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_process_tick)

    tick = object()
    prev = object()
    brain = {"state": "test"}
    send_alert = lambda *args, **kwargs: None

    result = adapter.process_tick(tick, prev, brain, send_alert)

    assert result == {"delegated": True}
    assert calls == [(tick, prev, brain, send_alert)]


def test_capture_bridge_uses_adapter_boundary_not_legacy_direct_import():
    capture_bridge = _repo() / "Core" / "capture_bridge.py"
    text = capture_bridge.read_text(encoding="utf-8", errors="replace")

    assert "from pf_engine_v6_adapter import process_tick" in text
    assert "from engine import process_tick" not in text

