from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_effort_result_progress_scorer import (  # noqa: E402
    REQUIRED_FIELDS,
    enrich_sequence_summary_effort_result_progress,
    find_forbidden_language,
    missing_required_field_counts,
    preservation_diff,
)

spec = importlib.util.spec_from_file_location(
    "build_t0129", ROOT / "tools" / "build_t0129_b9_effort_result_progress_scorer.py"
)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_t0129_enriches_all_required_fields() -> None:
    sample = mod.load_json(ROOT / "samples" / "b9_effort_result_progress_scorer_v0" / "sample_t009_sequence_summary_effort_result_progress.json")
    enriched = enrich_sequence_summary_effort_result_progress(sample)
    assert len(enriched["moments"]) == 5
    assert missing_required_field_counts(enriched) == {}
    assert find_forbidden_language(enriched) == []
    assert preservation_diff(sample, enriched) == []
    states = {m["b9_effort_result_progress_state"] for m in enriched["moments"]}
    assert "ABSORPTION_WITHOUT_PROGRESS" in states or "EFFORT_WITHOUT_RESULT" in states
    assert "PROGRESSIVE_WAVE" in states or "ABSORPTION_WITH_PROGRESS" in states
    for moment in enriched["moments"]:
        for field in REQUIRED_FIELDS:
            assert field in moment


def test_t0129_cli_outputs_pass(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_effort_result_progress_scorer_v0" / "sample_t009_sequence_summary_effort_result_progress.json"
    manifest = mod.run(sample, tmp_path)
    assert manifest["moments"] == 5
    assert manifest["total_missing_required_fields"] == 0
    assert manifest["forbidden_language_hit_count"] == 0
    assert manifest["preserved_field_change_count"] == 0
    assert (tmp_path / "B9_EFFORT_RESULT_PROGRESS_V0.zip").exists()
