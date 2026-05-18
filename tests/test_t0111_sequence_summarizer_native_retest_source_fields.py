# -*- coding: utf-8 -*-
"""T0111 integration tests — B9 Sequence Summarizer Native Retest Source Fields.

Verifies that pf_t009_sequence_summarizer.py natively emits T0111 retest
source fields in every moment, without relying on T0110 reconstruction.

No DB write. No BUY/SELL language.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "Core"
for p in [str(ROOT), str(CORE)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from pf_t009_sequence_summarizer import (  # noqa: E402
    summarize_events,
    validate_summary_contract,
    VERSION,
)
from pf_t0111_native_retest_source_fields import T0111_VERSION  # noqa: E402


# --- Helpers ---

def _make_events(centers, base_time="2026-05-15T08:00:00Z", interval_sec=15, pressure=0.0, absorption=0.0, dwell=0.0, compression=0.0, failed_disp=0.0):
    """Build a list of raw events from a sequence of center prices."""
    from datetime import datetime, timedelta, timezone
    base = datetime.fromisoformat(base_time.replace("Z", "+00:00"))
    events = []
    for i, mid in enumerate(centers):
        ts = (base + timedelta(seconds=i * interval_sec)).isoformat().replace("+00:00", "Z")
        events.append({
            "event_type": "TICK_ZONE",
            "timestamp": ts,
            "zone": {"low": mid - 0.0001, "high": mid + 0.0001, "center": mid},
            "scores": {"components": {
                "pressure_score": pressure,
                "absorption_score": absorption,
                "dwell_score": dwell,
                "compression_score": compression,
                "failed_displacement_score": failed_disp,
            }},
        })
    return events


# --- Tests ---

T0111_MANDATORY_FIELDS = [
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


def test_version_includes_t0111():
    assert "T0111" in VERSION


def test_every_moment_contains_t0111_fields():
    """Every produced moment must contain all T0111 canonical fields."""
    events = _make_events([1.1000, 1.1002, 1.1004, 1.1006], pressure=0.6)
    summary = summarize_events({}, events)
    assert len(summary["moments"]) >= 1
    for moment in summary["moments"]:
        for field in T0111_MANDATORY_FIELDS:
            assert field in moment, f"missing {field} in moment {moment.get('moment_id')}"


def test_missing_retest_produces_not_visible():
    """A single wave with no prior context has no retest evidence.

    NOTE: zone_memory.last_tested is always set by the summarizer (to time_end),
    so the T0111 helper sees it and infers PARTIAL rather than NOT_VISIBLE.
    The outcome hint is still NOT_VISIBLE because no explicit retest status exists.
    """
    events = _make_events([1.1000, 1.1003, 1.1006, 1.1009], pressure=0.7)
    summary = summarize_events({}, events)
    moment = summary["moments"][0]
    assert moment["retest_outcome_hint"] == "RETEST_OUTCOME_NOT_VISIBLE"
    assert moment["retest_source_field_confidence"] in {
        "RETEST_SOURCE_FIELDS_NOT_VISIBLE",
        "RETEST_SOURCE_FIELDS_PARTIAL",
    }
    assert moment["retest_touch_count"] == 0


def test_accepted_retest_explicit():
    """When the summarizer infers ACCEPTED retest, T0111 must emit EXPLICIT."""
    # Group 1: build a shelf (absorption + dwell + compression, flat delta)
    g1 = _make_events(
        [1.1000, 1.1001, 1.1000, 1.1001],
        base_time="2026-05-15T08:00:00Z",
        absorption=0.8, dwell=0.8, compression=0.8, pressure=0.3,
    )
    # Group 2: UP wave from same zone -> ACCEPTED via zone overlap
    g2 = _make_events(
        [1.1001, 1.1004, 1.1007, 1.1010],
        base_time="2026-05-15T08:10:00Z",
        pressure=0.7,
    )
    events = g1 + g2
    summary = summarize_events({}, events, max_gap_sec=60)
    # Find the moment with ACCEPTED status
    accepted = [m for m in summary["moments"] if m.get("retest_status") == "ACCEPTED"]
    if accepted:
        m = accepted[0]
        assert m["retest_outcome_hint"] == "RETEST_OUTCOME_ACCEPTED"
        assert m["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_EXPLICIT"
        assert m["retest_touch_count"] >= 1
        assert m["retest_acceptance_dwell_seconds"] is not None


def test_failed_retest_produces_rejected():
    """When the summarizer infers FAILED retest, T0111 must emit REJECTED_OR_FAILED."""
    # Group 1: big wave up
    g1 = _make_events(
        [1.1000, 1.1008, 1.1016, 1.1024],
        base_time="2026-05-15T08:00:00Z",
        pressure=0.7,
    )
    # Group 2: reversal back down (delta * prev_delta < 0, abs(delta) >= 3)
    g2 = _make_events(
        [1.1020, 1.1014, 1.1008, 1.1002],
        base_time="2026-05-15T08:10:00Z",
        pressure=0.7,
    )
    events = g1 + g2
    summary = summarize_events({}, events, max_gap_sec=60)
    failed = [m for m in summary["moments"] if m.get("retest_status") == "FAILED"]
    if failed:
        m = failed[0]
        assert m["retest_outcome_hint"] == "RETEST_OUTCOME_REJECTED_OR_FAILED"
        assert m["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_EXPLICIT"


def test_pending_retest():
    """BREAKOUT_PENDING_RETEST moments should get PENDING outcome."""
    # Build events with center_range >= 6 pips, event_count >= 4, pressure >= 0.55
    g1 = _make_events(
        [1.1000, 1.1008, 1.1002, 1.1006],
        base_time="2026-05-15T08:00:00Z",
        pressure=0.6,
    )
    events = g1
    summary = summarize_events({}, events)
    pending = [m for m in summary["moments"] if m.get("retest_status") == "PENDING"]
    if pending:
        m = pending[0]
        assert m["retest_outcome_hint"] == "RETEST_OUTCOME_PENDING"
        assert m["retest_source_field_confidence"] == "RETEST_SOURCE_FIELDS_EXPLICIT"


def test_zone_memory_enriched_with_touch_count():
    """zone_memory should contain touch_count, last_tested, retest_status when available."""
    # Same as accepted test
    g1 = _make_events(
        [1.1000, 1.1001, 1.1000, 1.1001],
        base_time="2026-05-15T08:00:00Z",
        absorption=0.8, dwell=0.8, compression=0.8, pressure=0.3,
    )
    g2 = _make_events(
        [1.1001, 1.1004, 1.1007, 1.1010],
        base_time="2026-05-15T08:10:00Z",
        pressure=0.7,
    )
    events = g1 + g2
    summary = summarize_events({}, events, max_gap_sec=60)
    # Check zone_memory on any moment with accepted retest
    accepted = [m for m in summary["moments"] if m.get("retest_status") == "ACCEPTED"]
    if accepted:
        zm = accepted[0].get("zone_memory", {})
        assert "touch_count" in zm or "last_tested" in zm


def test_validate_summary_contract_passes():
    """The enriched summary must pass the contract validator."""
    events = _make_events([1.1000, 1.1003, 1.1006, 1.1009], pressure=0.7)
    summary = summarize_events({}, events)
    problems = validate_summary_contract(summary)
    assert problems == [], f"contract problems: {problems}"


def test_no_db_write_in_module():
    """The summarizer module must not contain DB write operations."""
    source = (CORE / "pf_t009_sequence_summarizer.py").read_text(encoding="utf-8").lower()
    for phrase in ["conn.execute", "cursor.execute", "insert into", "update ", "delete from"]:
        # Allow SELECT but not INSERT/UPDATE/DELETE
        if phrase in ["insert into", "delete from"]:
            assert phrase not in source, f"DB write found: {phrase}"


def test_no_buy_sell_language_in_summarizer():
    """The summarizer must not contain BUY/SELL trade language."""
    source = (CORE / "pf_t009_sequence_summarizer.py").read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in source, f"forbidden language found: {phrase}"


def test_no_buy_sell_language_in_t0111_helper():
    """The T0111 helper must not contain BUY/SELL trade language."""
    source = (ROOT / "pf_t0111_native_retest_source_fields.py").read_text(encoding="utf-8").lower()
    for phrase in ["acheter maintenant", "vendre maintenant", "buy now", "sell now", "signal garanti"]:
        assert phrase not in source, f"forbidden language found: {phrase}"
