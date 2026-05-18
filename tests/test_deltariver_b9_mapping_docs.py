from pathlib import Path


def test_deltariver_b9_mapping_v2_contains_core_contract():
    doc = Path("Docs/Reports/DELTARIVER_TO_POWERFLOW_B9_MAPPING.md")
    assert doc.exists(), "mapping doc missing"
    text = doc.read_text(encoding="utf-8")
    required = [
        "B9 — Microfilm Battlefield Memory",
        "event brut",
        "moment contextualisé",
        "T009_MOMENT_IMBALANCE_ABSORBED",
        "T009_MOMENT_BREAK_RETEST",
        "M1_BAR_PROXY",
        "RAW_TICK",
        "Sequence Summarizer V0",
        "Aucun signal BUY/SELL",
    ]
    for item in required:
        assert item in text, f"missing marker: {item}"


def test_deltariver_b9_comparison_exists_and_mentions_v1_v2():
    doc = Path("Docs/Reports/DELTARIVER_TO_POWERFLOW_B9_V1_V2_COMPARISON.md")
    assert doc.exists(), "comparison doc missing"
    text = doc.read_text(encoding="utf-8")
    assert "V1" in text
    assert "V2" in text
    assert "La V2 remplace la V1" in text
