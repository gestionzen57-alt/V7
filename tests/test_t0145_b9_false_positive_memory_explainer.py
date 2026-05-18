from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_false_positive_memory_explainer import explain_summary
from tools.build_t0145_b9_false_positive_memory_explainer import read_json, run


class Args:
    sequence_summary_json = str(ROOT / "samples" / "b9_false_positive_memory_explainer_v0" / "sample_t009_sequence_summary_false_positive_memory.json")
    output_dir = str(ROOT / "outputs" / "b9_false_positive_memory_explainer_v0_test")


def test_t0145_false_positive_states_contract():
    data = read_json(Path(Args.sequence_summary_json))
    summary = explain_summary(data)
    assert summary["moments"] == 4
    assert summary["state_counts"].get("MEMORY_FP_LOW", 0) == 1
    assert summary["state_counts"].get("MEMORY_FP_HIGH", 0) >= 1
    assert summary["state_counts"].get("MEMORY_FP_REJECT_RAW_UNAVAILABLE", 0) == 1
    assert summary["raw_unavailable_allowed_count"] == 0
    assert summary["forbidden_language_hits"] == []
    rows = summary["rows"]
    assert any("SESSION_MISMATCH" in r["b9_memory_false_positive_flags"] for r in rows)
    assert any("RETEST_NOT_VISIBLE" in r["b9_memory_false_positive_flags"] for r in rows)


def test_t0145_cli_outputs(tmp_path):
    args = Args()
    args.output_dir = str(tmp_path)
    result = run(args)
    assert result["moments"] == 4
    assert result["raw_unavailable_allowed_count"] == 0
    assert Path(result["zip"]).exists()
    assert (tmp_path / "B9_FALSE_POSITIVE_MEMORY_ROWS_V0.csv").exists()
    assert (tmp_path / "B9_FALSE_POSITIVE_MEMORY_ENRICHED_SUMMARY_V0.json").exists()
