"""T0149 - B9 Reality Board Payload Candidate V0.

Read-only transformer from a B9 live brief once output to a Reality Board
candidate payload. It does not write DB, dashboard or Telegram surfaces.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

VERSION = "T0149_B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0"

READY_STATE = "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_READY"
REVIEW_LIMITED_SOURCE_STATE = "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REVIEW_LIMITED_SOURCE"
BLOCKED_MISSING_INPUT_STATE = "BLOCKED_MISSING_LIVE_BRIEF_INPUT"
BLOCKED_BRIEF_NOT_READY_STATE = "BLOCKED_LIVE_BRIEF_NOT_READY"
BLOCKED_RAW_UNAVAILABLE_STATE = "BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS"
BLOCKED_FORBIDDEN_LANGUAGE_STATE = "BLOCKED_FORBIDDEN_LANGUAGE"

FORBIDDEN_TOKENS = (
    "BUY",
    "SELL",
    "ACHETER",
    "VENDRE",
    "LONG NOW",
    "SHORT NOW",
    "TAKE PROFIT",
    "STOP LOSS",
    "WIN RATE",
    "SUCCESS RATE",
    "PROBABILITY OF SUCCESS",
    "PROBABILITE DE SUCCES",
    "PROBABILITÉ DE SUCCÈS",
)

REQUIRED_PAYLOAD_FIELDS = (
    "version",
    "payload_state",
    "payload_type",
    "candidate_id",
    "symbol",
    "time_start",
    "time_end",
    "session",
    "scene_role",
    "price_verdict",
    "source_quality_state",
    "memory_family",
    "memory_confidence_ladder",
    "false_positive_state",
    "attention_reason_fr",
    "b9_reading_fr",
    "memory_context_fr",
    "technical_risks",
    "what_to_watch_next_fr",
    "limits",
)


def _first_non_empty(*values: Any, default: str = "UNKNOWN") -> str:
    for value in values:
        if value is None:
            continue
        if isinstance(value, str) and value.strip():
            return value.strip()
        if not isinstance(value, str):
            return str(value)
    return default


def _as_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, tuple):
        return [str(v) for v in value if str(v).strip()]
    if isinstance(value, str):
        return [value] if value.strip() else []
    return [str(value)]


def _dig(data: Mapping[str, Any], *path: str, default: Any = None) -> Any:
    cur: Any = data
    for key in path:
        if not isinstance(cur, Mapping) or key not in cur:
            return default
        cur = cur[key]
    return cur


def scan_forbidden_language(obj: Any) -> List[str]:
    """Return forbidden tokens found in nested string content."""
    hits: List[str] = []

    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple, set)):
            for child in value:
                walk(child)
        elif isinstance(value, str):
            upper = value.upper()
            for token in FORBIDDEN_TOKENS:
                if token in upper and token not in hits:
                    hits.append(token)

    walk(obj)
    return hits


@dataclass
class RealityBoardPayloadCandidate:
    version: str
    payload_state: str
    payload_type: str
    generated_at_utc: str
    candidate_id: str
    symbol: str
    time_start: str
    time_end: str
    session: str
    scene_role: str
    price_verdict: str
    source_quality_state: str
    source_mode: str
    data_visibility: str
    confidence_cap: str
    memory_family: str
    memory_confidence_ladder: str
    false_positive_state: str
    top_match_film_id: str
    match_count: int
    cross_family_match_count: int
    attention_reason_fr: str
    b9_reading_fr: str
    memory_context_fr: str
    technical_risks: List[str]
    what_to_watch_next_fr: List[str]
    limits: List[str]
    raw_unavailable_in_results: bool
    low_trust_in_results: bool
    forbidden_language_hits: List[str]
    source_inputs: Dict[str, str]
    read_only_contract: Dict[str, bool]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def build_payload_candidate(live_brief: Mapping[str, Any]) -> Dict[str, Any]:
    existing_forbidden = _as_list(live_brief.get("forbidden_language_hits"))
    detected_forbidden = scan_forbidden_language(live_brief)
    forbidden_hits = sorted(set(existing_forbidden + detected_forbidden))

    brief_state = _first_non_empty(live_brief.get("brief_state"), live_brief.get("recognition_state"), default="UNKNOWN")
    raw_unavailable = bool(live_brief.get("raw_unavailable_in_results", False))
    low_trust = bool(live_brief.get("low_trust_in_results", False))

    source_quality_state = _first_non_empty(
        live_brief.get("source_quality_state"),
        _dig(live_brief, "latest_scene", "source_quality_state"),
        _dig(live_brief, "candidate", "source_quality_state"),
        default="SOURCE_QUALITY_UNKNOWN",
    )
    source_mode = _first_non_empty(
        live_brief.get("source_mode"),
        _dig(live_brief, "latest_scene", "source_mode"),
        _dig(live_brief, "candidate", "source_mode"),
        default="SOURCE_MODE_UNKNOWN",
    )
    data_visibility = _first_non_empty(
        live_brief.get("data_visibility"),
        _dig(live_brief, "latest_scene", "data_visibility"),
        _dig(live_brief, "candidate", "data_visibility"),
        default="DATA_VISIBILITY_UNKNOWN",
    )
    confidence_cap = _first_non_empty(
        live_brief.get("confidence_cap"),
        _dig(live_brief, "latest_scene", "confidence_cap"),
        _dig(live_brief, "candidate", "confidence_cap"),
        default="UNKNOWN",
    )

    if forbidden_hits:
        payload_state = BLOCKED_FORBIDDEN_LANGUAGE_STATE
    elif raw_unavailable:
        payload_state = BLOCKED_RAW_UNAVAILABLE_STATE
    elif brief_state not in {"B9_LIVE_BRIEF_READY", "B9_LIVE_SCENE_RECOGNITION_READY"}:
        payload_state = BLOCKED_BRIEF_NOT_READY_STATE
    elif source_quality_state in {"SOURCE_RAW_NUANCED", "SOURCE_PROXY_ONLY", "SOURCE_RECONSTRUCTED_LIMITED", "SOURCE_QUALITY_WEAK_LIMITED", "SOURCE_UNKNOWN_LIMITED"} or low_trust:
        payload_state = REVIEW_LIMITED_SOURCE_STATE
    else:
        payload_state = READY_STATE

    candidate_id = _first_non_empty(
        live_brief.get("candidate_id"),
        _dig(live_brief, "latest_scene", "candidate_id"),
        _dig(live_brief, "candidate", "candidate_id"),
        default="B9_REALITY_BOARD_CANDIDATE_UNKNOWN",
    )
    symbol = _first_non_empty(live_brief.get("symbol"), _dig(live_brief, "latest_scene", "symbol"), default="UNKNOWN")
    time_start = _first_non_empty(live_brief.get("time_start"), _dig(live_brief, "latest_scene", "time_start"), default="UNKNOWN")
    time_end = _first_non_empty(live_brief.get("time_end"), _dig(live_brief, "latest_scene", "time_end"), default="UNKNOWN")
    session = _first_non_empty(live_brief.get("session"), live_brief.get("b9_session"), _dig(live_brief, "latest_scene", "session"), default="SESSION_UNKNOWN")
    scene_role = _first_non_empty(live_brief.get("scene_role"), _dig(live_brief, "latest_scene", "scene_role"), default="SCENE_ROLE_UNKNOWN")
    price_verdict = _first_non_empty(live_brief.get("price_verdict"), live_brief.get("b9_price_verdict_state"), _dig(live_brief, "latest_scene", "price_verdict"), default="PENDING")
    memory_family = _first_non_empty(live_brief.get("memory_family"), live_brief.get("b6_memory_family"), default="MEMORY_FAMILY_UNKNOWN")
    memory_confidence_ladder = _first_non_empty(live_brief.get("memory_confidence_ladder"), live_brief.get("b9_memory_confidence_ladder"), default="MEMORY_CONFIDENCE_UNKNOWN")
    false_positive_state = _first_non_empty(live_brief.get("false_positive_state"), live_brief.get("b9_memory_false_positive_state"), default="MEMORY_FP_UNKNOWN")
    top_match_film_id = _first_non_empty(live_brief.get("top_match_film_id"), _dig(live_brief, "top_match", "film_id"), default="NO_MATCH")

    match_count = int(live_brief.get("match_count", len(_as_list(live_brief.get("matches")))))
    cross_family_match_count = int(live_brief.get("cross_family_match_count", 0))

    attention_reason_fr = _first_non_empty(
        live_brief.get("attention_reason_fr"),
        live_brief.get("summary_fr"),
        _dig(live_brief, "french_report", "ce_que_b9_voit"),
        default="B9 expose une scène candidate à lire, sans décision d'exécution.",
    )
    b9_reading_fr = _first_non_empty(
        live_brief.get("b9_reading_fr"),
        live_brief.get("brief_fr"),
        _dig(live_brief, "french_report", "ce_que_b9_voit"),
        default="Lecture B9 disponible mais non détaillée dans le brief source.",
    )
    memory_context_fr = _first_non_empty(
        live_brief.get("memory_context_fr"),
        live_brief.get("b6_memory_summary_fr"),
        default="La mémoire B6 fournit une proximité de film, pas une répétition certaine.",
    )

    technical_risks = _as_list(live_brief.get("technical_risks"))
    if not technical_risks:
        technical_risks = _as_list(live_brief.get("technical_limits"))
    if source_mode in {"M1_BAR_PROXY", "TF30_BAR_PROXY"} or "RECONSTRUCTED" in data_visibility:
        technical_risks.append("Lecture proxy/reconstruite : ne pas durcir en vérité raw.")
    if false_positive_state in {"MEMORY_FP_MEDIUM", "MEMORY_FP_HIGH"}:
        technical_risks.append("Similarité mémoire potentiellement piégeuse : lire les différences avant comparaison.")
    if memory_confidence_ladder in {"MEMORY_SOURCE_LIMITED", "MEMORY_SESSION_MISMATCH", "MEMORY_RETEST_MISSING", "MEMORY_PARTIAL_COMPARABLE"}:
        technical_risks.append(f"Comparabilité mémoire limitée : {memory_confidence_ladder}.")
    if not technical_risks:
        technical_risks = ["Aucune alerte technique forte dans le brief source."]

    what_to_watch_next = _as_list(live_brief.get("what_to_watch_next_fr"))
    if not what_to_watch_next:
        what_to_watch_next = [
            "Observer si le verdict prix confirme ou invalide le rôle de scène.",
            "Surveiller si la mémoire de zone est défendue, consommée ou rejetée.",
            "Comparer le prochain mouvement au film B6 proche sans supposer une répétition.",
        ]

    limits = _as_list(live_brief.get("limits")) or _as_list(live_brief.get("technical_limits"))
    limits.extend([
        "Payload candidat uniquement : aucun branchement dashboard live.",
        "Aucune transmission Telegram.",
        "Aucune décision d'exécution.",
        "Aucun taux de réussite.",
    ])

    payload = RealityBoardPayloadCandidate(
        version=VERSION,
        payload_state=payload_state,
        payload_type="B9_REALITY_BOARD_PAYLOAD_CANDIDATE",
        generated_at_utc=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        candidate_id=candidate_id,
        symbol=symbol,
        time_start=time_start,
        time_end=time_end,
        session=session,
        scene_role=scene_role,
        price_verdict=price_verdict,
        source_quality_state=source_quality_state,
        source_mode=source_mode,
        data_visibility=data_visibility,
        confidence_cap=confidence_cap,
        memory_family=memory_family,
        memory_confidence_ladder=memory_confidence_ladder,
        false_positive_state=false_positive_state,
        top_match_film_id=top_match_film_id,
        match_count=match_count,
        cross_family_match_count=cross_family_match_count,
        attention_reason_fr=attention_reason_fr,
        b9_reading_fr=b9_reading_fr,
        memory_context_fr=memory_context_fr,
        technical_risks=technical_risks,
        what_to_watch_next_fr=what_to_watch_next,
        limits=limits,
        raw_unavailable_in_results=raw_unavailable,
        low_trust_in_results=low_trust,
        forbidden_language_hits=forbidden_hits,
        source_inputs={
            "live_brief_state": brief_state,
            "source_mode": source_mode,
            "data_visibility": data_visibility,
            "source_quality_state": source_quality_state,
        },
        read_only_contract={
            "writes_powerflow_db": False,
            "writes_tick_archive_db": False,
            "writes_dashboard": False,
            "sends_telegram": False,
            "emits_execution_decision": False,
            "emits_success_probability": False,
        },
    ).to_dict()

    missing = [field for field in REQUIRED_PAYLOAD_FIELDS if field not in payload or payload[field] in (None, "")]
    payload["missing_required_field_counts"] = {field: 1 for field in missing}
    return payload


def build_blocked_missing_input_payload(missing_inputs: Iterable[str]) -> Dict[str, Any]:
    missing_list = list(missing_inputs)
    payload = {
        "version": VERSION,
        "payload_state": BLOCKED_MISSING_INPUT_STATE,
        "payload_type": "B9_REALITY_BOARD_PAYLOAD_CANDIDATE",
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "candidate_id": "BLOCKED_MISSING_INPUTS",
        "symbol": "UNKNOWN",
        "time_start": "UNKNOWN",
        "time_end": "UNKNOWN",
        "session": "SESSION_UNKNOWN",
        "scene_role": "UNKNOWN",
        "price_verdict": "PENDING",
        "source_quality_state": "SOURCE_QUALITY_UNKNOWN",
        "source_mode": "SOURCE_MODE_UNKNOWN",
        "data_visibility": "DATA_VISIBILITY_UNKNOWN",
        "confidence_cap": "UNKNOWN",
        "memory_family": "MEMORY_FAMILY_UNKNOWN",
        "memory_confidence_ladder": "MEMORY_CONFIDENCE_UNKNOWN",
        "false_positive_state": "MEMORY_FP_UNKNOWN",
        "top_match_film_id": "NO_MATCH",
        "match_count": 0,
        "cross_family_match_count": 0,
        "attention_reason_fr": "Payload Reality Board bloqué : le brief live T0148 est manquant.",
        "b9_reading_fr": "Aucune lecture Reality Board ne doit être construite sans brief live source.",
        "memory_context_fr": "Mémoire B6 non évaluée car l'entrée source est manquante.",
        "technical_risks": [f"Entrée manquante : {item}" for item in missing_list],
        "what_to_watch_next_fr": ["Générer d'abord T0148 B9 Live Brief Once Runner."],
        "limits": [
            "Payload candidat uniquement.",
            "Aucune écriture DB.",
            "Aucun dashboard live.",
            "Aucune transmission Telegram.",
            "Aucune décision d'exécution.",
        ],
        "raw_unavailable_in_results": False,
        "low_trust_in_results": False,
        "forbidden_language_hits": [],
        "source_inputs": {"missing_inputs": missing_list},
        "read_only_contract": {
            "writes_powerflow_db": False,
            "writes_tick_archive_db": False,
            "writes_dashboard": False,
            "sends_telegram": False,
            "emits_execution_decision": False,
            "emits_success_probability": False,
        },
        "missing_required_field_counts": {},
    }
    return payload
