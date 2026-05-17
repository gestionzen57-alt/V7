from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "docs" / "Contracts" / "B9_TEMPORALITY_CONTRACT.md"
REPORT = ROOT / "docs" / "Reports" / "B9_TEMPORALITY_CONTRACT_REPORT.md"


def _read(path: Path) -> str:
    assert path.exists(), f"Missing expected document: {path}"
    return path.read_text(encoding="utf-8")


def test_contract_and_report_exist():
    assert CONTRACT.exists()
    assert REPORT.exists()


def test_temporal_phase_enums_are_documented():
    text = _read(CONTRACT)
    for token in ["WINDOW_YOUNG", "WINDOW_ACTIVE", "WINDOW_LATE", "WINDOW_CLOSED"]:
        assert token in text


def test_watch_states_include_second_leg_and_absorption():
    text = _read(CONTRACT)
    for token in ["WATCH_SECOND_LEG", "WATCH_ABSORPTION"]:
        assert token in text


def test_raw_coverage_and_proxy_vs_raw_are_part_of_contract():
    text = _read(CONTRACT)
    for token in ["raw_coverage", "proxy_vs_raw_verdict", "RAW_UNAVAILABLE", "RAW_CONFIRMED"]:
        assert token in text


def test_b9_temporality_separation_is_explicit():
    text = _read(CONTRACT)
    required_phrases = [
        "B9 reste la trace locale",
        "Temporalité ne répète pas B9",
        "Temporalité ne remplace jamais B9",
        "B9 dit ce qui s’imprime dans la scène",
        "La Temporalité dit si cette scène est jeune, active, tardive ou consommée",
    ]
    for phrase in required_phrases:
        assert phrase in text


def test_no_decision_language_outside_forbidden_section():
    text = _read(CONTRACT)
    before_forbidden = text.split("## 7. Interdits", 1)[0]
    forbidden_tokens = ["BUY", "SELL", "buy", "sell", "achat immédiat", "vente immédiate"]
    for token in forbidden_tokens:
        assert token not in before_forbidden


def test_contract_documents_required_output_shape():
    text = _read(CONTRACT)
    for token in [
        "temporal_phase",
        "temporal_role",
        "watch_state",
        "phase_confidence",
        "why_fr",
        "limits",
    ]:
        assert token in text


def test_report_lists_exact_deliverables_and_validation_commands():
    text = _read(REPORT)
    for token in [
        "Core/docs/Contracts/B9_TEMPORALITY_CONTRACT.md",
        "Core/docs/Reports/B9_TEMPORALITY_CONTRACT_REPORT.md",
        "Core/tests/test_b9_temporality_contract_docs.py",
        "py_compile",
        "pytest",
    ]:
        assert token in text
