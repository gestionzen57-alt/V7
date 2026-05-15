from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def _core() -> Path:
    return _repo() / "Core"


def _load_adapter(monkeypatch):
    sys.path.insert(0, str(_core()))
    import pf_engine_v6_adapter as adapter

    monkeypatch.delenv(adapter.ENV_FLAG, raising=False)
    monkeypatch.delenv(adapter.STRICT_ENV_FLAG, raising=False)
    return adapter


def test_t002_feature_flag_default_uses_legacy_fallback(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    calls = []

    def fake_legacy(tick, prev, brain, send_alert):
        calls.append(("legacy", tick, prev, brain))
        return {"route": "legacy"}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_legacy)

    result = adapter.process_tick(None, None, {}, lambda *_: None)

    assert result == {"route": "legacy"}
    assert calls and calls[0][0] == "legacy"


def test_t002_feature_flag_routes_to_v6_when_entrypoint_exists(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    def fake_legacy(tick, prev, brain, send_alert):
        return {"route": "legacy"}

    def fake_v6(tick, prev, brain, send_alert):
        return {"route": "v6"}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_legacy)
    monkeypatch.setattr(adapter, "_v6_core", SimpleNamespace(process_tick=fake_v6))
    monkeypatch.setattr(adapter, "_V6_CORE_IMPORT_ERROR", None)
    monkeypatch.setenv(adapter.ENV_FLAG, "1")

    result = adapter.process_tick(None, None, {}, lambda *_: None)

    assert result == {"route": "v6"}


def test_t002_feature_flag_missing_v6_entrypoint_falls_back_non_strict(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    def fake_legacy(tick, prev, brain, send_alert):
        return {"route": "legacy"}

    monkeypatch.setattr(adapter._legacy_engine, "process_tick", fake_legacy)
    monkeypatch.setattr(adapter, "_v6_core", SimpleNamespace())
    monkeypatch.setattr(adapter, "_V6_CORE_IMPORT_ERROR", None)
    monkeypatch.setenv(adapter.ENV_FLAG, "1")

    result = adapter.process_tick(None, None, {}, lambda *_: None)

    assert result == {"route": "legacy"}


def test_t002_feature_flag_missing_v6_entrypoint_raises_in_strict(monkeypatch):
    adapter = _load_adapter(monkeypatch)

    monkeypatch.setattr(adapter, "_v6_core", SimpleNamespace())
    monkeypatch.setattr(adapter, "_V6_CORE_IMPORT_ERROR", None)
    monkeypatch.setenv(adapter.ENV_FLAG, "1")
    monkeypatch.setenv(adapter.STRICT_ENV_FLAG, "1")

    with pytest.raises(RuntimeError):
        adapter.process_tick(None, None, {}, lambda *_: None)


def test_t002_feature_flag_readiness_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T002_FEATURE_FLAGGED_REPLAY_READINESS.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_FEATURE_FLAGGED_REPLAY_READINESS"
    assert data["signature_ok"] is True
    assert data["default_live_behavior_changed"] is False
    assert data["feature_flag_boundary_tested"] is True
    assert data["strict_mode_tested"] is True
    assert data["status"] in {
        "FEATURE_FLAG_REPLAY_READY",
        "FEATURE_FLAG_REPLAY_PASSED",
        "FEATURE_FLAG_BOUNDARY_VALID_CORE_RUNTIME_ENTRYPOINT_MISSING",
    }
