from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple


LEGACY_EVENT_PRIORITY = {
    "KISS_REJECT": 100,
    "ZONE_REPULSION": 100,
    "EXTREME_HIGH": 90,
    "EXTREME_LOW": 90,
    "ZONE_PRESSURE_HIGH": 90,
    "ZONE_PRESSURE_LOW": 90,
    "COMPRESSION_BREAK": 80,
    "ELASTIC_RELEASE_LEGACY": 80,
    "SLINGSHOT": 75,
    "TACTICAL_REARM_RELEASE": 75,
    "CROSS": 55,
    "DOMINANCE_CROSS": 55,
    "COMPRESSION": 40,
    "ELASTIC_LOADING_LEGACY": 40,
}


def _upper(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _as_float(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _parse_dt(value: Any) -> Optional[datetime]:
    if not value:
        return None
    text = str(value).strip()
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except Exception:
        return None


def _event_priority(event: Dict[str, Any]) -> int:
    name = _upper(event.get("event"))
    role = _upper(event.get("event_role"))
    return max(LEGACY_EVENT_PRIORITY.get(name, 0), LEGACY_EVENT_PRIORITY.get(role, 0))


def _iter_legacy_events(evidence: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    latest = evidence.get("latest_event")
    if isinstance(latest, dict):
        yield latest

    recent = evidence.get("recent_events")
    if isinstance(recent, list):
        for item in recent:
            if isinstance(item, dict):
                yield item

    if any(k in evidence for k in ("event", "event_role", "bias", "price", "timeframe")):
        yield evidence


def _select_structural_event(evidence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    events = list(_iter_legacy_events(evidence))
    if not events:
        return None

    def key(event: Dict[str, Any]) -> Tuple[int, str]:
        stamp = str(event.get("detected_at") or event.get("event_at") or "")
        return (_event_priority(event), stamp)

    return sorted(events, key=key, reverse=True)[0]


def _detect_event_time_offset(event: Dict[str, Any]) -> bool:
    detected = _parse_dt(event.get("detected_at"))
    event_at = _parse_dt(event.get("event_at"))
    if not detected or not event_at:
        return False
    try:
        delta = abs((event_at - detected).total_seconds())
        return delta >= 3600
    except Exception:
        return False


def _price_zone_from_events(events: List[Dict[str, Any]]) -> Tuple[str, Optional[float], Optional[float]]:
    prices: List[float] = []
    for event in events:
        p = _as_float(event.get("price"))
        if p is not None:
            prices.append(p)

    if not prices:
        return "UNKNOWN", None, None

    low = min(prices)
    high = max(prices)
    return f"{low:.5f}-{high:.5f}", low, high


def _infer_last_structural_event(event_name: str, event_role: str, raw_bias: str) -> str:
    if event_name == "KISS_REJECT" or event_role == "ZONE_REPULSION":
        return "COUNTER_BREATH_REJECTED"

    if event_name == "EXTREME_HIGH" or event_role == "ZONE_PRESSURE_HIGH":
        return "HIGH_ZONE_REJECTION"

    if event_name == "EXTREME_LOW" or event_role == "ZONE_PRESSURE_LOW":
        return "LOWER_LOCK_CONFIRMED"

    if event_name == "COMPRESSION_BREAK" or event_role == "ELASTIC_RELEASE_LEGACY":
        if raw_bias == "PAIR_DOWN":
            return "RELEASE_DOWN_VALIDATED"
        if raw_bias == "PAIR_UP":
            return "RELEASE_UP_VALIDATED"
        return "FALSE_BIRTH"

    if event_name == "SLINGSHOT" or event_role == "TACTICAL_REARM_RELEASE":
        if raw_bias == "PAIR_DOWN":
            return "SECOND_LEG_DOWN"
        if raw_bias == "PAIR_UP":
            return "SECOND_LEG_UP"

    return "UNKNOWN"


def _infer_film_state(last_event: str, raw_bias: str, state: str) -> str:
    if last_event == "COUNTER_BREATH_REJECTED":
        return "LOWER_ZONE_ACTIVE" if raw_bias == "PAIR_DOWN" else "HIGH_ZONE_ACTIVE"

    if last_event == "HIGH_ZONE_REJECTION":
        return "HIGH_ZONE_REJECTION"

    if last_event == "LOWER_LOCK_CONFIRMED":
        return "LOWER_LOCK"

    if "RELEASE" in last_event:
        return "POST_RELEASE_REBUILD" if raw_bias == "PAIR_UP" else "POST_RELEASE_UNWIND"

    if "ELASTIC_RELEASE" in state:
        return "POST_RELEASE_UNWIND" if raw_bias == "PAIR_DOWN" else "POST_RELEASE_REBUILD"

    return "UNKNOWN"


def _infer_current_move_role(last_event: str, event_name: str, event_role: str, raw_bias: str) -> str:
    if last_event == "COUNTER_BREATH_REJECTED":
        return "SECOND_LEG" if raw_bias == "PAIR_DOWN" else "POST_LOW_REACTION"

    if last_event == "HIGH_ZONE_REJECTION":
        return "POST_HIGH_UNWIND"

    if last_event == "LOWER_LOCK_CONFIRMED":
        return "COUNTER_BREATH" if raw_bias == "PAIR_UP" else "PRESSURE_PENDING"

    if event_name == "COMPRESSION" or event_role == "ELASTIC_LOADING_LEGACY":
        return "PRESSURE_PENDING"

    if event_name == "COMPRESSION_BREAK" or event_role == "ELASTIC_RELEASE_LEGACY":
        return "RELEASE_CANDIDATE"

    return "UNKNOWN"


def _infer_zone_status(last_event: str, raw_bias: str) -> str:
    if last_event == "COUNTER_BREATH_REJECTED":
        return "REJECTION_HIGH" if raw_bias == "PAIR_DOWN" else "REJECTION_LOW"
    if last_event == "HIGH_ZONE_REJECTION":
        return "REJECTION_HIGH"
    if last_event == "LOWER_LOCK_CONFIRMED":
        return "LOWER_RANGE_ACTIVE"
    return "UNKNOWN"


def _infer_price_confirmation(last_event: str, event_name: str, event_role: str, raw_bias: str) -> str:
    if last_event in ("COUNTER_BREATH_REJECTED", "HIGH_ZONE_REJECTION"):
        return "PRICE_REJECTED_HIGH" if raw_bias == "PAIR_DOWN" else "PRICE_REJECTED_LOW"
    if last_event == "LOWER_LOCK_CONFIRMED":
        return "PRICE_REJECTED_LOW"
    if event_name == "COMPRESSION_BREAK" or event_role == "ELASTIC_RELEASE_LEGACY":
        return "PRICE_PENDING"
    return "PRICE_PENDING"


def _infer_texture(last_event: str, event_name: str, event_role: str) -> str:
    if last_event in ("COUNTER_BREATH_REJECTED", "HIGH_ZONE_REJECTION"):
        return "REJECTION_DETACHMENT"
    if event_name == "COMPRESSION_BREAK" or event_role == "ELASTIC_RELEASE_LEGACY":
        return "POST_RELEASE_DETACHMENT"
    if event_name == "COMPRESSION" or event_role == "ELASTIC_LOADING_LEGACY":
        return "NOISY_DETACHMENT"
    return "UNKNOWN"


def _infer_propagation(events: List[Dict[str, Any]]) -> str:
    timeframes = set()
    for event in events:
        tf = _upper(event.get("timeframe"))
        if tf:
            timeframes.add(tf)

    if any(tf in timeframes for tf in ("15", "30", "60", "H1", "H4")) and any(tf in timeframes for tf in ("1", "5", "M1", "M5")):
        return "LTF_MTF_RELAY"
    if timeframes:
        return "LTF_ONLY"
    return "UNKNOWN"


def _is_legacy_evidence(evidence: Dict[str, Any]) -> bool:
    if not isinstance(evidence, dict):
        return False
    if isinstance(evidence.get("latest_event"), dict):
        return True
    if isinstance(evidence.get("recent_events"), list):
        return True
    return any(k in evidence for k in ("event", "event_role", "bias", "price", "timeframe"))


def enrich_terrain_context_from_legacy(evidence: Dict[str, Any], base_context: Dict[str, Any]) -> Dict[str, Any]:
    # Conservative V7.6.2 adapter from legacy behavioral evidence to terrain_context.
    if not _is_legacy_evidence(evidence):
        return base_context

    context = dict(base_context)
    selected = _select_structural_event(evidence)
    if not selected:
        return context

    events = list(_iter_legacy_events(evidence))
    event_name = _upper(selected.get("event"))
    event_role = _upper(selected.get("event_role"))
    state = _upper(evidence.get("state") or evidence.get("status") or "")
    raw_bias = _upper(selected.get("bias") or evidence.get("bias") or context.get("raw_bias") or "UNKNOWN")
    if raw_bias not in {"PAIR_UP", "PAIR_DOWN", "MIXED", "NEUTRAL", "HOT", "WATCH", "ACTIVE", "UNKNOWN"}:
        raw_bias = "UNKNOWN"

    last_event = _infer_last_structural_event(event_name, event_role, raw_bias)
    film_state = _infer_film_state(last_event, raw_bias, state)
    current_move_role = _infer_current_move_role(last_event, event_name, event_role, raw_bias)
    zone_status = _infer_zone_status(last_event, raw_bias)
    price_confirmation = _infer_price_confirmation(last_event, event_name, event_role, raw_bias)
    texture = _infer_texture(last_event, event_name, event_role)
    propagation = _infer_propagation(events)
    zone, zone_low, zone_high = _price_zone_from_events(events)

    technical_risks = list(context.get("technical_risks") or [])
    if _detect_event_time_offset(selected) and "EVENT_TIME_OFFSET" not in technical_risks:
        technical_risks.append("EVENT_TIME_OFFSET")

    data_visibility = context.get("data_visibility") or "UNKNOWN"
    if technical_risks:
        # Preserve explicit legacy/base data states such as M1_MISSING or PACKETS_STALE.
        # EVENT_TIME_OFFSET should add a technical risk, not erase a more precise visibility state.
        if data_visibility in ("", "UNKNOWN", "FULL_READING"):
            data_visibility = "READING_PARTIAL"
    elif data_visibility == "UNKNOWN":
        data_visibility = "FULL_READING"

    generated_at = evidence.get("generated_at") or evidence.get("timestamp") or context.get("generated_at") or "UNKNOWN"
    market_time = selected.get("detected_at") or selected.get("event_at") or generated_at or context.get("market_time") or "UNKNOWN"

    context.update(
        {
            "schema_version": context.get("schema_version") or "terrain_packet_v76_0",
            "symbol": selected.get("symbol") or evidence.get("symbol") or context.get("symbol") or "UNKNOWN",
            "generated_at": generated_at,
            "market_time": market_time,
            "film_state": film_state if film_state != "UNKNOWN" else context.get("film_state", "UNKNOWN"),
            "last_structural_event": last_event if last_event != "UNKNOWN" else context.get("last_structural_event", "UNKNOWN"),
            "last_structural_direction": "DOWN" if raw_bias == "PAIR_DOWN" else ("UP" if raw_bias == "PAIR_UP" else context.get("last_structural_direction", "UNKNOWN")),
            "last_structural_time": selected.get("detected_at") or selected.get("event_at") or context.get("last_structural_time", "UNKNOWN"),
            "current_zone": zone if zone != "UNKNOWN" else context.get("current_zone", "UNKNOWN"),
            "current_zone_low": zone_low if zone_low is not None else context.get("current_zone_low"),
            "current_zone_high": zone_high if zone_high is not None else context.get("current_zone_high"),
            "current_zone_status": zone_status if zone_status != "UNKNOWN" else context.get("current_zone_status", "UNKNOWN"),
            "current_move_role": current_move_role if current_move_role != "UNKNOWN" else context.get("current_move_role", "UNKNOWN"),
            "raw_bias": raw_bias,
            "price_confirmation": price_confirmation if price_confirmation != "UNKNOWN" else context.get("price_confirmation", "UNKNOWN"),
            "propagation_state": propagation if propagation != "UNKNOWN" else context.get("propagation_state", "UNKNOWN"),
            "detachment_texture": texture if texture != "UNKNOWN" else context.get("detachment_texture", "UNKNOWN"),
            "data_visibility": data_visibility,
            "technical_risks": technical_risks,
            "legacy_selected_event": {
                "event": event_name,
                "event_role": event_role,
                "bias": raw_bias,
                "price": selected.get("price"),
                "timeframe": selected.get("timeframe"),
                "detected_at": selected.get("detected_at"),
                "event_at": selected.get("event_at"),
            },
            "watch_condition": context.get("watch_condition", "price_acceptance_or_rejection_follow_through"),
            "invalidation_condition": context.get("invalidation_condition", "opposite_price_acceptance_or_failed_follow_through"),
        }
    )

    refs = list(context.get("evidence_refs") or [])
    refs.append(
        "legacy_behavioral_state:{symbol}:{event}:{role}:{time}".format(
            symbol=context.get("symbol", "UNKNOWN"),
            event=event_name or "UNKNOWN",
            role=event_role or "UNKNOWN",
            time=market_time,
        )
    )
    context["evidence_refs"] = refs

    return context

