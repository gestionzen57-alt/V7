from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_active_insertion_symbol_delta_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_ACTIVE_INSERTION_SYMBOL_DELTA"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["thin_symbol"] == "USDJPY"
    assert isinstance(data["symbol_deltas"], dict)
    assert isinstance(data["table_deltas"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_active_insertion_symbol_delta_status_known():
    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_INSERTION_SYMBOL_DELTA.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "NO_TABLE_ROW_DELTA",
        "TABLE_ROWS_ADVANCED_WITHOUT_TRACKED_SYMBOL_DELTA",
        "REFERENCES_ADVANCED_THIN_SYMBOL_ZERO",
        "THIN_SYMBOL_ADVANCED_BUT_UNDER_25_PERCENT_REF_AVG",
        "THIN_SYMBOL_ADVANCED_MODERATELY_THIN",
        "THIN_SYMBOL_ADVANCED_HEALTHY",
        "THIN_SYMBOL_ADVANCED_REFERENCES_IDLE",
        "TABLE_ROWS_ADVANCED_UNCLASSIFIED_SYMBOLS",
    }
    assert data["status"] in allowed

