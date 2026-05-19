from pf_zone_context_reader import read_zone_context


def test_rejection_zone_detected_touch_and_strong_rejection():
    out = read_zone_context(
        1.3300,
        1.3310,
        [{"timestamp": "2026-05-19T08:00:00Z", "ticks": 6, "dwell_sec": 12, "reaction_pips": 11, "price_exit": 1.3321, "center_accepted": False}],
        4,
        1.3321,
    )
    assert out["zone_role"] == "REJECTION_ZONE"
    assert out["zone_status"] == "ACTIVE"
    assert out["zone_memory_active"] is True


def test_acceptance_zone_detected_touch_dwell_center_ok():
    out = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 8, "dwell_sec": 25, "reaction_pips": 2, "price_exit": 1.3306, "center_accepted": True}],
        3,
        1.3306,
    )
    assert out["zone_role"] == "ACCEPTANCE_ZONE"


def test_absorption_zone_detected_multi_touch_stagnation():
    out = read_zone_context(
        1.3300,
        1.3310,
        [
            {"ticks": 6, "dwell_sec": 18, "reaction_pips": 2, "price_exit": 1.3304},
            {"ticks": 7, "dwell_sec": 22, "reaction_pips": 2, "price_exit": 1.3306},
        ],
        2,
        1.3305,
    )
    assert out["zone_role"] == "ABSORPTION_ZONE"
    assert out["microfilm_metrics"]["net_price_progress_pips"] <= 3


def test_break_retest_zone_detected():
    out = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 6, "dwell_sec": 16, "reaction_pips": 5, "prior_breakout": True, "price_returns_to_zone": True, "retest_outcome": "FAILED"}],
        2,
        1.3305,
    )
    assert out["zone_role"] == "BREAK_RETEST_ZONE"


def test_rotation_anchor_zone_detected():
    out = read_zone_context(
        1.3300,
        1.3310,
        [
            {
                "ticks": 5,
                "dwell_sec": 12,
                "reaction_pips": 2,
                "center_cross_count": 3,
                "max_distance_above_center": 3,
                "max_distance_below_center": 3,
                "directional_escape": False,
            }
        ],
        2,
        1.3305,
    )
    assert out["zone_role"] == "ROTATION_ANCHOR_ZONE"


def test_stale_if_bars_since_touch_above_threshold():
    out = read_zone_context(1.3300, 1.3310, [], 51, 1.3350)
    assert out["zone_status"] == "STALE"
    assert out["reactivation_status"]["was_stale"] is True


def test_stale_reactivated_single_strong():
    out = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 5, "dwell_sec": 30, "reaction_pips": 8, "price_exit": 1.3320, "center_accepted": False}],
        55,
        1.3320,
    )
    assert out["zone_status"] == "OLD_BUT_REACTIVATED"
    assert out["reactivation_status"]["reactivation_type"] == "SINGLE_STRONG"


def test_stale_reactivated_multi_touch():
    out = read_zone_context(
        1.3300,
        1.3310,
        [
            {"ticks": 3, "dwell_sec": 23, "reaction_pips": 1, "price_exit": 1.3304},
            {"ticks": 4, "dwell_sec": 22, "reaction_pips": 1, "price_exit": 1.3306},
        ],
        70,
        1.3305,
    )
    assert out["zone_status"] == "OLD_BUT_REACTIVATED"
    assert out["reactivation_status"]["reactivation_type"] == "MULTI_TOUCH"


def test_stale_remains_stale_when_reactivation_insufficient():
    out = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 2, "dwell_sec": 8, "reaction_pips": 2, "price_exit": 1.3308}],
        80,
        1.3308,
    )
    assert out["zone_status"] == "STALE"
    assert out["reactivation_status"]["reactivated"] is False


def test_undefined_if_data_insufficient():
    out = read_zone_context(1.3300, 1.3310, [], 0, 1.3330)
    assert out["zone_role"] == "UNDEFINED"
    assert out["zone_memory_active"] is False


def test_source_stack_propagated():
    out = read_zone_context(1.3300, 1.3310, [], 0, 1.3330, source_stack="READING_PARTIAL|M1_BAR_PROXY")
    assert out["source_stack"] == "READING_PARTIAL|M1_BAR_PROXY"


def test_confidence_varies_with_evidence_quality():
    weak = read_zone_context(1.3300, 1.3310, [], 0, 1.3330)
    strong = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 8, "dwell_sec": 30, "reaction_pips": 9, "price_exit": 1.3320, "center_accepted": False}],
        0,
        1.3320,
    )
    assert strong["confidence"] > weak["confidence"]
