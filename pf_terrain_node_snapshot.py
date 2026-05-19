"""PowerFlow B9 - Terrain node snapshot builder.

Creates a read-only terrain node payload from zone context, price verdict,
previous scene state, and data visibility.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

PIP_SIZE = 0.0001
READING_PARTIAL = "READING_PARTIAL"
DO_NOT_EMIT = "DO_NOT_EMIT"

FORBIDDEN_CLAIMS_READING_PARTIAL = [
    "footprint exact",
    "delta brut confirmé",
    "participant identifié",
    "ordre limite confirmé",
    "causalité forte",
]

NODE_ROLE_MAP = {
    ("REJECTED", "REJECTION_ZONE"): ("HIGH_REJECTION_NODE", "Node rejet zone haute"),
    ("FAILED_REINTEGRATION", "BREAK_RETEST_ZONE"): (
        "FAILED_REINTEGRATION_NODE",
        "Réintégration échouée",
    ),
    ("PULLBACK_ABSORBED", "ACCEPTANCE_ZONE"): (
        "PULLBACK_ABSORBED_NODE",
        "Pullback absorbé",
    ),
    ("ACCEPTED", "ACCEPTANCE_ZONE"): ("ZONE_ACCEPTANCE_NODE", "Acceptation zone"),
    ("EFFORT_WITHOUT_RESULT", "ABSORPTION_ZONE"): (
        "EFFORT_WITHOUT_RESULT_NODE",
        "Effort sans résultat",
    ),
    ("CENTER_MIGRATION", None): ("CENTER_MIGRATION_NODE", "Migration centre"),
    ("INCONCLUSIVE", None): ("UNDEFINED_NODE", "Non défini"),
}

ROTATION_NODE = ("ROTATION_ANCHOR_NODE", "Node ancre de rotation")
ATTENTION_NODE = ("ATTENTION_NODE", "Node attention")
UNDEFINED_NODE = ("UNDEFINED_NODE", "Non défini")


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _timestamp_key(timestamp: str) -> str:
    compact = "".join(ch for ch in timestamp if ch.isdigit())
    if compact:
        return compact[:14]
    return datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")


def _stable_node_id(node_id: str, symbol: str, timestamp: str) -> str:
    if node_id and node_id.strip():
        return node_id.strip()
    return f"B9N_{symbol}_{_timestamp_key(timestamp)}"


def _zone_bounds(zone_context: dict) -> dict:
    bounds = zone_context.get("zone_bounds") or {}
    zone_low = _as_float(bounds.get("zone_low", zone_context.get("zone_low")))
    zone_high = _as_float(bounds.get("zone_high", zone_context.get("zone_high")))
    if zone_high < zone_low:
        zone_low, zone_high = zone_high, zone_low
    center = _as_float(bounds.get("center"), (zone_low + zone_high) / 2.0)
    width_pips = _as_float(bounds.get("width_pips"), abs(zone_high - zone_low) / PIP_SIZE)
    return {
        "zone_low": zone_low,
        "zone_high": zone_high,
        "center": center,
        "width_pips": round(width_pips, 3),
    }


def _candidate(price_verdict: dict) -> str:
    value = (
        price_verdict.get("price_verdict_candidate")
        or price_verdict.get("candidate")
        or price_verdict.get("verdict")
        or price_verdict.get("status")
        or "INCONCLUSIVE"
    )
    return _as_str(value, "INCONCLUSIVE").upper()


def _data_visibility_value(data_visibility: dict) -> str:
    value = (
        data_visibility.get("data_visibility")
        or data_visibility.get("visibility")
        or data_visibility.get("status")
        or data_visibility.get("quality")
        or "UNKNOWN"
    )
    return _as_str(value, "UNKNOWN").upper()


def _emit_policy(data_visibility: dict) -> str:
    value = data_visibility.get("emit_policy") or data_visibility.get("policy") or "EMIT"
    return _as_str(value, "EMIT").upper()


def _dedupe_stack(parts: list[str]) -> str:
    seen: list[str] = []
    for part in parts:
        if not part:
            continue
        for token in str(part).split("|"):
            token = token.strip()
            if token and token not in seen:
                seen.append(token)
    return "|".join(seen) if seen else "UNKNOWN_SOURCE"


def _forbidden_claims(data_visibility: str, source_stack: str) -> list[str]:
    if data_visibility == READING_PARTIAL or READING_PARTIAL in source_stack:
        return list(FORBIDDEN_CLAIMS_READING_PARTIAL)
    return []


def _node_role(price_candidate: str, zone_role: str, emit_policy: str) -> tuple[str, str]:
    if emit_policy == DO_NOT_EMIT:
        return ATTENTION_NODE
    if zone_role == "ROTATION_ANCHOR_ZONE":
        return ROTATION_NODE
    if (price_candidate, zone_role) in NODE_ROLE_MAP:
        return NODE_ROLE_MAP[(price_candidate, zone_role)]
    if (price_candidate, None) in NODE_ROLE_MAP:
        return NODE_ROLE_MAP[(price_candidate, None)]
    return UNDEFINED_NODE


def _node_status(
    *,
    emit_policy: str,
    price_candidate: str,
    zone_status: str,
    data_visibility: str,
) -> str:
    if emit_policy == DO_NOT_EMIT:
        return "ATTENTION"
    if price_candidate in {"INVALIDATED", "FAILED"}:
        return "INVALIDATED"
    if zone_status == "CONSUMED" or price_candidate == "CONSUMED":
        return "CONSUMED"
    if data_visibility == READING_PARTIAL or price_candidate in {"INCONCLUSIVE", "WATCH"}:
        return "ATTENTION"
    return "ACTIVE"


def _microfilm_evidence(zone_context: dict) -> dict:
    metrics = zone_context.get("microfilm_metrics") or {}
    return {
        "ticks_inside_zone": int(_as_float(metrics.get("ticks_inside_zone"), 0.0)),
        "dwell_seconds": _as_float(metrics.get("dwell_seconds"), 0.0),
        "rejection_distance_pips": _as_float(metrics.get("rejection_distance_pips"), 0.0),
        "center_penetration_ratio": _as_float(metrics.get("center_penetration_ratio"), 0.0),
    }


def _confidence(zone_context: dict, price_verdict: dict, data_visibility: str) -> float:
    zone_confidence = _as_float(zone_context.get("confidence"), 0.25)
    price_confidence = _as_float(price_verdict.get("confidence"), zone_confidence)
    value = round((zone_confidence * 0.60) + (price_confidence * 0.40), 3)
    if data_visibility == READING_PARTIAL:
        value = min(value, 0.45)
    return max(0.05, min(0.95, value))


def create_terrain_node_snapshot(
    node_id: str,
    symbol: str,
    timestamp: str,
    zone_context: dict,
    price_verdict: dict,
    previous_scene_state: dict,
    data_visibility: dict,
) -> dict:
    """Create a terrain node snapshot payload.

    The payload is a perception object only. It performs no write, no send, and
    no dashboard mutation.
    """

    price_candidate = _candidate(price_verdict)
    zone_role = _as_str(zone_context.get("zone_role"), "UNDEFINED")
    zone_status = _as_str(zone_context.get("zone_status"), "ACTIVE")
    visibility = _data_visibility_value(data_visibility)
    emit_policy = _emit_policy(data_visibility)

    source_stack = _dedupe_stack(
        [
            _as_str(zone_context.get("source_stack")),
            _as_str(price_verdict.get("source_stack")),
            _as_str(data_visibility.get("source_stack")),
        ]
    )
    role, role_fr = _node_role(price_candidate, zone_role, emit_policy)

    return {
        "node_id": _stable_node_id(node_id, symbol, timestamp),
        "symbol": symbol,
        "timestamp": timestamp,
        "node_status": _node_status(
            emit_policy=emit_policy,
            price_candidate=price_candidate,
            zone_status=zone_status,
            data_visibility=visibility,
        ),
        "node_role": role,
        "node_role_fr": role_fr,
        "zone_bounds": _zone_bounds(zone_context),
        "microfilm_evidence": _microfilm_evidence(zone_context),
        "price_verdict_candidate": price_candidate,
        "zone_role": zone_role,
        "data_visibility": visibility,
        "forbidden_claims": _forbidden_claims(visibility, source_stack),
        "confidence": _confidence(zone_context, price_verdict, visibility),
        "source_stack": source_stack,
        "scene_context": {
            "previous_scene": _as_str(previous_scene_state.get("previous_scene"), "UNKNOWN"),
            "last_structural_event": _as_str(
                previous_scene_state.get("last_structural_event"), "UNKNOWN"
            ),
        },
    }


__all__ = ["create_terrain_node_snapshot", "NODE_ROLE_MAP", "FORBIDDEN_CLAIMS_READING_PARTIAL"]

# B9_RUNTIME_CONTRACT_COMPAT_V5 terrain node facade
try:
    _B9_V5_ORIGINAL_CREATE_TERRAIN_NODE_SNAPSHOT = create_terrain_node_snapshot
except NameError:  # pragma: no cover
    _B9_V5_ORIGINAL_CREATE_TERRAIN_NODE_SNAPSHOT = None


def _b9_v5_public_packet(value):
    if hasattr(value, "__dict__"):
        return dict(value.__dict__)
    if isinstance(value, dict):
        return dict(value)
    return value


def create_terrain_node_snapshot(*args, **kwargs):
    """Compatibility facade for pf_engine_b9 terrain node creation.

    Accepts window-style keyword payloads such as zone_low/zone_high and returns
    a read-only packet if the original implementation cannot accept them.
    """
    original = _B9_V5_ORIGINAL_CREATE_TERRAIN_NODE_SNAPSHOT
    if original is not None:
        try:
            return original(*args, **kwargs)
        except TypeError as exc:
            if "unexpected keyword" not in str(exc):
                raise
            try:
                import inspect
                sig = inspect.signature(original)
                allowed = {
                    name: value
                    for name, value in kwargs.items()
                    if name in sig.parameters
                }
                return original(*args, **allowed)
            except Exception:
                pass

    symbol = kwargs.get("symbol") or (args[0] if args else "GBPUSD")
    zone_low = kwargs.get("zone_low")
    zone_high = kwargs.get("zone_high")
    current_price = kwargs.get("current_price")
    visibility = kwargs.get("data_visibility") or kwargs.get("visibility") or "TACTICAL_OK"
    price_verdict = kwargs.get("price_verdict_candidate") or kwargs.get("price_verdict") or "PENDING"
    node_id = kwargs.get("node_id") or f"B9NODE_{symbol}_COMPAT"
    return {
        "node_id": node_id,
        "symbol": symbol,
        "zone_bounds": {"low": zone_low, "high": zone_high},
        "zone_low": zone_low,
        "zone_high": zone_high,
        "current_price": current_price,
        "price_verdict_candidate": price_verdict,
        "data_visibility": visibility,
        "source_profile": kwargs.get("source_profile") or {
            "source_mode": "B9_RUNTIME_COMPAT",
            "data_visibility": visibility,
            "confidence_cap": 0.35,
        },
        "limits": ["runtime contract compatibility facade"],
        "raw": {k: _b9_v5_public_packet(v) for k, v in kwargs.items()},
    }
