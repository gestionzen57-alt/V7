# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path

import pytest


CORE = Path(__file__).resolve().parents[1] / "Core"
if str(CORE) not in sys.path:
    sys.path.insert(0, str(CORE))


def install_upstream_stubs(monkeypatch):
    sent = []

    data_guard = types.ModuleType("pf_data_visibility_guard")

    def check_data_visibility(window):
        return dict(
            window.get(
                "visibility_override",
                {
                    "node_status": "EMIT",
                    "data_visibility": window.get("data_visibility", "TACTICAL_OK"),
                    "source_mode": window.get("source_mode", "RAW_TICK_PLUS_FORCE_CONTEXT"),
                    "confidence_cap": window.get("confidence_cap", 1.0),
                },
            )
        )

    data_guard.check_data_visibility = check_data_visibility
    monkeypatch.setitem(sys.modules, "pf_data_visibility_guard", data_guard)

    false_birth = types.ModuleType("pf_false_birth_filter")
    false_birth.is_false_birth = lambda window: bool(window.get("false_birth", False))
    monkeypatch.setitem(sys.modules, "pf_false_birth_filter", false_birth)

    zone_reader = types.ModuleType("pf_zone_context_reader")

    def read_zone_context(window):
        return dict(
            window.get(
                "zone_context_override",
                {
                    "zone_role": window.get("zone_role", "ACCEPTANCE_ZONE"),
                    "zone_status": "ACTIVE",
                    "zone_low": window.get("zone_low"),
                    "zone_high": window.get("zone_high"),
                },
            )
        )

    zone_reader.read_zone_context = read_zone_context
    monkeypatch.setitem(sys.modules, "pf_zone_context_reader", zone_reader)

    price_verdict_mod = types.ModuleType("pf_price_verdict")

    class PricePath:
        def __init__(self, *args, **kwargs):
            self.payload = kwargs or (args[0] if args else {})

    class ZoneBounds:
        def __init__(self, *args, **kwargs):
            self.payload = kwargs or {"zone_low": args[0], "zone_high": args[1]}

    def compute_price_verdict(price_path, zone_bounds):
        payload = getattr(price_path, "payload", {}) or {}
        return dict(payload.get("price_verdict_override", {"verdict": "PULLBACK_ABSORBED", "confidence": 0.82}))

    price_verdict_mod.PricePath = PricePath
    price_verdict_mod.ZoneBounds = ZoneBounds
    price_verdict_mod.compute_price_verdict = compute_price_verdict
    monkeypatch.setitem(sys.modules, "pf_price_verdict", price_verdict_mod)

    snapshot_mod = types.ModuleType("pf_terrain_node_snapshot")

    def create_terrain_node_snapshot(window, visibility, zone_context, price_verdict):
        return {
            "symbol": window.get("symbol"),
            "timestamp": window.get("timestamp"),
            "node_role_fr": window.get("node_role_fr", "Pullback absorbé"),
            "zone_low": window.get("zone_low"),
            "zone_high": window.get("zone_high"),
            "price_verdict": price_verdict,
            "data_visibility": visibility.get("data_visibility"),
            "source_stack": visibility.get("source_mode"),
            "zone_context": zone_context,
        }

    snapshot_mod.create_terrain_node_snapshot = create_terrain_node_snapshot
    monkeypatch.setitem(sys.modules, "pf_terrain_node_snapshot", snapshot_mod)

    requalifier_mod = types.ModuleType("pf_packet_requalifier_v767")

    def requalify_packet(raw_packet, zone_context, price_verdict, previous_scene_state, data_visibility):
        return {
            "requalified_event": window_event(raw_packet, price_verdict),
            "requalified_event_fr": "Release UP — pullback absorbé",
            "requalification_rule": "TEST_RULE",
            "original_bias": raw_packet.get("raw_bias"),
            "requalified_confidence": float(raw_packet.get("packet_strength", 0.0)),
            "should_alert": True,
            "alert_reason": "perception B9 qualifiée",
            "forbidden_claims": [],
            "source_stack": data_visibility.get("source_mode", "TEST_SOURCE"),
        }

    def window_event(raw_packet, price_verdict):
        if price_verdict.get("verdict") == "REJECTED":
            return "RELEASE_UP_THEN_HIGH_ZONE_EXHAUSTION"
        return "RELEASE_UP_PULLBACK_ABSORBED"

    requalifier_mod.requalify_packet = requalify_packet
    monkeypatch.setitem(sys.modules, "pf_packet_requalifier_v767", requalifier_mod)

    import telegram_alert_sender_b9

    monkeypatch.setattr(telegram_alert_sender_b9, "send_b9_alert", lambda node, requalified, config: sent.append((node, requalified, config)))

    sys.modules.pop("pf_engine_b9", None)
    engine_mod = importlib.import_module("pf_engine_b9")
    monkeypatch.setattr(engine_mod, "send_b9_alert", lambda node, requalified, config: sent.append((node, requalified, config)))
    return engine_mod, sent


@pytest.fixture()
def sample_window():
    return {
        "symbol": "GBPUSD",
        "timestamp": "2026-05-15T10:11:00Z",
        "zone_low": 1.3350,
        "zone_high": 1.3374,
        "current_price": 1.3368,
        "zone_touch_history": [{"timestamp": "2026-05-15T10:00:00Z", "price": 1.3350}],
        "zone_bars_since_touch": 3,
        "price_path": {"prices": [1.3350, 1.3360, 1.3374]},
        "raw_bias": "UP",
        "packet_strength": 0.82,
        "previous_scene_state": {"scene_state": "POST_RELEASE", "last_structural_event": "RELEASE_UP_NODE"},
    }


