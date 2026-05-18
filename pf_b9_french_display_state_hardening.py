from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import re
from typing import Any, Dict, Iterable, List, Mapping, Optional

VERSION = "T0170_B9_FRENCH_DISPLAY_STATE_HARDENING_V0"

POLICY = {
    "read_only": True,
    "db_write": False,
    "dashboard_live_mutation": False,
    "telegram_send": False,
    "execution_decision": False,
    "outcome_probability": False,
    "engine_enums_preserved": True,
    "display_french_added": True,
}

ENUM_RE = re.compile(r"\b[A-Z][A-Z0-9]+(?:_[A-Z0-9]+)+\b")

IGNORED_ENUMS = {
    "JSON",
    "CSV",
    "ZIP",
    "UTF",
    "UTC",
    "TRUE",
    "FALSE",
    "M1_BAR_PROXY",
    "TF5_BAR_PROXY",
    "RAW_LIVE_BROKER",
}

ID_PREFIXES = ("B9LSC", "B6FC", "B6Q")


@dataclass(frozen=True)
class StateDisplayFr:
    key: str
    label_fr: str
    short_fr: str
    explanation_fr: str
    attention_level: str
    integration_rule_fr: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


def _state(
    key: str,
    label_fr: str,
    short_fr: str,
    explanation_fr: str,
    attention_level: str = "INFO",
    integration_rule_fr: str = "Conserver l'enum moteur et ajouter un champ *_fr pour l'affichage.",
) -> StateDisplayFr:
    return StateDisplayFr(
        key=key,
        label_fr=label_fr,
        short_fr=short_fr,
        explanation_fr=explanation_fr,
        attention_level=attention_level,
        integration_rule_fr=integration_rule_fr,
    )


