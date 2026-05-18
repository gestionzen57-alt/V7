"""T0154 — B9 Scene Transition Detector V0.

Read-only helper for detecting scene-state transitions between enriched B9 moments.
It never writes DBs, never emits trading instructions, and never converts memory
similarity into prediction.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping, Sequence

VERSION = "T0154_B9_SCENE_TRANSITION_DETECTOR_V0"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.I),
    re.compile(r"\bSELL\b", re.I),
    re.compile(r"\bachat\b", re.I),
    re.compile(r"\bvente\b", re.I),
    re.compile(r"probabilit[eé]\s+de\s+succ[eè]s", re.I),
    re.compile(r"taux\s+de\s+r[eé]ussite", re.I),
]

RAW_UNAVAILABLE_STATES = {
    "RAW_UNAVAILABLE",
    "RAW_UNAVAILABLE_REJECTED",
    "SCENE_BLOCKED_RAW_UNAVAILABLE",
    "MEMORY_REJECTED_RAW_UNAVAILABLE",
}

TRANSITION_MAP: Dict[tuple[str, str], str] = {
    ("SCENE_BUILDING", "SCENE_TESTING"): "BUILD_TO_TEST",
    ("SCENE_TESTING", "SCENE_ACCEPTED"): "TEST_TO_ACCEPTED",
    ("SCENE_TESTING", "SCENE_REJECTED"): "TEST_TO_REJECTED",
    ("SCENE_ACCEPTED", "SCENE_MEMORY_SHIFTED"): "ACCEPTED_TO_MEMORY_SHIFTED",
    ("SCENE_REJECTED", "SCENE_REBUILDING"): "REJECTION_TO_REBUILDING",
    ("SCENE_DECONSTRUCTING", "SCENE_REBUILDING"): "DECONSTRUCTION_TO_REBUILDING",
    ("SCENE_MEMORY_SHIFTED", "SCENE_TESTING"): "MEMORY_SHIFT_TO_NEW_TEST",
    ("SCENE_REBUILDING", "SCENE_TESTING"): "REBUILDING_TO_TEST",
    ("SCENE_ACCEPTED", "SCENE_DECONSTRUCTING"): "ACCEPTED_TO_DECONSTRUCTING",
}

TRANSITION_READINGS_FR = {
    "BUILD_TO_TEST": "La scène quitte la construction et entre dans une zone jugée par le prix.",
    "TEST_TO_ACCEPTED": "Le test de zone est accepté : le prix valide temporairement le terrain travaillé.",
    "TEST_TO_REJECTED": "Le test est rejeté : la zone ne produit pas d'acceptation durable.",
    "ACCEPTED_TO_MEMORY_SHIFTED": "L'acceptation déplace la mémoire : le centre actif migre vers une autre zone.",
    "REJECTION_TO_REBUILDING": "Après rejet, le flux tente de reconstruire une scène sur un autre terrain.",
    "DECONSTRUCTION_TO_REBUILDING": "La scène se déconstruit puis cherche une reconstruction locale.",
    "MEMORY_SHIFT_TO_NEW_TEST": "La mémoire déplacée devient à son tour une zone de test.",
    "REBUILDING_TO_TEST": "La reconstruction devient testable : le prix revient juger la zone.",
    "ACCEPTED_TO_DECONSTRUCTING": "Une zone acceptée commence à se défaire : la lecture doit rester prudente.",
    "STATE_STABLE": "L'état de scène reste stable entre deux moments consécutifs.",
    "RAW_UNAVAILABLE_TRANSITION_BLOCKED": "Transition bloquée : une des scènes dépend d'une source raw indisponible.",
    "SCENE_TRANSITION_REVIEW_REQUIRED": "Transition lisible mais non classée : revue technique nécessaire.",
}

@dataclass
class TransitionRow:
    transition_id: str
    date: str
    from_time_start: str
    from_time_end: str
    to_time_start: str
    to_time_end: str
    from_scene_state: str
    to_scene_state: str
    transition_type: str
    transition_strength_state: str
    from_price_verdict: str
    to_price_verdict: str
    from_scene_role: str
    to_scene_role: str
    from_node_role: str
    to_node_role: str
    memory_family: str
    memory_confidence_ladder: str
    false_positive_context_state: str
    source_quality_state: str
    transition_reading_fr: str
    technical_limits: str


def _get(d: Mapping[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = d.get(key)
        if value is not None and value != "":
            return str(value)
    return default


def _moments(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    raw = summary.get("moments") or summary.get("sequence_moments") or summary.get("items") or []
    if not isinstance(raw, list):
        return []
    return [m for m in raw if isinstance(m, dict)]


def _date_from_moment(moment: Mapping[str, Any]) -> str:
    explicit = _get(moment, "date")
    if explicit:
        return explicit[:10]
    ts = _get(moment, "time_start", "start", "timestamp")
    return ts[:10] if len(ts) >= 10 else "UNKNOWN_DATE"


def _transition_id(left: Mapping[str, Any], right: Mapping[str, Any], idx: int) -> str:
    base = "|".join([
        _get(left, "time_start"), _get(left, "time_end"),
        _get(right, "time_start"), _get(right, "time_end"),
        _get(left, "b9_scene_state", "scene_state"),
        _get(right, "b9_scene_state", "scene_state"),
        str(idx),
    ])
    return "B9TR_" + hashlib.sha1(base.encode("utf-8")).hexdigest()[:12].upper()


def _has_raw_unavailable(moment: Mapping[str, Any]) -> bool:
    haystack = " ".join(str(moment.get(k, "")) for k in (
        "proxy_vs_raw_verdict", "b9_source_quality_gate_state", "b9_scene_state",
        "b9_memory_confidence_ladder", "b9_source_truth_family", "technical_limits",
    ))
    return any(token in haystack for token in RAW_UNAVAILABLE_STATES)


def _transition_type(from_state: str, to_state: str, left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    if _has_raw_unavailable(left) or _has_raw_unavailable(right):
        return "RAW_UNAVAILABLE_TRANSITION_BLOCKED"
    if from_state == to_state:
        return "STATE_STABLE"
    return TRANSITION_MAP.get((from_state, to_state), "SCENE_TRANSITION_REVIEW_REQUIRED")


def _strength(transition_type: str, right: Mapping[str, Any]) -> str:
    if transition_type == "RAW_UNAVAILABLE_TRANSITION_BLOCKED":
        return "TRANSITION_BLOCKED"
    if transition_type == "SCENE_TRANSITION_REVIEW_REQUIRED":
        return "TRANSITION_REVIEW"
    if transition_type == "STATE_STABLE":
        return "TRANSITION_STABLE"
    src = _get(right, "b9_source_quality_gate_state", "source_quality_state")
    conf = _get(right, "b9_memory_confidence_ladder", "memory_confidence_ladder")
    fp = _get(right, "b9_memory_false_positive_state", "false_positive_context_state")
    if "RAW_CONFIRMED" in src and conf in {"MEMORY_STRONG_COMPARABLE", "MEMORY_PARTIAL_COMPARABLE"} and "HIGH" not in fp:
        return "TRANSITION_STRONG"
    if "LIMITED" in src or "MISMATCH" in conf or "MISSING" in conf or "HIGH" in fp:
        return "TRANSITION_LIMITED"
    return "TRANSITION_MEDIUM"


def _limits(transition_type: str, left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    limits = []
    for m in (left, right):
        val = _get(m, "technical_limits", "b9_price_verdict_limits", "b9_scene_state_limits")
        if val and val not in limits:
            limits.append(val)
    if transition_type == "RAW_UNAVAILABLE_TRANSITION_BLOCKED":
        limits.append("Transition exclue de la lecture active car une scène dépend de RAW_UNAVAILABLE.")
    fp = _get(right, "b9_memory_false_positive_state", "false_positive_context_state")
    if "HIGH" in fp:
        limits.append("Mémoire comparable avec piège technique fort : ne pas lire comme répétition certaine.")
    if not limits:
        limits.append("Lecture transitionnelle dérivée des champs B9 disponibles ; vérifier la source et le retest.")
    return " | ".join(limits)


def detect_scene_transitions(summary: Mapping[str, Any]) -> Dict[str, Any]:
    moments = _moments(summary)
    rows: List[TransitionRow] = []
    forbidden_hits: List[str] = []

    for idx, (left, right) in enumerate(zip(moments, moments[1:]), start=1):
        from_state = _get(left, "b9_scene_state", "scene_state", default="SCENE_REVIEW_REQUIRED")
        to_state = _get(right, "b9_scene_state", "scene_state", default="SCENE_REVIEW_REQUIRED")
        transition_type = _transition_type(from_state, to_state, left, right)
        reading = TRANSITION_READINGS_FR.get(transition_type, TRANSITION_READINGS_FR["SCENE_TRANSITION_REVIEW_REQUIRED"])
        row = TransitionRow(
            transition_id=_transition_id(left, right, idx),
            date=_date_from_moment(right),
            from_time_start=_get(left, "time_start", "start"),
            from_time_end=_get(left, "time_end", "end"),
            to_time_start=_get(right, "time_start", "start"),
            to_time_end=_get(right, "time_end", "end"),
            from_scene_state=from_state,
            to_scene_state=to_state,
            transition_type=transition_type,
            transition_strength_state=_strength(transition_type, right),
            from_price_verdict=_get(left, "b9_price_verdict_state", "price_verdict"),
            to_price_verdict=_get(right, "b9_price_verdict_state", "price_verdict"),
            from_scene_role=_get(left, "b9_scene_role", "scene_role"),
            to_scene_role=_get(right, "b9_scene_role", "scene_role"),
            from_node_role=_get(left, "b9_terrain_node_role", "node_role"),
            to_node_role=_get(right, "b9_terrain_node_role", "node_role"),
            memory_family=_get(right, "b6_memory_family", "memory_family"),
            memory_confidence_ladder=_get(right, "b9_memory_confidence_ladder", "memory_confidence_ladder"),
            false_positive_context_state=_get(right, "b9_memory_false_positive_state", "false_positive_context_state"),
            source_quality_state=_get(right, "b9_source_quality_gate_state", "source_quality_state"),
            transition_reading_fr=reading,
            technical_limits=_limits(transition_type, left, right),
        )
        text = " ".join(str(v) for v in asdict(row).values())
        for pattern in FORBIDDEN_PATTERNS:
            if pattern.search(text):
                forbidden_hits.append(f"{row.transition_id}:{pattern.pattern}")
        rows.append(row)

    state_counts: Dict[str, int] = {}
    strength_counts: Dict[str, int] = {}
    for row in rows:
        state_counts[row.transition_type] = state_counts.get(row.transition_type, 0) + 1
        strength_counts[row.transition_strength_state] = strength_counts.get(row.transition_strength_state, 0) + 1

    raw_blocked = sum(1 for row in rows if row.transition_type == "RAW_UNAVAILABLE_TRANSITION_BLOCKED")
    return {
        "version": VERSION,
        "moments": len(moments),
        "transitions": len(rows),
        "transition_type_counts": state_counts,
        "transition_strength_counts": strength_counts,
        "raw_unavailable_blocked_count": raw_blocked,
        "forbidden_language_hits": forbidden_hits,
        "rows": [asdict(r) for r in rows],
    }
