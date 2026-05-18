"""T0172 - B9 Live Chain Contract Validator V0.

Read-only contract validator for the B9 MAX live candidate chain.
It validates that artifacts produced by upstream bricks expose compatible fields,
state values, candidate identifiers, memory match metadata, French display status,
and no-decision guards before dashboard/Telegram integration is considered.
"""
from __future__ import annotations

import csv
import json
import re
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0172_B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0"

FORBIDDEN_LANGUAGE = [
    "BUY", "SELL", "ACHAT", "VENTE", "SIGNAL GAGNANT", "PROBABILITE DE REUSSITE",
    "TAUX DE REUSSITE", "ENTRE MAINTENANT", "CONSEIL FINANCIER",
]

DEFAULT_FILES = {
    "freshness_guard": "outputs/b9_live_data_freshness_guard_v0/B9_LIVE_DATA_FRESHNESS_GUARD_V0.json",
    "latest_scene_candidate": "outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json",
    "b9_b6_realignment": "outputs/b9_b6_auto_realignment_v0/B9_B6_AUTO_REALIGNMENT_V0.json",
    "live_brief_once": "outputs/b9_live_brief_once_v0/B9_LIVE_BRIEF_ONCE_V0.json",
    "attention_packet": "outputs/b9_trader_attention_packet_v0/B9_TRADER_ATTENTION_PACKET_V0.json",
    "reality_board_candidate": "outputs/b9_reality_board_integration_candidate_v0/B9_REALITY_BOARD_INTEGRATION_CANDIDATE_V0.json",
    "surface_adapter_candidate": "outputs/b9_reality_board_surface_adapter_candidate_v0/B9_REALITY_BOARD_SURFACE_ADAPTER_CANDIDATE_V0.json",
    "telegram_gate_candidate": "outputs/b9_telegram_fr_gate_candidate_v0/B9_TELEGRAM_FR_GATE_CANDIDATE_V0.json",
    "telegram_manual_approval": "outputs/b9_telegram_manual_approval_candidate_v0/B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE_V0.json",
    "french_display_contract": "outputs/b9_french_event_display_contract_v0/B9_FRENCH_EVENT_DISPLAY_CONTRACT_V0.json",
}

REQUIRED_FIELDS = {
    "freshness_guard": ["version", "guard_state"],
    "latest_scene_candidate": ["candidate_id"],
    "b9_b6_realignment": ["alignment_state", "candidate_id"],
    "live_brief_once": ["brief_state", "candidate_id"],
    "attention_packet": ["packet_state", "candidate_id", "no_trade_decision_guard"],
    "reality_board_candidate": ["payload_state", "candidate_id"],
    "surface_adapter_candidate": ["surface_state", "candidate_id"],
    "telegram_gate_candidate": ["gate_state", "candidate_id", "no_send_guard"],
    "telegram_manual_approval": ["approval_state", "candidate_id", "manual_approval_required", "no_send_guard"],
    "french_display_contract": ["contract_state"],
}

READY_PREFIX = {
    "b9_b6_realignment": ("B9_B6_REALIGNMENT_READY",),
    "live_brief_once": ("B9_LIVE_BRIEF_READY",),
    "attention_packet": ("B9_TRADER_ATTENTION_PACKET",),
    "reality_board_candidate": ("B9_REALITY_BOARD_INTEGRATION_CANDIDATE",),
    "surface_adapter_candidate": ("B9_SURFACE_ADAPTER_CANDIDATE",),
    "telegram_gate_candidate": ("B9_TELEGRAM_FR_GATE_CANDIDATE",),
    "telegram_manual_approval": ("B9_TELEGRAM_MANUAL_APPROVAL_CANDIDATE",),
    "french_display_contract": ("PASS",),
}

BLOCKED_MARKERS = ["BLOCKED", "RAW_UNAVAILABLE", "FORBIDDEN_LANGUAGE"]

@dataclass
class StepValidation:
    step: str
    expected_path: str
    exists: bool
    state_field: str
    state_value: str
    candidate_id: str
    missing_fields: str
    blocked: bool
    no_decision_guard_ok: bool
    no_send_guard_ok: bool
    raw_unavailable_flag: bool
    forbidden_language_hits: str
    technical_limits: str


