from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

VERSION = "T0176_B9_DASHBOARD_OPERATIONAL_DEGRADED_GATE_V0"
FORBIDDEN_TERMS = ["BUY", "SELL", "ACHAT", "VENTE", "SIGNAL GAGNANT", "PROBABILITE DE SUCCES"]


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception as exc:  # noqa: BLE001
        return {"_read_error": str(exc)}


def _read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in keys:
                keys.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys or ["empty"])
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _text_scan(obj: Any) -> List[str]:
    text = json.dumps(obj, ensure_ascii=False).upper()
    hits = []
    for term in FORBIDDEN_TERMS:
        pattern = r"(?<![A-ZÀ-Ü0-9_])" + re.escape(term) + r"(?![A-ZÀ-Ü0-9_])"
        if re.search(pattern, text):
            # Allow guards/negative statements about forbidden terms.
            if term in {"BUY", "SELL", "ACHAT", "VENTE"} and re.search(r"AUCUN\s+" + re.escape(term), text):
                continue
            hits.append(term)
    return sorted(set(hits))


def _make_card(step_id: str, required: str, status: str, expected_path: str, command: str) -> Dict[str, Any]:
    required_bool = str(required).strip().lower() in {"true", "1", "yes", "required"}
    return {
        "step_id": step_id or "UNKNOWN_STEP",
        "required": required_bool,
        "status": status or "MISSING",
        "expected_path": expected_path,
        "regeneration_command": command,
        "display_fr": ("Entrée obligatoire absente" if required_bool else "Entrée optionnelle absente"),
        "operator_hint_fr": "Régénérer cette brique avant lecture complète." if required_bool else "Lecture possible, mais contexte partiel.",
    }


