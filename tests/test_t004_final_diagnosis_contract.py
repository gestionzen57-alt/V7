from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_final_diagnosis_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_FINAL_DIAGNOSIS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_FINAL_DIAGNOSIS"
    assert data["runtime_wired"] is False
    assert data["db_written"] is False
    assert data["engine_change_required"] is False
    assert isinstance(data["operator_actions"], list)
    assert isinstance(data["engineering_actions"], list)


def test_t004_final_diagnosis_blocks_engine_patch():
    path = _repo() / "Docs" / "Contracts" / "T004_FINAL_DIAGNOSIS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    joined = "\n".join(data["not_causes"] + data["operator_actions"] + data["engineering_actions"]).lower()
    assert "engine" in joined
    assert data["engine_change_required"] is False

