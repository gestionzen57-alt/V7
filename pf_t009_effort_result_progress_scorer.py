"""B9 Effort / Result / Progress Scorer V0.

Read-only enrichment helpers for T009/B9 sequence summaries.

Doctrine:
- B9 does not search for a trading signal.
- B9 reads the trace left by effort.
- Absorption is not a direction; it is read against result and progress.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

VERSION = "T0129_B9_EFFORT_RESULT_PROGRESS_SCORER_V0"

FORBIDDEN_TERMS = (
    "BUY",
    "SELL",
    "ACHETER",
    "VENDRE",
    "PROBABILITY_OF_SUCCESS",
    "PROBABILITE_DE_SUCCES",
    "PROBABILITÉ DE SUCCÈS",
)

REQUIRED_FIELDS = (
    "b9_effort_score",
    "b9_result_score",
    "b9_progress_score",
    "b9_effort_result_ratio",
    "b9_progress_type",
    "b9_movement_role",
    "b9_memory_shift_state",
    "b9_effort_result_progress_state",
    "b9_effort_result_progress_reading_fr",
    "b9_effort_result_progress_limits",
)

PRESERVED_FIELDS = (
    "date",
    "time_start",
    "time_end",
    "start_time",
    "end_time",
    "label_fr",
    "moment_type",
    "source_family",
    "summary_recovery_type",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "proxy_raw_agreement_state",
    "source_quality_state",
    "raw_texture_role",
)


@dataclass(frozen=True)
class MomentScores:
    effort_score: float
    result_score: float
    progress_score: float
    effort_result_ratio: float
    progress_type: str
    movement_role: str
    memory_shift_state: str
    state: str
    reading_fr: str
    limits: List[str]


def _to_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    f = _to_float(value)
    if f is None:
        return default
    return int(f)


def _clip01(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 1.0:
        return 1.0
    return value


def _abs_num(moment: Mapping[str, Any], keys: Iterable[str]) -> Optional[float]:
    vals: List[float] = []
    for key in keys:
        val = _to_float(moment.get(key))
        if val is not None:
            vals.append(abs(val))
    if not vals:
        return None
    return max(vals)


def _text_blob(moment: Mapping[str, Any]) -> str:
    parts: List[str] = []
    for key, value in moment.items():
        if isinstance(value, str):
            parts.append(value)
        elif isinstance(value, list):
            parts.extend(str(x) for x in value)
    return " ".join(parts).upper()


def _has_absorption_texture(moment: Mapping[str, Any]) -> bool:
    blob = _text_blob(moment)
    return any(token in blob for token in ("ABSORPTION", "FRICTION", "SHELF", "EFFORT_WITHOUT_RESULT"))


def _signed_center_delta(moment: Mapping[str, Any]) -> Optional[float]:
    for key in ("center_delta_pips", "b9_center_delta_pips", "center_delta", "raw_delta_pips", "pip_delta"):
        val = _to_float(moment.get(key))
        if val is not None:
            return val
    start = _to_float(moment.get("center_start"))
    end = _to_float(moment.get("center_end"))
    if start is not None and end is not None:
        # Typical FX price delta to pips. If values are already pips, this remains a conservative fallback.
        return (end - start) * 10000.0
    return None


def compute_effort_score(moment: Mapping[str, Any]) -> float:
    """Compute a broker/source-relative effort score in [0, 1]."""
    explicit = _to_float(moment.get("b9_effort_load"))
    if explicit is not None:
        # b9_effort_load has no universal scale. Use a soft cap around active M1 microfilms.
        return round(_clip01(explicit / 8.0), 4)

    raw_ticks = _to_float(moment.get("raw_tick_count")) or _to_float(moment.get("raw_tick_count_dedup"))
    tick_density = _to_float(moment.get("raw_tick_density_per_minute"))
    event_count = _to_float(moment.get("events")) or _to_float(moment.get("event_count"))
    energy = _to_float(moment.get("energy"))
    texture = _to_float(moment.get("b9_microfilm_texture_score"))
    dwell = _to_float(moment.get("dwell")) or _to_float(moment.get("b9_dwell_seconds"))

    components: List[Tuple[float, float]] = []
    if raw_ticks is not None:
        components.append((_clip01(raw_ticks / 180.0), 0.28))
    if tick_density is not None:
        components.append((_clip01(tick_density / 120.0), 0.22))
    if event_count is not None:
        components.append((_clip01(event_count / 45.0), 0.20))
    if energy is not None:
        components.append((_clip01(abs(energy) / 45.0), 0.18))
    if texture is not None:
        components.append((_clip01(texture), 0.08))
    if dwell is not None:
        # If dwell is seconds, cap at 180s; if already 0..1, this remains fine after clipping.
        components.append((_clip01(dwell / 180.0 if dwell > 1.0 else dwell), 0.04))

    if not components:
        return 0.0
    weighted = sum(v * w for v, w in components)
    total_w = sum(w for _, w in components)
    return round(_clip01(weighted / total_w), 4)


def compute_result_score(moment: Mapping[str, Any]) -> float:
    """Compute actual directional result score in [0, 1]."""
    magnitude = _abs_num(
        moment,
        (
            "raw_delta_pips",
            "center_delta_pips",
            "b9_center_delta_pips",
            "center_delta",
            "pip_delta",
            "bid_delta_pips",
        ),
    )
    if magnitude is None:
        signed = _signed_center_delta(moment)
        magnitude = abs(signed) if signed is not None else 0.0
    return round(_clip01(magnitude / 18.0), 4)


def compute_progress_score(moment: Mapping[str, Any], result_score: float) -> float:
    """Compute structural progress score in [0, 1]."""
    range_pips = _abs_num(
        moment,
        (
            "center_range_pips",
            "center_range",
            "raw_range_pips",
            "price_range_pips",
            "max_favorable_excursion_pips",
        ),
    )
    if range_pips is None:
        range_pips = 0.0

    signed = _signed_center_delta(moment)
    coherence = 0.0
    if signed is not None and range_pips > 0:
        coherence = _clip01(abs(signed) / max(range_pips, 1e-6))
    elif result_score > 0:
        coherence = result_score

    explicit_progress = _to_float(moment.get("progress_score"))
    if explicit_progress is not None:
        return round(_clip01(explicit_progress), 4)

    range_component = _clip01(range_pips / 20.0)
    progress = 0.55 * range_component + 0.30 * result_score + 0.15 * coherence
    return round(_clip01(progress), 4)


def _progress_type(moment: Mapping[str, Any], result: float, progress: float) -> str:
    signed = _signed_center_delta(moment)
    if progress >= 0.58 and result >= 0.35:
        return "PROGRESSIVE_EXTENSION"
    if signed is not None and abs(signed) >= 6.0 and result >= 0.30:
        return "CENTER_MIGRATION"
    if result >= 0.20 and progress < 0.45:
        return "CORRECTIVE_BREATH"
    if result < 0.18:
        return "NO_PROGRESS"
    return "MIXED_PROGRESS"


def score_moment(moment: Mapping[str, Any]) -> MomentScores:
    effort = compute_effort_score(moment)
    result = compute_result_score(moment)
    progress = compute_progress_score(moment, result)
    ratio = round(effort / max(result, 0.05), 4)
    failed = _to_float(moment.get("failed_displacement")) or _to_float(moment.get("failed_displacement_mean")) or _to_float(moment.get("b9_failed_displacement")) or 0.0
    progress_type = _progress_type(moment, result, progress)
    absorption = _has_absorption_texture(moment)
    signed = _signed_center_delta(moment)
    blob = _text_blob(moment)
    migration_explicit = "CENTER_MIGRATION" in blob or "CENTRE DE GRAVIT" in blob or "CENTER MIGRATION" in blob

    limits = [
        "score relatif au microfilm et à la source disponible",
        "ne produit aucune décision de trade",
        "ne remplace pas le jugement du retest ni la source quality",
    ]

    if migration_explicit and result >= 0.30:
        state = "CENTER_MIGRATION"
        movement_role = "CENTER_DRIFT_DOWN" if signed is not None and signed < 0 else "CENTER_DRIFT_UP"
        memory_shift = "MEMORY_SHIFTING"
        reading = "Le centre de gravité migre: B9 lit un déplacement de mémoire plus qu'un signal isolé."
    elif effort >= 0.55 and result < 0.20:
        if absorption:
            state = "ABSORPTION_WITHOUT_PROGRESS"
            movement_role = "FRICTION_BRAKE"
            reading = "Effort visible sans progrès propre: le flux travaille mais ne déplace pas encore la mémoire."
        else:
            state = "EFFORT_WITHOUT_RESULT"
            movement_role = "EFFORT_STALL"
            reading = "Effort visible mais résultat faible: B9 conserve une lecture de friction, pas une direction."
        memory_shift = "MEMORY_NOT_MOVED"
    elif failed >= 0.75 and result < 0.30:
        state = "FAILED_DISPLACEMENT"
        movement_role = "FAILED_PUSH"
        memory_shift = "MEMORY_CONTESTED"
        reading = "Déplacement tenté mais mal accepté: la scène reste à juger par la réaction suivante."
    elif progress >= 0.58 and result >= 0.35:
        if absorption:
            state = "ABSORPTION_WITH_PROGRESS"
            movement_role = "ABSORBED_PROGRESSIVE_MOVE"
            reading = "Absorption avec centre qui avance: la pression progresse par paliers et déplace la mémoire."
        else:
            state = "PROGRESSIVE_WAVE"
            movement_role = "PROGRESSIVE_MOVE"
            reading = "L'effort produit du résultat et du progrès: le flux déplace la mémoire de scène."
        memory_shift = "MEMORY_SHIFTED"
    elif progress_type == "CENTER_MIGRATION":
        state = "CENTER_MIGRATION"
        movement_role = "CENTER_DRIFT_DOWN" if signed is not None and signed < 0 else "CENTER_DRIFT_UP"
        memory_shift = "MEMORY_SHIFTING"
        reading = "Le centre de gravité migre: B9 lit un déplacement de mémoire plus qu'un signal isolé."
    elif progress_type == "CORRECTIVE_BREATH":
        state = "CORRECTIVE_BREATH"
        movement_role = "REACTION_WITHOUT_NEW_STRUCTURE"
        memory_shift = "MEMORY_NOT_CONFIRMED_SHIFT"
        reading = "Le flux respire dans une structure existante: mouvement visible mais progrès limité."
    else:
        state = "EFFORT_RESULT_PROGRESS_MIXED"
        movement_role = "MIXED_SCENE_ROLE"
        memory_shift = "MEMORY_AMBIGUOUS"
        reading = "Lecture mixte: effort, résultat et progrès ne donnent pas encore un rôle dominant."

    if moment.get("source_mode") == "M1_BAR_PROXY" or "RECONSTRUCTED" in str(moment.get("data_visibility", "")):
        limits.append("lecture proxy/reconstruite: ne pas durcir en vérité raw")
    if str(moment.get("proxy_vs_raw_verdict", "")).upper() == "NUANCED_BY_RAW":
        limits.append("raw nuance la scène: ne pas présenter comme confirmée raw")

    return MomentScores(
        effort_score=round(effort, 4),
        result_score=round(result, 4),
        progress_score=round(progress, 4),
        effort_result_ratio=ratio,
        progress_type=progress_type,
        movement_role=movement_role,
        memory_shift_state=memory_shift,
        state=state,
        reading_fr=reading,
        limits=limits,
    )


def enrich_moment_effort_result_progress(moment: Mapping[str, Any]) -> Dict[str, Any]:
    enriched = dict(moment)
    scores = score_moment(moment)
    enriched.update(
        {
            "b9_effort_score": scores.effort_score,
            "b9_result_score": scores.result_score,
            "b9_progress_score": scores.progress_score,
            "b9_effort_result_ratio": scores.effort_result_ratio,
            "b9_progress_type": scores.progress_type,
            "b9_movement_role": scores.movement_role,
            "b9_memory_shift_state": scores.memory_shift_state,
            "b9_effort_result_progress_state": scores.state,
            "b9_effort_result_progress_reading_fr": scores.reading_fr,
            "b9_effort_result_progress_limits": scores.limits,
        }
    )
    return enriched


def _get_moments(summary: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    moments = summary.get("moments")
    if isinstance(moments, list):
        return moments
    for key in ("sequence_moments", "b9_moments", "items"):
        val = summary.get(key)
        if isinstance(val, list):
            return val
    return []


def enrich_sequence_summary_effort_result_progress(summary: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a copy of a B9/T009 summary enriched with effort/result/progress fields."""
    enriched = deepcopy(dict(summary))
    moments = _get_moments(enriched)
    enriched_moments = [enrich_moment_effort_result_progress(m) for m in moments]
    enriched["moments"] = enriched_moments
    metadata = dict(enriched.get("metadata") or {})
    metadata["b9_effort_result_progress_version"] = VERSION
    metadata["b9_effort_result_progress_policy"] = "READ_ONLY_INTERPRETATION_NO_DECISION"
    metadata["b9_effort_result_progress_doctrine"] = "effort_result_progress_without_order_or_success_rate"
    enriched["metadata"] = metadata
    return enriched


