from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t002_db_table_row_map_contract_is_explicit():
    path = _repo() / "Docs" / "Contracts" / "T002_DB_TABLE_ROW_MAP.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_DB_TABLE_ROW_MAP"
    assert data["runtime_wired"] is False
    assert data["read_only"] is True
    assert data["status"] in {"NO_DB", "DB_FOUND"}
    assert isinstance(data["table_count"], int)
    assert isinstance(data["tables"], list)
    assert isinstance(data["recommendations"], list)


def test_t002_db_table_row_map_entries_have_required_shape():
    path = _repo() / "Docs" / "Contracts" / "T002_DB_TABLE_ROW_MAP.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for table in data["tables"]:
        assert "table" in table
        assert "row_count" in table
        assert "columns" in table
        assert "score" in table

