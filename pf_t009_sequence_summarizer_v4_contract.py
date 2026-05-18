"""T0120/T0121 B9 Native Summarizer V4 contract helpers.

Read-only enrichment layer for T009/B9 sequence summaries.
No DB write. No dashboard. No Telegram. No BUY/SELL. No probability of success.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, MutableMapping

VERSION = "B9_NATIVE_SUMMARIZER_V4_CONTRACT_V0"
REQUIRED_V4_FIELDS = [
    "what_happens_fr", "why_it_matters_fr", "how_it_happened_fr", "mechanism_fr", "proof_summary_fr",
    "previous_context_fr", "cause_fr", "reaction_fr", "consequence_fr", "memory_shift_fr", "retest_role_fr",
    "scene_id", "scene_role", "parent_scene", "child_moments", "session_chapter", "fractal_reading_fr",
    "b9_center_path_state", "b9_effort_result_progress_state", "b9_progress_type", "b9_native_retest_judgment",
    "b9_source_quality_native_state", "b9_v4_timestamp_policy",
]
FORBIDDEN_TERMS = ("BUY", "SELL", "probability of success", "success probability")


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _number(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _moment_label(moment: MutableMapping[str, Any] | None) -> str:
    if not moment:
        return "Aucun contexte precedent disponible"
    return _text(moment.get("label_fr") or moment.get("label") or moment.get("moment_type") or moment.get("tag") or "Moment B9")


def _infer_center_delta(moment: MutableMapping[str, Any]) -> float:
    for key in ("center_delta", "center_delta_pips", "raw_delta_pips", "delta_pips"):
        if key in moment:
            return _number(moment.get(key))
    return _number(moment.get("center_end")) - _number(moment.get("center_start"))


def _infer_progress_type(moment: MutableMapping[str, Any]) -> str:
    label = (_moment_label(moment) + " " + _text(moment.get("moment_type"))).lower()
    delta = _infer_center_delta(moment)
    rng = abs(_number(moment.get("center_range") or moment.get("center_range_pips") or moment.get("raw_range_pips")))
    if "effort" in label and ("sans" in label or "without" in label):
        return "EFFORT_WITHOUT_RESULT"
    if "progress" in label or "vague progressive" in label or abs(delta) >= 8.0:
        return "PROGRESSIVE_WAVE"
    if "retest" in label or "decision" in label or "zone" in label:
        return "RETEST_OR_DECISION_AREA"
    if rng >= 5.0 and abs(delta) < rng * 0.45:
        return "CORRECTIVE_OR_ROTATIONAL_WAVE"
    if delta > 0:
        return "CENTER_MIGRATION_UP"
    if delta < 0:
        return "CENTER_MIGRATION_DOWN"
    return "LOCAL_FRICTION"


def _infer_retest(moment: MutableMapping[str, Any]) -> str:
    combined = " ".join(_text(moment.get(k)) for k in ("label_fr", "moment_type", "reading_fr", "retest_role_fr")).lower()
    if "retest" in combined and ("fail" in combined or "echou" in combined or "refus" in combined):
        return "RETEST_FAILED_VISIBLE"
    if "retest" in combined:
        return "RETEST_VISIBLE_PENDING_OR_NEUTRAL"
    if "break" in combined or "cassure" in combined:
        return "BREAK_NEEDS_RETEST"
    return "RETEST_NOT_VISIBLE"


def _infer_source_quality(moment: MutableMapping[str, Any]) -> str:
    verdict = _text(moment.get("proxy_vs_raw_verdict")).upper()
    state = _text(moment.get("source_quality_state")).upper()
    visibility = _text(moment.get("data_visibility")).upper()
    if verdict == "CONFIRMED_BY_RAW" or "STRONG" in state or "HIGH" in state:
        return "SOURCE_QUALITY_STRONG_OR_RAW_CONFIRMED"
    if verdict == "NUANCED_BY_RAW" or "RECONSTRUCTED" in visibility or "PROXY" in visibility:
        return "SOURCE_QUALITY_USABLE_BUT_NUANCED"
    if verdict == "RAW_UNAVAILABLE" or "UNAVAILABLE" in verdict:
        return "SOURCE_QUALITY_RAW_UNAVAILABLE"
    return "SOURCE_QUALITY_PARTIAL_OR_UNKNOWN"


def _session_chapter(progress_type: str) -> str:
    return {
        "EFFORT_WITHOUT_RESULT": "Decision de zone",
        "PROGRESSIVE_WAVE": "Memoire deplacee",
        "RETEST_OR_DECISION_AREA": "Test / retest",
        "CORRECTIVE_OR_ROTATIONAL_WAVE": "Respiration",
        "CENTER_MIGRATION_UP": "Migration de centre",
        "CENTER_MIGRATION_DOWN": "Migration de centre",
        "LOCAL_FRICTION": "Zone de friction locale",
    }.get(progress_type, "Scene locale")


def enrich_moment_v4(moment: MutableMapping[str, Any], index: int = 0, previous: MutableMapping[str, Any] | None = None) -> Dict[str, Any]:
    out = dict(moment)
    label = _moment_label(out)
    progress_type = _infer_progress_type(out)
    delta = _infer_center_delta(out)
    direction = "monte" if delta > 0 else "descend" if delta < 0 else "reste stable"
    retest_state = _infer_retest(out)
    source_state = _infer_source_quality(out)
    out.setdefault("what_happens_fr", f"{label}. Le centre de la scene {direction} et B9 qualifie le role local du flux.")
    out.setdefault("why_it_matters_fr", "Ce moment indique si l'effort de marche deplace vraiment la memoire ou reste bloque dans une zone de friction.")
    out.setdefault("how_it_happened_fr", "Lecture par chemin interne du centre, deplacement effectif, range, effort/resultat/progres et qualite source.")
    out.setdefault("mechanism_fr", f"Mecanisme dominant: {progress_type}. Delta centre estime: {delta:.2f} pips.")
    out.setdefault("proof_summary_fr", f"Preuves: label={label}; progress_type={progress_type}; retest={retest_state}; source={source_state}.")
    out.setdefault("previous_context_fr", _moment_label(previous))
    out.setdefault("cause_fr", "Le moment precedent cree le contexte de zone ou de memoire que ce moment vient tester ou deplacer.")
    out.setdefault("reaction_fr", "Le flux reagit par deplacement, friction, respiration ou test de zone selon le chemin interne observe.")
    out.setdefault("consequence_fr", "La scene conserve, deplace ou met en attente la memoire locale selon l'effort/resultat/progres.")
    out.setdefault("memory_shift_fr", "Memoire deplacee" if progress_type in {"PROGRESSIVE_WAVE", "CENTER_MIGRATION_UP", "CENTER_MIGRATION_DOWN"} else "Memoire non deplacee ou en attente de jugement")
    out.setdefault("retest_role_fr", retest_state)
    out.setdefault("scene_id", f"B9V4_SCENE_{index + 1:04d}")
    out.setdefault("scene_role", progress_type)
    out.setdefault("parent_scene", "B9_SEQUENCE_V4")
    out.setdefault("child_moments", [])
    out.setdefault("session_chapter", _session_chapter(progress_type))
    out.setdefault("fractal_reading_fr", "Ce moment est lu comme une brique du microfilm: event -> moment -> scene -> memoire, pas comme un signal isole.")
    out.setdefault("b9_center_path_state", "CENTER_MOVES_UP" if delta > 0 else "CENTER_MOVES_DOWN" if delta < 0 else "CENTER_STABLE_OR_FLAT")
    out.setdefault("b9_effort_result_progress_state", progress_type)
    out.setdefault("b9_progress_type", progress_type)
    out.setdefault("b9_native_retest_judgment", retest_state)
    out.setdefault("b9_source_quality_native_state", source_state)
    out.setdefault("b9_v4_timestamp_policy", "USE_ORIGINAL_TIME_IF_PRESENT_ELSE_SHIFTED_VISIBLE")
    return out


def _get_moments(summary: MutableMapping[str, Any]) -> List[MutableMapping[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments"):
        value = summary.get(key)
        if isinstance(value, list):
            return value
    return []


def enrich_sequence_summary_v4(summary: MutableMapping[str, Any]) -> Dict[str, Any]:
    enriched = deepcopy(dict(summary))
    moments = _get_moments(enriched)
    enriched_moments = []
    previous = None
    for idx, moment in enumerate(moments):
        if isinstance(moment, MutableMapping):
            new_moment = enrich_moment_v4(moment, idx, previous)
            enriched_moments.append(new_moment)
            previous = new_moment
        else:
            enriched_moments.append(moment)
    for key in ("moments", "sequence_moments", "b9_moments"):
        if isinstance(enriched.get(key), list):
            enriched[key] = enriched_moments
            break
    enriched.setdefault("b9_v4_contract_version", VERSION)
    enriched.setdefault("b9_v4_contract_state", "ENRICHED_NATIVE_CONTRACT")
    enriched.setdefault("b9_v4_forbidden_language_hits", find_forbidden_language(enriched))
    return enriched


def find_forbidden_language(obj: Any) -> List[str]:
    text = json_like_string(obj).upper()
    return [term for term in FORBIDDEN_TERMS if term.upper() in text]


def json_like_string(obj: Any) -> str:
    try:
        import json
        return json.dumps(obj, ensure_ascii=False)
    except Exception:
        return str(obj)
