from pathlib import Path
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "build_t0177_b9_dashboard_reality_board_relock.py"


def run_cli(tmp_path, *extra):
    core = tmp_path / "core"
    (core / "tools").mkdir(parents=True)
    out = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "--core-root", str(core), "--output-dir", str(out), "--print-json", *extra]
    return subprocess.run(cmd, text=True, capture_output=True, check=True), out


def test_dry_run_missing_builders_blocks(tmp_path):
    proc, out = run_cli(tmp_path)
    data = json.loads(proc.stdout)
    assert data["dashboard_state"] == "DASHBOARD_RELOCK_BLOCKED_REQUIRED_BUILDER_OR_COMMAND"
    assert data["counts"]["required_missing_builders"] >= 1
    assert (out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_V0.json").exists()


def test_detects_builder_in_dry_run(tmp_path):
    core = tmp_path / "core"
    tools = core / "tools"
    tools.mkdir(parents=True)
    builder = tools / "build_t0175_b9_global_chain_contract_lock.py"
    builder.write_text("print('dummy')\n", encoding="utf-8")
    out = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "--core-root", str(core), "--output-dir", str(out), "--print-json"]
    subprocess.run(cmd, text=True, capture_output=True, check=True)
    payload = json.loads((out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_V0.json").read_text(encoding="utf-8"))
    t0175 = [t for t in payload["targets"] if t["id"] == "T0175"][0]
    assert t0175["builder_path"].endswith("build_t0175_b9_global_chain_contract_lock.py")
    assert t0175["state"] == "DRY_RUN_READY"


def test_forbidden_language_scan(tmp_path):
    core = tmp_path / "core"
    (core / "tools").mkdir(parents=True)
    target_out = core / "outputs" / "t0175_b9_global_chain_contract_lock_v0"
    target_out.mkdir(parents=True)
    (target_out / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json").write_text('{"x":"BUY"}', encoding="utf-8")
    out = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "--core-root", str(core), "--output-dir", str(out), "--print-json"]
    subprocess.run(cmd, text=True, capture_output=True, check=True)
    payload = json.loads((out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_V0.json").read_text(encoding="utf-8"))
    assert payload["counts"]["forbidden_language_hits"] >= 1


def test_outputs_csv_and_md(tmp_path):
    _, out = run_cli(tmp_path)
    assert (out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_V0.md").exists()
    assert (out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_MISSING_INPUTS_V0.csv").exists()
    assert (out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_REGEN_COMMANDS_V0.csv").exists()
    assert (out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_MANIFEST_V0.json").exists()


def test_no_db_artifacts_declared(tmp_path):
    _, out = run_cli(tmp_path)
    payload = json.loads((out / "B9_DASHBOARD_REALITY_BOARD_RELOCK_V0.json").read_text(encoding="utf-8"))
    constraints = " ".join(payload["constraints"])
    assert "powerflow.db" in constraints
    assert "tick_archive.db" in constraints
