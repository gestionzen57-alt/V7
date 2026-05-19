from pf_terrain_node_snapshot import create_terrain_node_snapshot
from pf_zone_context_reader import read_zone_context


def zone_context(role_payload=None, *, source_stack="FORCE_SNAPSHOT_DERIVED"):
    if role_payload is not None:
        return role_payload
    return read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 6, "dwell_sec": 12, "reaction_pips": 11, "price_exit": 1.3321, "center_accepted": False}],
        2,
        1.3321,
        source_stack=source_stack,
    )


def snapshot(zc, verdict, visibility=None):
    return create_terrain_node_snapshot(
        node_id="",
        symbol="GBPUSD",
        timestamp="2026-05-19T08:00:00Z",
        zone_context=zc,
        price_verdict=verdict,
        previous_scene_state={"previous_scene": "LOWER_ZONE_ACTIVE", "last_structural_event": "COUNTER_BREATH_REJECTED"},
        data_visibility=visibility or {"data_visibility": "TACTICAL_OK", "source_stack": "VISIBILITY_GUARD"},
    )


def test_high_rejection_node_created_correctly():
    out = snapshot(zone_context(), {"verdict": "REJECTED", "confidence": 0.8, "source_stack": "PRICE_VERDICT"})
    assert out["node_role"] == "HIGH_REJECTION_NODE"
    assert out["node_role_fr"] == "Node rejet zone haute"
    assert out["node_status"] == "ACTIVE"


def test_failed_reintegration_node_created_correctly():
    zc = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 6, "dwell_sec": 16, "reaction_pips": 5, "prior_breakout": True, "price_returns_to_zone": True, "retest_outcome": "FAILED"}],
        2,
        1.3305,
    )
    out = snapshot(zc, {"verdict": "FAILED_REINTEGRATION", "confidence": 0.7})
    assert out["node_role"] == "FAILED_REINTEGRATION_NODE"


def test_pullback_absorbed_node_created_correctly():
    zc = read_zone_context(
        1.3300,
        1.3310,
        [{"ticks": 8, "dwell_sec": 25, "reaction_pips": 2, "price_exit": 1.3306, "center_accepted": True}],
        2,
        1.3306,
    )
    out = snapshot(zc, {"verdict": "PULLBACK_ABSORBED", "confidence": 0.74})
    assert out["node_role"] == "PULLBACK_ABSORBED_NODE"


def test_effort_without_result_node_created_correctly():
    zc = read_zone_context(
        1.3300,
        1.3310,
        [
            {"ticks": 6, "dwell_sec": 18, "reaction_pips": 1, "price_exit": 1.3304},
            {"ticks": 7, "dwell_sec": 22, "reaction_pips": 1, "price_exit": 1.3306},
        ],
        2,
        1.3305,
    )
    out = snapshot(zc, {"verdict": "EFFORT_WITHOUT_RESULT", "confidence": 0.76})
    assert out["node_role"] == "EFFORT_WITHOUT_RESULT_NODE"


def test_forbidden_claims_present_if_reading_partial():
    out = snapshot(
        zone_context(source_stack="READING_PARTIAL|M1_BAR_PROXY"),
        {"verdict": "REJECTED", "confidence": 0.8},
        {"data_visibility": "READING_PARTIAL", "source_stack": "VISIBILITY_GUARD"},
    )
    assert out["forbidden_claims"]
    assert "footprint exact" in out["forbidden_claims"]
    assert out["confidence"] <= 0.45


def test_node_status_attention_if_do_not_emit():
    out = snapshot(
        zone_context(),
        {"verdict": "REJECTED", "confidence": 0.8},
        {"data_visibility": "TACTICAL_OK", "emit_policy": "DO_NOT_EMIT"},
    )
    assert out["node_status"] == "ATTENTION"
    assert out["node_role"] == "ATTENTION_NODE"


def test_node_id_generated_from_timestamp_when_missing():
    out = snapshot(zone_context(), {"verdict": "REJECTED", "confidence": 0.8})
    assert out["node_id"] == "B9N_GBPUSD_20260519080000"


def test_source_stack_propagated_and_deduped():
    out = snapshot(
        zone_context(source_stack="FORCE_SNAPSHOT_DERIVED"),
        {"verdict": "REJECTED", "confidence": 0.8, "source_stack": "PRICE_VERDICT"},
        {"data_visibility": "TACTICAL_OK", "source_stack": "VISIBILITY_GUARD|PRICE_VERDICT"},
    )
    assert out["source_stack"] == "FORCE_SNAPSHOT_DERIVED|PRICE_VERDICT|VISIBILITY_GUARD"


def test_zone_bounds_calculated_center_and_width_pips():
    out = snapshot(zone_context(), {"verdict": "REJECTED", "confidence": 0.8})
    assert out["zone_bounds"]["center"] == 1.3305
    assert out["zone_bounds"]["width_pips"] == 10.0


def test_scene_context_transmitted():
    out = snapshot(zone_context(), {"verdict": "REJECTED", "confidence": 0.8})
    assert out["scene_context"] == {
        "previous_scene": "LOWER_ZONE_ACTIVE",
        "last_structural_event": "COUNTER_BREATH_REJECTED",
    }
