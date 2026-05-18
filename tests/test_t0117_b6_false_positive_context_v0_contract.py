from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def test_t0117_builds_false_positive_context(tmp_path: Path) -> None:
    script = Path("tools/build_t0117_b6_false_positive_context_v0.py")
    sample = Path("samples/b6_false_positive_context_v0/sample_t0115_similarity_query_result_v0.json")
    out = tmp_path / "out"
    result = subprocess.run(
        [sys.executable, str(script), "--query-result-json", str(sample), "--output-dir", str(out), "--top-k", "5"],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(result.stdout)
    assert summary["version"] == "T0117_B6_FALSE_POSITIVE_CONTEXT_V0"
    assert summary["matches_reviewed"] == 5
    assert summary["cross_family_match_count"] == 0
    assert summary["low_trust_in_results"] is False
    assert summary["raw_unavailable_in_results"] is False

    payload = json.loads((out / "B6_FALSE_POSITIVE_CONTEXT_V0.json").read_text(encoding="utf-8"))
    assert payload["policy"] == "SIMILARITY_IS_NOT_REPETITION_FALSE_POSITIVE_CONTEXT_V0"
    assert len(payload["false_positive_contexts"]) == 5
    for rec in payload["false_positive_contexts"]:
        assert "false_positive_context_state" in rec
        assert rec["false_positive_context_score"] >= 0
        assert "probabilite de succes" not in rec["safe_comparison_reading_fr"].lower()


def test_t0117_flags_live_inferred_family(tmp_path: Path) -> None:
    script = Path("tools/build_t0117_b6_false_positive_context_v0.py")
    sample = json.loads(Path("samples/b6_false_positive_context_v0/sample_t0115_similarity_query_result_v0.json").read_text(encoding="utf-8"))
    sample["query_scene"]["memory_family_origin"] = "heuristic_text_directional_progress"
    live_sample = tmp_path / "live_query_result.json"
    live_sample.write_text(json.dumps(sample, ensure_ascii=False), encoding="utf-8")
    out = tmp_path / "out"
    subprocess.run(
        [sys.executable, str(script), "--query-result-json", str(live_sample), "--output-dir", str(out), "--top-k", "1"],
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads((out / "B6_FALSE_POSITIVE_CONTEXT_V0.json").read_text(encoding="utf-8"))
    flags = payload["false_positive_contexts"][0]["risk_flags"]
    assert "MEMORY_FAMILY_INFERRED" in flags