DISPLAY_STATE_FR: Dict[str, StateDisplayFr] = {
    "B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS": _state(
        "B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS",
        "Contrat chaîne live bloqué : entrées manquantes",
        "Contrat bloqué",
        "Le validateur de chaîne live ne peut pas confirmer le contrat car une ou plusieurs entrées critiques manquent.",
        "BLOCKER",
    ),
    "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS": _state(
        "B9_LIVE_CHAIN_DRY_RUN_BLOCKED_MISSING_INPUTS",
        "Chaîne live dry-run bloquée : entrées manquantes",
        "Dry-run bloqué",
        "L'orchestrateur dry-run voit la chaîne, mais certaines briques nécessaires sont absentes.",
        "BLOCKER",
    ),
    "MISSING_INPUT": _state(
        "MISSING_INPUT",
        "Entrée manquante",
        "Entrée manquante",
        "Le fichier ou champ attendu n'est pas disponible pour cette étape.",
        "BLOCKER",
    ),
    "MISSING": _state(
        "MISSING",
        "Manquant",
        "Manquant",
        "La brique ou donnée attendue n'est pas présente.",
        "BLOCKER",
    ),
    "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_REVIEW_TECHNICAL_RISK": _state(
        "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_REVIEW_TECHNICAL_RISK",
        "Approbation manuelle Telegram : revue technique requise",
        "Revue Telegram requise",
        "Le message candidat existe, mais doit rester en revue technique avant tout usage manuel.",
        "WATCH",
    ),
    "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK": _state(
        "B9_TELEGRAM_FR_GATE_CANDIDATE_REVIEW_TECHNICAL_RISK",
        "Gate Telegram FR : revue technique requise",
        "Gate FR en revue",
        "Le gate français Telegram n'est pas en erreur critique, mais demande une relecture technique.",
        "WATCH",
    ),
    "RAW_UNAVAILABLE": _state(
        "RAW_UNAVAILABLE",
        "Raw indisponible",
        "Raw indisponible",
        "La preuve raw attendue n'est pas disponible ; la lecture doit afficher cette limite.",
        "BLOCKER",
    ),
    "RISK_001": _state(
        "RISK_001",
        "Risque technique 001 : briques live absentes",
        "Risque 001",
        "Une ou plusieurs briques live sont absentes ; la chaîne reste en dry-run.",
        "WATCH",
    ),
    "RISK_002": _state(
        "RISK_002",
        "Risque technique 002 : mémoire B6 non visible",
        "Risque 002",
        "Aucun film B6 comparable n'est visible dans les artefacts validés.",
        "WATCH",
    ),
    "RISK_003": _state(
        "RISK_003",
        "Risque technique 003 : garde no-send non confirmé",
        "Risque 003",
        "Le garde no-send Telegram n'est pas confirmé dans l'approbation manuelle.",
        "BLOCKER",
    ),
    "B9_LIVE_DATA_FRESHNESS_GUARD_V0": _state(
        "B9_LIVE_DATA_FRESHNESS_GUARD_V0",
        "Garde fraîcheur data live",
        "Freshness guard",
        "Brique chargée de vérifier la fraîcheur des données live.",
        "INFO",
    ),
    "B9_LATEST_SCENE_CANDIDATE_V0": _state(
        "B9_LATEST_SCENE_CANDIDATE_V0",
        "Dernière scène candidate B9",
        "Scène candidate",
        "Fichier attendu contenant la dernière scène candidate B9.",
        "INFO",
    ),
    "B9_LIVE_SCENE_CANDIDATE_QUEUE_V0": _state(
        "B9_LIVE_SCENE_CANDIDATE_QUEUE_V0",
        "File des scènes candidates B9",
        "Queue scènes",
        "Fichier attendu contenant la file des candidats live B9.",
        "INFO",
    ),
    "B9_B6_AUTO_REALIGNMENT_V0": _state(
        "B9_B6_AUTO_REALIGNMENT_V0",
        "Réalignement automatique B9 vers B6",
        "Alignement B9/B6",
        "Brique attendue pour réaligner la scène B9 avec la mémoire comparative B6.",
        "INFO",
    ),
    "B9_LIVE_BRIEF_ONCE_V0": _state(
        "B9_LIVE_BRIEF_ONCE_V0",
        "Brief live unique B9",
        "Brief live once",
        "Fichier attendu contenant le brief live assemblé une fois.",
        "INFO",
    ),
    "B9_TRADER_ATTENTION_PACKET_V0": _state(
        "B9_TRADER_ATTENTION_PACKET_V0",
        "Paquet d'attention trader",
        "Attention packet",
        "Brique attendue pour préparer une attention lisible sans décision.",
        "INFO",
    ),
    "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0": _state(
        "B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0",
        "Candidat d'intégration Reality Board",
        "Reality Board payload",
        "Payload candidat destiné à une surface Reality Board, sans mutation live.",
        "INFO",
    ),
    "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0": _state(
        "B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0",
        "Adaptateur de surface Reality Board",
        "Surface adapter",
        "Adaptateur candidat pour préparer l'affichage, sans modifier le dashboard.",
        "INFO",
    ),
    "B9_TELEGRAM_FR_GATE_CANDIDATE_V0": _state(
        "B9_TELEGRAM_FR_GATE_CANDIDATE_V0",
        "Gate Telegram FR candidat",
        "Gate Telegram FR",
        "Brique candidate de contrôle Telegram FR, sans envoi.",
        "INFO",
    ),
    "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0": _state(
        "B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0",
        "Candidat d'approbation manuelle Telegram",
        "Approbation manuelle",
        "Brique candidate de revue manuelle, sans envoi automatique.",
        "INFO",
    ),
    "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0": _state(
        "B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0",
        "Contrat d'affichage français",
        "Contrat français",
        "Contrat de traduction français trader pour les états B9/B6.",
        "INFO",
    ),
}


def is_id_like(token: str) -> bool:
    return any(token.startswith(prefix) for prefix in ID_PREFIXES)


