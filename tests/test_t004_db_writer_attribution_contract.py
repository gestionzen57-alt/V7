from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_db_writer_attribution_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_DB_WRITER_ATTRIBUTION.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_DB_WRITER_ATTRIBUTION"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert isinstance(data["recommendations"], list)
    assert isinstance(data["table_delta"], list)


def test_t004_db_writer_attribution_status_known():
    path = _repo() / "Docs" / "Contracts" / "T004_DB_WRITER_ATTRIBUTION.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "DB_ROWS_ADVANCED_DURING_WATCH",
        "DB_FILE_CHANGED_WITHOUT_VISIBLE_CAPTURE_PROCESS",
        "CAPTURE_PROCESS_VISIBLE_BUT_NO_DB_ROWS",
        "SCHEDULER_VISIBLE_BUT_NO_DB_ROWS",
        "SCHEDULED_TASK_CANDIDATES_BUT_NO_LIVE_WRITER",
        "NO_VISIBLE_WRITER_AND_NO_DB_ROW_DELTA",
        "INCONCLUSIVE_WRITER_ATTRIBUTION",
    }
    assert data["status"] in allowed

