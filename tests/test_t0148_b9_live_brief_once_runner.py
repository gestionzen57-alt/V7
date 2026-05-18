from __future__ import annotations

from pathlib import Path

from pf_t009_live_brief_once_runner import build_live_brief

S = Path("samples/b9_live_brief_once_runner_v0")


def test_t0148_ready_sample(tmp_path):
    summary = build_live_brief(
        latest_scene_json=S / "sample_latest_scene_candidate.json",
        queue_json=S / "sample_live_scene_queue.json",
        adapter_json=S / "sample_adapter_payload.json",
        similarity_query_json=S / "sample_similarity_query_result.json",
        false_positive_json=S / "sample_false_positive_context.json",
        terrain_synthesis_json=S / "sample_terrain_synthesis.json",
        french_report_json=S / "sample_french_report.json",
        output_dir=tmp_path,
        top_k=3,
    )
    assert summary["brief_state"] == "B9_LIVE_BRIEF_READY"
    assert summary["match_count"] == 3
    assert summary["top_match_film_id"] == "B6FC_20260514_1903_E8F0918A"
    assert summary["false_positive_context_available"] is True
    assert summary["terrain_synthesis_available"] is True
    assert summary["forbidden_language_hits"] == []
    assert (tmp_path / "B9_LIVE_BRIEF_ONCE_V0.md").exists()
    assert (tmp_path / "B9_LIVE_BRIEF_ONCE_V0.zip").exists()


def test_t0148_blocks_missing_input(tmp_path):
    summary = build_live_brief(
        latest_scene_json=S / "sample_latest_scene_candidate.json",
        queue_json=S / "sample_live_scene_queue.json",
        adapter_json=S / "sample_adapter_payload.json",
        similarity_query_json=S / "sample_similarity_query_result.json",
        false_positive_json=S / "missing_false_positive_context.json",
        terrain_synthesis_json=S / "sample_terrain_synthesis.json",
        french_report_json=S / "sample_french_report.json",
        output_dir=tmp_path,
        top_k=3,
    )
    assert summary["brief_state"] == "BLOCKED_MISSING_INPUTS"
    assert "false_positive_json" in summary["missing_inputs"]
    assert summary["forbidden_language_hits"] == []
