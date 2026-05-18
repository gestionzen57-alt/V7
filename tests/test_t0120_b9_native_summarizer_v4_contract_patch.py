from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4, summarize_contract_coverage


def _load_sample():
    path = ROOT / "samples" / "b9_native_summarizer_v4_contract_patch_v0" / "sample_t009_sequence_summary_raw_calibrated.json"
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def test_t0120_enriches_all_moments_with_required_fields():
    enriched = enrich_sequence_summary_v4(_load_sample())
    moments = enriched["moments"]
    assert moments
    required = [
        "what_happens_fr",
        "why_it_matters_fr",
        "how_it_happened_fr",
        "mechanism_fr",
        "proof_summary_fr",
        "previous_context_fr",
        "cause_fr",
        "reaction_fr",
        "consequence_fr",
        "memory_shift_fr",
        "retest_role_fr",
        "scene_id",
        "scene_role",
        "parent_scene",
        "child_moments",
        "session_chapter",
        "fractal_reading_fr",
        "b9_center_path_state",
        "b9_effort_result_progress_state",
        "b9_native_retest_judgment",
        "b9_source_quality_native_state",
    ]
    for moment in moments:
        for field in required:
            assert field in moment
            assert moment[field] not in (None, "")
    coverage = summarize_contract_coverage(enriched)
    assert coverage["missing_required_field_counts"] == {}


def test_t0120_preserves_policy_and_no_forbidden_language():
    enriched = enrich_sequence_summary_v4(_load_sample())
    coverage = summarize_contract_coverage(enriched)
    assert coverage["forbidden_language_hits"] == []
    assert enriched["metadata"]["b9_v4_contract_policy"] == "READ_ONLY_NATIVE_CONTRACT_ENRICHMENT_NO_DECISION"
    assert all(m["b9_v4_forbidden_language_policy"] == "NO_BUY_SELL_NO_PROBABILITY_OF_SUCCESS" for m in enriched["moments"])
    assert any(m["b9_native_retest_judgment"] == "RETEST_JUDGMENT_NOT_VISIBLE_NATIVE_FIELD_REQUIRED" for m in enriched["moments"])
