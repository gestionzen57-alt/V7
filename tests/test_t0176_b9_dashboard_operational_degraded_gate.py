from __future__ import annotations

import csv
import json
from pathlib import Path

from pf_t0176_b9_dashboard_operational_degraded_gate import VERSION, build_operational_gate


def write_contract(root: Path, state: str = "LOCK_BLOCKED_MISSING_REQUIRED", req: int = 2):
    out = root / "outputs" / "t0175_b9_global_chain_contract_lock_v0"
    out.mkdir(parents=True, exist_ok=True)
    (out / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json").write_text(json.dumps({
        "lock_state": state,
        "required_missing_count": req,
        "optional_missing_count": 1,
        "source_error_count": 0,
        "forbidden_language_hit_count": 0,
    }), encoding="utf-8")
    with (out / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["step_id", "required", "status", "expected_path", "regeneration_command"])
        writer.writeheader()
        writer.writerow({"step_id": "T0148_LIVE_BRIEF_ONCE", "required": "true", "status": "MISSING", "expected_path": "outputs/x.json", "regeneration_command": "python x.py"})


def test_degraded_ready_when_required_missing(tmp_path: Path):
    write_contract(tmp_path)
    payload = build_operational_gate(core_root=tmp_path, output_dir=tmp_path / "out")
    assert payload["version"] == VERSION
    assert payload["surface_state"] == "DASHBOARD_OPERATIONAL_DEGRADED_READY"
    assert payload["required_missing_count"] == 2
    assert payload["surface_cards"]
    assert payload["db_write"] is False
    assert payload["telegram_send"] is False


def test_ready_when_t0175_ready(tmp_path: Path):
    write_contract(tmp_path, state="LOCK_READY_FOR_DASHBOARD_REVIEW", req=0)
    payload = build_operational_gate(core_root=tmp_path, output_dir=tmp_path / "out")
    assert payload["surface_state"] == "DASHBOARD_OPERATIONAL_READY"


def test_hard_block_on_source_error(tmp_path: Path):
    out = tmp_path / "outputs" / "t0175_b9_global_chain_contract_lock_v0"
    out.mkdir(parents=True, exist_ok=True)
    (out / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json").write_text(json.dumps({
        "lock_state": "LOCK_BLOCKED_SOURCE_ERROR",
        "required_missing_count": 0,
        "optional_missing_count": 0,
        "source_error_count": 1,
        "forbidden_language_hit_count": 0,
    }), encoding="utf-8")
    payload = build_operational_gate(core_root=tmp_path, output_dir=tmp_path / "out")
    assert payload["surface_state"] == "DASHBOARD_OPERATIONAL_BLOCKED_HARD_CONTRACT_ERROR"
    assert "SOURCE_ERROR_PRESENT" in payload["hard_block_reasons"]