def build_operational_gate(
    *,
    core_root: Path,
    t0175_contract_json: Optional[Path] = None,
    t0175_missing_csv: Optional[Path] = None,
    output_dir: Path,
    allow_degraded: bool = True,
) -> Dict[str, Any]:
    core_root = core_root.resolve()
    output_dir = output_dir.resolve()
    contract_path = (t0175_contract_json or core_root / "outputs" / "t0175_b9_global_chain_contract_lock_v0" / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json").resolve()
    missing_path = (t0175_missing_csv or core_root / "outputs" / "t0175_b9_global_chain_contract_lock_v0" / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv").resolve()

    contract = _read_json(contract_path)
    missing_rows = _read_csv_rows(missing_path)

    lock_state = str(contract.get("lock_state") or "LOCK_UNKNOWN")
    required_missing_count = int(contract.get("required_missing_count") or 0)
    optional_missing_count = int(contract.get("optional_missing_count") or 0)
    source_error_count = int(contract.get("source_error_count") or 0)
    forbidden_language_hit_count = int(contract.get("forbidden_language_hit_count") or 0)

    missing_cards = [
        _make_card(
            str(row.get("step_id") or row.get("step") or row.get("name") or "UNKNOWN_STEP"),
            str(row.get("required") or row.get("is_required") or ""),
            str(row.get("status") or row.get("state") or "MISSING"),
            str(row.get("expected_path") or row.get("path") or ""),
            str(row.get("regeneration_command") or row.get("command") or ""),
        )
        for row in missing_rows
    ]

    hard_block_reasons: List[str] = []
    if source_error_count > 0:
        hard_block_reasons.append("SOURCE_ERROR_PRESENT")
    if forbidden_language_hit_count > 0:
        hard_block_reasons.append("FORBIDDEN_LANGUAGE_PRESENT")
    if not contract_path.exists():
        hard_block_reasons.append("T0175_CONTRACT_JSON_MISSING")

    if hard_block_reasons:
        surface_state = "DASHBOARD_OPERATIONAL_BLOCKED_HARD_CONTRACT_ERROR"
    elif lock_state == "LOCK_READY_FOR_DASHBOARD_REVIEW":
        surface_state = "DASHBOARD_OPERATIONAL_READY"
    elif allow_degraded:
        surface_state = "DASHBOARD_OPERATIONAL_DEGRADED_READY"
    else:
        surface_state = "DASHBOARD_OPERATIONAL_BLOCKED_MISSING_REQUIRED"

    payload: Dict[str, Any] = {
        "version": VERSION,
        "generated_at": _utc_now(),
        "core_root": str(core_root),
        "t0175_contract_json": str(contract_path),
        "t0175_contract_exists": contract_path.exists(),
        "t0175_missing_csv": str(missing_path),
        "t0175_missing_csv_exists": missing_path.exists(),
        "lock_state_in": lock_state,
        "surface_state": surface_state,
        "allow_degraded": allow_degraded,
        "required_missing_count": required_missing_count,
        "optional_missing_count": optional_missing_count,
        "source_error_count": source_error_count,
        "forbidden_language_hit_count": forbidden_language_hit_count,
        "hard_block_reasons": hard_block_reasons,
        "dashboard_live_wired": False,
        "telegram_send": False,
        "db_write": False,
        "display_policy_fr": {
            "core_rule": "Afficher ce qui existe, marquer ce qui manque, ne pas inventer une lecture complète.",
            "dashboard_role": "Le dashboard affiche la perception B9/B6 ; il ne décide pas.",
            "missing_inputs_role": "Les inputs manquants deviennent des cartes techniques visibles.",
        },
        "surface_cards": [
            {
                "card_id": "B9_SCENE_STATUS",
                "title_fr": "État de chaîne B9",
                "value_fr": "Lecture opérationnelle dégradée" if "DEGRADED" in surface_state else surface_state,
                "technical_state": surface_state,
            },
            {
                "card_id": "B9_MISSING_INPUTS",
                "title_fr": "Entrées runtime manquantes",
                "value_fr": f"{required_missing_count} obligatoires / {optional_missing_count} optionnelles",
                "technical_state": lock_state,
            },
        ] + missing_cards,
        "technical_limits": [
            "Mode dégradé : certains inputs runtime B9/B6 sont absents.",
            "Le dashboard peut afficher la chaîne et les manques, mais ne doit pas présenter une lecture complète si des inputs obligatoires manquent.",
            "Aucune action live n'est déclenchée par ce gate.",
        ],
    }
    payload["forbidden_language_hits"] = _text_scan(payload)

    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / "B9_DASHBOARD_OPERATIONAL_DEGRADED_GATE_V0.json"
    md_path = output_dir / "B9_DASHBOARD_OPERATIONAL_DEGRADED_GATE_V0.md"
    cards_path = output_dir / "B9_DASHBOARD_OPERATIONAL_SURFACE_CARDS_V0.csv"
    _write_json(json_path, payload)
    _write_csv(cards_path, payload["surface_cards"])

    md = [
        "# B9 Dashboard Operational Degraded Gate V0",
        "",
        f"- Surface state : `{surface_state}`",
        f"- Lock T0175 entrant : `{lock_state}`",
        f"- Inputs obligatoires manquants : `{required_missing_count}`",
        f"- Inputs optionnels manquants : `{optional_missing_count}`",
        f"- Source errors : `{source_error_count}`",
        f"- Langage interdit : `{payload['forbidden_language_hits']}`",
        "",
        "## Règle opérationnelle",
        "",
        "Afficher ce qui existe. Marquer ce qui manque. Ne pas inventer une lecture complète.",
        "",
        "## Cartes manquantes",
        "",
    ]
    for card in missing_cards:
        md.append(f"- `{card['step_id']}` — {card['display_fr']} — `{card['expected_path']}`")
    md.append("")
    md.append("## Limites techniques")
    for item in payload["technical_limits"]:
        md.append(f"- {item}")
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    payload["artifacts"] = {
        "json": str(json_path),
        "md": str(md_path),
        "cards_csv": str(cards_path),
    }
    _write_json(json_path, payload)
    return payload
