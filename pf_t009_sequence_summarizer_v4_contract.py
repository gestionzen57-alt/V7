#!/usr/bin/env python3
"""
T0120 - B9 Native Summarizer V4 Contract Patch.

Pure read-only enrichment layer for T009/B9 sequence summaries.
It converts existing B9 moments into a V4 native contract with:
- V1 why/how fields
- V2 scene causality fields
- V3 fractal scene fields
- center path / effort-result-progress / retest / source-quality fields

No DB access. No dashboard. No Telegram. No BUY/SELL. No probability of success.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

VERSION = "T0120_B9_NATIVE_SUMMARIZER_V4_CONTRACT_PATCH_V0"
FORBIDDEN_TERMS = ("BUY", "SELL", "ACHETER", "VENDRE", "PROBABILITY_OF_SUCCESS", "WIN_RATE")


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def _pips_label(value: float) -> str:
    if abs(value) < 0.5:
        return "quasi neutre"
    if value > 0:
        return "centre/prix orienté vers le haut"
    return "centre/prix orienté vers le bas"


def _moment_time(moment: Mapping[str, Any]) -> str:
    return _text(moment.get("time_start") or moment.get("start_time") or "UNKNOWN_TIME")


def _moment_end_time(moment: Mapping[str, Any]) -> str:
    return _text(moment.get("time_end") or moment.get("end_time") or "UNKNOWN_TIME")


def _source_quality_state(moment: Mapping[str, Any]) -> str:
    if _text(moment.get("proxy_vs_raw_verdict")) == "RAW_UNAVAILABLE":
        return "SOURCE_QUALITY_RAW_UNAVAILABLE"
    coverage = _text(moment.get("raw_coverage"))
    raw_ticks = _safe_int(moment.get("raw_tick_count"))
    visibility = _text(moment.get("data_visibility") or moment.get("raw_data_visibility"))
    if coverage == "FULL" and raw_ticks >= 100:
        return "SOURCE_QUALITY_STRONG_RAW_VISIBLE"
    if "RECONSTRUCTED" in visibility or _text(moment.get("source_mode")).endswith("PROXY"):
        return "SOURCE_QUALITY_RECONSTRUCTED_PROXY_VISIBLE"
    if raw_ticks > 0:
        return "SOURCE_QUALITY_PARTIAL_RAW_VISIBLE"
    return "SOURCE_QUALITY_UNKNOWN_OR_THIN"


def infer_center_path_state(moment: Mapping[str, Any]) -> str:
    center_speed = _safe_float(moment.get("b9_center_migration_speed_pips_per_min"), 0.0)
    raw_delta = _safe_float(moment.get("raw_delta_pips"), 0.0)
    pip_delta = _safe_float(moment.get("pip_delta"), 0.0)
    effective = center_speed if abs(center_speed) >= 0.05 else raw_delta if abs(raw_delta) >= 0.3 else pip_delta
    if effective >= 2.0:
        return "CENTER_PATH_ADVANCING_UP_FAST"
    if effective >= 0.3:
        return "CENTER_PATH_ADVANCING_UP"
    if effective <= -2.0:
        return "CENTER_PATH_ADVANCING_DOWN_FAST"
    if effective <= -0.3:
        return "CENTER_PATH_ADVANCING_DOWN"
    return "CENTER_PATH_BLOCKED_OR_ROTATING"


def infer_effort_result_progress_state(moment: Mapping[str, Any]) -> Tuple[str, str]:
    efficiency = _safe_float(moment.get("b9_directional_efficiency"), 0.0)
    effort_ratio = _safe_float(moment.get("b9_effort_result_ratio"), 0.0)
    raw_range = abs(_safe_float(moment.get("raw_range_pips"), 0.0))
    pip_delta = abs(_safe_float(moment.get("pip_delta"), 0.0))
    natural_state = _text(moment.get("b9_absorption_like_state"))
    flow_intent = _text(moment.get("b9_flow_intent_state"))

    if "EFFORT_WITHOUT_RESULT" in natural_state or (effort_ratio >= 12 and efficiency < 0.12):
        return "EFFORT_WITHOUT_RESULT", "FRICTION_OR_ABSORPTION_MEMORY"
    if pip_delta >= 6 or raw_range >= 6 or efficiency >= 0.35:
        if "FLOW_MIXED" in flow_intent and raw_range < 3:
            return "MOVEMENT_WITH_LIMITED_PROGRESS", "CORRECTIVE_OR_ROTATION_MEMORY"
        return "EFFORT_RESULT_PROGRESS", "PROGRESSIVE_WAVE_MEMORY"
    if raw_range >= 2.5:
        return "MOVEMENT_WITH_LIMITED_PROGRESS", "CORRECTIVE_OR_ROTATION_MEMORY"
    return "LOCAL_FRICTION_OR_DECISION", "DECISION_ZONE_MEMORY"


def infer_native_retest_judgment(moment: Mapping[str, Any]) -> str:
    hint = _text(moment.get("retest_outcome_hint"))
    natural = _text(moment.get("b9_retest_natural_state"))
    status = _text(moment.get("b9_retest_source_status"))
    touch_count = _safe_int(moment.get("retest_touch_count") or moment.get("b9_retest_touch_count_proxy"))
    if "NOT_VISIBLE" in hint or "NOT_VISIBLE" in natural or "NOT_VISIBLE" in status:
        return "RETEST_JUDGMENT_NOT_VISIBLE_NATIVE_FIELD_REQUIRED"
    if touch_count <= 0:
        return "RETEST_JUDGMENT_NOT_TOUCHED"
    if "FAILED" in hint or "REJECTION" in hint:
        return "RETEST_JUDGED_REJECTED_OR_FAILED"
    if "ACCEPT" in hint or "HELD" in hint:
        return "RETEST_JUDGED_ACCEPTED_OR_HELD"
    return "RETEST_JUDGMENT_PARTIAL"


def infer_session_chapter(moment: Mapping[str, Any]) -> str:
    center_path = infer_center_path_state(moment)
    erp, _ = infer_effort_result_progress_state(moment)
    retest = infer_native_retest_judgment(moment)
    if "RETEST" in retest and "NOT_VISIBLE" not in retest:
        return "Test / retest"
    if erp == "EFFORT_WITHOUT_RESULT":
        return "Décision de zone"
    if "ADVANCING" in center_path:
        return "Migration de centre"
    if erp == "MOVEMENT_WITH_LIMITED_PROGRESS":
        return "Respiration"
    return "Ouverture / transition"


def infer_scene_role(moment: Mapping[str, Any]) -> str:
    erp, memory_role = infer_effort_result_progress_state(moment)
    center_path = infer_center_path_state(moment)
    if erp == "EFFORT_WITHOUT_RESULT":
        return "EFFORT_WITHOUT_RESULT_SCENE"
    if memory_role == "PROGRESSIVE_WAVE_MEMORY" and "UP" in center_path:
        return "PROGRESSIVE_WAVE_UP_SCENE"
    if memory_role == "PROGRESSIVE_WAVE_MEMORY" and "DOWN" in center_path:
        return "PROGRESSIVE_WAVE_DOWN_SCENE"
    if memory_role == "CORRECTIVE_OR_ROTATION_MEMORY":
        return "CORRECTIVE_OR_ROTATION_SCENE"
    return "LOCAL_DECISION_SCENE"


def _build_scene_id(moment: Mapping[str, Any], index: int) -> str:
    seed = "|".join([
        _moment_time(moment),
        _moment_end_time(moment),
        _text(moment.get("source_mode")),
        _text(moment.get("raw_texture_role")),
        str(index),
    ])
    return "B9V4_%s_%s" % (_moment_time(moment)[:10].replace("-", ""), hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10].upper())


def _what_happens_fr(moment: Mapping[str, Any]) -> str:
    center_path = infer_center_path_state(moment)
    erp, _ = infer_effort_result_progress_state(moment)
    raw_texture = _text(moment.get("raw_texture_role"), "texture raw non spécifiée")
    if erp == "EFFORT_WITHOUT_RESULT":
        return "Le flux produit de l'effort, mais le résultat directionnel reste limité; la scène ressemble à une friction ou absorption locale."
    if "ADVANCING_UP" in center_path:
        return "Le centre de gravité progresse vers le haut par déplacement mesurable, avec texture raw à conserver comme preuve de contexte."
    if "ADVANCING_DOWN" in center_path:
        return "Le centre de gravité progresse vers le bas par déplacement mesurable, avec texture raw à conserver comme preuve de contexte."
    return "La scène travaille une zone locale sans déplacement de mémoire suffisamment net. Texture: %s." % raw_texture


def _why_it_matters_fr(moment: Mapping[str, Any]) -> str:
    erp, memory_role = infer_effort_result_progress_state(moment)
    if erp == "EFFORT_WITHOUT_RESULT":
        return "C'est utile pour B9 car l'effort sans progrès peut signaler une barrière, une absorption ou une zone mémoire en construction."
    if memory_role == "PROGRESSIVE_WAVE_MEMORY":
        return "C'est utile pour B9 car l'effort produit du résultat et déplace la mémoire de la scène."
    if memory_role == "CORRECTIVE_OR_ROTATION_MEMORY":
        return "C'est utile pour B9 car le mouvement existe mais peut rester respiration ou correction sans nouveau territoire durable."
    return "C'est utile pour B9 comme zone de décision locale à relier au contexte précédent et au retest."


def _how_it_happened_fr(moment: Mapping[str, Any]) -> str:
    raw_ticks = _safe_int(moment.get("raw_tick_count"))
    raw_delta = _safe_float(moment.get("raw_delta_pips"), 0.0)
    raw_range = _safe_float(moment.get("raw_range_pips"), 0.0)
    ratio = _safe_float(moment.get("b9_effort_result_ratio"), 0.0)
    return "Lecture par microfilm: raw_tick_count=%s, raw_delta_pips=%.2f, raw_range_pips=%.2f, effort_result_ratio=%.2f." % (raw_ticks, raw_delta, raw_range, ratio)


def _mechanism_fr(moment: Mapping[str, Any]) -> str:
    center_path = infer_center_path_state(moment)
    erp, memory_role = infer_effort_result_progress_state(moment)
    retest = infer_native_retest_judgment(moment)
    return "Mécanisme: %s + %s + %s. Rôle mémoire: %s." % (center_path, erp, retest, memory_role)


def _proof_summary_fr(moment: Mapping[str, Any]) -> str:
    verdict = _text(moment.get("proxy_vs_raw_verdict"), "UNKNOWN_RAW_VERDICT")
    quality = _source_quality_state(moment)
    visibility = _text(moment.get("data_visibility"), "UNKNOWN_VISIBILITY")
    source_mode = _text(moment.get("source_mode"), "UNKNOWN_SOURCE_MODE")
    return "Preuves: source_mode=%s, data_visibility=%s, proxy_vs_raw_verdict=%s, source_quality=%s." % (source_mode, visibility, verdict, quality)


def _cause_reaction_consequence(moment: Mapping[str, Any], previous: Optional[Mapping[str, Any]]) -> Tuple[str, str, str, str, str]:
    center_path = infer_center_path_state(moment)
    erp, memory_role = infer_effort_result_progress_state(moment)
    prev_role = infer_scene_role(previous) if previous else "NO_PREVIOUS_CONTEXT"
    previous_context = "Contexte précédent: %s." % prev_role if previous else "Premier moment disponible; contexte précédent non disponible dans ce payload."
    if previous is None:
        cause = "Cause non déduite: début de séquence."
    elif erp == "EFFORT_WITHOUT_RESULT":
        cause = "Le flux arrive sur une zone où l'effort ne produit pas de progrès net."
    elif "ADVANCING" in center_path:
        cause = "Le moment précédent laisse une mémoire que le flux teste ou déplace."
    else:
        cause = "La scène précédente laisse une zone de décision encore active."

    if erp == "EFFORT_WITHOUT_RESULT":
        reaction = "Réaction: le prix travaille la zone sans déplacement net de mémoire."
        consequence = "Conséquence: conserver la zone comme friction ou absorption potentielle."
        memory_shift = "La mémoire ne se déplace pas encore clairement."
    elif memory_role == "PROGRESSIVE_WAVE_MEMORY":
        direction = "vers le haut" if "UP" in center_path else "vers le bas"
        reaction = "Réaction: le flux avance %s et transforme l'effort en déplacement." % direction
        consequence = "Conséquence: la mémoire active se déplace %s." % direction
        memory_shift = "Mémoire déplacée; le centre path doit être conservé."
    else:
        reaction = "Réaction: le flux respire ou corrige sans validation dure."
        consequence = "Conséquence: garder une lecture alternative active."
        memory_shift = "Mémoire partiellement déplacée ou encore en test."

    retest = infer_native_retest_judgment(moment)
    if "NOT_VISIBLE" in retest:
        retest_role = "Retest non visible; garder le jugement de zone en attente."
    elif "ACCEPTED" in retest or "HELD" in retest:
        retest_role = "Retest visible: la zone semble acceptée ou tenue selon les champs disponibles."
    elif "FAILED" in retest or "REJECTED" in retest:
        retest_role = "Retest visible: la zone est rejetée ou échoue selon les champs disponibles."
    else:
        retest_role = "Retest partiel; ne pas durcir le jugement."

    return previous_context, cause, reaction, consequence, memory_shift + " " + retest_role


def enrich_moment_v4(moment: Mapping[str, Any], index: int = 0, previous: Optional[Mapping[str, Any]] = None) -> Dict[str, Any]:
    enriched: Dict[str, Any] = dict(moment)
    scene_id = _build_scene_id(moment, index)
    scene_role = infer_scene_role(moment)
    center_path = infer_center_path_state(moment)
    erp_state, memory_role = infer_effort_result_progress_state(moment)
    retest_judgment = infer_native_retest_judgment(moment)
    session_chapter = infer_session_chapter(moment)
    prev_context, cause, reaction, consequence, memory_shift_retest = _cause_reaction_consequence(moment, previous)

    enriched.update({
        "b9_v4_contract_version": VERSION,
        "b9_v4_native_contract_state": "B9_V4_CONTRACT_ENRICHED",
        "b9_v4_timestamp_policy": "CANONICAL_TIME_FIELDS_PRESERVED_NO_SHIFTED_TIME_REWRITE",
        "b9_v4_forbidden_language_policy": "NO_BUY_SELL_NO_PROBABILITY_OF_SUCCESS",
        "what_happens_fr": _what_happens_fr(moment),
        "why_it_matters_fr": _why_it_matters_fr(moment),
        "how_it_happened_fr": _how_it_happened_fr(moment),
        "mechanism_fr": _mechanism_fr(moment),
        "proof_summary_fr": _proof_summary_fr(moment),
        "previous_context_fr": prev_context,
        "cause_fr": cause,
        "reaction_fr": reaction,
        "consequence_fr": consequence,
        "memory_shift_fr": memory_shift_retest,
        "retest_role_fr": memory_shift_retest.split(" ", 1)[1] if " " in memory_shift_retest else memory_shift_retest,
        "scene_id": scene_id,
        "scene_role": scene_role,
        "parent_scene": "B9_SEQUENCE_%s" % _moment_time(moment)[:10],
        "child_moments": [],
        "session_chapter": session_chapter,
        "fractal_reading_fr": "Microfilm → moment → scène: %s; %s; %s." % (center_path, erp_state, retest_judgment),
        "b9_center_path_state": center_path,
        "b9_effort_result_progress_state": erp_state,
        "b9_progress_type": memory_role,
        "b9_native_retest_judgment": retest_judgment,
        "b9_source_quality_native_state": _source_quality_state(moment),
        "b9_v4_limits": [
            "read-only enrichment layer",
            "no DB write",
            "no dashboard",
            "no Telegram",
            "no BUY/SELL language",
            "no probability of success",
            "retest remains pending when not visible",
            "proxy fields remain proxy fields and are not hardened into raw truth",
        ],
    })
    return enriched


def enrich_sequence_summary_v4(summary: Mapping[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = dict(summary)
    moments = list(summary.get("moments") or summary.get("sequence_moments") or [])
    enriched_moments: List[Dict[str, Any]] = []
    previous: Optional[Mapping[str, Any]] = None
    for idx, moment in enumerate(moments):
        enriched = enrich_moment_v4(moment, idx, previous)
        enriched_moments.append(enriched)
        previous = enriched
    out["moments"] = enriched_moments
    metadata = dict(out.get("metadata") or {})
    metadata.update({
        "b9_v4_contract_version": VERSION,
        "b9_v4_contract_applied_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "b9_v4_contract_policy": "READ_ONLY_NATIVE_CONTRACT_ENRICHMENT_NO_DECISION",
        "b9_v4_moment_count": len(enriched_moments),
    })
    out["metadata"] = metadata
    return out


def scan_forbidden_language(payload: Any) -> List[str]:
    """Scan decision-like language in reading fields only.

