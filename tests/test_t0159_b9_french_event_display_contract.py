from pf_b9_french_event_display_contract import build_contract, translate_event, validate_contract


def test_contract_has_core_categories_and_no_forbidden_language():
    rows = build_contract()
    validation = validate_contract(rows)
    assert validation["contract_state"] == "PASS"
    assert validation["entry_count"] >= 40
    assert not validation["missing_categories"]
    assert not validation["forbidden_language_hits"]


def test_translate_known_and_unknown_events():
    rows = build_contract()
    scene = translate_event("SCENE_ACCEPTED", rows)
    assert scene["label_fr_short"] == "Scene acceptee"
    assert "prix" in scene["phrase_fr_trader"].lower()
    unknown = translate_event("NEW_UNMAPPED_EVENT", rows)
    assert unknown["category"] == "unknown"
    assert unknown["severity_hint"] == "REVIEW"


def test_extra_entries_are_accepted():
    rows = build_contract([
        {
            "category": "scene_state",
            "enum_key": "CUSTOM_TEST_EVENT",
            "label_fr_short": "Evenement test",
            "phrase_fr_trader": "Evenement test lisible en francais trader.",
        }
    ])
    translated = translate_event("CUSTOM_TEST_EVENT", rows)
    assert translated["label_fr_short"] == "Evenement test"
