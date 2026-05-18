from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VERSION = "T0176_B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0"
DEFAULT_LOCK_DIR = Path("outputs") / "t0175_b9_global_chain_contract_lock_v0"
DEFAULT_OUTPUT_DIR = Path("outputs") / "t0176_b9_chain_degraded_dashboard_candidate_v0"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bENTRY\b",
    r"\bSTOP\b",
    r"\bTARGET\b",
    r"\bTAKE PROFIT\b",
    r"\bSUCCESS RATE\b",
    r"\bWIN RATE\b",
]

SECTION_TITLES = [
    "Etat de chaine B9",
    "Lecture operationnelle degradee",
    "Inputs manquants",
    "Cartes techniques par brique absente",
    "Commandes de regeneration",
    "Ce que B9 voit deja",
    "Ce que B9 ne peut pas encore completer",
    "Source quality",
]


@dataclass
class LoadedInputs:
    lock_json_path: Path
    missing_csv_path: Path
    source_matrix_csv_path: Path
    manifest_json_path: Path
    lock_payload: Dict[str, Any]
    missing_rows: List[Dict[str, str]]
    source_rows: List[Dict[str, str]]
    load_errors: List[str]


def _read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root is not an object: {path}")
    return payload


def _read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return [dict(row) for row in csv.DictReader(fh)]


