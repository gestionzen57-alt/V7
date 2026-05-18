
from __future__ import annotations

import csv
import json
import re
import zipfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "T0171_B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0"

# Output-facing forbidden wording only. Source guards may contain technical terms.
FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.IGNORECASE),
    re.compile(r"\bSELL\b", re.IGNORECASE),
    re.compile(r"\bachat\b", re.IGNORECASE),
    re.compile(r"\bvente\b", re.IGNORECASE),
    re.compile(r"probabilit", re.IGNORECASE),
    re.compile(r"taux de r", re.IGNORECASE),
]

DEFAULT_RELATIVE_INPUTS = {
    "freshness_guard": "outputs/b9_live_data_freshness_guard_v0/B9_LIVE_DATA_FRESHNESS_GUARD_V0.json",
    "latest_scene_candidate": "outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json",
    "candidate_queue": "outputs/b9_live_scene_candidate_queue_v0/B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json",
    "auto_realignment": "outputs/b9_b6_auto_realignment_v0/B9_B6_AUTO_REALIGNMENT_V0.json",
    "live_brief_once": "outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json",
    "attention_packet": "outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json",
    "reality_board_payload": "outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
    "surface_adapter": "outputs/b9_reality_board_surface_adapter_candidate_v0/B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json",
    "telegram_gate": "outputs/b9_telegram_fr_gate_candidate_v0/B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json",
    "telegram_manual_approval": "outputs/b9_telegram_manual_approval_candidate_v0/B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0.json",
    "french_display_contract": "outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json",
}

CRITICAL_STEPS = [
    "freshness_guard",
    "latest_scene_candidate",
    "auto_realignment",
    "live_brief_once",
    "attention_packet",
    "reality_board_payload",
    "telegram_gate",
]

STATE_KEYS = [
    "guard_state", "queue_state", "alignment_state", "brief_state", "packet_state",
    "payload_state", "surface_state", "gate_state", "approval_state", "contract_state",
]

BLOCKING_PREFIXES = ("BLOCKED",)
REVIEW_MARKERS = ("REVIEW", "PARTIAL", "LIMITED", "STALE", "UNQUALIFIED", "MISSING")
READY_MARKERS = ("READY", "PASS", "LIVE_FRESH")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_json(path: Path) -> Tuple[Optional[Dict[str, Any]], str]:
    if not path.exists():
        return None, "MISSING"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data, "OK"
        return {"_root": data}, "OK_NON_OBJECT_ROOT"
    except Exception as exc:  # pragma: no cover - defensive for runtime files
        return {"_error": str(exc)}, "INVALID_JSON"


def get_nested_any(data: Dict[str, Any], keys: List[str], default: Any = "") -> Any:
    for key in keys:
        cur: Any = data
        ok = True
        for part in key.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                ok = False
                break
        if ok and cur not in (None, ""):
            return cur
    return default


def find_state(data: Dict[str, Any]) -> str:
    for key in STATE_KEYS:
        value = get_nested_any(data, [key, f"summary.{key}", f"result.{key}"])
        if value:
            return str(value)
    # Common wrappers
    for key in ["state", "status", "runtime_state"]:
        value = get_nested_any(data, [key, f"summary.{key}"])
        if value:
            return str(value)
    return "STATE_UNKNOWN"


def classify_step(name: str, status: str, state: str, data: Optional[Dict[str, Any]]) -> str:
    if status == "MISSING":
        return "MISSING"
    if status != "OK" and status != "OK_NON_OBJECT_ROOT":
        return "INVALID"
    upper = state.upper()
    if upper.startswith(BLOCKING_PREFIXES):
        return "BLOCKED"
    if name == "freshness_guard" and any(x in upper for x in ["DB_EMPTY", "DB_MISSING", "TABLE_MISSING", "RAW_TEXTURE_MISSING", "SOURCE_LIVE_UNQUALIFIED", "STALE"]):
        return "REVIEW"
    if any(x in upper for x in REVIEW_MARKERS):
        return "REVIEW"
    if any(x in upper for x in READY_MARKERS):
        return "READY"
    # Treat present but unknown as review, not ready.
    return "REVIEW"


