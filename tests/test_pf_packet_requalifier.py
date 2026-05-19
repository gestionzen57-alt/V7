from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "Core"))

from pf_packet_requalifier_v767 import requalify_packet


def packet(raw_bias="UP", strength=0.88):
    return {"symbol": "GBPUSD", "timestamp": "2026-05-15T10:00:00Z", "raw_bias": raw_bias, "packet_strength": strength}


def zone(role, status="FRESH"):
    return {"zone_role": role, "zone_status": status, "zone_low": 1.333, "zone_high": 1.337}


def verdict(name, confidence=0.82):
    return {"verdict": name, "confidence": confidence}


def scene(state="NEUTRAL", last="NONE"):
    return {"scene_state": state, "last_structural_event": last}


def visibility(state="TACTICAL_OK", mode="FORCE_SNAPSHOT_DERIVED", cap=0.90, stack=None):
    out = {"data_visibility": state, "source_mode": mode, "confidence_cap": cap}
    if stack is not None:
        out["source_stack"] = stack
    return out


def assert_event(result, event, rule):
    assert result["requalified_event"] == event
    assert result["requalification_rule"] == rule
    assert result["should_alert"] is True
    assert "BUY_SIGNAL" in result["forbidden_claims"]
    assert "SELL_SIGNAL" in result["forbidden_claims"]


