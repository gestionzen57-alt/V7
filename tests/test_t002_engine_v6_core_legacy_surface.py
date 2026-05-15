from __future__ import annotations

from pathlib import Path
import json
import sys
from types import SimpleNamespace


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_derive_legacy_tick_surface_from_object():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_legacy_tick_surface

    tick = SimpleNamespace(dev_a="GBP", dev_b="USD", val_a="1.2", val_b="-0.4", gap="1.6", timeframe=1, spread="0.0002")
    surface = derive_legacy_tick_surface(tick)

    assert surface.dev_a == "GBP"
    assert surface.dev_b == "USD"
    assert surface.val_a == 1.2
    assert surface.val_b == -0.4
    assert surface.gap == 1.6
    assert surface.timeframe == 1
    assert surface.spread == 0.0002


def test_derive_legacy_tick_surface_from_dict_and_derived_spread():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_legacy_tick_surface

    tick = {"dev_a": "EUR", "dev_b": "USD", "val_a": 0.7, "val_b": -0.2, "gap": 0.9, "timeframe": 5, "bid": 1.1000, "ask": 1.1003}
    surface = derive_legacy_tick_surface(tick)

    assert surface.dev_a == "EUR"
    assert surface.dev_b == "USD"
    assert surface.val_a == 0.7
    assert surface.val_b == -0.2
    assert surface.gap == 0.9
    assert surface.timeframe == 5
    assert round(surface.spread, 6) == 0.0003


def test_legacy_tick_surface_to_dict():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_legacy_tick_surface, legacy_tick_surface_to_dict

    surface = derive_legacy_tick_surface({"dev_a": "GBP", "dev_b": "JPY", "val_a": 2, "val_b": 1, "gap": 1, "timeframe": 15})
    data = legacy_tick_surface_to_dict(surface)

    assert data["dev_a"] == "GBP"
    assert data["dev_b"] == "JPY"
    assert data["gap"] == 1.0
    assert data["spread"] is None


def test_legacy_surface_fields_match_t002_tick_contract_expectation():
    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    expected = {"dev_a", "dev_b", "val_a", "val_b", "gap", "timeframe", "spread"}
    seen = set(contract["uncovered_direct_fields"]) | set(contract["covered_direct_fields"])

    assert expected <= seen


def test_pf_engine_v6_core_still_has_no_runtime_wiring_or_side_effects():
    core_file = _core() / "pf_engine_v6_core.py"
    text = core_file.read_text(encoding="utf-8", errors="replace")

    forbidden_tokens = ["import engine", "from engine import", "import capture_bridge", "sqlite3", ".execute(", ".commit(", "send_alert(", "dashboard_", "cockpit_"]

    for token in forbidden_tokens:
        assert token not in text

