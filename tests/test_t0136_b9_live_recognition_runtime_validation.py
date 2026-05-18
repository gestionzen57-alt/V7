from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_t0136_b9_live_recognition_runtime_validation.py"
spec = importlib.util.spec_from_file_location("t0136", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_t0136_sample_contract_passes(tmp_path: Path) -> None:
    sample_dir = Path(__file__).resolve().parents[1] / "samples" / "b9_live_recognition_runtime_validation_v0"
    manifest = mod.validate(
        mode="sample",
        core_root=Path(__file__).resolve().parents[1],
        sample_dir=sample_dir,
        output_dir=tmp_path,
        top_k=3,
        execute_t0135=False,
    )
    assert manifest["runtime_validation_state"] == "PASS_SAMPLE_CONTRACT"
    assert manifest["required_inputs_found"] == manifest["required_inputs_total"]
    assert manifest["match_count"] == 3
    assert manifest["cross_family_match_count"] == 0
    assert manifest["low_trust_in_results"] is False
    assert manifest["raw_unavailable_in_results"] is False
    assert manifest["forbidden_language_hit_count"] == 0


def test_t0136_runtime_missing_inputs_is_blocked_not_failure(tmp_path: Path) -> None:
    empty_core = tmp_path / "empty_core"
    empty_core.mkdir()
    manifest = mod.validate(
        mode="runtime",
        core_root=empty_core,
        sample_dir=empty_core,
        output_dir=tmp_path / "out",
        top_k=3,
        execute_t0135=True,
    )
    assert manifest["runtime_validation_state"] == "BLOCKED_MISSING_RUNTIME_INPUTS"
    assert manifest["required_inputs_found"] == 0
    assert manifest["t0135_executed"] is False
