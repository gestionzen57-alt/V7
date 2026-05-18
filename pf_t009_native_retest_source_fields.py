"""T0111B / T0128 native retest source fields for B9 sequence summaries.

Read-only helper. It enriches already-built T009/B9 sequence summaries with
explicit retest source fields while preserving existing moment content.

Doctrine:
- B9 does not seek a signal.
- B9 reads the trace left by effort.
- A retest is a scene judgment, not a trade decision.
- No BUY/SELL language. No probability of success.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional

VERSION = "T0111B_NATIVE_RETEST_SOURCE_FIELDS_V0"
POLICY = "INTERPRETATION_ONLY_NO_DECISION"

REQUIRED_RETEST_FIELDS = [
    "retest_source_fields_version",
    "retest_visible",
    "retest_source",
    "retest_zone",
    "retest_start",
    "retest_end",
    "retest_result",
    "retest_judgment_fr",
    "retest_limits",
]

FORBIDDEN_LANGUAGE = [
    "BUY",
    "SELL",
    "ACHETER",
    "VENDRE",
    "probability of success",
    "probabilité de succès",
    "success probability",
]

DEFAULT_LIMITS = [
    "native retest fields are generated from the B9 moment payload and sequence context",
    "if raw retest evidence is absent, the retest remains NOT_VISIBLE or PENDING",
    "M1 proxy and reconstructed summaries remain source-limited",
    "no BUY/SELL language",
    "no probability of success",
]


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_as_text(v) for v in value)
    if isinstance(value, Mapping):
        return " ".join(f"{k} {_as_text(v)}" for k, v in value.items())
    return str(value)


def _combined_text(moment: Mapping[str, Any]) -> str:
    keys = [
        "label_fr",
        "moment_type",
        "reading_fr",
        "what_happens_fr",
        "why_it_matters_fr",
        "how_it_happened_fr",
        "mechanism_fr",
        "proof_summary_fr",
        "previous_context_fr",
        "cause_fr",
        "reaction_fr",
        "consequence_fr",
        "memory_shift_fr",
        "retest_role_fr",
        "session_chapter",
        "fractal_reading_fr",
        "b9_retest_mixed_reading_fr",
        "b9_retest_source_reading_fr",
        "b9_natural_flow_reading_fr",
        "tags",
        "b9_factor_flags",
    ]
    return " ".join(_as_text(moment.get(k)) for k in keys).lower()


def _first_present(moment: Mapping[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        value = moment.get(key)
        if value not in (None, "", [], {}):
            return value
    return default


def _time_start(moment: Mapping[str, Any]) -> Optional[str]:
    return _first_present(moment, ["time_start", "start_time", "orig_start", "raw_window_start_mt5"])


def _time_end(moment: Mapping[str, Any]) -> Optional[str]:
    return _first_present(moment, ["time_end", "end_time", "orig_end", "raw_window_end_mt5"])


def _zone_label(moment: Mapping[str, Any], previous: Optional[Mapping[str, Any]]) -> str:
    explicit = _first_present(
        moment,
        [
            "retest_zone",
            "zone",
            "zone_label",
            "zone_global",
            "current_zone",
            "price_zone",
            "retest_zone_distance_pips",
        ],
    )
    if explicit not in (None, ""):
        return _as_text(explicit)

    low = _first_present(moment, ["zone_low", "price_low", "raw_zone_low", "center_min", "center_start"])
    high = _first_present(moment, ["zone_high", "price_high", "raw_zone_high", "center_max", "center_end"])
    if low not in (None, "") and high not in (None, ""):
        return f"{low}–{high}"

    if previous:
        p_low = _first_present(previous, ["zone_low", "price_low", "raw_zone_low", "center_min", "center_start"])
        p_high = _first_present(previous, ["zone_high", "price_high", "raw_zone_high", "center_max", "center_end"])
        if p_low not in (None, "") and p_high not in (None, ""):
            return f"previous_zone:{p_low}–{p_high}"

    return "RETEST_ZONE_NOT_VISIBLE"


@dataclass(frozen=True)
class RetestClassification:
    visible: bool
    result: str
    judgment_fr: str
    source: str


def classify_native_retest(moment: Mapping[str, Any], previous: Optional[Mapping[str, Any]] = None) -> RetestClassification:
    """Classify retest state from explicit fields and B9 textual/sequence evidence."""
    text = _combined_text(moment)

    explicit_status = _as_text(
        _first_present(
            moment,
            [
                "retest_outcome_hint",
                "b9_retest_source_status",
                "b9_retest_natural_state",
                "retest_source_field_confidence",
                "b9_retest_source_readiness",
            ],
            "",
        )
    ).lower()

    combined = f"{text} {explicit_status}"

    if any(token in combined for token in ["failed reintegration", "réintégration échou", "reintegration failed", "failed_reintegration"]):
        return RetestClassification(
            True,
            "FAILED_REINTEGRATION",
            "Le retour dans la zone échoue : la scène reste jugée par un retest défavorable.",
            "NATIVE_TEXT_AND_SEQUENCE_INFERENCE",
        )

    if any(token in combined for token in ["retest_failed", "break_retest_failed", "retest échou", "retest echou", "reprise refus", "refusée", "refuse", "rejet", "rejected"]):
        return RetestClassification(
            True,
            "RETEST_FAILED",
            "Le retest ne confirme pas la reprise : le prix juge la zone défavorablement.",
            "NATIVE_TEXT_AND_SEQUENCE_INFERENCE",
        )

    if any(token in combined for token in ["pullback absorb", "zone défendue", "zone defendue", "accepted", "accepté", "accepte", "defended", "zone_defended", "pullback_absorbed"]):
        return RetestClassification(
            True,
            "RETEST_ACCEPTED",
            "Le retour teste la zone sans casser la provenance : le retest est accepté ou défendu.",
            "NATIVE_TEXT_AND_SEQUENCE_INFERENCE",
        )

    if any(token in combined for token in ["retest", "zone de décision", "zone de decision", "decision area", "retrace_decision", "pending"]):
        return RetestClassification(
            True,
            "RETEST_PENDING",
            "La scène montre un retour de jugement, mais le verdict du retest reste en attente.",
            "NATIVE_TEXT_AND_SEQUENCE_INFERENCE",
        )

    # If legacy fields explicitly say not visible, keep the absence visible.
    if any(token in combined for token in ["not_visible", "not visible", "non visible", "pas visible"]):
        return RetestClassification(
            False,
            "RETEST_NOT_VISIBLE",
            "Le retest n’est pas visible dans les champs source disponibles.",
            "RETEST_SOURCE_NOT_VISIBLE",
        )

    # Sequence hint: if there is a previous moment and current wording implies return/respiration,
    # expose a weak pending retest rather than pretending raw confirmation exists.
    if previous and any(token in combined for token in ["respiration", "corrective", "retour", "pullback", "frein", "shelf"]):
        return RetestClassification(
            True,
            "RETEST_PENDING",
            "Le moment ressemble à un retour de jugement sur la zone précédente, mais le verdict reste limité.",
            "NATIVE_SEQUENCE_CONTEXT_INFERENCE",
        )

    return RetestClassification(
        False,
        "RETEST_NOT_VISIBLE",
        "Le retest n’est pas visible dans ce moment.",
        "RETEST_SOURCE_NOT_VISIBLE",
    )


def enrich_moment_with_native_retest_fields(
    moment: Mapping[str, Any],
    previous: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    enriched: Dict[str, Any] = dict(moment)
    classification = classify_native_retest(enriched, previous)

    enriched["retest_source_fields_version"] = VERSION
    enriched["retest_visible"] = bool(classification.visible)
    enriched["retest_source"] = classification.source
    enriched["retest_zone"] = _zone_label(enriched, previous) if classification.visible else "RETEST_ZONE_NOT_VISIBLE"
    enriched["retest_start"] = _time_start(enriched) if classification.visible else None
    enriched["retest_end"] = _time_end(enriched) if classification.visible else None
    enriched["retest_result"] = classification.result
    enriched["retest_judgment_fr"] = classification.judgment_fr
    enriched["retest_limits"] = list(DEFAULT_LIMITS)
    enriched["retest_native_policy"] = POLICY

    return enriched


def _get_moments_container(summary: MutableMapping[str, Any]) -> List[Dict[str, Any]]:
    moments = summary.get("moments")
    if isinstance(moments, list):
        return moments

    # Some payloads nest moments under timeframes.[0].segments.root_list.
    timeframes = summary.get("timeframes")
    if isinstance(timeframes, list) and timeframes:
        segments = timeframes[0].get("segments") if isinstance(timeframes[0], Mapping) else None
        root_list = segments.get("root_list") if isinstance(segments, Mapping) else None
        if isinstance(root_list, list):
            summary["moments"] = root_list
            return root_list

    summary["moments"] = []
    return summary["moments"]


def enrich_sequence_summary_with_native_retest_fields(summary: Mapping[str, Any]) -> Dict[str, Any]:
    enriched = deepcopy(dict(summary))
    moments = _get_moments_container(enriched)
    new_moments: List[Dict[str, Any]] = []

    previous: Optional[Mapping[str, Any]] = None
    for moment in moments:
        if not isinstance(moment, Mapping):
            continue
        enriched_moment = enrich_moment_with_native_retest_fields(moment, previous)
        new_moments.append(enriched_moment)
        previous = enriched_moment

    enriched["moments"] = new_moments
    metadata = dict(enriched.get("metadata") or {})
    metadata["t0111b_native_retest_source_fields_version"] = VERSION
    metadata["t0111b_native_retest_policy"] = POLICY
    metadata["t0111b_native_retest_notes"] = [
        "native retest fields are carried on every moment",
        "not visible remains explicit and is not upgraded to confirmation",
        "retest judgment is interpretive scene context, not a trade decision",
    ]
    enriched["metadata"] = metadata
    return enriched


def find_missing_required_fields(summary: Mapping[str, Any]) -> Dict[str, int]:
    missing: Dict[str, int] = {field: 0 for field in REQUIRED_RETEST_FIELDS}
    for moment in summary.get("moments", []) or []:
        if not isinstance(moment, Mapping):
            continue
        for field in REQUIRED_RETEST_FIELDS:
            if field not in moment:
                missing[field] += 1
    return {k: v for k, v in missing.items() if v}


def find_forbidden_language(payload: Any) -> List[str]:
    """Return decision-language hits, ignoring explicit negative policy statements.

    Documentation often contains phrases such as "no BUY/SELL". Those are
    policy locks, not forbidden output decisions. This checker flags positive or
    unqualified decision language only.
    """
    text = _as_text(payload).lower()
    hits: List[str] = []
    for token in FORBIDDEN_LANGUAGE:
        t = token.lower()
        if t not in text:
            continue
        negated_patterns = [
            f"no {t}",
            f"no {t}/",
            f"no buy/sell",
            f"aucun {t}",
            f"aucune {t}",
            f"pas de {t}",
            f"sans {t}",
            "no probability of success",
            "aucune probabilité de succès",
        ]
        if any(pattern in text for pattern in negated_patterns):
            continue
        hits.append(token)
    return hits
