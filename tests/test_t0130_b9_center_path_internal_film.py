from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "build_t0130_b9_center_path_internal_film.py"
spec = importlib.util.spec_from_file_location("build_t0130", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def test_t0130_sample_center_path_pass(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_center_path_internal_film_v0" / "sample_t009_sequence_summary_center_path.json"
    manifest = mod.run(sample, tmp_path)
    assert manifest["moments"] == 5
    assert manifest["total_missing_required_fields"] == 0
    assert manifest["forbidden_language_hit_count"] == 0
    assert manifest["preserved_field_changes"] == 0
    assert manifest["shape_counts"].get("CENTER_PATH_NOT_VISIBLE", 0) == 0
    assert (tmp_path / "B9_CENTER_PATH_INTERNAL_FILM_V0.zip").exists()


def test_t0130_has_core_shapes(tmp_path: Path) -> None:
    sample = ROOT / "samples" / "b9_center_path_internal_film_v0" / "sample_t009_sequence_summary_center_path.json"
    manifest = mod.run(sample, tmp_path)
    shapes = manifest["shape_counts"]
    assert any(k.startswith("STRAIGHT_PROGRESS_UP") or k.startswith("STAIR_STEP_PROGRESS_UP") for k in shapes)
    assert any(k.startswith("STRAIGHT_PROGRESS_DOWN") or k.startswith("STAIR_STEP_PROGRESS_DOWN") for k in shapes)
    assert "SPIKE_AND_RETRACE" in shapes or "ROUND_TRIP_NO_PROGRESS" in shapes
