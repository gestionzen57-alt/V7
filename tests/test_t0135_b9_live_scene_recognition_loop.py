from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_scene_recognition_loop import build_live_scene_recognition_loop, run


def sample_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "samples" / "b9_live_scene_recognition_loop_v0"


def test_t0135_sample_loop_passes(tmp_path: Path) -> None:
    s = sample_dir()
    manifest = run(
        live_scene_json=s / "sample_b9_live_scene_query_payload.json",
        similarity_query_json=s / "sample_t0115_similarity_query_result.json",
        false_positive_json=s / "sample_t0117_false_positive_context.json",
        terrain_synthesis_json=s / "sample_t0118_human_terrain_synthesis.json",
        french_report_json=s / "sample_b9_french_trader_scene_report.json",
        output_dir=tmp_path,
        top_k=3,
    )
    assert manifest["recognition_state"] == "B9_LIVE_SCENE_RECOGNITION_READY"
    assert manifest["match_count"] == 3
    assert manifest["top_match_film_id"] == "B6FC_20260514_1903_E8F0918A"
    assert manifest["cross_family_match_count"] == 0
    assert manifest["low_trust_in_results"] is False
    assert manifest["raw_unavailable_in_results"] is False
    assert manifest["false_positive_context_available"] is True
    assert manifest["terrain_synthesis_available"] is True
    assert manifest["forbidden_language_hits"] == []
    assert (tmp_path / "B9_LIVE_SCENE_RECOGNITION_LOOP_V0.zip").exists()


def test_t0135_review_required_on_cross_family() -> None:
    packet = build_live_scene_recognition_loop(
        {
            "film_id": "LIVE_SCENE_TEST",
            "memory_family": "DIRECTIONAL_PROGRESS_MEMORY",
            "memory_family_origin": "provided",
            "source_family": "LIVE_B9_SCENE",
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
        },
        {"similar_films": [{"film_id": "OTHER", "film_date": "2026-05-01", "memory_family": "FRICTION_ABSORPTION_MEMORY", "similarity_score": 0.8}]},
        {},
        {},
        {},
        top_k=1,
    )
    assert packet["recognition_state"] == "B9_LIVE_RECOGNITION_REVIEW_REQUIRED" or packet["recognition_state"] == "B9_LIVE_SCENE_RECOGNITION_REVIEW_REQUIRED"
    assert packet["loop_checks"]["cross_family_match_count"] == 1
