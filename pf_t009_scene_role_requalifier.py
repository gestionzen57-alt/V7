"""
T0140 - B9 Scene Role Requalifier V0.

Read-only helper that enriches B9/T009 moments with a scene-role reading.
It does not decide, predict, emit orders, write databases, call dashboards, or call Telegram.

Doctrine:
B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
Ne lis pas l'absorption comme une direction.
Lis ou elle deplace la memoire.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0140_B9_SCENE_ROLE_REQUALIFIER_V0"

FORBIDDEN_TERMS = (
    "BUY", "SELL", "ACHETER", "VENDRE", "LONG ", "SHORT ",
    "probability of success", "probabilite de succes", "taux de reussite",
    "trade signal", "signal d'achat", "signal de vente",
)

REQUIRED_FIELDS = [
    "b9_scene_role_version",
    "b9_scene_role_state",
    "b9_scene_role_code",
    "b9_scene_role_fr",
    "b9_scene_role_reason_fr",
    "b9_scene_role_evidence",
    "b9_scene_role_limits",
    "b9_scene_role_requalification_source",
]

ROLE_ORDER = [
    "RETEST_FAILED_REJECTION_NODE",
    "FAILED_REINTEGRATION_NODE",
    "HIGH_REJECTION_NODE",
    "LOW_ZONE_DEFENDED_REACTION",
    "PULLBACK_ABSORBED_RECONSTRUCTION",
    "CENTER_MIGRATION_DOWN_MEMORY_SHIFT",
    "CENTER_MIGRATION_UP_MEMORY_SHIFT",
    "PROGRESSIVE_FIRST_LEG",
    "PROGRESSIVE_SECOND_LEG_CANDIDATE",
    "CORRECTIVE_BREATH_NO_PROGRESS",
    "ABSORPTION_SHELF_FRICTION",
    "EFFORT_WITHOUT_RESULT_FRICTION",
    "ZONE_DECISION_PENDING",
    "SCENE_ROLE_REVIEW_REQUIRED",
]


def _s(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    return str(value).strip()


def _u(value: Any) -> str:
    return _s(value).upper()


def _f(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "null", "None"):
            return default
        return float(value)
    except Exception:
        return default


def _listify(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _contains_any(text: str, words: Iterable[str]) -> bool:
    t = _u(text)
    return any(w.upper() in t for w in words)


def detect_forbidden_language(obj: Any, prefix: str = "") -> List[str]:
    hits: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            hits.extend(detect_forbidden_language(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits.extend(detect_forbidden_language(v, f"{prefix}[{i}]"))
    elif isinstance(obj, str):
        upper = obj.upper()
        for term in FORBIDDEN_TERMS:
            if term.upper() in upper:
                hits.append(f"{prefix}:{term}")
    return hits


def _evidence(moment: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "label_fr": _s(moment.get("label_fr") or moment.get("label") or moment.get("moment_type")),
        "moment_type": _s(moment.get("moment_type")),
        "effort_result_progress_state": _s(moment.get("b9_effort_result_progress_state")),
        "progress_type": _s(moment.get("b9_progress_type")),
        "movement_role": _s(moment.get("b9_movement_role")),
        "memory_shift_state": _s(moment.get("b9_memory_shift_state")),
        "retest_result": _s(moment.get("retest_result") or moment.get("b9_native_retest_judgment")),
        "source_gate_state": _s(moment.get("b9_source_quality_gate_state")),
        "center_path_shape": _s(moment.get("b9_center_path_shape")),
        "internal_progress_state": _s(moment.get("b9_internal_progress_state")),
        "session": _s(moment.get("b9_session")),
        "raw_texture_role": _s(moment.get("raw_texture_role")),
        "center_delta_pips": _f(moment.get("center_delta") or moment.get("b9_center_net_delta_pips") or moment.get("raw_delta_pips")),
        "center_range_pips": _f(moment.get("center_range") or moment.get("b9_center_range_pips") or moment.get("raw_range_pips")),
    }


def _base_limits(moment: Dict[str, Any]) -> List[str]:
    limits: List[str] = [
        "role de scene interpretatif, pas decisionnel",
        "aucun ordre directionnel, aucun ordre d'execution",
        "aucune statistique de reussite",
    ]
    source_state = _u(moment.get("b9_source_quality_gate_state"))
    visibility = _u(moment.get("data_visibility"))
    source_mode = _u(moment.get("source_mode"))
    verdict = _u(moment.get("proxy_vs_raw_verdict"))
    if "PROXY" in source_mode or "RECONSTRUCT" in visibility:
        limits.append("lecture proxy ou reconstruite: ne pas durcir en verite raw")
    if "NUANCED" in verdict or "NUANCED" in source_state:
        limits.append("raw nuance la scene: ne pas presenter comme confirmation dure")
    if "RAW_UNAVAILABLE" in verdict or "RAW_UNAVAILABLE" in source_state:
        limits.append("raw indisponible: role utilisable seulement pour audit, pas memoire active")
    if not _s(moment.get("retest_result") or moment.get("b9_native_retest_judgment")):
        limits.append("retest non visible ou non fourni: role moins tranche")
    return limits


def _make(role: str, state: str, fr: str, reason: str, ev: Dict[str, Any], limits: List[str]) -> Dict[str, Any]:
    return {
        "b9_scene_role_version": VERSION,
        "b9_scene_role_state": state,
        "b9_scene_role_code": role,
        "b9_scene_role_fr": fr,
        "b9_scene_role_reason_fr": reason,
        "b9_scene_role_evidence": ev,
        "b9_scene_role_limits": limits,
        "b9_scene_role_requalification_source": "T0140_RULE_BASED_SCENE_ROLE_REQUALIFICATION_V0",
    }


def classify_scene_role(moment: Dict[str, Any], previous: Dict[str, Any] | None = None, next_moment: Dict[str, Any] | None = None) -> Dict[str, Any]:
    ev = _evidence(moment)
    limits = _base_limits(moment)
    text = " ".join(_s(v) for v in [
        moment.get("label_fr"), moment.get("moment_type"), moment.get("reading_fr"),
        moment.get("b9_effort_result_progress_state"), moment.get("b9_progress_type"),
        moment.get("b9_movement_role"), moment.get("b9_memory_shift_state"),
        moment.get("b9_native_retest_judgment"), moment.get("retest_result"),
        moment.get("b9_center_path_shape"), moment.get("b9_internal_progress_state"),
    ])
    up = _u(text)
    cd = ev["center_delta_pips"]
    cr = abs(ev["center_range_pips"])
    retest = _u(ev.get("retest_result"))
    erp = _u(ev.get("effort_result_progress_state"))
    progress = _u(ev.get("progress_type"))
    memory = _u(ev.get("memory_shift_state"))
    path = _u(ev.get("center_path_shape"))

    if "RAW_UNAVAILABLE" in _u(moment.get("proxy_vs_raw_verdict")) or "RAW_UNAVAILABLE" in _u(moment.get("b9_source_quality_gate_state")):
        return _make(
            "SCENE_ROLE_REVIEW_REQUIRED",
            "B9_SCENE_ROLE_REJECT_RAW_UNAVAILABLE",
            "Lecture de role rejetee pour memoire active: raw indisponible.",
            "La scene peut rester lisible en audit, mais la source ne permet pas une memoire active propre.",
            ev, limits,
        )

    if "FAILED_REINTEGRATION" in retest or "FAILED_REINTEGRATION" in up:
        return _make(
            "FAILED_REINTEGRATION_NODE",
            "B9_SCENE_ROLE_READY",
            "Node de reintegration echouee.",
            "Le prix tente de revenir dans la zone mais ne reconstruit pas l'acceptation; la scene change de role.",
            ev, limits,
        )

    if "RETEST_FAILED" in retest or "RETEST FAILED" in retest or "RETEST_ECHOUE" in retest or "RETEST ECHOUE" in up or "BREAK_RETEST_FAILED" in up:
        return _make(
            "RETEST_FAILED_REJECTION_NODE",
            "B9_SCENE_ROLE_READY",
            "Retest echoue: reprise refusee.",
            "Le retest juge la scene: la tentative ne tient pas et la memoire precedente reste dominante ou se deplace contre la tentative.",
            ev, limits,
        )

    if "HIGH_REJECTION" in up or "REJET HAUT" in up or "REJECTION" in up and cd < 0:
        return _make(
            "HIGH_REJECTION_NODE",
            "B9_SCENE_ROLE_READY",
            "Node de rejet haut.",
            "La projection haute ne se maintient pas; le haut devient zone de rejet ou de friction.",
            ev, limits,
        )

    if "LOW_ZONE_DEFENDED" in up or "ZONE BASSE DEFENDUE" in up or "LOWER_ZONE_DEFENDED" in up:
        return _make(
            "LOW_ZONE_DEFENDED_REACTION",
            "B9_SCENE_ROLE_READY",
            "Zone basse defendue: reaction apres pression basse.",
            "Le bas ne cede pas au test; le rebond peut etre lu comme reaction de zone, pas comme verite directionnelle.",
            ev, limits,
        )

    if "PULLBACK_ABSORBED" in up or "PULLBACK ABSORBE" in up:
        return _make(
            "PULLBACK_ABSORBED_RECONSTRUCTION",
            "B9_SCENE_ROLE_READY",
            "Pullback absorbe: reconstruction possible de scene.",
            "Le retour ne casse pas la provenance; la scene peut se reconstruire autour du mouvement precedent.",
            ev, limits,
        )

    if "CENTER_MIGRATION" in erp or "CENTER_MIGRATION" in progress or "CENTER_MIGRATION" in up or "CENTRE" in up and ("DESCEND" in up or cd < -2.0):
        if cd < 0 or "DOWN" in up or "DESCEND" in up:
            return _make(
                "CENTER_MIGRATION_DOWN_MEMORY_SHIFT",
                "B9_SCENE_ROLE_READY",
                "Centre de gravite qui descend: memoire qui migre vers le bas.",
                "L'absorption ne bloque pas la pression; elle accompagne un deplacement de memoire par paliers.",
                ev, limits,
            )
        return _make(
            "CENTER_MIGRATION_UP_MEMORY_SHIFT",
            "B9_SCENE_ROLE_READY",
            "Centre de gravite qui monte: memoire qui migre vers le haut.",
            "Le flux reprend du terrain par paliers et deplace la memoire active.",
            ev, limits,
        )

    if "PROGRESSIVE_WAVE" in erp or "PROGRESSIVE" in progress or "VAGUE PROGRESSIVE" in up:
        # Second leg candidate if previous role was absorbed/corrective or if retest is accepted.
        prev_text = _u(previous or {})
        if previous and ("PULLBACK" in prev_text or "CORRECTIVE" in prev_text or "ABSORPTION" in prev_text or "ACCEPTED" in retest):
            return _make(
                "PROGRESSIVE_SECOND_LEG_CANDIDATE",
                "B9_SCENE_ROLE_READY",
                "Deuxieme jambe candidate: progression apres respiration ou absorption.",
                "La vague produit du progres apres une zone de respiration ou de friction; elle peut requalifier la scene en reconstruction.",
                ev, limits,
            )
        return _make(
            "PROGRESSIVE_FIRST_LEG",
            "B9_SCENE_ROLE_READY",
            "Premiere jambe progressive: le flux avance et deplace la memoire.",
            "L'effort produit du resultat et du progres; la scene avance au lieu de seulement respirer.",
            ev, limits,
        )

    if "CORRECTIVE" in erp or "CORRECTIVE" in progress or "RESPIRATION" in up or "BREATH" in up:
        return _make(
            "CORRECTIVE_BREATH_NO_PROGRESS",
            "B9_SCENE_ROLE_READY",
            "Respiration corrective sans progres durable.",
            "Le prix bouge, mais ne deplace pas proprement la memoire active; la scene respire plus qu'elle ne progresse.",
            ev, limits,
        )

    if "ABSORPTION_WITHOUT_PROGRESS" in erp or "EFFORT_WITHOUT_RESULT" in erp or "EFFORT SANS" in up:
        # If high dwell/range but no net displacement -> shelf/friction.
        role = "ABSORPTION_SHELF_FRICTION" if cr >= 2.0 else "EFFORT_WITHOUT_RESULT_FRICTION"
        fr = "Palier d'absorption / friction locale." if role == "ABSORPTION_SHELF_FRICTION" else "Effort sans resultat: friction locale."
        reason = "Beaucoup d'effort apparait, mais le resultat et le progres restent limites; B9 lit une zone de frein, pas une direction."
        return _make(role, "B9_SCENE_ROLE_READY", fr, reason, ev, limits)

    if "ABSORPTION_WITH_PROGRESS" in erp:
        direction = "bas" if cd < 0 else "haut"
        return _make(
            "CENTER_MIGRATION_DOWN_MEMORY_SHIFT" if cd < 0 else "CENTER_MIGRATION_UP_MEMORY_SHIFT",
            "B9_SCENE_ROLE_READY",
            f"Absorption avec progres: memoire qui migre vers le {direction}.",
            "L'absorption ne bloque pas; elle accompagne le deplacement du centre par paliers.",
            ev, limits,
        )

    if "DECISION" in up or "ZONE" in up:
        return _make(
            "ZONE_DECISION_PENDING",
            "B9_SCENE_ROLE_REVIEW",
            "Zone de decision: jugement encore ouvert.",
            "Le flux travaille une zone mais le retest/verdict prix ne tranche pas encore proprement.",
            ev, limits,
        )

    return _make(
        "SCENE_ROLE_REVIEW_REQUIRED",
        "B9_SCENE_ROLE_REVIEW",
        "Role de scene a revoir.",
        "Les preuves disponibles ne suffisent pas pour requalifier proprement le moment.",
        ev, limits,
    )


def enrich_moment_with_scene_role(moment: Dict[str, Any], previous: Dict[str, Any] | None = None, next_moment: Dict[str, Any] | None = None) -> Dict[str, Any]:
    enriched = deepcopy(moment)
    enriched.update(classify_scene_role(enriched, previous=previous, next_moment=next_moment))
    return enriched


def enrich_sequence_summary_scene_roles(summary: Dict[str, Any]) -> Dict[str, Any]:
    enriched = deepcopy(summary)
    moments = _listify(enriched.get("moments"))
    out: List[Dict[str, Any]] = []
    for i, moment in enumerate(moments):
        if not isinstance(moment, dict):
            continue
        prev = moments[i - 1] if i > 0 and isinstance(moments[i - 1], dict) else None
        nxt = moments[i + 1] if i + 1 < len(moments) and isinstance(moments[i + 1], dict) else None
        out.append(enrich_moment_with_scene_role(moment, prev, nxt))
    enriched["moments"] = out
    metadata = dict(enriched.get("metadata") or {})
    metadata["b9_scene_role_requalifier_version"] = VERSION
    metadata["b9_scene_role_requalifier_policy"] = "INTERPRETATION_ONLY_NO_DECISION"
    enriched["metadata"] = metadata
    return enriched


def validate_enriched_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    moments = _listify(summary.get("moments"))
    missing_counts = {field: 0 for field in REQUIRED_FIELDS}
    state_counts: Dict[str, int] = {}
    role_counts: Dict[str, int] = {}
    for moment in moments:
        if not isinstance(moment, dict):
            continue
        for field in REQUIRED_FIELDS:
            if field not in moment or moment.get(field) in (None, ""):
                missing_counts[field] += 1
        state = _s(moment.get("b9_scene_role_state")) or "UNKNOWN"
        code = _s(moment.get("b9_scene_role_code")) or "UNKNOWN"
        state_counts[state] = state_counts.get(state, 0) + 1
        role_counts[code] = role_counts.get(code, 0) + 1
    missing_counts = {k: v for k, v in missing_counts.items() if v}
    forbidden = detect_forbidden_language(summary)
    return {
        "moments": len([m for m in moments if isinstance(m, dict)]),
        "missing_required_field_counts": missing_counts,
        "state_counts": state_counts,
        "role_counts": role_counts,
        "forbidden_language_hits": forbidden,
        "forbidden_language_hit_count": len(forbidden),
    }