def rows_from_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, moment in enumerate(_get_moments(summary), start=1):
        row = {"moment_index": idx}
        for key in (
            "time_start",
            "time_end",
            "start_time",
            "end_time",
            "label_fr",
            "moment_type",
            "source_mode",
            "data_visibility",
            "proxy_vs_raw_verdict",
            "raw_texture_role",
        ):
            row[key] = moment.get(key, "")
        for key in REQUIRED_FIELDS:
            row[key] = moment.get(key, "")
        rows.append(row)
    return rows


def count_states(summary: Mapping[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for moment in _get_moments(summary):
        state = str(moment.get("b9_effort_result_progress_state", "MISSING"))
        counts[state] = counts.get(state, 0) + 1
    return counts


def missing_required_field_counts(summary: Mapping[str, Any]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for moment in _get_moments(summary):
        for key in REQUIRED_FIELDS:
            value = moment.get(key)
            if value is None or value == "" or value == []:
                counts[key] = counts.get(key, 0) + 1
    return counts


def find_forbidden_language(obj: Any, path: str = "$") -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            hits.extend(find_forbidden_language(value, f"{path}.{key}"))
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            hits.extend(find_forbidden_language(value, f"{path}[{idx}]"))
    elif isinstance(obj, str):
        upper = obj.upper()
        for term in FORBIDDEN_TERMS:
            if term in upper:
                hits.append({"path": path, "term": term})
    return hits


def preservation_diff(before: Mapping[str, Any], after: Mapping[str, Any]) -> List[Dict[str, Any]]:
    before_moments = _get_moments(before)
    after_moments = _get_moments(after)
    diffs: List[Dict[str, Any]] = []
    for idx, (b, a) in enumerate(zip(before_moments, after_moments), start=1):
        for field in PRESERVED_FIELDS:
            if b.get(field) != a.get(field):
                diffs.append(
                    {
                        "moment_index": idx,
                        "field": field,
                        "before": b.get(field),
                        "after": a.get(field),
                    }
                )
    return diffs
