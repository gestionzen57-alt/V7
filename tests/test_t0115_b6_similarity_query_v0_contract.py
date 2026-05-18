import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "build_t0115_b6_similarity_query_v0.py"
spec = importlib.util.spec_from_file_location("t0115", MODULE)
t0115 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t0115)


def film(fid, family, state="B6_KEEP_CANDIDATE", verdict="CONFIRMED_BY_RAW", raw_texture="RAW_PROGRESS_CONFIRMED", delta="1.0", rng="2.0"):
    return {
        "film_id": fid,
        "date": "2026-05-18",
        "time_start": "2026-05-18T00:00:00+00:00",
        "time_end": "2026-05-18T00:01:00+00:00",
        "session": "TEST_SESSION",
        "memory_family": family,
        "source_family": "FORCE_SNAPSHOT_DERIVED",
        "summary_recovery_type": "FORCE_SNAPSHOT_DERIVED",
        "source_mode": "M1_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
        "confidence_cap": "0.35",
        "moment_type": "TEST_MOMENT",
        "label_fr": "Film test",
        "raw_agreement": verdict,
        "proxy_vs_raw_verdict": verdict,
        "source_quality_state": "SOURCE_QUALITY_USABLE",
        "source_quality_score": "0.80",
        "b6_memory_candidate_state": state,
        "b6_memory_candidate_score": "0.90",
        "raw_texture_role": raw_texture,
        "raw_delta_pips": delta,
        "raw_range_pips": rng,
        "raw_tick_count": "100",
        "base": "Base scene progressive",
        "reaction": "Reaction raw progressive",
        "projection": "Projection utile",
        "judgment": "Judgment technique usable",
        "limits": "read-only; no BUY/SELL; no probability",
    }


def make_index():
    films = [
        film("A", "DIRECTIONAL_PROGRESS_MEMORY"),
        film("B", "DIRECTIONAL_PROGRESS_MEMORY", delta="1.2", rng="2.4"),
        film("C", "FRICTION_ABSORPTION_MEMORY", raw_texture="RAW_FRICTION_CONFIRMED"),
        film("D", "DIRECTIONAL_PROGRESS_MEMORY", state="B6_LOW_TRUST_CANDIDATE"),
        film("E", "DIRECTIONAL_PROGRESS_MEMORY", verdict="RAW_UNAVAILABLE"),
    ]
    return {"film_similarity_index": [{"query_film": f, "similar_films": []} for f in films]}


def test_query_filters_low_trust_raw_unavailable_and_cross_family():
    index = make_index()
    result = t0115.query_by_scene(index, film("Q", "DIRECTIONAL_PROGRESS_MEMORY"), top_k=10)
    ids = [m["film_id"] for m in result["similar_films"]]
    assert "B" in ids
    assert "C" not in ids
    assert "D" not in ids
    assert "E" not in ids
    assert result["integrity_checks"]["cross_family_match_count"] == 0
    assert result["integrity_checks"]["low_trust_in_results"] is False
    assert result["integrity_checks"]["raw_unavailable_in_results"] is False


def test_cli_writes_query_outputs(tmp_path):
    index_path = tmp_path / "index.json"
    index_path.write_text(json.dumps(make_index()), encoding="utf-8")
    out = tmp_path / "out"
    rc = t0115.main([
        "--similarity-index", str(index_path),
        "--scene-id", "Q",
        "--memory-family", "DIRECTIONAL_PROGRESS_MEMORY",
        "--base", "Base scene progressive",
        "--reaction", "Reaction raw progressive",
        "--projection", "Projection utile",
        "--judgment", "Judgment technique usable",
        "--raw-delta-pips", "1.1",
        "--raw-range-pips", "2.1",
        "--raw-tick-count", "120",
        "--source-quality-score", "0.8",
        "--confidence-cap", "0.35",
        "--b6-memory-candidate-score", "0.9",
        "--output-dir", str(out),
        "--top-k", "3",
    ])
    assert rc == 0
    assert (out / "B6_SIMILARITY_QUERY_RESULT_V0.json").exists()
    assert (out / "B6_SIMILARITY_QUERY_RESULT_V0.md").exists()
    assert (out / "B6_SIMILARITY_QUERY_RESULT_V0.csv").exists()
    assert (out / "B6_SIMILARITY_QUERY_RESULT_V0.zip").exists()
