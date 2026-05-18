#!/usr/bin/env python
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

VERSION = "B9_TELEGRAM_PREVIEW_AUDIT_BOARD_V0_T0165A_SECTION_TOLERANCE"

FORBIDDEN_PATTERNS = [
    r"\bBUY\b", r"\bSELL\b", r"\bachat\b", r"\bvente\b",
    r"\bentre\s+maintenant\b", r"\bprobabilit[ée]\s+de\s+r[ée]ussite\b",
    r"\bsignal\s+gagnant\b", r"\bconseil\s+financier\b",
]
REQUIRED_SECTIONS = ["B9 voit", "Zone", "État", "Mémoire proche", "Piège technique", "À surveiller", "Limite"]

def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"_missing": True, "_path": str(path)}
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:
        return {"_invalid_json": True, "_path": str(path), "_error": str(exc)}

def forbidden_hits(text: str) -> list[str]:
    return [p for p in FORBIDDEN_PATTERNS if re.search(p, text or "", flags=re.IGNORECASE)]

def has_section(text: str, section: str) -> bool:
    """Accept 'B9 voit :', 'B9 voit:', '- B9 voit :', and extra spaces."""
    pattern = r"(?im)^\s*(?:[-*]\s*)?" + re.escape(section) + r"\s*:"
    return re.search(pattern, text or "") is not None

def section_missing(text: str) -> list[str]:
    return [s for s in REQUIRED_SECTIONS if not has_section(text, s)]

def get_message(preview: Mapping[str, Any], gate: Mapping[str, Any]) -> str:
    message = str(preview.get("message_candidate") or gate.get("message_candidate") or "")
    if message.strip():
        return message
    sections = preview.get("sections")
    if isinstance(sections, Mapping):
        lines = []
        for section in REQUIRED_SECTIONS:
            val = sections.get(section)
            if val is not None and str(val).strip():
                lines.append(f"{section} : {val}")
        return "\n".join(lines)
    return ""

def classify_gate(preview: Mapping[str, Any], gate: Mapping[str, Any]) -> tuple[str, str]:
    message = get_message(preview, gate)
    hits = forbidden_hits(message)
    missing = section_missing(message)
    if hits:
        return "BLOCKED_FORBIDDEN_LANGUAGE", "|".join(hits)
    if missing:
        return "BLOCKED_MISSING_SECTIONS", "|".join(missing)
    if gate.get("telegram_send_enabled") is not False:
        return "BLOCKED_SEND_FLAG_NOT_FALSE", "telegram_send_enabled must be false"
    if gate.get("send_attempted") not in (False, None):
        return "BLOCKED_SEND_ATTEMPTED", "send_attempted must be false"
    if gate.get("gate_status") not in ("DRY_RUN_PASS", "DRY_RUN_BLOCKED", None):
        return "REVIEW_UNKNOWN_GATE_STATUS", str(gate.get("gate_status"))
    if gate.get("gate_status") == "DRY_RUN_BLOCKED":
        return "REVIEW_DRY_RUN_BLOCKED", "gate artifact already blocked"
    return "READY_FOR_HUMAN_REVIEW_NO_SEND", "preview is formatted and gated as no-send"

def message_stats(message: str) -> dict[str, Any]:
    lines = [x for x in str(message or "").splitlines() if x.strip()]
    return {
        "char_count": len(message or ""),
        "line_count": len(lines),
        "section_count": sum(1 for s in REQUIRED_SECTIONS if has_section(message, s)),
    }

def read_preview_gate(output_root: Path) -> tuple[Path, Path, dict[str, Any], dict[str, Any]]:
    preview_path = output_root / "B9_TELEGRAM_FR_PREVIEW_V0.json"
    gate_path = output_root / "B9_TELEGRAM_DRY_RUN_GATE_V0.json"
    return preview_path, gate_path, load_json(preview_path), load_json(gate_path)

