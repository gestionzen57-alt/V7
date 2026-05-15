from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_usdjpy_root_cause_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_ROOT_CAUSE.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_USDJPY_THIN_ROOT_CAUSE"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["thin_symbol"] == "USDJPY"
    assert isinstance(data["tables"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_usdjpy_root_cause_is_known_category():
    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_ROOT_CAUSE.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {"relative_sparsity", "freshness_lag", "symbol_absent_in_symbol_table", "mild_relative_sparsity", "schema_or_no_symbol_table"}
    assert data["likely_cause"] in allowed

