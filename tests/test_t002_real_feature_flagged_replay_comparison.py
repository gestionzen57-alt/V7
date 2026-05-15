from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t002_real_feature_flagged_replay_contract_passes():
    path = _repo() / "Docs" / "Contracts" / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON"
    assert data["case_count"] >= 1
    assert data["v6_pass_count"] == data["case_count"]
    assert data["verdict"] == "FEATURE_FLAGGED_REPLAY_PASS"
    assert data["default_live_behavior_changed"] is False


def test_t002_real_feature_flagged_replay_rows_are_v6_core():
    path = _repo() / "Docs" / "Contracts" / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    for row in data["rows"]:
        assert row["v6_pass"] is True
        assert row["v6"]["ok"] is True
        assert row["v6"]["result_summary"]["route"] == "v6_core"
        assert row["v6"]["send_alert_calls"] == 0
        assert row["v6"]["brain_changed"] is False


def test_t002_real_feature_flagged_replay_legacy_coroutines_are_resolved():
    path = _repo() / "Docs" / "Contracts" / "T002_REAL_FEATURE_FLAGGED_REPLAY_COMPARISON.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert "legacy_async_awaited_count" in data
    for row in data["rows"]:
        assert "awaited" in row["legacy"]
        assert "awaited" in row["v6"]
