"""T0134 - B9 French Trader Scene Report V0.

Read-only renderer that turns enriched B9/T009 moments into a French trader
scene report. It does not decide, route alerts, write databases, or trigger any
execution surface.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Mapping, Sequence

VERSION = "T0134_B9_FRENCH_TRADER_SCENE_REPORT_V0"

FORBIDDEN_TERMS = (
    "BUY",
    "SELL",
    "ACHETER",
    "VENDRE",
    "PROBABILITY_OF_SUCCESS",
    "PROBABILITE DE SUCCES",
    "PROBABILITÉ DE SUCCÈS",
    "TAUX DE REUSSITE",
    "TAUX DE RÉUSSITE",
)

REPORT_SECTIONS = (
    "ce_que_b9_voit",
    "d_ou_vient_le_prix",
    "zone_active",
    "effort_visible",
    "resultat_obtenu",
    "progres_reel",
    "retest_qui_juge",
    "memoire_deplacee",
    "film_b6_proche",
    "pieges_techniques",
    "ce_que_b9_ne_peut_pas_conclure",
)


def _text(value: Any, fallback: str = "Non renseigné") -> str:
    if value is None:
        return fallback
    if isinstance(value, str):
        return value.strip() or fallback
    if isinstance(value, bool):
        return "oui" if value else "non"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        parts = [_text(x, "").strip() for x in value]
        return "; ".join(p for p in parts if p) or fallback
    return str(value)


def _num(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _moment_label(moment: Mapping[str, Any]) -> str:
    return _text(moment.get("label_fr") or moment.get("reading_fr") or moment.get("moment_type") or moment.get("b9_effort_result_progress_state"), "Moment B9")


def _format_time(moment: Mapping[str, Any]) -> str:
    start = moment.get("time_start_real") or moment.get("time_start") or moment.get("start") or moment.get("timestamp")
    end = moment.get("time_end_real") or moment.get("time_end") or moment.get("end") or start
    if start and end and start != end:
        return f"{start} -> {end}"
    return _text(start, "heure non renseignée")


def _derive_origin(moment: Mapping[str, Any]) -> str:
    previous = moment.get("previous_context_fr") or moment.get("cause_fr")
    if previous:
        return _text(previous)
    source_family = _text(moment.get("source_family") or moment.get("summary_recovery_type"), "provenance source non renseignée")
    source_mode = _text(moment.get("source_mode"), "mode source non renseigné")
    return f"La scène provient d'une lecture {source_family} avec source {source_mode}."


def _derive_zone(moment: Mapping[str, Any]) -> str:
    zone = moment.get("retest_zone") or moment.get("current_zone") or moment.get("zone") or moment.get("zone_status")
    if zone:
        return _text(zone)
    low = moment.get("zone_low") or moment.get("price_low") or moment.get("center_min") or moment.get("b9_center_min")
    high = moment.get("zone_high") or moment.get("price_high") or moment.get("center_max") or moment.get("b9_center_max")
    if low is not None and high is not None:
        return f"Zone travaillée approximative : {low} - {high}."
    return "Zone active non renseignée dans le summary."


def _derive_effort(moment: Mapping[str, Any]) -> str:
    state = moment.get("b9_effort_result_progress_state") or moment.get("moment_type")
    effort = moment.get("b9_effort_score") or moment.get("absorption_mean") or moment.get("avg_absorption")
    failed = moment.get("failed_displacement_mean") or moment.get("avg_failed_displacement")
    parts = []
    if state:
        parts.append(f"État effort/résultat : {_text(state)}.")
    if effort is not None:
        parts.append(f"Score d'effort : {_text(effort)}.")
    if failed is not None:
        parts.append(f"Failed displacement : {_text(failed)}.")
    if moment.get("b9_effort_result_progress_reading_fr"):
        parts.append(_text(moment.get("b9_effort_result_progress_reading_fr")))
    return " ".join(parts) or "Effort visible non quantifié dans cette scène."


def _derive_result(moment: Mapping[str, Any]) -> str:
    result_score = moment.get("b9_result_score")
    delta = moment.get("raw_delta_pips") or moment.get("center_delta") or moment.get("b9_center_net_delta_pips")
    if moment.get("result_fr"):
        return _text(moment.get("result_fr"))
    parts = []
    if result_score is not None:
        parts.append(f"Résultat mesuré : {result_score}.")
    if delta is not None:
        parts.append(f"Déplacement net : {delta} pips environ.")
    if not parts:
        parts.append("Résultat prix non renseigné explicitement.")
    return " ".join(parts)


def _derive_progress(moment: Mapping[str, Any]) -> str:
    progress_state = moment.get("b9_progress_type") or moment.get("b9_internal_progress_state") or moment.get("session_chapter")
    progress_score = moment.get("b9_progress_score")
    center_shape = moment.get("b9_center_path_shape")
    parts = []
    if progress_state:
        parts.append(f"Type de progrès : {_text(progress_state)}.")
    if progress_score is not None:
        parts.append(f"Score de progrès : {_text(progress_score)}.")
    if center_shape:
        parts.append(f"Chemin interne du centre : {_text(center_shape)}.")
    if moment.get("b9_center_path_reading_fr"):
        parts.append(_text(moment.get("b9_center_path_reading_fr")))
    return " ".join(parts) or "Progrès réel non établi dans les champs disponibles."


def _derive_retest(moment: Mapping[str, Any]) -> str:
    visible = moment.get("retest_visible")
    judgment = moment.get("retest_judgment_fr") or moment.get("retest_result") or moment.get("b9_native_retest_judgment")
    limits = moment.get("retest_limits")
    if visible is False:
        return "Retest non visible : la scène reste sans jugement de retest natif."
    parts = []
    if visible is True:
        parts.append("Retest visible.")
    if judgment:
        parts.append(_text(judgment))
    if limits:
        parts.append(f"Limite retest : {_text(limits)}.")
    return " ".join(parts) or "Retest non renseigné dans cette scène."


def _derive_memory_shift(moment: Mapping[str, Any]) -> str:
    memory = moment.get("memory_shift_fr") or moment.get("b9_memory_shift_state") or moment.get("memory_candidate_reason")
    if memory:
        return _text(memory)
    center_state = moment.get("b9_internal_progress_state") or moment.get("b9_center_path_shape")
    if center_state:
        return f"Mémoire lue via le chemin du centre : {_text(center_state)}."
    return "Déplacement de mémoire non confirmé par les champs disponibles."


def _derive_b6(moment: Mapping[str, Any], b6_brief: Mapping[str, Any] | None) -> str:
    if not b6_brief:
        return "Aucun brief B6 fourni à T0134."
    top = b6_brief.get("top_match_film_id") or b6_brief.get("top_match") or b6_brief.get("nearest_film")
    summary = b6_brief.get("b6_similarity_summary_fr") or b6_brief.get("memory_brief_fr") or b6_brief.get("summary_fr")
    parts = []
    if top:
        parts.append(f"Film B6 proche : {_text(top)}.")
    if summary:
        parts.append(_text(summary))
    return " ".join(parts) or "Brief B6 fourni mais sans film dominant lisible."


def _derive_technical_traps(moment: Mapping[str, Any], b6_brief: Mapping[str, Any] | None) -> str:
    traps: List[str] = []
    source_limits = moment.get("b9_source_quality_limits") or moment.get("technical_limits") or moment.get("b9_effort_result_progress_limits")
    if source_limits:
        traps.append(_text(source_limits))
    if moment.get("b9_source_quality_gate_state"):
        traps.append(f"Source quality : {_text(moment.get('b9_source_quality_gate_state'))}.")
    if moment.get("proxy_vs_raw_verdict"):
        traps.append(f"Accord proxy/raw : {_text(moment.get('proxy_vs_raw_verdict'))}.")
    if b6_brief:
        flags = b6_brief.get("b6_false_positive_context_fr") or b6_brief.get("technical_cautions") or b6_brief.get("false_positive_flags")
        if flags:
            traps.append(f"Pièges B6 : {_text(flags)}.")
    return " ".join(traps) or "Aucun piège technique explicite fourni ; conserver la provenance et les limites visibles."


def _cannot_conclude(moment: Mapping[str, Any]) -> str:
    clauses = [
        "B9 ne conclut pas une décision d'exécution.",
        "B9 ne transforme pas une similarité en répétition certaine.",
    ]
    if moment.get("data_visibility") and "RECONSTRUCT" in _text(moment.get("data_visibility")).upper():
        clauses.append("La lecture reconstruite ne devient pas footprint raw complet.")
    if moment.get("proxy_vs_raw_verdict") == "NUANCED_BY_RAW":
        clauses.append("Une scène nuancée par le raw ne devient pas confirmée raw.")
    if moment.get("proxy_vs_raw_verdict") == "RAW_UNAVAILABLE":
        clauses.append("Raw indisponible : scène hors vérité raw active.")
    return " ".join(clauses)


def render_moment_report(moment: Mapping[str, Any], index: int, b6_brief: Mapping[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "moment_index": index,
        "time_range": _format_time(moment),
        "title_fr": _moment_label(moment),
        "ce_que_b9_voit": _text(moment.get("what_happens_fr") or moment.get("reading_fr") or _moment_label(moment)),
        "d_ou_vient_le_prix": _derive_origin(moment),
        "zone_active": _derive_zone(moment),
        "effort_visible": _derive_effort(moment),
        "resultat_obtenu": _derive_result(moment),
        "progres_reel": _derive_progress(moment),
        "retest_qui_juge": _derive_retest(moment),
        "memoire_deplacee": _derive_memory_shift(moment),
        "film_b6_proche": _derive_b6(moment, b6_brief),
        "pieges_techniques": _derive_technical_traps(moment, b6_brief),
        "ce_que_b9_ne_peut_pas_conclure": _cannot_conclude(moment),
        "source_family": _text(moment.get("source_family") or moment.get("summary_recovery_type"), "source non renseignée"),
        "source_mode": _text(moment.get("source_mode"), "source mode non renseigné"),
        "data_visibility": _text(moment.get("data_visibility"), "data visibility non renseignée"),
        "source_quality_gate_state": _text(moment.get("b9_source_quality_gate_state") or moment.get("source_quality_state"), "source quality non renseignée"),
    }


def extract_moments(summary: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    for key in ("moments", "sequence_moments", "items", "rows"):
        value = summary.get(key)
        if isinstance(value, list):
            return [m for m in value if isinstance(m, Mapping)]
    if isinstance(summary, Mapping) and any(k in summary for k in ("moment_type", "label_fr", "time_start")):
        return [summary]
    return []


def build_scene_report(summary: Mapping[str, Any], b6_brief: Mapping[str, Any] | None = None, top_k: int | None = None) -> Dict[str, Any]:
    moments = extract_moments(summary)
    if top_k is not None:
        moments = moments[: max(0, top_k)]
    moment_reports = [render_moment_report(moment, i + 1, b6_brief=b6_brief) for i, moment in enumerate(moments)]
    forbidden_hits = detect_forbidden_language(moment_reports)
    state_counts: Dict[str, int] = {}
    for report in moment_reports:
        key = report.get("source_quality_gate_state", "UNKNOWN")
        state_counts[str(key)] = state_counts.get(str(key), 0) + 1
    return {
        "version": VERSION,
        "report_state": "PASS" if not forbidden_hits and moment_reports else "REVIEW",
        "moments": len(moment_reports),
        "moment_reports": moment_reports,
        "source_quality_state_counts": state_counts,
        "forbidden_language_hits": forbidden_hits,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "order_execution": False,
        "probability_of_success": False,
    }


def detect_forbidden_language(obj: Any) -> List[str]:
    text = str(obj).upper()
    return [term for term in FORBIDDEN_TERMS if term in text]


def to_markdown(report: Mapping[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# B9 French Trader Scene Report V0")
    lines.append("")
    lines.append("## Phrase de cap")
    lines.append("")
    lines.append("B9 ne cherche pas le signal. B9 cherche la trace laissée par l’effort.")
    lines.append("B6 compare les films. Le brief transmet une mémoire comparable, pas une décision d'exécution.")
    lines.append("")
    lines.append("## Synthèse runtime")
    lines.append("")
    lines.append(f"- Version : `{report.get('version')}`")
    lines.append(f"- État : `{report.get('report_state')}`")
    lines.append(f"- Moments : `{report.get('moments')}`")
    lines.append(f"- Read-only : `{report.get('read_only')}`")
    lines.append(f"- DB write : `{report.get('db_write')}`")
    lines.append(f"- Dashboard : `{report.get('dashboard')}`")
    lines.append(f"- Telegram : `{report.get('telegram')}`")
    lines.append("")
    lines.append("## Lecture des moments")
    lines.append("")
    for item in report.get("moment_reports", []):
        lines.append(f"### Moment {item.get('moment_index')} — {item.get('time_range')}")
        lines.append("")
        lines.append(f"**Titre :** {item.get('title_fr')}")
        lines.append("")
        for section in REPORT_SECTIONS:
            label = section.replace("_", " ").capitalize()
            lines.append(f"**{label} :**")
            lines.append(str(item.get(section, "Non renseigné")))
            lines.append("")
        lines.append("**Provenance et qualité :**")
        lines.append(f"Source family : `{item.get('source_family')}`  ")
        lines.append(f"Source mode : `{item.get('source_mode')}`  ")
        lines.append(f"Data visibility : `{item.get('data_visibility')}`  ")
        lines.append(f"Source quality gate : `{item.get('source_quality_gate_state')}`")
        lines.append("")
    lines.append("## Ce que le rapport ne fait pas")
    lines.append("")
    lines.append("- Il ne modifie pas `powerflow.db`.")
    lines.append("- Il ne modifie pas `tick_archive.db`.")
    lines.append("- Il ne déclenche pas dashboard ou Telegram.")
    lines.append("- Il ne transforme pas une lecture proxy en vérité raw.")
    lines.append("- Il ne transforme pas une similarité B6 en répétition certaine.")
    return "\n".join(lines) + "\n"
