from pathlib import Path
import json

from pf_t009_reality_board_surface_adapter_candidate import build_surface_adapter, run


def test_surface_adapter_ready_or_partial():
    read_model = json.loads(Path("samples/b9_reality_board_surface_adapter_candidate_v0/sample_read_model.json").read_text(encoding="utf-8"))
    panel = json.loads(Path("samples/b9_reality_board_surface_adapter_candidate_v0/sample_panel.json").read_text(encoding="utf-8"))
    payload = json.loads(Path("samples/b9_reality_board_surface_adapter_candidate_v0/sample_payload.json").read_text(encoding="utf-8"))
    display = json.loads(Path("samples/b9_reality_board_surface_adapter_candidate_v0/sample_display_contract.json").read_text(encoding="utf-8"))
    surface = build_surface_adapter(read_model, panel, payload, display)
    assert surface["surface_state"] in {"B9_SURFACE_ADAPTER_CANDIDATE_READY", "B9_SURFACE_ADAPTER_CANDIDATE_PARTIAL_INPUTS"}
    assert surface["candidate_id"] == "B9LSC_E49A7AEC65CE"
    assert surface["summary"]["match_count"] == 3
    assert surface["summary"]["top_match_film_id"] == "B6FC_20260511_1641_010496DB"
    assert surface["forbidden_language_hits"] == []
    assert surface["no_decision_guard"] is True


def test_surface_adapter_blocks_missing_inputs_only_when_all_missing():
    surface = build_surface_adapter({}, {}, {}, {})
    assert surface["surface_state"] == "BLOCKED_MISSING_SURFACE_INPUTS"
    assert surface["input_presence"]["read_model_present"] is False


def test_run_writes_outputs(tmp_path):
    summary = run(
        read_model_json="samples/b9_reality_board_surface_adapter_candidate_v0/sample_read_model.json",
        panel_json="samples/b9_reality_board_surface_adapter_candidate_v0/sample_panel.json",
        payload_json="samples/b9_reality_board_surface_adapter_candidate_v0/sample_payload.json",
        display_contract_json="samples/b9_reality_board_surface_adapter_candidate_v0/sample_display_contract.json",
        output_dir=str(tmp_path),
    )
    assert Path(summary["zip"]).exists()
    assert (tmp_path / "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json").exists()
    assert summary["forbidden_language_hits"] == []