Policy/limits fields intentionally contain strings such as NO_BUY_SELL to
assert the guardrail. Those guardrail declarations are not violations.
"""
    readable_suffixes = ("_fr", "reading", "label", "role", "state", "judgment", "chapter")
    texts: List[str] = []

    def walk(obj: Any, key: str = "") -> None:
        lowered = key.lower()
        if "policy" in lowered or "limit" in lowered or "forbidden" in lowered:
            return
        if isinstance(obj, Mapping):
            for k, v in obj.items():
                walk(v, str(k))
        elif isinstance(obj, list):
            for item in obj:
                walk(item, key)
        elif isinstance(obj, str):
            if key.endswith(readable_suffixes) or any(token in lowered for token in ("reading", "label", "role", "state", "judgment", "chapter")):
                texts.append(obj.upper())

    walk(payload)
    text = "\n".join(texts)
    return sorted({term for term in FORBIDDEN_TERMS if term in text})


def summarize_contract_coverage(summary: Mapping[str, Any]) -> Dict[str, Any]:
    moments = list(summary.get("moments") or [])
    required = [
        "what_happens_fr", "why_it_matters_fr", "how_it_happened_fr", "mechanism_fr", "proof_summary_fr",
        "previous_context_fr", "cause_fr", "reaction_fr", "consequence_fr", "memory_shift_fr", "retest_role_fr",
        "scene_id", "scene_role", "parent_scene", "child_moments", "session_chapter", "fractal_reading_fr",
        "b9_center_path_state", "b9_effort_result_progress_state", "b9_native_retest_judgment", "b9_source_quality_native_state",
    ]
    counts = {field: 0 for field in required}
    for moment in moments:
        for field in required:
            if field in moment and moment[field] not in (None, ""):
                counts[field] += 1
    missing = {k: len(moments) - v for k, v in counts.items() if len(moments) - v > 0}
    state_counts: Dict[str, int] = {}
    retest_counts: Dict[str, int] = {}
    for moment in moments:
        state_counts[_text(moment.get("b9_effort_result_progress_state"), "UNKNOWN")] = state_counts.get(_text(moment.get("b9_effort_result_progress_state"), "UNKNOWN"), 0) + 1
        retest_counts[_text(moment.get("b9_native_retest_judgment"), "UNKNOWN")] = retest_counts.get(_text(moment.get("b9_native_retest_judgment"), "UNKNOWN"), 0) + 1
    return {
        "version": VERSION,
        "moment_count": len(moments),
        "required_fields": required,
        "field_coverage_counts": counts,
        "missing_required_field_counts": missing,
        "effort_result_progress_counts": state_counts,
        "native_retest_judgment_counts": retest_counts,
        "forbidden_language_hits": scan_forbidden_language(summary),
    }