def _load_json(path: Path) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    if not path.exists():
        return None, "missing file"
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            return None, "json root is not object"
        return data, None
    except Exception as exc:  # pragma: no cover - exact exception differs by platform
        return None, f"json load error: {exc}"


def _first_present(d: Dict[str, Any], names: Iterable[str], default: str = "") -> str:
    for name in names:
        val = d.get(name)
        if val is not None and val != "":
            return str(val)
    return default


def _state_field_for_step(step: str) -> str:
    candidates = {
        "freshness_guard": "guard_state",
        "b9_b6_realignment": "alignment_state",
        "live_brief_once": "brief_state",
        "attention_packet": "packet_state",
        "reality_board_candidate": "payload_state",
        "surface_adapter_candidate": "surface_state",
        "telegram_gate_candidate": "gate_state",
        "telegram_manual_approval": "approval_state",
        "french_display_contract": "contract_state",
    }
    return candidates.get(step, "state")


def _contains_forbidden_text(data: Any) -> List[str]:
    text = json.dumps(data, ensure_ascii=False).upper()
    hits: List[str] = []
    for term in FORBIDDEN_LANGUAGE:
        pattern = re.escape(term.upper())
        if re.search(pattern, text):
            hits.append(term)
    return sorted(set(hits))


def _is_blocked_state(state: str) -> bool:
    up = state.upper()
    return any(marker in up for marker in BLOCKED_MARKERS)


def _raw_unavailable(data: Dict[str, Any]) -> bool:
    text = json.dumps(data, ensure_ascii=False).upper()
    return "RAW_UNAVAILABLE" in text or "MEMORY_REJECTED_RAW_UNAVAILABLE" in text


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes", "oui", "ok"}
    return bool(value)


def _match_count(data: Dict[str, Any]) -> int:
    for key in ("match_count", "matches", "similar_films_count"):
        val = data.get(key)
        if isinstance(val, int):
            return val
        if isinstance(val, str) and val.isdigit():
            return int(val)
    for key in ("similar_films", "matches", "memory_matches"):
        val = data.get(key)
        if isinstance(val, list):
            return len(val)
    return 0


