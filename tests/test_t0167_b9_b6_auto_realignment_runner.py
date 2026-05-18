from pathlib import Path
import json

from pf_t009_b9_b6_auto_realignment_runner import run_alignment

SAMPLE_DIR = Path("samples/b9_b6_auto_realignment_v0")


def test_t0167_realigns_candidate_with_b6_memory(tmp_path):
    summary = run_alignment(
        latest_scene_json=SAMPLE_DIR / "sample_latest_scene_candidate.json",
        b6_index_json=SAMPLE_DIR / "sample_b6_similarity_index.json",
        output_dir=tmp_path,
        top_k=3,
    )
    assert summary["alignment_state"] == "B9_B6_REALIGNMENT_READY"
    assert summary["candidate"]["candidate_id"] == "B9LSC_E49A7AEC65CE"
    assert summary["match_count"] == 3
    assert summary["top_match_film_id"]
    assert summary["query_payload"]["source_candidate_id"] == "B9LSC_E49A7AEC65CE"
    assert all(m["memory_family"] == "DIRECTIONAL_PROGRESS_MEMORY" for m in summary["matches"])
    assert summary["forbidden_language_hits"] == []


def test_t0167_blocks_missing_latest_scene_without_faking(tmp_path):
    summary = run_alignment(
        latest_scene_json=tmp_path / "missing_latest.json",
        b6_index_json=SAMPLE_DIR / "sample_b6_similarity_index.json",
        output_dir=tmp_path / "out",
    )
    assert summary["alignment_state"] == "BLOCKED_MISSING_LATEST_SCENE_CANDIDATE"
    assert summary["match_count"] == 0
    assert summary["missing_inputs"]


def test_t0167_rejects_raw_unavailable_memory(tmp_path):
    summary = run_alignment(
        latest_scene_json=SAMPLE_DIR / "sample_latest_scene_candidate.json",
        b6_index_json=SAMPLE_DIR / "sample_b6_similarity_index_with_raw_unavailable.json",
        output_dir=tmp_path,
        top_k=5,
    )
    assert summary["match_count"] >= 1
    assert summary["rejected_memory_count"] == 1
    assert all("RAW_UNAVAILABLE" not in m.get("source_quality_state", "") for m in summary["matches"])
