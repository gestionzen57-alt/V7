from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_t0128_b9_native_retest_source_fields.py"
spec = importlib.util.spec_from_file_location("t0128_builder", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_t0128_sample_native_retest_fields_pass(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_native_retest_source_fields_v0" / "sample_t009_sequence_summary_retest_candidate.json"
    manifest = mod.run(sample, tmp_path)
    assert manifest["moments"] == 5
    assert manifest["retest_visible_count"] >= 4
    assert manifest["missing_required_field_counts"] == {}
    assert manifest["forbidden_language_hits"] == []
    assert manifest["retest_result_counts"]["RETEST_FAILED"] >= 1
    assert manifest["retest_result_counts"]["RETEST_ACCEPTED"] >= 1
    assert manifest["retest_result_counts"]["FAILED_REINTEGRATION"] >= 1


def test_t0128_outputs_created(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_native_retest_source_fields_v0" / "sample_t009_sequence_summary_retest_candidate.json"
    manifest = mod.run(sample, tmp_path)
    expected = [
        "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.md",
        "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.json",
        "B9_NATIVE_RETEST_SOURCE_FIELDS_ROWS_V0.csv",
        "B9_NATIVE_RETEST_SOURCE_FIELDS_COUNTS_V0.csv",
        "B9_NATIVE_RETEST_SOURCE_FIELDS_ENRICHED_SUMMARY_V0.json",
        "B9_NATIVE_RETEST_SOURCE_FIELDS_MANIFEST.json",
        "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.zip",
    ]
    for name in expected:
        assert (tmp_path / name).exists(), name
    assert manifest["read_only"] is True
    assert manifest["db_write"] is False