def validate_chain(core_root: Path, output_dir: Path, file_map: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = dict(DEFAULT_FILES)
    if file_map:
        files.update({k: v for k, v in file_map.items() if v})

    rows: List[StepValidation] = []
    loaded: Dict[str, Dict[str, Any]] = {}
    candidate_ids: List[str] = []
    all_forbidden: List[str] = []
    missing_steps: List[str] = []
    blocked_steps: List[str] = []
    raw_unavailable_steps: List[str] = []

    for step, rel in files.items():
        path = Path(rel)
        if not path.is_absolute():
            path = core_root / rel
        data, err = _load_json(path)
        state_field = _state_field_for_step(step)
        technical_limits: List[str] = []
        if err:
            missing_steps.append(step)
            technical_limits.append(err)
            rows.append(StepValidation(
                step=step,
                expected_path=str(path),
                exists=False,
                state_field=state_field,
                state_value="MISSING_INPUT",
                candidate_id="",
                missing_fields=",".join(REQUIRED_FIELDS.get(step, [])),
                blocked=True,
                no_decision_guard_ok=False,
                no_send_guard_ok=False,
                raw_unavailable_flag=False,
                forbidden_language_hits="",
                technical_limits="; ".join(technical_limits),
            ))
            continue

        loaded[step] = data
        missing_fields = [f for f in REQUIRED_FIELDS.get(step, []) if f not in data]
        state_value = str(data.get(state_field, data.get("state", "UNKNOWN_STATE")))
        candidate_id = _first_present(data, ["candidate_id", "latest_candidate_id", "scene_id", "film_id"])
        if candidate_id:
            candidate_ids.append(candidate_id)
        hits = _contains_forbidden_text(data)
        all_forbidden.extend(hits)
        raw_flag = _raw_unavailable(data)
        blocked = _is_blocked_state(state_value) or bool(missing_fields) or bool(hits) or raw_flag
        if blocked:
            blocked_steps.append(step)
        if raw_flag:
            raw_unavailable_steps.append(step)
        no_decision_guard_ok = _as_bool(data.get("no_trade_decision_guard", data.get("no_decision_guard", False)))
        no_send_guard_ok = _as_bool(data.get("no_send_guard", False))
        if step in {"attention_packet"} and not no_decision_guard_ok:
            blocked = True
            technical_limits.append("missing no-decision guard")
        if step in {"telegram_gate_candidate", "telegram_manual_approval"} and not no_send_guard_ok:
            blocked = True
            technical_limits.append("missing no-send guard")
        if missing_fields:
            technical_limits.append("missing required fields: " + ",".join(missing_fields))
        if hits:
            technical_limits.append("forbidden language hits in user-facing artifact")
        if raw_flag:
            technical_limits.append("raw unavailable marker detected")

        rows.append(StepValidation(
            step=step,
            expected_path=str(path),
            exists=True,
            state_field=state_field,
            state_value=state_value,
            candidate_id=candidate_id,
            missing_fields=",".join(missing_fields),
            blocked=blocked,
            no_decision_guard_ok=no_decision_guard_ok,
            no_send_guard_ok=no_send_guard_ok,
            raw_unavailable_flag=raw_flag,
            forbidden_language_hits=",".join(hits),
            technical_limits="; ".join(technical_limits),
        ))

    # Cross-step candidate consistency. Ignore display contract and freshness guard.
    identity_ids = [r.candidate_id for r in rows if r.candidate_id and r.step not in {"french_display_contract", "freshness_guard"}]
    unique_ids = sorted(set(identity_ids))
    candidate_consistency_ok = len(unique_ids) <= 1
    primary_candidate_id = unique_ids[0] if candidate_consistency_ok and unique_ids else (unique_ids[0] if unique_ids else "")

    if not candidate_consistency_ok:
        blocked_steps.append("candidate_id_consistency")

    live_brief = loaded.get("live_brief_once", {})
    realignment = loaded.get("b9_b6_realignment", {})
    attention = loaded.get("attention_packet", {})
    telegram_manual = loaded.get("telegram_manual_approval", {})

    total_match_count = max(_match_count(live_brief), _match_count(realignment), _match_count(attention))
    top_match_film_id = _first_present(live_brief, ["top_match_film_id"], _first_present(realignment, ["top_match_film_id"], _first_present(attention, ["top_match_film_id"])))
    false_positive_context_available = _as_bool(live_brief.get("false_positive_context_available", attention.get("false_positive_context_available", False)))

    if missing_steps:
        state = "B9_LIVE_CHAIN_CONTRACT_BLOCKED_MISSING_INPUTS"
    elif all_forbidden:
        state = "B9_LIVE_CHAIN_CONTRACT_BLOCKED_FORBIDDEN_LANGUAGE"
    elif raw_unavailable_steps:
        state = "B9_LIVE_CHAIN_CONTRACT_BLOCKED_RAW_UNAVAILABLE"
    elif not candidate_consistency_ok:
        state = "B9_LIVE_CHAIN_CONTRACT_BLOCKED_CANDIDATE_MISMATCH"
    elif blocked_steps:
        state = "B9_LIVE_CHAIN_CONTRACT_REVIEW_TECHNICAL_RISK"
    else:
        state = "B9_LIVE_CHAIN_CONTRACT_PASS"

    summary: Dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "contract_state": state,
        "candidate_id": primary_candidate_id,
        "steps_checked": len(rows),
        "steps_found": sum(1 for r in rows if r.exists),
        "missing_steps": missing_steps,
        "blocked_steps": sorted(set(blocked_steps)),
        "raw_unavailable_steps": sorted(set(raw_unavailable_steps)),
        "candidate_consistency_ok": candidate_consistency_ok,
        "candidate_ids_seen": unique_ids,
        "match_count": total_match_count,
        "top_match_film_id": top_match_film_id,
        "false_positive_context_available": false_positive_context_available,
        "manual_approval_required": _as_bool(telegram_manual.get("manual_approval_required", True)),
        "manual_approval_granted": _as_bool(telegram_manual.get("manual_approval_granted", False)),
        "no_send_guard": _as_bool(telegram_manual.get("no_send_guard", False)),
        "forbidden_language_hits": sorted(set(all_forbidden)),
        "read_only": True,
        "db_write": False,
        "dashboard_live_write": False,
        "telegram_send": False,
        "no_trade_decision_guard": True,
    }
    summary["technical_limits"] = _technical_limits(summary, rows)

    _write_outputs(output_dir, summary, rows)
    return summary


