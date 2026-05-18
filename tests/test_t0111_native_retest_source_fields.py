"""Tests T0111 — pf_t0111_native_retest_source_fields.py

Rules verified:
    - Read-only: no DB, no dashboard, no Telegram, no BUY/SELL
    - No probability of success in outputs
    - Source-aware: proxy → PROXY_CAUTION confidence
    - Additive: existing keys never removed
    - Fallback: empty / missing moment handled gracefully
    - All contract fields present after enrichment
    - zone_memory sub-dict updated correctly
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running from tests/ or from repo root
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from pf_t0111_native_retest_source_fields import (
    T0111_VERSION,
    RETEST_OUTCOME_ACCEPTED,
    RETEST_OUTCOME_FAILED,
    RETEST_OUTCOME_NOT_VISIBLE,
    RETEST_OUTCOME_PENDING,
    RETEST_OUTCOME_PARTIAL,
    enrich_moment_with_native_retest_source_fields,
    enrich_moments_batch,
    probe,
)

# ─── Contract fields that must be present after enrichment ───────────────────

CONTRACT_FIELDS = [
    "retest_source_fields_version",
    "retest_touch_count",
    "retest_first_touch_time",
    "retest_last_touch_time",
    "retest_delay_seconds",
    "retest_acceptance_dwell_seconds",
    "retest_rejection_speed_pips_per_min",
    "retest_zone_distance_pips",
    "retest_outcome_hint",
    "retest_source_field_confidence",
]

FORBIDDEN_TERMS = [
    "BUY", "SELL", "probability of success", "success probability",
    "trade recommendation", "entry signal",
]


def _base_moment(**kwargs):
    """Minimal valid moment dict."""
    base = {
        "moment_id": "T009M-001",
        "moment_type": "T009_MOMENT_GENERIC_BATTLEFIELD",
        "label_fr": "Zone de friction locale",
        "time_start": "2026-05-15T09:00:00Z",
        "time_end": "2026-05-15T09:30:00Z",
        "zone_low": 1.26800,
        "zone_high": 1.26900,
        "center_start": 1.26850,
        "center_end": 1.26855,
        "center_delta_pips": 0.5,
        "center_range_pips": 3.2,
        "source_mode": "M1_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED",
        "confidence_cap": 0.6,
        "retest_status": "NOT_ISOLATED",
        "effort_role": "LOCAL_TRACE",
        "memory_state": "LOCAL_MEMORY_ACTIVE",
        "zone_memory": {
            "zone_low": 1.26800,
            "zone_high": 1.26900,
            "zone_center_start": 1.26850,
            "zone_center_end": 1.26855,
            "first_seen": "2026-05-15T09:00:00Z",
            "last_seen": "2026-05-15T09:30:00Z",
            "last_tested": None,
            "state": "LOCAL_MEMORY_ACTIVE",
            "event_count": 4,
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.6,
        },
    }
    base.update(kwargs)
    return base


# ─── 1. Contract: all fields present ─────────────────────────────────────────

def test_all_contract_fields_present():
    result = enrich_moment_with_native_retest_source_fields(_base_moment())
    missing = [f for f in CONTRACT_FIELDS if f not in result]
    assert missing == [], f"Missing contract fields: {missing}"


def test_version_tag_correct():
    result = enrich_moment_with_native_retest_source_fields(_base_moment())
    assert result["retest_source_fields_version"] == T0111_VERSION


# ─── 2. Anti-signal: no forbidden language ───────────────────────────────────

def test_no_forbidden_language_in_output():
    import json
    result = enrich_moment_with_native_retest_source_fields(_base_moment())
    text = json.dumps(result).upper()
    hits = [t for t in FORBIDDEN_TERMS if t.upper() in text]
    assert hits == [], f"Forbidden language found: {hits}"


def test_probe_no_forbidden_language():
    """Probe values must not contain forbidden signal language.
    Keys like 'no_buy_sell' are doctrine descriptors, not signal language.
    We check string values only.
    """
    import json
    p = probe()
    # Serialize only the values (not the keys)
    values_text = json.dumps(list(p.values())).upper()
    # These terms are forbidden in *values*, not in doctrine key names
    value_forbidden = ["PROBABILITY OF SUCCESS", "SUCCESS PROBABILITY",
                       "TRADE RECOMMENDATION", "ENTRY SIGNAL"]
    hits = [t for t in value_forbidden if t.upper() in values_text]
    assert hits == [], f"Forbidden language in probe values: {hits}"


# ─── 3. Source-aware confidence ──────────────────────────────────────────────

def test_proxy_source_gives_proxy_caution():
    m = _base_moment(source_mode="M1_BAR_PROXY", data_visibility="RECONSTRUCTED")
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_source_field_confidence"] == "PROXY_CAUTION"


def test_raw_source_gives_high_confidence():
    m = _base_moment(source_mode="ONTICK_RAW", data_visibility="LIVE", confidence_cap=0.9)
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_source_field_confidence"] == "HIGH"


def test_low_confidence_cap_gives_low_confidence():
    m = _base_moment(source_mode="HISTORICAL_RAW", data_visibility="OK", confidence_cap=0.3)
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_source_field_confidence"] == "LOW"


# ─── 4. Touch count inference ────────────────────────────────────────────────

def test_no_touch_on_generic_battlefield():
    m = _base_moment(moment_type="T009_MOMENT_GENERIC_BATTLEFIELD", retest_status="NOT_ISOLATED")
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_touch_count"] == 0


def test_touch_on_break_retest_failed():
    m = _base_moment(
        moment_type="T009_MOMENT_BREAK_RETEST_FAILED",
        retest_status="FAILED",
        center_delta_pips=-5.0,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_touch_count"] >= 1


def test_touch_on_retrace_decision_area():
    m = _base_moment(
        moment_type="T009_MOMENT_RETRACE_DECISION_AREA",
        retest_status="PENDING",
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_touch_count"] >= 1


def test_existing_touch_count_preserved_if_positive():
    m = _base_moment(
        moment_type="T009_MOMENT_RETRACE_DECISION_AREA",
        retest_touch_count=3,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_touch_count"] == 3


# ─── 5. Outcome hint ─────────────────────────────────────────────────────────

def test_outcome_not_visible_when_no_touch():
    m = _base_moment(moment_type="T009_MOMENT_GENERIC_BATTLEFIELD", retest_status="NOT_ISOLATED")
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_outcome_hint"] == RETEST_OUTCOME_NOT_VISIBLE


def test_outcome_failed_for_break_retest_failed():
    m = _base_moment(
        moment_type="T009_MOMENT_BREAK_RETEST_FAILED",
        retest_status="FAILED",
        center_delta_pips=-5.0,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_outcome_hint"] == RETEST_OUTCOME_FAILED


def test_outcome_pending_for_breakout_pending():
    m = _base_moment(
        moment_type="T009_MOMENT_BREAKOUT_PENDING_RETEST",
        retest_status="PENDING",
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_outcome_hint"] == RETEST_OUTCOME_PENDING


def test_outcome_accepted_for_accepted_status():
    m = _base_moment(
        moment_type="T009_MOMENT_CENTER_MIGRATION_UP",
        retest_status="ACCEPTED",
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_outcome_hint"] == RETEST_OUTCOME_ACCEPTED


def test_existing_canonical_outcome_preserved():
    m = _base_moment(
        moment_type="T009_MOMENT_GENERIC_BATTLEFIELD",
        retest_outcome_hint="RETEST_OUTCOME_PARTIAL",
        retest_status="ACTIVE_RETEST",
        retest_touch_count=1,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_outcome_hint"] == RETEST_OUTCOME_PARTIAL


def test_legacy_bare_failed_normalized():
    m = _base_moment(
        retest_outcome_hint="FAILED",
        retest_touch_count=1,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_outcome_hint"] == RETEST_OUTCOME_FAILED


# ─── 6. Rejection speed ──────────────────────────────────────────────────────

def test_rejection_speed_computed_for_failed_retest():
    m = _base_moment(
        moment_type="T009_MOMENT_BREAK_RETEST_FAILED",
        retest_status="FAILED",
        center_delta_pips=-8.0,
        time_start="2026-05-15T09:00:00Z",
        time_end="2026-05-15T09:04:00Z",  # 4 min
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    spd = result["retest_rejection_speed_pips_per_min"]
    assert spd is not None and spd > 0


def test_rejection_speed_none_for_non_failed():
    m = _base_moment(
        moment_type="T009_MOMENT_ABSORPTION_SHELF",
        retest_status="NOT_ISOLATED",
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_rejection_speed_pips_per_min"] is None


# ─── 7. Zone distance ────────────────────────────────────────────────────────

def test_zone_distance_computed():
    m = _base_moment(
        center_end=1.26920,
        zone_low=1.26800,
        zone_high=1.26900,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    dist = result["retest_zone_distance_pips"]
    assert dist is not None
    # center_end(1.26920) - zone_mid(1.26850) = 0.00070 = 7.0 pips
    assert abs(dist - 7.0) < 0.5


def test_zone_distance_none_when_zone_missing():
    m = _base_moment(zone_low=None, zone_high=None)
    result = enrich_moment_with_native_retest_source_fields(m)
    assert result["retest_zone_distance_pips"] is None


# ─── 8. zone_memory enrichment ───────────────────────────────────────────────

def test_zone_memory_touch_count_updated():
    m = _base_moment(
        moment_type="T009_MOMENT_RETRACE_DECISION_AREA",
        retest_status="PENDING",
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    zm = result.get("zone_memory", {})
    assert zm.get("touch_count", 0) >= 1


def test_zone_memory_retest_status_set():
    m = _base_moment(
        moment_type="T009_MOMENT_BREAK_RETEST_FAILED",
        retest_status="FAILED",
        center_delta_pips=-5.0,
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    zm = result.get("zone_memory", {})
    assert zm.get("retest_status") == "RETEST_FAILED"


def test_zone_memory_not_touched_when_no_touch():
    m = _base_moment(moment_type="T009_MOMENT_GENERIC_BATTLEFIELD")
    original_zm = dict(m["zone_memory"])
    result = enrich_moment_with_native_retest_source_fields(m)
    zm = result.get("zone_memory", {})
    # last_tested should still be None (was None, no touch detected)
    assert zm.get("last_tested") == original_zm.get("last_tested")


# ─── 9. Additive: original keys preserved ────────────────────────────────────

def test_original_keys_not_removed():
    m = _base_moment()
    original_keys = set(m.keys())
    result = enrich_moment_with_native_retest_source_fields(m)
    missing = original_keys - set(result.keys())
    assert missing == set(), f"Keys removed: {missing}"


def test_input_not_mutated():
    m = _base_moment()
    original_copy = dict(m)
    enrich_moment_with_native_retest_source_fields(m)
    assert m == original_copy


# ─── 10. Empty / edge cases ──────────────────────────────────────────────────

def test_empty_moment_does_not_raise():
    result = enrich_moment_with_native_retest_source_fields({})
    for field in CONTRACT_FIELDS:
        assert field in result, f"Missing field on empty input: {field}"


def test_batch_empty_list():
    result = enrich_moments_batch([])
    assert result == []


def test_batch_preserves_order_and_count():
    moments = [_base_moment(moment_id=f"T009M-{i:03d}") for i in range(5)]
    result = enrich_moments_batch(moments)
    assert len(result) == 5
    for i, r in enumerate(result):
        assert r["moment_id"] == f"T009M-{i:03d}"


# ─── 11. probe() ─────────────────────────────────────────────────────────────

def test_probe_returns_expected_keys():
    p = probe()
    for key in ("version", "state", "read_only", "no_db_write", "no_buy_sell", "fields_added"):
        assert key in p


def test_probe_version_matches():
    assert probe()["version"] == T0111_VERSION


def test_probe_read_only_true():
    assert probe()["read_only"] is True
    assert probe()["no_db_write"] is True
    assert probe()["no_buy_sell"] is True


# ─── 12. Timing coherence ────────────────────────────────────────────────────

def test_delay_seconds_non_negative():
    m = _base_moment(
        moment_type="T009_MOMENT_RETRACE_DECISION_AREA",
        retest_status="PENDING",
        time_start="2026-05-15T09:00:00Z",
        time_end="2026-05-15T09:15:00Z",
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    delay = result["retest_delay_seconds"]
    if delay is not None:
        assert delay >= 0


def test_dwell_seconds_for_decision_area():
    m = _base_moment(
        moment_type="T009_MOMENT_RETRACE_DECISION_AREA",
        retest_status="PENDING",
        time_start="2026-05-15T09:00:00Z",
        time_end="2026-05-15T09:10:00Z",  # 600s
    )
    result = enrich_moment_with_native_retest_source_fields(m)
    dwell = result["retest_acceptance_dwell_seconds"]
    assert dwell is not None
    assert abs(dwell - 600.0) < 1.0
