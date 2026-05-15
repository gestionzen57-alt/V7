from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_usd_base_polarity_cohort_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_USD_BASE_POLARITY_COHORT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_USD_BASE_POLARITY_COHORT"
    assert data["read_only"] is True
    assert data["runtime_wired"] is False
    assert data["engine_change_required"] is False
    assert "USDJPY" in data["usd_base_symbols"]
    assert "USDCAD" in data["usd_base_symbols"]
    assert isinstance(data["symbol_deltas"], dict)
    assert isinstance(data["recommendations"], list)


def test_t004_usd_base_polarity_verdict_known():
    path = _repo() / "Docs" / "Contracts" / "T004_USD_BASE_POLARITY_COHORT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    allowed = {
        "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES",
        "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC",
        "USDJPY_ADVANCES_USDCAD_ZERO_SYMBOL_SPECIFIC",
        "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE",
        "USD_BASE_ADVANCES_REFERENCES_IDLE",
        "NO_TRACKED_SYMBOL_ADVANCED",
        "INCONCLUSIVE_POLARITY_COHORT",
    }
    assert data["verdict"] in allowed

