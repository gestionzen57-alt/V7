from __future__ import annotations

import json
from pathlib import Path

from pf_t009_live_chain_runtime_missing_input_resolver import EXPECTED_STEPS, run


def _touch_all_expected(root: Path) -> None:
    for step in EXPECTED_STEPS:
        path = root / step.required_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('{"ok": true}\n', encoding="utf-8")


def test_missing_inputs_generate_regeneration_plan(tmp_path: Path):
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps({
        "candidate_id": "B9LSC_E49A7AEC65CE",
        "match_count": 3,
        "top_match_film_id": "B6FC_20260511_1641_010496DB",
        "missing_steps": ["T0148_LIVE_BRIEF_ONCE", "T0170_TELEGRAM_MANUAL_APPROVAL"],
    }), encoding="utf-8")
    summary = run(tmp_path, tmp_path / "out", contract)
    assert summary["missing_or_regenerate_count"] >= 2
    assert "T0148_LIVE_BRIEF_ONCE" in summary["missing_steps"]
    assert (tmp_path / "out" / "B9_LIVE_CHAIN_REGENERATION_PLAN_V0.ps1").exists()


def test_complete_inputs_pass(tmp_path: Path):
    _touch_all_expected(tmp_path)
    contract = tmp_path / "outputs/b9_live_chain_contract_validator_v0/B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.json"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_text(json.dumps({
        "candidate_id": "B9LSC_E49A7AEC65CE",
        "match_count": 3,
        "top_match_film_id": "B6FC_20260511_1641_010496DB",
        "missing_steps": [],
    }), encoding="utf-8")
    summary = run(tmp_path, tmp_path / "out")
    assert summary["resolver_state"] == "B9_LIVE_CHAIN_INPUTS_COMPLETE"
    assert summary["missing_or_regenerate_count"] == 0


def test_outputs_have_no_forbidden_language(tmp_path: Path):
    summary = run(tmp_path, tmp_path / "out", tmp_path / "missing_contract.json")
    assert summary["forbidden_language_hits"] == []
    md = (tmp_path / "out" / "B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.md").read_text(encoding="utf-8")
    assert "probabilité de réussite" not in md.lower()
