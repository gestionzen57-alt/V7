#!/usr/bin/env python3
"""PowerFlow V7.6 minimal terrain context builder.

This module is standalone and intentionally does not read dashboard, Telegram,
or any display surface. It normalizes evidence into the context fields consumed
by pf_packet_requalification_once.requalify_packet.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

UNKNOWN = "UNKNOWN"

DATA_VISIBILITY_ALIASES = {
    "FULL_STACK_VISIBLE": "FULL_READING",
    "TACTICAL_OK": "FULL_READING",
    "DATA_PARTIAL": "READING_PARTIAL",
    "DATA_BLIND": "READING_PARTIAL",
    "DATA_UNKNOWN": "UNKNOWN",
}

ZONE_STATUS_ALIASES = {
    "LOWER_ZONE_ACTIVE": "LOWER_RANGE_ACTIVE",
    "HIGH_ZONE_ACTIVE": "HIGH_RANGE_ACTIVE",
    "ABOVE_ZONE": "ACCEPTANCE_ABOVE_ZONE",
    "BELOW_ZONE": "ACCEPTANCE_BELOW_ZONE",
    "MID_ZONE": "RANGE_MID_NOISE",
    "RANGE_ACTIVE": "RANGE_MID_NOISE",
}

PRICE_ALIASES = {"PRICE_UNKNOWN": "UNKNOWN"}
PROPAGATION_ALIASES = {"PROPAGATION_UNKNOWN": "UNKNOWN"}
TEXTURE_ALIASES = {"TEXTURE_UNKNOWN": "UNKNOWN"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _upper(value: Any, fallback: str = UNKNOWN) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text.upper() if text else fallback


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _first_present(evidence: Dict[str, Any], *keys: str, fallback: Any = UNKNOWN) -> Any:
    for key in keys:
        if key in evidence and evidence[key] not in (None, ""):
            return evidence[key]
    return fallback


def _derive_raw_bias(evidence: Dict[str, Any]) -> str:
    direct = _upper(_first_present(evidence, "raw_bias", "bias", "packet_type", "alert_type", fallback=""), "")
    if direct in {"PAIR_UP", "PAIR_DOWN", "HOT", "WATCH", "ACTIVE", "B3_B2", "B3_B4_P1"}:
        return direct
    if _as_bool(evidence.get("b3_active")) and _as_bool(evidence.get("b4_active")) and _as_bool(evidence.get("p1_active")):
        return "B3_B4_P1"
    if _as_bool(evidence.get("b3_active")) and _as_bool(evidence.get("b2_active")):
        return "B3_B2"
    return UNKNOWN


def _derive_data_visibility(evidence: Dict[str, Any], risks: List[str]) -> str:
    provided = DATA_VISIBILITY_ALIASES.get(_upper(evidence.get("data_visibility"), ""), _upper(evidence.get("data_visibility"), ""))
    m1_missing = evidence.get("m1_available") is False or _as_bool(evidence.get("m1_missing"))
    stale = _as_bool(evidence.get("packets_stale")) or _as_bool(evidence.get("stale"))
    temporal_gaps = _as_bool(evidence.get("temporal_gaps"))
    event_offset = _as_bool(evidence.get("event_time_offset"))
    b8_degraded = _as_bool(evidence.get("b8_degraded")) or _as_bool(evidence.get("cross_validation_degraded"))

    if m1_missing:
        risks.extend([risk for risk in ["M1_MISSING", "READING_PARTIAL"] if risk not in risks])
    if stale:
        risks.extend([risk for risk in ["PACKETS_STALE", "READING_PARTIAL"] if risk not in risks])
    if temporal_gaps and "TEMPORAL_GAPS" not in risks:
        risks.append("TEMPORAL_GAPS")
    if event_offset and "EVENT_TIME_OFFSET" not in risks:
        risks.append("EVENT_TIME_OFFSET")
    if b8_degraded:
        for risk in ["B8_DEGRADED", "CROSS_VALIDATION_DEGRADED"]:
            if risk not in risks:
                risks.append(risk)

    if m1_missing and stale:
        return "M1_MISSING_PACKETS_STALE"
    if m1_missing:
        return "M1_MISSING"
    if stale:
        return "PACKETS_STALE"
    if temporal_gaps:
        return "TEMPORAL_GAPS"
    if event_offset:
        return "EVENT_TIME_OFFSET"
    if b8_degraded:
        return "B8_DEGRADED"
    if provided:
        return provided
    return "FULL_READING"


def build_terrain_context(evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize partial evidence into a fallback-safe terrain context."""
    evidence = evidence or {}
    risks = list(evidence.get("technical_risks") or [])
    generated_at = str(_first_present(evidence, "generated_at", fallback=_utc_now()))
    low = evidence.get("current_zone_low")
    high = evidence.get("current_zone_high")
    zone = _first_present(evidence, "current_zone", "zone", fallback=None)
    if not zone and low is not None and high is not None:
        zone = f"{low}-{high}"
    if not zone:
        zone = UNKNOWN

    return {
        "schema_version": "terrain_context_v76_0",
        "symbol": str(_first_present(evidence, "symbol", fallback=UNKNOWN)),
        "generated_at": generated_at,
        "market_time": str(_first_present(evidence, "market_time", "event_at", fallback=generated_at)),
        "film_state": _upper(_first_present(evidence, "film_state", "phase", fallback=UNKNOWN)),
        "last_structural_event": _upper(_first_present(evidence, "last_structural_event", "last_event", fallback=UNKNOWN)),
        "last_structural_direction": _upper(_first_present(evidence, "last_structural_direction", "last_direction", fallback=UNKNOWN)),
        "last_structural_time": str(_first_present(evidence, "last_structural_time", fallback=UNKNOWN)),
        "current_zone": str(zone),
        "current_zone_low": low,
        "current_zone_high": high,
        "current_zone_status": ZONE_STATUS_ALIASES.get(_upper(_first_present(evidence, "current_zone_status", "zone_status", fallback=UNKNOWN)), _upper(_first_present(evidence, "current_zone_status", "zone_status", fallback=UNKNOWN))),
        "current_move_role": _upper(_first_present(evidence, "current_move_role", "move_role", fallback=UNKNOWN)),
        "raw_bias": _derive_raw_bias(evidence),
        "price_confirmation": PRICE_ALIASES.get(_upper(_first_present(evidence, "price_confirmation", fallback=UNKNOWN)), _upper(_first_present(evidence, "price_confirmation", fallback=UNKNOWN))),
        "propagation_state": PROPAGATION_ALIASES.get(_upper(_first_present(evidence, "propagation_state", "b7_state", fallback=UNKNOWN)), _upper(_first_present(evidence, "propagation_state", "b7_state", fallback=UNKNOWN))),
        "detachment_texture": TEXTURE_ALIASES.get(_upper(_first_present(evidence, "detachment_texture", "b7_texture", fallback=UNKNOWN)), _upper(_first_present(evidence, "detachment_texture", "b7_texture", fallback=UNKNOWN))),
        "data_visibility": _derive_data_visibility(evidence, risks),
        "technical_risks": risks,
        "evidence_refs": list(evidence.get("evidence_refs") or []),
        # Carry through raw booleans used by the requalification patch.
        "b2_active": _as_bool(evidence.get("b2_active")),
        "b3_active": _as_bool(evidence.get("b3_active")),
        "b4_active": _as_bool(evidence.get("b4_active")),
        "p1_active": _as_bool(evidence.get("p1_active")),
        "m1_missing": _as_bool(evidence.get("m1_missing")),
        "packets_stale": _as_bool(evidence.get("packets_stale")),
        "b8_degraded": _as_bool(evidence.get("b8_degraded")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a minimal PowerFlow V7.6 terrain context from evidence JSON.")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    with open(args.input, "r", encoding="utf-8") as handle:
        evidence = json.load(handle)
    context = build_terrain_context(evidence)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as handle:
        json.dump(context, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return 0



# V7.6.2 legacy evidence adapter wrapper
try:
    _v76_original_build_terrain_context = build_terrain_context

    def build_terrain_context(evidence):
        base_context = _v76_original_build_terrain_context(evidence)
        try:
            from pf_legacy_evidence_adapter_once import enrich_terrain_context_from_legacy
            return enrich_terrain_context_from_legacy(evidence, base_context)
        except Exception:
            return base_context
except NameError:
    pass


if __name__ == "__main__":
    raise SystemExit(main())
