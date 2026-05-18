"""T0146 - B9 Memory Confidence Ladder V0.

Read-only enrichment layer for B9/T009 moments.
It qualifies memory comparability. It does not predict outcome,
produce execution advice, or write to any database.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0146_B9_MEMORY_CONFIDENCE_LADDER_V0"

REQUIRED_FIELDS = [
    "b9_memory_comparability_state",
    "b9_memory_comparability_score",
    "b9_memory_confidence_ladder_flags",
    "b9_memory_confidence_ladder_reading_fr",
    "b9_memory_confidence_ladder_limits",
]

FORBIDDEN_TERMS = ["BUY", "SELL", "ACHETER", "VENDRE", "TAUX DE REUSSITE", "TAUX DE RÉUSSITE", "PROBABILITE DE SUCCES", "PROBABILITÉ DE SUCCÈS"]

RAW_UNAVAILABLE_STATES = {"RAW_UNAVAILABLE", "SOURCE_RAW_UNAVAILABLE_REJECTED", "MEMORY_FP_REJECT_RAW_UNAVAILABLE", "MEMORY_REJECTED_RAW_UNAVAILABLE", "RAW_UNAVAILABLE_REJECTED"}
STRONG_SOURCE_STATES = {"SOURCE_RAW_CONFIRMED", "STRONG", "HIGH", "FULL_RAW"}
NUANCED_SOURCE_STATES = {"SOURCE_RAW_NUANCED", "NUANCED_BY_RAW", "MEDIUM"}
LIMITED_SOURCE_STATES = {"SOURCE_PROXY_ONLY", "SOURCE_RECONSTRUCTED_LIMITED", "SOURCE_QUALITY_WEAK_LIMITED", "SOURCE_UNKNOWN_LIMITED", "M1_BAR_PROXY", "RECONSTRUCTED"}


def _upper(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().upper()


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    text = str(value).strip()
    if not text:
        return []
    if ";" in text:
        return [p.strip() for p in text.split(";") if p.strip()]
    if "," in text:
        return [p.strip() for p in text.split(",") if p.strip()]
    return [text]


def extract_moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "rows", "items"):
        value = summary.get(key)
        if isinstance(value, list):
            return value
    if isinstance(summary.get("summary"), dict):
        return extract_moments(summary["summary"])
    return []


def set_moments(summary: Dict[str, Any], moments: List[Dict[str, Any]]) -> Dict[str, Any]:
    out = deepcopy(summary)
    for key in ("moments", "sequence_moments", "rows", "items"):
        if isinstance(out.get(key), list):
            out[key] = moments
            return out
    if isinstance(out.get("summary"), dict):
        out["summary"] = set_moments(out["summary"], moments)
        return out
    out["moments"] = moments
    return out


def _has_raw_unavailable(moment: Dict[str, Any]) -> bool:
    fields = [
        moment.get("proxy_vs_raw_verdict"),
        moment.get("b9_source_quality_gate_state"),
        moment.get("b9_memory_false_positive_state"),
        moment.get("b9_b6_memory_family"),
        moment.get("b9_scene_family"),
        moment.get("b9_price_verdict_state"),
    ]
    flags = _as_list(moment.get("b9_memory_false_positive_flags")) + _as_list(moment.get("b9_source_quality_flags"))
    return any(_upper(v) in RAW_UNAVAILABLE_STATES for v in fields + flags)


def _source_limited(moment: Dict[str, Any]) -> bool:
    fields = [
        moment.get("b9_source_quality_gate_state"),
        moment.get("source_quality_state"),
        moment.get("source_mode"),
        moment.get("data_visibility"),
        moment.get("summary_recovery_type"),
    ]
    joined = " ".join(_upper(v) for v in fields)
    return any(state in joined for state in LIMITED_SOURCE_STATES) or "FORCE_SNAPSHOT_DERIVED" in joined


def _source_strong(moment: Dict[str, Any]) -> bool:
    fields = [
        moment.get("b9_source_quality_gate_state"),
        moment.get("source_quality_state"),
        moment.get("proxy_vs_raw_verdict"),
        moment.get("data_visibility"),
    ]
    joined = " ".join(_upper(v) for v in fields)
    return any(state in joined for state in STRONG_SOURCE_STATES) or "CONFIRMED_BY_RAW" in joined


def _source_nuanced(moment: Dict[str, Any]) -> bool:
    fields = [
        moment.get("b9_source_quality_gate_state"),
        moment.get("source_quality_state"),
        moment.get("proxy_vs_raw_verdict"),
    ]
    joined = " ".join(_upper(v) for v in fields)
    return any(state in joined for state in NUANCED_SOURCE_STATES)


def _retest_missing(moment: Dict[str, Any]) -> bool:
    retest_visible = moment.get("retest_visible")
    retest_result = _upper(moment.get("retest_result"))
    judgment = _upper(moment.get("b9_native_retest_judgment"))
    role = _upper(moment.get("retest_role_fr"))
    if retest_visible is False:
        return True
    if retest_result in {"", "RETEST_NOT_VISIBLE", "NOT_VISIBLE", "UNKNOWN"} and judgment in {"", "RETEST_NOT_VISIBLE", "UNKNOWN"}:
        return True
    return "NON VISIBLE" in role or "PAS VISIBLE" in role


def _session_mismatch(moment: Dict[str, Any]) -> bool:
    flags = _as_list(moment.get("b9_memory_false_positive_flags")) + _as_list(moment.get("b9_memory_confidence_ladder_flags"))
    if any("SESSION" in _upper(f) and ("MISMATCH" in _upper(f) or "DIFFERENT" in _upper(f) or "DIFFERENTE" in _upper(f)) for f in flags):
        return True
    return _upper(moment.get("b9_memory_comparison_state")) == "MEMORY_SESSION_MISMATCH"


def _center_path_mismatch(moment: Dict[str, Any]) -> bool:
    flags = _as_list(moment.get("b9_memory_false_positive_flags"))
    return any("CENTER" in _upper(f) and ("MISMATCH" in _upper(f) or "DIFFER" in _upper(f)) for f in flags)


def _false_positive_level(moment: Dict[str, Any]) -> str:
    state = _upper(moment.get("b9_memory_false_positive_state"))
    if "HIGH" in state:
        return "HIGH"
    if "MEDIUM" in state:
        return "MEDIUM"
    if "LOW" in state:
        return "LOW"
    return "UNKNOWN"


def classify_memory_comparability(moment: Dict[str, Any]) -> Tuple[str, int, List[str], str, List[str]]:
    flags: List[str] = []
    limits: List[str] = []
    score = 70

    if _has_raw_unavailable(moment):
        return (
            "MEMORY_REJECTED_RAW_UNAVAILABLE",
            0,
            ["RAW_UNAVAILABLE_REJECTED"],
            "Mémoire rejetée : la donnée raw est indisponible ou explicitement rejetée. La scène reste utile pour audit, pas pour mémoire active.",
            ["RAW_UNAVAILABLE exclu de la mémoire active."],
        )

    fp = _false_positive_level(moment)
    if fp == "HIGH":
        score -= 30
        flags.append("FALSE_POSITIVE_CONTEXT_HIGH")
        limits.append("Piège de similarité élevé : la proximité mémoire doit rester auditée.")
    elif fp == "MEDIUM":
        score -= 15
        flags.append("FALSE_POSITIVE_CONTEXT_MEDIUM")
    elif fp == "LOW":
        score += 5
        flags.append("FALSE_POSITIVE_CONTEXT_LOW")

    if _source_limited(moment):
        score -= 20
        flags.append("SOURCE_LIMITED_OR_PROXY")
        limits.append("Source proxy ou reconstruite : ne pas durcir en vérité raw.")
    elif _source_nuanced(moment):
        score -= 10
        flags.append("RAW_NUANCED")
        limits.append("RAW nuance la scène : ne pas présenter comme confirmation dure.")
    elif _source_strong(moment):
        score += 10
        flags.append("SOURCE_STRONG")

    if _retest_missing(moment):
        score -= 20
        flags.append("RETEST_MISSING")
        limits.append("Retest absent ou non visible : comparaison mémoire incomplète.")

    if _session_mismatch(moment):
        score -= 15
        flags.append("SESSION_MISMATCH")
        limits.append("Session différente : même famille possible, texture de flux différente.")

    if _center_path_mismatch(moment):
        score -= 15
        flags.append("CENTER_PATH_DIFFERENT")
        limits.append("Chemin interne du centre différent : similarité fragile.")

    if _upper(moment.get("b9_b6_memory_family")) in {"", "MEMORY_UNKNOWN", "UNKNOWN"}:
        score -= 15
        flags.append("MEMORY_FAMILY_UNKNOWN")
        limits.append("Famille mémoire non stabilisée.")

    score = max(0, min(100, score))

    if "RETEST_MISSING" in flags:
        state = "MEMORY_RETEST_MISSING"
        reading = "Mémoire comparable mais retest manquant : le film ressemble, le juge de zone reste incomplet."
    elif "SESSION_MISMATCH" in flags:
        state = "MEMORY_SESSION_MISMATCH"
        reading = "Mémoire comparable avec session différente : même famille possible, texture temporelle à nuancer."
    elif "SOURCE_LIMITED_OR_PROXY" in flags or "RAW_NUANCED" in flags:
        state = "MEMORY_SOURCE_LIMITED"
        reading = "Mémoire exploitable mais source limitée : comparaison utile, vérité raw non durcie."
    elif score >= 75 and fp in {"LOW", "UNKNOWN"}:
        state = "MEMORY_STRONG_COMPARABLE"
        reading = "Mémoire fortement comparable : famille, source et pièges techniques restent cohérents."
    else:
        state = "MEMORY_PARTIAL_COMPARABLE"
        reading = "Mémoire partiellement comparable : film proche mais différences techniques à garder visibles."

    if not limits:
        limits.append("Comparabilité mémoire uniquement ; aucune répétition certaine, aucune décision d'exécution.")

    return state, score, flags, reading, limits


def enrich_moment(moment: Dict[str, Any]) -> Dict[str, Any]:
    out = deepcopy(moment)
    state, score, flags, reading, limits = classify_memory_comparability(out)
    out["b9_memory_confidence_ladder_version"] = VERSION
    out["b9_memory_comparability_state"] = state
    out["b9_memory_comparability_score"] = score
    out["b9_memory_confidence_ladder_flags"] = flags
    out["b9_memory_confidence_ladder_reading_fr"] = reading
    out["b9_memory_confidence_ladder_limits"] = limits
    return out


def enrich_sequence_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    moments = extract_moments(summary)
    enriched = [enrich_moment(m) if isinstance(m, dict) else m for m in moments]
    out = set_moments(summary, enriched)
    out["b9_memory_confidence_ladder_version"] = VERSION
    return out


def forbidden_language_hits(obj: Any) -> List[str]:
    text = str(obj).upper()
    return [term for term in FORBIDDEN_TERMS if term in text]
