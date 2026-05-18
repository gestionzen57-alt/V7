import json
from pathlib import Path

from tools.build_t0178_b9_relock_after_runtime_regen import (
    decide_verdict,
    extract_last_json_object,
    infer_regen_command,
    build_relock,
)


def test_extract_last_json_object_from_mixed_stdout():
    text = "hello\n{\"old\": true}\nnoise\n{\"lock_state\": \"LOCK_READY_FOR_DASHBOARD_REVIEW\"}\n"
    parsed = extract_last_json_object(text)
    assert parsed["lock_state"] == "LOCK_READY_FOR_DASHBOARD_REVIEW"


def test_decide_verdict_ready():
    verdict = decide_verdict("LOCK_READY_FOR_DASHBOARD_REVIEW", "MISSING", 0, 0, 0)
    assert verdict.final_state == "READY"
    assert verdict.can_display_b9_now is True
    assert verdict.display_mode == "FULL_CONTRACT_REVIEW"


def test_decide_verdict_degraded_ready_from_t0176():
    verdict = decide_verdict("LOCK_BLOCKED_MISSING_REQUIRED", "DEGRADED_REQUIRED_INPUTS_MISSING", 7, 0, 0)
    assert verdict.final_state == "DEGRADED_READY"
    assert verdict.can_display_b9_now is True
    assert verdict.display_mode == "OPERATIONAL_DEGRADED"


def test_decide_verdict_forbidden_blocks():
    verdict = decide_verdict("LOCK_READY_FOR_DASHBOARD_REVIEW", "READY_FULL_CHAIN_VIEW", 0, 1, 0)
    assert verdict.final_state == "BLOCKED_FORBIDDEN_LANGUAGE"
    assert verdict.can_display_b9_now is False


def test_infer_regen_command_mentions_t0169():
    cmd = infer_regen_command({"path": "outputs/b9_reality_board_surface_adapter_candidate_v0/B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json"})
    assert "build_t0169" in cmd


def test_build_relock_dry_run_with_existing_jsons(tmp_path: Path):
    core = tmp_path
    (core / "outputs/t0175_b9_global_chain_contract_lock_v0").mkdir(parents=True)
    (core / "outputs/t0176_b9_chain_degraded_dashboard_candidate_v0").mkdir(parents=True)
    (core / "Docs/Reports").mkdir(parents=True)
    (core / "outputs/t0175_b9_global_chain_contract_lock_v0/B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json").write_text(
        json.dumps({"lock_state": "LOCK_BLOCKED_MISSING_REQUIRED", "required_missing_count": 2, "optional_missing_count": 1}),
        encoding="utf-8",
    )
    (core / "outputs/t0176_b9_chain_degraded_dashboard_candidate_v0/B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.json").write_text(
        json.dumps({"dashboard_state": "DEGRADED_REQUIRED_INPUTS_MISSING"}),
        encoding="utf-8",
    )
    summary = build_relock(core, Path("outputs/t0178_test"), execute=False)
    assert summary["final_state"] == "DEGRADED_READY"
    assert summary["can_display_b9_now"] is True
    assert Path(summary["artifacts"]["summary_json"]).exists()
    assert Path(summary["artifacts"]["docs_report_md"]).exists()
