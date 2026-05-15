from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_live_capture_health_counter_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_LIVE_CAPTURE_HEALTH_COUNTER.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_LIVE_CAPTURE_HEALTH_COUNTER"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["thin_symbol"] == "USDJPY"
    assert isinstance(data["deltas"], dict)
    assert isinstance(data["recommendations"], list)


def test_t004_live_capture_health_counter_status_known():
    path = _repo() / "Docs" / "Contracts" / "T004_LIVE_CAPTURE_HEALTH_COUNTER.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "DB_READ_ERROR",
        "NO_LIVE_DELTA_CAPTURE_INACTIVE_OR_IDLE",
        "THIN_SYMBOL_NO_DELTA_REFERENCES_ACTIVE",
        "THIN_SYMBOL_DELTA_UNDER_25_PERCENT_REF_AVG",
        "THIN_SYMBOL_DELTA_MODERATELY_THIN",
        "THIN_SYMBOL_DELTA_HEALTHY",
        "THIN_SYMBOL_DELTA_PRESENT_REFERENCES_IDLE",
    }
    assert data["status"] in allowed

