from __future__ import annotations

from pathlib import Path

from pf_b9_french_display_state_hardening import (
    DISPLAY_STATE_FR,
    audit_outputs,
    enum_tokens,
    translate_enum,
    translate_text_for_display,
    write_outputs,
)


def test_t0170_translates_known_leaks() -> None:
    assert translate_enum("MISSING_INPUT").label_fr == "Entrée manquante"
    assert translate_enum("RAW_UNAVAILABLE").label_fr == "Raw indisponible"
    assert "revue technique requise" in translate_enum("B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK").label_fr


def test_t0170_detects_enum_tokens_without_ids() -> None:
    text = "state=B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS candidate=B9LSC_TEST film=B6FC_TEST"
    assert enum_tokens(text) == ["B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS"]


def test_t0170_translate_text_keeps_engine_enum_visible() -> None:
    text = "State: B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS"
    rendered = translate_text_for_display(text)
    assert "Contrat chaîne live bloqué" in rendered
    assert "B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS" in rendered


def test_t0170_audit_outputs(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    target = outputs / "b9_live_chain_contract_validator_v0"
    target.mkdir(parents=True)
    (target / "report.md").write_text(
        "State: `B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS`\n"
        "- `freshness_guard`: MISSING_INPUT\n"
        "- RAW_UNAVAILABLE bloque l'approbation active.\n",
        encoding="utf-8",
    )

    audit = audit_outputs(outputs)
    assert audit["files_scanned"] == 1
    assert "B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS" in audit["covered_tokens"]
    assert "MISSING_INPUT" in audit["covered_tokens"]
    assert "RAW_UNAVAILABLE" in audit["covered_tokens"]
    assert audit["uncovered_tokens"] == []


def test_t0170_write_outputs(tmp_path: Path) -> None:
    outputs = tmp_path / "outputs"
    target = outputs / "b9_telegram_manual_approval_candidate_v0_install_validation"
    target.mkdir(parents=True)
    (target / "candidate.md").write_text(
        "- approval_state : `B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_REVIEW_TECHNICAL_RISK`\n",
        encoding="utf-8",
    )

    paths = write_outputs(outputs, tmp_path / "out")
    for path in paths.values():
        assert Path(path).exists()
    md = Path(paths["md"]).read_text(encoding="utf-8")
    assert "Approbation manuelle Telegram" in md