def test_pipeline_complete_end_to_end(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result["status"] == "NODE_CREATED"
    assert result["symbol"] == "GBPUSD"
    assert result["node"]["node_role_fr"] == "Pullback absorbé"
    assert result["requalified"]["requalified_event"] == "RELEASE_UP_PULLBACK_ABSORBED"
    assert result["alert_sent"] is True
    assert len(sent) == 1


def test_false_birth_intercepts_pipeline(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    sample_window["false_birth"] = True
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result == {
        "status": "FALSE_BIRTH",
        "symbol": "GBPUSD",
        "node": None,
        "requalified": None,
        "alert_sent": False,
    }
    assert sent == []


def test_do_not_emit_stops_alert(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    sample_window["visibility_override"] = {"node_status": "DO_NOT_EMIT", "data_visibility": "TACTICAL_OK"}
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result["status"] == "NODE_CREATED"
    assert result["alert_sent"] is False
    assert sent == []


@pytest.mark.parametrize("data_visibility", ["TACTICAL_OK", "RECONSTRUCTED"])
def test_alert_sent_for_tactical_or_reconstructed(monkeypatch, sample_window, data_visibility):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    sample_window["data_visibility"] = data_visibility
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result["alert_sent"] is True
    assert len(sent) == 1


def test_reading_partial_alerts_when_confidence_is_solid(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    sample_window["data_visibility"] = "READING_PARTIAL"
    sample_window["packet_strength"] = 0.60
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result["alert_sent"] is True
    assert len(sent) == 1


def test_reading_partial_does_not_alert_when_confidence_is_weak(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    sample_window["data_visibility"] = "READING_PARTIAL"
    sample_window["packet_strength"] = 0.59
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result["alert_sent"] is False
    assert sent == []


def test_no_alert_when_telegram_disabled(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": False})
    result = engine.process_window(sample_window)
    assert result["status"] == "NODE_CREATED"
    assert result["alert_sent"] is False
    assert sent == []


def test_node_created_returns_complete_node(monkeypatch, sample_window):
    engine_mod, _sent = install_upstream_stubs(monkeypatch)
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": False})
    result = engine.process_window(sample_window)
    node = result["node"]
    assert node["symbol"] == "GBPUSD"
    assert node["zone_low"] == pytest.approx(1.3350)
    assert node["zone_high"] == pytest.approx(1.3374)
    assert node["price_verdict"]["verdict"] == "PULLBACK_ABSORBED"
    assert node["data_visibility"] == "TACTICAL_OK"


def test_imports_work(monkeypatch):
    engine_mod, _sent = install_upstream_stubs(monkeypatch)
    assert hasattr(engine_mod, "PowerFlowEngineB9")
    assert callable(engine_mod.check_data_visibility)
    assert callable(engine_mod.is_false_birth)
    assert callable(engine_mod.requalify_packet)


def test_rejected_verdict_flows_to_requalifier(monkeypatch, sample_window):
    engine_mod, _sent = install_upstream_stubs(monkeypatch)
    sample_window["price_path"] = {"price_verdict_override": {"verdict": "REJECTED", "confidence": 0.77}}
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": False})
    result = engine.process_window(sample_window)
    assert result["requalified"]["requalified_event"] == "RELEASE_UP_THEN_HIGH_ZONE_EXHAUSTION"


def test_unknown_visibility_does_not_alert(monkeypatch, sample_window):
    engine_mod, sent = install_upstream_stubs(monkeypatch)
    sample_window["data_visibility"] = "BLIND_UNKNOWN"
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": True})
    result = engine.process_window(sample_window)
    assert result["alert_sent"] is False
    assert sent == []


def test_process_window_requires_dict(monkeypatch):
    engine_mod, _sent = install_upstream_stubs(monkeypatch)
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": False})
    with pytest.raises(TypeError):
        engine.process_window(None)


def test_engine_preserves_previous_scene_state_for_requalifier(monkeypatch, sample_window):
    captured = {}
    engine_mod, _sent = install_upstream_stubs(monkeypatch)

    def capture_requalify(raw_packet, zone_context, price_verdict, previous_scene_state, data_visibility):
        captured["previous"] = previous_scene_state
        return {
            "requalified_event": "RELEASE_UP_PULLBACK_ABSORBED",
            "requalified_confidence": 0.8,
            "source_stack": "TEST",
        }

    monkeypatch.setattr(engine_mod, "requalify_packet", capture_requalify)
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": False})
    engine.process_window(sample_window)
    assert captured["previous"]["scene_state"] == "POST_RELEASE"
    assert captured["previous"]["last_structural_event"] == "RELEASE_UP_NODE"


def test_raw_packet_shape_for_requalifier(monkeypatch, sample_window):
    captured = {}
    engine_mod, _sent = install_upstream_stubs(monkeypatch)

    def capture_requalify(raw_packet, zone_context, price_verdict, previous_scene_state, data_visibility):
        captured["raw"] = raw_packet
        return {
            "requalified_event": "RELEASE_UP_PULLBACK_ABSORBED",
            "requalified_confidence": 0.8,
            "source_stack": "TEST",
        }

    monkeypatch.setattr(engine_mod, "requalify_packet", capture_requalify)
    engine = engine_mod.PowerFlowEngineB9({"ENABLE_TELEGRAM": False})
    engine.process_window(sample_window)
    assert captured["raw"] == {
        "symbol": "GBPUSD",
        "timestamp": "2026-05-15T10:11:00Z",
        "raw_bias": "UP",
        "packet_strength": 0.82,
    }
