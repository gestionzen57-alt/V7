"""
T0133 — B9 Source Quality Hard Gate V0.

Read-only source provenance gate for B9/T009 moments.
It prevents proxy/reconstructed/nuanced scenes from being presented as raw-confirmed truth.
No DB access. No dashboard. No Telegram. No BUY/SELL. No probability of success.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0133_B9_SOURCE_QUALITY_HARD_GATE_V0"

FORBIDDEN_TERMS = [
    "BUY", "SELL", "ACHETER", "VENDRE", "LONG", "SHORT",
    "TAKE PROFIT", "STOP LOSS", "PROBABILITY OF SUCCESS", "TAUX DE REUSSITE",
    "TAUX DE RÉUSSITE", "SUCCESS RATE",
]

REQUIRED_GATE_FIELDS = [
    "b9_source_quality_gate_version",
    "b9_source_truth_family",
    "b9_source_quality_gate_state",
    "b9_source_quality_gate_severity",
    "b9_source_quality_flags",
    "b9_source_confidence_cap_effective",
    "b9_raw_claim_allowed",
    "b9_confirmation_claim_allowed",
    "b9_source_quality_reading_fr",
    "b9_source_quality_limits",
]

KNOWN_SOURCE_FAMILIES = {
    "FORCE_SNAPSHOT_DERIVED",
    "RECOVERED_EXISTING_B9_SUMMARY",
    "ORIGINAL_AVAILABLE_SUMMARY",
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _upper(value: Any) -> str:
    return _norm(value).upper()


def _float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def get_moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments", "items"):
        value = summary.get(key)
        if isinstance(value, list):
            return value
    return []


def set_moments(summary: Dict[str, Any], moments: List[Dict[str, Any]]) -> Dict[str, Any]:
    for key in ("moments", "sequence_moments", "b9_moments", "items"):
        if isinstance(summary.get(key), list):
            summary[key] = moments
            return summary
    summary["moments"] = moments
    return summary


def infer_truth_family(moment: Dict[str, Any]) -> str:
    candidates = [
        moment.get("source_family"),
        moment.get("summary_recovery_type"),
        moment.get("recovery_type"),
    ]
    haystack = " ".join(_upper(v) for v in candidates)
    for family in KNOWN_SOURCE_FAMILIES:
        if family in haystack:
            return family
    if "FORCE" in haystack and "SNAPSHOT" in haystack:
        return "FORCE_SNAPSHOT_DERIVED"
    if "RECOVER" in haystack:
        return "RECOVERED_EXISTING_B9_SUMMARY"
    if "ORIGINAL" in haystack:
        return "ORIGINAL_AVAILABLE_SUMMARY"
    return "UNKNOWN_SOURCE_FAMILY"


def compute_source_gate(moment: Dict[str, Any]) -> Dict[str, Any]:
    truth_family = infer_truth_family(moment)
    source_mode = _upper(moment.get("source_mode"))
    data_visibility = _upper(moment.get("data_visibility"))
    verdict = _upper(moment.get("proxy_vs_raw_verdict") or moment.get("raw_verdict"))
    agreement_state = _upper(moment.get("proxy_raw_agreement_state"))
    source_quality_state = _upper(moment.get("source_quality_state"))
    confidence_cap = _float(moment.get("confidence_cap"), default=0.0)
    raw_tick_count = _int(moment.get("raw_tick_count"), default=0)

    flags: List[str] = []

    is_proxy = "PROXY" in source_mode or "PROXY" in data_visibility
    is_reconstructed = "RECONSTRUCT" in data_visibility or truth_family == "FORCE_SNAPSHOT_DERIVED"
    is_raw_mode = "RAW" in source_mode or "RAW" in data_visibility
    is_full_raw = "FULL" in data_visibility and "RAW" in data_visibility
    is_raw_unavailable = "RAW_UNAVAILABLE" in verdict or "RAW_UNAVAILABLE" in agreement_state
    is_nuanced = "NUANCED_BY_RAW" in verdict or "NUANCED" in agreement_state
    is_confirmed = "CONFIRMED_BY_RAW" in verdict or "CONFIRMED" in agreement_state

    if truth_family == "UNKNOWN_SOURCE_FAMILY":
        flags.append("SOURCE_FAMILY_UNKNOWN")
    else:
        flags.append(f"SOURCE_FAMILY_{truth_family}")

    if truth_family == "FORCE_SNAPSHOT_DERIVED":
        flags.append("FORCE_SNAPSHOT_DERIVED_NOT_RECOVERED_EXISTING_SUMMARY")
    if truth_family == "RECOVERED_EXISTING_B9_SUMMARY":
        flags.append("RECOVERED_EXISTING_SUMMARY_NOT_FORCE_SNAPSHOT")
    if truth_family == "ORIGINAL_AVAILABLE_SUMMARY":
        flags.append("ORIGINAL_AVAILABLE_SUMMARY_SEPARATE_FAMILY")

    if is_proxy or is_reconstructed:
        flags.append("PROXY_OR_RECONSTRUCTED_NOT_RAW_TRUTH")
    if confidence_cap and confidence_cap < 0.5:
        flags.append("CONFIDENCE_CAP_LIMITED")
    if not source_mode:
        flags.append("SOURCE_MODE_MISSING")
    if not data_visibility:
        flags.append("DATA_VISIBILITY_MISSING")

    raw_claim_allowed = bool(is_raw_mode and is_full_raw and raw_tick_count > 0 and not is_proxy and not is_reconstructed)
    confirmation_claim_allowed = bool(is_confirmed and raw_tick_count > 0 and not is_nuanced and not is_raw_unavailable)

    if is_raw_unavailable:
        state = "SOURCE_RAW_UNAVAILABLE_REJECTED"
        severity = "BLOCK_ACTIVE_MEMORY"
        confirmation_claim_allowed = False
        raw_claim_allowed = False
        flags.append("RAW_UNAVAILABLE_REJECT_MEMORY_ACTIVE")
        reading = "Raw indisponible : la scène doit rester hors mémoire active et ne peut pas être durcie."
    elif is_nuanced:
        state = "SOURCE_RAW_NUANCED"
        severity = "LIMIT_CONFIRMATION_LANGUAGE"
        confirmation_claim_allowed = False
        raw_claim_allowed = False if (is_proxy or is_reconstructed) else raw_claim_allowed
        flags.append("NUANCED_BY_RAW_NOT_CONFIRMED")
        reading = "Le raw nuance la lecture : la scène peut être exploitée comme contexte, jamais comme confirmation dure."
    elif is_confirmed:
        state = "SOURCE_RAW_CONFIRMED"
        severity = "ALLOW_RAW_SUPPORTED_READING"
        flags.append("CONFIRMED_BY_RAW_ALLOWED_AS_RAW_SUPPORTED_READING")
        if not raw_claim_allowed:
            flags.append("RAW_SUPPORTED_BUT_NOT_RAW_TRUTH")
        reading = "La lecture est appuyée par le raw, avec conservation de la provenance et des limites de source."
    elif is_reconstructed:
        state = "SOURCE_RECONSTRUCTED_LIMITED"
        severity = "RECONSTRUCTED_LIMITS_VISIBLE"
        confirmation_claim_allowed = False
        raw_claim_allowed = False
        flags.append("RECONSTRUCTED_LIMITED_READING")
        reading = "Lecture reconstruite : utile pour la scène, limitée pour toute prétention raw."
    elif is_proxy:
        state = "SOURCE_PROXY_ONLY"
        severity = "PROXY_LIMITS_VISIBLE"
        confirmation_claim_allowed = False
        raw_claim_allowed = False
        flags.append("PROXY_ONLY_READING")
        reading = "Lecture proxy : utile pour la structure, non assimilable à une vérité raw."
    elif source_quality_state in {"LOW", "WEAK", "DEGRADED"}:
        state = "SOURCE_QUALITY_WEAK_LIMITED"
        severity = "WEAK_SOURCE_LIMITS_VISIBLE"
        confirmation_claim_allowed = False
        raw_claim_allowed = False
        flags.append("SOURCE_QUALITY_WEAK")
        reading = "Qualité source faible : la scène reste visible mais doit porter ses limites."
    else:
        state = "SOURCE_UNKNOWN_LIMITED"
        severity = "UNKNOWN_LIMITS_VISIBLE"
        confirmation_claim_allowed = False
        raw_claim_allowed = False
        flags.append("SOURCE_LIMITS_REQUIRE_REVIEW")
        reading = "Source insuffisamment qualifiée : lecture conservée, claims raw bloqués."

    limits = []
    if is_proxy:
        limits.append("Source proxy : ne pas présenter comme footprint raw.")
    if is_reconstructed:
        limits.append("Lecture reconstruite : garder confidence_cap et data_visibility visibles.")
    if is_nuanced:
        limits.append("NUANCED_BY_RAW ne doit jamais devenir CONFIRMED_BY_RAW.")
    if is_raw_unavailable:
        limits.append("RAW_UNAVAILABLE exclut la mémoire active.")
    if truth_family != "UNKNOWN_SOURCE_FAMILY":
        limits.append(f"Famille source séparée : {truth_family}.")
    if not limits:
        limits.append("Conserver provenance, verdict raw et limites dans tout export.")

    return {
        "b9_source_quality_gate_version": VERSION,
        "b9_source_truth_family": truth_family,
        "b9_source_quality_gate_state": state,
        "b9_source_quality_gate_severity": severity,
        "b9_source_quality_flags": flags,
        "b9_source_confidence_cap_effective": confidence_cap,
        "b9_raw_claim_allowed": raw_claim_allowed,
        "b9_confirmation_claim_allowed": confirmation_claim_allowed,
        "b9_source_quality_reading_fr": reading,
        "b9_source_quality_limits": limits,
    }


def enrich_summary_source_quality(summary: Dict[str, Any]) -> Dict[str, Any]:
    enriched = deepcopy(summary)
    moments = []
    for moment in get_moments(enriched):
        new_moment = deepcopy(moment)
        new_moment.update(compute_source_gate(new_moment))
        moments.append(new_moment)
    set_moments(enriched, moments)
    metadata = enriched.setdefault("metadata", {})
    metadata["b9_source_quality_hard_gate_version"] = VERSION
    metadata["b9_source_quality_hard_gate_read_only"] = True
    return enriched


def missing_required_counts(moments: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {field: 0 for field in REQUIRED_GATE_FIELDS}
    for moment in moments:
        for field in REQUIRED_GATE_FIELDS:
            value = moment.get(field)
            if value is None or value == "" or value == []:
                counts[field] += 1
    return {k: v for k, v in counts.items() if v}


def find_forbidden_language(obj: Any) -> List[str]:
    text = json_dumps_for_scan(obj).upper()
    return [term for term in FORBIDDEN_TERMS if term in text]


def json_dumps_for_scan(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, sort_keys=True)


def summarize(enriched_summary: Dict[str, Any]) -> Dict[str, Any]:
    moments = get_moments(enriched_summary)
    state_counts: Dict[str, int] = {}
    family_counts: Dict[str, int] = {}
    raw_claim_allowed_count = 0
    confirmation_claim_allowed_count = 0
    nuance_promoted_count = 0
    raw_unavailable_allowed_count = 0

    for m in moments:
        state = _norm(m.get("b9_source_quality_gate_state")) or "UNKNOWN"
        family = _norm(m.get("b9_source_truth_family")) or "UNKNOWN"
        state_counts[state] = state_counts.get(state, 0) + 1
        family_counts[family] = family_counts.get(family, 0) + 1
        if m.get("b9_raw_claim_allowed") is True:
            raw_claim_allowed_count += 1
        if m.get("b9_confirmation_claim_allowed") is True:
            confirmation_claim_allowed_count += 1
        verdict = _upper(m.get("proxy_vs_raw_verdict"))
        if "NUANCED_BY_RAW" in verdict and m.get("b9_confirmation_claim_allowed") is True:
            nuance_promoted_count += 1
        if "RAW_UNAVAILABLE" in verdict and (m.get("b9_raw_claim_allowed") or m.get("b9_confirmation_claim_allowed")):
            raw_unavailable_allowed_count += 1

    return {
        "version": VERSION,
        "moments": len(moments),
        "state_counts": state_counts,
        "family_counts": family_counts,
        "raw_claim_allowed_count": raw_claim_allowed_count,
        "confirmation_claim_allowed_count": confirmation_claim_allowed_count,
        "nuanced_promoted_to_confirmed_count": nuance_promoted_count,
        "raw_unavailable_allowed_count": raw_unavailable_allowed_count,
        "missing_required_field_counts": missing_required_counts(moments),
        "forbidden_language_hits": find_forbidden_language(enriched_summary),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
