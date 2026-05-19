"""PowerFlow V7.6.7 B9 packet requalifier.

Mission:
    Transform a raw packet bias into a terrain role without deciding for the trader.

Doctrine:
    - requalification is perception, not censorship;
    - early alerting is expected;
    - confidence caps are technical visibility limits, not trade warnings;
    - no BUY/SELL, no execution decision, no financial-risk wording.

This module is intentionally pure-Python and side-effect free.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional


DictLike = Mapping[str, Any]


EVENT_FR: Dict[str, str] = {
    "RELEASE_UP_PULLBACK_ABSORBED": "Release UP avec pullback absorbe par la zone basse",
    "RELEASE_UP_THEN_HIGH_ZONE_EXHAUSTION": "Release UP puis exhaustion/rejet en zone haute",
    "POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN": "Counter-breath post-release rejete puis second leg DOWN",
    "RELEASE_DOWN_LOWER_ZONE_DEFENDED_LATE_COUNTER_BOUNCE": "Release DOWN puis zone basse defendue / rebond tardif",
    "ROTATION_BUILDING": "Rotation en construction autour de l'ancre",
    "BREAK_RETEST_FAILED_REINTEGRATION": "Cassure puis retest avec reintegration echouee",
    "EFFORT_WITHOUT_RESULT_ZONE_FRICTION": "Effort sans resultat sur zone de friction / absorption",
    "ACCEPTED_HIGH_ZONE": "Zone haute acceptee",
}

RULE_NAMES: Dict[str, str] = {
    "RULE_01_RELEASE_UP_PULLBACK_ABSORBED": "Release UP + acceptance zone + pullback absorbe",
    "RULE_02_RELEASE_UP_HIGH_EXHAUSTION": "Release UP + rejection zone + rejet/reintegration echouee",
    "RULE_03_POST_RELEASE_SECOND_LEG_DOWN": "Release DOWN + post-release + counter-breath rejete + second leg",
    "RULE_04_RELEASE_DOWN_LOWER_ZONE_DEFENDED": "Release DOWN + absorption zone + effort sans resultat",
    "RULE_05_ROTATION_ANCHOR": "Rotation + anchor + verdict inconclusif",
    "RULE_06_BREAK_RETEST_FAILED": "Break retest zone + reintegration echouee",
    "RULE_07_EFFORT_WITHOUT_RESULT_FRICTION": "Effort sans resultat + absorption zone",
    "RULE_08_ACCEPTED_HIGH_ZONE": "UP + acceptance zone + zone acceptee",
    "RULE_09_FALLBACK_UNQUALIFIED": "Fallback : biais brut transmis sans role terrain qualifie",
}

FORBIDDEN_CLAIMS_BASE: List[str] = [
    "BUY_SIGNAL",
    "SELL_SIGNAL",
    "AUTO_EXECUTION",
    "FINANCIAL_RISK_WARNING",
    "WAIT_FOR_CONFIRMATION_AS_CENSORSHIP",
]


@dataclass(frozen=True)
class RequalificationRule:
    rule_id: str
    event: str
    predicate: Callable[[str, str, str, str], bool]


# Order matters. More specific rules must stay above generic friction/fallback rules.
RULES: List[RequalificationRule] = [
    RequalificationRule(
        "RULE_01_RELEASE_UP_PULLBACK_ABSORBED",
        "RELEASE_UP_PULLBACK_ABSORBED",
        lambda raw_bias, zone_role, verdict, scene_state: (
            raw_bias == "UP"
            and zone_role == "ACCEPTANCE_ZONE"
            and verdict == "PULLBACK_ABSORBED"
        ),
    ),
    RequalificationRule(
        "RULE_02_RELEASE_UP_HIGH_EXHAUSTION",
        "RELEASE_UP_THEN_HIGH_ZONE_EXHAUSTION",
        lambda raw_bias, zone_role, verdict, scene_state: (
            raw_bias == "UP"
            and zone_role == "REJECTION_ZONE"
            and verdict in {"REJECTED", "FAILED_REINTEGRATION"}
        ),
    ),
    RequalificationRule(
        "RULE_03_POST_RELEASE_SECOND_LEG_DOWN",
        "POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN",
        lambda raw_bias, zone_role, verdict, scene_state: (
            raw_bias == "DOWN"
            and scene_state == "POST_RELEASE"
            and verdict == "REJECTED"
            and zone_role == "REJECTION_ZONE"
        ),
    ),
    RequalificationRule(
        "RULE_04_RELEASE_DOWN_LOWER_ZONE_DEFENDED",
        "RELEASE_DOWN_LOWER_ZONE_DEFENDED_LATE_COUNTER_BOUNCE",
        lambda raw_bias, zone_role, verdict, scene_state: (
            raw_bias == "DOWN"
            and zone_role == "ABSORPTION_ZONE"
            and verdict == "EFFORT_WITHOUT_RESULT"
        ),
    ),
    RequalificationRule(
        "RULE_05_ROTATION_ANCHOR",
        "ROTATION_BUILDING",
        lambda raw_bias, zone_role, verdict, scene_state: (
            zone_role == "ROTATION_ANCHOR_ZONE" and verdict == "INCONCLUSIVE"
        ),
    ),
    RequalificationRule(
        "RULE_06_BREAK_RETEST_FAILED",
        "BREAK_RETEST_FAILED_REINTEGRATION",
        lambda raw_bias, zone_role, verdict, scene_state: (
            zone_role == "BREAK_RETEST_ZONE" and verdict == "FAILED_REINTEGRATION"
        ),
    ),
    RequalificationRule(
        "RULE_07_EFFORT_WITHOUT_RESULT_FRICTION",
        "EFFORT_WITHOUT_RESULT_ZONE_FRICTION",
        lambda raw_bias, zone_role, verdict, scene_state: (
            verdict == "EFFORT_WITHOUT_RESULT" and zone_role == "ABSORPTION_ZONE"
        ),
    ),
    RequalificationRule(
        "RULE_08_ACCEPTED_HIGH_ZONE",
        "ACCEPTED_HIGH_ZONE",
        lambda raw_bias, zone_role, verdict, scene_state: (
            raw_bias == "UP" and verdict == "ACCEPTED" and zone_role == "ACCEPTANCE_ZONE"
        ),
    ),
]


def _norm(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    return str(value).strip().upper() or default


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _clamp01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _source_stack(data_visibility: DictLike) -> str:
    explicit = data_visibility.get("source_stack")
    if explicit:
        return str(explicit)
    visibility = _norm(data_visibility.get("data_visibility"), "UNKNOWN")
    mode = _norm(data_visibility.get("source_mode"), "UNKNOWN")
    cap_raw = data_visibility.get("confidence_cap", "NA")
    return f"{mode}|{visibility}|cap={cap_raw}"


def _technical_forbidden_claims(
    *,
    data_visibility: str,
    source_mode: str,
    zone_status: str,
) -> List[str]:
    claims = list(FORBIDDEN_CLAIMS_BASE)

    if data_visibility in {"READING_PARTIAL", "DEGRADED", "MINIMAL", "BLIND"}:
        claims.extend([
            "FULL_STACK_VISIBLE",
            "RAW_TICK_CONFIRMED",
            "HIGH_CONFIDENCE_UNCAPPED",
        ])

    if source_mode in {"M1_BAR_PROXY", "RECONSTRUCTED", "FORCE_SNAPSHOT_DERIVED"}:
        claims.extend([
            "NATIVE_FOOTPRINT_CONFIRMED",
            "EXACT_BID_ASK_DELTA_CLAIM",
        ])

    if zone_status in {"STALE", "STALE_ZONE", "PACKETS_STALE"}:
        claims.extend([
            "FRESH_ZONE",
            "LIVE_PACKET_FRESHNESS_CONFIRMED",
        ])

    # Stable order without duplicates.
    return list(dict.fromkeys(claims))


def _confidence(
    raw_packet: DictLike,
    price_verdict: DictLike,
    zone_context: DictLike,
    data_visibility: DictLike,
) -> float:
    packet_strength = _clamp01(_as_float(raw_packet.get("packet_strength"), 0.50))
    price_confidence = _clamp01(_as_float(price_verdict.get("confidence"), 0.50))
    confidence = min(packet_strength, price_confidence)

    cap = data_visibility.get("confidence_cap")
    if cap is not None:
        confidence = min(confidence, _clamp01(_as_float(cap, confidence)))

    data_state = _norm(data_visibility.get("data_visibility"), "UNKNOWN")
    if data_state == "READING_PARTIAL":
        confidence = min(confidence, 0.35)
    elif data_state == "DEGRADED":
        confidence = min(confidence, 0.50)
    elif data_state == "MINIMAL":
        confidence = min(confidence, 0.45)
    elif data_state == "BLIND":
        confidence = min(confidence, 0.20)

    zone_status = _norm(zone_context.get("zone_status"), "UNKNOWN")
    if zone_status in {"STALE", "STALE_ZONE", "PACKETS_STALE"}:
        confidence = min(confidence, 0.40)

    return round(_clamp01(confidence), 4)


def _event_fr(event: str) -> str:
    if event in EVENT_FR:
        return EVENT_FR[event]
    if event.startswith("UNQUALIFIED_"):
        suffix = event.replace("UNQUALIFIED_", "", 1)
        return f"Packet brut {suffix} transmis sans requalification terrain"
    return event.replace("_", " ").title()


def _match_rule(raw_bias: str, zone_role: str, verdict: str, scene_state: str) -> tuple[str, str]:
    for rule in RULES:
        if rule.predicate(raw_bias, zone_role, verdict, scene_state):
            return rule.event, rule.rule_id
    fallback_event = f"UNQUALIFIED_{raw_bias}"
    return fallback_event, "RULE_09_FALLBACK_UNQUALIFIED"


def requalify_packet(
    raw_packet: dict,
    zone_context: dict,
    price_verdict: dict,
    previous_scene_state: dict,
    data_visibility: dict,
) -> dict:
    """Requalify a raw B9 packet into a terrain role.

    Args:
        raw_packet: {"symbol", "timestamp", "raw_bias", "packet_strength"}
        zone_context: {"zone_role", "zone_status", "zone_low", "zone_high"}
        price_verdict: {"verdict", "confidence"}
        previous_scene_state: {"scene_state", "last_structural_event"}
        data_visibility: {"data_visibility", "source_mode", "confidence_cap"}

    Returns:
        Dict with the mission-required fields.
    """
    raw_packet = raw_packet or {}
    zone_context = zone_context or {}
    price_verdict = price_verdict or {}
    previous_scene_state = previous_scene_state or {}
    data_visibility = data_visibility or {}

    raw_bias = _norm(raw_packet.get("raw_bias"), "UNKNOWN")
    zone_role = _norm(zone_context.get("zone_role"), "UNKNOWN")
    verdict = _norm(price_verdict.get("verdict"), "UNKNOWN")
    scene_state = _norm(previous_scene_state.get("scene_state"), "UNKNOWN")
    source_mode = _norm(data_visibility.get("source_mode"), "UNKNOWN")
    visibility = _norm(data_visibility.get("data_visibility"), "UNKNOWN")
    zone_status = _norm(zone_context.get("zone_status"), "UNKNOWN")

    event, rule_id = _match_rule(raw_bias, zone_role, verdict, scene_state)
    confidence = _confidence(raw_packet, price_verdict, zone_context, data_visibility)

    recognized = not event.startswith("UNQUALIFIED_")
    should_alert = True  # Doctrine: transmit the perception; final engine may decide routing.
    if recognized:
        alert_reason = f"Requalification terrain detectee: {RULE_NAMES[rule_id]}"
    else:
        alert_reason = "Packet brut transmis: aucune regle terrain plus precise n'a matche."

    return {
        "requalified_event": event,
        "requalified_event_fr": _event_fr(event),
        "requalification_rule": rule_id,
        "requalification_rule_fr": RULE_NAMES.get(rule_id, rule_id),
        "original_bias": raw_bias,
        "requalified_confidence": confidence,
        "should_alert": should_alert,
        "alert_reason": alert_reason,
        "forbidden_claims": _technical_forbidden_claims(
            data_visibility=visibility,
            source_mode=source_mode,
            zone_status=zone_status,
        ),
        "source_stack": _source_stack(data_visibility),
    }


__all__ = [
    "EVENT_FR",
    "FORBIDDEN_CLAIMS_BASE",
    "RULES",
    "requalify_packet",
]
