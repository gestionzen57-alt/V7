"""Patch helper for integrating B8 into pf_confluence_gravity.py.

Copy the function into pf_confluence_gravity.py or import it from the B8 module
if the project layout allows that without circular dependencies.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Dict


def enrich_with_b8_cross_validation(
    confluence_state: Dict,
    cross_validation_state: Dict,
) -> Dict:
    """Attach B8 driver context to an existing confluence state.

    This function is read-only with respect to inputs. It does not decide,
    trade, censor, or overwrite previous confluence data; it only adds a
    named driver context and contradictions when B8 sees them.
    """

    enriched = deepcopy(confluence_state or {})
    driver_detection = cross_validation_state.get("driver_detection", {})
    metrics = cross_validation_state.get("metrics", {})

    enriched["b8_cross_symbol_validation"] = {
        "symbol": cross_validation_state.get("symbol"),
        "timeframe": cross_validation_state.get("timeframe"),
        "driver_detection": driver_detection,
        "metrics": metrics,
        "cross_pair_details": cross_validation_state.get("cross_pair_details", {}),
        "alert_triggered": cross_validation_state.get("alert_triggered", False),
        "alert_type": cross_validation_state.get("alert_type"),
    }

    if cross_validation_state.get("alert_triggered"):
        enriched["b8_alert"] = {
            "type": cross_validation_state.get("alert_type"),
            "message": "Driver confirmed: "
            f"{driver_detection.get('primary_driver', 'UNKNOWN')}",
            "confidence": driver_detection.get("confidence"),
        }

    # This tag is explanatory context for the dashboard/mapper, not a decision.
    primary_driver = driver_detection.get("primary_driver")
    if primary_driver and primary_driver != "MIXED":
        enriched["driver_context_note"] = (
            "B8 names the likely cross-symbol driver; trader arbitrates."
        )

    return enriched
