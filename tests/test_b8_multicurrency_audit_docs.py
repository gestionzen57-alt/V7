from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "Reports"
CONTRACTS = ROOT / "docs" / "Contracts"

FILES = [
    REPORTS / "B8_MULTICURRENCY_FX_IMPLEMENTATION_AUDIT.md",
    REPORTS / "B8_COMMUNICATION_MAP_WITH_BRICKS.md",
    REPORTS / "B8_GAP_ANALYSIS_AND_ROADMAP.md",
    CONTRACTS / "B8_CROSS_SYMBOL_CONTEXT_CONTRACT.md",
]


def read_all() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in FILES)


def test_docs_exist():
    for path in FILES:
        assert path.exists(), path


def test_cross_symbol_context_contract_terms_present():
    text = read_all()
    assert "cross_symbol_context" in text
    assert "GBP_STRENGTH" in text
    assert "USD_WEAKNESS" in text
    assert "MIXED_DRIVER" in text
    assert "UNKNOWN_DRIVER" in text


def test_honest_unknown_and_degraded_are_present():
    text = read_all()
    assert "HONEST_UNKNOWN" in text
    assert "CROSS_VALIDATION_DEGRADED" in text
    assert "B8_TIME_ALIGNMENT_RISK" in text


def test_b8_context_b9_local_scene_separation():
    text = read_all()
    assert "B9 = scene locale" in text or "B9 = scene locale." in text
    assert "B8 = contexte multi-devises" in text or "B8 = validation cross-symbol" in text
    assert "B8 ne reclassifie pas B9" in text


def test_no_directional_execution_language():
    text = read_all().lower()
    forbidden = ["recommandation buy", "recommandation sell", "ordre d'achat", "ordre de vente", "entry", "take profit", "stop loss"]
    for word in forbidden:
        assert word not in text


def test_no_dashboard_telegram_dependency_as_engine():
    text = read_all().lower()
    assert "aucune dependance de pf_* vers dashboard_*" in text
    assert "aucune dependance de pf_* vers telegram_*" in text


def test_coverage_and_alignment_fields_present():
    text = read_all()
    assert "aligned_symbols" in text
    assert "missing_symbols" in text
    assert "stale_symbols" in text
    assert "max_gap_seconds" in text
    assert "coverage" in text
