from __future__ import annotations

import csv
import json
import os
import re
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0173_B9_LIVE_CHAIN_RUNTIME_MISSING_INPUT_RESOLVER_V0"

FORBIDDEN_PATTERNS = [
    re.compile(r"\bordre\s+d['’]?ex[ée]cution\b", re.IGNORECASE),
    re.compile(r"\bprobabilit[ée]\s+de\s+r[ée]ussite\b", re.IGNORECASE),
    re.compile(r"\btaux\s+de\s+r[ée]ussite\b", re.IGNORECASE),
]

@dataclass(frozen=True)
class ChainStep:
    step_id: str
    ticket: str
    label_fr: str
    required_path: str
    command: str
    depends_on: str
    purpose_fr: str

EXPECTED_STEPS: List[ChainStep] = [
    ChainStep(
        "T0166_FRESHNESS_GUARD",
        "T0166",
        "Fraicheur source live",
        "outputs/b9_live_data_freshness_guard_v0/B9_LIVE_DATA_FRESHNESS_GUARD_V0.json",
        "python tools\\build_t0166_b9_live_data_freshness_guard.py --core-root . --output-dir outputs\\b9_live_data_freshness_guard_v0 --freshness-seconds 300",
        "DB et candidate B9",
        "Qualifier si la source live est fraiche, vide, stale ou raw-unqualified.",
    ),
    ChainStep(
        "T0147_LATEST_SCENE_CANDIDATE",
        "T0147",
        "Scene candidate B9",
        "outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json",
        "python tools\\build_t0147_b9_live_scene_candidate_queue.py --sequence-summary-json samples\\b9_live_scene_candidate_queue_v0\\sample_t009_sequence_summary_live_queue.json --output-dir outputs\\b9_live_scene_candidate_queue_v0 --max-candidates 12",
        "summary B9 enrichi",
        "Creer la scene candidate qui sert d'ancre candidate_id.",
    ),
    ChainStep(
        "T0167_B9_B6_REALIGNMENT",
        "T0167",
        "Realignement B9 vers B6",
        "outputs/b9_b6_auto_realignment_v0/B9_B6_AUTO_REALIGNMENT_V0.json",
        "python tools\\build_t0167_b9_b6_auto_realignment_runner.py --latest-scene-json outputs\\b9_live_scene_candidate_queue_v0\\B9_LATEST_SCENE_CANDIDATE_V0.json --b6-index-json outputs\\b6_similarity_index_v0\\B6_SIMILARITY_INDEX_V0.json --film-cards-json outputs\\b6_film_library_v0\\B6_FILM_CARDS_V0.json --output-dir outputs\\b9_b6_auto_realignment_v0 --top-k 5",
        "T0147 + B6 index",
        "Aligner la memoire B6 sur la scene B9 courante.",
    ),
    ChainStep(
        "T0148_LIVE_BRIEF_ONCE",
        "T0148",
        "Brief live B9/B6",
        "outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json",
        "python tools\\build_t0148_b9_live_brief_once_runner.py --latest-scene-json outputs\\b9_live_scene_candidate_queue_v0\\B9_LATEST_SCENE_CANDIDATE_V0.json --queue-json outputs\\b9_live_scene_candidate_queue_v0\\B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json --adapter-json outputs\\b6_live_scene_adapter_v0\\B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json --similarity-query-json outputs\\b6_similarity_query_v0\\B6_SIMILARITY_QUERY_RESULT_V0.json --false-positive-json outputs\\b6_false_positive_context_v0\\B6_FALSE_POSITIVE_CONTEXT_V0.json --terrain-synthesis-json outputs\\b6_human_terrain_synthesis_v0\\B6_HUMAN_TERRAIN_SYNTHESIS_V0.json --french-report-json outputs\\b9_french_trader_scene_report_v0\\B9_FRENCH_TRADER_SCENE_REPORT_V0.json --output-dir outputs\\b9_live_brief_once_v0 --top-k 3",
        "T0147 + T0167 + B6 outputs",
        "Assembler scene, memoire, differences et pieges techniques.",
    ),
    ChainStep(
        "T0155_TRADER_ATTENTION_PACKET",
        "T0155",
        "Packet attention trader",
        "outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json",
        "python tools\\build_t0155_b9_trader_attention_packet.py --input-json outputs\\b9_live_brief_once_v0\\B9_LIVE_BRIEF_ONCE_V0.json --output-dir outputs\\b9_trader_attention_packet_v0",
        "T0148",
        "Transformer le brief en packet d'attention read-only.",
    ),
    ChainStep(
        "T0156_REALITY_BOARD_CANDIDATE",
        "T0156",
        "Payload Reality Board candidat",
        "outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
        "python tools\\build_t0156_b9_reality_board_integration_candidate.py --attention-packet-json outputs\\b9_trader_attention_packet_v0\\B9_TRADER_ATTENTION_PACKET_V0.json --output-dir outputs\\b9_reality_board_integration_candidate_v0",
        "T0155",
        "Preparer un payload candidat pour affichage futur.",
    ),
    ChainStep(
        "T0169_SURFACE_ADAPTER_CANDIDATE",
        "T0169",
        "Surface adapter Reality Board candidat",
        "outputs/b9_reality_board_surface_adapter_candidate_v0/B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json",
        "python tools\\build_t0169_b9_reality_board_surface_adapter_candidate.py --read-model-json outputs\\b9_reality_board_read_model_v01\\B9_REALITY_BOARD_READ_MODEL_V01.json --panel-json outputs\\b9_reality_board_scene_panel_candidate_v01\\B9_REALITY_BOARD_SCENE_PANEL_CANDIDATE_V01.json --payload-json outputs\\b9_reality_board_integration_candidate_v0\\B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json --display-contract-json outputs\\b9_french_event_display_contract_v0\\B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json --output-dir outputs\\b9_reality_board_surface_adapter_candidate_v0 --print-json",
        "T0156 + T0160/T0161 + T0159",
        "Preparer la surface lisible par dashboard futur.",
    ),
    ChainStep(
        "T0157_TELEGRAM_FR_GATE",
        "T0157",
        "Gate Telegram FR candidat",
        "outputs/b9_telegram_fr_gate_candidate_v0/B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json",
        "python tools\\build_t0157_b9_telegram_fr_gate_candidate.py --reality-board-payload-json outputs\\b9_reality_board_integration_candidate_v0\\B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json --output-dir outputs\\b9_telegram_fr_gate_candidate_v0",
        "T0156",
        "Preparer le message FR candidat sans envoi.",
    ),
    ChainStep(
        "T0170_TELEGRAM_MANUAL_APPROVAL",
        "T0170",
        "Approbation manuelle Telegram candidate",
        "outputs/b9_telegram_manual_approval_candidate_v0/B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0.json",
        "python tools\\build_t0170_b9_telegram_manual_approval_candidate.py --telegram-gate-json outputs\\b9_telegram_fr_gate_candidate_v0\\B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json --output-dir outputs\\b9_telegram_manual_approval_candidate_v0 --print-json",
        "T0157",
        "Creer une checklist d'approbation manuelle, sans envoi.",
    ),
    ChainStep(
        "T0159_FRENCH_DISPLAY_CONTRACT",
        "T0159",
        "Contrat affichage FR",
        "outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json",
        "python tools\\build_t0159_b9_french_event_display_contract.py --output-dir outputs\\b9_french_event_display_contract_v0 --print-json",
        "lexique B9",
        "Garantir que les enums moteur soient traduits en francais trader.",
    ),
    ChainStep(
        "T0172_CONTRACT_VALIDATOR",
        "T0172",
        "Validation contrat chaine live",
        "outputs/b9_live_chain_contract_validator_v0/B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.json",
        "python tools\\build_t0172_b9_live_chain_contract_validator.py --core-root . --output-dir outputs\\b9_live_chain_contract_validator_v0 --print-json",
        "toute la chaine candidate",
        "Valider presence, alignement candidate_id et garde-fous.",
    ),
]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_json_load_error": str(exc), "_path": str(path)}


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: Optional[List[str]] = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: List[str] = []
        for row in rows:
            for key in row.keys():
                if key not in keys:
                    keys.append(key)
        fieldnames = keys or ["empty"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _forbidden_hits_text(text: str) -> List[str]:
    hits: List[str] = []
    for pattern in FORBIDDEN_PATTERNS:
        for match in pattern.findall(text):
            hit = str(match)
            if hit not in hits:
                hits.append(hit)
    return hits


def _step_aliases(step_id: str) -> List[str]:
    aliases = [step_id]
    if "T0148" in step_id:
        aliases += ["T0148", "T0148_LIVE_BRIEF", "LIVE_BRIEF", "B9_LIVE_BRIEF_ONCE"]
    if "T0147" in step_id:
        aliases += ["T0147", "LATEST_SCENE", "LATEST_SCENE_CANDIDATE"]
    if "T0167" in step_id:
        aliases += ["T0167", "REALIGNMENT", "B9_B6_REALIGNMENT"]
    if "T0155" in step_id:
        aliases += ["T0155", "ATTENTION_PACKET"]
    if "T0156" in step_id:
        aliases += ["T0156", "REALITY_BOARD_CANDIDATE"]
    if "T0169" in step_id:
        aliases += ["T0169", "SURFACE_ADAPTER"]
    if "T0157" in step_id:
        aliases += ["T0157", "TELEGRAM_GATE"]
    if "T0170" in step_id:
        aliases += ["T0170", "MANUAL_APPROVAL"]
    if "T0159" in step_id:
        aliases += ["T0159", "DISPLAY_CONTRACT", "FRENCH_DISPLAY"]
    if "T0166" in step_id:
        aliases += ["T0166", "FRESHNESS_GUARD"]
    if "T0172" in step_id:
        aliases += ["T0172", "CONTRACT_VALIDATOR"]
    return list(dict.fromkeys(aliases))


def _contract_missing_set(contract: Dict[str, Any]) -> set[str]:
    raw = contract.get("missing_steps") or contract.get("missing_inputs") or []
    if isinstance(raw, str):
        raw = [raw]
    result = set()
    for item in raw if isinstance(raw, list) else []:
        if isinstance(item, dict):
            candidate = item.get("step_id") or item.get("ticket") or item.get("path") or item.get("name")
        else:
            candidate = str(item)
        if candidate:
            result.add(candidate.upper().replace(" ", "_"))
    return result


def _matches_missing_contract(step: ChainStep, missing_set: set[str]) -> bool:
    if not missing_set:
        return False
    aliases = [a.upper().replace(" ", "_") for a in _step_aliases(step.step_id)]
    for missing in missing_set:
        for alias in aliases:
            if missing == alias or alias in missing or missing in alias:
                return True
    return False


def _resolve_steps(core_root: Path, contract: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    missing_set = _contract_missing_set(contract)
    rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    plan_rows: List[Dict[str, Any]] = []
    order = 0
    for step in EXPECTED_STEPS:
        path = core_root / step.required_path
        exists = path.exists()
        contract_flags_missing = _matches_missing_contract(step, missing_set)
        state = "FOUND" if exists and not contract_flags_missing else "MISSING"
        if exists and contract_flags_missing:
            state = "REGENERATE_REQUESTED_BY_T0172"
        row = {
            "step_id": step.step_id,
            "ticket": step.ticket,
            "label_fr": step.label_fr,
            "required_path": step.required_path,
            "exists": bool(exists),
            "contract_flags_missing": bool(contract_flags_missing),
            "resolver_state": state,
            "depends_on": step.depends_on,
            "purpose_fr": step.purpose_fr,
            "command": step.command,
        }
        rows.append(row)
        if state != "FOUND":
            order += 1
            missing_rows.append(row)
            plan_rows.append({
                "run_order": order,
                "step_id": step.step_id,
                "ticket": step.ticket,
                "why": "missing_file" if not exists else "contract_validator_requested_regeneration",
                "required_path": step.required_path,
                "command": step.command,
                "expected_after_run": step.required_path,
            })
    return rows, missing_rows, plan_rows


def _make_md(summary: Dict[str, Any], missing_rows: List[Dict[str, Any]], plan_rows: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    lines.append("# T0173 — B9 Live Chain Runtime Missing Input Resolver V0")
    lines.append("")
    lines.append("## Résumé")
    lines.append(f"- État resolver : `{summary['resolver_state']}`")
    lines.append(f"- Étapes attendues : `{summary['expected_steps']}`")
    lines.append(f"- Étapes manquantes / à régénérer : `{summary['missing_or_regenerate_count']}`")
    lines.append(f"- Candidate ID : `{summary.get('candidate_id') or ''}`")
    lines.append(f"- Match count : `{summary.get('match_count')}`")
    lines.append(f"- Top film : `{summary.get('top_match_film_id') or ''}`")
    lines.append("")
    lines.append("## Doctrine")
    lines.append("B9 lit la scène. B6 compare les films. Le resolver indique quoi relancer ; il ne déclenche aucune action.")
    lines.append("")
    if not missing_rows:
        lines.append("## Verdict")
        lines.append("Tous les inputs attendus sont présents selon le scan local et le contrat T0172.")
    else:
        lines.append("## Inputs manquants ou à régénérer")
        for row in missing_rows:
            lines.append(f"- `{row['step_id']}` — {row['label_fr']} — `{row['required_path']}`")
        lines.append("")
        lines.append("## Plan de régénération recommandé")
        for row in plan_rows:
            lines.append(f"{row['run_order']}. **{row['ticket']}** — {row['step_id']}")
            lines.append("")
            lines.append("```powershell")
            lines.append(str(row["command"]))
            lines.append("```")
            lines.append("")
    lines.append("## Limites")
    lines.append("- Read-only.")
    lines.append("- Aucune écriture DB.")
    lines.append("- Aucun cockpit live modifié.")
    lines.append("- Aucun envoi Telegram.")
    lines.append("- Aucun ordre directionnel.")
    lines.append("- Aucune promesse de performance.")
    return "\n".join(lines) + "\n"


def _write_ps1(path: Path, plan_rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "$ErrorActionPreference = 'Stop'",
        "Set-Location \"C:\\Users\\User\\Desktop\\ProjetPowerFlow\\IA\\GPT\\core\"",
        "Write-Host '=== T0173 suggested regeneration plan ===' -ForegroundColor Cyan",
    ]
    if not plan_rows:
        lines.append("Write-Host 'No missing inputs detected by T0173.' -ForegroundColor Green")
    else:
        for row in plan_rows:
            safe_cmd = str(row["command"]).replace("'", "''")
            lines.append(f"Write-Host 'Step {row['run_order']}: {row['step_id']}' -ForegroundColor Yellow")
            lines.append(f"Write-Host '{safe_cmd}'")
            lines.append("Write-Host ''")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(core_root: str | Path, output_dir: str | Path, contract_json: str | Path | None = None) -> Dict[str, Any]:
    core = Path(core_root).resolve()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    contract_path = Path(contract_json) if contract_json else core / "outputs/b9_live_chain_contract_validator_v0/B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.json"
    if not contract_path.is_absolute():
        contract_path = core / contract_path
    contract = _load_json(contract_path)

    rows, missing_rows, plan_rows = _resolve_steps(core, contract)

    state = "B9_LIVE_CHAIN_INPUTS_COMPLETE" if not missing_rows else "B9_LIVE_CHAIN_MISSING_INPUTS_PLAN_READY"
    if not contract_path.exists():
        state = "B9_LIVE_CHAIN_CONTRACT_FILE_MISSING_PLAN_READY"

    candidate_id = contract.get("candidate_id") or contract.get("latest_candidate_id") or ""
    match_count = contract.get("match_count", "")
    top_match_film_id = contract.get("top_match_film_id") or ""
    summary: Dict[str, Any] = {
        "version": VERSION,
        "generated_at": _now(),
        "resolver_state": state,
        "core_root": str(core),
        "contract_json": str(contract_path),
        "contract_exists": contract_path.exists(),
        "candidate_id": candidate_id,
        "match_count": match_count,
        "top_match_film_id": top_match_film_id,
        "expected_steps": len(EXPECTED_STEPS),
        "found_steps": sum(1 for r in rows if r["resolver_state"] == "FOUND"),
        "missing_or_regenerate_count": len(missing_rows),
        "missing_steps": [r["step_id"] for r in missing_rows],
        "read_only": True,
        "db_write": False,
        "dashboard_live_write": False,
        "telegram_send": False,
        "technical_limits": [],
    }
    if not contract_path.exists():
        summary["technical_limits"].append("T0172 contract validator output is missing; resolver uses filesystem scan and full regeneration plan.")
    if missing_rows:
        summary["technical_limits"].append("One or more runtime inputs are missing or requested for regeneration.")

    md = _make_md(summary, missing_rows, plan_rows)
    forbidden_hits = _forbidden_hits_text(md + json.dumps(summary, ensure_ascii=False))
    summary["forbidden_language_hits"] = forbidden_hits

    json_path = out / "B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.json"
    md_path = out / "B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.md"
    inputs_csv = out / "B9_LIVE_CHAIN_MISSING_INPUTS_V0.csv"
    plan_csv = out / "B9_LIVE_CHAIN_REGENERATION_PLAN_V0.csv"
    all_steps_csv = out / "B9_LIVE_CHAIN_RESOLVER_STEPS_V0.csv"
    commands_ps1 = out / "B9_LIVE_CHAIN_REGENERATION_PLAN_V0.ps1"
    manifest_path = out / "B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_MANIFEST.json"
    zip_path = out / "B9_LIVE_CHAIN_MISSING_INPUT_RESOLVER_V0.zip"

    _write_json(json_path, {"summary": summary, "steps": rows, "missing_inputs": missing_rows, "regeneration_plan": plan_rows})
    md_path.write_text(md, encoding="utf-8")
    _write_csv(inputs_csv, missing_rows)
    _write_csv(plan_csv, plan_rows)
    _write_csv(all_steps_csv, rows)
    _write_ps1(commands_ps1, plan_rows)

    manifest = {
        "version": VERSION,
        "generated_at": _now(),
        "outputs": [p.name for p in [json_path, md_path, inputs_csv, plan_csv, all_steps_csv, commands_ps1]],
        "zip": str(zip_path),
        "read_only": True,
    }
    _write_json(manifest_path, manifest)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in [json_path, md_path, inputs_csv, plan_csv, all_steps_csv, commands_ps1, manifest_path]:
            zf.write(path, arcname=path.name)
    summary["zip"] = str(zip_path)
    _write_json(json_path, {"summary": summary, "steps": rows, "missing_inputs": missing_rows, "regeneration_plan": plan_rows})
    return summary
