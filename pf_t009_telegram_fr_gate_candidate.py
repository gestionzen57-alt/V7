"""T0157 - B9 Telegram FR Gate Candidate V0.

Read-only builder for a Telegram-ready French trader message candidate.
It does not send messages and does not import telegram_* modules.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Tuple
import json
import re

VERSION = "T0157_B9_TELEGRAM_FR_GATE_CANDIDATE_V0"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b", r"\bSELL\b", r"\bLONG\b", r"\bSHORT\b",
    r"achat\s+maintenant", r"vente\s+maintenant", r"entre[r]?\s+en\s+position",
    r"probabilit[eé]\s+de\s+(succ[eè]s|r[eé]ussite)", r"taux\s+de\s+r[eé]ussite",
    r"signal\s+(d['’])?(achat|vente)", r"ordre\s+(d['’])?(achat|vente)",
]

BLOCKING_STATES = {
    "BLOCKED_MISSING_ATTENTION_PACKET_INPUT",
    "BLOCKED_ATTENTION_PACKET_NOT_READY",
    "BLOCKED_RAW_UNAVAILABLE_IN_ATTENTION_PACKET",
    "BLOCKED_FORBIDDEN_LANGUAGE",
    "BLOCKED_MISSING_NO_DECISION_GUARD",
    "BLOCKED_MISSING_LIVE_BRIEF_INPUT",
    "BLOCKED_LIVE_BRIEF_NOT_READY",
    "BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS",
}

READY_STATES = {
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_READY",
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK",
    "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_READY",
    "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REVIEW_LIMITED_SOURCE",
}

@dataclass
class TelegramGateResult:
    version: str
    gate_state: str
    candidate_id: str
    scene_state: str
    price_verdict: str
    memory_confidence_ladder: str
    match_count: int
    top_match_film_id: str
    false_positive_context_available: bool
    no_send_guard: bool
    no_trade_decision_guard: bool
    forbidden_language_hits: List[str]
    technical_limits: List[str]
    telegram_message_fr: str
    telegram_payload_candidate: Dict[str, Any]


def _get(obj: Dict[str, Any], *names: str, default: Any = "") -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj and obj[name] not in (None, ""):
            return obj[name]
    return default


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool): return value
    if isinstance(value, str): return value.strip().lower() in {"1", "true", "yes", "oui"}
    return bool(value)


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except Exception:
        return 0


def forbidden_hits(text: str) -> List[str]:
    hits = []
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, text or "", flags=re.IGNORECASE):
            hits.append(pat)
    return hits


def _extract_payload(raw: Dict[str, Any]) -> Dict[str, Any]:
    # Accept several wrapper shapes from T0149/T0156/T0155.
    for key in ("reality_board_payload_candidate", "reality_board_payload", "payload", "attention_packet", "packet"):
        val = raw.get(key)
        if isinstance(val, dict):
            merged = dict(raw)
            merged.update(val)
            return merged
    return raw


def build_telegram_gate_candidate(reality_board_candidate: Dict[str, Any]) -> Dict[str, Any]:
    src = _extract_payload(reality_board_candidate)
    payload_state = str(_get(src, "payload_state", "integration_state", "packet_state", default="UNKNOWN"))
    candidate_id = str(_get(src, "candidate_id", "scene_id", "latest_candidate_id", default="UNKNOWN_CANDIDATE"))
    scene_state = str(_get(src, "scene_state", "b9_scene_state", default="SCENE_UNKNOWN"))
    price_verdict = str(_get(src, "price_verdict", "b9_price_verdict_state", default="PENDING"))
    scene_role = str(_get(src, "scene_role", "b9_scene_role", default="SCENE_ROLE_UNKNOWN"))
    active_zone = str(_get(src, "active_zone", "zone", "zone_reading", default="zone non précisée"))
    latest_node = str(_get(src, "latest_node", "node_role", "terrain_node", default="node non précisé"))
    memory_conf = str(_get(src, "memory_confidence_ladder", "memory_confidence_state", default="MEMORY_NOT_AVAILABLE"))
    match_count = _as_int(_get(src, "match_count", "matches", default=0))
    top_film = str(_get(src, "top_match_film_id", "top_b6_film_id", "film_id", default=""))
    fp_available = _as_bool(_get(src, "false_positive_context_available", default=False))
    source_quality = str(_get(src, "source_quality_gate_state", "source_quality_state", default="SOURCE_QUALITY_UNKNOWN"))
    technical_risks = _get(src, "technical_risks", "technical_limits", "limits", default=[])
    if isinstance(technical_risks, str):
        technical_risks = [technical_risks] if technical_risks else []
    if not isinstance(technical_risks, list):
        technical_risks = [str(technical_risks)]

    # Gate policy.
    no_decision_guard = _as_bool(_get(src, "no_trade_decision_guard", default=True))
    no_send_guard = True
    raw_unavailable = "RAW_UNAVAILABLE" in json.dumps(src, ensure_ascii=False).upper()

    gate_state = "B9_TELEGRAM_FR_GATE_CANDIDATE_READY"
    if payload_state in BLOCKING_STATES:
        gate_state = "BLOCKED_REALITY_BOARD_PAYLOAD_NOT_READY"
    elif raw_unavailable:
        gate_state = "BLOCKED_RAW_UNAVAILABLE_IN_PACKET"
    elif not no_decision_guard:
        gate_state = "BLOCKED_MISSING_NO_DECISION_GUARD"
    elif payload_state not in READY_STATES and payload_state != "UNKNOWN":
        gate_state = "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK"
    elif fp_available or "LIMITED" in source_quality or "PARTIAL" in memory_conf:
        gate_state = "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK"

    memory_line = "Mémoire B6 : aucune mémoire comparable alignée."
    if match_count > 0:
        memory_line = f"Mémoire B6 : {match_count} film(s) proche(s)"
        if top_film:
            memory_line += f", top = {top_film}"
        memory_line += "."

    fp_line = "Piège technique : non signalé."
    if fp_available:
        fp_line = "Piège technique : similarité fragile / contexte faux positif à lire avant interprétation."

    risk_line = "Limites : source et contexte à vérifier."
    if technical_risks:
        risk_line = "Limites : " + "; ".join(str(x) for x in technical_risks[:4]) + "."

    message = "\n".join([
        "B9 — packet d’attention",
        f"Scène : {scene_state} | rôle : {scene_role}",
        f"Zone : {active_zone}",
        f"Node : {latest_node}",
        f"Verdict prix : {price_verdict}",
        memory_line,
        f"Comparabilité mémoire : {memory_conf}",
        fp_line,
        risk_line,
        "Ce message réveille l’attention. Il ne donne aucun ordre d’exécution.",
    ])

    hits = forbidden_hits(message)
    if hits and not gate_state.startswith("BLOCKED"):
        gate_state = "BLOCKED_FORBIDDEN_LANGUAGE"

    candidate = {
        "version": VERSION,
        "send_enabled": False,
        "transport": "TELEGRAM_CANDIDATE_NO_SEND",
        "candidate_id": candidate_id,
        "gate_state": gate_state,
        "message_fr": message,
        "no_send_guard": no_send_guard,
        "no_trade_decision_guard": no_decision_guard,
    }
    result = TelegramGateResult(
        version=VERSION,
        gate_state=gate_state,
        candidate_id=candidate_id,
        scene_state=scene_state,
        price_verdict=price_verdict,
        memory_confidence_ladder=memory_conf,
        match_count=match_count,
        top_match_film_id=top_film,
        false_positive_context_available=fp_available,
        no_send_guard=no_send_guard,
        no_trade_decision_guard=no_decision_guard,
        forbidden_language_hits=hits,
        technical_limits=technical_risks,
        telegram_message_fr=message,
        telegram_payload_candidate=candidate,
    )
    return asdict(result)


def load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def dump_json(path: str, data: Dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
