from __future__ import annotations

import json
from pathlib import Path
import sys


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def _round_float(value):
    if isinstance(value, float):
        return round(value, 10)
    return value


def _rounded_dict(data: dict):
    return {k: _round_float(v) for k, v in data.items()}


def _contract():
    path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["contract"] == "POWERFLOW_T002_ENGINE_V6_CORE_DB_REPLAY_COMPARISON"
    assert data["runtime_wired"] is False
    return data


def test_db_replay_contract_status_is_explicit():
    data = _contract()
    assert data["status"] in {"NO_DB", "NO_MATCHING_TABLE", "MATCHING_TABLE_NO_ROWS", "SAMPLES_FOUND"}
    assert isinstance(data["case_count"], int)


def test_db_replay_cases_match_legacy_surface_when_samples_exist():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_legacy_tick_surface, legacy_tick_surface_to_dict

    data = _contract()
    if data["status"] != "SAMPLES_FOUND":
        assert data['case_count'] == 0
        return

    assert data["case_count"] > 0
    for case in data["cases"]:
        surface = derive_legacy_tick_surface(case["tick"])
        actual = _rounded_dict(legacy_tick_surface_to_dict(surface))
        expected = _rounded_dict(case["expected_legacy_surface"])
        assert actual == expected, case["id"]


def test_db_replay_keeps_core_unwired():
    core_file = _core() / "pf_engine_v6_core.py"
    text = core_file.read_text(encoding="utf-8", errors="replace")
    forbidden = ["import engine", "from engine import", "import capture_bridge", "send_alert(", "sqlite3", ".execute(", ".commit("]
    for token in forbidden:
        assert token not in text

