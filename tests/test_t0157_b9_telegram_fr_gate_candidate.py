from argparse import Namespace
from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_telegram_fr_gate_candidate import build_telegram_gate_candidate
from tools.build_t0157_b9_telegram_fr_gate_candidate import run


def sample_payload():
    return {
        "payload_state": "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK",
        "candidate_id": "B9LSC_E49A7AEC65CE",
        "scene_state": "SCENE_ACCEPTED",
        "scene_role": "PROGRESSIVE_FIRST_LEG",
        "active_zone": "1.3350-1.3374",
        "latest_node": "PROGRESSIVE_REACTION_NODE",
        "price_verdict": "ACCEPTED",
        "memory_confidence_ladder": "MEMORY_PARTIAL_COMPARABLE",
        "match_count": 3,
        "top_match_film_id": "B6FC_20260511_1641_010496DB",
        "false_positive_context_available": True,
        "source_quality_gate_state": "SOURCE_QUALITY_LIVE_UNQUALIFIED",
        "technical_risks": ["source live candidate encore unqualified", "mémoire comparable avec piège technique"],
        "no_trade_decision_guard": True,
    }


def test_gate_candidate_review_no_send():
    result = build_telegram_gate_candidate(sample_payload())
    assert result["gate_state"] == "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK"
    assert result["no_send_guard"] is True
    assert result["no_trade_decision_guard"] is True
    assert result["match_count"] == 3
    assert result["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert result["false_positive_context_available"] is True
    assert result["forbidden_language_hits"] == []
    assert "aucun ordre" in result["telegram_message_fr"].lower()


def test_cli_outputs(tmp_path):
    input_path = tmp_path / "payload.json"
    input_path.write_text(json.dumps(sample_payload(), ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out"
    summary = run(Namespace(reality_board_payload_json=str(input_path), output_dir=str(out)))
    assert summary["gate_state"] == "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK"
    assert (out / "B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json").exists()
    assert (out / "B9_TELEGRAM_FR_MESSAGE_CANDIDATE_V0.txt").exists()
    assert (out / "B9_TELEGRAM_FR_GATE_CANDIDATE_V0.zip").exists()
