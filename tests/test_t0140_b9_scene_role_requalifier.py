from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / 'tools' / 'build_t0140_b9_scene_role_requalifier.py'
spec = importlib.util.spec_from_file_location('t0140_builder', MOD_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_t0140_sample_scene_roles(tmp_path: Path):
    sample = ROOT / 'samples' / 'b9_scene_role_requalifier_v0' / 'sample_t009_sequence_summary_scene_roles.json'
    manifest = mod.run(sample, tmp_path)
    assert manifest['moments'] == 7
    assert manifest['missing_required_field_counts'] == {}
    assert manifest['forbidden_language_hit_count'] == 0
    assert manifest['role_counts']['EFFORT_WITHOUT_RESULT_FRICTION'] == 1
    assert manifest['role_counts']['RETEST_FAILED_REJECTION_NODE'] == 1
    assert manifest['role_counts']['PROGRESSIVE_FIRST_LEG'] >= 1
    assert manifest['role_counts']['CENTER_MIGRATION_DOWN_MEMORY_SHIFT'] == 1
    assert manifest['state_counts']['B9_SCENE_ROLE_REJECT_RAW_UNAVAILABLE'] == 1


def test_t0140_outputs_exist(tmp_path: Path):
    sample = ROOT / 'samples' / 'b9_scene_role_requalifier_v0' / 'sample_t009_sequence_summary_scene_roles.json'
    mod.run(sample, tmp_path)
    assert (tmp_path / 'B9_SCENE_ROLE_REQUALIFIER_V0.md').exists()
    assert (tmp_path / 'B9_SCENE_ROLE_REQUALIFIER_ROWS_V0.csv').exists()
    assert (tmp_path / 'B9_SCENE_ROLE_REQUALIFIER_V0.zip').exists()
