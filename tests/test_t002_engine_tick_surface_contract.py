from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def test_tick_surface_contract_exists_and_is_static_map():
    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["contract"] == "POWERFLOW_T002_ENGINE_TICK_SURFACE_CONTRACT"
    assert "tick_attrs" in contract
    assert "prev_attrs" in contract
    assert "supported_by_pf_engine_v6_core" in contract


def test_v6_core_derives_supported_surface_fields():
    sys.path.insert(0, str(_core()))

    from pf_engine_v6_core import derive_tick_context

    tick = SimpleNamespace(symbol="GBPUSD", timestamp="t1", bid=1.2500, ask=1.2502)
    prev = SimpleNamespace(symbol="GBPUSD", timestamp="t0", bid=1.2490, ask=1.2492)

    ctx = derive_tick_context(tick, prev)

    assert ctx.symbol == "GBPUSD"
    assert ctx.timestamp == "t1"
    assert round(ctx.price, 6) == 1.2501
    assert round(ctx.prev_price, 6) == 1.2491
    assert round(ctx.price_delta, 6) == 0.001
    assert round(ctx.spread, 6) == 0.0002


def test_uncovered_tick_fields_are_documented_not_silently_claimed():
    contract_path = _repo() / "Docs" / "Contracts" / "T002_ENGINE_TICK_SURFACE_CONTRACT.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    covered = set(contract["covered_direct_fields"])
    supported = set(contract["supported_by_pf_engine_v6_core"])

    assert covered <= supported
    assert isinstance(contract["uncovered_direct_fields"], list)
    assert isinstance(contract["nested_fields"], list)

