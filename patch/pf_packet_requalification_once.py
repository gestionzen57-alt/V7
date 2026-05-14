#!/usr/bin/env python3
"""PowerFlow V7.6 minimal terrain packet requalification patch.

Standalone, standard-library only, fallback-safe.

Integration TODO:
- Wire build_terrain_context(...) before this function when real evidence bus is available.
- Persist returned terrain packet to the existing dashboard surface only after consumers accept terrain_packet_v76_0.
- Keep raw_bias visible for audit, but never as the sole primary reading.
"""
from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

SCHEMA_VERSION = "terrain_packet_v76_0"
AUDIT_SCHEMA_VERSION = "terrain_packet_audit_v76_0"
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

DATA_VISIBILITY_VALUES = {
    "FULL_READING",
    "READING_PARTIAL",
    "MICROFILM_MISSING",
    "M1_MISSING",
    "PACKETS_STALE",
    "M1_MISSING_PACKETS_STALE",
    "CROSS_VALIDATION_DEGRADED",
    "B8_DEGRADED",
    "B5_B8_HONEST_UNKNOWN",
    "TEMPORAL_GAPS",
    "EVENT_TIME_OFFSET",
    "UNKNOWN",
}

PRICE_VALUES = {
    "PRICE_CONFIRMED",
    "PRICE_PENDING",
    "PRICE_FAILED",
    "PRICE_INVALIDATED",
    "PRICE_ACCEPTED_ABOVE_ZONE",
    "PRICE_ACCEPTED_BELOW_ZONE",
    "PRICE_REJECTED_HIGH",
    "PRICE_REJECTED_LOW",
    "PRICE_ABSORBED_PULLBACK",
    "UNKNOWN",
}

PROPAGATION_VALUES = {
    "LTF_ONLY",
    "LTF_MTF_RELAY",
    "MTF_HTF_RELAY",
    "FAILED_PROPAGATION",
    "RELAY_DEGRADING",
    "COUNTERFLOW_AGAINST_STRUCTURE",
    "UNKNOWN",
}

