from __future__ import annotations

import csv
import json
from pathlib import Path

from tools.build_t0176_b9_chain_degraded_dashboard_candidate import build_contract, main


def _write_t0175_sample(root: Path) -> Path:
    lock_dir = root / "outputs" / "t0175_b9_global_chain_contract_lock_v0"
    lock_dir.mkdir(parents=True)
    (lock_dir / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json").write_text(
        json.dumps(
            {
                "lock_state": "LOCK_BLOCKED_MISSING_REQUIRED",
                "required_missing_count": 2,
                "optional_missing_count": 1,
                "source_error_count": 0,
                "forbidden_language_hit_count": 0,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    with (lock_dir / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "required"])
        writer.writeheader()
        writer.writerow({"path": "outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json", "required": "true"})
        writer.writerow({"path": "tools/build_t0169_b9_reality_board_surface_adapter_candidate.py", "required": "true"})
    with (lock_dir / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_SOURCE_MATRIX_V0.csv").open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["path", "status"])
        writer.writeheader()
        writer.writerow({"path": "outputs/b9_reality_board_read_model_v01/B9_REALITY_BOARD_READ_MODEL_V01.json", "status": "present"})
    return lock_dir


def test_build_contract_degraded_state(tmp_path: Path) -> None:
    _write_t0175_sample(tmp_path)
    out = tmp_path / "outputs" / "t0176"
    contract = build_contract(tmp_path, out)
    assert contract["dashboard_candidate_state"] == "DEGRADED_REQUIRED_INPUTS_MISSING"
    assert contract["chain_state"]["required_missing_count"] == 2
    assert len(contract["sections"]["inputs_manquants"]) == 2


def test_missing_cards_classify_t0169_and_attention_packet(tmp_path: Path) -> None:
    _write_t0175_sample(tmp_path)
    contract = build_contract(tmp_path, tmp_path / "out")
    bricks = {card["brick"] for card in contract["sections"]["cartes_techniques_par_brique_absente"]}
    assert "T0169 surface adapter" in bricks
    assert "Trader attention packet" in bricks


def test_already_visible_from_source_matrix(tmp_path: Path) -> None:
    _write_t0175_sample(tmp_path)
    contract = build_contract(tmp_path, tmp_path / "out")
    visible = contract["sections"]["ce_que_b9_voit_deja"]
    assert visible
    assert visible[0]["brick"] == "Reality Board read model"


def test_cli_writes_outputs(tmp_path: Path) -> None:
    _write_t0175_sample(tmp_path)
    rc = main(["--core-root", str(tmp_path), "--output-dir", "outputs/t0176", "--print-json"])
    assert rc == 0
    out_dir = tmp_path / "outputs" / "t0176"
    assert (out_dir / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.json").exists()
    assert (out_dir / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.md").exists()
    assert (out_dir / "B9_CHAIN_DEGRADED_DASHBOARD_MISSING_BRICK_CARDS_V0.csv").exists()
    assert (out_dir / "B9_CHAIN_DEGRADED_DASHBOARD_REGEN_COMMANDS_V0.csv").exists()


def test_missing_lock_blocks_without_crashing(tmp_path: Path) -> None:
    contract = build_contract(tmp_path, tmp_path / "out")
    assert contract["dashboard_candidate_state"] == "BLOCKED_T0175_LOCK_UNREADABLE"
    assert contract["source_lock"]["load_errors"]
