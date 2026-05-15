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


def _golden_cases():
    path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["contract"] == "POWERFLOW_T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES"
    assert data["runtime_wired"] is False
    return data["cases"]


def test_golden_tick_context_cases_match_expected_output():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_tick_context, tick_context_to_dict

    for case in _golden_cases():
        ctx = derive_tick_context(case["tick"], case["prev"])
        actual = _rounded_dict(tick_context_to_dict(ctx))
        expected = _rounded_dict(case["expected_context"])
        assert actual == expected, case["id"]


def test_golden_legacy_surface_cases_match_expected_output():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_legacy_tick_surface, legacy_tick_surface_to_dict

    for case in _golden_cases():
        surface = derive_legacy_tick_surface(case["tick"])
        actual = _rounded_dict(legacy_tick_surface_to_dict(surface))
        expected = _rounded_dict(case["expected_legacy_surface"])
        assert actual == expected, case["id"]


def test_golden_contract_keeps_core_detached_from_runtime():
    core_file = _core() / "pf_engine_v6_core.py"
    text = core_file.read_text(encoding="utf-8", errors="replace")

    forbidden = ["import engine", "from engine import", "import capture_bridge", "send_alert(", "sqlite3", ".execute(", ".commit("]
    for token in forbidden:
        assert token not in text

