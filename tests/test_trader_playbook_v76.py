# -*- coding: utf-8 -*-
from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "patch" / "pf_trader_playbook_once.py"
spec = importlib.util.spec_from_file_location("pf_trader_playbook_once", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def build(packet):
    return mod.build_playbook(packet)


def assert_no_execution_fields(playbook):
    text = str(playbook).upper()
    for forbidden in ["BUY", "SELL", "ENTRY", "EXIT", "TARGET", "STOP"]:
        assert forbidden not in text
    assert playbook["do_not_execute"] is True
    assert playbook["trader_decides"] is True


def test_high_zone_exhaustion_with_partial_data():
    p = {
        "symbol": "GBPUSD",
        "qualified_bias": "HIGH_ZONE_EXHAUSTION_RISK",
        "price_confirmation": "PRICE_REJECTED_LOW",
        "data_visibility": "READING_PARTIAL",
        "packet_quality": "DEGRADED",
    }
    out = build(p)
    assert out["playbook_state"] == "HIGH_ZONE_EXHAUSTION_RISK"
    assert out["playbook_label_fr"] == "Risque d'epuisement en zone haute"
    assert "Ne pas chase" in out["watch_plan_fr"]
    assert "zone haute" in out["invalidation_fr"]
    assert "Lecture partielle" in out["no_trade_warning_fr"]
    assert_no_execution_fields(out)


def test_post_high_unwind():
    p = {
        "symbol": "GBPUSD",
        "film_state": "HIGH_ZONE_REJECTION",
        "last_structural_event": "HIGH_ZONE_REJECTION",
        "raw_bias": "PAIR_DOWN",
        "qualified_bias": "POST_HIGH_UNWIND",
        "price_confirmation": "PRICE_CONFIRMED_DOWN",
        "data_visibility": "FULL_STACK_VISIBLE",
    }
    out = build(p)
    assert out["playbook_state"] == "POST_HIGH_UNWIND"
    assert "zone haute" in out["playbook_label_fr"]
    assert_no_execution_fields(out)


def test_second_leg_down_after_counter_breath_rejected():
    p = {
        "symbol": "GBPUSD",
        "last_structural_event": "COUNTER_BREATH_REJECTED",
        "current_move_role": "SECOND_LEG",
        "qualified_bias": "SECOND_LEG_DOWN",
        "raw_bias": "PAIR_DOWN",
        "price_confirmation": "PRICE_CONFIRMED_DOWN",
        "data_visibility": "TACTICAL_OK",
    }
    out = build(p)
    assert out["playbook_state"] == "SECOND_LEG_DOWN"
    assert "Second mouvement" in out["playbook_label_fr"]
    assert_no_execution_fields(out)


def test_post_release_counter_breath():
    p = {
        "symbol": "GBPUSD",
        "last_structural_event": "RELEASE_DOWN_VALIDATED",
        "current_move_role": "COUNTER_BREATH",
        "qualified_bias": "POST_RELEASE_COUNTER_BREATH",
        "raw_bias": "PAIR_UP",
        "price_confirmation": "PRICE_PENDING",
        "data_visibility": "FULL_STACK_VISIBLE",
    }
    out = build(p)
    assert out["playbook_state"] == "POST_RELEASE_COUNTER_BREATH"
    assert "Respiration inverse" in out["playbook_label_fr"]
    assert_no_execution_fields(out)


def test_post_low_counter_breath():
    p = {
        "symbol": "GBPUSD",
        "film_state": "LOWER_ZONE_RANGE_ACTIVE",
        "current_move_role": "POST_LOW_REACTION",
        "qualified_bias": "POST_LOW_COUNTER_BREATH",
        "raw_bias": "PAIR_UP",
        "price_confirmation": "PRICE_PENDING",
        "data_visibility": "TACTICAL_OK",
    }
    out = build(p)
    assert out["playbook_state"] == "POST_LOW_COUNTER_BREATH"
    assert "zone basse" in out["playbook_context_fr"]
    assert_no_execution_fields(out)


def test_honest_unknown_data_limited():
    p = {
        "symbol": "GBPUSD",
        "film_state": "UNKNOWN",
        "qualified_bias": "HONEST_UNKNOWN",
        "price_confirmation": "UNKNOWN",
        "data_visibility": "MICROFILM_MISSING_PACKETS_STALE",
        "packet_quality": "HONEST_UNKNOWN",
    }
    out = build(p)
    assert out["playbook_state"] == "HONEST_UNKNOWN"
    assert "inconnue honnete" in out["playbook_label_fr"]
    assert "Lecture partielle" in out["no_trade_warning_fr"]
    assert_no_execution_fields(out)


def test_nested_packet_fields_are_supported():
    p = {
        "terrain": {
            "symbol": "GBPUSD",
            "film_state": "LOWER_ZONE_ACTIVE",
            "current_move_role": "POST_LOW_REACTION",
            "raw_bias": "PAIR_UP",
            "data_visibility": "TACTICAL_OK",
        },
        "packet": {
            "qualified_bias": "POST_LOW_COUNTER_BREATH",
            "price_confirmation": "PRICE_PENDING",
        },
    }
    out = build(p)
    assert out["playbook_state"] == "POST_LOW_COUNTER_BREATH"
    assert out["source_fields"]["qualified_bias"] == "POST_LOW_COUNTER_BREATH"

