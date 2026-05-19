"""B9 source constants for PowerFlow V7.6.7.

These constants make source quality visible to B6/B9 without creating a trade decision.
"""

from __future__ import annotations

SOURCE_MODE_RECOVERED_B9 = "RECOVERED_EXISTING_B9_SUMMARY"
SOURCE_MODE_FORCE_DERIVED = "FORCE_SNAPSHOT_DERIVED"
SOURCE_MODE_RAW_MT5_NATIVE = "RAW_TICK_PLUS_FORCE_CONTEXT"

FIELD_MEMORY_SOURCE_TAG = {
    "2026-05-06": SOURCE_MODE_RECOVERED_B9,
    "2026-05-07": SOURCE_MODE_FORCE_DERIVED,
    "2026-05-08": SOURCE_MODE_FORCE_DERIVED,
    "2026-05-09": SOURCE_MODE_FORCE_DERIVED,
    "2026-05-12": SOURCE_MODE_FORCE_DERIVED,
    "2026-05-13": SOURCE_MODE_FORCE_DERIVED,
    "2026-05-14": SOURCE_MODE_FORCE_DERIVED,
    "2026-05-15": SOURCE_MODE_FORCE_DERIVED,
}

MT5_RAW_IMPACT = {
    "BREAK_RETEST_FAILED": "VERY_HIGH",
    "HIGH_REJECTION_NODE": "VERY_HIGH",
    "FALSE_BIRTH": "VERY_HIGH",
    "EFFORT_WITHOUT_RESULT": "HIGH",
    "ABSORPTION_SHELF": "HIGH",
    "PROGRESSIVE_WAVE": "MEDIUM",
    "RELEASE_SCENE": "LOW",
}


def get_field_memory_source_tag(source_date: str) -> str:
    """Return source mode attached to a B6 field-memory source date."""
    return FIELD_MEMORY_SOURCE_TAG.get(str(source_date), SOURCE_MODE_FORCE_DERIVED)


def get_mt5_raw_impact(event_name: str) -> str:
    """Return expected impact of raw MT5 availability for an event family."""
    return MT5_RAW_IMPACT.get(str(event_name), "UNKNOWN")


__all__ = [
    "SOURCE_MODE_RECOVERED_B9",
    "SOURCE_MODE_FORCE_DERIVED",
    "SOURCE_MODE_RAW_MT5_NATIVE",
    "FIELD_MEMORY_SOURCE_TAG",
    "MT5_RAW_IMPACT",
    "get_field_memory_source_tag",
    "get_mt5_raw_impact",
]
