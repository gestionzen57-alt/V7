import json
import importlib.util
import sys
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "build_t0175_b9_global_chain_contract_lock.py"
spec = importlib.util.spec_from_file_location("t0175", MODULE_PATH)
t0175 = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = t0175
spec.loader.exec_module(t0175)


def write_json(root: Path, rel: str, data: dict):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def populate_required(root: Path):
    for item in t0175.REQUIRED_FILES:
        rel = item["path"]
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if rel.endswith(".json"):
            path.write_text(json.dumps({"source_quality": "TEST_OK", "gate_state": "OK"}), encoding="utf-8")
        else:
            path.write_text("# dummy builder\n", encoding="utf-8")
    write_json(root, "outputs/t0169_surface_adapter_candidate_v0/B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json", {"source_quality": "TEST_OK"})


def test_lock_ready_when_required_present(tmp_path):
    populate_required(tmp_path)
    contract = t0175.build_contract(tmp_path)
    assert contract["lock_state"] in {"LOCK_READY_FOR_DASHBOARD_REVIEW", "LOCK_PARTIAL_OPTIONAL_MISSING"}
    assert contract["required_missing_count"] == 0
    assert contract["db_touched"] is False
    assert contract["dashboard_live_wired"] is False


def test_missing_required_blocks(tmp_path):
    contract = t0175.build_contract(tmp_path)
    assert contract["lock_state"] == "LOCK_BLOCKED_MISSING_REQUIRED"
    assert contract["required_missing_count"] > 0


def test_forbidden_language_blocks(tmp_path):
    populate_required(tmp_path)
    target = tmp_path / t0175.REQUIRED_FILES[0]["path"]
    target.write_text(json.dumps({"source_quality": "OK", "text": "BUY now"}), encoding="utf-8")
    contract = t0175.build_contract(tmp_path)
    assert contract["lock_state"] == "LOCK_BLOCKED_FORBIDDEN_LANGUAGE"
    assert contract["forbidden_language_hit_count"] >= 1


def test_outputs_written(tmp_path):
    populate_required(tmp_path)
    contract = t0175.build_contract(tmp_path)
    out = tmp_path / "out"
    artifacts = t0175.write_outputs(contract, out)
    assert Path(artifacts["contract_json"]).exists()
    assert Path(artifacts["contract_md"]).exists()
    assert Path(artifacts["source_csv"]).exists()


def test_json_source_error_blocks(tmp_path):
    populate_required(tmp_path)
    bad = tmp_path / t0175.REQUIRED_FILES[0]["path"]
    bad.write_text("{broken json", encoding="utf-8")
    contract = t0175.build_contract(tmp_path)
    assert contract["lock_state"] == "LOCK_BLOCKED_SOURCE_ERROR"
    assert contract["source_error_count"] >= 1
