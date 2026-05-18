from __future__ import annotations

import json
from pathlib import Path

from pf_b9_reality_board_read_model_v0 import (
    PANEL_OUTPUT_DIR,
    READ_MODEL_OUTPUT_DIR,
    build_read_model,
    build_scene_panel_candidate,
    generate_artifacts,
)


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def test_read_model_generates_required_sections(tmp_path: Path) -> None:
    repo = tmp_path
    write_json(
        repo / "outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
        {
            "what_b9_sees_fr": "B9 voit une migration de mémoire locale.",
            "scene_state": "CENTER_MIGRATION_DOWN",
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.35,
        },
    )
    write_json(
        repo / "outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json",
        {"watch_condition": "surveiller retest et absorption", "technical_risks": ["M1_PROXY_LIMIT"]},
    )
    write_json(
        repo / "outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json",
        {"price_verdict": "PENDING_RETEST", "zone_active": {"low": 1.333, "high": 1.334}},
    )
    write_json(
        repo / "outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json",
        {"scene_id": "scene_001", "session_chapter": "Migration de centre"},
    )

    read_model = build_read_model(repo)
    assert read_model["read_only"] is True
    assert read_model["dashboard_live_binding"] is False
    assert read_model["sections"]["ce_que_b9_voit"]["body_fr"] == "B9 voit une migration de mémoire locale."
    assert read_model["source_quality"]["technical_status"] in {"OK", "DEGRADED"}
    for key in [
        "ce_que_b9_voit",
        "etat_de_scene",
        "transition",
        "zone_active",
        "node_terrain",
        "verdict_prix",
        "memoire_b6_proche",
        "similarites",
        "differences",
        "pieges_techniques",
        "source_quality",
        "ce_qu_il_faut_surveiller_ensuite",
        "ce_que_b9_ne_peut_pas_conclure",
    ]:
        assert key in read_model["sections"]


def test_panel_candidate_has_no_decision_buttons(tmp_path: Path) -> None:
    read_model = build_read_model(tmp_path)
    panel = build_scene_panel_candidate(read_model)
    assert panel["candidate_only"] is True
    assert panel["dashboard_live_binding"] is False
    assert "BUY_SELL_BUTTON" in panel["forbidden_ui"]
    assert all(block["display_contract"] == "TEXT_ONLY_NO_DECISION_BUTTON" for block in panel["display_blocks"])


def test_generate_artifacts_writes_outputs_and_sanitizes_decision_terms(tmp_path: Path) -> None:
    repo = tmp_path
    write_json(
        repo / "outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
        {"what_b9_sees_fr": "Source disait BUY puis SELL mais le read model neutralise."},
    )
    paths = generate_artifacts(repo)
    assert (repo / READ_MODEL_OUTPUT_DIR / "B9_REALITY_BOARD_READ_MODEL_V0.json").exists()
    assert (repo / PANEL_OUTPUT_DIR / "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V0.md").exists()
    read_text = paths["read_model_md"].read_text(encoding="utf-8")
    assert "BUY" not in read_text
    assert "SELL" not in read_text
    assert "Le dashboard affiche, il ne décide pas." in read_text
