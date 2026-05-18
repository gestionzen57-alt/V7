from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_t0125_b9_v4_golden_replay_batch_runner.py"
spec = importlib.util.spec_from_file_location("t0125", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_t0125_sample_batch_passes(tmp_path: Path) -> None:
    sample_dir = ROOT / "samples" / "b9_v4_golden_replay_batch_runner_v0"
    manifest = mod.run(sample_dir, tmp_path)
    assert manifest["batch_state"] == "PASS"
    assert manifest["files_processed"] >= 3
    assert manifest["files_failed"] == 0
    assert manifest["total_missing_required_fields"] == 0
    assert manifest["total_forbidden_language_hits"] == 0
    assert Path(manifest["zip"]).exists()


def test_t0125_forbidden_terms_detected() -> None:
    hits = mod.find_forbidden({"text": "BUY"})
    assert "BUY" in hits
