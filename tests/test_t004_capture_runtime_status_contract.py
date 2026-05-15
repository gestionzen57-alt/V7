from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_capture_runtime_status_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_RUNTIME_STATUS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_CAPTURE_RUNTIME_STATUS"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["db_status"], dict)


def test_t004_capture_runtime_status_known():
    path = _repo() / "Docs" / "Contracts" / "T004_CAPTURE_RUNTIME_STATUS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "ACTIVE_DB_NOT_FOUND",
        "CAPTURE_PROCESS_DETECTED_DB_RECENT",
        "CAPTURE_PROCESS_DETECTED_DB_STALE",
        "SCHEDULER_PROCESS_DETECTED_DB_RECENT",
        "SCHEDULER_PROCESS_DETECTED_DB_STALE",
        "PYTHON_PROCESS_DETECTED_DB_RECENT",
        "PYTHON_PROCESS_DETECTED_DB_STALE",
        "NO_CAPTURE_PROCESS_DETECTED_BUT_DB_RECENT",
        "NO_CAPTURE_PROCESS_DETECTED_DB_STALE",
    }
    assert data["status"] in allowed