def build_board(output_root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    preview_path, gate_path, preview, gate = read_preview_gate(output_root)
    message = get_message(preview, gate)
    status, reason = classify_gate(preview, gate)
    stats = message_stats(message)
    row = {
        "audit_version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "output_root": str(output_root),
        "preview_path": str(preview_path),
        "gate_path": str(gate_path),
        "preview_exists": preview_path.exists(),
        "gate_exists": gate_path.exists(),
        "preview_version": preview.get("version"),
        "gate_version": gate.get("version"),
        "gate_status": gate.get("gate_status"),
        "audit_status": status,
        "audit_reason": reason,
        "telegram_send_enabled": gate.get("telegram_send_enabled", preview.get("telegram_send_enabled")),
        "send_attempted": gate.get("send_attempted"),
        "dry_run_only": gate.get("dry_run_only"),
        "forbidden_hits": "|".join(forbidden_hits(message)),
        "missing_sections": "|".join(section_missing(message)),
        **stats,
        "message_candidate": message,
        "doctrine": "Le message Telegram réveille l’attention, il ne décide pas.",
    }
    summary = {
        "version": VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "rows": 1,
        "audit_status_counts": {status: 1},
        "constraints": [
            "NO_TELEGRAM_SEND",
            "NO_CREDENTIAL_TOUCH",
            "NO_TELEGRAM_MODULE_CREATION",
            "NO_EXISTING_TELEGRAM_MODULE_MODIFICATION",
            "READ_ONLY",
            "NO_DB",
            "NO_DASHBOARD_LIVE",
        ],
    }
    return [row], summary

def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fields = list(rows[0].keys()) if rows else ["audit_version"]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def md_table(rows: list[dict[str, Any]], fields: list[str]) -> str:
    if not rows:
        return "_Aucun élément._"
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for r in rows:
        vals = []
        for f in fields:
            v = str(r.get(f, "")).replace("|", "\\|").replace("\n", "<br>")
            vals.append(v)
        lines.append("| " + " | ".join(vals) + " |")
    return "\n".join(lines)

def write_md(path: Path, rows: list[dict[str, Any]], summary: Mapping[str, Any]) -> None:
    row = rows[0] if rows else {}
    text = f"""# B9 Telegram Preview Audit Board V0

```text
version = {VERSION}
audit_status = {row.get('audit_status')}
gate_status = {row.get('gate_status')}
telegram_send_enabled = {row.get('telegram_send_enabled')}
send_attempted = {row.get('send_attempted')}
dry_run_only = {row.get('dry_run_only')}
```

## Verdict

{row.get('audit_status')} — {row.get('audit_reason')}

## Board

{md_table(rows, ['audit_status','gate_status','char_count','line_count','section_count','forbidden_hits','missing_sections'])}

## Message candidat

```text
{row.get('message_candidate','')}
```

## Contraintes

{chr(10).join('- ' + x for x in summary.get('constraints', []))}

## Doctrine

Le message Telegram réveille l’attention, il ne décide pas.

## Prochaine étape

Validation humaine uniquement. Aucun envoi réel ne doit être déclenché par cette brique.
"""
    path.write_text(text, encoding="utf-8")

def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--preview-root", default="outputs/b9_telegram_fr_preview_v0")
    p.add_argument("--output-dir", default="outputs/b9_telegram_preview_audit_board_v0")
    p.add_argument("--strict-exit", action="store_true", help="Return 2 when audit is blocked. Default is non-fatal read-only report mode.")
    args = p.parse_args(argv)

    preview_root = Path(args.preview_root)
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    rows, summary = build_board(preview_root)
    csv_path = out / "B9_TELEGRAM_PREVIEW_AUDIT_BOARD_V0.csv"
    json_path = out / "B9_TELEGRAM_PREVIEW_AUDIT_BOARD_V0.json"
    md_path = out / "B9_TELEGRAM_PREVIEW_AUDIT_BOARD_V0.md"

    write_csv(csv_path, rows)
    json_path.write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
    write_md(md_path, rows, summary)

    print(f"Wrote: {csv_path}")
    print(f"Wrote: {json_path}")
    print(f"Wrote: {md_path}")
    print(f"Audit: {rows[0]['audit_status']}")
    if args.strict_exit and rows[0]["audit_status"] != "READY_FOR_HUMAN_REVIEW_NO_SEND":
        return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
