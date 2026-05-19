from __future__ import annotations

import json
from pathlib import Path

from pf_t009_telegram_manual_approval_candidate import build_manual_approval_candidate, run


def test_ready_review_candidate_from_gate(tmp_path: Path):
    gate = {
        "gate_state": "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK",
        "candidate_id": "B9LSC_E49A7AEC65CE",
        "message_fr": "B9 voit une vague progressive réelle. Mémoire comparable, piège technique fort. À surveiller : retest de la zone.",
        "match_count": 3,
        "top_match_film_id": "B6FC_20260511_1641_010496DB",
        "false_positive_context_available": True,
        "no_send_guard": True,
        "no_decision_guard": True,
    }
    packet = build_manual_approval_candidate(gate)
    assert packet["approval_state"] == "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_REVIEW_TECHNICAL_RISK"
    assert packet["manual_approval_required"] is True
    assert packet["manual_approval_granted"] is False
    assert packet["no_send_guard"] is True
    assert packet["match_count"] == 3
    assert packet["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert packet["forbidden_language_hits"] == []


def test_missing_gate_blocks(tmp_path: Path):
    packet = run(tmp_path / "missing.json", tmp_path / "out")
    assert packet["approval_state"] == "BLOCKED_MISSING_TELEGRAM_GATE_INPUT"
    assert packet["manual_approval_granted"] is False
    assert packet["no_send_guard"] is True
    assert (tmp_path / "out" / "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0.json").exists()


def test_forbidden_language_blocks_user_message():
    gate = {
        "gate_state": "B9_TELEGRAM_FR_GATE_CANDIDATE_READY",
        "candidate_id": "X",
        "message_fr": "BUY maintenant",
        "no_send_guard": True,
        "no_decision_guard": True,
    }
    packet = build_manual_approval_candidate(gate)
    assert packet["approval_state"] == "BLOCKED_TELEGRAM_MANUAL_APPROVAL_CANDIDATE"
    assert packet["forbidden_language_hits"]


def test_cli_outputs(tmp_path: Path):
    gate_path = tmp_path / "gate.json"
    gate_path.write_text(json.dumps({
        "gate_state": "B9_TELEGRAM_FR_GATE_CANDIDATE_READY",
        "candidate_id": "B9LSC_SAMPLE",
        "message_fr": "B9 voit une scène acceptée. Mémoire comparable à vérifier.",
        "no_send_guard": True,
        "no_decision_guard": True,
    }, ensure_ascii=False), encoding="utf-8")
    packet = run(gate_path, tmp_path / "out")
    assert packet["approval_state"] == "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_READY_FOR_REVIEW"
    assert (tmp_path / "out" / "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0.zip").exists()
