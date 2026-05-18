"""T0156 - B9 Reality Board Integration Candidate V0.

Read-only transformer from a B9 Trader Attention Packet into a Reality Board
candidate payload. This module does not write to DB, does not touch dashboard
runtime, and does not send Telegram messages.
"""
from __future__ import annotations

import csv
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

VERSION = "T0156_B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0"

READY = "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_READY"
REVIEW = "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_REVIEW_TECHNICAL_RISK"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_ATTENTION_PACKET_INPUT"
BLOCKED_PACKET_NOT_READY = "BLOCKED_ATTENTION_PACKET_NOT_READY"
BLOCKED_RAW_UNAVAILABLE = "BLOCKED_RAW_UNAVAILABLE_IN_ATTENTION_PACKET"
BLOCKED_FORBIDDEN_LANGUAGE = "BLOCKED_FORBIDDEN_LANGUAGE"
BLOCKED_DECISION_GUARD = "BLOCKED_MISSING_NO_DECISION_GUARD"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bLONG\b", re.IGNORECASE),
    re.compile(r"\bSHORT\b", re.IGNORECASE),
    re.compile(r"\bENTRY\b", re.IGNORECASE),
    re.compile(r"\bTP\b", re.IGNORECASE),
    re.compile(r"\bSL\b", re.IGNORECASE),
    re.compile(r"probabilit[eé]\s+de\s+succ[eè]s", re.IGNORECASE),
    re.compile(r"taux\s+de\s+r[eé]ussite", re.IGNORECASE),
    re.compile(r"win\s*rate", re.IGNORECASE),
]

