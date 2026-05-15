from __future__ import annotations

import json
from pathlib import Path


def _repo() -> Path:
    return Path(__file__).resolve().parents[1]


def test_t004_requalification_contract_shape():
    path = _repo() / "Docs" / "Contracts" / "T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert data["contract"] == "POWERFLOW_T004_REQUALIFICATION_AFTER_USD_BASE_COHORT"
    assert data["engine_change_required"] is False
    assert data["dashboard_change_required"] is False
    assert data["db_change_required"] is False
    assert isinstance(data["symbol_deltas"], dict)
    assert isinstance(data["operator_actions"], list)


def test_t004_requalification_mentions_usd_base_result():
    path = _repo() / "Docs" / "Contracts" / "T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    assert "cohort" in data["source_cohort_contract"].lower()
    assert data["cohort_verdict"] in {
        "USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE",
        "USDCAD_ADVANCES_USDJPY_ZERO_SYMBOL_SPECIFIC",
        "USD_BASE_COHORT_NOT_ADVANCING_WHILE_USD_QUOTE_ADVANCES",
        "USDJPY_ADVANCES_USDCAD_ZERO_SYMBOL_SPECIFIC",
        "USD_BASE_ADVANCES_REFERENCES_IDLE",
        "NO_TRACKED_SYMBOL_ADVANCED",
        "INCONCLUSIVE_POLARITY_COHORT",
    }

