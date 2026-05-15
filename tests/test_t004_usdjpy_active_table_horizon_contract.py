from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_usdjpy_active_table_horizon_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_ACTIVE_TABLE_HORIZON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_USDJPY_ACTIVE_TABLE_HORIZON"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["thin_symbol"] == "USDJPY"
    assert isinstance(data["tables"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_usdjpy_active_table_horizon_verdict_known():
    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_ACTIVE_TABLE_HORIZON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "POSSIBLE_SUFFIX_OR_NEAR_SYMBOL_ROUTE",
        "USDJPY_ABSENT_FROM_ACTIVE_INSERTION_TABLES",
        "USDJPY_STALE_VS_REFERENCES",
        "USDJPY_HISTORICALLY_SPARSE_IN_ACTIVE_TABLES",
        "NO_CLEAR_USDJPY_HORIZON_DEFECT",
    }
    assert data["verdict"] in allowed

