from __future__ import annotations

import json
from pathlib import Path

from pf_t009_scene_transition_detector import detect_scene_transitions

SAMPLE = Path("samples/b9_scene_transition_detector_v0/sample_t009_sequence_summary_scene_transitions.json")


def test_t0154_detects_expected_transitions():
    summary = detect_scene_transitions(json.loads(SAMPLE.read_text(encoding="utf-8")))
    assert summary["moments"] == 8
    assert summary["transitions"] == 7
    counts = summary["transition_type_counts"]
    assert counts["BUILD_TO_TEST"] == 1
    assert counts["TEST_TO_ACCEPTED"] == 1
    assert counts["ACCEPTED_TO_MEMORY_SHIFTED"] == 1
    assert counts["MEMORY_SHIFT_TO_NEW_TEST"] == 1
    assert counts["TEST_TO_REJECTED"] == 1
    assert counts["RAW_UNAVAILABLE_TRANSITION_BLOCKED"] == 1
    assert summary["raw_unavailable_blocked_count"] == 1


def test_t0154_no_forbidden_language_and_required_fields():
    summary = detect_scene_transitions(json.loads(SAMPLE.read_text(encoding="utf-8")))
    assert summary["forbidden_language_hits"] == []
    required = {
        "transition_id", "from_scene_state", "to_scene_state", "transition_type",
        "transition_strength_state", "transition_reading_fr", "technical_limits",
    }
    for row in summary["rows"]:
        assert required.issubset(row.keys())
        assert row["transition_reading_fr"]
        assert "probabilité" not in row["transition_reading_fr"].lower()
