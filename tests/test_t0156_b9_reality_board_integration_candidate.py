from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_reality_board_integration_candidate import (  # noqa: E402
    BLOCKED_FORBIDDEN_LANGUAGE,
    REVIEW,
    build_reality_board_payload,
    run_from_file,
)


def test_t0156_sample_payload_review_limited(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_reality_board_integration_candidate_v0" / "sample_b9_trader_attention_packet.json"
    summary = run_from_file(sample, tmp_path)
    assert summary["payload_state"] == REVIEW
    assert summary["candidate_id"] == "B9LSC_E49A7AEC65CE"
    assert summary["match_count"] == 3
    assert summary["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert summary["false_positive_context_available"] is True
    assert summary["forbidden_language_hits"] == []
    assert Path(summary["zip"]).exists()


def test_t0156_blocks_forbidden_language() -> None:
    payload = build_reality_board_payload({
        "packet_state": "B9_TRADER_ATTENTION_PACKET_READY",
        "candidate_id": "B9LSC_FORBIDDEN",
        "attention_reason_fr": "BUY maintenant",
        "no_trade_decision_guard": True,
    })
    assert payload["payload_state"] == BLOCKED_FORBIDDEN_LANGUAGE
    assert payload["forbidden_language_hits"]
