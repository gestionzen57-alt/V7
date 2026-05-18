"""B9 Trader Attention Packet V0.

Read-only PowerFlow helper that turns an enriched B9 scene / live brief /
Reality Board candidate into a trader attention packet.

Doctrine:
- B9 does not seek signals.
- B9 reads the trace left by effort.
- The packet wakes attention; it is not an execution decision.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

VERSION = "T0155_B9_TRADER_ATTENTION_PACKET_V0"

FORBIDDEN_TERMS = (
    "BUY",
    "SELL",
    "ACHETER",
    "VENDRE",
    "LONG ",
    "SHORT ",
    "TAKE PROFIT",
    "STOP LOSS",
    "WIN RATE",
    "TAUX DE REUSSITE",
    "TAUX DE RÉUSSITE",
    "PROBABILITE DE SUCCES",
    "PROBABILITÉ DE SUCCÈS",
)

RAW_UNAVAILABLE_MARKERS = (
    "RAW_UNAVAILABLE",
    "SOURCE_RAW_UNAVAILABLE_REJECTED",
    "MEMORY_REJECTED_RAW_UNAVAILABLE",
    "RAW_UNAVAILABLE_NODE_REJECTED",
    "SCENE_BLOCKED_RAW_UNAVAILABLE",
    "RAW_UNAVAILABLE_TRANSITION_BLOCKED",
)

LIMITED_SOURCE_MARKERS = (
    "M1_BAR_PROXY",
    "RECONSTRUCTED",
    "FORCE_SNAPSHOT_DERIVED",
    "SOURCE_RECONSTRUCTED_LIMITED",
    "SOURCE_PROXY_ONLY",
    "SOURCE_QUALITY_LIVE_UNQUALIFIED",
    "NUANCED_BY_RAW",
)

FALSE_POSITIVE_HIGH_MARKERS = (
    "B6_FALSE_POSITIVE_CONTEXT_HIGH",
    "MEMORY_FP_HIGH",
    "false_positive_high",
    "HIGH",
)


@dataclass
class TraderAttentionPacket:
    version: str
    packet_id: str
    generated_at_utc: str
    packet_state: str
    attention_reason: str
    candidate_id: str
    date: str
    time_start: str
    time_end: str
    label_fr: str
    scene_state: str
    scene_transition: str
    active_zone: str
    latest_node: str
    price_verdict: str
    scene_role: str
    memory_context: Dict[str, Any]
    technical_risks: List[str]
    what_to_watch_next: List[str]
    evidence: Dict[str, Any]
    blocked_reason: str
    no_trade_decision_guard: bool
    doctrine: str


def load_json(path: str | Path) -> Any:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with Path(path).open("w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _dig(obj: Any, *keys: str, default: Any = "") -> Any:
    cur = obj
    for key in keys:
        if isinstance(cur, Mapping) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur


def _first_non_empty(*values: Any, default: str = "") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str) and value.strip():
            return value.strip()
        if isinstance(value, (list, tuple)) and value:
            return str(value[0])
    return default


def _collect_strings(obj: Any) -> List[str]:
    out: List[str] = []
    if isinstance(obj, Mapping):
        for value in obj.values():
            out.extend(_collect_strings(value))
    elif isinstance(obj, list):
        for value in obj:
            out.extend(_collect_strings(value))
    elif isinstance(obj, str):
        out.append(obj)
    elif obj is not None:
        out.append(str(obj))
    return out


def scan_forbidden_language(obj: Any) -> List[str]:
    hits: List[str] = []
    joined_strings = _collect_strings(obj)
    for text in joined_strings:
        upper = f" {text.upper()} "
        for term in FORBIDDEN_TERMS:
            if term in upper:
                hits.append(term.strip())
    return sorted(set(hits))


def _contains_any(obj: Any, markers: Sequence[str]) -> bool:
    upper_values = [s.upper() for s in _collect_strings(obj)]
    return any(marker.upper() in value for value in upper_values for marker in markers)


def _latest_moment(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in (
        "latest_scene_candidate",
        "latest_candidate",
        "candidate",
        "payload",
        "live_brief",
        "reality_board_payload_candidate",
    ):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    for key in ("moments", "items", "rows", "queue", "candidates"):
        values = payload.get(key)
        if isinstance(values, list) and values:
            for value in reversed(values):
                if isinstance(value, Mapping):
                    return value
    return payload


def _memory_context(payload: Mapping[str, Any], moment: Mapping[str, Any]) -> Dict[str, Any]:
    matches = []
    for key in ("matches", "similar_films", "memory_matches", "top_matches"):
        value = payload.get(key)
        if isinstance(value, list):
            matches = value
            break
    if not matches:
        for key in ("matches", "similar_films", "memory_matches", "top_matches"):
            value = moment.get(key)
            if isinstance(value, list):
                matches = value
                break

    top = matches[0] if matches and isinstance(matches[0], Mapping) else {}
    match_count = _first_non_empty(payload.get("match_count"), moment.get("match_count"), len(matches) if matches else "0")
    top_film = _first_non_empty(
        payload.get("top_match_film_id"),
        moment.get("top_match_film_id"),
        _dig(top, "film_id"),
        _dig(top, "id"),
        default="",
    )
    false_positive_state = _first_non_empty(
        payload.get("false_positive_state"),
        payload.get("b9_memory_false_positive_state"),
        moment.get("b9_memory_false_positive_state"),
        _dig(top, "false_positive_context_state"),
        _dig(top, "context_state"),
        default="",
    )
    ladder = _first_non_empty(
        payload.get("memory_confidence_ladder"),
        payload.get("b9_memory_confidence_ladder_state"),
        moment.get("b9_memory_confidence_ladder_state"),
        moment.get("memory_confidence_state"),
        default="",
    )
    return {
        "memory_family": _first_non_empty(payload.get("memory_family"), moment.get("memory_family"), moment.get("b6_memory_family"), default=""),
        "scene_family": _first_non_empty(payload.get("scene_family"), moment.get("scene_family"), moment.get("b9_b6_scene_family"), default=""),
        "memory_confidence_ladder": ladder,
        "match_count": int(float(match_count)) if str(match_count).replace(".", "", 1).isdigit() else 0,
        "top_match_film_id": top_film,
        "false_positive_context_available": bool(
            payload.get("false_positive_context_available")
            or moment.get("false_positive_context_available")
            or false_positive_state
            or payload.get("false_positive_contexts")
        ),
        "false_positive_state": false_positive_state,
        "top_match_label_fr": _first_non_empty(_dig(top, "label_fr"), _dig(top, "title"), default=""),
    }


def _active_zone(moment: Mapping[str, Any]) -> str:
    low = _first_non_empty(moment.get("zone_low"), moment.get("origin_zone_low"), moment.get("active_zone_low"), default="")
    high = _first_non_empty(moment.get("zone_high"), moment.get("origin_zone_high"), moment.get("active_zone_high"), default="")
    center = _first_non_empty(moment.get("zone_center"), moment.get("origin_zone_center"), moment.get("active_zone_center"), default="")
    if low and high:
        return f"{low}–{high}" + (f" | centre {center}" if center else "")
    return _first_non_empty(moment.get("active_zone"), moment.get("zone_id"), moment.get("origin_zone_id"), default="ZONE_NON_RENSEIGNEE")


def _technical_risks(payload: Mapping[str, Any], moment: Mapping[str, Any], memory: Mapping[str, Any]) -> List[str]:
    risks: List[str] = []
    source_values = _collect_strings({"payload": payload, "moment": moment, "memory": memory})
    upper = " | ".join(source_values).upper()
    if any(marker in upper for marker in LIMITED_SOURCE_MARKERS):
        risks.append("source limitée ou reconstruite : ne pas durcir en vérité raw")
    if "NUANCED_BY_RAW" in upper:
        risks.append("raw nuance la scène : ne pas présenter comme confirmé plein")
    if "SOURCE_QUALITY_LIVE_UNQUALIFIED" in upper:
        risks.append("source live encore non qualifiée côté texture raw")
    if memory.get("false_positive_context_available"):
        state = str(memory.get("false_positive_state") or "").upper()
        if any(marker in state for marker in FALSE_POSITIVE_HIGH_MARKERS):
            risks.append("mémoire comparable avec piège technique fort")
        else:
            risks.append("mémoire comparable à lire avec contexte de faux positif")
    if memory.get("match_count", 0) == 0:
        risks.append("aucun film B6 proche exploitable dans ce packet")
    if not _first_non_empty(moment.get("retest_visible"), moment.get("b9_native_retest_judgment"), moment.get("retest_result"), default=""):
        risks.append("retest non visible ou non renseigné dans le packet")
    if not risks:
        risks.append("aucune fragilité majeure détectée par T0155, sous réserve de source et replay")
    return risks


def _watch_next(moment: Mapping[str, Any], memory: Mapping[str, Any]) -> List[str]:
    verdict = _first_non_empty(moment.get("b9_price_verdict_state"), moment.get("price_verdict"), default="PENDING")
    scene_state = _first_non_empty(moment.get("b9_scene_state"), moment.get("scene_state"), default="SCENE_REVIEW_REQUIRED")
    items = []
    if "TEST" in scene_state or verdict == "PENDING":
        items.append("observer si le retest accepte, rejette ou réintègre la zone")
    if "ACCEPT" in verdict or "MEMORY_SHIFT" in scene_state:
        items.append("surveiller si la mémoire déplacée devient nouvelle zone de travail")
    if "REJECT" in verdict or "FAILED_REINTEGRATION" in verdict:
        items.append("surveiller si le rejet crée une deuxième jambe ou seulement une respiration")
    if memory.get("false_positive_context_available"):
        items.append("comparer les différences avec les films B6 proches avant de durcir la lecture")
    if not items:
        items.append("surveiller la prochaine transition de scène avant toute requalification")
    return items


def build_trader_attention_packet(payload: Mapping[str, Any]) -> Dict[str, Any]:
    moment = _latest_moment(payload)
    memory = _memory_context(payload, moment)
    forbidden = scan_forbidden_language({"payload": payload, "moment": moment, "memory": memory})
    raw_blocked = _contains_any({"payload": payload, "moment": moment, "memory": memory}, RAW_UNAVAILABLE_MARKERS)

    scene_state = _first_non_empty(moment.get("b9_scene_state"), moment.get("scene_state"), payload.get("scene_state"), default="SCENE_REVIEW_REQUIRED")
    transition = _first_non_empty(moment.get("b9_scene_transition"), moment.get("transition_type"), payload.get("scene_transition"), default="TRANSITION_NON_RENSEIGNEE")
    verdict = _first_non_empty(moment.get("b9_price_verdict_state"), moment.get("price_verdict"), payload.get("price_verdict"), default="PENDING")
    node = _first_non_empty(moment.get("node_role"), moment.get("latest_node"), payload.get("latest_node"), default="NODE_NON_RENSEIGNE")
    scene_role = _first_non_empty(moment.get("b9_scene_role"), moment.get("scene_role"), payload.get("scene_role"), default="SCENE_ROLE_REVIEW_REQUIRED")

    candidate_id = _first_non_empty(
        payload.get("candidate_id"), moment.get("candidate_id"), moment.get("scene_id"), moment.get("id"), default="B9_PACKET_UNKNOWN"
    )
    packet_seed = f"{candidate_id}|{scene_state}|{transition}|{verdict}|{memory.get('top_match_film_id','')}"
    packet_id = "B9ATP_" + hashlib.sha1(packet_seed.encode("utf-8")).hexdigest()[:12].upper()

    if forbidden:
        state = "BLOCKED_FORBIDDEN_LANGUAGE"
        blocked_reason = ", ".join(forbidden)
    elif raw_blocked:
        state = "BLOCKED_RAW_UNAVAILABLE"
        blocked_reason = "RAW_UNAVAILABLE détecté dans la scène, la mémoire ou le contexte"
    elif memory.get("false_positive_context_available") or memory.get("memory_confidence_ladder") in {
        "MEMORY_PARTIAL_COMPARABLE",
        "MEMORY_SOURCE_LIMITED",
        "MEMORY_SESSION_MISMATCH",
        "MEMORY_RETEST_MISSING",
    }:
        state = "B9_TRADER_ATTENTION_PACKET_REVIEW_TECHNICAL_RISK"
        blocked_reason = ""
    elif memory.get("match_count", 0) > 0:
        state = "B9_TRADER_ATTENTION_PACKET_READY"
        blocked_reason = ""
    else:
        state = "B9_TRADER_ATTENTION_PACKET_REVIEW_NO_MEMORY_MATCH"
        blocked_reason = ""

    attention_reason = _first_non_empty(
        moment.get("attention_reason"),
        payload.get("attention_reason"),
        default=f"Scène {scene_state} avec verdict {verdict} et rôle {scene_role}",
    )

    packet = TraderAttentionPacket(
        version=VERSION,
        packet_id=packet_id,
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        packet_state=state,
        attention_reason=attention_reason,
        candidate_id=candidate_id,
        date=_first_non_empty(moment.get("date"), payload.get("date"), default=""),
        time_start=_first_non_empty(moment.get("time_start"), payload.get("time_start"), default=""),
        time_end=_first_non_empty(moment.get("time_end"), payload.get("time_end"), default=""),
        label_fr=_first_non_empty(moment.get("label_fr"), payload.get("label_fr"), default="Scène B9 à qualifier"),
        scene_state=scene_state,
        scene_transition=transition,
        active_zone=_active_zone(moment),
        latest_node=node,
        price_verdict=verdict,
        scene_role=scene_role,
        memory_context=memory,
        technical_risks=_technical_risks(payload, moment, memory),
        what_to_watch_next=_watch_next(moment, memory),
        evidence={
            "source_quality_state": _first_non_empty(moment.get("b9_source_quality_gate_state"), moment.get("source_quality_state"), payload.get("source_quality_state"), default=""),
            "source_mode": _first_non_empty(moment.get("source_mode"), payload.get("source_mode"), default=""),
            "data_visibility": _first_non_empty(moment.get("data_visibility"), payload.get("data_visibility"), default=""),
            "confidence_cap": _first_non_empty(moment.get("confidence_cap"), payload.get("confidence_cap"), default=""),
            "retest": _first_non_empty(moment.get("b9_native_retest_judgment"), moment.get("retest_result"), moment.get("retest_visible"), default=""),
            "center_path": _first_non_empty(moment.get("b9_center_path_shape"), moment.get("center_path_shape"), default=""),
            "effort_result_progress": _first_non_empty(moment.get("b9_effort_result_progress_state"), moment.get("progress_type"), default=""),
            "forbidden_language_hits": forbidden,
        },
        blocked_reason=blocked_reason,
        no_trade_decision_guard=True,
        doctrine="B9 lit la scène. B6 compare les films. Le packet attire l'attention du trader, il ne décide pas.",
    )
    return asdict(packet)


def render_markdown(packet: Mapping[str, Any]) -> str:
    mem = packet.get("memory_context", {}) if isinstance(packet.get("memory_context"), Mapping) else {}
    risks = packet.get("technical_risks") or []
    watch = packet.get("what_to_watch_next") or []
    lines = [
        "# B9 Trader Attention Packet V0",
        "",
        "## État",
        f"- Packet : `{packet.get('packet_state', '')}`",
        f"- ID : `{packet.get('packet_id', '')}`",
        f"- Candidat : `{packet.get('candidate_id', '')}`",
        "",
        "## Ce qui réveille l'attention",
        str(packet.get("attention_reason", "")),
        "",
        "## Scène",
        f"- Temps : {packet.get('time_start', '')} → {packet.get('time_end', '')}",
        f"- Label : {packet.get('label_fr', '')}",
        f"- État : `{packet.get('scene_state', '')}`",
        f"- Transition : `{packet.get('scene_transition', '')}`",
        f"- Zone active : {packet.get('active_zone', '')}",
        f"- Node : `{packet.get('latest_node', '')}`",
        f"- Verdict prix : `{packet.get('price_verdict', '')}`",
        f"- Rôle : `{packet.get('scene_role', '')}`",
        "",
        "## Mémoire B6",
        f"- Famille : `{mem.get('memory_family', '')}`",
        f"- Famille scène : `{mem.get('scene_family', '')}`",
        f"- Comparabilité : `{mem.get('memory_confidence_ladder', '')}`",
        f"- Films proches : {mem.get('match_count', 0)}",
        f"- Top film : `{mem.get('top_match_film_id', '')}`",
        f"- Faux positif contexte : `{mem.get('false_positive_context_available', False)}` / `{mem.get('false_positive_state', '')}`",
        "",
        "## Risques techniques",
    ]
    lines += [f"- {risk}" for risk in risks]
    lines += ["", "## À surveiller ensuite"]
    lines += [f"- {item}" for item in watch]
    lines += [
        "",
        "## Ce que le packet ne conclut pas",
        "- Pas d'ordre directionnel.",
        "- Pas de taux de réussite.",
        "- Pas de décision d'exécution.",
        "- Une mémoire comparable n'est pas une répétition certaine.",
        "",
        "## Doctrine",
        str(packet.get("doctrine", "")),
        "",
    ]
    return "\n".join(lines)


def packet_to_row(packet: Mapping[str, Any]) -> Dict[str, Any]:
    mem = packet.get("memory_context", {}) if isinstance(packet.get("memory_context"), Mapping) else {}
    return {
        "packet_id": packet.get("packet_id", ""),
        "packet_state": packet.get("packet_state", ""),
        "candidate_id": packet.get("candidate_id", ""),
        "time_start": packet.get("time_start", ""),
        "time_end": packet.get("time_end", ""),
        "label_fr": packet.get("label_fr", ""),
        "scene_state": packet.get("scene_state", ""),
        "scene_transition": packet.get("scene_transition", ""),
        "active_zone": packet.get("active_zone", ""),
        "latest_node": packet.get("latest_node", ""),
        "price_verdict": packet.get("price_verdict", ""),
        "scene_role": packet.get("scene_role", ""),
        "memory_family": mem.get("memory_family", ""),
        "scene_family": mem.get("scene_family", ""),
        "memory_confidence_ladder": mem.get("memory_confidence_ladder", ""),
        "match_count": mem.get("match_count", 0),
        "top_match_film_id": mem.get("top_match_film_id", ""),
        "false_positive_context_available": mem.get("false_positive_context_available", False),
        "blocked_reason": packet.get("blocked_reason", ""),
    }