TEXTURE_VALUES = {
    "STRUCTURAL_DETACHMENT",
    "NOISY_DETACHMENT",
    "COUNTER_BREATH_DETACHMENT",
    "POST_RELEASE_DETACHMENT",
    "LATE_SESSION_DETACHMENT",
    "EXHAUSTION_DETACHMENT",
    "REJECTION_DETACHMENT",
    "FALSE_REACTION_DETACHMENT",
    "UNKNOWN",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _upper(value: Any, fallback: str = UNKNOWN) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text.upper() if text else fallback


def _append_unique(items: List[str], *values: str) -> None:
    for value in values:
        if value and value not in items:
            items.append(value)


def _has_any(value: str, tokens: Iterable[str]) -> bool:
    return any(token in value for token in tokens)


def _normalize_data_visibility(raw: Dict[str, Any], technical_risks: List[str]) -> str:
    provided = DATA_VISIBILITY_ALIASES.get(_upper(raw.get("data_visibility"), ""), _upper(raw.get("data_visibility"), ""))
    m1_missing = _as_bool(raw.get("m1_missing")) or raw.get("m1_available") is False or provided in {"M1_MISSING", "MICROFILM_MISSING"}
    stale = _as_bool(raw.get("packets_stale")) or _as_bool(raw.get("stale")) or provided == "PACKETS_STALE"
    temporal_gaps = _as_bool(raw.get("temporal_gaps")) or provided == "TEMPORAL_GAPS"
    event_offset = _as_bool(raw.get("event_time_offset")) or provided == "EVENT_TIME_OFFSET"
    b8_degraded = _as_bool(raw.get("b8_degraded")) or _as_bool(raw.get("cross_validation_degraded")) or provided in {"B8_DEGRADED", "CROSS_VALIDATION_DEGRADED"}
    honest_unknown = _as_bool(raw.get("b5_b8_honest_unknown")) or provided == "B5_B8_HONEST_UNKNOWN"

    if m1_missing:
        _append_unique(technical_risks, "M1_MISSING", "READING_PARTIAL")
    if stale:
        _append_unique(technical_risks, "PACKETS_STALE", "READING_PARTIAL")
    if temporal_gaps:
        _append_unique(technical_risks, "TEMPORAL_GAPS")
    if event_offset:
        _append_unique(technical_risks, "EVENT_TIME_OFFSET")
    if b8_degraded:
        _append_unique(technical_risks, "B8_DEGRADED", "CROSS_VALIDATION_DEGRADED")
    if honest_unknown:
        _append_unique(technical_risks, "B5_B8_HONEST_UNKNOWN")

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
    if honest_unknown:
        return "B5_B8_HONEST_UNKNOWN"
    if b8_degraded:
        return "B8_DEGRADED"
    if provided in DATA_VISIBILITY_VALUES:
        return provided
    if provided:
        _append_unique(technical_risks, f"UNRECOGNIZED_DATA_VISIBILITY:{provided}")
        return "UNKNOWN"
    return "FULL_READING"


def _normalize_price(raw: Dict[str, Any]) -> str:
    provided = PRICE_ALIASES.get(_upper(raw.get("price_confirmation"), ""), _upper(raw.get("price_confirmation"), ""))
    if provided in PRICE_VALUES:
        return provided
    if _as_bool(raw.get("price_invalidated")):
        return "PRICE_INVALIDATED"
    if _as_bool(raw.get("price_failed")):
        return "PRICE_FAILED"
    if _as_bool(raw.get("price_accepted_above_zone")):
        return "PRICE_ACCEPTED_ABOVE_ZONE"
    if _as_bool(raw.get("price_accepted_below_zone")):
        return "PRICE_ACCEPTED_BELOW_ZONE"
    if _as_bool(raw.get("price_rejected_high")):
        return "PRICE_REJECTED_HIGH"
    if _as_bool(raw.get("price_rejected_low")):
        return "PRICE_REJECTED_LOW"
    if _as_bool(raw.get("pullback_absorbed")) or _as_bool(raw.get("price_absorbed_pullback")):
        return "PRICE_ABSORBED_PULLBACK"
    if _as_bool(raw.get("price_confirmed")) or _as_bool(raw.get("price_accepted")):
        return "PRICE_CONFIRMED"
    if _as_bool(raw.get("no_price_displacement")) or _as_bool(raw.get("price_pending")):
        return "PRICE_PENDING"
    return "UNKNOWN"


def _normalize_raw_bias(raw: Dict[str, Any]) -> str:
    raw_bias = _upper(raw.get("raw_bias") or raw.get("bias") or raw.get("packet_type"))
    if raw_bias in {"PAIR_UP", "PAIR_DOWN", "HOT", "WATCH", "ACTIVE", "B3_B2", "B3_B4_P1"}:
        return raw_bias
    if _as_bool(raw.get("b3_active")) and _as_bool(raw.get("b2_active")) and not (_as_bool(raw.get("b4_active")) and _as_bool(raw.get("p1_active"))):
        return "B3_B2"
    if _as_bool(raw.get("b3_active")) and _as_bool(raw.get("b4_active")) and _as_bool(raw.get("p1_active")):
        return "B3_B4_P1"
    return "UNKNOWN"


def _zone_text(raw: Dict[str, Any]) -> str:
    current_zone = raw.get("current_zone")
    if current_zone:
        return str(current_zone)
    low = raw.get("current_zone_low")
    high = raw.get("current_zone_high")
    if low is not None and high is not None:
        return f"{low}-{high}"
    return UNKNOWN


def _zone_watch(raw: Dict[str, Any]) -> Tuple[str, str]:
    low = raw.get("current_zone_low")
    high = raw.get("current_zone_high")
    if low is not None and high is not None:
        return (
            f"ACCEPTANCE_ABOVE_{high}_OR_BREAK_BELOW_{low}",
            f"PRICE_RECLASSIFICATION_IF_ACCEPTANCE_FAILS_OR_ZONE_BREAKS_{low}_{high}",
        )
    return "PRICE_ACCEPTANCE_OR_REJECTION", "PRICE_INVALIDATES_CURRENT_ROLE"


def _initial_packet(raw: Dict[str, Any], technical_risks: List[str]) -> Dict[str, Any]:
    generated_at = raw.get("generated_at") or _utc_now()
    propagation = PROPAGATION_ALIASES.get(_upper(raw.get("propagation_state")), _upper(raw.get("propagation_state")))
    if propagation not in PROPAGATION_VALUES:
        propagation = "UNKNOWN"
    texture = TEXTURE_ALIASES.get(_upper(raw.get("detachment_texture")), _upper(raw.get("detachment_texture")))
    if texture not in TEXTURE_VALUES:
        texture = "UNKNOWN"

    data_visibility = _normalize_data_visibility(raw, technical_risks)
    price = _normalize_price(raw)
    raw_bias = _normalize_raw_bias(raw)
    watch, invalidation = _zone_watch(raw)

    return {
        "schema_version": SCHEMA_VERSION,
        "symbol": str(raw.get("symbol") or "UNKNOWN"),
        "generated_at": generated_at,
        "market_time": str(raw.get("market_time") or raw.get("event_at") or generated_at),
        "film_state": _upper(raw.get("film_state")),
        "last_structural_event": _upper(raw.get("last_structural_event")),
        "last_structural_direction": _upper(raw.get("last_structural_direction"), "UNKNOWN") if _upper(raw.get("last_structural_direction"), "UNKNOWN") in {"UP", "DOWN", "MIXED", "NONE", "UNKNOWN"} else "UNKNOWN",
        "last_structural_time": str(raw.get("last_structural_time") or "UNKNOWN"),
        "current_zone": _zone_text(raw),
        "current_zone_low": raw.get("current_zone_low"),
        "current_zone_high": raw.get("current_zone_high"),
        "current_zone_status": ZONE_STATUS_ALIASES.get(_upper(raw.get("current_zone_status"), "UNKNOWN"), _upper(raw.get("current_zone_status"), "UNKNOWN")),
        "current_move_role": _upper(raw.get("current_move_role")),
        "raw_bias": raw_bias,
        "qualified_bias": "UNKNOWN",
        "packet_quality": "UNKNOWN",
        "price_confirmation": price,
        "propagation_state": propagation,
        "detachment_texture": texture,
        "data_visibility": data_visibility,
        "watch_condition": watch,
        "invalidation_condition": invalidation,
        "technical_risks": technical_risks,
        "evidence_refs": list(raw.get("evidence_refs") or []),
    }


def requalify_packet(raw_packet: Dict[str, Any]) -> Dict[str, Any]:
    """Return a terrain_packet_v76_0 from a raw evidence packet.

    The function is deliberately deterministic and conservative: unknown or partial
    inputs produce explicit UNKNOWN/READING_PARTIAL states rather than exceptions.
    """
    raw = copy.deepcopy(raw_packet or {})
    technical_risks: List[str] = list(raw.get("technical_risks") or [])
    packet = _initial_packet(raw, technical_risks)
    rules: List[str] = []

    raw_bias = packet["raw_bias"]
    last_event = packet["last_structural_event"]
    film = packet["film_state"]
    zone_status = packet["current_zone_status"]
    price = packet["price_confirmation"]
    propagation = packet["propagation_state"]
    texture = packet["detachment_texture"]
    data_visibility = packet["data_visibility"]

    def set_result(rule: str, qualified: str, quality: str, price_override: str | None = None, watch: str | None = None, invalidation: str | None = None) -> None:
        packet["qualified_bias"] = qualified
        packet["packet_quality"] = quality
        if price_override:
            packet["price_confirmation"] = price_override
        if watch:
            packet["watch_condition"] = watch
        if invalidation:
            packet["invalidation_condition"] = invalidation
        _append_unique(rules, rule)

    # 1. Hard data/cross-validation rules remain visible and can dominate weak packets.
    b5_b8_weak = data_visibility in {"B8_DEGRADED", "B5_B8_HONEST_UNKNOWN", "CROSS_VALIDATION_DEGRADED"} or "B8_DEGRADED" in technical_risks
    data_degraded = data_visibility in {"READING_PARTIAL", "MICROFILM_MISSING", "M1_MISSING", "PACKETS_STALE", "M1_MISSING_PACKETS_STALE", "TEMPORAL_GAPS", "EVENT_TIME_OFFSET", "UNKNOWN"}

    # 2. B3/B2 and B3/B4/P1 before generic bias rules.
    b3 = _as_bool(raw.get("b3_active")) or raw_bias in {"B3_B2", "B3_B4_P1"}
    b2 = _as_bool(raw.get("b2_active")) or raw_bias == "B3_B2"
    b4 = _as_bool(raw.get("b4_active")) or raw_bias == "B3_B4_P1"
    p1 = _as_bool(raw.get("p1_active")) or raw_bias == "B3_B4_P1"

    if b3 and b2 and not (b4 and p1):
        set_result(
            "R_B3_B2_EVENT_STACK_NOT_RELEASE",
            "EVENT_STACK",
            "EVENT_STACK_NOT_RELEASE",
            "PRICE_PENDING" if price == "UNKNOWN" else None,
            "WAIT_FOR_B4_P1_PRICE_AND_PROPAGATION",
            "PRICE_REJECTION_OR_NOISE_CONFIRMS_EVENT_STACK_ONLY",
        )
    elif b3 and b4 and p1:
        if price in {"PRICE_CONFIRMED", "PRICE_ACCEPTED_ABOVE_ZONE", "PRICE_ACCEPTED_BELOW_ZONE"} and propagation != "FAILED_PROPAGATION" and not data_degraded:
            set_result(
                "R_B3_B4_P1_WITH_PRICE_ACCEPTANCE_RELEASE_VALIDATED",
                "RELEASE_VALIDATED",
                "RELEASE_VALIDATED",
                "PRICE_CONFIRMED",
                "MONITOR_PRICE_ACCEPTANCE_AND_PROPAGATION",
                "LOSS_OF_PRICE_ACCEPTANCE",
            )
        elif price in {"PRICE_FAILED", "PRICE_INVALIDATED", "PRICE_REJECTED_HIGH", "PRICE_REJECTED_LOW"}:
            set_result(
                "R_B3_B4_P1_WITH_PRICE_REJECTION_FAILED_RELEASE",
                "FAILED_RELEASE",
                "FAILED_RELEASE",
                "PRICE_FAILED" if price != "PRICE_INVALIDATED" else "PRICE_INVALIDATED",
                "WATCH_REBUILD_OR_PRESSURE_PENDING",
                "DO_NOT_READ_AS_RELEASE_VALIDATED",
            )
        else:
            set_result(
                "R_B3_B4_P1_RELEASE_CANDIDATE",
                "RELEASE_CANDIDATE",
                "CANDIDATE_NOT_VALIDATED",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                "WAIT_FOR_PRICE_ZONE_AND_B7_CONFIRMATION",
                "PRICE_REJECTION_OR_FAILED_PROPAGATION",
            )

    # 3. Raw bias requalification by film/zone/price.
    if raw_bias == "PAIR_UP":
        if _as_bool(raw.get("lower_low_after_event")) or price == "PRICE_INVALIDATED":
            set_result(
                "R_PAIR_UP_AFTER_LOWER_LOW_POST_LOW_REACTION",
                "COUNTER_BREATH_REJECTED",
                "REACTION_NOT_RELEASE",
                "PRICE_INVALIDATED",
                "WATCH_IF_LOW_RETEST_REJECTS_OR_REINTEGRATES_ZONE",
                "NEW_LOWER_LOW_CONFIRMS_COUNTER_BREATH_FAILED",
            )
        elif last_event in {"RELEASE_DOWN_VALIDATED", "LONDON_RELEASE_DOWN", "LOWER_LOCK", "LOWER_PRICE_ACCEPTANCE"} or _has_any(film, ["LOWER_LOCK", "RELEASE_DOWN"]):
            set_result(
                "R_PAIR_UP_AFTER_RELEASE_DOWN_COUNTER_BREATH",
                "POST_RELEASE_COUNTER_BREATH",
                "REACTION_NOT_RELEASE",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                packet["watch_condition"],
                "LOWER_LOW_OR_REJECTION_BELOW_ACTIVE_ZONE",
            )
        elif last_event in {"COUNTER_BREATH_REJECTED", "LOW_RETEST"} or _has_any(film, ["LOWER_ZONE_RANGE", "POST_LOW"]):
            set_result(
                "R_PAIR_UP_AFTER_LOWER_LOW_POST_LOW_REACTION",
                "POST_LOW_COUNTER_BREATH",
                "REACTION_NOT_RELEASE",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                packet["watch_condition"],
                "NEW_LOWER_LOW_OR_REJECTION_BELOW_ACTIVE_ZONE",
            )
        elif price == "PRICE_ACCEPTED_ABOVE_ZONE":
            set_result(
                "R_PAIR_UP_ACCEPTED_ABOVE_ZONE_CONTINUATION",
                "UP_CONTINUATION_ACCEPTED",
                "CONTINUATION_ACCEPTED",
                None,
                "MONITOR_ACCEPTANCE_ABOVE_ACTIVE_ZONE",
                "REINTEGRATION_BELOW_ACCEPTED_ZONE",
            )
        elif _has_any(last_event, ["HIGH_ZONE", "HIGH_REJECTION", "EXHAUSTION"]) or texture == "EXHAUSTION_DETACHMENT":
            set_result(
                "R_PAIR_UP_AFTER_HIGH_EXHAUSTION_RISK",
                "HIGH_ZONE_EXHAUSTION_RISK",
                "EXHAUSTION_RISK",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                "WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION",
                "HIGH_REJECTION_OR_UNWIND",
            )
        elif _as_bool(raw.get("late_session")) or texture == "LATE_SESSION_DETACHMENT":
            set_result(
                "R_PAIR_UP_LATE_SESSION_THIN_BOUNCE",
                "LATE_THIN_BOUNCE",
                "LOW_QUALITY_REACTION",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                "WATCH_IF_THIN_BOUNCE_GETS_ACCEPTED",
                "FAST_REJECTION_OR_STALE_PACKET",
            )

    elif raw_bias == "PAIR_DOWN":
        if price == "PRICE_ABSORBED_PULLBACK" or _as_bool(raw.get("close_high_after_event")):
            set_result(
                "R_PAIR_DOWN_AFTER_RELEASE_UP_PULLBACK",
                "PULLBACK_ABSORBED",
                "PULLBACK_CONTEXT",
                "PRICE_ABSORBED_PULLBACK",
                "WATCH_IF_ABSORPTION_HOLDS",
                "LOSS_OF_HIGH_ACCEPTANCE",
            )
        elif last_event in {"RELEASE_UP_VALIDATED", "MIDDAY_RELEASE_UP"} or _has_any(film, ["RELEASE_UP_VALIDATED", "POST_RELEASE"]):
            set_result(
                "R_PAIR_DOWN_AFTER_RELEASE_UP_PULLBACK",
                "POST_RELEASE_PULLBACK",
                "PULLBACK_CONTEXT",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                "WATCH_PULLBACK_ABSORPTION_OR_REJECTION",
                "CLOSE_HIGH_AFTER_PULLBACK_ABSORBS_PRESSURE",
            )
        elif last_event in {"HIGH_ZONE_REJECTION", "HIGH_REJECTION"} or price == "PRICE_REJECTED_HIGH" or _has_any(film, ["HIGH_REJECTION", "POST_HIGH"]):
            set_result(
                "R_PAIR_DOWN_AFTER_HIGH_REJECTION_UNWIND",
                "POST_HIGH_UNWIND",
                "STRUCTURAL_REACTION",
                "PRICE_REJECTED_HIGH" if price == "UNKNOWN" else None,
                "WATCH_UNWIND_CONTINUATION_OR_REINTEGRATION",
                "REACCEPTANCE_ABOVE_REJECTED_HIGH",
            )
        elif last_event == "COUNTER_BREATH_REJECTED" or _has_any(film, ["COUNTER_BREATH_REJECTED", "SECOND_LEG"]):
            set_result(
                "R_PAIR_DOWN_AFTER_COUNTER_BREATH_REJECTED_SECOND_LEG",
                "SECOND_LEG_DOWN",
                "STRUCTURAL_CONTINUATION",
                "PRICE_CONFIRMED" if price == "UNKNOWN" else None,
                "WATCH_LOWER_ACCEPTANCE_AND_PROPAGATION",
                "REINTEGRATION_ABOVE_COUNTER_BREATH_ZONE",
            )
        elif _as_bool(raw.get("close_high_after_event")):
            set_result(
                "R_PAIR_DOWN_AFTER_RELEASE_UP_PULLBACK",
                "FAILED_PRESSURE",
                "PULLBACK_CONTEXT",
                "PRICE_ABSORBED_PULLBACK",
                "WATCH_IF_UP_ACCEPTANCE_HOLDS",
                "PAIR_DOWN_PRESSURE_FAILED_BY_CLOSE_HIGH",
            )

    elif raw_bias == "HOT":
        if _as_bool(raw.get("after_extension")) or texture == "EXHAUSTION_DETACHMENT":
            set_result(
                "R_HOT_AFTER_EXTENSION_CONSUMED",
                "EXHAUSTION_OR_CONSUMED",
                "CONSUMED_OR_LATE",
                "PRICE_PENDING" if price == "UNKNOWN" else None,
                "WATCH_FOR_FRESH_ACCEPTANCE_NOT_CONSUMED_HEAT",
                "REJECTION_AFTER_EXTENSION",
            )
        elif price in {"PRICE_CONFIRMED", "PRICE_ACCEPTED_ABOVE_ZONE", "PRICE_ACCEPTED_BELOW_ZONE"}:
            set_result(
                "R_HOT_WITH_ACCEPTANCE_EVENT_CONFIRMED",
                "EVENT_CONFIRMED",
                "CONFIRMED_EVENT",
                "PRICE_CONFIRMED",
                "WATCH_PRICE_RESOLUTION_AFTER_CONFIRMED_EVENT",
                "LOSS_OF_ACCEPTANCE",
            )
        elif _as_bool(raw.get("no_price_displacement")) or price in {"PRICE_PENDING", "UNKNOWN"}:
            set_result(
                "R_HOT_WITHOUT_PRICE_PRESSURE_PENDING",
                "PRESSURE_PENDING",
                "PRESSURE_NOT_RELEASE",
                "PRICE_PENDING",
                "WAIT_FOR_PRICE_DISPLACEMENT_OR_ACCEPTANCE",
                "PRESSURE_DISSIPATES_OR_PACKET_STALE",
            )

    # 4. Texture and propagation as quality modifiers, not a hidden decision engine.
    if propagation == "FAILED_PROPAGATION":
        _append_unique(technical_risks, "FAILED_PROPAGATION")
        if packet["packet_quality"] in {"RELEASE_VALIDATED", "CONFIRMED_EVENT"}:
            packet["packet_quality"] = "CANDIDATE_NOT_VALIDATED"
            _append_unique(rules, "R_B7_FAILED_PROPAGATION_LIMITS_VALIDATION")
    elif propagation == "RELAY_DEGRADING":
        _append_unique(technical_risks, "RELAY_DEGRADING")
    elif propagation == "COUNTERFLOW_AGAINST_STRUCTURE":
        _append_unique(technical_risks, "COUNTERFLOW_AGAINST_STRUCTURE_INFO_ONLY")

    if texture in {"NOISY_DETACHMENT", "FALSE_REACTION_DETACHMENT"}:
        _append_unique(technical_risks, texture)
        if packet["packet_quality"] == "UNKNOWN":
            packet["packet_quality"] = "DATA_LIMITED"

    # 5. B5/B8 degraded can dominate only when no stronger contextual rule has fired.
    if b5_b8_weak:
        _append_unique(rules, "R_B5_B8_WEAK_HONEST_UNKNOWN")
        if packet["qualified_bias"] == "UNKNOWN" or raw_bias in {"WATCH", "ACTIVE", "UNKNOWN"}:
            packet["qualified_bias"] = "HONEST_UNKNOWN"
            packet["packet_quality"] = "HONEST_UNKNOWN"
            packet["price_confirmation"] = "UNKNOWN" if price == "UNKNOWN" else price

    # 6. Stale/partial must be visible and can limit quality if no stronger precise rule exists.
    if data_degraded:
        _append_unique(rules, "R_PACKETS_STALE_READING_PARTIAL")
        if packet["qualified_bias"] == "UNKNOWN" or raw_bias in {"WATCH", "ACTIVE", "UNKNOWN"}:
            packet["qualified_bias"] = "READING_PARTIAL"
            packet["packet_quality"] = "DATA_LIMITED"
        elif packet["packet_quality"] in {"FULL", "RELEASE_VALIDATED", "CONFIRMED_EVENT"} and data_visibility != "EVENT_TIME_OFFSET":
            packet["packet_quality"] = "DATA_LIMITED"

    if packet["qualified_bias"] == "UNKNOWN":
        packet["qualified_bias"] = "READING_PARTIAL" if data_degraded else "HONEST_UNKNOWN"
    if packet["packet_quality"] == "UNKNOWN":
        packet["packet_quality"] = "DATA_LIMITED" if data_degraded else "HONEST_UNKNOWN"

    audit_entry = {
        "schema_version": AUDIT_SCHEMA_VERSION,
        "generated_at": packet["generated_at"],
        "symbol": packet["symbol"],
        "raw_bias": packet["raw_bias"],
        "qualified_bias": packet["qualified_bias"],
        "packet_quality": packet["packet_quality"],
        "price_confirmation": packet["price_confirmation"],
        "data_visibility": packet["data_visibility"],
        "rules_fired": rules,
        "technical_risks": packet["technical_risks"],
        "evidence_refs": packet["evidence_refs"],
    }
    packet["audit_entry"] = audit_entry
    return packet


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("input JSON must be an object")
    return data


def _write_json(path: str, data: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _append_audit(path: str, audit_entry: Dict[str, Any]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(audit_entry, ensure_ascii=False, sort_keys=True) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Requalify a raw PowerFlow packet into terrain_packet_v76_0.")
    parser.add_argument("--input", required=True, help="Input raw packet JSON object")
    parser.add_argument("--output", required=True, help="Output terrain packet JSON")
    parser.add_argument("--audit", required=False, help="Append audit entry JSONL")
    args = parser.parse_args()

    packet = requalify_packet(_load_json(args.input))
    _write_json(args.output, packet)
    if args.audit:
        _append_audit(args.audit, packet["audit_entry"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
