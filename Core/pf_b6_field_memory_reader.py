"""PowerFlow V7.6.7 B6 field memory reader.

B6 memory is a film memory: it should compare the current terrain scene with known
field films, not produce a BUY/SELL decision and not overstate source quality.

This file is designed as a drop-in V7.6.7 patch:
    - FILM_LIBRARY contains 15 films;
    - films 8..15 are the B9 extension requested by GPT-2 mission;
    - HARD_EXCLUSION_PAIRS contains extended contradictions;
    - matching score is intentionally small and explainable: 0..3.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

try:  # Keeps this module usable in isolation during tests.
    from pf_b9_source_constants import FIELD_MEMORY_SOURCE_TAG, get_field_memory_source_tag
except Exception:  # pragma: no cover - fallback for unusual import layout
    FIELD_MEMORY_SOURCE_TAG = {}

    def get_field_memory_source_tag(source_date: str) -> str:
        return "FORCE_SNAPSHOT_DERIVED"


Film = Dict[str, Any]
Context = Mapping[str, Any]

# Existing V7.6 field films rebuilt from the terrain calibration library.
# Films 8..15 below are added exactly for the GPT-2 B9 extension.
FILM_LIBRARY: List[Film] = [
    {
        "film_id": "RELEASE_UP_FROM_LOW_THEN_HIGH_ZONE_EXHAUSTION",
        "source_date": "2026-05-06",
        "sequence_signature": ["LOW_ZONE_BUILDING", "RELEASE_UP_VALIDATED", "HIGH_ZONE_EXHAUSTION", "POST_RELEASE_UNWIND"],
        "zone_roles": ["low_zone_building", "high_zone_exhaustion"],
        "price_verdicts": ["release_up_validated", "high_zone_exhaustion", "post_release_unwind"],
        "last_structural_event": "RELEASE_UP_NODE",
        "move_roles_expected": ["RELEASE_UP_VALIDATED", "HIGH_ZONE_EXHAUSTION", "POST_RELEASE_UNWIND"],
        "memory_rule": "UP apres high-zone deja consommee = suspect / consumed.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["ACCEPTED_HIGH_ZONE"],
    },
    {
        "film_id": "LATE_HIGH_REJECTION_WITH_DEEP_UNWIND",
        "source_date": "2026-05-07",
        "sequence_signature": ["POST_RELEASE_REBUILD", "LATE_UP_EXTENSION", "HIGH_ZONE_REJECTION", "DEEP_POST_HIGH_UNWIND"],
        "zone_roles": ["high_zone_rejected"],
        "price_verdicts": ["late_extension", "high_zone_rejection", "deep_unwind"],
        "last_structural_event": "HIGH_REJECTION_NODE",
        "move_roles_expected": ["LATE_UP_EXTENSION", "POST_HIGH_UNWIND"],
        "memory_rule": "DOWN apres high rejete = post-high unwind, pas direction brute.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["ACCEPTED_HIGH_ZONE"],
    },
    {
        "film_id": "RELEASE_UP_VALIDATED_CLOSE_NEAR_HIGH",
        "source_date": "2026-05-08",
        "sequence_signature": ["LOW_ZONE_REBUILD", "RELEASE_UP_VALIDATED", "PULLBACK_ABSORBED", "CONTINUATION_UP", "CLOSE_NEAR_HIGH"],
        "zone_roles": ["low_zone_rebuild", "accepted_high_zone"],
        "price_verdicts": ["release_up_validated", "pullback_absorbed", "close_near_high"],
        "last_structural_event": "RELEASE_UP_NODE",
        "move_roles_expected": ["RELEASE_FIRST_LEG", "PULLBACK_ABSORBED", "CONTINUATION_UP"],
        "memory_rule": "Close near high valide l'acceptation apres release UP.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["FAILED_REINTEGRATION"],
    },
    {
        "film_id": "RELEASE_UP_FROM_COMPRESSION_THEN_SECOND_LEG_UP_AND_EXHAUSTION",
        "source_date": "2026-05-11",
        "sequence_signature": ["PRE_LONDON_FALSE_BIRTHS", "MIDDAY_RELEASE_UP", "POST_RELEASE_PULLBACK", "SECOND_LEG_UP", "HIGH_ZONE_EXHAUSTION", "LATE_UNWIND"],
        "zone_roles": ["compression_zone", "high_zone_exhaustion"],
        "price_verdicts": ["false_births", "release_up", "second_leg_up", "late_unwind"],
        "last_structural_event": "SECOND_LEG_UP_NODE",
        "move_roles_expected": ["FALSE_BIRTH", "RELEASE_UP", "SECOND_LEG", "EXHAUSTION"],
        "memory_rule": "B3+B2 seul produit des false births; B4/P1/prix/B7 doivent qualifier.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["CLEAN_DIRECTIONAL_RELEASE"],
    },
    {
        "film_id": "LONDON_RELEASE_DOWN_WITH_LOWER_LOCK_AND_LATE_COUNTER_BREATH",
        "source_date": "2026-05-12",
        "sequence_signature": ["ASIA_HIGH_FAILURE", "LONDON_RELEASE_DOWN", "LOWER_PRICE_ACCEPTANCE", "POST_RELEASE_COUNTER_BREATH", "SECOND_LOW_TEST", "LATE_COUNTER_BOUNCE"],
        "zone_roles": ["lower_lock", "lower_zone_active"],
        "price_verdicts": ["release_down", "lower_price_acceptance", "late_counter_bounce"],
        "last_structural_event": "RELEASE_DOWN_NODE",
        "move_roles_expected": ["RELEASE_DOWN", "LOWER_LOCK", "COUNTER_BREATH"],
        "memory_rule": "PAIR_UP apres release down = counter-breath par defaut jusqu'a reintegration confirmee.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["RETEST_OUTCOME_ACCEPTED"],
    },
    {
        "film_id": "POST_RELEASE_COUNTER_BREATH_REJECTED_THEN_SECOND_LEG_DOWN",
        "source_date": "2026-05-13",
        "sequence_signature": ["POST_RELEASE_LOWER_ACCEPTANCE", "LONDON_COUNTER_BREATH_UP", "COUNTER_BREATH_REJECTED", "SECOND_LEG_DOWN", "LOWER_LOW", "POST_LOW_COUNTER_BREATH", "LATE_THIN_BOUNCE"],
        "zone_roles": ["lower_acceptance", "counter_breath_rejected"],
        "price_verdicts": ["counter_breath_rejected", "second_leg_down", "lower_low"],
        "last_structural_event": "SECOND_LEG_DOWN_NODE",
        "move_roles_expected": ["COUNTER_BREATH", "COUNTER_BREATH_REJECTED", "SECOND_LEG_DOWN"],
        "memory_rule": "Counter-breath rejete devient carburant du second leg.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["RETEST_OUTCOME_ACCEPTED"],
    },
    {
        "film_id": "LOWER_ZONE_RANGE_WITH_COUNTER_BREATH_REJECTED_READING_PARTIAL",
        "source_date": "2026-05-14",
        "sequence_signature": ["LOWER_ZONE_RANGE_ACTIVE", "COUNTER_BREATH_UP", "COUNTER_BREATH_REJECTED", "LOW_RETEST", "POST_LOW_REACTION"],
        "zone_roles": ["lower_zone_range_active"],
        "price_verdicts": ["counter_breath_rejected", "low_retest", "post_low_reaction"],
        "last_structural_event": "READING_PARTIAL_NODE",
        "move_roles_expected": ["COUNTER_BREATH", "READING_PARTIAL"],
        "memory_rule": "M1 absent + packets stale = reading partial visible en haut.",
        "data_visibility_required": "READING_PARTIAL",
        "exclusion_if_same_dir": ["RAW_TICK_CONFIRMED"],
    },
    # Film 8 - LOW_ZONE_BUILD_RELEASE_UP
    {
        "film_id": "LOW_ZONE_BUILD_RELEASE_UP",
        "source_date": "2026-05-15",
        "sequence_signature": ["LOW_ZONE_BUILD", "COMPRESSION", "RELEASE_UP"],
        "zone_roles": ["low_zone_build"],
        "price_verdicts": ["zone_acceptance", "upward_displacement"],
        "last_structural_event": "RELEASE_UP_NODE",
        "move_roles_expected": ["ZONE_BUILD", "RELEASE_FIRST_LEG"],
        "memory_rule": "Zone basse construite + compression -> release UP validee.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": [],
    },
    # Film 9 - HIGH_ZONE_REJECTION
    {
        "film_id": "HIGH_ZONE_REJECTION",
        "source_date": "2026-05-15",
        "sequence_signature": ["HIGH_ZONE_TOUCH", "CENTER_FAILED", "REJECTION_DOWN"],
        "zone_roles": ["high_zone_rejected"],
        "price_verdicts": ["center_failed", "down_rejection_speed"],
        "last_structural_event": "HIGH_REJECTION_NODE",
        "move_roles_expected": ["TOUCH_HIGH", "REJECTION_DOWN"],
        "memory_rule": "Touch zone haute + centre echoue + rejet rapide down.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["ACCEPTED_HIGH_ZONE"],
    },
    # Film 10 - BREAK_RETEST_FAILED
    {
        "film_id": "BREAK_RETEST_FAILED",
        "source_date": "2026-05-15",
        "sequence_signature": ["BREAK", "RETEST", "FAILED_REINTEGRATION"],
        "zone_roles": ["break_retest_zone"],
        "price_verdicts": ["breakout", "return_to_zone", "center_failed"],
        "last_structural_event": "FAILED_REINTEGRATION_NODE",
        "move_roles_expected": ["BREAKOUT", "RETEST", "FAILED_REINTEGRATION"],
        "memory_rule": "Cassure -> retest -> centre echoue -> reintegration echouee.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["RETEST_OUTCOME_ACCEPTED"],
    },
    # Film 11 - EFFORT_WITHOUT_RESULT_FRICTION
    {
        "film_id": "EFFORT_WITHOUT_RESULT_FRICTION",
        "source_date": "2026-05-15",
        "sequence_signature": ["HIGH_ACTIVITY", "LOW_PRICE_PROGRESS", "FRICTION"],
        "zone_roles": ["friction_zone"],
        "price_verdicts": ["activity_present", "progress_weak", "range_contained"],
        "last_structural_event": "EFFORT_WITHOUT_RESULT_NODE",
        "move_roles_expected": ["HIGH_ACTIVITY", "COMPRESSION"],
        "memory_rule": "Activite forte + progression prix faible = friction / effort sans resultat.",
        "data_visibility_required": "RECONSTRUCTED",
        "exclusion_if_same_dir": ["CLEAN_DIRECTIONAL_RELEASE"],
    },
    # Film 12 - PROGRESSIVE_WAVE
    {
        "film_id": "PROGRESSIVE_WAVE",
        "source_date": "2026-05-15",
        "sequence_signature": ["STEP_PROGRESS", "SHALLOW_PULLBACKS", "CONTINUATION"],
        "zone_roles": ["wave_progression"],
        "price_verdicts": ["higher_steps_or_lower_steps", "pullback_absorbed", "net_progress"],
        "last_structural_event": "PROGRESSIVE_WAVE_NODE",
        "move_roles_expected": ["WAVE_PROGRESSION"],
        "memory_rule": "Progression par etapes + pullbacks peu profonds + continuation.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["BALANCED_ROTATION"],
    },
    # Film 13 - ROTATIONAL_AUCTION
    {
        "film_id": "ROTATIONAL_AUCTION",
        "source_date": "2026-05-15",
        "sequence_signature": ["CENTER_CROSSES", "BALANCED_RANGE", "NO_ESCAPE"],
        "zone_roles": ["rotation_anchor_zone"],
        "price_verdicts": ["multiple_center_crosses", "range_stability", "no_directional_displacement"],
        "last_structural_event": "ROTATION_ANCHOR_NODE",
        "move_roles_expected": ["AUCTION_ROTATIONAL_BALANCE"],
        "memory_rule": "Enchere rotationnelle : croisements centre multiples + pas d'echappee directionnelle.",
        "data_visibility_required": "TACTICAL_OK",
        "exclusion_if_same_dir": ["RELEASE_UP", "RELEASE_DOWN"],
    },
    # Film 14 - RAW_TEXTURE_TRAP
    {
        "film_id": "RAW_TEXTURE_TRAP",
        "source_date": "2026-05-15",
        "sequence_signature": ["PROXY_DIRECTIONAL", "RAW_ROTATION", "NUANCED_BY_RAW"],
        "zone_roles": ["texture_trap"],
        "price_verdicts": ["proxy_directional_read", "raw_rotation_or_friction", "source_quality_limited"],
        "last_structural_event": "RAW_TEXTURE_TRAP_NODE",
        "move_roles_expected": ["PROXY_DIRECTIONAL_READ"],
        "memory_rule": "Lecture proxy directionnelle + raw montre rotation/friction = piege de texture.",
        "data_visibility_required": "READING_PARTIAL",
        "exclusion_if_same_dir": ["CONFIRMED_BY_RAW_STRONG"],
    },
    # Film 15 - LIVE_ATTENTION_ONLY
    {
        "film_id": "LIVE_ATTENTION_ONLY",
        "source_date": "2026-05-15",
        "sequence_signature": ["LIVE_SOURCE_UNQUALIFIED", "ATTENTION_REQUIRED", "NO_DECISION"],
        "zone_roles": ["live_candidate"],
        "price_verdicts": ["unqualified_raw_texture", "manual_review_required"],
        "last_structural_event": "ATTENTION_NODE",
        "move_roles_expected": ["LIVE_ATTENTION_CANDIDATE"],
        "memory_rule": "Source live non qualifiee -> attention requise -> pas de decision automatique.",
        "data_visibility_required": "READING_PARTIAL",
        "exclusion_if_same_dir": ["TELEGRAM_SEND_ENABLED"],
    },
]

HARD_EXCLUSION_PAIRS: List[Tuple[str, str]] = [
    ("PULLBACK_ABSORBED", "FAILED_REINTEGRATION"),
    ("RETEST_OUTCOME_ACCEPTED", "RETEST_OUTCOME_REJECTED"),
    ("FLOW_DIRECTIONAL_DISPLACEMENT", "FLOW_BALANCED_AUCTION"),
    ("CONFIRMED_BY_RAW", "RAW_UNAVAILABLE"),
    ("CLEAN_PROGRESSIVE_WAVE", "FLOW_GAPPY_LIMIT"),
]

VISIBILITY_RANK = {
    "BLIND": 0,
    "READING_PARTIAL": 1,
    "RECONSTRUCTED": 2,
    "MINIMAL": 2,
    "DEGRADED": 2,
    "TACTICAL_OK": 3,
    "FULL_STACK_VISIBLE": 4,
    "RAW_TICK_PLUS_FORCE_CONTEXT": 4,
}


def _norm(value: Any) -> str:
    return str(value).strip().lower() if value is not None else ""


def _upper(value: Any) -> str:
    return str(value).strip().upper() if value is not None else ""


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]


def film_ids() -> List[str]:
    return [film["film_id"] for film in FILM_LIBRARY]


def get_film_by_id(film_id: str) -> Optional[Film]:
    expected = _upper(film_id)
    for film in FILM_LIBRARY:
        if _upper(film.get("film_id")) == expected:
            return dict(film)
    return None


def has_hard_exclusion(tokens: Iterable[str]) -> bool:
    token_set = {_upper(token) for token in tokens}
    for left, right in HARD_EXCLUSION_PAIRS:
        if left in token_set and right in token_set:
            return True
        if right in token_set and left in token_set:
            return True
    return False


def _visibility_ok(required: str, actual: str) -> bool:
    required_u = _upper(required)
    actual_u = _upper(actual)
    if not required_u:
        return True
    if required_u == "READING_PARTIAL":
        return actual_u in {"READING_PARTIAL", "DEGRADED", "MINIMAL", "TACTICAL_OK", "FULL_STACK_VISIBLE", "RECONSTRUCTED"}
    if required_u == "RECONSTRUCTED":
        return actual_u in {"RECONSTRUCTED", "TACTICAL_OK", "FULL_STACK_VISIBLE", "RAW_TICK_PLUS_FORCE_CONTEXT"}
    return VISIBILITY_RANK.get(actual_u, 0) >= VISIBILITY_RANK.get(required_u, 0)


def _intersection_score(current: Iterable[Any], expected: Iterable[Any]) -> int:
    current_set = {_norm(item) for item in current if _norm(item)}
    expected_set = {_norm(item) for item in expected if _norm(item)}
    if not current_set or not expected_set:
        return 0
    return 1 if current_set.intersection(expected_set) else 0


def score_film_match(context: Context, film: Film) -> Dict[str, Any]:
    """Return an explainable 0..3 score for one film.

    Score dimensions:
        +1 sequence token overlap
        +1 zone role overlap
        +1 price verdict overlap or structural-event match

    Hard exclusions force score=0 and mark excluded=True.
    Source visibility below the film requirement also forces score=0.
    """
    current_sequence = _as_list(context.get("sequence_signature"))
    current_zones = _as_list(context.get("zone_roles"))
    current_verdicts = _as_list(context.get("price_verdicts"))
    current_moves = _as_list(context.get("move_roles"))
    current_tokens = current_sequence + current_zones + current_verdicts + current_moves + _as_list(context.get("last_structural_event"))

    if has_hard_exclusion(current_tokens):
        return {
            "film_id": film["film_id"],
            "score": 0,
            "excluded": True,
            "exclusion_reason": "HARD_EXCLUSION_PAIR",
            "source_mode": get_field_memory_source_tag(film.get("source_date", "")),
        }

    film_exclusions = {_upper(item) for item in _as_list(film.get("exclusion_if_same_dir"))}
    current_upper = {_upper(item) for item in current_tokens}
    direct_exclusions = sorted(film_exclusions.intersection(current_upper))
    if direct_exclusions:
        return {
            "film_id": film["film_id"],
            "score": 0,
            "excluded": True,
            "exclusion_reason": "FILM_EXCLUSION_IF_SAME_DIR:" + ",".join(direct_exclusions),
            "source_mode": get_field_memory_source_tag(film.get("source_date", "")),
        }

    actual_visibility = context.get("data_visibility", context.get("data_visibility_required", "TACTICAL_OK"))
    if not _visibility_ok(str(film.get("data_visibility_required", "TACTICAL_OK")), str(actual_visibility)):
        return {
            "film_id": film["film_id"],
            "score": 0,
            "excluded": True,
            "exclusion_reason": "SOURCE_VISIBILITY_BELOW_REQUIRED",
            "source_mode": get_field_memory_source_tag(film.get("source_date", "")),
        }

    sequence_score = _intersection_score(current_sequence, film.get("sequence_signature", []))
    zone_score = _intersection_score(current_zones, film.get("zone_roles", []))
    verdict_score = _intersection_score(current_verdicts, film.get("price_verdicts", []))
    structural_score = 1 if _upper(context.get("last_structural_event")) == _upper(film.get("last_structural_event")) and context.get("last_structural_event") else 0
    move_score = _intersection_score(current_moves, film.get("move_roles_expected", []))

    third_dimension = 1 if (verdict_score or structural_score or move_score) else 0
    score = int(sequence_score + zone_score + third_dimension)

    return {
        "film_id": film["film_id"],
        "score": max(0, min(3, score)),
        "excluded": False,
        "source_date": film.get("source_date"),
        "source_mode": get_field_memory_source_tag(film.get("source_date", "")),
        "memory_rule": film.get("memory_rule", ""),
        "matched_dimensions": {
            "sequence": bool(sequence_score),
            "zone": bool(zone_score),
            "verdict_or_structure_or_move": bool(third_dimension),
        },
    }


def match_field_memory(context: Context, *, source_date: Optional[str] = None, min_score: int = 1) -> List[Dict[str, Any]]:
    """Match current B9/B6 context against the 15-film library.

    Args:
        context: current scene descriptors.
        source_date: optional exact filter, e.g. "2026-05-15".
        min_score: minimum returned score, default 1.

    Returns:
        List sorted by score DESC then film_id ASC. Excluded films are omitted.
    """
    results: List[Dict[str, Any]] = []
    for film in FILM_LIBRARY:
        if source_date is not None and str(film.get("source_date")) != str(source_date):
            continue
        result = score_film_match(context, film)
        if not result.get("excluded") and int(result.get("score", 0)) >= min_score:
            results.append(result)

    return sorted(results, key=lambda item: (-int(item.get("score", 0)), str(item.get("film_id", ""))))


def best_field_memory_match(context: Context, *, source_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
    matches = match_field_memory(context, source_date=source_date, min_score=1)
    return matches[0] if matches else None


__all__ = [
    "FILM_LIBRARY",
    "HARD_EXCLUSION_PAIRS",
    "film_ids",
    "get_film_by_id",
    "has_hard_exclusion",
    "score_film_match",
    "match_field_memory",
    "best_field_memory_match",
]
