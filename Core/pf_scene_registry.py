#!/usr/bin/env python3
"""
PowerFlow V7.2 — Scene Registry V0.1

Non-blocking behavioral scene recognition for B6 memory enrichment.

IMPORTANT:
- This module does not decide.
- This module does not filter alerts.
- This module does not suppress early scenes.
- This module gives names to market-flow scenes so B6 can remember behavior.

The machine names.
The memory compares.
The trader decides.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple


VERSION = "SceneRegistryV0.1"
METHOD = "powerflow_scene_registry_non_blocking"


def _upper(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    text = str(value).strip()
    if not text:
        return default
    return text.upper()


def _num(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def get_nested(obj: Dict[str, Any], path: Sequence[str], default: Any = None) -> Any:
    cur: Any = obj
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def extract_alert_type(alert: Dict[str, Any]) -> str:
    return _upper(
        alert.get("scene_id")
        or alert.get("alert_type")
        or alert.get("type")
        or alert.get("event_type")
        or alert.get("name")
    )


def extract_regime(alert: Dict[str, Any]) -> str:
    return _upper(
        get_nested(alert, ["regime_context", "regime"])
        or get_nested(alert, ["regime", "regime"])
        or alert.get("regime")
    )


def extract_session(alert: Dict[str, Any]) -> str:
    return _upper(
        get_nested(alert, ["session_context", "session"])
        or get_nested(alert, ["session", "session"])
        or alert.get("session")
    )


def extract_eie_state(alert: Dict[str, Any]) -> str:
    return _upper(
        alert.get("EIE_state")
        or alert.get("eie_state")
        or get_nested(alert, ["eie_context", "state"])
        or get_nested(alert, ["EIE_context", "state"])
    )


def extract_b4_state(alert: Dict[str, Any]) -> str:
    return _upper(
        alert.get("B4_state")
        or alert.get("b4_state")
        or alert.get("cycle_state")
        or get_nested(alert, ["b4_context", "cycle_state"])
        or get_nested(alert, ["B4_context", "cycle_state"])
    )


def extract_b5_direction(alert: Dict[str, Any]) -> str:
    return _upper(
        alert.get("B5_direction")
        or alert.get("b5_direction")
        or alert.get("direction")
        or get_nested(alert, ["b5_context", "direction"])
        or get_nested(alert, ["B5_context", "direction"])
    )


def extract_b3_noise_ratio(alert: Dict[str, Any]) -> Optional[float]:
    return _num(
        alert.get("B3_noise_ratio")
        or alert.get("b3_noise_ratio")
        or alert.get("noise_ratio")
        or get_nested(alert, ["b3_context", "noise_ratio"])
        or get_nested(alert, ["B3_context", "noise_ratio"])
    )


def extract_b3_speed(alert: Dict[str, Any]) -> Optional[float]:
    return _num(
        alert.get("B3_speed")
        or alert.get("speed")
        or alert.get("speed_magnitude")
        or get_nested(alert, ["b3_context", "speed_magnitude"])
        or get_nested(alert, ["B3_context", "speed_magnitude"])
    )


def extract_b3_angle(alert: Dict[str, Any]) -> Optional[float]:
    return _num(
        alert.get("B3_angle")
        or alert.get("angle")
        or alert.get("angle_kalman")
        or get_nested(alert, ["b3_context", "angle_kalman"])
        or get_nested(alert, ["B3_context", "angle_kalman"])
    )


def extract_b7_state(alert: Dict[str, Any]) -> str:
    return _upper(
        alert.get("B7_state")
        or alert.get("b7_state")
        or alert.get("resonance_state")
        or get_nested(alert, ["b7_context", "resonance_state"])
        or get_nested(alert, ["B7_context", "resonance_state"])
    )


def extract_volatility_texture(alert: Dict[str, Any]) -> str:
    return _upper(
        alert.get("volatility_texture")
        or alert.get("B7_texture")
        or alert.get("b7_texture")
        or get_nested(alert, ["volatility_context", "texture"])
        or get_nested(alert, ["B7_context", "texture"])
    )


def extract_outcome(alert: Dict[str, Any]) -> str:
    return _upper(alert.get("outcome") or get_nested(alert, ["outcome_context", "outcome"]))


def extract_bars_to_move(alert: Dict[str, Any]) -> Optional[float]:
    return _num(alert.get("bars_to_move") or get_nested(alert, ["outcome_context", "bars_to_move"]))


def memory_tuple_6d(alert: Dict[str, Any]) -> Tuple[str, str, str, str, str, str]:
    """
    Existing B6-compatible tuple. Do not break this shape.
    scene_id can be used as the first dimension if available.
    """
    return (
        _upper(alert.get("scene_id") or extract_alert_type(alert)),
        extract_regime(alert),
        extract_session(alert),
        extract_eie_state(alert),
        extract_b4_state(alert),
        extract_b5_direction(alert),
    )


def compression_qualification(alert: Dict[str, Any]) -> Dict[str, Any]:
    """
    B4 doctrine:
    B4 compression alone is insufficient.
    Cross with B1/B3/B5/EIE to qualify real vs fake compression.
    """
    regime = extract_regime(alert)
    b4 = extract_b4_state(alert)
    b5 = extract_b5_direction(alert)
    eie = extract_eie_state(alert)
    noise = extract_b3_noise_ratio(alert)

    is_b4_comp = "COMPRESS" in b4
    noise_high = noise is not None and noise > 0.35
    noise_clean = noise is not None and noise < 0.10

    real_conditions = [
        is_b4_comp,
        regime in {"COMPRESSION", "TRANSITION", "RANGE_TO_COMPRESSION"},
        b5 in {"DIVERGENT_EXTREME", "SYNCHRO_STRUCTURAL", "SYNCHRO", "DIVERGENT"},
        eie not in {"UNKNOWN", "ABSENT", "NONE", "NEUTRAL"},
        not noise_high,
    ]

    fake_conditions = [
        is_b4_comp,
        regime in {"RANGE", "UNKNOWN", "NEUTRAL"},
        b5 in {"NEUTRAL", "UNKNOWN", "MIXED"},
        eie in {"UNKNOWN", "ABSENT", "NONE", "NEUTRAL"},
        noise_high,
    ]

    real_score = sum(1 for x in real_conditions if x) / len(real_conditions)
    fake_score = sum(1 for x in fake_conditions if x) / len(fake_conditions)

    if not is_b4_comp:
        label = "NO_B4_COMPRESSION"
    elif real_score >= 0.75 and fake_score < 0.50:
        label = "COMPRESSION_REAL_CANDIDATE"
    elif fake_score >= 0.60:
        label = "COMPRESSION_FAKE_RISK"
    else:
        label = "COMPRESSION_AMBIGUOUS"

    technical_risks: List[str] = []
    if is_b4_comp and noise_high:
        technical_risks.append("B4_COMPRESSING_WITH_B3_NOISE_HIGH")
    if is_b4_comp and regime in {"RANGE", "UNKNOWN", "NEUTRAL"}:
        technical_risks.append("B4_COMPRESSING_WITHOUT_HTF_COMPRESSION")
    if is_b4_comp and b5 in {"NEUTRAL", "UNKNOWN", "MIXED"}:
        technical_risks.append("B4_COMPRESSING_WITH_B5_NEUTRAL")
    if is_b4_comp and eie in {"UNKNOWN", "ABSENT", "NONE", "NEUTRAL"}:
        technical_risks.append("B4_COMPRESSING_WITHOUT_EIE")
    if is_b4_comp and noise_clean:
        technical_risks.append("B3_SIGNAL_CLEAN")

    return {
        "compression_label": label,
        "real_score": round(real_score, 4),
        "fake_score": round(fake_score, 4),
        "technical_risks": technical_risks,
    }


@dataclass(frozen=True)
class SceneDefinition:
    scene_id: str
    family: str
    description: str
    outcomes: Tuple[str, ...]
    base_risks: Tuple[str, ...] = field(default_factory=tuple)


def score_scene(scene_id: str, alert: Dict[str, Any]) -> float:
    """
    Lightweight rule scoring. Non-blocking confidence, not a trade signal.
    """
    alert_type = extract_alert_type(alert)
    regime = extract_regime(alert)
    b4 = extract_b4_state(alert)
    b5 = extract_b5_direction(alert)
    eie = extract_eie_state(alert)
    b7 = extract_b7_state(alert)
    texture = extract_volatility_texture(alert)
    noise = extract_b3_noise_ratio(alert)
    speed = extract_b3_speed(alert)
    angle = extract_b3_angle(alert)

    def has_any(value: str, words: Sequence[str]) -> bool:
        return any(w in value for w in words)

    pts = 0.0
    max_pts = 5.0

    if scene_id == "FIRST_DETACHMENT_MICRO":
        pts += 1.5 if has_any(alert_type, ["FIRST_DETACHMENT", "DETACHMENT", "MICRO"]) else 0
        pts += 1.0 if regime in {"COMPRESSION", "TRANSITION", "TENDANCE", "TREND"} else 0
        pts += 1.0 if has_any(b4, ["COMPRESS", "STABLE"]) else 0
        pts += 1.0 if noise is not None and noise < 0.35 else 0
        pts += 0.5 if speed is not None and speed > 0 else 0

    elif scene_id == "PULLBACK_ABSORBED":
        pts += 1.5 if has_any(alert_type, ["PULLBACK", "ABSORB"]) else 0
        pts += 1.0 if regime in {"COMPRESSION", "TENDANCE", "TREND", "TRANSITION"} else 0
        pts += 1.0 if has_any(b4, ["COMPRESS", "STABLE"]) else 0
        pts += 1.0 if has_any(eie, ["ELASTIC", "EXTREME", "PRE_EXTREME"]) else 0
        pts += 0.5 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0

    elif scene_id == "ZONE_BREATH_COMPRESSION":
        cq = compression_qualification(alert)
        pts += 2.0 if has_any(b4, ["COMPRESS"]) else 0
        pts += 1.0 if regime in {"COMPRESSION", "RANGE_TO_COMPRESSION", "TRANSITION"} else 0
        pts += 1.0 if noise is not None and noise < 0.35 else 0
        pts += 0.5 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0
        pts += 0.5 if has_any(eie, ["ELASTIC", "EXTREME", "PRE_EXTREME"]) else 0
        if cq["compression_label"] == "COMPRESSION_FAKE_RISK":
            pts = min(pts, 2.5)

    elif scene_id == "COUNTER_BREATH":
        pts += 1.5 if has_any(alert_type, ["COUNTER", "BREATH"]) else 0
        pts += 1.0 if regime in {"TENDANCE", "TREND", "COMPRESSION"} else 0
        pts += 1.0 if has_any(b4, ["STABLE", "COMPRESS"]) else 0
        pts += 1.0 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0
        pts += 0.5 if noise is None or noise < 0.40 else 0

    elif scene_id == "SECOND_LEG_BIRTH":
        pts += 1.5 if has_any(alert_type, ["SECOND", "LEG"]) else 0
        pts += 1.0 if regime in {"TENDANCE", "TREND", "TRANSITION"} else 0
        pts += 1.0 if has_any(b4, ["EXPAND", "STABLE"]) else 0
        pts += 1.0 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0
        pts += 0.5 if b7 in {"RESONANT", "LAGGED"} else 0

    elif scene_id == "PRICE_LAG_CATCH_UP":
        pts += 1.5 if has_any(alert_type, ["LAG", "CATCH"]) else 0
        pts += 1.0 if b7 == "LAGGED" else 0
        pts += 1.0 if regime in {"COMPRESSION", "TRANSITION"} else 0
        pts += 1.0 if has_any(b4, ["COMPRESS", "EXPAND"]) else 0
        pts += 0.5 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0

    elif scene_id == "SPREAD_FRICTION_FIELD":
        pts += 1.5 if has_any(alert_type, ["FRICTION", "SPREAD", "NOISE"]) else 0
        pts += 1.0 if noise is not None and noise > 0.35 else 0
        pts += 1.0 if has_any(b4, ["NOISY"]) else 0
        pts += 1.0 if texture in {"SESSION_FRICTION", "MM_NOISE"} else 0
        pts += 0.5 if b5 in {"UNKNOWN", "NEUTRAL", "MIXED"} else 0

    elif scene_id == "LEADER_FOLLOWER_IMBALANCE":
        pts += 1.5 if has_any(alert_type, ["LEADER", "FOLLOWER", "IMBALANCE"]) else 0
        pts += 1.5 if has_any(b5, ["DIVERGENT"]) else 0
        pts += 1.0 if regime in {"TRANSITION", "TENDANCE", "TREND"} else 0
        pts += 0.5 if b7 == "LAGGED" else 0
        pts += 0.5 if noise is None or noise < 0.40 else 0

    elif scene_id == "NODE_BIRTH":
        pts += 1.5 if has_any(alert_type, ["NODE"]) else 0
        pts += 1.0 if regime in {"COMPRESSION", "TRANSITION"} else 0
        pts += 1.0 if has_any(b4, ["COMPRESS", "STABLE"]) else 0
        pts += 1.0 if has_any(eie, ["ELASTIC", "EXTREME", "PRE_EXTREME"]) else 0
        pts += 0.5 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0

    elif scene_id == "REPULSION_CLEAN":
        pts += 1.5 if has_any(alert_type, ["REPULSION", "REJECTION", "REJECT"]) else 0
        pts += 1.0 if has_any(eie, ["ELASTIC", "EXTREME"]) else 0
        pts += 1.0 if noise is not None and noise < 0.20 else 0
        pts += 1.0 if has_any(b4, ["STABLE", "EXPAND"]) else 0
        pts += 0.5 if b5 not in {"UNKNOWN", "NEUTRAL"} else 0

    return round(max(0.0, min(1.0, pts / max_pts)), 4)


SCENES: Dict[str, SceneDefinition] = {
    "FIRST_DETACHMENT_MICRO": SceneDefinition(
        scene_id="FIRST_DETACHMENT_MICRO",
        family="BIRTH",
        description="Première séparation propre du flux sur M1.",
        outcomes=("RELEASE_CONFIRMED", "NO_FOLLOW_THROUGH", "FAKE_DETACHMENT", "SECOND_LEG", "COUNTER_BREATH"),
        base_risks=("M1_NOISE_POSSIBLE", "EARLY_MATURITY", "RELAY_ABSENT"),
    ),
    "PULLBACK_ABSORBED": SceneDefinition(
        scene_id="PULLBACK_ABSORBED",
        family="ABSORPTION",
        description="Retour vers zone active absorbé par le flux.",
        outcomes=("RELEASE_CONFIRMED", "SECOND_LEG", "REJECTION", "NO_FOLLOW_THROUGH", "ABSORPTION_CONTINUED"),
        base_risks=("PULLBACK_TOO_SHORT", "ZONE_CONTEXT_MISSING", "B5_RELATION_UNCLEAR"),
    ),
    "ZONE_BREATH_COMPRESSION": SceneDefinition(
        scene_id="ZONE_BREATH_COMPRESSION",
        family="COMPRESSION",
        description="Respiration de zone avec cycles qui se contractent.",
        outcomes=("RELEASE_CONFIRMED", "COMPRESSION_CONTINUES", "FAKE_COMPRESSION", "RANGE_STALL", "REJECTION"),
        base_risks=("B4_FALSE_POSITIVE", "SESSION_DEAD_ZONE"),
    ),
    "COUNTER_BREATH": SceneDefinition(
        scene_id="COUNTER_BREATH",
        family="BREATH",
        description="Respiration adverse sans inversion confirmée.",
        outcomes=("SECOND_LEG", "RELEASE_RESUMED", "TRUE_REVERSAL", "NO_FOLLOW_THROUGH", "ABSORPTION"),
        base_risks=("REVERSAL_CONFUSION", "COUNTER_MOVE_TOO_STRONG"),
    ),
    "SECOND_LEG_BIRTH": SceneDefinition(
        scene_id="SECOND_LEG_BIRTH",
        family="CONTINUATION",
        description="Naissance d’une deuxième jambe après première impulsion.",
        outcomes=("SECOND_LEG_CONFIRMED", "FAILED_SECOND_LEG", "OVEREXTENSION", "COUNTER_BREATH", "REJECTION"),
        base_risks=("FIRST_LEG_EXHAUSTED", "LATE_MATURITY"),
    ),
    "PRICE_LAG_CATCH_UP": SceneDefinition(
        scene_id="PRICE_LAG_CATCH_UP",
        family="LAG",
        description="Le prix rattrape un flux qui avait bougé avant lui.",
        outcomes=("CATCH_UP_CONFIRMED", "LAG_PERSISTS", "FALSE_LEAD", "RELEASE_CONFIRMED", "NO_FOLLOW_THROUGH"),
        base_risks=("PRICE_STILL_LAGGING", "LEADER_SIGNAL_WEAK"),
    ),
    "SPREAD_FRICTION_FIELD": SceneDefinition(
        scene_id="SPREAD_FRICTION_FIELD",
        family="FRICTION",
        description="Champ rugueux, instable ou parasité.",
        outcomes=("FRICTION_RESOLVES", "FAKE_BREAK", "NO_FOLLOW_THROUGH", "REJECTION", "DELAYED_RELEASE"),
        base_risks=("SPREAD_FRICTION", "MM_NOISE", "SESSION_FRICTION", "LOW_SIGNAL_CLEANLINESS"),
    ),
    "LEADER_FOLLOWER_IMBALANCE": SceneDefinition(
        scene_id="LEADER_FOLLOWER_IMBALANCE",
        family="RELATIONAL",
        description="Un leader tire, un follower retarde ou résiste.",
        outcomes=("FOLLOWER_CATCH_UP", "LEADER_EXHAUSTION", "DIVERGENCE_CONTINUES", "REVERSION", "SECOND_LEG"),
        base_risks=("LEADER_UNCLEAR", "FOLLOWER_NOISE", "B5_SAMPLE_LOW"),
    ),
    "NODE_BIRTH": SceneDefinition(
        scene_id="NODE_BIRTH",
        family="NODE",
        description="Naissance d’un node comportemental / temporel.",
        outcomes=("NODE_CONFIRMED", "RELEASE_FROM_NODE", "NODE_REJECTED", "RANGE_STALL", "COMPRESSION_CONTINUES"),
        base_risks=("NODE_TOO_EARLY", "LOW_CONVERGENCE", "B6_NO_HISTORY"),
    ),
    "REPULSION_CLEAN": SceneDefinition(
        scene_id="REPULSION_CLEAN",
        family="REPULSION",
        description="Répulsion propre depuis zone ou état extrême.",
        outcomes=("REJECTION_CONFIRMED", "SECOND_LEG", "FAKE_REPULSION", "ZONE_RETEST", "NO_FOLLOW_THROUGH"),
        base_risks=("RETEST_PROBABLE", "B5_CONFIRMATION_WEAK", "EIE_CONTEXT_LIMITED"),
    ),
}


def infer_scene(alert: Dict[str, Any], threshold: float = 0.35) -> Dict[str, Any]:
    scores = {scene_id: score_scene(scene_id, alert) for scene_id in SCENES}
    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    top_scene, top_score = ranked[0] if ranked else ("UNKNOWN", 0.0)

    if top_score < threshold:
        top_scene = "UNKNOWN_SCENE"
        family = "UNKNOWN"
        description = "Aucune scène du registre ne dépasse le seuil."
        outcomes: Tuple[str, ...] = ()
        base_risks: Tuple[str, ...] = ("LOW_SCENE_CONFIDENCE",)
    else:
        scene = SCENES[top_scene]
        family = scene.family
        description = scene.description
        outcomes = scene.outcomes
        base_risks = scene.base_risks

    comp = compression_qualification(alert)
    risks = list(base_risks)
    risks.extend(comp.get("technical_risks", []))
    if top_score < 0.50:
        risks.append("LOW_SCENE_CONFIDENCE")
    if extract_outcome(alert) == "UNKNOWN":
        risks.append("OUTCOME_NOT_YET_OBSERVED")

    return {
        "scene_id": top_scene,
        "scene_family": family,
        "scene_confidence_non_blocking": float(top_score),
        "scene_description": description,
        "scene_scores": dict(ranked),
        "expected_outcomes_to_observe": list(outcomes),
        "compression_qualification": comp,
        "memory_tuple_6d": list(memory_tuple_6d({**alert, "scene_id": top_scene})),
        "additional_memory_fields": {
            "B3_noise_ratio": extract_b3_noise_ratio(alert),
            "B7_state": extract_b7_state(alert),
            "outcome": extract_outcome(alert),
            "bars_to_move": extract_bars_to_move(alert),
        },
        "technical_risks": list(dict.fromkeys(risks)),
        "metrics_only": True,
        "no_filtering": True,
        "no_trade_decision": True,
        "method": METHOD,
        "version": VERSION,
    }


def enrich_alert_with_scene(alert: Dict[str, Any], threshold: float = 0.35) -> Dict[str, Any]:
    enriched = dict(alert)
    scene_context = infer_scene(alert, threshold=threshold)

    enriched["scene_id"] = scene_context["scene_id"]
    enriched["scene_family"] = scene_context["scene_family"]
    enriched["scene_confidence_non_blocking"] = scene_context["scene_confidence_non_blocking"]
    enriched["scene_context"] = scene_context
    enriched["memory_tuple_6d"] = scene_context["memory_tuple_6d"]

    existing_risks = enriched.get("technical_risks")
    if not isinstance(existing_risks, list):
        existing_risks = [] if existing_risks is None else [str(existing_risks)]
    enriched["technical_risks"] = list(dict.fromkeys(existing_risks + scene_context["technical_risks"]))

    # Normalize optional fields for B6 future use without breaking current B6.
    extra = scene_context["additional_memory_fields"]
    if extra.get("B3_noise_ratio") is not None:
        enriched["B3_noise_ratio"] = extra["B3_noise_ratio"]
    if extra.get("B7_state") != "UNKNOWN":
        enriched["B7_state"] = extra["B7_state"]
    if extra.get("outcome") != "UNKNOWN":
        enriched["outcome"] = extra["outcome"]
    if extra.get("bars_to_move") is not None:
        enriched["bars_to_move"] = extra["bars_to_move"]

    return enriched