BLOCKED_PACKET_STATES = {
    "B9_TRADER_ATTENTION_PACKET_BLOCKED",
    "B9_TRADER_ATTENTION_PACKET_BLOCKED_RAW_UNAVAILABLE",
    "BLOCKED_RAW_UNAVAILABLE_IN_MEMORY_RESULTS",
    "BLOCKED_MISSING_INPUTS",
    "BLOCKED_FORBIDDEN_LANGUAGE",
}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float, bool)):
        return str(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _first_present(mapping: Mapping[str, Any], keys: Iterable[str], default: Any = None) -> Any:
    for key in keys:
        if key in mapping and mapping[key] not in (None, ""):
            return mapping[key]
    return default


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def extract_packet(data: Mapping[str, Any]) -> Dict[str, Any]:
    """Normalize supported attention-packet shapes into one dict."""
    for key in ("attention_packet", "trader_attention_packet", "packet", "latest_packet"):
        candidate = data.get(key)
        if isinstance(candidate, dict):
            return dict(candidate)
    packets = data.get("packets") or data.get("attention_packets")
    if isinstance(packets, list) and packets and isinstance(packets[0], dict):
        return dict(packets[0])
    # T0155 sample/root shape already carries packet fields at top-level.
    return dict(data)


def find_forbidden_language(payload: Mapping[str, Any]) -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    safe_skip_keys = {
        "no_trade_decision_guard",
        "forbidden_language_hits",
        "forbidden_language_hit_count",
        "no_buy_sell_guard",
    }

    def walk(prefix: str, value: Any) -> None:
        if prefix.split(".")[-1] in safe_skip_keys:
            return
        if isinstance(value, Mapping):
            for k, v in value.items():
                walk(f"{prefix}.{k}" if prefix else str(k), v)
            return
        if isinstance(value, list):
            for idx, item in enumerate(value):
                walk(f"{prefix}[{idx}]", item)
            return
        text = _as_text(value)
        for pattern in FORBIDDEN_PATTERNS:
            match = pattern.search(text)
            if match:
                hits.append({"field": prefix, "hit": match.group(0)})

    walk("", payload)
    return hits


def _boolish(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "oui", "y"}
    if value is None:
        return default
    return bool(value)


def _extract_memory_context(packet: Mapping[str, Any]) -> Dict[str, Any]:
    memory = _first_present(packet, ["memory_context", "b6_memory_context", "memory"], {})
    if not isinstance(memory, dict):
        memory = {}
    return dict(memory)


def _extract_technical_risks(packet: Mapping[str, Any]) -> List[str]:
    risks = _first_present(packet, ["technical_risks", "technical_risks_fr", "risk_flags"], [])
    if isinstance(risks, str):
        return [line.strip(" -") for line in risks.splitlines() if line.strip(" -")]
    return [str(item) for item in _as_list(risks) if str(item).strip()]


def _active_zone(packet: Mapping[str, Any]) -> Dict[str, Any]:
    zone = _first_present(packet, ["active_zone", "zone", "current_zone"], {})
    if isinstance(zone, dict):
        return dict(zone)
    return {"label": _as_text(zone)} if zone else {}


def _latest_node(packet: Mapping[str, Any]) -> Dict[str, Any]:
    node = _first_present(packet, ["latest_node", "terrain_node", "node"], {})
    if isinstance(node, dict):
        return dict(node)
    return {"label": _as_text(node)} if node else {}


def _derive_payload_state(packet: Mapping[str, Any], forbidden_hits: List[Dict[str, str]]) -> str:
    if not packet:
        return BLOCKED_MISSING_INPUT
    if forbidden_hits:
        return BLOCKED_FORBIDDEN_LANGUAGE

    packet_state = _as_text(_first_present(packet, ["packet_state", "attention_packet_state", "state"], ""))
    if packet_state in BLOCKED_PACKET_STATES or packet_state.startswith("BLOCKED_"):
        if "RAW_UNAVAILABLE" in packet_state:
            return BLOCKED_RAW_UNAVAILABLE
        return BLOCKED_PACKET_NOT_READY

    no_decision_guard = _boolish(_first_present(packet, ["no_trade_decision_guard", "no_decision_guard"], True), True)
    if not no_decision_guard:
        return BLOCKED_DECISION_GUARD

    raw_unavailable = _boolish(_first_present(packet, ["raw_unavailable_in_results", "raw_unavailable_allowed_count"], False), False)
    if raw_unavailable:
        return BLOCKED_RAW_UNAVAILABLE

    memory = _extract_memory_context(packet)
    memory_ladder = _as_text(_first_present(memory, ["memory_confidence_ladder", "memory_confidence_state"], ""))
    risks = _extract_technical_risks(packet)
    packet_state_upper = packet_state.upper()
    if risks or "REVIEW" in packet_state_upper or "LIMITED" in memory_ladder or "PARTIAL" in memory_ladder:
        return REVIEW
    return READY


def build_reality_board_payload(data: Mapping[str, Any]) -> Dict[str, Any]:
    packet = extract_packet(data)
    forbidden_hits = find_forbidden_language(packet)
    payload_state = _derive_payload_state(packet, forbidden_hits)
    memory = _extract_memory_context(packet)
    technical_risks = _extract_technical_risks(packet)

    candidate_id = _as_text(_first_present(packet, ["candidate_id", "scene_id", "id"], "UNKNOWN_CANDIDATE"))
    scene_state = _as_text(_first_present(packet, ["scene_state", "b9_scene_state"], "SCENE_UNKNOWN"))
    price_verdict = _as_text(_first_present(packet, ["price_verdict", "b9_price_verdict_state"], "PENDING"))
    scene_role = _as_text(_first_present(packet, ["scene_role", "b9_scene_role"], "SCENE_ROLE_UNKNOWN"))
    attention_reason = _as_text(_first_present(packet, ["attention_reason", "attention_reason_fr"], "Scene candidate B9 a inspecter."))
    what_to_watch_next = _as_text(_first_present(packet, ["what_to_watch_next", "what_to_watch_next_fr"], "Surveiller le prochain retest, la source et la coherence memoire."))

    match_count = int(_first_present(memory, ["match_count", "matches"], _first_present(packet, ["match_count"], 0)) or 0)
    top_match = _as_text(_first_present(memory, ["top_match_film_id", "top_film_id"], _first_present(packet, ["top_match_film_id"], "")))
    fp_available = _boolish(_first_present(memory, ["false_positive_context_available"], _first_present(packet, ["false_positive_context_available"], False)), False)
    memory_ladder = _as_text(_first_present(memory, ["memory_confidence_ladder", "memory_confidence_state"], _first_present(packet, ["memory_confidence_ladder"], "MEMORY_UNKNOWN")))

    active_zone = _active_zone(packet)
    latest_node = _latest_node(packet)
    technical_risks = technical_risks or ["Aucun risque technique explicite fourni par le packet."]

    payload: Dict[str, Any] = {
        "version": VERSION,
        "payload_state": payload_state,
        "generated_at_utc": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "candidate_id": candidate_id,
        "display_title_fr": f"B9 - Scene candidate {candidate_id}",
        "attention_reason_fr": attention_reason,
        "scene_state": scene_state,
        "scene_role": scene_role,
        "price_verdict": price_verdict,
        "active_zone": active_zone,
        "latest_node": latest_node,
        "memory_context": {
            "memory_confidence_ladder": memory_ladder,
            "match_count": match_count,
            "top_match_film_id": top_match,
            "false_positive_context_available": fp_available,
            "memory_reading_fr": _as_text(_first_present(memory, ["memory_reading_fr", "summary_fr"], "Memoire comparable a lire avec ses limites techniques.")),
        },
        "technical_risks": technical_risks,
        "what_to_watch_next_fr": what_to_watch_next,
        "guards": {
            "read_only": True,
            "no_db_write": True,
            "no_dashboard_write": True,
            "no_telegram": True,
            "no_directional_order": True,
            "no_success_probability": True,
            "trader_decides": True,
        },
        "forbidden_language_hits": forbidden_hits,
        "no_trade_decision_guard": _boolish(_first_present(packet, ["no_trade_decision_guard", "no_decision_guard"], True), True),
    }
    return payload


def _md_escape(value: Any) -> str:
    return _as_text(value).replace("\n", " ").strip()


def render_markdown(payload: Mapping[str, Any]) -> str:
    memory = payload.get("memory_context", {}) if isinstance(payload.get("memory_context"), Mapping) else {}
    active_zone = payload.get("active_zone", {}) if isinstance(payload.get("active_zone"), Mapping) else {}
    latest_node = payload.get("latest_node", {}) if isinstance(payload.get("latest_node"), Mapping) else {}
    risks = payload.get("technical_risks", [])
    risk_lines = "\n".join(f"- {risk}" for risk in _as_list(risks))
    hits = payload.get("forbidden_language_hits", [])
    hit_lines = "\n".join(f"- {hit}" for hit in hits) if hits else "- Aucun"
    return f"""# B9 Reality Board Integration Candidate V0

## Etat

```text
{payload.get('payload_state')}
```

## Scene candidate

- Candidate : `{payload.get('candidate_id')}`
- Etat de scene : `{payload.get('scene_state')}`
- Role : `{payload.get('scene_role')}`
- Verdict prix : `{payload.get('price_verdict')}`

## Raison d'attention

{_md_escape(payload.get('attention_reason_fr'))}

## Zone active

```json
{json.dumps(active_zone, ensure_ascii=False, indent=2)}
```

## Node terrain

```json
{json.dumps(latest_node, ensure_ascii=False, indent=2)}
```

## Memoire B6

- Echelle : `{memory.get('memory_confidence_ladder', 'MEMORY_UNKNOWN')}`
- Films proches : `{memory.get('match_count', 0)}`
- Top film : `{memory.get('top_match_film_id', '')}`
- Contexte faux positif disponible : `{memory.get('false_positive_context_available', False)}`

{_md_escape(memory.get('memory_reading_fr', ''))}

## Risques techniques

{risk_lines}

## A surveiller ensuite

{_md_escape(payload.get('what_to_watch_next_fr'))}

## Garde-fous

- Read-only : true
- Aucune ecriture powerflow.db
- Aucune ecriture tick_archive.db
- Aucun dashboard live
- Aucun Telegram
- Aucun ordre directionnel
- Aucun taux de reussite
- Le trader decide

## Langage interdit detecte

{hit_lines}
"""


def write_outputs(payload: Mapping[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json"
    md_path = output_dir / "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.md"
    csv_path = output_dir / "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_ROW_V0.csv"
    manifest_path = output_dir / "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_MANIFEST.json"
    zip_path = output_dir / "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.zip"

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")

    memory = payload.get("memory_context", {}) if isinstance(payload.get("memory_context"), Mapping) else {}
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "candidate_id",
            "payload_state",
            "scene_state",
            "scene_role",
            "price_verdict",
            "memory_confidence_ladder",
            "match_count",
            "top_match_film_id",
            "false_positive_context_available",
            "forbidden_language_hit_count",
        ])
        writer.writeheader()
        writer.writerow({
            "candidate_id": payload.get("candidate_id", ""),
            "payload_state": payload.get("payload_state", ""),
            "scene_state": payload.get("scene_state", ""),
            "scene_role": payload.get("scene_role", ""),
            "price_verdict": payload.get("price_verdict", ""),
            "memory_confidence_ladder": memory.get("memory_confidence_ladder", ""),
            "match_count": memory.get("match_count", 0),
            "top_match_film_id": memory.get("top_match_film_id", ""),
            "false_positive_context_available": memory.get("false_positive_context_available", False),
            "forbidden_language_hit_count": len(payload.get("forbidden_language_hits", [])),
        })

    manifest = {
        "version": VERSION,
        "payload_state": payload.get("payload_state"),
        "candidate_id": payload.get("candidate_id"),
        "files": [json_path.name, md_path.name, csv_path.name],
        "read_only": True,
        "db_write": False,
        "dashboard_write": False,
        "telegram": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in (json_path, md_path, csv_path, manifest_path):
            zf.write(path, arcname=path.name)

    return {
        "json": str(json_path),
        "md": str(md_path),
        "csv": str(csv_path),
        "manifest": str(manifest_path),
        "zip": str(zip_path),
    }


def run_from_file(input_json: Path, output_dir: Path) -> Dict[str, Any]:
    data = load_json(input_json)
    payload = build_reality_board_payload(data)
    paths = write_outputs(payload, output_dir)
    memory = payload.get("memory_context", {}) if isinstance(payload.get("memory_context"), Mapping) else {}
    return {
        "version": VERSION,
        "payload_state": payload.get("payload_state"),
        "candidate_id": payload.get("candidate_id"),
        "scene_state": payload.get("scene_state"),
        "price_verdict": payload.get("price_verdict"),
        "memory_confidence_ladder": memory.get("memory_confidence_ladder"),
        "match_count": memory.get("match_count"),
        "top_match_film_id": memory.get("top_match_film_id"),
        "false_positive_context_available": memory.get("false_positive_context_available"),
        "forbidden_language_hits": payload.get("forbidden_language_hits", []),
        "zip": paths["zip"],
    }
