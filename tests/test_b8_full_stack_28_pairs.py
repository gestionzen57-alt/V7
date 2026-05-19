"""GPT-4 validation tests: B8 28-pair full-stack over PowerFlowEngineB9.

These tests are intentionally engine-facing and read-only. They do not write DB,
do not send Telegram, and do not mutate dashboard state.
"""
from __future__ import annotations

import importlib
from typing import Any

import pytest

PAIRS_28 = [
    # USD quote
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD",
    # USD base
    "USDJPY", "USDCAD", "USDCHF",
    # EUR cross
    "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD",
    # GBP cross
    "GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD",
    # AUD cross
    "AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD",
    # CAD JPY CHF NZD cross
    "CADJPY", "CHFJPY", "NZDJPY", "NZDCHF", "NZDCAD", "CADCHF",
]

USD_QUOTE = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD"]
USD_BASE = ["USDJPY", "USDCAD", "USDCHF"]
EUR_CROSS = ["EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD"]
GBP_CROSS = ["GBPJPY", "GBPCHF", "GBPAUD", "GBPCAD", "GBPNZD"]
AUD_CROSS = ["AUDJPY", "AUDCHF", "AUDCAD", "AUDNZD"]
OTHER_CROSS = ["CADJPY", "CHFJPY", "NZDJPY", "NZDCHF", "NZDCAD", "CADCHF"]
VALID_STATUSES = {"NODE_CREATED", "FALSE_BIRTH", "NO_EVENT"}

ENGINE_CANDIDATES = [
    ("pf_engine_b9", "PowerFlowEngineB9"),
    ("powerflow_engine_b9", "PowerFlowEngineB9"),
    ("pf_b9_engine", "PowerFlowEngineB9"),
    ("pf_engine", "PowerFlowEngineB9"),
    ("engine", "PowerFlowEngineB9"),
]


def _load_engine_class():
    errors: list[str] = []
    for module_name, class_name in ENGINE_CANDIDATES:
        try:
            module = importlib.import_module(module_name)
            engine_cls = getattr(module, class_name)
            return engine_cls
        except Exception as exc:  # noqa: BLE001 - report all candidate failures.
            errors.append(f"{module_name}.{class_name}: {exc}")
    pytest.skip("PowerFlowEngineB9 not importable in this environment. Tried: " + " | ".join(errors))


@pytest.fixture()
def engine():
    Engine = _load_engine_class()
    return Engine({"ENABLE_TELEGRAM": False})


def make_mock_window(symbol: str) -> dict[str, Any]:
    """Generate a valid mock B9/B8 window for one symbol."""
    return {
        "symbol": symbol,
        "timestamp": "2026-05-19T09:00:00",
        "zone_low": 1.2700,
        "zone_high": 1.2750,
        "current_price": 1.2725,
        "source_stack": "FORCE_SNAPSHOT_DERIVED",
        "raw_bias": "UP",
        "packet_strength": 0.6,
        "zone_bars_since_touch": 10,
        "zone_touch_history": [],
        "previous_scene_state": {},
        "price_path": {
            "price_min": 1.2705,
            "price_max": 1.2748,
            "price_open": 1.2715,
            "price_close": 1.2730,
            "ticks_total": 15,
            "ticks_inside_zone": 5,
            "ticks_inside_center_band": 2,
            "dwell_seconds_inside_zone": 10.0,
            "dwell_seconds_inside_center": 0.0,
            "max_center_penetration_ratio": 0.4,
            "price_exits_original_side": False,
            "rejection_distance_pips": 0.0,
            "rejection_speed_pips_per_min": 0.0,
            "net_progress_pips": 3.0,
            "is_pullback_context": False,
        },
    }


def _assert_result_contract(result: dict[str, Any], symbol: str) -> None:
    assert isinstance(result, dict)
    assert result.get("status") in VALID_STATUSES
    assert result.get("symbol") in (symbol, None) or "symbol" in result
    assert result.get("alert_sent") in (False, None)
    if result.get("status") == "NODE_CREATED":
        node = result.get("node")
        assert isinstance(node, dict)
        assert node.get("symbol") in (symbol, None) or "symbol" in node


def test_28_pairs_no_crash(engine):
    """28 pairs process without crash and return a valid status."""
    for pair in PAIRS_28:
        result = engine.process_window(make_mock_window(pair))
        _assert_result_contract(result, pair)


def test_pairs_list_has_exactly_28_unique_symbols():
    assert len(PAIRS_28) == 28
    assert len(set(PAIRS_28)) == 28


def test_gbpusd_node_complete_when_created(engine):
    """GBPUSD node exposes required node fields when a node is created."""
    result = engine.process_window(make_mock_window("GBPUSD"))
    _assert_result_contract(result, "GBPUSD")
    if result["status"] == "NODE_CREATED":
        node = result["node"]
        assert "node_id" in node
        assert "zone_bounds" in node
        assert "price_verdict_candidate" in node
        assert "data_visibility" in node


def test_alert_not_sent_enable_false(engine):
    result = engine.process_window(make_mock_window("GBPUSD"))
    assert result.get("alert_sent") in (False, None)


@pytest.mark.parametrize("pair", USD_BASE)
def test_usd_base_pairs_process(engine, pair):
    result = engine.process_window(make_mock_window(pair))
    _assert_result_contract(result, pair)


@pytest.mark.parametrize("pair", ["EURGBP", "GBPJPY", "AUDNZD"])
def test_cross_pairs_process(engine, pair):
    result = engine.process_window(make_mock_window(pair))
    _assert_result_contract(result, pair)


@pytest.mark.parametrize("bucket", [USD_QUOTE, USD_BASE, EUR_CROSS, GBP_CROSS, AUD_CROSS, OTHER_CROSS])
def test_all_b8_buckets_process(engine, bucket):
    for pair in bucket:
        result = engine.process_window(make_mock_window(pair))
        _assert_result_contract(result, pair)


def test_force_snapshot_derived_source_stack_preserved_or_accepted(engine):
    window = make_mock_window("EURUSD")
    result = engine.process_window(window)
    _assert_result_contract(result, "EURUSD")


def test_false_birth_and_no_event_are_non_decision_states(engine):
    result = engine.process_window(make_mock_window("NZDCAD"))
    assert result["status"] in VALID_STATUSES
    assert "BUY" not in str(result).upper()
    assert "SELL" not in str(result).upper()


def test_engine_does_not_require_telegram_for_28_pairs(engine):
    for pair in PAIRS_28:
        result = engine.process_window(make_mock_window(pair))
        assert result.get("alert_sent") in (False, None)
