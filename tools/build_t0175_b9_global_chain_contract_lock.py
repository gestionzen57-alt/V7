#!/usr/bin/env python3
"""T0175 - B9 Global Chain Contract Lock V0.

Read-only contract locker for the B9 Reality Board / live chain candidate.
It validates the presence, source quality and forbidden-decision language of
candidate artefacts before any dashboard live wiring.

It does not read or write powerflow.db or tick_archive.db.
It does not modify cockpit, dashboard or telegram modules.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

VERSION = "T0175_B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bENTRY\b",
    r"\bSTOP\s*LOSS\b",
    r"\bTAKE\s*PROFIT\b",
    r"\bTARGET\b",
    r"probabilit[eé]\s+de\s+succ[eè]s",
    r"taux\s+de\s+r[eé]ussite",
    r"probability\s+of\s+success",
    r"success\s+rate",
    r"bouton\s+d[eé]cision",
    r"ordre\s+directionnel",
]

# Required files for the display/read-model chain. T0169 output is pattern-based
# because the exact folder name can vary across local packs.
REQUIRED_FILES = [
    {
        "role": "reality_board_integration_candidate",
        "path": "outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
        "why": "Source coeur de l'integration Reality Board candidate.",
    },
    {
        "role": "trader_attention_packet",
        "path": "outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json",
        "why": "Packet attention trader B9, sans decision.",
    },
    {
        "role": "live_brief_once",
        "path": "outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json",
        "why": "Brief live B9 candidate, lecture courte.",
    },
    {
        "role": "latest_scene_candidate",
        "path": "outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json",
        "why": "Scene candidate courante B9.",
    },
    {
        "role": "read_model_v01",
        "path": "outputs/b9_reality_board_read_model_v01/B9_REALITY_BOARD_READ_MODEL_V01.json",
        "why": "Read model V0.1 du Reality Board.",
    },
    {
        "role": "scene_panel_candidate_v01",
        "path": "outputs/b9_reality_board_scene_panel_candidate_v01/B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json",
        "why": "Panel candidat scene B9 pour affichage futur.",
    },
    {
        "role": "t0169_builder",
        "path": "tools/build_t0169_b9_reality_board_surface_adapter_candidate.py",
        "why": "Builder T0169 present et patchable/importable depuis tools.",
    },
]

REQUIRED_PATTERNS = [
    {
        "role": "t0169_surface_adapter_candidate_output",
        "glob": "outputs/**/B9_REALITY_BOARD_SURFACE_ADAPTER*CANDIDATE*.json",
        "why": "Sortie candidate T0169 surface adapter Reality Board.",
    }
]

OPTIONAL_FILES = [
    {
        "role": "french_event_display_contract",
        "path": "outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json",
        "why": "Contrat affichage francais trader si disponible.",
    },
    {
        "role": "live_chain_orchestrator_dry_run",
        "path": "outputs/b9_live_chain_orchestrator_dry_run_v0/B9_LIVE_CHAIN_ORCHESTRATOR_DRY_RUN_V0.json",
        "why": "Dry-run orchestrateur chaine live B9.",
    },
    {
        "role": "live_chain_contract_validator",
        "path": "outputs/b9_live_chain_contract_validator_v0/B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.json",
        "why": "Validation contrat chaine live si deja produite.",
    },
    {
        "role": "live_chain_missing_input_resolver",
        "path": "outputs/b9_live_chain_missing_input_resolver_v0/B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.json",
        "why": "Diagnostic inputs manquants si deja produit.",
    },
    {
        "role": "t0174_import_path_hotfix",
        "path": "outputs/t0174_t0169_import_path_hotfix_v0/T0174_T0169_IMPORT_PATH_HOTFIX_V0.json",
        "why": "Etat du hotfix import path T0169 si conserve en runtime.",
    },
]

OUTPUT_NAMES = {
    "json": "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json",
    "md": "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.md",
    "missing_csv": "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv",
    "forbidden_csv": "B9_GLOBAL_CHAIN_CONTRACT_LOCK_FORBIDDEN_HITS_V0.csv",
    "source_csv": "B9_GLOBAL_CHAIN_CONTRACT_LOCK_SOURCE_MATRIX_V0.csv",
    "manifest": "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MANIFEST_V0.json",
}

@dataclass
class SourceRow:
    role: str
    path: str
    required: bool
    exists: bool
    valid_json: bool
    source_quality: str
    gate_state: str
    why: str
    technical_limit: str


def _norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def read_json(path: Path) -> Tuple[bool, Optional[Any], str]:
    try:
        text = path.read_text(encoding="utf-8-sig")
        return True, json.loads(text), ""
    except Exception as exc:  # noqa: BLE001 - report exact local source issue
        return False, None, f"JSON_READ_ERROR: {type(exc).__name__}: {exc}"


def compact_value(value: Any, limit: int = 220) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True)
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit] + ("..." if len(text) > limit else "")


def extract_source_quality(data: Any) -> str:
    if not isinstance(data, dict):
        return "UNKNOWN"
    candidates = [
        data.get("source_quality"),
        data.get("data_visibility"),
        data.get("gate_state"),
        data.get("display_gate"),
        data.get("hotfix_state"),
    ]
    for item in candidates:
        if isinstance(item, str) and item.strip():
            return item.strip()
    for key in ("metadata", "meta", "quality", "contract"):
        nested = data.get(key)
        if isinstance(nested, dict):
            for nested_key in ("source_quality", "data_visibility", "gate_state", "display_gate"):
                value = nested.get(nested_key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    return "UNKNOWN"


def scan_forbidden_text(path: Path, role: str) -> List[Dict[str, str]]:
    hits: List[Dict[str, str]] = []
    if not path.exists() or path.is_dir():
        return hits
    if path.suffix.lower() not in {".json", ".md", ".txt", ".csv", ".py"}:
        return hits
    try:
        text = path.read_text(encoding="utf-8-sig", errors="ignore")
    except Exception as exc:  # noqa: BLE001
        return [{"role": role, "path": _norm(path), "pattern": "READ_ERROR", "sample": str(exc)}]
    for pattern in FORBIDDEN_PATTERNS:
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            start = max(0, match.start() - 70)
            end = min(len(text), match.end() + 70)
            sample = re.sub(r"\s+", " ", text[start:end]).strip()
            hits.append({
                "role": role,
                "path": _norm(path),
                "pattern": pattern,
                "sample": sample[:260],
            })
    return hits


def resolve_source(core_root: Path, spec: Dict[str, str], required: bool) -> Tuple[SourceRow, Optional[Path], Optional[Any], List[Dict[str, str]]]:
    rel = spec["path"]
    path = core_root / rel
    if not path.exists():
        row = SourceRow(
            role=spec["role"],
            path=rel,
            required=required,
            exists=False,
            valid_json=False if path.suffix.lower() == ".json" else True,
            source_quality="MISSING",
            gate_state="MISSING_REQUIRED" if required else "MISSING_OPTIONAL",
            why=spec.get("why", ""),
            technical_limit="Fichier absent dans le working tree courant.",
        )
        return row, None, None, []

    data: Optional[Any] = None
    valid_json = True
    technical_limit = ""
    if path.suffix.lower() == ".json":
        valid_json, data, technical_limit = read_json(path)
    source_quality = extract_source_quality(data) if valid_json else "SOURCE_ERROR"
    gate_state = "OK" if valid_json else "SOURCE_ERROR"
    row = SourceRow(
        role=spec["role"],
        path=rel,
        required=required,
        exists=True,
        valid_json=valid_json,
        source_quality=source_quality,
        gate_state=gate_state,
        why=spec.get("why", ""),
        technical_limit=technical_limit,
    )
    hits = scan_forbidden_text(path, spec["role"])
    return row, path, data, hits


def resolve_pattern(core_root: Path, spec: Dict[str, str]) -> Tuple[SourceRow, List[Path], List[Dict[str, str]]]:
    matches = sorted(core_root.glob(spec["glob"]))
    if not matches:
        row = SourceRow(
            role=spec["role"],
            path=spec["glob"],
            required=True,
            exists=False,
            valid_json=False,
            source_quality="MISSING",
            gate_state="MISSING_REQUIRED",
            why=spec.get("why", ""),
            technical_limit="Aucun fichier ne correspond au pattern requis.",
        )
        return row, [], []
    # Prefer shortest/latest deterministic path by lexical order.
    selected = matches[0]
    valid_json, data, technical_limit = read_json(selected)
    source_quality = extract_source_quality(data) if valid_json else "SOURCE_ERROR"
    row = SourceRow(
        role=spec["role"],
        path=_norm(selected.relative_to(core_root)),
        required=True,
        exists=True,
        valid_json=valid_json,
        source_quality=source_quality,
        gate_state="OK" if valid_json else "SOURCE_ERROR",
        why=spec.get("why", ""),
        technical_limit=technical_limit if technical_limit else f"Pattern matched {len(matches)} file(s). Selected first deterministic path.",
    )
    hits = scan_forbidden_text(selected, spec["role"])
    return row, matches, hits


def determine_lock_state(rows: Sequence[SourceRow], forbidden_hits: Sequence[Dict[str, str]]) -> str:
    if any(row.required and not row.exists for row in rows):
        return "LOCK_BLOCKED_MISSING_REQUIRED"
    if any(row.required and not row.valid_json for row in rows):
        return "LOCK_BLOCKED_SOURCE_ERROR"
    if forbidden_hits:
        return "LOCK_BLOCKED_FORBIDDEN_LANGUAGE"
    if any((not row.required) and (not row.exists) for row in rows):
        return "LOCK_PARTIAL_OPTIONAL_MISSING"
    return "LOCK_READY_FOR_DASHBOARD_REVIEW"


def build_contract(core_root: Path) -> Dict[str, Any]:
    rows: List[SourceRow] = []
    loaded: Dict[str, Any] = {}
    forbidden_hits: List[Dict[str, str]] = []
    pattern_matches: Dict[str, List[str]] = {}

    for spec in REQUIRED_FILES:
        row, path, data, hits = resolve_source(core_root, spec, True)
        rows.append(row)
        if data is not None:
            loaded[row.role] = data
        forbidden_hits.extend(hits)

    for spec in REQUIRED_PATTERNS:
        row, matches, hits = resolve_pattern(core_root, spec)
        rows.append(row)
        pattern_matches[row.role] = [_norm(p.relative_to(core_root)) for p in matches]
        forbidden_hits.extend(hits)

    for spec in OPTIONAL_FILES:
        row, path, data, hits = resolve_source(core_root, spec, False)
        rows.append(row)
        if data is not None:
            loaded[row.role] = data
        forbidden_hits.extend(hits)

    lock_state = determine_lock_state(rows, forbidden_hits)
    required_missing = [asdict(r) for r in rows if r.required and not r.exists]
    optional_missing = [asdict(r) for r in rows if (not r.required) and not r.exists]
    source_errors = [asdict(r) for r in rows if r.exists and not r.valid_json]

    next_watch = [
        "Relancer T0169 surface adapter candidate si le fichier output T0169 manque.",
        "Verifier que le Reality Board lit uniquement les artefacts candidats et non la logique B9.",
        "Conserver la source quality visible en haut du panel.",
        "Bloquer tout vocabulaire decisionnel si une source amont en injecte.",
    ]
    cannot_conclude = [
        "B9 ne conclut pas une decision trader.",
        "B9 ne donne pas de probabilite de succes.",
        "B9 ne garantit pas que la scene est exploitable en live si des inputs sont manquants.",
        "Le contrat ne branche pas le dashboard live ; il valide seulement la surface candidate.",
    ]

    return {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "core_root": str(core_root),
        "lock_state": lock_state,
        "changed_source_files": False,
        "db_touched": False,
        "dashboard_live_wired": False,
        "telegram_touched": False,
        "buy_sell_allowed": False,
        "success_probability_allowed": False,
        "required_missing_count": len(required_missing),
        "optional_missing_count": len(optional_missing),
        "source_error_count": len(source_errors),
        "forbidden_language_hit_count": len(forbidden_hits),
        "source_matrix": [asdict(r) for r in rows],
        "required_missing": required_missing,
        "optional_missing": optional_missing,
        "source_errors": source_errors,
        "forbidden_language_hits": forbidden_hits,
        "pattern_matches": pattern_matches,
        "sections_locked": [
            "Ce que B9 voit",
            "Etat de scene",
            "Transition",
            "Zone active",
            "Node terrain",
            "Verdict prix",
            "Memoire B6 proche",
            "Similarites",
            "Differences",
            "Pieges techniques",
            "Source quality",
            "Ce qu'il faut surveiller ensuite",
            "Ce que B9 ne peut pas conclure",
        ],
        "next_watch": next_watch,
        "cannot_conclude": cannot_conclude,
        "technical_limits": [
            "Read-only hors outputs T0175 generes.",
            "Aucune DB lue ou ecrite.",
            "Aucun import cockpit, dashboard live ou telegram.",
            "Les outputs runtime T0175 ne doivent pas etre commites sauf decision architecte explicite.",
        ],
    }


def write_csv(path: Path, rows: Sequence[Dict[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def render_markdown(contract: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("# T0175 - B9 Global Chain Contract Lock V0")
    lines.append("")
    lines.append(f"Generated UTC: {contract['generated_at_utc']}")
    lines.append(f"Core root: `{contract['core_root']}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"`{contract['lock_state']}`")
    lines.append("")
    lines.append("```text")
    lines.append("Le dashboard affiche, il ne decide pas.")
    lines.append("B9 ne cherche pas le signal. B9 cherche la trace laissee par l'effort.")
    lines.append("```")
    lines.append("")
    lines.append("## Contract flags")
    lines.append("")
    for key in ["changed_source_files", "db_touched", "dashboard_live_wired", "telegram_touched", "buy_sell_allowed", "success_probability_allowed"]:
        lines.append(f"- {key}: `{contract[key]}`")
    lines.append("")
    lines.append("## Counters")
    lines.append("")
    for key in ["required_missing_count", "optional_missing_count", "source_error_count", "forbidden_language_hit_count"]:
        lines.append(f"- {key}: `{contract[key]}`")
    lines.append("")
    lines.append("## Source matrix")
    lines.append("")
    lines.append("| Role | Required | Exists | Valid JSON | Source quality | Gate | Path |")
    lines.append("|---|---:|---:|---:|---|---|---|")
    for row in contract["source_matrix"]:
        lines.append(
            f"| {row['role']} | {row['required']} | {row['exists']} | {row['valid_json']} | "
            f"{row['source_quality']} | {row['gate_state']} | `{row['path']}` |"
        )
    lines.append("")
    lines.append("## Required missing")
    lines.append("")
    if not contract["required_missing"]:
        lines.append("Aucun input requis manquant.")
    else:
        for row in contract["required_missing"]:
            lines.append(f"- `{row['path']}` - {row['why']}")
    lines.append("")
    lines.append("## Forbidden language hits")
    lines.append("")
    if not contract["forbidden_language_hits"]:
        lines.append("Aucun vocabulaire decisionnel interdit detecte dans les sources scannees.")
    else:
        for hit in contract["forbidden_language_hits"][:50]:
            lines.append(f"- `{hit['path']}` pattern `{hit['pattern']}` sample: {hit['sample']}")
    lines.append("")
    lines.append("## Sections locked")
    lines.append("")
    for section in contract["sections_locked"]:
        lines.append(f"- {section}")
    lines.append("")
    lines.append("## Ce qu'il faut surveiller ensuite")
    lines.append("")
    for item in contract["next_watch"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Ce que B9 ne peut pas conclure")
    lines.append("")
    for item in contract["cannot_conclude"]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("## Limites techniques")
    lines.append("")
    for item in contract["technical_limits"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def write_outputs(contract: Dict[str, Any], output_dir: Path) -> Dict[str, str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "contract_json": output_dir / OUTPUT_NAMES["json"],
        "contract_md": output_dir / OUTPUT_NAMES["md"],
        "missing_csv": output_dir / OUTPUT_NAMES["missing_csv"],
        "forbidden_csv": output_dir / OUTPUT_NAMES["forbidden_csv"],
        "source_csv": output_dir / OUTPUT_NAMES["source_csv"],
        "manifest_json": output_dir / OUTPUT_NAMES["manifest"],
    }
    paths["contract_json"].write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    paths["contract_md"].write_text(render_markdown(contract), encoding="utf-8")
    write_csv(paths["missing_csv"], contract["required_missing"] + contract["optional_missing"], [
        "role", "path", "required", "exists", "valid_json", "source_quality", "gate_state", "why", "technical_limit"
    ])
    write_csv(paths["forbidden_csv"], contract["forbidden_language_hits"], ["role", "path", "pattern", "sample"])
    write_csv(paths["source_csv"], contract["source_matrix"], [
        "role", "path", "required", "exists", "valid_json", "source_quality", "gate_state", "why", "technical_limit"
    ])
    manifest = {
        "version": VERSION,
        "generated_at_utc": contract["generated_at_utc"],
        "lock_state": contract["lock_state"],
        "artifacts": {k: str(v) for k, v in paths.items()},
        "runtime_outputs_commit_policy": "DO_NOT_COMMIT_UNLESS_ARCHITECT_APPROVES",
    }
    paths["manifest_json"].write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return {k: str(v) for k, v in paths.items()}


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build T0175 B9 global chain contract lock V0.")
    parser.add_argument("--core-root", default=".", help="PowerFlow Core root path.")
    parser.add_argument("--output-dir", default="outputs/t0175_b9_global_chain_contract_lock_v0", help="Output directory.")
    parser.add_argument("--print-json", action="store_true", help="Print JSON summary to stdout.")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    core_root = Path(args.core_root).resolve()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = core_root / output_dir
    contract = build_contract(core_root)
    artifacts = write_outputs(contract, output_dir)
    summary = {
        "version": contract["version"],
        "core_root": contract["core_root"],
        "output_dir": str(output_dir),
        "lock_state": contract["lock_state"],
        "required_missing_count": contract["required_missing_count"],
        "optional_missing_count": contract["optional_missing_count"],
        "source_error_count": contract["source_error_count"],
        "forbidden_language_hit_count": contract["forbidden_language_hit_count"],
        "artifacts": artifacts,
        "db_touched": False,
        "dashboard_live_wired": False,
        "telegram_touched": False,
    }
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"[PASS] {VERSION} generated")
        print(f"[LOCK_STATE] {contract['lock_state']}")
        for name, path in artifacts.items():
            print(f"[ARTIFACT] {name}: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