def test_rule_1_release_up_pullback_absorbed():
    result = requalify_packet(packet("UP"), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED"), scene(), visibility())
    assert_event(result, "RELEASE_UP_PULLBACK_ABSORBED", "RULE_01_RELEASE_UP_PULLBACK_ABSORBED")


def test_rule_2_release_up_rejected_high_exhaustion():
    result = requalify_packet(packet("UP"), zone("REJECTION_ZONE"), verdict("REJECTED"), scene(), visibility())
    assert_event(result, "RELEASE_UP_THEN_HIGH_ZONE_EXHAUSTION", "RULE_02_RELEASE_UP_HIGH_EXHAUSTION")


def test_rule_2_release_up_failed_reintegration_high_exhaustion():
    result = requalify_packet(packet("UP"), zone("REJECTION_ZONE"), verdict("FAILED_REINTEGRATION"), scene(), visibility())
    assert_event(result, "RELEASE_UP_THEN_HIGH_ZONE_EXHAUSTION", "RULE_02_RELEASE_UP_HIGH_EXHAUSTION")


def test_rule_3_post_release_counter_breath_rejected_second_leg_down():
    result = requalify_packet(packet("DOWN"), zone("REJECTION_ZONE"), verdict("REJECTED"), scene("POST_RELEASE"), visibility())
    assert_event(result, "POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN", "RULE_03_POST_RELEASE_SECOND_LEG_DOWN")


def test_rule_4_release_down_lower_zone_defended_late_counter_bounce():
    result = requalify_packet(packet("DOWN"), zone("ABSORPTION_ZONE"), verdict("EFFORT_WITHOUT_RESULT"), scene(), visibility())
    assert_event(result, "RELEASE_DOWN_LOWER_ZONE_DEFENDED_LATE_COUNTER_BOUNCE", "RULE_04_RELEASE_DOWN_LOWER_ZONE_DEFENDED")


def test_rule_5_rotation_building():
    result = requalify_packet(packet("MIXED"), zone("ROTATION_ANCHOR_ZONE"), verdict("INCONCLUSIVE"), scene(), visibility())
    assert_event(result, "ROTATION_BUILDING", "RULE_05_ROTATION_ANCHOR")


def test_rule_6_break_retest_failed_reintegration():
    result = requalify_packet(packet("DOWN"), zone("BREAK_RETEST_ZONE"), verdict("FAILED_REINTEGRATION"), scene(), visibility())
    assert_event(result, "BREAK_RETEST_FAILED_REINTEGRATION", "RULE_06_BREAK_RETEST_FAILED")


def test_rule_7_effort_without_result_zone_friction_when_not_rule_4():
    result = requalify_packet(packet("UP"), zone("ABSORPTION_ZONE"), verdict("EFFORT_WITHOUT_RESULT"), scene(), visibility())
    assert_event(result, "EFFORT_WITHOUT_RESULT_ZONE_FRICTION", "RULE_07_EFFORT_WITHOUT_RESULT_FRICTION")


def test_rule_8_accepted_high_zone():
    result = requalify_packet(packet("UP"), zone("ACCEPTANCE_ZONE"), verdict("ACCEPTED"), scene(), visibility())
    assert_event(result, "ACCEPTED_HIGH_ZONE", "RULE_08_ACCEPTED_HIGH_ZONE")


def test_fallback_unqualified_down():
    result = requalify_packet(packet("DOWN"), zone("UNKNOWN_ZONE"), verdict("UNKNOWN"), scene(), visibility())
    assert_event(result, "UNQUALIFIED_DOWN", "RULE_09_FALLBACK_UNQUALIFIED")
    assert "sans requalification" in result["requalified_event_fr"].lower()


def test_fallback_unqualified_unknown_for_missing_bias():
    result = requalify_packet({}, {}, {}, {}, {})
    assert result["requalified_event"] == "UNQUALIFIED_UNKNOWN"
    assert result["original_bias"] == "UNKNOWN"


def test_reading_partial_adds_forbidden_claims_and_caps_confidence():
    result = requalify_packet(packet("UP", 0.99), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED", 0.98), scene(), visibility("READING_PARTIAL", "M1_BAR_PROXY", 0.95))
    assert result["requalified_confidence"] == 0.35
    assert "FULL_STACK_VISIBLE" in result["forbidden_claims"]
    assert "RAW_TICK_CONFIRMED" in result["forbidden_claims"]
    assert "EXACT_BID_ASK_DELTA_CLAIM" in result["forbidden_claims"]


def test_degraded_caps_confidence_to_050():
    result = requalify_packet(packet("UP", 0.99), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED", 0.99), scene(), visibility("DEGRADED", cap=0.99))
    assert result["requalified_confidence"] == 0.50


def test_minimal_caps_confidence_to_045():
    result = requalify_packet(packet("UP", 0.99), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED", 0.99), scene(), visibility("MINIMAL", cap=0.99))
    assert result["requalified_confidence"] == 0.45


def test_blind_caps_confidence_to_020():
    result = requalify_packet(packet("UP", 0.99), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED", 0.99), scene(), visibility("BLIND", cap=0.99))
    assert result["requalified_confidence"] == 0.20


def test_stale_zone_caps_confidence_and_forbids_fresh_zone_claim():
    result = requalify_packet(packet("UP", 0.99), zone("ACCEPTANCE_ZONE", "STALE"), verdict("PULLBACK_ABSORBED", 0.99), scene(), visibility("TACTICAL_OK", cap=0.99))
    assert result["requalified_confidence"] == 0.40
    assert "FRESH_ZONE" in result["forbidden_claims"]


def test_confidence_takes_min_packet_strength_price_confidence_and_cap():
    result = requalify_packet(packet("UP", 0.76), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED", 0.64), scene(), visibility("TACTICAL_OK", cap=0.50))
    assert result["requalified_confidence"] == 0.50


def test_source_stack_composed_when_not_explicit():
    result = requalify_packet(packet("UP"), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED"), scene(), visibility("TACTICAL_OK", "FORCE_SNAPSHOT_DERIVED", 0.77))
    assert result["source_stack"] == "FORCE_SNAPSHOT_DERIVED|TACTICAL_OK|cap=0.77"


def test_source_stack_propagated_when_explicit():
    result = requalify_packet(packet("UP"), zone("ACCEPTANCE_ZONE"), verdict("PULLBACK_ABSORBED"), scene(), visibility(stack="B9_RAW|FIELD_MEMORY|cap=0.35"))
    assert result["source_stack"] == "B9_RAW|FIELD_MEMORY|cap=0.35"


def test_lowercase_inputs_are_normalized():
    result = requalify_packet(packet("up"), zone("acceptance_zone"), verdict("pullback_absorbed"), scene(), visibility())
    assert_event(result, "RELEASE_UP_PULLBACK_ABSORBED", "RULE_01_RELEASE_UP_PULLBACK_ABSORBED")


def test_rule_order_prefers_rule_4_over_generic_rule_7_for_down_absorption():
    result = requalify_packet(packet("DOWN"), zone("ABSORPTION_ZONE"), verdict("EFFORT_WITHOUT_RESULT"), scene(), visibility())
    assert result["requalification_rule"] == "RULE_04_RELEASE_DOWN_LOWER_ZONE_DEFENDED"


def test_never_returns_auto_execution_claim():
    result = requalify_packet(packet("UP"), zone("ACCEPTANCE_ZONE"), verdict("ACCEPTED"), scene(), visibility())
    assert "AUTO_EXECUTION" in result["forbidden_claims"]
    assert "BUY" not in result["requalified_event"]
    assert "SELL" not in result["requalified_event"]