def enum_tokens(text: str) -> List[str]:
    tokens: List[str] = []
    for token in ENUM_RE.findall(str(text)):
        if token in IGNORED_ENUMS:
            continue
        if is_id_like(token):
            continue
        tokens.append(token)
    return sorted(set(tokens))


def translate_enum(token: str) -> StateDisplayFr:
    found = DISPLAY_STATE_FR.get(token)
    if found:
        return found
    return _state(
        token,
        f"Traduction à ajouter : {token}",
        "Traduction à ajouter",
        "Enum technique visible dans une sortie affichable, non encore couvert par T0170.",
        "WATCH",
        "Ajouter cet enum au dictionnaire T0170 si la fuite se répète.",
    )


def translate_text_for_display(text: str, keep_enum: bool = True) -> str:
    output = str(text)
    for token in enum_tokens(output):
        display = translate_enum(token)
        replacement = f"{display.label_fr} ({token})" if keep_enum else display.label_fr
        output = output.replace(token, replacement)
    return output


def should_skip_line(line: str) -> bool:
    text = line.strip()
    if not text:
        return True
    if text in {"{", "}", "[", "]", ",", "},"}:
        return True
    if re.match(r'^\s*"(version|generated_at|zip|path|output_dir|json|csv|md)"\s*:', text):
        return True
    return False


def read_text_lines(path: Path) -> List[str]:
    if path.suffix.lower() == ".json":
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    if path.suffix.lower() in {".csv", ".md", ".txt"}:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
    return []


def iter_output_text_files(outputs_dir: Path) -> Iterable[Path]:
    if not outputs_dir.exists():
        return []
    return sorted(
        p for p in outputs_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in {".json", ".csv", ".md", ".txt"}
    )


def audit_outputs(outputs_dir: Path) -> Dict[str, Any]:
    files = list(iter_output_text_files(outputs_dir))
    enum_rows: List[Dict[str, Any]] = []
    ok_rows: List[Dict[str, Any]] = []
    token_counts: Dict[str, int] = {}

    for path in files:
        rel = str(path.relative_to(outputs_dir.parent)) if outputs_dir.parent in path.parents else str(path)
        for idx, line in enumerate(read_text_lines(path), start=1):
            if should_skip_line(line):
                continue
            tokens = enum_tokens(line)
            if tokens:
                for token in tokens:
                    token_counts[token] = token_counts.get(token, 0) + 1
                enum_rows.append(
                    {
                        "file": rel,
                        "line": idx,
                        "tokens": tokens,
                        "original_text": " ".join(line.strip().split()),
                        "display_text_fr": translate_text_for_display(line.strip(), keep_enum=True),
                    }
                )
            else:
                lower = line.lower()
                if any(hint in lower for hint in ("_fr", "français", "mémoire", "scene", "scène", "brief", "telegram", "lecture", "piège", "affichage")):
                    ok_rows.append(
                        {
                            "file": rel,
                            "line": idx,
                            "text": " ".join(line.strip().split()),
                        }
                    )

    uncovered = sorted(token for token in token_counts if token not in DISPLAY_STATE_FR)
    covered = sorted(token for token in token_counts if token in DISPLAY_STATE_FR)

    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "policy": POLICY,
        "outputs_dir": str(outputs_dir),
        "files_scanned": len(files),
        "ok_rows": ok_rows,
        "enum_leak_rows": enum_rows,
        "token_counts": token_counts,
        "covered_tokens": covered,
        "uncovered_tokens": uncovered,
        "risk_summary": {
            "enum_leak_count": len(enum_rows),
            "covered_token_count": len(covered),
            "uncovered_token_count": len(uncovered),
            "read_only": True,
        },
        "integration_rule_fr": "Ne pas remplacer les enums moteur. Ajouter state_fr/status_fr/details_fr à côté des champs techniques affichés.",
    }


