from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "build_t0127_b9_timestamp_remap_guard_v0.py"
spec = importlib.util.spec_from_file_location("t0127", MOD_PATH)
mod = importlib.util.module_from_spec(spec)
sys.modules["t0127"] = mod
spec.loader.exec_module(mod)  # type: ignore[union-attr]


def test_t0127_detects_shift_and_remaps(tmp_path: Path) -> None:
    summary = ROOT / "samples" / "b9_timestamp_remap_guard_v0" / "sample_t009_sequence_summary_shifted.json"
    replay = ROOT / "samples" / "b9_timestamp_remap_guard_v0" / "sample_t009_replay_sequence_report.json"
    manifest = mod.run(summary, tmp_path, replay)
    assert manifest["timestamp_guard_state"] == "PASS_WITH_SHIFT_DETECTED"
    assert manifest["moments_checked"] == 3
    assert manifest["shifted_moment_count"] == 3
    assert manifest["policy_counts"]["TIMESTAMP_SHIFT_DETECTED"] == 3
    assert manifest["missing_required_field_counts"] == {}
    assert manifest["forbidden_language_hits"] == []


def test_t0127_no_buy_sell_or_db_write(tmp_path: Path) -> None:
    summary = ROOT / "samples" / "b9_timestamp_remap_guard_v0" / "sample_t009_sequence_summary_shifted.json"
    replay = ROOT / "samples" / "b9_timestamp_remap_guard_v0" / "sample_t009_replay_sequence_report.json"
    manifest = mod.run(summary, tmp_path, replay)
    assert manifest["read_only"] is True
    assert manifest["db_write"] is False
    assert manifest["dashboard"] is False
    assert manifest["telegram"] is False
    assert manifest["buy_sell"] is False
    assert manifest["probability_of_success"] is False
