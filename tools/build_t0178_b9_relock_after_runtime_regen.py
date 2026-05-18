#!/usr/bin/env python3
"""T0178 - B9 relock after runtime regeneration.

Runs/reads T0175 Global Chain Contract Lock and T0176 Dashboard Degraded Gate,
then produces a compact orchestration verdict for dashboard readiness.

Contract:
- No DB access.
- No cockpit live wiring.
- No Telegram.
- No BUY/SELL, no success probability, no decision button.
- Writes only T0178 outputs and a Docs/Reports markdown report.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

VERSION = "T0178_B9_RELOCK_AFTER_RUNTIME_REGEN_V0"

T0175_BUILDER = Path("tools/build_t0175_b9_global_chain_contract_lock.py")
T0176_BUILDER = Path("tools/build_t0176_b9_chain_degraded_dashboard_candidate.py")

T0175_OUT_DIR = Path("outputs/t0175_b9_global_chain_contract_lock_v0")
T0176_OUT_DIR = Path("outputs/t0176_b9_chain_degraded_dashboard_candidate_v0")

T0175_JSON = T0175_OUT_DIR / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.json"
T0175_MISSING_CSV = T0175_OUT_DIR / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_MISSING_INPUTS_V0.csv"
T0176_JSON = T0176_OUT_DIR / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.json"
T0176_REGEN_CSV = T0176_OUT_DIR / "B9_CHAIN_DEGRADED_DASHBOARD_REGEN_COMMANDS_V0.csv"
T0176_MISSING_BRICKS_CSV = T0176_OUT_DIR / "B9_CHAIN_DEGRADED_DASHBOARD_MISSING_BRICK_CARDS_V0.csv"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bENTRY\b",
    r"\bSTOP\b",
    r"\bTAKE\s*PROFIT\b",
    r"\bTARGET\b",
    r"probabilit[eé]\s+de\s+succ[eè]s",
    r"success\s+probability",
]

READY_LOCK_STATES = {"LOCK_READY_FOR_DASHBOARD_REVIEW"}
PARTIAL_LOCK_STATES = {"LOCK_PARTIAL_OPTIONAL_MISSING"}
DASHBOARD_DEGRADED_OK_STATES = {
    "READY_FULL_CHAIN_VIEW",
    "DEGRADED_OPTIONAL_INPUTS_MISSING",
    "DEGRADED_REQUIRED_INPUTS_MISSING",
    "DASHBOARD_OPERATIONAL_DEGRADED_READY",
    "DASHBOARD_OPERATIONAL_DEGRADED_RELOCK",
    "DASHBOARD_READY_FOR_CANDIDATE_REVIEW",
    "DASHBOARD_OPERATIONAL_DEGRADED_REVIEW",
}
BLOCKED_PREFIXES = ("BLOCKED", "LOCK_BLOCKED", "DASHBOARD_RELOCK_BLOCKED")


@dataclass
class CommandResult:
    name: str
    command: str
    returncode: Optional[int]
    state: str
    stdout_tail: str = ""
    stderr_tail: str = ""
    parsed_json: Optional[Dict[str, Any]] = None


@dataclass
class RelockVerdict:
    final_state: str
    can_display_b9_now: bool
    display_mode: str
    reason_fr: str
    next_action_fr: str


def tail(text: str, max_chars: int = 2500) -> str:
    if not text:
        return ""
    return text[-max_chars:]


def extract_last_json_object(text: str) -> Optional[Dict[str, Any]]:
    """Extract the last JSON object printed in mixed stdout."""
    if not text:
        return None
    starts = [m.start() for m in re.finditer(r"\{", text)]
    for start in reversed(starts):
        candidate = text[start:].strip()
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    return None


def load_json(path: Path) -> Optional[Dict[str, Any]]:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {"_source_error": str(exc), "_path": str(path)}


def read_csv_rows(path: Path, max_rows: int = 200) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    rows: List[Dict[str, str]] = []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({str(k): "" if v is None else str(v) for k, v in row.items()})
                if len(rows) >= max_rows:
                    break
    except Exception as exc:  # noqa: BLE001
        rows.append({"source_error": str(exc), "path": str(path)})
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]], default_headers: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    headers: List[str] = list(default_headers)
    for row in rows:
        for key in row.keys():
            if key not in headers:
                headers.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        for row in rows:
            writer.writerow({h: row.get(h, "") for h in headers})


def run_python_command(core_root: Path, args: List[str], name: str) -> CommandResult:
    cmd = [sys.executable] + args
    proc = subprocess.run(
        cmd,
        cwd=str(core_root),
        text=True,
        capture_output=True,
        check=False,
    )
    parsed = extract_last_json_object(proc.stdout)
    state = "OK" if proc.returncode == 0 else "FAILED"
    return CommandResult(
        name=name,
        command=" ".join(cmd),
        returncode=proc.returncode,
        state=state,
        stdout_tail=tail(proc.stdout),
        stderr_tail=tail(proc.stderr),
        parsed_json=parsed,
    )


def get_lock_state(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return "MISSING"
    return str(data.get("lock_state") or data.get("state") or data.get("contract_state") or "UNKNOWN")


def get_dashboard_state(data: Optional[Dict[str, Any]]) -> str:
    if not data:
        return "MISSING"
    return str(data.get("dashboard_state") or data.get("panel_state") or data.get("state") or "UNKNOWN")


def int_field(data: Optional[Dict[str, Any]], key: str) -> int:
    if not data:
        return 0
    try:
        return int(data.get(key, 0) or 0)
    except (TypeError, ValueError):
        return 0


def decide_verdict(
    lock_state: str,
    dashboard_state: str,
    required_missing_count: int,
    forbidden_language_hit_count: int,
    source_error_count: int,
) -> RelockVerdict:
    if forbidden_language_hit_count > 0:
        return RelockVerdict(
            final_state="BLOCKED_FORBIDDEN_LANGUAGE",
            can_display_b9_now=False,
            display_mode="BLOCKED",
            reason_fr="Langage interdit detecte dans une surface candidate.",
            next_action_fr="Nettoyer le vocabulaire decisionnel avant affichage.",
        )
    if source_error_count > 0:
        return RelockVerdict(
            final_state="BLOCKED_SOURCE_ERROR",
            can_display_b9_now=False,
            display_mode="BLOCKED",
            reason_fr="Une source de chaine B9 est illisible ou corrompue.",
            next_action_fr="Corriger la source illisible puis relancer T0175 et T0176.",
        )
    if lock_state in READY_LOCK_STATES:
        return RelockVerdict(
            final_state="READY",
            can_display_b9_now=True,
            display_mode="FULL_CONTRACT_REVIEW",
            reason_fr="Contrat B9 complet pour revue dashboard candidate.",
            next_action_fr="Passer en revue architecte de surface read-only.",
        )
    if lock_state in PARTIAL_LOCK_STATES:
        return RelockVerdict(
            final_state="PARTIAL",
            can_display_b9_now=True,
            display_mode="PARTIAL_OPTIONAL_MISSING",
            reason_fr="Contrat B9 exploitable avec seulement des inputs optionnels manquants.",
            next_action_fr="Afficher le panel candidate et regenerer les optionnels restants.",
        )
    if dashboard_state in DASHBOARD_DEGRADED_OK_STATES:
        return RelockVerdict(
            final_state="DEGRADED_READY",
            can_display_b9_now=True,
            display_mode="OPERATIONAL_DEGRADED",
            reason_fr="T0176 convertit le verrou incomplet en lecture operationnelle degradee exploitable.",
            next_action_fr="Afficher ce que B9 voit deja, les manques et les commandes de regeneration.",
        )
    if required_missing_count > 0:
        return RelockVerdict(
            final_state="BLOCKED_REQUIRED_MISSING",
            can_display_b9_now=False,
            display_mode="BLOCKED",
            reason_fr="Inputs requis encore absents et pas de gate degrade exploitable detecte.",
            next_action_fr="Regenerer les inputs requis listes puis relancer T0175/T0176.",
        )
    if lock_state.startswith(BLOCKED_PREFIXES) or dashboard_state.startswith(BLOCKED_PREFIXES):
        return RelockVerdict(
            final_state="BLOCKED",
            can_display_b9_now=False,
            display_mode="BLOCKED",
            reason_fr="La chaine reste bloquee par un verrou technique.",
            next_action_fr="Lire les rapports T0175/T0176 pour isoler la brique bloquante.",
        )
    return RelockVerdict(
        final_state="UNKNOWN_RELOCK_STATE",
        can_display_b9_now=False,
        display_mode="UNKNOWN",
        reason_fr="Etat de relock non interpretable avec les contrats connus.",
        next_action_fr="Verifier les JSON T0175/T0176 et mettre a jour le mapping de contrat.",
    )


def count_forbidden_hits_in_texts(paths: Iterable[Path]) -> List[Dict[str, Any]]:
    hits: List[Dict[str, Any]] = []
    compiled = [(p, re.compile(p, flags=re.IGNORECASE)) for p in FORBIDDEN_PATTERNS]
    for path in paths:
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:  # noqa: BLE001
            hits.append({"path": str(path), "pattern": "SOURCE_READ_ERROR", "match": str(exc)})
            continue
        for pattern, rgx in compiled:
            match = rgx.search(text)
            if match:
                hits.append({"path": str(path), "pattern": pattern, "match": match.group(0)})
    return hits


def normalize_missing_rows(rows: List[Dict[str, str]]) -> List[Dict[str, str]]:
    normalized: List[Dict[str, str]] = []
    for row in rows:
        item = dict(row)
        if "regen_command" not in item:
            item["regen_command"] = infer_regen_command(item)
        if "brick" not in item:
            item["brick"] = item.get("source") or item.get("input") or item.get("path") or "UNKNOWN"
        if "requiredness" not in item:
            item["requiredness"] = item.get("required") or item.get("is_required") or "UNKNOWN"
        normalized.append(item)
    return normalized


def infer_regen_command(row: Dict[str, str]) -> str:
    blob = " ".join(str(v) for v in row.values()).lower()
    if "t0159" in blob or "french_event_display" in blob:
        return "python <builder_T0159> --core-root . --output-dir outputs/b9_french_event_display_contract_v0 --print-json"
    if "t0169" in blob or "surface_adapter" in blob:
        return "python tools/build_t0169_b9_reality_board_surface_adapter_candidate.py --core-root . --output-dir outputs/b9_reality_board_surface_adapter_candidate_v0 --print-json"
    if "t0156" in blob or "reality_board" in blob:
        return "python <builder_T0156> --core-root . --output-dir outputs/b9_reality_board_integration_candidate_v0 --print-json"
    if "t0176" in blob or "degraded" in blob:
        return "python tools/build_t0176_b9_chain_degraded_dashboard_candidate.py --core-root . --output-dir outputs/t0176_b9_chain_degraded_dashboard_candidate_v0 --print-json"
    if "t0175" in blob or "contract_lock" in blob:
        return "python tools/build_t0175_b9_global_chain_contract_lock.py --core-root . --output-dir outputs/t0175_b9_global_chain_contract_lock_v0 --print-json"
    return "A confirmer par architecte: builder non identifie automatiquement."


def write_markdown_report(
    path: Path,
    summary: Dict[str, Any],
    before: Dict[str, Any],
    after: Dict[str, Any],
    commands: List[CommandResult],
    missing_rows: List[Dict[str, str]],
    regen_rows: List[Dict[str, str]],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# T0178 - B9 Relock After Runtime Regen V0")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- Final state: `{summary['final_state']}`")
    lines.append(f"- Can display B9 now: `{summary['can_display_b9_now']}`")
    lines.append(f"- Display mode: `{summary['display_mode']}`")
    lines.append(f"- Reason: {summary['reason_fr']}")
    lines.append(f"- Next action: {summary['next_action_fr']}")
    lines.append("")
    lines.append("## T0175 / T0176 state")
    lines.append("")
    lines.append(f"- T0175 before: `{before.get('t0175_lock_state', 'MISSING')}`")
    lines.append(f"- T0175 after: `{after.get('t0175_lock_state', 'MISSING')}`")
    lines.append(f"- T0176 before: `{before.get('t0176_dashboard_state', 'MISSING')}`")
    lines.append(f"- T0176 after: `{after.get('t0176_dashboard_state', 'MISSING')}`")
    lines.append(f"- Required missing after: `{after.get('required_missing_count', 0)}`")
    lines.append(f"- Optional missing after: `{after.get('optional_missing_count', 0)}`")
    lines.append(f"- Source errors after: `{after.get('source_error_count', 0)}`")
    lines.append(f"- Forbidden language hits after: `{after.get('forbidden_language_hit_count', 0)}`")
    lines.append("")
    lines.append("## Command results")
    lines.append("")
    for cmd in commands:
        lines.append(f"### {cmd.name}")
        lines.append(f"- State: `{cmd.state}`")
        lines.append(f"- Return code: `{cmd.returncode}`")
        lines.append(f"- Command: `{cmd.command}`")
        if cmd.parsed_json:
            state_fields = {k: cmd.parsed_json.get(k) for k in ("lock_state", "dashboard_state", "state") if k in cmd.parsed_json}
            if state_fields:
                lines.append(f"- Parsed state: `{state_fields}`")
        if cmd.stderr_tail:
            lines.append("- stderr tail:")
            lines.append("```text")
            lines.append(cmd.stderr_tail.strip())
            lines.append("```")
        lines.append("")
    lines.append("## Remaining missing inputs")
    lines.append("")
    if not missing_rows:
        lines.append("No remaining missing inputs found in T0175 CSV.")
    else:
        for row in missing_rows[:50]:
            brick = row.get("brick") or row.get("input") or row.get("path") or "UNKNOWN"
            req = row.get("requiredness") or row.get("required") or "UNKNOWN"
            cmd = row.get("regen_command") or ""
            lines.append(f"- `{brick}` | requiredness=`{req}` | regen=`{cmd}`")
        if len(missing_rows) > 50:
            lines.append(f"- ... {len(missing_rows) - 50} more rows in CSV")
    lines.append("")
    lines.append("## Regeneration commands")
    lines.append("")
    if regen_rows:
        for row in regen_rows[:50]:
            command = row.get("command") or row.get("regen_command") or row.get("cmd") or str(row)
            lines.append(f"- `{command}`")
    else:
        lines.append("No explicit T0176 regeneration command CSV found. Commands were inferred where possible in the missing input CSV.")
    lines.append("")
    lines.append("## Contract")
    lines.append("")
    lines.append("- No cockpit live modification.")
    lines.append("- No DB touch.")
    lines.append("- No Telegram.")
    lines.append("- No BUY/SELL.")
    lines.append("- No success probability.")
    lines.append("- No decision button.")
    lines.append("- Dashboard displays. It does not decide.")
    lines.append("")
    lines.append("## Doctrine")
    lines.append("")
    lines.append("B9 ne cherche pas le signal. B9 cherche la trace laissee par l'effort.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_relock(core_root: Path, output_dir: Path, execute: bool) -> Dict[str, Any]:
    core_root = core_root.resolve()
    output_dir = (core_root / output_dir).resolve() if not output_dir.is_absolute() else output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    docs_report = core_root / "Docs" / "Reports" / "T0175_T0176_B9_RELOCK_AFTER_RUNTIME_REGEN_REPORT.md"

    pre_t0175 = load_json(core_root / T0175_JSON)
    pre_t0176 = load_json(core_root / T0176_JSON)
    before = {
        "t0175_lock_state": get_lock_state(pre_t0175),
        "t0176_dashboard_state": get_dashboard_state(pre_t0176),
        "required_missing_count": int_field(pre_t0175, "required_missing_count"),
        "optional_missing_count": int_field(pre_t0175, "optional_missing_count"),
    }

    commands: List[CommandResult] = []
    if execute:
        if (core_root / T0175_BUILDER).exists():
            commands.append(run_python_command(core_root, [str(T0175_BUILDER), "--core-root", ".", "--output-dir", str(T0175_OUT_DIR), "--print-json"], "T0175 Global Chain Contract Lock"))
        else:
            commands.append(CommandResult("T0175 Global Chain Contract Lock", str(T0175_BUILDER), None, "MISSING_BUILDER"))
        if (core_root / T0176_BUILDER).exists():
            commands.append(run_python_command(core_root, [str(T0176_BUILDER), "--core-root", ".", "--output-dir", str(T0176_OUT_DIR), "--print-json"], "T0176 Dashboard Operational Degraded Gate"))
        else:
            commands.append(CommandResult("T0176 Dashboard Operational Degraded Gate", str(T0176_BUILDER), None, "MISSING_BUILDER"))
    else:
        commands.append(CommandResult("T0175 Global Chain Contract Lock", str(T0175_BUILDER), None, "DRY_RUN"))
        commands.append(CommandResult("T0176 Dashboard Operational Degraded Gate", str(T0176_BUILDER), None, "DRY_RUN"))

    post_t0175 = load_json(core_root / T0175_JSON)
    post_t0176 = load_json(core_root / T0176_JSON)

    forbidden_paths = [
        core_root / T0175_JSON,
        core_root / T0176_JSON,
        core_root / T0175_OUT_DIR / "B9_GLOBAL_CHAIN_CONTRACT_LOCK_V0.md",
        core_root / T0176_OUT_DIR / "B9_CHAIN_DEGRADED_DASHBOARD_CANDIDATE_V0.md",
    ]
    forbidden_hits = count_forbidden_hits_in_texts(forbidden_paths)

    lock_state = get_lock_state(post_t0175)
    dashboard_state = get_dashboard_state(post_t0176)
    required_missing_count = int_field(post_t0175, "required_missing_count")
    optional_missing_count = int_field(post_t0175, "optional_missing_count")
    source_error_count = int_field(post_t0175, "source_error_count") + int_field(post_t0176, "source_error_count")
    forbidden_count = int_field(post_t0175, "forbidden_language_hit_count") + int_field(post_t0176, "forbidden_language_hit_count") + len(forbidden_hits)

    verdict = decide_verdict(lock_state, dashboard_state, required_missing_count, forbidden_count, source_error_count)
    after = {
        "t0175_lock_state": lock_state,
        "t0176_dashboard_state": dashboard_state,
        "required_missing_count": required_missing_count,
        "optional_missing_count": optional_missing_count,
        "source_error_count": source_error_count,
        "forbidden_language_hit_count": forbidden_count,
    }

    missing_rows = normalize_missing_rows(read_csv_rows(core_root / T0175_MISSING_CSV))
    regen_rows = read_csv_rows(core_root / T0176_REGEN_CSV)
    brick_cards_rows = read_csv_rows(core_root / T0176_MISSING_BRICKS_CSV)

    command_rows = [asdict(c) | {"parsed_json": json.dumps(c.parsed_json, ensure_ascii=False) if c.parsed_json else ""} for c in commands]

    contract_json = output_dir / "B9_RELOCK_AFTER_RUNTIME_REGEN_V0.json"
    contract_md = output_dir / "B9_RELOCK_AFTER_RUNTIME_REGEN_V0.md"
    remaining_csv = output_dir / "B9_RELOCK_REMAINING_MISSING_INPUTS_V0.csv"
    regen_csv = output_dir / "B9_RELOCK_REGEN_COMMANDS_V0.csv"
    command_csv = output_dir / "B9_RELOCK_COMMAND_RESULTS_V0.csv"
    forbidden_csv = output_dir / "B9_RELOCK_FORBIDDEN_HITS_V0.csv"
    manifest_json = output_dir / "B9_RELOCK_AFTER_RUNTIME_REGEN_MANIFEST_V0.json"

    summary = {
        "version": VERSION,
        "core_root": str(core_root),
        "output_dir": str(output_dir),
        "executed": execute,
        "final_state": verdict.final_state,
        "can_display_b9_now": verdict.can_display_b9_now,
        "display_mode": verdict.display_mode,
        "reason_fr": verdict.reason_fr,
        "next_action_fr": verdict.next_action_fr,
        "before": before,
        "after": after,
        "command_results": [asdict(c) for c in commands],
        "remaining_missing_count_csv_rows": len(missing_rows),
        "regen_command_count_csv_rows": len(regen_rows),
        "missing_brick_card_count_csv_rows": len(brick_cards_rows),
        "forbidden_hits": forbidden_hits,
        "db_touched": False,
        "dashboard_live_wired": False,
        "telegram_touched": False,
        "artifacts": {
            "summary_json": str(contract_json),
            "summary_md": str(contract_md),
            "docs_report_md": str(docs_report),
            "remaining_missing_csv": str(remaining_csv),
            "regen_commands_csv": str(regen_csv),
            "command_results_csv": str(command_csv),
            "forbidden_hits_csv": str(forbidden_csv),
            "manifest_json": str(manifest_json),
        },
    }

    contract_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown_report(contract_md, summary, before, after, commands, missing_rows, regen_rows)
    write_markdown_report(docs_report, summary, before, after, commands, missing_rows, regen_rows)
    write_csv(remaining_csv, missing_rows, ["brick", "requiredness", "path", "input", "source", "regen_command"])
    write_csv(regen_csv, regen_rows, ["brick", "command", "regen_command", "path"])
    write_csv(command_csv, command_rows, ["name", "state", "returncode", "command", "stdout_tail", "stderr_tail", "parsed_json"])
    write_csv(forbidden_csv, forbidden_hits, ["path", "pattern", "match"])
    manifest = {
        "version": VERSION,
        "generated_artifacts": summary["artifacts"],
        "contract": {
            "no_db": True,
            "no_live_dashboard_wiring": True,
            "no_telegram": True,
            "no_buy_sell": True,
            "dashboard_displays_does_not_decide": True,
        },
    }
    manifest_json.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="T0178 B9 relock after runtime regeneration.")
    parser.add_argument("--core-root", default=".", help="PowerFlow Core root")
    parser.add_argument("--output-dir", default=str(Path("outputs/t0178_b9_relock_after_runtime_regen_v0")), help="Output directory")
    parser.add_argument("--execute", action="store_true", help="Actually run T0175 then T0176 builders")
    parser.add_argument("--print-json", action="store_true", help="Print JSON summary")
    args = parser.parse_args(argv)

    summary = build_relock(Path(args.core_root), Path(args.output_dir), execute=args.execute)
    if args.print_json:
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"[PASS] {VERSION} generated")
        print(f"[STATE] {summary['final_state']} display_mode={summary['display_mode']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