def extract_candidate_id(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return ""
    return str(get_nested_any(data, [
        "candidate_id", "latest_candidate_id", "scene.candidate_id", "summary.candidate_id",
        "payload.candidate_id", "attention_packet.candidate_id", "telegram_candidate.candidate_id"
    ], ""))


def extract_match_count(data: Optional[Dict[str, Any]]) -> int:
    if not data:
        return 0
    raw = get_nested_any(data, ["match_count", "matches", "summary.match_count", "memory.match_count"], None)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    for key in ["similar_films", "matches", "memory_matches", "top_matches"]:
        value = data.get(key)
        if isinstance(value, list):
            return len(value)
    return 0


def extract_top_match(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return ""
    top = get_nested_any(data, ["top_match_film_id", "memory.top_match_film_id", "summary.top_match_film_id"], "")
    if top:
        return str(top)
    for key in ["similar_films", "matches", "memory_matches", "top_matches"]:
        value = data.get(key)
        if isinstance(value, list) and value:
            first = value[0]
            if isinstance(first, dict):
                return str(first.get("film_id") or first.get("id") or first.get("card_id") or "")
    return ""


def scan_forbidden_text(text: str) -> List[str]:
    hits: List[str] = []
    for pat in FORBIDDEN_PATTERNS:
        if pat.search(text):
            hits.append(pat.pattern)
    return hits


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def collect_forbidden_hits(outputs: Dict[str, Any]) -> List[str]:
    # Scan only user-facing strings in the dry-run outputs, not source code.
    text_parts: List[str] = []
    for key in ["orchestrator_reading_fr", "technical_limits", "operator_next_steps", "chain_cards"]:
        value = outputs.get(key)
        text_parts.append(json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value)
    return sorted(set(scan_forbidden_text("\n".join(text_parts))))


def build_chain_cards(inputs: Dict[str, Tuple[Path, Optional[Dict[str, Any]], str]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for name, (path, data, status) in inputs.items():
        state = find_state(data or {}) if data else "MISSING"
        step_status = classify_step(name, status, state, data)
        cards.append({
            "step": name,
            "path": str(path),
            "file_status": status,
            "state": state,
            "step_status": step_status,
            "candidate_id": extract_candidate_id(data),
            "match_count": extract_match_count(data),
            "top_match_film_id": extract_top_match(data),
            "technical_note_fr": technical_note_for_step(name, step_status, state),
        })
    return cards


def technical_note_for_step(name: str, status: str, state: str) -> str:
    if status == "MISSING":
        return "Entrée absente : la chaîne dry-run doit marquer cette étape comme incomplète."
    if status == "INVALID":
        return "Entrée invalide : JSON non lisible ou structure inattendue."
    upper = state.upper()
    if upper.startswith("BLOCKED"):
        return "Étape bloquée : ne pas masquer le blocage dans les surfaces d'affichage."
    if status == "REVIEW":
        return "Étape lisible avec limite technique : afficher en revue, pas comme état final robuste."
    return "Étape disponible pour assemblage dry-run."


def determine_orchestrator_state(cards: List[Dict[str, Any]]) -> str:
    critical = [c for c in cards if c["step"] in CRITICAL_STEPS]
    if any(c["step_status"] == "INVALID" for c in critical):
        return "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_INVALID_INPUT"
    if any(c["step_status"] == "MISSING" for c in critical):
        return "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS"
    if any(c["step_status"] == "BLOCKED" for c in critical):
        return "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_UPSTREAM_STATE"
    if any(c["step_status"] == "REVIEW" for c in critical):
        return "B9_LIVE_CHAIN_DRY_RUN_REVIEW_TECHNICAL_RISK"
    return "B9_LIVE_CHAIN_DRY_RUN_READY"


def build_markdown(summary: Dict[str, Any], cards: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("# B9 Live Chain Orchestrator Dry Run V0")
    lines.append("")
    lines.append("## Verdict")
    lines.append(f"- État : `{summary['orchestrator_state']}`")
    lines.append(f"- Candidat : `{summary.get('candidate_id') or 'non identifié'}`")
    lines.append(f"- Film B6 principal : `{summary.get('top_match_film_id') or 'non disponible'}`")
    lines.append(f"- Matches mémoire : `{summary.get('match_count', 0)}`")
    lines.append("")
    lines.append("## Lecture")
    lines.append(summary["orchestrator_reading_fr"])
    lines.append("")
    lines.append("## Chaîne")
    lines.append("| Étape | Statut | État | Candidat | Matches | Note |")
    lines.append("|---|---:|---|---|---:|---|")
    for c in cards:
        lines.append(f"| {c['step']} | {c['step_status']} | `{c['state']}` | `{c.get('candidate_id','')}` | {c.get('match_count',0)} | {c['technical_note_fr']} |")
    lines.append("")
    lines.append("## Limites techniques")
    for item in summary["technical_limits"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Prochain geste opérateur")
    for item in summary["operator_next_steps"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Doctrine")
    lines.append("B9 lit la scène. B6 compare les films. L'orchestrateur dry-run vérifie la chaîne ; il ne déclenche aucune action.")
    lines.append("")
    return "\n".join(lines)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["step", "path", "file_status", "state", "step_status", "candidate_id", "match_count", "top_match_film_id", "technical_note_fr"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def make_zip(output_dir: Path, files: List[Path], zip_name: str) -> str:
    zip_path = output_dir / zip_name
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, f.name)
    return str(zip_path)


def run(
    core_root: Path,
    output_dir: Path,
    input_overrides: Optional[Dict[str, str]] = None,
    strict: bool = False,
) -> Dict[str, Any]:
    core_root = Path(core_root)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    input_overrides = input_overrides or {}

    resolved: Dict[str, Tuple[Path, Optional[Dict[str, Any]], str]] = {}
    for name, rel in DEFAULT_RELATIVE_INPUTS.items():
        path = Path(input_overrides.get(name, rel))
        if not path.is_absolute():
            path = core_root / path
        data, status = read_json(path)
        resolved[name] = (path, data, status)

    cards = build_chain_cards(resolved)
    orchestrator_state = determine_orchestrator_state(cards)

    candidate_id = ""
    for c in cards:
        if c.get("candidate_id"):
            candidate_id = c["candidate_id"]
            break
    top_match = ""
    match_count = 0
    for c in cards:
        if c.get("match_count", 0) > match_count:
            match_count = int(c.get("match_count", 0))
            top_match = c.get("top_match_film_id", "")

    missing = [c["step"] for c in cards if c["step_status"] == "MISSING"]
    blocked = [c["step"] for c in cards if c["step_status"] == "BLOCKED"]
    review = [c["step"] for c in cards if c["step_status"] == "REVIEW"]

    if orchestrator_state == "B9_LIVE_CHAIN_DRY_RUN_READY":
        reading = "Chaîne live dry-run prête : les étapes critiques sont présentes et lisibles."
    elif orchestrator_state == "B9_LIVE_CHAIN_DRY_RUN_REVIEW_TECHNICAL_RISK":
        reading = "Chaîne live dry-run exploitable en revue : au moins une étape critique porte une limite technique visible."
    elif orchestrator_state == "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS":
        reading = "Chaîne live dry-run bloquée : une ou plusieurs entrées critiques manquent."
    else:
        reading = "Chaîne live dry-run bloquée : un état amont empêche l'assemblage propre."

    technical_limits = [
        "Read-only : aucune base ni surface live n'est modifiée.",
        "Dry-run : aucune transmission externe n'est déclenchée.",
        "La mémoire comparable reste une comparaison technique, pas une répétition certaine.",
    ]
    if missing:
        technical_limits.append("Entrées manquantes : " + ", ".join(missing))
    if blocked:
        technical_limits.append("Étapes bloquées : " + ", ".join(blocked))
    if review:
        technical_limits.append("Étapes en revue technique : " + ", ".join(review))

    next_steps = []
    if missing:
        next_steps.append("Générer les sorties manquantes avant de présenter la chaîne comme complète.")
    if "freshness_guard" in review or "freshness_guard" in missing:
        next_steps.append("Vérifier la fraîcheur source avant surface dashboard ou preview message.")
    if "auto_realignment" in missing:
        next_steps.append("Relancer l'alignement B9 vers B6 pour garantir que la mémoire correspond au candidat courant.")
    if not next_steps:
        next_steps.append("Inspecter le Markdown dry-run puis décider du prochain niveau d'intégration candidat.")

    summary: Dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "orchestrator_state": orchestrator_state,
        "candidate_id": candidate_id,
        "match_count": match_count,
        "top_match_film_id": top_match,
        "missing_steps": missing,
        "blocked_steps": blocked,
        "review_steps": review,
        "chain_cards": cards,
        "orchestrator_reading_fr": reading,
        "technical_limits": technical_limits,
        "operator_next_steps": next_steps,
        "dry_run_guard": True,
        "no_db_write_guard": True,
        "no_dashboard_live_guard": True,
        "no_external_transmission_guard": True,
        "no_execution_decision_guard": True,
    }
    summary["forbidden_language_hits"] = collect_forbidden_hits(summary)

    json_path = output_dir / "B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0.json"
    md_path = output_dir / "B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0.md"
    csv_path = output_dir / "B9_LIVE_CHAIN_STEPS_V0.csv"
    risks_path = output_dir / "B9_LIVE_CHAIN_TECHNICAL_RISKS_V0.csv"
    manifest_path = output_dir / "B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_MANIFEST.json"

    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(summary, cards), encoding="utf-8")
    write_csv(csv_path, cards)
    write_csv(risks_path, [c for c in cards if c["step_status"] in {"MISSING", "INVALID", "BLOCKED", "REVIEW"}])

    manifest = {
        "version": VERSION,
        "outputs": [str(json_path), str(md_path), str(csv_path), str(risks_path)],
        "read_only": True,
        "dry_run": True,
        "forbidden_language_hits": summary["forbidden_language_hits"],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_path = make_zip(output_dir, [json_path, md_path, csv_path, risks_path, manifest_path], "B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0.zip")
    summary["zip"] = zip_path
    # Rewrite with zip path included
    json_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if strict and orchestrator_state.startswith("B9_LIVE_CHAIN_DRY_RUN_BLOCKED"):
        raise SystemExit(2)
    if summary["forbidden_language_hits"]:
        raise SystemExit(3)
    return summary