def _str(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _first_present(row: Dict[str, str], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        if key in row and _str(row.get(key)):
            return _str(row.get(key))
    return default


def _normalize_rel_path(text: str) -> str:
    return text.replace("\\", "/").strip()


def _classify_brick(missing_ref: str) -> Dict[str, str]:
    lower = missing_ref.lower().replace("\\", "/")

    if "t0169" in lower or "surface_adapter" in lower or "reality_board_surface_adapter" in lower:
        return {
            "brick": "T0169 surface adapter",
            "role": "Adapter le read model B9 vers une surface dashboard candidate, sans brancher le live.",
            "impact": "Le dashboard ne peut pas verifier la compatibilite finale de surface.",
            "regen": "python tools\\build_t0169_b9_reality_board_surface_adapter_candidate.py sample",
        }
    if "reality_board_read_model" in lower:
        return {
            "brick": "Reality Board read model",
            "role": "Normaliser les lectures B9 en champs affichables et tracables.",
            "impact": "Le panel ne peut pas garantir l'ordre des sections ni l'origine des champs.",
            "regen": "python run_b9_reality_board_read_model_v01_once.py --repo .",
        }
    if "scene_panel" in lower:
        return {
            "brick": "Scene panel candidate",
            "role": "Preparer la carte de scene affichable par le dashboard candidat.",
            "impact": "La surface degradee peut informer, mais pas montrer le panel final attendu.",
            "regen": "python run_b9_reality_board_read_model_v01_once.py --repo .",
        }
    if "trader_attention_packet" in lower:
        return {
            "brick": "Trader attention packet",
            "role": "Resumer ce qui doit reveiller l'attention trader sans decision.",
            "impact": "La lecture operationnelle est incomplete et doit rester degradee.",
            "regen": "Relancer la mission T0155 / builder Trader Attention Packet.",
        }
    if "live_brief" in lower:
        return {
            "brick": "Live brief",
            "role": "Fournir le brief court B9 de la scene courante.",
            "impact": "Le dashboard ne peut pas afficher une synthese live complete.",
            "regen": "Relancer la mission T0156 / builder Live Brief.",
        }
    if "latest_scene_candidate" in lower or "scene_candidate_queue" in lower:
        return {
            "brick": "Latest scene candidate queue",
            "role": "Exposer la derniere scene candidate sans modifier le live.",
            "impact": "La chaine ne sait pas quelle scene courante utiliser comme reference.",
            "regen": "Relancer le builder de queue B9 live scene candidate.",
        }
    if "integration_candidate" in lower:
        return {
            "brick": "Reality board integration candidate",
            "role": "Agreger les pieces B9 en candidat d'integration dashboard.",
            "impact": "La chaine ne peut pas prouver la coherence inter-briques.",
            "regen": "Relancer la mission T0148 / integration candidate.",
        }
    if "french_event_display_contract" in lower:
        return {
            "brick": "French event display contract",
            "role": "Garantir un affichage francais trader lisible des evenements.",
            "impact": "Le dashboard peut afficher une lecture moins propre en francais trader.",
            "regen": "Relancer le builder B9 French Event Display Contract.",
        }
    if "b6" in lower or "memory" in lower or "similarity" in lower:
        return {
            "brick": "B6 memory / similarity",
            "role": "Donner la memoire de film proche, similarites et differences.",
            "impact": "B9 voit la scene locale mais ne peut pas ancrer la memoire proche.",
            "regen": "Relancer les builders B6 memory / similarity requis par le lock.",
        }
    return {
        "brick": "Brique B9 non classee",
        "role": "Input requis par le contrat global T0175.",
        "impact": "La chaine reste partielle tant que cet input manque.",
        "regen": "Lire le CSV T0175 missing inputs et relancer le builder proprietaire de cette sortie.",
    }


def _row_missing_ref(row: Dict[str, str]) -> str:
    return _first_present(
        row,
        [
            "path",
            "relative_path",
            "file",
            "expected_file",
            "input_path",
            "source_path",
            "name",
            "input_name",
            "artifact",
            "required_input",
        ],
        "UNKNOWN_INPUT",
    )


def _row_required(row: Dict[str, str]) -> str:
    raw = _first_present(row, ["required", "is_required", "requirement", "kind", "level"], "required")
    lower = raw.lower()
    if lower in {"true", "1", "yes", "required", "requis", "mandatory"}:
        return "required"
    if lower in {"false", "0", "no", "optional", "optionnel"}:
        return "optional"
    return raw or "required"


def _source_row_path(row: Dict[str, str]) -> str:
    return _first_present(row, ["path", "relative_path", "file", "source_path", "artifact", "name"], "UNKNOWN_SOURCE")


def _source_row_status(row: Dict[str, str]) -> str:
    return _first_present(row, ["status", "state", "exists", "present", "quality", "source_quality"], "UNKNOWN")


def load_inputs(core_root: Path, lock_dir: Optional[Path] = None) -> LoadedInputs:
    base = core_root / (lock_dir or DEFAULT_LOCK_DIR)
    lock_json = base / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json"
    missing_csv = base / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv"
    source_csv = base / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_SOURCE_MATRIX_V0.csv"
    manifest_json = base / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MANIFEST_V0.json"

    errors: List[str] = []
    payload: Dict[str, Any] = {}
    missing_rows: List[Dict[str, str]] = []
    source_rows: List[Dict[str, str]] = []

    if lock_json.exists():
        try:
            payload = _read_json(lock_json)
        except Exception as exc:  # pragma: no cover - defensive path
            errors.append(f"LOCK_JSON_ERROR: {exc}")
    else:
        errors.append(f"LOCK_JSON_MISSING: {lock_json}")

    try:
        missing_rows = _read_csv(missing_csv)
    except Exception as exc:  # pragma: no cover - defensive path
        errors.append(f"MISSING_CSV_ERROR: {exc}")

    try:
        source_rows = _read_csv(source_csv)
    except Exception as exc:  # pragma: no cover - defensive path
        errors.append(f"SOURCE_MATRIX_CSV_ERROR: {exc}")

    return LoadedInputs(
        lock_json_path=lock_json,
        missing_csv_path=missing_csv,
        source_matrix_csv_path=source_csv,
        manifest_json_path=manifest_json,
        lock_payload=payload,
        missing_rows=missing_rows,
        source_rows=source_rows,
        load_errors=errors,
    )


def build_missing_cards(missing_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    cards: List[Dict[str, str]] = []
    seen = set()
    for row in missing_rows:
        ref = _row_missing_ref(row)
        if ref in seen:
            continue
        seen.add(ref)
        cls = _classify_brick(ref)
        cards.append(
            {
                "missing_input": ref,
                "requirement": _row_required(row),
                "brick": cls["brick"],
                "technical_role": cls["role"],
                "dashboard_impact": cls["impact"],
                "regeneration_command": cls["regen"],
            }
        )
    return cards


def build_already_visible(source_rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    visible: List[Dict[str, str]] = []
    for row in source_rows:
        status = _source_row_status(row)
        low = status.lower()
        if low in {"true", "present", "exists", "ok", "ready", "available"} or "present" in low or "ok" in low:
            path = _source_row_path(row)
            cls = _classify_brick(path)
            visible.append(
                {
                    "source": path,
                    "status": status,
                    "brick": cls["brick"],
                    "what_b9_can_see": cls["role"],
                }
            )
    return visible


def determine_dashboard_state(lock_state: str, missing_required: int, load_errors: List[str], forbidden_hits: int) -> str:
    if load_errors:
        return "BLOCKED_T0175_LOCK_UNREADABLE"
    if forbidden_hits > 0:
        return "BLOCKED_FORBIDDEN_LANGUAGE"
    if lock_state == "LOCK_READY_FOR_DASHBOARD_REVIEW":
        return "READY_FULL_CHAIN_VIEW"
    if lock_state == "LOCK_PARTIAL_OPTIONAL_MISSING":
        return "DEGRADED_OPTIONAL_INPUTS_MISSING"
    if missing_required > 0 or lock_state == "LOCK_BLOCKED_MISSING_REQUIRED":
        return "DEGRADED_REQUIRED_INPUTS_MISSING"
    if lock_state:
        return "DEGRADED_CHAIN_STATE_UNKNOWN"
    return "BLOCKED_T0175_LOCK_NOT_FOUND"


def _scan_forbidden(payload: Any) -> List[Dict[str, str]]:
    text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    hits: List[Dict[str, str]] = []
    for pat in FORBIDDEN_PATTERNS:
        for match in re.finditer(pat, text, flags=re.IGNORECASE):
            start = max(match.start() - 30, 0)
            end = min(match.end() + 30, len(text))
            hits.append({"pattern": pat, "snippet": text[start:end]})
            break
    return hits


def build_contract(core_root: Path, output_dir: Path, lock_dir: Optional[Path] = None) -> Dict[str, Any]:
    inputs = load_inputs(core_root, lock_dir)
    lock = inputs.lock_payload
    lock_state = _str(lock.get("lock_state"), "LOCK_NOT_LOADED")
    missing_required = int(lock.get("required_missing_count") or 0) if lock else 0
    missing_optional = int(lock.get("optional_missing_count") or 0) if lock else 0
    source_error_count = int(lock.get("source_error_count") or 0) if lock else 0
    prior_forbidden = int(lock.get("forbidden_language_hit_count") or 0) if lock else 0

    missing_cards = build_missing_cards(inputs.missing_rows)
    if not missing_cards and missing_required:
        missing_cards.append(
            {
                "missing_input": "T0175 reported missing required inputs but missing CSV is unavailable or empty.",
                "requirement": "required",
                "brick": "T0175 missing input detail",
                "technical_role": "Detail des inputs absents.",
                "dashboard_impact": "Le dashboard peut afficher le count, mais pas les cartes par brique.",
                "regeneration_command": "Relancer T0175 puis ouvrir B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv.",
            }
        )

    already_visible = build_already_visible(inputs.source_rows)
    forbidden_hits = _scan_forbidden({"missing_cards": missing_cards, "already_visible": already_visible})
    total_forbidden = prior_forbidden + len(forbidden_hits)
    dashboard_state = determine_dashboard_state(lock_state, missing_required, inputs.load_errors, total_forbidden)

    commands = [
        {
            "label": "Relancer T0175 lock",
            "command": "python tools\\build_t0175_b9_global_chain_contract_lock.py --core-root . --output-dir outputs\\t0175_b9_global_chain_contract_lock_v0 --print-json",
        },
        {
            "label": "Relancer ce panel degrade T0176",
            "command": "python tools\\build_t0176_b9_chain_degraded_dashboard_candidate.py --core-root . --output-dir outputs\\t0176_b9_chain_degraded_dashboard_candidate_v0 --print-json",
        },
    ]
    for card in missing_cards:
        cmd = card.get("regeneration_command", "")
        if cmd and not any(item["command"] == cmd for item in commands):
            commands.append({"label": f"Regenerer {card['brick']}", "command": cmd})

    contract: Dict[str, Any] = {
        "version": VERSION,
        "core_root": str(core_root),
        "output_dir": str(output_dir),
        "source_lock": {
            "lock_json": str(inputs.lock_json_path),
            "missing_csv": str(inputs.missing_csv_path),
            "source_matrix_csv": str(inputs.source_matrix_csv_path),
            "manifest_json": str(inputs.manifest_json_path),
            "load_errors": inputs.load_errors,
        },
        "dashboard_candidate_state": dashboard_state,
        "chain_state": {
            "t0175_lock_state": lock_state,
            "required_missing_count": missing_required,
            "optional_missing_count": missing_optional,
            "source_error_count": source_error_count,
            "forbidden_language_hit_count": total_forbidden,
        },
        "sections": {
            "etat_de_chaine_b9": {
                "title": "Etat de chaine B9",
                "reading_fr": _chain_reading(dashboard_state, missing_required, missing_optional),
            },
            "lecture_operationnelle_degradee": {
                "title": "Lecture operationnelle degradee",
                "reading_fr": _degraded_reading(dashboard_state),
            },
            "inputs_manquants": missing_cards,
            "cartes_techniques_par_brique_absente": missing_cards,
            "commandes_de_regeneration": commands,
            "ce_que_b9_voit_deja": already_visible,
            "ce_que_b9_ne_peut_pas_encore_completer": [
                {
                    "missing_input": card["missing_input"],
                    "cannot_complete_fr": card["dashboard_impact"],
                }
                for card in missing_cards
            ],
            "source_quality": {
                "lock_source": "T0175 global chain contract lock",
                "source_error_count": source_error_count,
                "load_errors": inputs.load_errors,
                "source_matrix_rows": len(inputs.source_rows),
            },
        },
        "forbidden_language_hits": forbidden_hits,
        "db_touched": False,
        "dashboard_live_wired": False,
        "telegram_touched": False,
    }
    return contract


def _chain_reading(state: str, missing_required: int, missing_optional: int) -> str:
    if state == "READY_FULL_CHAIN_VIEW":
        return "La chaine B9 est complete pour revue dashboard candidate. Le live n'est pas branche."
    if state == "DEGRADED_OPTIONAL_INPUTS_MISSING":
        return f"La chaine B9 est lisible, mais {missing_optional} input(s) optionnel(s) manquent."
    if state == "DEGRADED_REQUIRED_INPUTS_MISSING":
        return f"Lecture operationnelle degradee : {missing_required} input(s) requis manquent encore."
    if state == "BLOCKED_T0175_LOCK_UNREADABLE":
        return "Le lock T0175 est absent ou illisible. Le dashboard candidat ne peut afficher qu'un diagnostic."
    if state == "BLOCKED_FORBIDDEN_LANGUAGE":
        return "Le contrat contient du langage interdit pour la surface dashboard candidate."
    return "Etat de chaine inconnu ou incomplet."


def _degraded_reading(state: str) -> str:
    if state.startswith("READY"):
        return "Affichage complet candidat possible apres revue architecte."
    if state.startswith("DEGRADED"):
        return "Le dashboard peut afficher une lecture degradee utile : ce qui manque, ce qui existe deja, et les commandes de regeneration."
    return "Le dashboard ne doit pas afficher une scene complete. Afficher uniquement le blocage technique et les prochaines actions."


def render_markdown(contract: Dict[str, Any]) -> str:
    c = contract
    chain = c["chain_state"]
    sections = c["sections"]
    lines: List[str] = []
    lines.append(f"# {VERSION}")
    lines.append("")
    lines.append("## Etat de chaine B9")
    lines.append("")
    lines.append(f"- Dashboard candidate state: `{c['dashboard_candidate_state']}`")
    lines.append(f"- T0175 lock state: `{chain['t0175_lock_state']}`")
    lines.append(f"- Inputs requis manquants: {chain['required_missing_count']}")
    lines.append(f"- Inputs optionnels manquants: {chain['optional_missing_count']}")
    lines.append(f"- Source errors: {chain['source_error_count']}")
    lines.append(f"- Forbidden language hits: {chain['forbidden_language_hit_count']}")
    lines.append("")
    lines.append(sections["etat_de_chaine_b9"]["reading_fr"])
    lines.append("")

    lines.append("## Lecture operationnelle degradee")
    lines.append("")
    lines.append(sections["lecture_operationnelle_degradee"]["reading_fr"])
    lines.append("")

    lines.append("## Inputs manquants")
    lines.append("")
    missing = sections["inputs_manquants"]
    if missing:
        lines.append("| Input | Requirement | Brique | Impact dashboard |")
        lines.append("|---|---|---|---|")
        for card in missing:
            lines.append(
                f"| `{card['missing_input']}` | {card['requirement']} | {card['brick']} | {card['dashboard_impact']} |"
            )
    else:
        lines.append("Aucun input manquant remonte par T0175.")
    lines.append("")

    lines.append("## Cartes techniques par brique absente")
    lines.append("")
    if missing:
        for idx, card in enumerate(missing, 1):
            lines.append(f"### Carte {idx} - {card['brick']}")
            lines.append("")
            lines.append(f"- Input: `{card['missing_input']}`")
            lines.append(f"- Role technique: {card['technical_role']}")
            lines.append(f"- Impact: {card['dashboard_impact']}")
            lines.append(f"- Commande: `{card['regeneration_command']}`")
            lines.append("")
    else:
        lines.append("Aucune carte absente.")
        lines.append("")

    lines.append("## Commandes de regeneration")
    lines.append("")
    for item in sections["commandes_de_regeneration"]:
        lines.append(f"- {item['label']}: `{item['command']}`")
    lines.append("")

    lines.append("## Ce que B9 voit deja")
    lines.append("")
    visible = sections["ce_que_b9_voit_deja"]
    if visible:
        lines.append("| Source | Status | Brique | Lecture disponible |")
        lines.append("|---|---|---|---|")
        for row in visible:
            lines.append(f"| `{row['source']}` | {row['status']} | {row['brick']} | {row['what_b9_can_see']} |")
    else:
        lines.append("Aucune source presente n'a ete declaree par la source matrix T0175, ou la matrix est absente.")
    lines.append("")

    lines.append("## Ce que B9 ne peut pas encore completer")
    lines.append("")
    cannot = sections["ce_que_b9_ne_peut_pas_encore_completer"]
    if cannot:
        for item in cannot:
            lines.append(f"- `{item['missing_input']}` : {item['cannot_complete_fr']}")
    else:
        lines.append("Aucune limite de completion detectee.")
    lines.append("")

    lines.append("## Source quality")
    lines.append("")
    sq = sections["source_quality"]
    lines.append(f"- Lock source: {sq['lock_source']}")
    lines.append(f"- Source matrix rows: {sq['source_matrix_rows']}")
    lines.append(f"- Load errors: {len(sq['load_errors'])}")
    lines.append("")

    lines.append("## Garde-fous")
    lines.append("")
    lines.append("- Aucune DB touchee.")
    lines.append("- Aucun cockpit live branche.")
    lines.append("- Aucun Telegram touche.")
    lines.append("- Aucun bouton decisionnel.")
    lines.append("- Le dashboard affiche, il ne decide pas.")
    lines.append("")
    return "\n".join(lines)


def write_outputs(contract: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.json"
    md_path = output_dir / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.md"
    cards_csv = output_dir / "B9_CHAIN_DEGRADED_DASHBOARD_MISSING_BRICK_CARDS_V0.csv"
    commands_csv = output_dir / "B9_CHAIN_DEGRADED_DASHBOARD_REGEN_COMMANDS_V0.csv"
    manifest_path = output_dir / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_MANIFEST_V0.json"

    json_path.write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown(contract), encoding="utf-8")

    cards = contract["sections"]["cartes_techniques_par_brique_absente"]
    with cards_csv.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = ["missing_input", "requirement", "brick", "technical_role", "dashboard_impact", "regeneration_command"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in cards:
            writer.writerow({key: row.get(key, "") for key in fieldnames})

    commands = contract["sections"]["commandes_de_regeneration"]
    with commands_csv.open("w", encoding="utf-8", newline="") as fh:
        fieldnames = ["label", "command"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in commands:
            writer.writerow(row)

    manifest = {
        "version": VERSION,
        "artifacts": {
            "candidate_json": str(json_path),
            "candidate_md": str(md_path),
            "missing_brick_cards_csv": str(cards_csv),
            "regen_commands_csv": str(commands_csv),
            "manifest_json": str(manifest_path),
        },
        "dashboard_candidate_state": contract["dashboard_candidate_state"],
        "db_touched": False,
        "dashboard_live_wired": False,
        "telegram_touched": False,
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest["artifacts"]


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build T0176 B9 chain degraded dashboard candidate V0")
    parser.add_argument("--core-root", default=".", help="Core root directory")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR), help="Output directory relative to core root or absolute")
    parser.add_argument("--lock-dir", default=str(DEFAULT_LOCK_DIR), help="T0175 lock dir relative to core root")
    parser.add_argument("--print-json", action="store_true", help="Print summary JSON")
    args = parser.parse_args(argv)

    core_root = Path(args.core_root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = core_root / output_dir
    lock_dir = Path(args.lock_dir)

    contract = build_contract(core_root, output_dir, lock_dir)
    artifacts = write_outputs(contract, output_dir)
    summary = {
        "version": VERSION,
        "core_root": str(core_root),
        "output_dir": str(output_dir),
        "dashboard_candidate_state": contract["dashboard_candidate_state"],
        "t0175_lock_state": contract["chain_state"]["t0175_lock_state"],
        "required_missing_count": contract["chain_state"]["required_missing_count"],
        "optional_missing_count": contract["chain_state"]["optional_missing_count"],
        "missing_card_count": len(contract["sections"]["cartes_techniques_par_brique_absente"]),
        "regeneration_command_count": len(contract["sections"]["commandes_de_regeneration"]),
        "forbidden_language_hit_count": contract["chain_state"]["forbidden_language_hit_count"],
        "artifacts": artifacts,
        "db_touched": False,
        "dashboard_live_wired": False,
        "telegram_touched": False,
    }
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"[PASS] {VERSION} generated")
        print(f"[STATE] {summary['dashboard_candidate_state']}")
        for key, path in artifacts.items():
            print(f"[ARTIFACT] {key}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
