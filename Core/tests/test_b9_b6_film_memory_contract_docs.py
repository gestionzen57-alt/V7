# -*- coding: utf-8 -*-
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CONTRACT_CANDIDATES = [
    ROOT / "Docs" / "Contracts" / "B9_B6_FILM_MEMORY_CONTRACT.md",
    ROOT / "Core" / "docs" / "Contracts" / "B9_B6_FILM_MEMORY_CONTRACT.md",
]

REPORT_CANDIDATES = [
    ROOT / "Docs" / "Reports" / "B9_B6_FILM_MEMORY_CONTRACT_REPORT.md",
    ROOT / "Core" / "docs" / "Reports" / "B9_B6_FILM_MEMORY_CONTRACT_REPORT.md",
]


def _first_existing(paths):
    for path in paths:
        if path.exists():
            return path
    raise AssertionError("Missing expected file. Checked: " + ", ".join(str(p) for p in paths))


def _read(path):
    return path.read_text(encoding="utf-8")


def test_contract_file_exists():
    assert _first_existing(CONTRACT_CANDIDATES).exists()


def test_report_file_exists():
    assert _first_existing(REPORT_CANDIDATES).exists()


def test_required_b6_fields_present():
    text = _read(_first_existing(CONTRACT_CANDIDATES))
    required = [
        "film_signature",
        "sequence_signature",
        "dominant_zone_memory",
        "raw_confirmation_state",
        "historical_analogy",
        "false_positive_risks",
        "confirmation_needed_fr",
        "invalidation_needed_fr",
        "limits",
    ]
    for item in required:
        assert item in text


def test_raw_confirmation_states_present():
    text = _read(_first_existing(CONTRACT_CANDIDATES))
    for item in [
        "RAW_CONFIRMED",
        "RAW_PARTIAL",
        "RAW_UNAVAILABLE",
        "RAW_DIVERGENCE",
    ]:
        assert item in text


def test_false_positive_risks_present():
    text = _read(_first_existing(CONTRACT_CANDIDATES))
    for item in [
        "PROXY_PROGRESSIVE_WAVE_OVERREAD",
        "ZERO_DURATION_ARTIFACT",
        "RAW_BROKER_RELATIVE",
        "SOURCE_PROFILE_LIMITED",
    ]:
        assert item in text


def test_b6_compares_but_does_not_predict():
    text = _read(_first_existing(CONTRACT_CANDIDATES))
    assert "B6 compares" in text or "B6 compare" in text
    assert "B6 does not predict" in text or "B6 ne prédit pas" in text
    assert "B6 does not decide" in text or "B6 ne décide pas" in text


def test_no_directional_order_language():
    combined = (
        _read(_first_existing(CONTRACT_CANDIDATES)) + "\n" +
        _read(_first_existing(REPORT_CANDIDATES))
    ).lower()
    forbidden_phrases = [
        "acheter maintenant",
        "vendre maintenant",
        "entry signal",
        "automatic entry",
        "trade garanti",
        "signal infaillible",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in combined


def test_constraints_are_visible():
    text = _read(_first_existing(REPORT_CANDIDATES))
    for item in [
        "documentary-only",
        "read-only",
        "no `powerflow.db` write",
        "no dashboard",
        "no Telegram",
        "no premature B8 fusion",
    ]:
        assert item in text
