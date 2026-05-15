from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_active_db_decision_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_DECISION.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_ACTIVE_DB_DECISION"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["decision"] in {"ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS", "POPULATED_DB_EXISTS", "ONLY_EMPTY_ROOT_DB_FOUND", "NO_POPULATED_DB_CONFIRMED"}
    assert isinstance(data["recommendations"], list)


def test_t004_active_db_decision_blocks_symbol_debug_when_root_empty_and_populated_exists():
    path = _repo() / "Docs" / "Contracts" / "T004_ACTIVE_DB_DECISION.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    if data["decision"] == "ROOT_DB_EMPTY_BUT_POPULATED_DB_EXISTS":
        assert data["best_populated_db"] is not None
        assert data["root_db"]["total_rows"] == 0

