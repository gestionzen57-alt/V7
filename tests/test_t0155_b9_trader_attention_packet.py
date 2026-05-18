from pathlib import Path
import argparse

from tools.build_t0155_b9_trader_attention_packet import run
from pf_t009_trader_attention_packet import load_json, build_trader_attention_packet

ROOT = Path(__file__).resolve().parents[1]


def test_t0155_packet_ready_or_review(tmp_path):
    args = argparse.Namespace(
        input_json=str(ROOT / "samples" / "b9_trader_attention_packet_v0" / "sample_b9_trader_attention_input.json"),
        output_dir=str(tmp_path / "out"),
    )
    summary = run(args)
    assert summary["packet_state"] == "B9_TRADER_ATTENTION_PACKET_REVIEW_TECHNICAL_RISK"
    assert summary["match_count"] == 3
    assert summary["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert summary["false_positive_context_available"] is True
    assert summary["forbidden_language_hits"] == []
    assert summary["no_trade_decision_guard"] is True


def test_t0155_raw_unavailable_blocked():
    payload = load_json(ROOT / "samples" / "b9_trader_attention_packet_v0" / "sample_b9_trader_attention_raw_unavailable.json")
    packet = build_trader_attention_packet(payload)
    assert packet["packet_state"] == "BLOCKED_RAW_UNAVAILABLE"
    assert packet["no_trade_decision_guard"] is True
    assert "RAW_UNAVAILABLE" in packet["blocked_reason"]
