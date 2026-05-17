from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "docs" / "Reports"
DOC_A = REPORTS / "B9_PROXY_VS_RAW_FIRST_VALIDATION.md"
DOC_B = REPORTS / "T010_B9_PROXY_VS_RAW_FINAL_REPORT.md"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_t010_reports_exist():
    assert DOC_A.exists()
    assert DOC_B.exists()


def test_reports_contain_required_alignment_and_broker():
    merged = _text(DOC_A) + "\n" + _text(DOC_B)
    assert "raw_ts_mt5 + 180 minutes" in merged
    assert "OneFunded Capital Ltd." in merged
    assert "MT5_RAW_ALIGNED" in merged


def test_reports_contain_required_counts():
    merged = _text(DOC_A) + "\n" + _text(DOC_B)
    assert "57" in merged
    assert "15" in merged
    assert "6" in merged
    assert "74 108" in merged
    assert "78" in merged


def test_reports_describe_proxy_raw_roles():
    merged = _text(DOC_A) + "\n" + _text(DOC_B)
    assert "M1_BAR_PROXY" in merged
    assert "RECONSTRUCTED" in merged
    assert "MT5 HISTORICAL_RAW" in merged
    assert "Le proxy M1 raconte la scène" in merged
    assert "Le raw MT5 vérifie la texture" in merged


def test_reports_have_no_directional_recommendation():
    merged = _text(DOC_A) + "\n" + _text(DOC_B)
    forbidden_recommendations = [
        "recommandation BUY",
        "recommandation SELL",
        "BUY recommandé",
        "SELL recommandé",
        "signal BUY",
        "signal SELL",
    ]
    upper = merged.upper()
    for phrase in forbidden_recommendations:
        assert phrase.upper() not in upper


def test_reports_state_no_db_dashboard_telegram_rules():
    merged = _text(DOC_A) + "\n" + _text(DOC_B)
    assert "aucune écriture powerflow.db" in merged
    assert "aucune écriture tick_archive.db" in merged
    assert "aucun dashboard" in merged
    assert "aucun Telegram" in merged
