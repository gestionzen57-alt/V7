from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_t0146_b9_memory_confidence_ladder import main


def test_t0146_memory_confidence_ladder_states(tmp_path):
    sample = ROOT / "samples" / "b9_memory_confidence_ladder_v0" / "sample_t009_sequence_summary_memory_confidence.json"
    summary = main(["--sequence-summary-json", str(sample), "--output-dir", str(tmp_path)])
    counts = summary["state_counts"]
    assert summary["moments"] == 6
    assert counts["MEMORY_STRONG_COMPARABLE"] == 1
    assert counts["MEMORY_SOURCE_LIMITED"] == 1
    assert counts["MEMORY_SESSION_MISMATCH"] == 1
    assert counts["MEMORY_RETEST_MISSING"] == 1
    assert counts["MEMORY_PARTIAL_COMPARABLE"] == 1
    assert counts["MEMORY_REJECTED_RAW_UNAVAILABLE"] == 1
    assert summary["missing_required_field_counts"] == {}
    assert summary["forbidden_language_hits"] == []
    assert summary["raw_unavailable_allowed_count"] == 0


def test_t0146_outputs_exist(tmp_path):
    sample = ROOT / "samples" / "b9_memory_confidence_ladder_v0" / "sample_t009_sequence_summary_memory_confidence.json"
    main(["--sequence-summary-json", str(sample), "--output-dir", str(tmp_path)])
    assert (tmp_path / "B9_MEMORY_CONFIDENCE_LADDER_V0.md").exists()
    assert (tmp_path / "B9_MEMORY_CONFIDENCE_LADDER_ROWS_V0.csv").exists()
    assert (tmp_path / "B9_MEMORY_CONFIDENCE_LADDER_ENRICHED_SUMMARY_V0.json").exists()
    data = json.loads((tmp_path / "B9_MEMORY_CONFIDENCE_LADDER_ENRICHED_SUMMARY_V0.json").read_text(encoding="utf-8"))
    moments = data["moments"]
    assert all("b9_memory_comparability_state" in m for m in moments)
