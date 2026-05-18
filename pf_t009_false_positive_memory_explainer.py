# -*- coding: utf-8 -*-
"""
T0145 - B9 False Positive Memory Explainer V0

Read-only helper for PowerFlow B9/B6.
It explains why a memory similarity can be technically misleading.
It does not predict, rank execution, or produce BUY/SELL decisions.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0145_B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0"

FORBIDDEN_TERMS = [
    "buy",
    "sell",
    "acheter",
    "vendre",
    "long ",
    "short ",
    "probability of success",
    "probabilite de succes",
    "probabilité de succès",
    "winrate",
    "take profit",
    "stop loss",
]

RAW_UNAVAILABLE_VALUES = {
    "RAW_UNAVAILABLE",
    "SOURCE_RAW_UNAVAILABLE_REJECTED",
    "MEMORY_REJECTED_RAW_UNAVAILABLE",
    "RAW_UNAVAILABLE_REJECTED",
}

LOW_TRUST_VALUES = {
    "B6_LOW_TRUST_CANDIDATE",
    "LOW_TRUST",
    "SOURCE_QUALITY_WEAK_LIMITED",
    "SOURCE_UNKNOWN_LIMITED",
}


def _as_str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        return value
    return str(value)


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _lower_text(value: Any) -> str:
    if isinstance(value, (dict, list, tuple)):
        return str(value).lower()
    return _as_str(value).lower()


def get_moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments", "rows"):
        value = summary.get(key)
        if isinstance(value, list):
            return [m for m in value if isinstance(m, dict)]
    if isinstance(summary, list):
        return [m for m in summary if isinstance(m, dict)]
    return []


def detect_forbidden_language(obj: Any) -> List[str]:
    text = _lower_text(obj)
    hits: List[str] = []
    for term in FORBIDDEN_TERMS:
        if term in text:
            hits.append(term)
    return sorted(set(hits))


def _top_match(moment: Dict[str, Any]) -> Dict[str, Any]:
    candidates = []
    for key in ("b6_nearest_films", "b6_memory_matches", "similarity_matches", "matches"):
        value = moment.get(key)
        if isinstance(value, list):
            candidates.extend([v for v in value if isinstance(v, dict)])
    if candidates:
        return candidates[0]
    # flattened top-match fields are common in B9 reports
    flat_keys = [k for k in moment if k.startswith("b6_top_match_") or k.startswith("top_match_")]
    if flat_keys:
        out: Dict[str, Any] = {}
        for key in flat_keys:
            if key.startswith("b6_top_match_"):
                out[key.replace("b6_top_match_", "")] = moment.get(key)
            if key.startswith("top_match_"):
                out[key.replace("top_match_", "")] = moment.get(key)
        return out
    return {}


def _source_fields(moment: Dict[str, Any]) -> Dict[str, str]:
    return {
        "source_family": _as_str(moment.get("source_family") or moment.get("b9_source_truth_family")),
        "summary_recovery_type": _as_str(moment.get("summary_recovery_type")),
        "source_mode": _as_str(moment.get("source_mode")),
        "data_visibility": _as_str(moment.get("data_visibility")),
        "proxy_vs_raw_verdict": _as_str(moment.get("proxy_vs_raw_verdict")),
        "source_quality_state": _as_str(moment.get("source_quality_state") or moment.get("b9_source_quality_gate_state")),
    }


def _has_raw_unavailable(moment: Dict[str, Any]) -> bool:
    fields = _source_fields(moment)
    values = set(fields.values())
    values.add(_as_str(moment.get("b6_memory_family")))
    values.add(_as_str(moment.get("b9_b6_memory_family")))
    values.add(_as_str(moment.get("b9_source_quality_gate_state")))
    values.add(_as_str(moment.get("proxy_raw_agreement_state")))
    return bool(values & RAW_UNAVAILABLE_VALUES)


def _has_low_trust(moment: Dict[str, Any]) -> bool:
    values = set(_source_fields(moment).values())
    values.add(_as_str(moment.get("b6_memory_candidate_state")))
    values.add(_as_str(moment.get("source_quality_state")))
    values.add(_as_str(moment.get("b9_source_quality_gate_state")))
    return bool(values & LOW_TRUST_VALUES)


def _flag_source_limits(moment: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    fields = _source_fields(moment)
    source_mode = fields["source_mode"]
    visibility = fields["data_visibility"]
    recovery = fields["summary_recovery_type"]
    raw_verdict = fields["proxy_vs_raw_verdict"]
    confidence_cap = _as_float(moment.get("confidence_cap") or moment.get("b9_source_confidence_cap_effective"), 1.0)

    if recovery == "FORCE_SNAPSHOT_DERIVED":
        flags.append("FORCE_SNAPSHOT_DERIVED_NOT_RECOVERED_SUMMARY")
    if "PROXY" in source_mode or source_mode == "M1_BAR_PROXY":
        flags.append("PROXY_SOURCE_MODE")
    if visibility in {"RECONSTRUCTED", "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED"}:
        flags.append("RECONSTRUCTED_VISIBILITY")
    if raw_verdict == "NUANCED_BY_RAW":
        flags.append("RAW_NUANCED_NOT_CONFIRMED")
    if raw_verdict == "RAW_UNAVAILABLE":
        flags.append("RAW_UNAVAILABLE")
    if confidence_cap and confidence_cap < 0.50:
        flags.append("LOW_CONFIDENCE_CAP")
    if _has_low_trust(moment):
        flags.append("LOW_TRUST_SOURCE")
    return flags


def _flag_retest_limits(moment: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    visible = moment.get("retest_visible")
    judgment = _as_str(moment.get("b9_native_retest_judgment") or moment.get("retest_result") or moment.get("retest_judgment"))
    if visible is False or judgment in {"", "RETEST_NOT_VISIBLE"}:
        flags.append("RETEST_NOT_VISIBLE")
    elif judgment in {"RETEST_PENDING", "PENDING"}:
        flags.append("RETEST_PENDING")
    elif judgment in {"RETEST_FAILED", "FAILED_REINTEGRATION"}:
        flags.append("RETEST_FAILURE_CONTEXT")
    return flags


def _flag_session_limits(moment: Dict[str, Any], match: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    scene_session = _as_str(moment.get("b9_session") or moment.get("session"))
    match_session = _as_str(match.get("session") or match.get("b9_session") or match.get("source_session"))
    if scene_session and match_session and scene_session != match_session:
        flags.append("SESSION_MISMATCH")
    if scene_session in {"DEAD_ZONE", "SESSION_UNKNOWN"}:
        flags.append("SESSION_CONTEXT_WEAK")
    return flags


def _flag_family_limits(moment: Dict[str, Any], match: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    scene_family = _as_str(moment.get("b9_b6_scene_family") or moment.get("b9_scene_family"))
    memory_family = _as_str(moment.get("b9_b6_memory_family") or moment.get("b6_memory_family"))
    match_family = _as_str(match.get("b6_memory_family") or match.get("memory_family") or match.get("family"))
    match_scene = _as_str(match.get("b9_b6_scene_family") or match.get("scene_family"))

    if memory_family and match_family and memory_family != match_family:
        flags.append("MEMORY_FAMILY_MISMATCH")
    if scene_family and match_scene and scene_family != match_scene:
        flags.append("SCENE_FAMILY_VARIANT")
    if scene_family in {"", "SCENE_FAMILY_REVIEW_REQUIRED"}:
        flags.append("SCENE_FAMILY_INFERRED_OR_WEAK")
    return flags


def _flag_center_path_limits(moment: Dict[str, Any], match: Dict[str, Any]) -> List[str]:
    flags: List[str] = []
    scene_shape = _as_str(moment.get("b9_center_path_shape") or moment.get("center_path_shape"))
    match_shape = _as_str(match.get("center_path_shape") or match.get("b9_center_path_shape"))
    visibility = _as_str(moment.get("b9_center_path_visibility"))
    if visibility in {"CENTER_PATH_START_END_ONLY", "CENTER_PATH_NOT_VISIBLE", "CENTER_PATH_PROXY_EXTREMES"}:
        flags.append(visibility)
    if scene_shape and match_shape and scene_shape != match_shape:
        flags.append("CENTER_PATH_SHAPE_MISMATCH")
    return flags


def _score_from_flags(flags: Iterable[str]) -> int:
    score = 0
    weights = {
        "RAW_UNAVAILABLE": 100,
        "LOW_TRUST_SOURCE": 35,
        "FORCE_SNAPSHOT_DERIVED_NOT_RECOVERED_SUMMARY": 22,
        "PROXY_SOURCE_MODE": 18,
        "RECONSTRUCTED_VISIBILITY": 18,
        "RAW_NUANCED_NOT_CONFIRMED": 18,
        "LOW_CONFIDENCE_CAP": 14,
        "RETEST_NOT_VISIBLE": 25,
        "RETEST_PENDING": 15,
        "RETEST_FAILURE_CONTEXT": 10,
        "SESSION_MISMATCH": 14,
        "SESSION_CONTEXT_WEAK": 10,
        "MEMORY_FAMILY_MISMATCH": 30,
        "SCENE_FAMILY_VARIANT": 18,
        "SCENE_FAMILY_INFERRED_OR_WEAK": 16,
        "CENTER_PATH_START_END_ONLY": 15,
        "CENTER_PATH_NOT_VISIBLE": 25,
        "CENTER_PATH_PROXY_EXTREMES": 12,
        "CENTER_PATH_SHAPE_MISMATCH": 18,
    }
    for flag in flags:
        score += weights.get(flag, 8)
    return max(0, min(100, score))


def _state_from_score(score: int, raw_unavailable: bool) -> str:
    if raw_unavailable:
        return "MEMORY_FP_REJECT_RAW_UNAVAILABLE"
    if score >= 70:
        return "MEMORY_FP_HIGH"
    if score >= 35:
        return "MEMORY_FP_MEDIUM"
    return "MEMORY_FP_LOW"


def _comparison_state(state: str) -> str:
    if state == "MEMORY_FP_REJECT_RAW_UNAVAILABLE":
        return "MEMORY_COMPARISON_REJECTED_RAW_UNAVAILABLE"
    if state == "MEMORY_FP_HIGH":
        return "MEMORY_COMPARISON_REVIEW_REQUIRED"
    if state == "MEMORY_FP_MEDIUM":
        return "MEMORY_COMPARISON_USABLE_WITH_LIMITS"
    return "MEMORY_COMPARISON_USABLE"


def _fr_summary(flags: List[str], state: str) -> Tuple[str, str, List[str]]:
    limits: List[str] = []
    if state == "MEMORY_FP_REJECT_RAW_UNAVAILABLE":
        caution = "Film proche rejeté pour mémoire active : la scène contient une indisponibilité raw critique."
    elif state == "MEMORY_FP_HIGH":
        caution = "Film proche utile pour audit, mais la comparaison est fragile et doit rester en revue."
    elif state == "MEMORY_FP_MEDIUM":
        caution = "Film proche exploitable comme contexte, avec limites techniques visibles."
    else:
        caution = "Film proche comparable : aucun piège technique majeur détecté dans le sample."

    explanations: List[str] = []
    mapping = {
        "FORCE_SNAPSHOT_DERIVED_NOT_RECOVERED_SUMMARY": "source dérivée force snapshot, à ne pas confondre avec un summary récupéré",
        "PROXY_SOURCE_MODE": "lecture proxy, pas footprint raw complet",
        "RECONSTRUCTED_VISIBILITY": "lecture reconstruite, utile pour la scène mais limitée pour le détail microstructure",
        "RAW_NUANCED_NOT_CONFIRMED": "raw nuance la scène, il ne la confirme pas entièrement",
        "LOW_CONFIDENCE_CAP": "confiance capée par la source",
        "RETEST_NOT_VISIBLE": "retest non visible, le jugement de zone reste partiel",
        "RETEST_PENDING": "retest en attente, la scène n'est pas complètement jugée",
        "SESSION_MISMATCH": "session différente entre scène actuelle et film mémoire",
        "SESSION_CONTEXT_WEAK": "session faible ou inconnue",
        "MEMORY_FAMILY_MISMATCH": "famille mémoire différente",
        "SCENE_FAMILY_VARIANT": "famille de scène proche mais variante",
        "SCENE_FAMILY_INFERRED_OR_WEAK": "famille de scène inférée ou à revoir",
        "CENTER_PATH_SHAPE_MISMATCH": "chemin interne du centre différent",
        "CENTER_PATH_START_END_ONLY": "chemin du centre réduit au début/fin",
        "CENTER_PATH_PROXY_EXTREMES": "chemin du centre approché par extrêmes proxy",
        "CENTER_PATH_NOT_VISIBLE": "chemin interne du centre non visible",
        "RAW_UNAVAILABLE": "raw indisponible",
        "LOW_TRUST_SOURCE": "source faible ou low trust",
    }
    for flag in flags:
        if flag in mapping:
            explanations.append(mapping[flag])
            limits.append(mapping[flag])

    if not explanations:
        explanations.append("pas de divergence technique majeure dans les champs disponibles")

    difference = "Différences / pièges : " + "; ".join(explanations) + "."
    return caution, difference, sorted(set(limits))


@dataclass
class MemoryFalsePositiveRow:
    moment_id: str
    time_start: str
    time_end: str
    b9_b6_scene_family: str
    b9_b6_memory_family: str
    top_match_film_id: str
    top_match_family: str
    b9_memory_false_positive_state: str
    b9_memory_false_positive_score: int
    b9_memory_false_positive_flags: List[str]
    b9_memory_comparison_state: str
    b9_memory_similarity_caution_fr: str
    b9_memory_difference_explanation_fr: str
    b9_memory_technical_limits: List[str]


def explain_moment(moment: Dict[str, Any], index: int) -> Dict[str, Any]:
    match = _top_match(moment)
    flags: List[str] = []
    flags.extend(_flag_source_limits(moment))
    flags.extend(_flag_retest_limits(moment))
    flags.extend(_flag_session_limits(moment, match))
    flags.extend(_flag_family_limits(moment, match))
    flags.extend(_flag_center_path_limits(moment, match))
    flags = sorted(set(flags))

    raw_unavailable = _has_raw_unavailable(moment) or "RAW_UNAVAILABLE" in flags
    score = _score_from_flags(flags)
    state = _state_from_score(score, raw_unavailable)
    comparison_state = _comparison_state(state)
    caution, difference, limits = _fr_summary(flags, state)

    row = MemoryFalsePositiveRow(
        moment_id=_as_str(moment.get("moment_id") or moment.get("id") or f"moment_{index:03d}"),
        time_start=_as_str(moment.get("time_start") or moment.get("start") or moment.get("b9_time_start_real")),
        time_end=_as_str(moment.get("time_end") or moment.get("end") or moment.get("b9_time_end_real")),
        b9_b6_scene_family=_as_str(moment.get("b9_b6_scene_family") or moment.get("b9_scene_family")),
        b9_b6_memory_family=_as_str(moment.get("b9_b6_memory_family") or moment.get("b6_memory_family")),
        top_match_film_id=_as_str(match.get("film_id") or match.get("id")),
        top_match_family=_as_str(match.get("b6_memory_family") or match.get("memory_family") or match.get("family")),
        b9_memory_false_positive_state=state,
        b9_memory_false_positive_score=score,
        b9_memory_false_positive_flags=flags,
        b9_memory_comparison_state=comparison_state,
        b9_memory_similarity_caution_fr=caution,
        b9_memory_difference_explanation_fr=difference,
        b9_memory_technical_limits=limits,
    )

    enriched = dict(moment)
    enriched.update({
        "b9_false_positive_memory_version": VERSION,
        "b9_memory_false_positive_state": row.b9_memory_false_positive_state,
        "b9_memory_false_positive_score": row.b9_memory_false_positive_score,
        "b9_memory_false_positive_flags": row.b9_memory_false_positive_flags,
        "b9_memory_comparison_state": row.b9_memory_comparison_state,
        "b9_memory_similarity_caution_fr": row.b9_memory_similarity_caution_fr,
        "b9_memory_difference_explanation_fr": row.b9_memory_difference_explanation_fr,
        "b9_memory_technical_limits": row.b9_memory_technical_limits,
    })
    return {"row": asdict(row), "moment": enriched}


def explain_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    moments = get_moments(summary)
    rows: List[Dict[str, Any]] = []
    enriched_moments: List[Dict[str, Any]] = []
    for idx, moment in enumerate(moments, start=1):
        explained = explain_moment(moment, idx)
        rows.append(explained["row"])
        enriched_moments.append(explained["moment"])

    state_counts: Dict[str, int] = {}
    comparison_counts: Dict[str, int] = {}
    flag_counts: Dict[str, int] = {}
    for row in rows:
        state_counts[row["b9_memory_false_positive_state"]] = state_counts.get(row["b9_memory_false_positive_state"], 0) + 1
        comparison_counts[row["b9_memory_comparison_state"]] = comparison_counts.get(row["b9_memory_comparison_state"], 0) + 1
        for flag in row["b9_memory_false_positive_flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1

    enriched_summary = dict(summary)
    if "moments" in enriched_summary or not any(k in enriched_summary for k in ("sequence_moments", "b9_moments", "rows")):
        enriched_summary["moments"] = enriched_moments
    elif "sequence_moments" in enriched_summary:
        enriched_summary["sequence_moments"] = enriched_moments
    elif "b9_moments" in enriched_summary:
        enriched_summary["b9_moments"] = enriched_moments
    elif "rows" in enriched_summary:
        enriched_summary["rows"] = enriched_moments

    forbidden_hits = detect_forbidden_language(enriched_summary)
    raw_unavailable_allowed_count = sum(1 for r in rows if r["b9_memory_false_positive_state"] != "MEMORY_FP_REJECT_RAW_UNAVAILABLE" and "RAW_UNAVAILABLE" in r["b9_memory_false_positive_flags"])

    return {
        "version": VERSION,
        "moments": len(moments),
        "state_counts": state_counts,
        "comparison_counts": comparison_counts,
        "flag_counts": flag_counts,
        "raw_unavailable_allowed_count": raw_unavailable_allowed_count,
        "forbidden_language_hits": forbidden_hits,
        "rows": rows,
        "enriched_summary": enriched_summary,
    }