def write_outputs(outputs_dir: Path, output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    audit = audit_outputs(outputs_dir)

    json_path = output_dir / "B9_FRENCH_DISPLAY_STATE_HARDENING_V0.json"
    csv_path = output_dir / "B9_FRENCH_DISPLAY_STATE_HARDENING_ENUMS_V0.csv"
    leaks_csv_path = output_dir / "B9_FRENCH_DISPLAY_STATE_HARDENING_LEAKS_V0.csv"
    md_path = output_dir / "B9_FRENCH_DISPLAY_STATE_HARDENING_V0.md"

    json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["key", "label_fr", "short_fr", "explanation_fr", "attention_level", "integration_rule_fr", "covered_in_scan"],
        )
        writer.writeheader()
        seen = set(audit["token_counts"].keys())
        for key in sorted(DISPLAY_STATE_FR):
            row = DISPLAY_STATE_FR[key].to_dict()
            row["covered_in_scan"] = key in seen
            writer.writerow(row)
        for key in audit["uncovered_tokens"]:
            row = translate_enum(key).to_dict()
            row["covered_in_scan"] = True
            writer.writerow(row)

    with leaks_csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["file", "line", "tokens", "original_text", "display_text_fr"],
        )
        writer.writeheader()
        for row in audit["enum_leak_rows"]:
            writer.writerow({**row, "tokens": ", ".join(row["tokens"])})

    lines = [
        "# T0170 — B9 French Display State Hardening V0",
        "",
        "## Résumé",
        "",
        f"- Fichiers scannés : `{audit['files_scanned']}`",
        f"- Lignes avec enums visibles : `{len(audit['enum_leak_rows'])}`",
        f"- Enums couverts : `{len(audit['covered_tokens'])}`",
        f"- Enums non couverts : `{len(audit['uncovered_tokens'])}`",
        "- Read-only : `True`",
        "",
        "## Règle d'intégration",
        "",
        audit["integration_rule_fr"],
        "",
        "## Enums couverts par le dictionnaire T0170",
        "",
        "| Enum | Français trader | Niveau |",
        "|---|---|---|",
    ]
    for token in audit["covered_tokens"]:
        display = translate_enum(token)
        lines.append(f"| `{token}` | {display.label_fr} | `{display.attention_level}` |")

    lines.extend(["", "## Enums non couverts", ""])
    if audit["uncovered_tokens"]:
        for token in audit["uncovered_tokens"]:
            lines.append(f"- `{token}` → Traduction à ajouter")
    else:
        lines.append("Aucun enum non couvert détecté.")

    lines.extend(["", "## Fuites visibles à durcir", ""])
    if audit["enum_leak_rows"]:
        lines.append("| Fichier | Ligne | Enums | Rendu FR proposé |")
        lines.append("|---|---:|---|---|")
        for row in audit["enum_leak_rows"][:160]:
            lines.append(
                f"| `{row['file']}` | {row['line']} | `{', '.join(row['tokens'])}` | {row['display_text_fr']} |"
            )
    else:
        lines.append("Aucune fuite enum visible détectée.")

    lines.extend(
        [
            "",
            "## Risques techniques",
            "",
            "- Si un rapport Markdown affiche `state` brut, ajouter `state_fr` à côté.",
            "- Si un CSV est destiné au trader, ajouter une colonne française parallèle.",
            "- Si le CSV est purement technique, l'enum peut rester, mais le dashboard/Telegram doit lire la colonne française.",
            "- Ne jamais remplacer l'enum moteur : elle reste nécessaire aux tests.",
            "",
            "Phrase : le moteur parle enum ; le trader lit français.",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "json": str(json_path),
        "enum_csv": str(csv_path),
        "leaks_csv": str(leaks_csv_path),
        "md": str(md_path),
    }


if __name__ == "__main__":
    paths = write_outputs(Path("outputs"), Path("outputs/b9_french_display_state_hardening_v0"))
    print(json.dumps({"version": VERSION, "paths": paths}, ensure_ascii=False, indent=2))
