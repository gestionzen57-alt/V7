from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_golden_terrain_fixture_builder import build_from_csv, REQUIRED_FIXTURE_FIELDS


def test_t0168_sample_builds_ready_fixtures(tmp_path):
    sample = ROOT / "samples" / "b9_golden_terrain_fixture_builder_v0" / "T0150_B9_GOLDEN_TERRAIN_CASES_V1_SAMPLE.csv"
    result = build_from_csv(sample, tmp_path)
    summary = result["summary"]
    assert summary["fixture_count"] >= 7
    assert summary["ready_count"] >= 5
    assert summary["review_count"] >= 2
    assert summary["forbidden_language_hits"] == []
    assert (tmp_path / "B9_GOLDEN_TERRAIN_FIXTURES_V0.json").exists()


def test_t0168_required_fields_present(tmp_path):
    sample = ROOT / "samples" / "b9_golden_terrain_fixture_builder_v0" / "T0150_B9_GOLDEN_TERRAIN_CASES_V1_SAMPLE.csv"
    result = build_from_csv(sample, tmp_path)
    fixtures = result["fixtures"]
    for fixture in fixtures:
        for field in REQUIRED_FIXTURE_FIELDS:
            assert field in fixture
            assert fixture[field] not in (None, "", [])


def test_t0168_raw_guard_and_no_decision(tmp_path):
    sample = ROOT / "samples" / "b9_golden_terrain_fixture_builder_v0" / "T0150_B9_GOLDEN_TERRAIN_CASES_V1_SAMPLE.csv"
    result = build_from_csv(sample, tmp_path)
    for fixture in result["fixtures"]:
        assert fixture["no_decision_guard"] is True
        assert "expected_scene_role" in fixture
