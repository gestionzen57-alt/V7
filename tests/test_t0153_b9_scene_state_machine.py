
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

from build_t0153_b9_scene_state_machine import run

class Args:
    sequence_summary_json = str(ROOT / "samples" / "b9_scene_state_machine_v0" / "sample_t009_sequence_summary_scene_state.json")
    output_dir = str(ROOT / "outputs" / "b9_scene_state_machine_v0_test")


def test_t0153_scene_state_machine_sample_contract():
    result = run(Args())
    assert result["moments"] == 8
    assert result["missing_required_field_counts"] == {}
    assert result["forbidden_language_hits"] == []
    assert result["raw_unavailable_allowed_count"] == 0
    assert result["state_counts"].get("SCENE_TESTING", 0) >= 1
    assert result["state_counts"].get("SCENE_ACCEPTED", 0) >= 1
    assert result["state_counts"].get("SCENE_REJECTED", 0) >= 1
    assert result["state_counts"].get("SCENE_MEMORY_SHIFTED", 0) >= 1
    assert result["state_counts"].get("SCENE_BLOCKED_RAW_UNAVAILABLE", 0) == 1


def test_t0153_outputs_exist():
    result = run(Args())
    out = Path(Args.output_dir)
    assert (out / "B9_SCENE_STATE_MACHINE_V0.md").exists()
    assert (out / "B9_SCENE_STATE_MACHINE_ROWS_V0.csv").exists()
    assert Path(result["zip"]).exists()
