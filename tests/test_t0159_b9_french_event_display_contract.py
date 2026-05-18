from __future__ import annotations

import json
from pathlib import Path

import pytest

from pf_b9_french_event_display_contract import (
    CONTRACT,
    VERSION,
    get_display,
    translate_event,
    translate_payload,
    validate_contract,
    write_json_csv_md,
)


def test_t0159_examples_are_translated() -> None:
    assert translate_event("scene_state", "SCENE_ACCEPTED") == "Scène acceptée par le prix"
    assert translate_event("scene_transition", "PULLBACK_ABSORBED") == "Pullback absorbé"
    assert translate_event("memory_confidence_ladder", "MEMORY_PARTIAL_COMPARABLE") == "Mémoire comparable partielle"
    assert translate_event("false_positive_context", "B9_FALSE_POSITIVE_CONTEXT_HIGH") == "Film proche, mais piège technique fort"
    assert translate_event("source_quality_gate", "RAW_UNAVAILABLE_REJECTED") == "Rejeté : raw indisponible"


def test_t0159_contract_covers_required_categories() -> None:
    required = {
        "scene_state",
        "scene_transition",
        "scene_role",
        "price_verdict",
        "terrain_node",
        "memory_confidence_ladder",
        "false_positive_context",
        "source_quality_gate",
        "telegram_gate_state",
        "reality_board_payload_state",
    }
    assert required.issubset(CONTRACT.keys())


def test_t0159_unknown_enum_has_visible_fallback() -> None:
    display = get_display("scene_state", "NEW_UNKNOWN_ENUM")
    assert display.key == "NEW_UNKNOWN_ENUM"
    assert "Traduction à ajouter" in display.label_fr
    assert display.attention_level == "WATCH"


def test_t0159_alias_payload_translation() -> None:
    payload = {
        "memory_confidence_state": "MEMORY_STRONG_COMPARABLE",
        "source_quality_gate_state": "SOURCE_RAW_NUANCED",
        "false_positive_state": "B6_FALSE_POSITIVE_CONTEXT_HIGH",
    }
    translated = translate_payload(payload)
    assert translated["memory_confidence_state"]["label_fr"] == "Mémoire fortement comparable"
    assert translated["source_quality_gate_state"]["label_fr"] == "Source nuancée par raw"
    assert translated["false_positive_state"]["label_fr"] == "Film proche, mais piège technique fort"


def test_t0159_validation_passes() -> None:
    validation = validate_contract()
    assert validation["version"] == VERSION
    assert validation["passed"] is True
    assert validation["forbidden_display_hits"] == []
    assert validation["missing_labels"] == []


def test_t0159_writes_outputs(tmp_path: Path) -> None:
    paths = write_json_csv_md(tmp_path)
    for path in paths.values():
        assert Path(path).exists()
    payload = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert payload["version"] == VERSION
    assert payload["validation"]["passed"] is True
    csv_text = Path(paths["csv"]).read_text(encoding="utf-8")
    assert "SCENE_ACCEPTED" in csv_text
    md_text = Path(paths["md"]).read_text(encoding="utf-8")
    assert "B9 French Event Display Contract V0" in md_text
