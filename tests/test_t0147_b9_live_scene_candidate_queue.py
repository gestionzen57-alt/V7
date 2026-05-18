from __future__ import annotations

from pathlib import Path
import json
import tempfile

from tools.build_t0147_b9_live_scene_candidate_queue import main
from pf_t009_live_scene_candidate_queue import build_queue

SAMPLE = Path("samples/b9_live_scene_candidate_queue_v0/sample_t009_sequence_summary_live_queue.json")


def test_t0147_queue_contract():
    with tempfile.TemporaryDirectory() as tmp:
        out = main(["--sequence-summary-json", str(SAMPLE), "--output-dir", tmp, "--max-candidates", "5"])
        assert out["moments_seen"] == 5
        assert out["candidates_ready"] >= 1
        assert out["candidates_review"] >= 1
        assert out["candidates_rejected"] >= 1
        assert out["forbidden_language_hits"] == []
        assert Path(out["zip"]).exists()
        assert (Path(tmp) / "B9_LATEST_SCENE_CANDIDATE_V0.json").exists()


def test_t0147_rejects_raw_unavailable_and_no_forbidden_language():
    data = json.loads(SAMPLE.read_text(encoding="utf-8"))
    result = build_queue(data)
    states = result["state_counts"]
    assert states.get("B9_LIVE_SCENE_CANDIDATE_REJECT_RAW_UNAVAILABLE", 0) == 1
    assert result["forbidden_language_hits"] == []
    assert result["read_only_contract"]["db_write"] is False
    assert result["read_only_contract"]["telegram"] is False
