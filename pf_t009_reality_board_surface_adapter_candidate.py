"""T0169 - B9 Reality Board Surface Adapter Candidate V0.

Read-only adapter that converts B9 Reality Board read-model artifacts into a
stable surface payload candidate. It does not import cockpit modules, does not
write DB files, and does not send Telegram messages.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import csv
import hashlib
import re
import zipfile

VERSION = "T0169_B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bachat\b", re.IGNORECASE),
    re.compile(r"\bvente\b", re.IGNORECASE),
    re.compile(r"probabilit[eé]\s+de\s+(r[eé]ussite|succ[eè]s)", re.IGNORECASE),
    re.compile(r"taux\s+de\s+(r[eé]ussite|succ[eè]s)", re.IGNORECASE),
    re.compile(r"signal\s+gagnant", re.IGNORECASE),
]

READY_STATES = {
    "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_READY",
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_READY",
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK",
    "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REVIEW_LIMITED_SOURCE",
}

PARTIAL_MARKERS = {
    "PARTIAL_INPUTS_MISSING",
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK",
    "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_REVIEW_LIMITED_SOURCE",
}

BLOCKED_MARKERS = {
    "BLOCKED_MISSING_INPUTS",
    "BLOCKED_MISSING_LIVE_BRIEF_INPUT",
    "BLOCKED_LIVE_BRIEF_NOT_READY",
    "BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS",
    "BLOCKED_RAW_UNAVAILABLE_IN_ATTENTION_PACKET",
    "BLOCKED_FORBIDDEN_LANGUAGE",
    "BLOCKED_MISSING_NO_DECISION_GUARD",
}

DEFAULT_FR = {
    "SCENE_ACCEPTED": "Scène acceptée par le prix",
    "SCENE_REJECTED": "Scène rejetée par le prix",
    "SCENE_TESTING": "Scène en test",
    "SCENE_MEMORY_SHIFTED": "Mémoire de zone déplacée",
    "ACCEPTED": "Accepté par le prix",
    "REJECTED": "Rejeté par le prix",
    "PULLBACK_ABSORBED": "Pullback absorbé",
    "FAILED_REINTEGRATION": "Réintégration échouée",
    "MEMORY_PARTIAL_COMPARABLE": "Mémoire comparable partielle",
    "MEMORY_STRONG_COMPARABLE": "Mémoire fortement comparable",
    "MEMORY_RETEST_MISSING": "Mémoire avec retest manquant",
    "MEMORY_SESSION_MISMATCH": "Mémoire comparable mais session différente",
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK": "Surface à afficher avec limites techniques visibles",
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_READY": "Surface prête pour lecture candidat",
}


def _load_json(path: Optional[Path]) -> Dict[str, Any]:
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {"_value": data}
    except Exception as exc:  # pragma: no cover - defensive
        return {"_load_error": str(exc), "_path": str(p)}


def _first_present(*values: Any, default: Any = "") -> Any:
    for value in values:
        if value not in (None, "", [], {}):
            return value
    return default


def _nested(data: Dict[str, Any], *keys: str, default: Any = "") -> Any:
    cur: Any = data
    for key in keys:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        else:
            return default
    return cur


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "rows", "matches", "similar_films", "false_positive_contexts"):
            if isinstance(value.get(key), list):
                return value[key]
        return [value]
    return [value]


def _scan_forbidden_texts(payload: Any) -> List[str]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    hits: List[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        if pattern.search(text):
            hits.append(pattern.pattern)
    return hits


def _extract_display_map(display_contract: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
    entries = display_contract.get("entries") or display_contract.get("events") or []
    result: Dict[str, Dict[str, str]] = {}
    if isinstance(entries, dict):
        for key, value in entries.items():
            if isinstance(value, dict):
                result[key] = value
            else:
                result[key] = {"label_fr": str(value)}
    elif isinstance(entries, list):
        for row in entries:
            if not isinstance(row, dict):
                continue
            key = str(row.get("enum_key") or row.get("key") or row.get("event") or "")
            if key:
                result[key] = row
    return result


def _fr(enum_value: Any, display_map: Dict[str, Dict[str, str]]) -> str:
    if not enum_value:
        return "Non renseigné"
    key = str(enum_value)
    row = display_map.get(key, {})
    return str(row.get("label_fr") or row.get("short_fr") or row.get("phrase_fr") or DEFAULT_FR.get(key) or key.replace("_", " ").title())


def _surface_state(read_model: Dict[str, Any], panel: Dict[str, Any], payload: Dict[str, Any]) -> str:
    candidate_states = [
        str(read_model.get("read_model_state") or ""),
        str(read_model.get("gate_state") or ""),
        str(panel.get("panel_state") or ""),
        str(payload.get("payload_state") or payload.get("state") or ""),
    ]
    if any(state in BLOCKED_MARKERS or state.startswith("BLOCKED_") for state in candidate_states):
        return "B9_SURFACE_ADAPTER_BLOCKED_UPSTREAM"
    if not read_model and not payload and not panel:
        return "BLOCKED_MISSING_SURFACE_INPUTS"
    if any(state in PARTIAL_MARKERS for state in candidate_states):
        return "B9_SURFACE_ADAPTER_CANDIDATE_PARTIAL_INPUTS"
    if any(state in READY_STATES for state in candidate_states) or read_model or payload:
        return "B9_SURFACE_ADAPTER_CANDIDATE_READY"
    return "B9_SURFACE_ADAPTER_CANDIDATE_REVIEW_REQUIRED"


def build_surface_adapter(
    read_model: Dict[str, Any],
    panel: Dict[str, Any],
    payload: Dict[str, Any],
    display_contract: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    display_map = _extract_display_map(display_contract or {})
    candidate_id = _first_present(
        read_model.get("candidate_id"),
        _nested(read_model, "current_scene", "candidate_id"),
        panel.get("candidate_id"),
        _nested(panel, "scene", "candidate_id"),
        payload.get("candidate_id"),
        _nested(payload, "candidate", "candidate_id"),
        default="UNKNOWN_CANDIDATE",
    )
    scene_state = _first_present(
        read_model.get("scene_state"),
        _nested(read_model, "current_scene", "scene_state"),
        panel.get("scene_state"),
        _nested(panel, "scene", "scene_state"),
        payload.get("scene_state"),
        default="SCENE_REVIEW_REQUIRED",
    )
    transition = _first_present(
        read_model.get("scene_transition"),
        _nested(read_model, "current_scene", "scene_transition"),
        panel.get("scene_transition"),
        payload.get("scene_transition"),
        default="TRANSITION_NOT_PROVIDED",
    )
    price_verdict = _first_present(
        read_model.get("price_verdict"),
        _nested(read_model, "current_scene", "price_verdict"),
        panel.get("price_verdict"),
        payload.get("price_verdict"),
        default="PENDING",
    )
    memory_ladder = _first_present(
        read_model.get("memory_confidence_ladder"),
        _nested(read_model, "memory_context", "memory_confidence_ladder"),
        panel.get("memory_confidence_ladder"),
        payload.get("memory_confidence_ladder"),
        default="MEMORY_PARTIAL_COMPARABLE",
    )
    source_quality = _first_present(
        read_model.get("source_quality_state"),
        _nested(read_model, "source_quality", "state"),
        payload.get("source_quality_state"),
        default="SOURCE_QUALITY_REVIEW_REQUIRED",
    )
    top_match_film_id = _first_present(
        read_model.get("top_match_film_id"),
        _nested(read_model, "memory_context", "top_match_film_id"),
        payload.get("top_match_film_id"),
        default="",
    )
    match_count = int(_first_present(
        read_model.get("match_count"),
        _nested(read_model, "memory_context", "match_count"),
        payload.get("match_count"),
        default=0,
    ) or 0)
    active_zone = _first_present(
        read_model.get("active_zone"),
        _nested(read_model, "current_scene", "active_zone"),
        panel.get("active_zone"),
        payload.get("active_zone"),
        default="Zone non renseignée",
    )
    latest_node = _first_present(
        read_model.get("latest_node"),
        _nested(read_model, "current_scene", "latest_node"),
        panel.get("latest_node"),
        payload.get("latest_node"),
        default="Node non renseigné",
    )
    technical_risks = []
    for container in (read_model, panel, payload):
        for key in ("technical_risks", "technical_limits", "risks", "limits"):
            technical_risks.extend([str(x) for x in _as_list(container.get(key)) if str(x).strip()])
    if not technical_risks:
        technical_risks = ["Aucune limite technique explicite fournie par les inputs."]

    what_to_watch_next = _first_present(
        read_model.get("what_to_watch_next"),
        _nested(read_model, "next_watch", "fr"),
        payload.get("what_to_watch_next"),
        default="Surveiller la réaction du prix sur la zone active et la stabilité de la mémoire comparable.",
    )

    surface_state = _surface_state(read_model, panel, payload)
    surface_payload = {
        "version": VERSION,
        "surface_state": surface_state,
        "candidate_id": candidate_id,
        "display_language": "fr-FR-trader",
        "read_only": True,
        "no_dashboard_live_write": True,
        "no_telegram_send": True,
        "no_db_write": True,
        "no_decision_guard": True,
        "headline_fr": f"B9 voit : {_fr(scene_state, display_map)}",
        "surface_cards": [
            {"slot": "ce_que_b9_voit", "label_fr": "Ce que B9 voit", "value_fr": _fr(scene_state, display_map), "raw_value": scene_state},
            {"slot": "transition", "label_fr": "Transition", "value_fr": _fr(transition, display_map), "raw_value": transition},
            {"slot": "zone_active", "label_fr": "Zone active", "value_fr": str(active_zone), "raw_value": active_zone},
            {"slot": "node_terrain", "label_fr": "Node terrain", "value_fr": str(latest_node), "raw_value": latest_node},
            {"slot": "verdict_prix", "label_fr": "Verdict prix", "value_fr": _fr(price_verdict, display_map), "raw_value": price_verdict},
            {"slot": "memoire_b6", "label_fr": "Mémoire B6", "value_fr": _fr(memory_ladder, display_map), "raw_value": memory_ladder},
            {"slot": "film_proche", "label_fr": "Film proche", "value_fr": top_match_film_id or "Aucun film proche affichable", "raw_value": top_match_film_id},
            {"slot": "source_quality", "label_fr": "Source quality", "value_fr": _fr(source_quality, display_map), "raw_value": source_quality},
            {"slot": "a_surveiller", "label_fr": "À surveiller", "value_fr": str(what_to_watch_next), "raw_value": what_to_watch_next},
        ],
        "summary": {
            "scene_state": scene_state,
            "scene_state_fr": _fr(scene_state, display_map),
            "scene_transition": transition,
            "scene_transition_fr": _fr(transition, display_map),
            "price_verdict": price_verdict,
            "price_verdict_fr": _fr(price_verdict, display_map),
            "memory_confidence_ladder": memory_ladder,
            "memory_confidence_ladder_fr": _fr(memory_ladder, display_map),
            "match_count": match_count,
            "top_match_film_id": top_match_film_id,
            "false_positive_context_available": bool(_first_present(read_model.get("false_positive_context_available"), payload.get("false_positive_context_available"), default=False)),
            "source_quality_state": source_quality,
            "source_quality_state_fr": _fr(source_quality, display_map),
        },
        "technical_risks": sorted(set(technical_risks)),
        "what_to_watch_next_fr": str(what_to_watch_next),
        "what_b9_cannot_conclude_fr": [
            "B9 ne transforme pas cette scène en décision d’exécution.",
            "Une mémoire comparable n’est pas une répétition certaine.",
            "Une source proxy ou partielle reste techniquement limitée.",
        ],
        "input_presence": {
            "read_model_present": bool(read_model),
            "panel_present": bool(panel),
            "payload_present": bool(payload),
            "display_contract_present": bool(display_contract),
        },
    }
    hits = _scan_forbidden_texts(surface_payload)
    surface_payload["forbidden_language_hits"] = hits
    if hits:
        surface_payload["surface_state"] = "BLOCKED_FORBIDDEN_LANGUAGE"
    return surface_payload


def write_outputs(surface: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json"
    md_path = output_dir / "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.md"
    cards_path = output_dir / "B9_REALITY_BOARD_SURFACE_CARDS_V0.csv"
    risks_path = output_dir / "B9_REALITY_BOARD_SURFACE_TECHNICAL_RISKS_V0.csv"
    manifest_path = output_dir / "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_MANIFEST.json"
    zip_path = output_dir / "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.zip"

    json_path.write_text(json.dumps(surface, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# B9 Reality Board Surface Adapter Candidate V0",
        "",
        f"State: `{surface.get('surface_state')}`",
        f"Candidate: `{surface.get('candidate_id')}`",
        "",
        "## Lecture surface",
    ]
    for card in surface.get("surface_cards", []):
        lines.append(f"- **{card.get('label_fr')}** : {card.get('value_fr')}")
    lines.extend(["", "## Risques techniques"])
    for risk in surface.get("technical_risks", []):
        lines.append(f"- {risk}")
    lines.extend(["", "## À surveiller", str(surface.get("what_to_watch_next_fr") or "Non renseigné")])
    lines.extend(["", "## Ce que B9 ne peut pas conclure"])
    for item in surface.get("what_b9_cannot_conclude_fr", []):
        lines.append(f"- {item}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with cards_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["slot", "label_fr", "value_fr", "raw_value"])
        writer.writeheader()
        for row in surface.get("surface_cards", []):
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})

    with risks_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["risk_fr"])
        writer.writeheader()
        for risk in surface.get("technical_risks", []):
            writer.writerow({"risk_fr": risk})

    manifest = {
        "version": VERSION,
        "surface_state": surface.get("surface_state"),
        "candidate_id": surface.get("candidate_id"),
        "files": [json_path.name, md_path.name, cards_path.name, risks_path.name],
        "read_only": True,
        "no_dashboard_live_write": True,
        "no_telegram_send": True,
        "no_db_write": True,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in [json_path, md_path, cards_path, risks_path, manifest_path]:
            zf.write(p, arcname=p.name)
    return {
        "version": VERSION,
        "surface_state": surface.get("surface_state"),
        "candidate_id": surface.get("candidate_id"),
        "output_dir": str(output_dir),
        "zip": str(zip_path),
        "forbidden_language_hits": surface.get("forbidden_language_hits", []),
    }


def run(
    read_model_json: Optional[str] = None,
    panel_json: Optional[str] = None,
    payload_json: Optional[str] = None,
    display_contract_json: Optional[str] = None,
    output_dir: str = "outputs/b9_reality_board_surface_adapter_candidate_v0",
) -> Dict[str, Any]:
    read_model = _load_json(Path(read_model_json)) if read_model_json else {}
    panel = _load_json(Path(panel_json)) if panel_json else {}
    payload = _load_json(Path(payload_json)) if payload_json else {}
    display_contract = _load_json(Path(display_contract_json)) if display_contract_json else {}
    surface = build_surface_adapter(read_model, panel, payload, display_contract)
    return write_outputs(surface, Path(output_dir))
