"""PowerFlow B9 Reality Board Read Model V0.

Read-only adapter for B9 dashboard candidate work.
It reads existing B9 output JSON files and emits a clean read model plus a
scene panel candidate. It does not import cockpit/dashboard/telegram modules
and does not touch any SQLite database.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

VERSION = "T0160_T0161_B9_REALITY_BOARD_READ_MODEL_V0"

READ_MODEL_OUTPUT_DIR = Path("outputs/b9_reality_board_read_model_v0")
PANEL_OUTPUT_DIR = Path("outputs/b9_reality_board_scene_panel_candidate_v0")
REPORT_OUTPUT_PATH = Path("docs/Reports/T0160_T0161_B9_REALITY_BOARD_DASHBOARD_CANDIDATE_INTEGRATION.md")

FORBIDDEN_DECISION_TERMS = (
    "BUY",
    "SELL",
    "buy",
    "sell",
    "Achat conseillé",
    "Vente conseillée",
    "ordre d'achat",
    "ordre de vente",
)

SECTION_ORDER = [
    "ce_que_b9_voit",
    "etat_de_scene",
    "transition",
    "zone_active",
    "node_terrain",
    "verdict_prix",
    "memoire_b6_proche",
    "similarites",
    "differences",
    "pieges_techniques",
    "source_quality",
    "ce_qu_il_faut_surveiller_ensuite",
    "ce_que_b9_ne_peut_pas_conclure",
]

SECTION_TITLES = {
    "ce_que_b9_voit": "Ce que B9 voit",
    "etat_de_scene": "État de scène",
    "transition": "Transition",
    "zone_active": "Zone active",
    "node_terrain": "Node terrain",
    "verdict_prix": "Verdict prix",
    "memoire_b6_proche": "Mémoire B6 proche",
    "similarites": "Similarités",
    "differences": "Différences",
    "pieges_techniques": "Pièges techniques",
    "source_quality": "Source quality",
    "ce_qu_il_faut_surveiller_ensuite": "Ce qu’il faut surveiller ensuite",
    "ce_que_b9_ne_peut_pas_conclure": "Ce que B9 ne peut pas conclure",
}

INPUT_SPECS = {
    "integration_candidate": Path("outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json"),
    "trader_attention_packet": Path("outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json"),
    "live_brief": Path("outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json"),
    "latest_scene_candidate": Path("outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json"),
    "french_event_display_contract": Path("outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json"),
}


@dataclass(frozen=True)
class LoadedInput:
    name: str
    path: Path
    exists: bool
    payload: Any = None
    error: Optional[str] = None
    sha256: Optional[str] = None


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def safe_read_json(path: Path) -> Tuple[Optional[Any], Optional[str], Optional[str]]:
    if not path.exists():
        return None, "MISSING", None
    try:
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()[:16]
        return json.loads(raw.decode("utf-8-sig")), None, sha
    except Exception as exc:  # pragma: no cover - defensive against malformed local outputs
        return None, f"JSON_READ_ERROR: {exc}", None


def load_inputs(repo: Path, input_specs: Mapping[str, Path] = INPUT_SPECS) -> Dict[str, LoadedInput]:
    loaded: Dict[str, LoadedInput] = {}
    for name, rel_path in input_specs.items():
        full_path = repo / rel_path
        payload, error, sha = safe_read_json(full_path)
        loaded[name] = LoadedInput(
            name=name,
            path=rel_path,
            exists=full_path.exists(),
            payload=payload,
            error=error,
            sha256=sha,
        )
    return loaded


def sanitize_text(value: Any) -> Any:
    """Neutralise decision-like vocabulary while preserving read-only meaning."""
    if isinstance(value, str):
        text = value
        replacements = {
            r"\bBUY\b": "PRESSION_UP_SOURCE_NEUTRALISEE",
            r"\bSELL\b": "PRESSION_DOWN_SOURCE_NEUTRALISEE",
            r"\bbuy\b": "pression_up_source_neutralisee",
            r"\bsell\b": "pression_down_source_neutralisee",
            r"Achat conseillé": "pression up neutralisée",
            r"Vente conseillée": "pression down neutralisée",
            r"ordre d'achat": "instruction neutralisée",
            r"ordre de vente": "instruction neutralisée",
        }
        for pattern, repl in replacements.items():
            text = re.sub(pattern, repl, text)
        return text
    if isinstance(value, list):
        return [sanitize_text(item) for item in value]
    if isinstance(value, dict):
        return {str(key): sanitize_text(val) for key, val in value.items()}
    return value


def flatten_items(obj: Any, prefix: str = "") -> Iterable[Tuple[str, Any]]:
    if isinstance(obj, Mapping):
        for key, val in obj.items():
            new_prefix = f"{prefix}.{key}" if prefix else str(key)
            yield new_prefix, val
            yield from flatten_items(val, new_prefix)
    elif isinstance(obj, list):
        for idx, val in enumerate(obj):
            new_prefix = f"{prefix}[{idx}]"
            yield new_prefix, val
            yield from flatten_items(val, new_prefix)


def first_by_key(payloads: Sequence[Any], key_patterns: Sequence[str]) -> Optional[Any]:
    lowered_patterns = [p.lower() for p in key_patterns]
    for payload in payloads:
        if payload is None:
            continue
        for key_path, value in flatten_items(payload):
            key_leaf = re.split(r"[.\[]", key_path)[-1].rstrip("]").lower()
            key_full = key_path.lower()
            if any(pattern == key_leaf or pattern in key_full for pattern in lowered_patterns):
                if value not in (None, "", [], {}):
                    return sanitize_text(value)
    return None


def collect_by_key(payloads: Sequence[Any], key_patterns: Sequence[str], limit: int = 8) -> List[Any]:
    seen: set[str] = set()
    values: List[Any] = []
    lowered_patterns = [p.lower() for p in key_patterns]
    for payload in payloads:
        if payload is None:
            continue
        for key_path, value in flatten_items(payload):
            key_leaf = re.split(r"[.\[]", key_path)[-1].rstrip("]").lower()
            key_full = key_path.lower()
            if any(pattern == key_leaf or pattern in key_full for pattern in lowered_patterns):
                if value in (None, "", [], {}):
                    continue
                sanitized = sanitize_text(value)
                marker = json.dumps(sanitized, ensure_ascii=False, sort_keys=True, default=str)
                if marker not in seen:
                    seen.add(marker)
                    values.append(sanitized)
                    if len(values) >= limit:
                        return values
    return values


def as_text_list(value: Any, fallback: str) -> List[str]:
    if value in (None, "", [], {}):
        return [fallback]
    if isinstance(value, list):
        result: List[str] = []
        for item in value:
            if isinstance(item, Mapping):
                result.append(json.dumps(sanitize_text(item), ensure_ascii=False, sort_keys=True))
            else:
                result.append(str(sanitize_text(item)))
        return result or [fallback]
    if isinstance(value, Mapping):
        return [json.dumps(sanitize_text(value), ensure_ascii=False, sort_keys=True)]
    return [str(sanitize_text(value))]


def normalize_scalar(value: Any, fallback: str = "NON_RENSEIGNE") -> str:
    if value in (None, "", [], {}):
        return fallback
    if isinstance(value, Mapping):
        return json.dumps(sanitize_text(value), ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return " | ".join(as_text_list(value, fallback))
    return str(sanitize_text(value))


def source_quality_summary(loaded: Mapping[str, LoadedInput]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    missing: List[str] = []
    errors: List[str] = []
    payloads = [item.payload for item in loaded.values() if item.payload is not None]
    for name, item in loaded.items():
        row = {
            "name": name,
            "path": item.path.as_posix(),
            "exists": item.exists,
            "status": "OK" if item.exists and item.error is None else item.error or "MISSING",
            "sha256_16": item.sha256,
        }
        rows.append(row)
        if not item.exists:
            missing.append(name)
        elif item.error:
            errors.append(f"{name}: {item.error}")

    source_mode = first_by_key(payloads, ["source_mode", "data_source_mode", "mode_source"])
    data_visibility = first_by_key(payloads, ["data_visibility", "visibility", "source_visibility"])
    confidence_cap = first_by_key(payloads, ["confidence_cap", "cap_confiance"])

    return {
        "rows": rows,
        "missing_inputs": missing,
        "input_errors": errors,
        "source_mode": normalize_scalar(source_mode, "UNKNOWN_SOURCE_MODE"),
        "data_visibility": normalize_scalar(data_visibility, "UNKNOWN_VISIBILITY"),
        "confidence_cap": normalize_scalar(confidence_cap, "NON_RENSEIGNE"),
        "technical_status": "DEGRADED" if missing or errors else "OK",
    }


def build_sections(loaded: Mapping[str, LoadedInput]) -> Dict[str, Dict[str, Any]]:
    payloads = [item.payload for item in loaded.values() if item.payload is not None]
    sq = source_quality_summary(loaded)

    b9_sees = first_by_key(payloads, [
        "ce_que_b9_voit", "what_b9_sees_fr", "b9_sees_fr", "headline_fr", "live_brief_fr",
        "summary_fr", "reading_fr", "lecture_fr",
    ])
    scene_state = first_by_key(payloads, ["scene_state", "etat_de_scene", "scene_role", "session_chapter", "chapter"])
    transition = first_by_key(payloads, ["transition", "transition_fr", "scene_transition", "memory_shift_fr"])
    active_zone = first_by_key(payloads, ["zone_active", "active_zone", "zone", "zone_fr", "price_zone"])
    terrain_node = first_by_key(payloads, ["node_terrain", "terrain_node", "node", "temporal_node", "node_state"])
    price_verdict = first_by_key(payloads, ["verdict_prix", "price_verdict", "price_confirmation", "price_judgement", "retest_role_fr"])
    b6_memory = first_by_key(payloads, ["memoire_b6_proche", "b6", "nearest_memory", "closest_memory", "historical_context"])
    similarities = collect_by_key(payloads, ["similarities", "similarites", "similarity", "similarite"], limit=8)
    differences = collect_by_key(payloads, ["differences", "differences_fr", "difference"], limit=8)
    tech_traps = collect_by_key(payloads, ["technical_traps", "pieges_techniques", "technical_risks", "risques_techniques", "limits", "limitations"], limit=10)
    watch_next = collect_by_key(payloads, ["watch_next", "surveiller", "next_watch", "watch_condition", "next_focus"], limit=8)
    cannot_conclude = collect_by_key(payloads, ["cannot_conclude", "ne_peut_pas_conclure", "unknown", "honest_unknown", "not_concluded"], limit=8)

    if not tech_traps:
        tech_traps = [
            "Risque de lecture partielle si une entrée B9 manque ou si la source quality est dégradée.",
            "Risque de surinterprétation si un proxy M1 est lu comme footprint raw tick.",
        ]
    if sq["missing_inputs"]:
        cannot_conclude.append("Lecture complète impossible : entrées manquantes = " + ", ".join(sq["missing_inputs"]))
    if not cannot_conclude:
        cannot_conclude = [
            "B9 ne conclut pas une décision trader.",
            "B9 ne conclut pas une probabilité de succès.",
            "B9 ne conclut pas une direction exploitable seule sans lecture de scène et source quality.",
        ]

    sections: Dict[str, Dict[str, Any]] = {
        "ce_que_b9_voit": {
            "title": SECTION_TITLES["ce_que_b9_voit"],
            "body_fr": normalize_scalar(b9_sees, "B9 voit une scène locale à afficher, mais le résumé source n’est pas renseigné."),
            "evidence": as_text_list(collect_by_key(payloads, ["proof_summary_fr", "evidence", "preuves", "reason_fr"], limit=5), "Aucune preuve source structurée détectée."),
        },
        "etat_de_scene": {
            "title": SECTION_TITLES["etat_de_scene"],
            "body_fr": normalize_scalar(scene_state, "État de scène non renseigné par les sources B9."),
            "fields": {
                "scene_id": normalize_scalar(first_by_key(payloads, ["scene_id"]), "NON_RENSEIGNE"),
                "scene_role": normalize_scalar(first_by_key(payloads, ["scene_role"]), "NON_RENSEIGNE"),
                "session_chapter": normalize_scalar(first_by_key(payloads, ["session_chapter"]), "NON_RENSEIGNE"),
            },
        },
        "transition": {
            "title": SECTION_TITLES["transition"],
            "body_fr": normalize_scalar(transition, "Transition non qualifiée : garder en lecture partielle."),
        },
        "zone_active": {
            "title": SECTION_TITLES["zone_active"],
            "body_fr": normalize_scalar(active_zone, "Zone active non renseignée : ne pas afficher comme niveau validé."),
            "fields": {
                "zone_low": normalize_scalar(first_by_key(payloads, ["zone_low", "low", "zone_min"]), "NON_RENSEIGNE"),
                "zone_high": normalize_scalar(first_by_key(payloads, ["zone_high", "high", "zone_max"]), "NON_RENSEIGNE"),
                "zone_center": normalize_scalar(first_by_key(payloads, ["zone_center", "center", "centre"]), "NON_RENSEIGNE"),
            },
        },
        "node_terrain": {
            "title": SECTION_TITLES["node_terrain"],
            "body_fr": normalize_scalar(terrain_node, "Node terrain non renseigné."),
        },
        "verdict_prix": {
            "title": SECTION_TITLES["verdict_prix"],
            "body_fr": normalize_scalar(price_verdict, "Verdict prix non renseigné : afficher PENDING / NON_JUGE."),
        },
        "memoire_b6_proche": {
            "title": SECTION_TITLES["memoire_b6_proche"],
            "body_fr": normalize_scalar(b6_memory, "Aucune mémoire B6 proche structurée trouvée."),
        },
        "similarites": {
            "title": SECTION_TITLES["similarites"],
            "items": as_text_list(similarities, "Similarités non renseignées."),
        },
        "differences": {
            "title": SECTION_TITLES["differences"],
            "items": as_text_list(differences, "Différences non renseignées."),
        },
        "pieges_techniques": {
            "title": SECTION_TITLES["pieges_techniques"],
            "items": as_text_list(tech_traps, "Aucun piège technique renseigné."),
        },
        "source_quality": {
            "title": SECTION_TITLES["source_quality"],
            "body_fr": f"Mode source={sq['source_mode']} | visibilité={sq['data_visibility']} | cap={sq['confidence_cap']} | statut={sq['technical_status']}",
            "inputs": sq["rows"],
            "missing_inputs": sq["missing_inputs"],
            "input_errors": sq["input_errors"],
        },
        "ce_qu_il_faut_surveiller_ensuite": {
            "title": SECTION_TITLES["ce_qu_il_faut_surveiller_ensuite"],
            "items": as_text_list(watch_next, "Surveiller la réaction prix, le retest, la migration de mémoire et la qualité source."),
        },
        "ce_que_b9_ne_peut_pas_conclure": {
            "title": SECTION_TITLES["ce_que_b9_ne_peut_pas_conclure"],
            "items": as_text_list(cannot_conclude, "B9 ne décide pas."),
        },
    }
    return sanitize_text(sections)


def build_read_model(repo: Path) -> Dict[str, Any]:
    loaded = load_inputs(repo)
    sections = build_sections(loaded)
    sq = source_quality_summary(loaded)
    read_model = {
        "version": VERSION,
        "artifact": "B9_REALITY_BOARD_READ_MODEL_V0",
        "generated_at_utc": utc_now_iso(),
        "read_only": True,
        "dashboard_live_binding": False,
        "telegram": False,
        "databases_written": [],
        "decision_policy": {
            "no_buy_sell": True,
            "no_success_probability": True,
            "no_decision_button": True,
            "dashboard_displays_only": True,
            "trader_decides": True,
        },
        "input_sources": sq["rows"],
        "source_quality": {
            "source_mode": sq["source_mode"],
            "data_visibility": sq["data_visibility"],
            "confidence_cap": sq["confidence_cap"],
            "technical_status": sq["technical_status"],
            "missing_inputs": sq["missing_inputs"],
            "input_errors": sq["input_errors"],
        },
        "sections_order": SECTION_ORDER,
        "sections": sections,
    }
    return sanitize_text(read_model)


def build_scene_panel_candidate(read_model: Mapping[str, Any]) -> Dict[str, Any]:
    sections = read_model.get("sections", {})
    display_blocks: List[Dict[str, Any]] = []
    for key in SECTION_ORDER:
        section = sections.get(key, {}) if isinstance(sections, Mapping) else {}
        title = section.get("title", SECTION_TITLES.get(key, key)) if isinstance(section, Mapping) else SECTION_TITLES.get(key, key)
        body = section.get("body_fr") if isinstance(section, Mapping) else None
        items = section.get("items") if isinstance(section, Mapping) else None
        fields = section.get("fields") if isinstance(section, Mapping) else None
        severity = "INFO"
        if key in {"pieges_techniques", "source_quality", "ce_que_b9_ne_peut_pas_conclure"}:
            severity = "TECHNICAL"
        elif key in {"verdict_prix", "transition", "ce_qu_il_faut_surveiller_ensuite"}:
            severity = "WATCH"
        display_blocks.append({
            "key": key,
            "title_fr": title,
            "severity": severity,
            "body_fr": body,
            "items": items,
            "fields": fields,
            "display_contract": "TEXT_ONLY_NO_DECISION_BUTTON",
        })
    return sanitize_text({
        "version": VERSION,
        "artifact": "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V0",
        "generated_at_utc": read_model.get("generated_at_utc", utc_now_iso()),
        "candidate_only": True,
        "dashboard_live_binding": False,
        "panel_role_fr": "Surface candidate de lecture B9. Affiche le film local, ne décide pas.",
        "forbidden_ui": ["BUY_SELL_BUTTON", "SUCCESS_PROBABILITY", "AUTO_DECISION", "TELEGRAM_SEND"],
        "display_blocks": display_blocks,
    })


def md_escape(text: Any) -> str:
    return str(text).replace("\r\n", "\n").replace("\r", "\n")


def render_section_md(key: str, section: Mapping[str, Any]) -> str:
    title = section.get("title", SECTION_TITLES.get(key, key))
    lines = [f"## {title}", ""]
    body = section.get("body_fr")
    if body:
        lines.append(md_escape(body))
        lines.append("")
    fields = section.get("fields")
    if isinstance(fields, Mapping) and fields:
        for f_key, f_val in fields.items():
            lines.append(f"- **{f_key}** : {md_escape(f_val)}")
        lines.append("")
    evidence = section.get("evidence")
    if isinstance(evidence, list) and evidence:
        lines.append("**Preuves / indices source**")
        for item in evidence:
            lines.append(f"- {md_escape(item)}")
        lines.append("")
    items = section.get("items")
    if isinstance(items, list) and items:
        for item in items:
            lines.append(f"- {md_escape(item)}")
        lines.append("")
    if key == "source_quality":
        inputs = section.get("inputs", [])
        if isinstance(inputs, list) and inputs:
            lines.append("| Entrée | Statut | Chemin | SHA |")
            lines.append("|---|---|---|---|")
            for row in inputs:
                if isinstance(row, Mapping):
                    lines.append(
                        f"| `{row.get('name')}` | `{row.get('status')}` | `{row.get('path')}` | `{row.get('sha256_16')}` |"
                    )
            lines.append("")
    return "\n".join(lines)


def render_read_model_md(read_model: Mapping[str, Any]) -> str:
    lines = [
        "# B9 Reality Board Read Model V0",
        "",
        f"**Version :** `{read_model.get('version')}`",
        f"**Généré UTC :** `{read_model.get('generated_at_utc')}`",
        "",
        "## Contrat",
        "",
        "```text",
        "Read-only.",
        "Aucun dashboard live branché.",
        "Aucune écriture powerflow.db / tick_archive.db.",
        "Aucun Telegram.",
        "Aucun BUY/SELL.",
        "Aucune probabilité de succès.",
        "Aucun bouton décision.",
        "Le dashboard affiche, il ne décide pas.",
        "```",
        "",
    ]
    sections = read_model.get("sections", {})
    for key in read_model.get("sections_order", SECTION_ORDER):
        section = sections.get(key, {}) if isinstance(sections, Mapping) else {}
        if isinstance(section, Mapping):
            lines.append(render_section_md(key, section))
    return sanitize_rendered_markdown("\n".join(lines).rstrip() + "\n")


def render_panel_md(panel: Mapping[str, Any]) -> str:
    lines = [
        "# B9 Reality Board Scene Panel Candidate V0",
        "",
        f"**Version :** `{panel.get('version')}`",
        f"**Généré UTC :** `{panel.get('generated_at_utc')}`",
        "",
        "```text",
        "Panel candidat uniquement.",
        "Ne pas brancher directement au cockpit live sans validation architecte.",
        "Surface texte uniquement : aucun bouton décision, aucun Telegram.",
        "```",
        "",
    ]
    for block in panel.get("display_blocks", []):
        if not isinstance(block, Mapping):
            continue
        lines.append(f"## {block.get('title_fr')}")
        lines.append("")
        lines.append(f"**Sévérité affichage :** `{block.get('severity')}`")
        lines.append("")
        body = block.get("body_fr")
        if body:
            lines.append(md_escape(body))
            lines.append("")
        fields = block.get("fields")
        if isinstance(fields, Mapping) and fields:
            for f_key, f_val in fields.items():
                lines.append(f"- **{f_key}** : {md_escape(f_val)}")
            lines.append("")
        items = block.get("items")
        if isinstance(items, list) and items:
            for item in items:
                lines.append(f"- {md_escape(item)}")
            lines.append("")
    return sanitize_rendered_markdown("\n".join(lines).rstrip() + "\n")


def sanitize_rendered_markdown(text: str) -> str:
    cleaned = sanitize_text(text)
    assert isinstance(cleaned, str)
    return cleaned


def render_integration_report(read_model: Mapping[str, Any], panel: Mapping[str, Any]) -> str:
    sq = read_model.get("source_quality", {})
    lines = [
        "# Rapport d’intégration dashboard candidat — T0160/T0161",
        "",
        "## Résumé mission",
        "",
        "Création d’un read model B9 et d’un panel candidat pour préparer l’affichage Reality Board sans modifier le cockpit live.",
        "",
        "## Artefacts générés",
        "",
        "```text",
        "outputs/b9_reality_board_read_model_v0/B9_REALITY_BOARD_READ_MODEL_V0.json",
        "outputs/b9_reality_board_read_model_v0/B9_REALITY_BOARD_READ_MODEL_V0.md",
        "outputs/b9_reality_board_scene_panel_candidate_v0/B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V0.json",
        "outputs/b9_reality_board_scene_panel_candidate_v0/B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V0.md",
        "docs/Reports/T0160_T0161_B9_REALITY_BOARD_DASHBOARD_CANDIDATE_INTEGRATION.md",
        "```",
        "",
        "## Contrat respecté",
        "",
        "- Read-only.",
        "- Aucun dashboard live modifié.",
        "- Aucune écriture DB.",
        "- Aucun Telegram.",
        "- Aucun BUY/SELL.",
        "- Aucune probabilité de succès.",
        "- Aucun bouton décision.",
        "",
        "## Source quality détectée",
        "",
        f"- Source mode : `{sq.get('source_mode')}`",
        f"- Data visibility : `{sq.get('data_visibility')}`",
        f"- Confidence cap : `{sq.get('confidence_cap')}`",
        f"- Statut technique : `{sq.get('technical_status')}`",
        "",
        "## Entrées",
        "",
        "| Entrée | Statut | Chemin | SHA |",
        "|---|---|---|---|",
    ]
    for row in read_model.get("input_sources", []):
        if isinstance(row, Mapping):
            lines.append(f"| `{row.get('name')}` | `{row.get('status')}` | `{row.get('path')}` | `{row.get('sha256_16')}` |")
    lines.extend([
        "",
        "## Limites / blockers",
        "",
        "- Le panel est candidat : il ne doit pas être branché au cockpit live sans validation architecte.",
        "- Si une entrée est manquante, le read model reste utilisable mais doit afficher `READING_PARTIAL` / source dégradée.",
        "- Les textes sont neutralisés si une source injecte du vocabulaire décisionnel.",
        "",
        "## Prochain geste architecte",
        "",
        "Valider le contrat d’affichage, puis décider si le cockpit peut lire ce read model comme source externe sans importer de logique B9.",
    ])
    return sanitize_rendered_markdown("\n".join(lines).rstrip() + "\n")


def write_json(path: Path, data: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def generate_artifacts(repo: Path) -> Dict[str, Path]:
    repo = repo.resolve()
    read_model = build_read_model(repo)
    panel = build_scene_panel_candidate(read_model)

    read_json = repo / READ_MODEL_OUTPUT_DIR / "B9_REALITY_BOARD_READ_MODEL_V0.json"
    read_md = repo / READ_MODEL_OUTPUT_DIR / "B9_REALITY_BOARD_READ_MODEL_V0.md"
    panel_json = repo / PANEL_OUTPUT_DIR / "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V0.json"
    panel_md = repo / PANEL_OUTPUT_DIR / "B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V0.md"
    report_md = repo / REPORT_OUTPUT_PATH

    write_json(read_json, read_model)
    write_text(read_md, render_read_model_md(read_model))
    write_json(panel_json, panel)
    write_text(panel_md, render_panel_md(panel))
    write_text(report_md, render_integration_report(read_model, panel))

    return {
        "read_model_json": read_json,
        "read_model_md": read_md,
        "panel_json": panel_json,
        "panel_md": panel_md,
        "integration_report_md": report_md,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Generate B9 Reality Board read model and scene panel candidate V0.")
    parser.add_argument("--repo", default=".", help="Path to PowerFlow core repo directory.")
    parser.add_argument("--strict-inputs", action="store_true", help="Fail if required B9 source JSON files are missing.")
    args = parser.parse_args(argv)

    repo = Path(args.repo).resolve()
    loaded = load_inputs(repo)
    required = ["integration_candidate", "trader_attention_packet", "live_brief", "latest_scene_candidate"]
    missing_required = [name for name in required if not loaded[name].exists]
    if args.strict_inputs and missing_required:
        print("[FAIL] Required B9 inputs missing: " + ", ".join(missing_required))
        return 2

    artifacts = generate_artifacts(repo)
    print("[PASS] B9 Reality Board read model generated")
    for name, path in artifacts.items():
        try:
            rel = path.relative_to(repo)
        except ValueError:
            rel = path
        print(f"[ARTIFACT] {name}: {rel}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
