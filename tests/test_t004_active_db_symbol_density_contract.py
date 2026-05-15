from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_active_db_symbol_density_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_SYMBOL_DENSITY.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_ACTIVE_DB_SYMBOL_DENSITY"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert "USDJPY" in data["symbols"]
    assert isinstance(data["symbol_totals"], dict)
    assert isinstance(data["tables"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_active_db_symbol_density_status_is_known():
    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_SYMBOL_DENSITY.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "DB_NOT_FOUND",
        "DB_FOUND_EMPTY",
        "POPULATED_DB_NO_SYMBOL_TABLE",
        "USDJPY_ZERO_REFERENCES_PRESENT",
        "NO_REQUESTED_SYMBOL_ROWS",
        "USDJPY_THIN_RELATIVE",
        "USDJPY_PRESENT",
        "USDJPY_PRESENT_NO_REFERENCES",
    }
    assert data["status"] in allowed

