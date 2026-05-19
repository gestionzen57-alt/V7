from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Core"))

from pf_b6_field_memory_reader import (
    FILM_LIBRARY,
    HARD_EXCLUSION_PAIRS,
    best_field_memory_match,
    film_ids,
    get_film_by_id,
    has_hard_exclusion,
    match_field_memory,
    score_film_match,
)
from pf_b9_source_constants import (
    FIELD_MEMORY_SOURCE_TAG,
    MT5_RAW_IMPACT,
    SOURCE_MODE_FORCE_DERIVED,
    SOURCE_MODE_RAW_MT5_NATIVE,
    SOURCE_MODE_RECOVERED_B9,
    get_field_memory_source_tag,
    get_mt5_raw_impact,
)


def ctx(seq=None, zones=None, verdicts=None, moves=None, last=None, visibility="TACTICAL_OK"):
    return {
        "sequence_signature": seq or [],
        "zone_roles": zones or [],
        "price_verdicts": verdicts or [],
        "move_roles": moves or [],
        "last_structural_event": last,
        "data_visibility": visibility,
    }


def assert_best(context, film_id, source_date="2026-05-15"):
    best = best_field_memory_match(context, source_date=source_date)
    assert best is not None
    assert best["film_id"] == film_id
    assert best["score"] == 3


def test_library_contains_exactly_15_films():
    assert len(FILM_LIBRARY) == 15
    assert len(set(film_ids())) == 15


def test_new_film_ids_8_to_15_present():
    expected = {
        "LOW_ZONE_BUILD_RELEASE_UP",
        "HIGH_ZONE_REJECTION",
        "BREAK_RETEST_FAILED",
        "EFFORT_WITHOUT_RESULT_FRICTION",
        "PROGRESSIVE_WAVE",
        "ROTATIONAL_AUCTION",
        "RAW_TEXTURE_TRAP",
        "LIVE_ATTENTION_ONLY",
    }
    assert expected.issubset(set(film_ids()))


def test_low_zone_build_release_up_matches_score_3():
    assert_best(ctx(["LOW_ZONE_BUILD", "COMPRESSION"], ["low_zone_build"], ["zone_acceptance"], ["ZONE_BUILD"]), "LOW_ZONE_BUILD_RELEASE_UP")


def test_high_zone_rejection_matches_score_3():
    assert_best(ctx(["HIGH_ZONE_TOUCH"], ["high_zone_rejected"], ["center_failed"], ["TOUCH_HIGH"]), "HIGH_ZONE_REJECTION")


def test_break_retest_failed_matches_score_3():
    assert_best(ctx(["BREAK", "RETEST"], ["break_retest_zone"], ["center_failed"], ["RETEST"]), "BREAK_RETEST_FAILED")


def test_effort_without_result_friction_matches_score_3_with_reconstructed_visibility():
    assert_best(ctx(["HIGH_ACTIVITY"], ["friction_zone"], ["progress_weak"], ["COMPRESSION"], visibility="RECONSTRUCTED"), "EFFORT_WITHOUT_RESULT_FRICTION")


def test_progressive_wave_matches_score_3():
    assert_best(ctx(["STEP_PROGRESS"], ["wave_progression"], ["net_progress"], ["WAVE_PROGRESSION"]), "PROGRESSIVE_WAVE")


def test_rotational_auction_matches_score_3():
    assert_best(ctx(["CENTER_CROSSES"], ["rotation_anchor_zone"], ["range_stability"], ["AUCTION_ROTATIONAL_BALANCE"]), "ROTATIONAL_AUCTION")


def test_raw_texture_trap_matches_score_3_with_reading_partial():
    assert_best(ctx(["PROXY_DIRECTIONAL"], ["texture_trap"], ["raw_rotation_or_friction"], ["PROXY_DIRECTIONAL_READ"], visibility="READING_PARTIAL"), "RAW_TEXTURE_TRAP")


def test_live_attention_only_matches_score_3_with_reading_partial():
    assert_best(ctx(["LIVE_SOURCE_UNQUALIFIED"], ["live_candidate"], ["manual_review_required"], ["LIVE_ATTENTION_CANDIDATE"], visibility="READING_PARTIAL"), "LIVE_ATTENTION_ONLY")


def test_hard_exclusion_pairs_extended_are_present():
    expected = {
        ("PULLBACK_ABSORBED", "FAILED_REINTEGRATION"),
        ("RETEST_OUTCOME_ACCEPTED", "RETEST_OUTCOME_REJECTED"),
        ("FLOW_DIRECTIONAL_DISPLACEMENT", "FLOW_BALANCED_AUCTION"),
        ("CONFIRMED_BY_RAW", "RAW_UNAVAILABLE"),
        ("CLEAN_PROGRESSIVE_WAVE", "FLOW_GAPPY_LIMIT"),
    }
    assert expected.issubset(set(HARD_EXCLUSION_PAIRS))


