from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_capture_symbol_routing_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_CAPTURE_SYMBOL_ROUTING_AUDIT"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["thin_symbol"] == "USDJPY"
    assert isinstance(data["risk_flags"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_capture_symbol_routing_has_operator_recommendations():
    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_SYMBOL_ROUTING_AUDIT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    joined = "\n".join(data["recommendations"]).lower()
    assert "engine" in joined
    assert "usdjpy" in joined

