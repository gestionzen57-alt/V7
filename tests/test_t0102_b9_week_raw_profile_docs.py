from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "Docs" / "Reports"
FILES = [
    REPORTS / "B9_WEEK_RAW_PROFILE_20260504_20260515.md",
    REPORTS / "B9_PRICE_MEMORY_ZONES_20260504_20260515.md",
    REPORTS / "B9_SCENE_BANK_RAW_20260504_20260515.md",
    REPORTS / "B9_B6_LAB_CANDIDATES_20260504_20260515.md",
]


def read_all() -> str:
    return "\n".join(p.read_text(encoding="utf-8") for p in FILES)

def test_t0102_reports_exist():
    for path in FILES:
        assert path.exists(), path


def test_week_raw_profile_contains_required_counts_and_dedup_rule():
    text = (REPORTS / "B9_WEEK_RAW_PROFILE_20260504_20260515.md").read_text(encoding="utf-8")
    assert "872 957" in text
    assert "120 322" in text
    assert "752 635" in text
    assert "DISTINCT ts_utc, bid, ask, mid, spread" in text
    assert "54 722" in text
    assert "65 589" in text


def test_scene_categories_are_present():
    text = (REPORTS / "B9_SCENE_BANK_RAW_20260504_20260515.md").read_text(encoding="utf-8")
    for token in [
        "PROGRESSIVE_WAVE_CONFIRMED",
        "CENTER_MIGRATION_CONFIRMED",
        "EFFORT_WITHOUT_RESULT",
        "HIGH_ZONE_EXHAUSTION",
        "LOWER_LOCK",
        "COUNTER_BREATH_REJECTED",
        "READING_PARTIAL",
        "RAW_PROXY_DIVERGENCE",
        "MEMORY_SHIFTED",
    ]:
        assert token in text


def test_price_memory_zones_are_documented():
    text = (REPORTS / "B9_PRICE_MEMORY_ZONES_20260504_20260515.md").read_text(encoding="utf-8")
    for zone in ["1.3390", "1.3362", "1.3345", "1.3317"]:
        assert zone in text
    assert "zone_memory" in text


def test_b6_lab_candidates_have_five_to_ten_scenes():
    text = (REPORTS / "B9_B6_LAB_CANDIDATES_20260504_20260515.md").read_text(encoding="utf-8")
    assert "SCN_20260515_1000_PROGRESSIVE" in text
    assert "SCN_20260515_1100_MIGRATION_DOWN" in text
    assert "SCN_20260513_COUNTER_REJECTED" in text
    assert "B6 compare mais ne prédit pas" in text


def test_limits_are_visible():
    text = read_all()
    for token in [
        "read-only",
        "aucune écriture powerflow.db",
        "aucune écriture tick_archive.db",
        "aucun dashboard",
        "aucun Telegram",
        "broker-relative",
        "pas de footprint exact",
    ]:
        assert token in text


def test_no_decision_language_as_recommendation():
    text = read_all().lower()
    forbidden_phrases = [
        "recommandation: buy",
        "recommandation : buy",
        "recommandation: sell",
        "recommandation : sell",
        "signal confirmé d'achat",
        "signal confirmé de vente",
        "entrée obligatoire",
        "sortie obligatoire",
    ]
    for phrase in forbidden_phrases:
        assert phrase not in text
