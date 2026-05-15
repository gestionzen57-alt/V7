from __future__ import annotations

import inspect
import json
from pathlib import Path
import sys


def test_engine_process_tick_contract_signature_is_stable():
    repo = Path(__file__).resolve().parents[1]
    core = repo / "Core"
    sys.path.insert(0, str(core))

    import engine

    contract_path = repo / "Docs" / "Contracts" / "T002_ENGINE_PROCESS_TICK_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert hasattr(engine, "process_tick")
    assert callable(engine.process_tick)
    assert str(inspect.signature(engine.process_tick)) == contract["signature"]


def test_capture_bridge_uses_v6_adapter_boundary():
    repo = Path(__file__).resolve().parents[1]
    capture_bridge = repo / "Core" / "capture_bridge.py"
    text = capture_bridge.read_text(encoding="utf-8", errors="replace")

    assert "from pf_engine_v6_adapter import process_tick" in text
    assert "from engine import process_tick" not in text
