"""T0147 - B9 Live Scene Candidate Queue V0.

Read-only helper for building a queue of B9 live scene candidates from enriched
T009/B9 moments. This module does not write databases, does not emit orders,
does not talk to dashboard or Telegram, and does not compute success odds.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import hashlib
import json
import re

VERSION = "T0147_B9_LIVE_SCENE_CANDIDATE_QUEUE_V0"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bachat\b", re.IGNORECASE),
    re.compile(r"\bvente\b", re.IGNORECASE),
    re.compile(r"probabilit[eé]\s+de\s+(succ[eè]s|r[eé]ussite)", re.IGNORECASE),
    re.compile(r"taux\s+de\s+(succ[eè]s|r[eé]ussite)", re.IGNORECASE),
]

RAW_UNAVAILABLE_VALUES = {"RAW_UNAVAILABLE", "SOURCE_RAW_UNAVAILABLE_REJECTED", "MEMORY_REJECTED_RAW_UNAVAILABLE"}
REJECT_MEMORY_STATES = {"MEMORY_REJECTED_RAW_UNAVAILABLE"}
REJECT_SOURCE_STATES = {"SOURCE_RAW_UNAVAILABLE_REJECTED"}

STRONG_SCENE_ROLES = {
    "RETEST_FAILED_REJECTION_NODE",
    "FAILED_REINTEGRATION_NODE",
    "PULLBACK_ABSORBED_RECONSTRUCTION",
    "LOW_ZONE_DEFENDED_REACTION",
    "PROGRESSIVE_FIRST_LEG",
    "PROGRESSIVE_SECOND_LEG_CANDIDATE",
    "CENTER_MIGRATION_DOWN_MEMORY_SHIFT",
    "CENTER_MIGRATION_UP_MEMORY_SHIFT",
}

STRONG_VERDICTS = {
    "ACCEPTED",
    "REJECTED",
    "PULLBACK_ABSORBED",
    "LOWER_ZONE_DEFENDED",
    "FAILED_REINTEGRATION",
}

STRONG_MEMORY_STATES = {"MEMORY_STRONG_COMPARABLE", "MEMORY_PARTIAL_COMPARABLE"}
WEAK_MEMORY_STATES = {"MEMORY_SOURCE_LIMITED", "MEMORY_SESSION_MISMATCH", "MEMORY_RETEST_MISSING"}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return f"{prefix}_{hashlib.sha1(raw).hexdigest()[:12].upper()}"


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def text_blob(obj: Any) -> str:
    try:
        return json.dumps(obj, ensure_ascii=False, sort_keys=True)
    except TypeError:
        return str(obj)


def forbidden_hits(obj: Any) -> List[str]:
    blob = text_blob(obj)
    hits: List[str] = []
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(blob):
            hits.append(pat.pattern)
    return sorted(set(hits))


def get_moments(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "items", "rows"):
        value = summary.get(key)
        if isinstance(value, list):
            return [dict(x) for x in value if isinstance(x, Mapping)]
    if isinstance(summary.get("summary"), Mapping):
        nested = summary["summary"]
        for key in ("moments", "sequence_moments", "items", "rows"):
            value = nested.get(key)
            if isinstance(value, list):
                return [dict(x) for x in value if isinstance(x, Mapping)]
    return []


def raw_unavailable(moment: Mapping[str, Any]) -> bool:
    fields = [
        moment.get("proxy_vs_raw_verdict"),
        moment.get("b9_source_quality_gate_state"),
        moment.get("b9_memory_confidence_state"),
        moment.get("b9_memory_comparability_state"),
        moment.get("source_quality_state"),
        moment.get("b9_source_quality_native_state"),
        moment.get("data_visibility"),
    ]
    return any(str(v).upper() in RAW_UNAVAILABLE_VALUES for v in fields if v is not None)


def field(moment: Mapping[str, Any], *names: str, default: str = "") -> str:
    for name in names:
        value = moment.get(name)
        if value is not None and str(value).strip() != "":
            return str(value)
    return default


def numeric(moment: Mapping[str, Any], *names: str, default: float = 0.0) -> float:
    for name in names:
        value = moment.get(name)
        if value is None or value == "":
            continue
        try:
            return float(value)
        except (TypeError, ValueError):
            continue
    return default


def score_moment(moment: Mapping[str, Any]) -> Tuple[float, List[str]]:
    score = 0.0
    reasons: List[str] = []

    scene_role = field(moment, "b9_scene_role", "scene_role", "label", "label_fr").upper()
    price_verdict = field(moment, "b9_price_verdict_state", "price_verdict").upper()
    memory_state = field(moment, "b9_memory_confidence_state", "b9_memory_comparability_state", "b9_memory_confidence_ladder_state").upper()
    fp_state = field(moment, "b9_memory_false_positive_state").upper()
    source_gate = field(moment, "b9_source_quality_gate_state", "source_quality_state").upper()
    retest_visible = str(moment.get("retest_visible", moment.get("b9_native_retest_visible", ""))).lower() in {"true", "1", "yes"}
    center_visibility = field(moment, "b9_center_path_visibility").upper()
    confidence_cap = numeric(moment, "confidence_cap", "b9_source_confidence_cap_effective", default=0.0)

    if scene_role in STRONG_SCENE_ROLES:
        score += 24
        reasons.append("rôle de scène fort")
    elif scene_role:
        score += 10
        reasons.append("rôle de scène présent")

    if price_verdict in STRONG_VERDICTS:
        score += 20
        reasons.append("verdict prix exploitable")
    elif price_verdict == "PENDING":
        score += 8
        reasons.append("verdict prix en attente")

    if retest_visible:
        score += 14
        reasons.append("retest visible")

    if memory_state in STRONG_MEMORY_STATES:
        score += 18
        reasons.append("mémoire B6 comparable")
    elif memory_state in WEAK_MEMORY_STATES:
        score += 7
        reasons.append("mémoire B6 exploitable mais limitée")

    if fp_state == "MEMORY_FP_LOW":
        score += 8
        reasons.append("piège mémoire faible")
    elif fp_state == "MEMORY_FP_MEDIUM":
        score += 2
        reasons.append("piège mémoire moyen")
    elif fp_state == "MEMORY_FP_HIGH":
        score -= 8
        reasons.append("piège mémoire élevé")

    if source_gate == "SOURCE_RAW_CONFIRMED":
        score += 12
        reasons.append("source raw confirmée")
    elif source_gate == "SOURCE_RAW_NUANCED":
        score += 5
        reasons.append("source raw nuancée")
    elif source_gate in {"SOURCE_PROXY_ONLY", "SOURCE_RECONSTRUCTED_LIMITED"}:
        score += 1
        reasons.append("source proxy/reconstruite")

    if center_visibility == "CENTER_PATH_VISIBLE":
        score += 8
        reasons.append("chemin interne visible")
    elif center_visibility == "CENTER_PATH_PROXY_EXTREMES":
        score += 3
        reasons.append("chemin interne proxy")

    if confidence_cap > 0:
        score += min(max(confidence_cap, 0.0), 1.0) * 6
        reasons.append("confidence_cap tracé")

    return round(score, 3), reasons


def candidate_state(moment: Mapping[str, Any], score: float) -> Tuple[str, str]:
    if raw_unavailable(moment):
        return "B9_LIVE_SCENE_CANDIDATE_REJECT_RAW_UNAVAILABLE", "RAW_UNAVAILABLE exclu de la queue active."
    if forbidden_hits(moment):
        return "B9_LIVE_SCENE_CANDIDATE_REJECT_FORBIDDEN_LANGUAGE", "Langage interdit détecté."
    memory_state = field(moment, "b9_memory_confidence_state", "b9_memory_comparability_state").upper()
    if memory_state in REJECT_MEMORY_STATES:
        return "B9_LIVE_SCENE_CANDIDATE_REJECT_MEMORY", "Mémoire rejetée par la ladder."
    source_state = field(moment, "b9_source_quality_gate_state").upper()
    if source_state in REJECT_SOURCE_STATES:
        return "B9_LIVE_SCENE_CANDIDATE_REJECT_SOURCE", "Source rejetée par hard gate."
    if score >= 65:
        return "B9_LIVE_SCENE_CANDIDATE_READY", "Scène candidate exploitable en lecture live."
    if score >= 30:
        return "B9_LIVE_SCENE_CANDIDATE_REVIEW", "Scène candidate à revoir, mais utile pour attention terrain."
    return "B9_LIVE_SCENE_CANDIDATE_LOW_SIGNAL", "Scène trop pauvre pour queue prioritaire."


def build_candidate(moment: Mapping[str, Any], index: int) -> Dict[str, Any]:
    base = {
        "idx": index,
        "time_start": field(moment, "time_start_real", "time_start", "start", default=""),
        "time_end": field(moment, "time_end_real", "time_end", "end", default=""),
        "label_fr": field(moment, "label_fr", "label", "b9_scene_role_reading_fr", default="Scène B9"),
        "scene_role": field(moment, "b9_scene_role", "scene_role", default="SCENE_ROLE_UNKNOWN"),
        "price_verdict": field(moment, "b9_price_verdict_state", "price_verdict", default="PENDING"),
        "terrain_node": field(moment, "node_role", "b9_terrain_node_role", default="TERRAIN_NODE_UNKNOWN"),
        "memory_family": field(moment, "b9_b6_memory_family", "memory_family", default="MEMORY_FAMILY_UNKNOWN"),
        "scene_family": field(moment, "b9_b6_scene_family", "scene_family", default="SCENE_FAMILY_UNKNOWN"),
        "memory_confidence_state": field(moment, "b9_memory_confidence_state", "b9_memory_comparability_state", default="MEMORY_COMPARABILITY_UNKNOWN"),
        "false_positive_state": field(moment, "b9_memory_false_positive_state", default="MEMORY_FP_UNKNOWN"),
        "source_quality_gate_state": field(moment, "b9_source_quality_gate_state", default="SOURCE_QUALITY_UNKNOWN"),
        "session": field(moment, "b9_session", "session", default="SESSION_UNKNOWN"),
        "session_phase": field(moment, "b9_session_phase", default="SESSION_PHASE_UNKNOWN"),
        "retest_result": field(moment, "retest_result", "b9_native_retest_judgment", default="RETEST_UNKNOWN"),
        "center_path_shape": field(moment, "b9_center_path_shape", default="CENTER_PATH_UNKNOWN"),
        "source_mode": field(moment, "source_mode", default=""),
        "data_visibility": field(moment, "data_visibility", default=""),
        "confidence_cap": moment.get("confidence_cap", moment.get("b9_source_confidence_cap_effective", "")),
        "technical_limits": as_list(moment.get("technical_limits")) + as_list(moment.get("b9_memory_technical_limits")) + as_list(moment.get("b9_source_quality_limits")),
    }
    score, reasons = score_moment(moment)
    state, state_reason = candidate_state(moment, score)
    candidate_payload = dict(base)
    candidate_payload.update({"score": score, "state": state})
    candidate_id = stable_id("B9LSC", candidate_payload)
    base.update({
        "candidate_id": candidate_id,
        "candidate_score": score,
        "candidate_state": state,
        "candidate_reason": state_reason,
        "candidate_score_reasons": reasons,
        "attention_brief_fr": build_attention_brief(base, state, reasons),
    })
    return base


def build_attention_brief(base: Mapping[str, Any], state: str, reasons: Sequence[str]) -> str:
    label = base.get("label_fr") or "Scène B9"
    role = base.get("scene_role") or "rôle non qualifié"
    verdict = base.get("price_verdict") or "verdict en attente"
    memory = base.get("memory_confidence_state") or "mémoire non qualifiée"
    source = base.get("source_quality_gate_state") or "source non qualifiée"
    reason_txt = "; ".join(reasons[:4]) if reasons else "preuve insuffisante"
    return (
        f"B9 met en file une scène candidate: {label}. "
        f"Rôle: {role}. Verdict prix: {verdict}. Mémoire: {memory}. "
        f"Source: {source}. Raisons techniques: {reason_txt}. État queue: {state}."
    )


def build_queue(summary: Mapping[str, Any], max_candidates: int = 12) -> Dict[str, Any]:
    moments = get_moments(summary)
    candidates = [build_candidate(m, i) for i, m in enumerate(moments, start=1)]
    candidates.sort(key=lambda c: (c.get("candidate_state") != "B9_LIVE_SCENE_CANDIDATE_READY", -float(c.get("candidate_score") or 0)))
    active = [c for c in candidates if c.get("candidate_state") in {"B9_LIVE_SCENE_CANDIDATE_READY", "B9_LIVE_SCENE_CANDIDATE_REVIEW"}]
    rejected = [c for c in candidates if str(c.get("candidate_state", "")).startswith("B9_LIVE_SCENE_CANDIDATE_REJECT")]
    low_signal = [c for c in candidates if c.get("candidate_state") == "B9_LIVE_SCENE_CANDIDATE_LOW_SIGNAL"]
    selected = active[:max_candidates]
    latest = selected[0] if selected else None

    state_counts: Dict[str, int] = {}
    for c in candidates:
        state = str(c.get("candidate_state"))
        state_counts[state] = state_counts.get(state, 0) + 1

    summary_out: Dict[str, Any] = {
        "version": VERSION,
        "generated_at": utc_now_iso(),
        "queue_state": "B9_LIVE_SCENE_QUEUE_READY" if selected else "B9_LIVE_SCENE_QUEUE_EMPTY",
        "moments_seen": len(moments),
        "candidates_total": len(candidates),
        "candidates_active": len(active),
        "candidates_ready": state_counts.get("B9_LIVE_SCENE_CANDIDATE_READY", 0),
        "candidates_review": state_counts.get("B9_LIVE_SCENE_CANDIDATE_REVIEW", 0),
        "candidates_low_signal": len(low_signal),
        "candidates_rejected": len(rejected),
        "state_counts": state_counts,
        "latest_scene_candidate": latest,
        "queue": selected,
        "rejected": rejected,
        "low_signal": low_signal,
        "forbidden_language_hits": forbidden_hits(candidates),
        "read_only_contract": {
            "db_write": False,
            "dashboard": False,
            "telegram": False,
            "directional_order": False,
            "success_rate": False,
        },
    }
    return summary_out


def markdown_report(result: Mapping[str, Any]) -> str:
    lines = [
        "# T0147 — B9 Live Scene Candidate Queue V0",
        "",
        "## Résumé",
        "",
        f"- Version : `{result.get('version')}`",
        f"- État queue : `{result.get('queue_state')}`",
        f"- Moments vus : {result.get('moments_seen')}",
        f"- Candidats actifs : {result.get('candidates_active')}",
        f"- Ready : {result.get('candidates_ready')}",
        f"- Review : {result.get('candidates_review')}",
        f"- Rejetés : {result.get('candidates_rejected')}",
        "",
        "## Phrase de cap",
        "",
        "B9 ne cherche pas le signal. B9 cherche la trace laissée par l'effort.",
        "",
        "## Latest scene candidate",
        "",
    ]
    latest = result.get("latest_scene_candidate")
    if isinstance(latest, Mapping):
        lines.extend([
            f"- Candidate ID : `{latest.get('candidate_id')}`",
            f"- État : `{latest.get('candidate_state')}`",
            f"- Score technique : {latest.get('candidate_score')}",
            f"- Heure : {latest.get('time_start')} → {latest.get('time_end')}",
            f"- Label : {latest.get('label_fr')}",
            f"- Rôle : `{latest.get('scene_role')}`",
            f"- Verdict prix : `{latest.get('price_verdict')}`",
            f"- Mémoire : `{latest.get('memory_confidence_state')}`",
            f"- Brief : {latest.get('attention_brief_fr')}",
        ])
    else:
        lines.append("Aucun candidat actif.")
    lines.extend(["", "## Queue active", ""])
    for c in result.get("queue", []) or []:
        lines.extend([
            f"### {c.get('candidate_id')}",
            "",
            f"- État : `{c.get('candidate_state')}`",
            f"- Score : {c.get('candidate_score')}",
            f"- Rôle : `{c.get('scene_role')}`",
            f"- Verdict : `{c.get('price_verdict')}`",
            f"- Session : `{c.get('session')}` / `{c.get('session_phase')}`",
            f"- Mémoire : `{c.get('memory_confidence_state')}`",
            f"- Piège mémoire : `{c.get('false_positive_state')}`",
            f"- Source : `{c.get('source_quality_gate_state')}`",
            f"- Lecture : {c.get('attention_brief_fr')}",
            "",
        ])
    lines.extend([
        "## Limites",
        "",
        "- Read-only.",
        "- Aucune écriture powerflow.db.",
        "- Aucune écriture tick_archive.db.",
        "- Aucun dashboard.",
        "- Aucun Telegram.",
        "- Aucun ordre directionnel.",
        "- Aucun taux de réussite.",
        "- Une scène proxy reste proxy.",
        "- RAW_UNAVAILABLE est rejeté de la queue active.",
        "",
    ])
    return "\n".join(lines)


def csv_rows(candidates: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    keys = [
        "candidate_id", "candidate_state", "candidate_score", "time_start", "time_end", "label_fr",
        "scene_role", "price_verdict", "terrain_node", "memory_family", "scene_family",
        "memory_confidence_state", "false_positive_state", "source_quality_gate_state", "session",
        "session_phase", "retest_result", "center_path_shape", "source_mode", "data_visibility",
        "confidence_cap", "candidate_reason", "attention_brief_fr"
    ]
    rows: List[Dict[str, Any]] = []
    for c in candidates:
        rows.append({k: c.get(k, "") for k in keys})
    return rows
