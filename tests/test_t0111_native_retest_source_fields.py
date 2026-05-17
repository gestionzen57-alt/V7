from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t0111_native_retest_source_fields import (  # noqa: E402
    OUTCOME_ACCEPTED,
    OUTCOME_NOT_VISIBLE,
    OUTCOME_PENDING,
    OUTCOME_REJECTED,
    T0111_VERSION,
    enrich_moment_with_native_retest_source_fields,
    enrich_summary_with_native_retest_source_fields,
)


def test_missing_retest_is_not_visible():
    moment = {
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": "2026-05-15T08:01:00Z",
    }
    out = enrich_moment_with_native_retest_source_fields(moment)
    assert out["retest_source_fields_version"] == T0111_VERSION
    assert out["retest_touch_count"] == 0
    assert out["retest_outcome_hint"] == OUTCOME_NOT_VISIBLE
    assert out["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_NOT_VISIBLE"


def test_explicit_pending_gets_minimum_touch():
    moment = {
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": "2026-05-15T08:01:00Z",
        "retest_status": "PENDING",
    }
    out = enrich_moment_with_native_retest_source_fields(moment)
    assert out["retest_outcome_hint"] == OUTCOME_PENDING
    assert out["retest_touch_count"] == 1
    assert out["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_EXPLICIT"
    assert out["zone_memory"]["retest_status"] == OUTCOME_PENDING


def test_explicit_accepted_gets_accepted_hint():
    moment = {
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": "2026-05-15T08:02:00Z",
        "retest_status": "ACCEPTED",
    }
    out = enrich_moment_with_native_retest_source_fields(moment)
    assert out["retest_outcome_hint"] == OUTCOME_ACCEPTED
    assert out["retest_touch_count"] == 1
    assert out["retest_acceptance_dwell_seconds"] == 120.0


def test_explicit_failed_gets_rejection_hint_and_speed_when_raw_delta_available():
    moment = {
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": "2026-05-15T08:01:00Z",
        "retest_status": "FAILED",
        "raw_delta_pips": -5,
    }
    out = enrich_moment_with_native_retest_source_fields(moment)
    assert out["retest_outcome_hint"] == OUTCOME_REJECTED
    assert out["retest_rejection_speed_pips_per_min"] == 5.0


def test_zone_memory_is_canonicalized():
    moment = {
        "time_start": "2026-05-15T08:00:00Z",
        "time_end": "2026-05-15T08:03:00Z",
        "zone_memory": {
            "touch_count": 3,
            "last_tested": "2026-05-15T07:58:00Z",
            "retest_status": "ACCEPTED",
            "retest_first_touch_time": "2026-05-15T07:57:00Z",
        },
    }
    out = enrich_moment_with_native_retest_source_fields(moment)
    assert out["retest_touch_count"] == 3
    assert out["retest_delay_seconds"] == 120.0
    assert out["retest_first_touch_time"].startswith("2026-05-15T07:57:00")
    assert out["retest_last_touch_time"].startswith("2026-05-15T07:58:00")
    assert out["retest_outcome_hint"] == OUTCOME_ACCEPTED


def test_summary_enrichment_preserves_moments_count():
    summary = {
        "moments": [
            {"time_start": "2026-05-15T08:00:00Z", "time_end": "2026-05-15T08:01:00Z"},
            {"time_start": "2026-05-15T08:02:00Z", "time_end": "2026-05-15T08:03:00Z", "retest_status": "PENDING"},
        ]
    }
    out = enrich_summary_with_native_retest_source_fields(summary)
    assert len(out["moments"]) == 2
    assert out["b9_sequence_summarizer_native_fields"]["version"] == T0111_VERSION
    assert all("retest_outcome_hint" in m for m in out["moments"])


def test_no_decision_language_in_helper():
    text = (ROOT / "pf_t0111_native_retest_source_fields.py").read_text(encoding="utf-8").lower()
    forbidden = ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]
    for phrase in forbidden:
        assert phrase not in text
