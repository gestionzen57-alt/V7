from pathlib import Path
import importlib.util
import sys

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_t0126_b9_runtime_replay_pack_collector.py"
spec = importlib.util.spec_from_file_location("t0126", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def test_t0126_collector_keeps_real_candidate_and_excludes_validation(tmp_path: Path) -> None:
    scan_root = Path(__file__).resolve().parents[1] / "samples" / "b9_runtime_replay_pack_collector_v0"
    manifest = mod.run(scan_root, tmp_path)
    assert manifest["files_discovered"] == 1
    assert manifest["candidates_keep"] == 1
    assert manifest["candidates_rejected"] == 0
    assert manifest["read_only"] is True
    assert manifest["db_write"] is False
    assert manifest["buy_sell"] is False
    assert (tmp_path / "B9_RUNTIME_REPLAY_PACK_INDEX_V0.csv").exists()
    assert (tmp_path / "B9_RUNTIME_REPLAY_PACK_COLLECTOR_V0.zip").exists()


def test_t0126_no_forbidden_language_in_sample(tmp_path: Path) -> None:
    scan_root = Path(__file__).resolve().parents[1] / "samples" / "b9_runtime_replay_pack_collector_v0"
    manifest = mod.run(scan_root, tmp_path)
    assert manifest["forbidden_language_files"] == 0
    assert manifest["files_with_v4_fields"] == 1
    assert manifest["files_with_source_quality"] == 1
    assert manifest["files_with_timestamp_policy"] == 1
