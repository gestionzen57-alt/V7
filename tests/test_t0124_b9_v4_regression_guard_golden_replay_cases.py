from __future__ import annotations

import importlib.util
import json
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_t0124_b9_v4_regression_guard_golden_replay_cases.py"
spec = importlib.util.spec_from_file_location("t0124_guard", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_t0124_sample_golden_cases_pass(tmp_path: Path) -> None:
    sample = Path(__file__).resolve().parents[1] / "samples" / "b9_v4_regression_guard_golden_replay_cases_v0" / "sample_b9_v4_golden_replay_cases_input.json"
    manifest = mod.run(sample, tmp_path)
    assert manifest["regression_guard_state"] == "PASS"
    assert manifest["golden_case_count"] == 6
    assert manifest["golden_cases_passed"] == 6
    assert manifest["golden_cases_failed"] == 0
    assert manifest["total_missing_required_fields"] == 0
    assert manifest["forbidden_language_hit_count"] == 0
    assert (tmp_path / "B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES_V0.zip").exists()


def test_t0124_detects_regression(tmp_path: Path) -> None:
    sample_data = json.loads(json.dumps(mod.SAMPLE_SUMMARY))
    sample_data["moments"][1]["b9_progress_type"] = "EFFORT_WITHOUT_RESULT"
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps(sample_data), encoding="utf-8")
    manifest = mod.run(broken, tmp_path / "out")
    assert manifest["regression_guard_state"] == "FAIL"
    assert manifest["golden_cases_failed"] >= 1
