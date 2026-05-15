from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_usdjpy_diagnostic_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_DATA_DIAGNOSTIC.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_USDJPY_THIN_DATA_DIAGNOSTIC"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert "USDJPY" in data["symbols"]
    assert isinstance(data["tables"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_usdjpy_diagnostic_tables_have_required_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_USDJPY_THIN_DATA_DIAGNOSTIC.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for table in data["tables"]:
        assert "table" in table
        assert "row_count" in table
        assert "columns" in table
        assert "per_symbol" in table

