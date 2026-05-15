from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_t002_runtime_adapter_signature_matches_frozen_contract(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert str(inspect.signature(adapter.process_tick)) == contract["signature"]


def test_t002_runtime_adapter_has_safe_flag_default(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    monkeypatch.delenv(adapter.ENV_FLAG, raising=False)
    assert adapter.v6_core_runtime_enabled() is False

    monkeypatch.setenv(adapter.ENV_FLAG, "1")
    assert adapter.v6_core_runtime_enabled() is True

    status = adapter.runtime_adapter_status()
    assert status["fallback"] == "legacy_engine.process_tick"
    assert status["env_flag"] == "POWERFLOW_T002_USE_V6_CORE"


def test_t002_runtime_adapter_has_no_ui_or_alert_imports():
    adapter_file = _core() / "pf_engine_v6_adapter.py"
    text = adapter_file.read_text(encoding="utf-8", errors="replace").lower()

    forbidden = [
        "import dashboard",
        "from dashboard",
        "import cockpit",
        "from cockpit",
        "import telegram",
        "from telegram",
    ]

    for token in forbidden:
        assert token not in text


def test_t002_capture_bridge_uses_adapter_boundary_when_possible():
    capture_bridge = _core() / "capture_bridge.py"
    text = capture_bridge.read_text(encoding="utf-8", errors="replace")

    assert "pf_engine_v6_adapter" in text or "from engine import process_tick" not in text