def _technical_limits(summary: Dict[str, Any], rows: List[StepValidation]) -> List[str]:
    limits: List[str] = []
    if summary["missing_steps"]:
        limits.append("Une ou plusieurs briques live sont absentes ; dry-run uniquement.")
    if not summary["candidate_consistency_ok"]:
        limits.append("Les candidate_id ne sont pas alignés sur toute la chaîne.")
    if summary["raw_unavailable_steps"]:
        limits.append("RAW_UNAVAILABLE détecté : chaîne live active bloquée.")
    if summary["forbidden_language_hits"]:
        limits.append("Langage interdit détecté dans un artefact utilisateur.")
    if summary["match_count"] == 0:
        limits.append("Aucun film B6 comparable visible dans les artefacts validés.")
    if not summary["no_send_guard"]:
        limits.append("Le no-send guard Telegram n'est pas confirmé dans l'approbation manuelle.")
    if not limits:
        limits.append("Contrat live cohérent ; reste dry-run, sans dashboard live ni Telegram send.")
    return limits


def _write_outputs(output_dir: Path, summary: Dict[str, Any], rows: List[StepValidation]) -> None:
    json_path = output_dir / "B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.json"
    md_path = output_dir / "B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.md"
    steps_csv = output_dir / "B9_LIVE_CHAIN_CONTRACT_STEPS_V0.csv"
    risks_csv = output_dir / "B9_LIVE_CHAIN_CONTRACT_RISKS_V0.csv"
    manifest = output_dir / "B9_LIVE_CHAIN_CONTRACT_VALIDATOR_MANIFEST.json"
    zip_path = output_dir / "B9_LIVE_CHAIN_CONTRACT_VALIDATOR_V0.zip"

    json_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# B9 Live Chain Contract Validator V0",
        "",
        f"State: `{summary['contract_state']}`",
        f"Candidate: `{summary.get('candidate_id','')}`",
        f"Steps found: {summary['steps_found']}/{summary['steps_checked']}",
        f"Match count: {summary['match_count']}",
        f"Top film: `{summary.get('top_match_film_id','')}`",
        f"False-positive context available: {summary['false_positive_context_available']}",
        "",
        "## Lecture PowerFlow",
        "B9 lit la scène. B6 compare les films. Le validator vérifie le contrat live ; il ne déclenche aucune action.",
        "",
        "## Limites techniques",
    ]
    lines.extend([f"- {x}" for x in summary.get("technical_limits", [])])
    lines.extend(["", "## Steps"])
    for r in rows:
        lines.append(f"- `{r.step}`: {r.state_value} | exists={r.exists} | blocked={r.blocked} | candidate={r.candidate_id}")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with steps_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(rows[0]).keys()) if rows else ["step"])
        writer.writeheader()
        for row in rows:
            writer.writerow(asdict(row))

    with risks_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["risk_id", "risk_fr"])
        writer.writeheader()
        for i, risk in enumerate(summary.get("technical_limits", []), start=1):
            writer.writerow({"risk_id": f"RISK_{i:03d}", "risk_fr": risk})

    manifest_data = {
        "version": VERSION,
        "files": [p.name for p in [json_path, md_path, steps_csv, risks_csv, manifest, zip_path]],
        "read_only": True,
        "db_write": False,
        "dashboard_live_write": False,
        "telegram_send": False,
    }
    manifest.write_text(json.dumps(manifest_data, indent=2, ensure_ascii=False), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in [json_path, md_path, steps_csv, risks_csv, manifest]:
            zf.write(p, arcname=p.name)


def run(args: Any) -> Dict[str, Any]:
    core_root = Path(getattr(args, "core_root", ".")).resolve()
    output_dir = Path(getattr(args, "output_dir", "outputs/b9_live_chain_contract_validator_v0"))
    if not output_dir.is_absolute():
        output_dir = core_root / output_dir
    file_map = getattr(args, "file_map", None)
    return validate_chain(core_root=core_root, output_dir=output_dir, file_map=file_map)