def test_hard_exclusion_detects_conflict_any_order():
    assert has_hard_exclusion(["FAILED_REINTEGRATION", "PULLBACK_ABSORBED"])


def test_hard_exclusion_forces_score_zero():
    film = get_film_by_id("PROGRESSIVE_WAVE")
    result = score_film_match(ctx(["STEP_PROGRESS"], ["wave_progression"], ["PULLBACK_ABSORBED", "FAILED_REINTEGRATION"]), film)
    assert result["score"] == 0
    assert result["excluded"] is True
    assert result["exclusion_reason"] == "HARD_EXCLUSION_PAIR"


def test_film_specific_exclusion_blocks_same_direction_conflict():
    film = get_film_by_id("HIGH_ZONE_REJECTION")
    result = score_film_match(ctx(["HIGH_ZONE_TOUCH"], ["high_zone_rejected"], ["center_failed"], ["ACCEPTED_HIGH_ZONE"]), film)
    assert result["score"] == 0
    assert result["excluded"] is True
    assert result["exclusion_reason"].startswith("FILM_EXCLUSION_IF_SAME_DIR")


def test_score_can_be_zero_one_two_three():
    film = get_film_by_id("PROGRESSIVE_WAVE")
    assert score_film_match(ctx(), film)["score"] == 0
    assert score_film_match(ctx(["STEP_PROGRESS"]), film)["score"] == 1
    assert score_film_match(ctx(["STEP_PROGRESS"], ["wave_progression"]), film)["score"] == 2
    assert score_film_match(ctx(["STEP_PROGRESS"], ["wave_progression"], ["net_progress"]), film)["score"] == 3


def test_source_date_filter_limits_results_to_20260515():
    matches = match_field_memory(ctx(["LOW_ZONE_BUILD"], ["low_zone_build"], ["zone_acceptance"]), source_date="2026-05-15")
    assert matches
    assert all(match["source_date"] == "2026-05-15" for match in matches)


def test_source_date_filter_can_return_no_match_for_other_date():
    matches = match_field_memory(ctx(["LOW_ZONE_BUILD"], ["low_zone_build"], ["zone_acceptance"]), source_date="2026-05-06")
    assert matches == []


def test_visibility_below_required_blocks_tactical_ok_film():
    film = get_film_by_id("LOW_ZONE_BUILD_RELEASE_UP")
    result = score_film_match(ctx(["LOW_ZONE_BUILD"], ["low_zone_build"], ["zone_acceptance"], visibility="READING_PARTIAL"), film)
    assert result["score"] == 0
    assert result["excluded"] is True
    assert result["exclusion_reason"] == "SOURCE_VISIBILITY_BELOW_REQUIRED"


def test_reconstructed_visibility_satisfies_effort_without_result_friction():
    film = get_film_by_id("EFFORT_WITHOUT_RESULT_FRICTION")
    result = score_film_match(ctx(["HIGH_ACTIVITY"], ["friction_zone"], ["range_contained"], visibility="RECONSTRUCTED"), film)
    assert result["score"] == 3
    assert result["excluded"] is False


def test_source_constants_modes_added():
    assert SOURCE_MODE_RECOVERED_B9 == "RECOVERED_EXISTING_B9_SUMMARY"
    assert SOURCE_MODE_FORCE_DERIVED == "FORCE_SNAPSHOT_DERIVED"
    assert SOURCE_MODE_RAW_MT5_NATIVE == "RAW_TICK_PLUS_FORCE_CONTEXT"


def test_field_memory_source_tag_dates():
    assert FIELD_MEMORY_SOURCE_TAG["2026-05-06"] == SOURCE_MODE_RECOVERED_B9
    assert FIELD_MEMORY_SOURCE_TAG["2026-05-15"] == SOURCE_MODE_FORCE_DERIVED
    assert get_field_memory_source_tag("2099-01-01") == SOURCE_MODE_FORCE_DERIVED


def test_mt5_raw_impact_map():
    assert MT5_RAW_IMPACT["BREAK_RETEST_FAILED"] == "VERY_HIGH"
    assert MT5_RAW_IMPACT["PROGRESSIVE_WAVE"] == "MEDIUM"
    assert get_mt5_raw_impact("UNKNOWN_EVENT") == "UNKNOWN"


def test_best_match_returns_none_when_no_score():
    assert best_field_memory_match(ctx(["NOTHING"], ["none"], ["none"]), source_date="2026-05-15") is None
