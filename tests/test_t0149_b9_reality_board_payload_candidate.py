from __future__ import annotations

import json
from pathlib import Path

from pf_t009_reality_board_payload_candidate import (
    BLOCKED_MISSING_INPUT_STATE,
    REVIEW_LIMITED_SOURCE_STATE,
    build_blocked_missing_input_payload,
    build_payload_candidate,
)
from tools.build_t0149_b9_reality_board_payload_candidate import run


ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "b9_reality_board_payload_candidate_v0" / "sample_b9_live_brief_once_ready.json"


class Args:
    live_brief_json = str(SAMPLE)
    output_dir = str(ROOT / "outputs" / "b9_reality_board_payload_candidate_v0_test")


def test_t0149_build_payload_candidate_review_limited_source():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    payload = build_payload_candidate(data)
    assert payload["version"] == "T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0"
    assert payload["payload_state"] == REVIEW_LIMITED_SOURCE_STATE
    assert payload["candidate_id"] == "B9LIVE_20260515_1100_1131"
    assert payload["memory_confidence_ladder"] == "MEMORY_PARTIAL_COMPARABLE"
    assert payload["raw_unavailable_in_results"] is False
    assert payload["forbidden_language_hits"] == []
    assert payload["read_only_contract"]["writes_powerflow_db"] is False
    assert payload["read_only_contract"]["writes_dashboard"] is False
    assert payload["missing_required_field_counts"] == {}


def test_t0149_cli_writes_outputs_and_blocks_missing_input(tmp_path):
    summary = run(Args())
    assert summary["candidate_id"] == "B9LIVE_20260515_1100_1131"
    assert summary["payload_state"] == REVIEW_LIMITED_SOURCE_STATE
    assert summary["forbidden_language_hits"] == []
    assert Path(summary["zip"]).exists()

    blocked = build_blocked_missing_input_payload(["missing.json"])
    assert blocked["payload_state"] == BLOCKED_MISSING_INPUT_STATE
    assert blocked["read_only_contract"]["sends_telegram"] is False
