from pathlib import Path

from pf_t009_live_chain_orchestrator_dry_run import run

SAMPLE = Path("samples/b9_live_chain_orchestrator_dry_run_v0")

def overrides():
    return {
        "freshness_guard": str(SAMPLE / "sample_freshness_guard.json"),
        "latest_scene_candidate": str(SAMPLE / "sample_latest_scene_candidate.json"),
        "candidate_queue": str(SAMPLE / "sample_candidate_queue.json"),
        "auto_realignment": str(SAMPLE / "sample_auto_realignment.json"),
        "live_brief_once": str(SAMPLE / "sample_live_brief_once.json"),
        "attention_packet": str(SAMPLE / "sample_attention_packet.json"),
        "reality_board_payload": str(SAMPLE / "sample_reality_board_payload.json"),
        "surface_adapter": str(SAMPLE / "sample_surface_adapter.json"),
        "telegram_gate": str(SAMPLE / "sample_telegram_gate.json"),
        "telegram_manual_approval": str(SAMPLE / "sample_manual_approval.json"),
        "french_display_contract": str(SAMPLE / "sample_display_contract.json"),
    }


def test_t0171_sample_review_chain(tmp_path):
    summary = run(Path("."), tmp_path, overrides())
    assert summary["orchestrator_state"] == "B9_LIVE_CHAIN_DRY_RUN_REVIEW_TECHNICAL_RISK"
    assert summary["candidate_id"] == "B9LSC_E49A7AEC65CE"
    assert summary["match_count"] == 3
    assert summary["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert summary["forbidden_language_hits"] == []


def test_t0171_missing_critical_input_blocks(tmp_path):
    ov = overrides()
    del ov["live_brief_once"]
    summary = run(Path("."), tmp_path, ov)
    assert summary["orchestrator_state"] == "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS"
    assert "live_brief_once" in summary["missing_steps"]


def test_t0171_outputs_written(tmp_path):
    summary = run(Path("."), tmp_path, overrides())
    assert (tmp_path / "B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0.json").exists()
    assert (tmp_path / "B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0.md").exists()
    assert (tmp_path / "B9_LIVE_CHAIN_STEPS_V0.csv").exists()
    assert Path(summary["zip"]).exists()
