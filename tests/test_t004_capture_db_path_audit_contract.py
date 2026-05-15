from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_capture_db_path_audit_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_DB_PATH_AUDIT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_CAPTURE_DB_PATH_AUDIT"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert isinstance(data["candidate_db_paths"], list)
    assert isinstance(data["recommendations"], list)


def test_t004_capture_db_path_audit_db_entries_have_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_DB_PATH_AUDIT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for item in data["candidate_db_paths"]:
        assert "path" in item
        assert "exists" in item
        assert "total_rows" in item

