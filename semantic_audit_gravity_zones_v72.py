#!/usr/bin/env python3
"""
PowerFlow V7.2 — Semantic Audit Scanner: Gravity / Zones / Footprints

Run from repo root:
    python semantic_audit_gravity_zones_v72.py

Outputs:
    output/semantic_audit_gravity_zones_report.json
    output/semantic_audit_gravity_zones_report.md

This scanner is read-only. It does not modify Core files.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any


TARGET_FILES = [
    "Core/pf_spearman_gravity.py",
    "Core/run_spearman_gravity_once.py",
    "Core/pf_relational_gravity_bridge.py",
    "Core/pf_relational_gravity_probe.py",
    "Core/pf_orchestral_gravity_v02.py",
    "Core/pf_confluence_gravity.py",
    "Core/pf_confluence_elastic.py",
    "Core/pf_zone_dynamics.py",
    "Core/pf_temporal_node_state.py",
    "Core/pf_flow_nodes.py",
    "Core/pf_behavioral_alert_mapper.py",
    "Core/pf_memory_engine.py",
    "Core/pf_scene_registry.py",
    "Core/pf_memory_scene_enrichment.py",
]

PATTERNS = {
    "gravity_core": [
        r"\bspearman\b", r"\brho\b", r"\bSYNCHRO\b", r"\bDIVERGENT\b",
        r"\bNEUTRAL\b", r"\bCODEPENDANT_EXTREME\b", r"\bDIVERGENT_EXTREME\b",
        r"\bMIXED_PROBABILISTE\b",
    ],
    "leader_follower": [
        r"\bleader\b", r"\bfollower\b", r"\bantagon", r"\bcoalition\b",
        r"\bcrossing\b", r"\borchestral\b",
    ],
    "zone_core": [
        r"\bzone\b", r"\bEIE\b", r"\bEWZ\b", r"\bENZ\b", r"\bZNE\b",
        r"\bPRE_EXTREME\b", r"\bEARLY_EXTREME\b", r"\bACCUMULAT", r"\bRUPTURE\b",
        r"\belastic\b", r"\bnode\b",
    ],
    "scene_memory": [
        r"\bscene_id\b", r"\bscene_family\b", r"\bmemory_tuple\b",
        r"\boutcome\b", r"\bbars_to_move\b", r"\bcompression_qualification\b",
    ],
    "institutional_red_flags": [
        r"\binstitution", r"\bsmart money\b", r"\bbank(s)?\b",
        r"\border.?flow\b", r"\bBUY\b", r"\bSELL\b",
    ],
    "classical_zone_red_flags": [
        r"\bsupport\b", r"\bresistance\b", r"\border block\b",
        r"\bsupply\b", r"\bdemand\b", r"\boverbought\b", r"\boversold\b",
    ],
    "architecture_red_flags": [
        r"import\s+cockpit_", r"from\s+cockpit_", r"import\s+telegram_",
        r"sqlite3\.connect\(.*mode=rw", r"INSERT\s+INTO", r"UPDATE\s+",
        r"DELETE\s+FROM",
    ],
}


def read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def scan_file(path: Path, text: str) -> Dict[str, Any]:
    lines = text.splitlines()
    result: Dict[str, Any] = {
        "path": str(path),
        "exists": True,
        "line_count": len(lines),
        "matches": {},
        "red_flags": [],
    }

    for group, patterns in PATTERNS.items():
        hits = []
        for idx, line in enumerate(lines, start=1):
            for pattern in patterns:
                if re.search(pattern, line, flags=re.IGNORECASE):
                    hits.append({
                        "line": idx,
                        "pattern": pattern,
                        "text": line.strip()[:240],
                    })
        result["matches"][group] = hits[:80]

        if group.endswith("red_flags") and hits:
            result["red_flags"].append(group)

    return result


def classify_findings(file_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
    summary = defaultdict(int)
    red_flags = defaultdict(list)

    for report in file_reports:
        if not report.get("exists"):
            summary["missing_files"] += 1
            continue

        for group, hits in report.get("matches", {}).items():
            if hits:
                summary[f"files_with_{group}"] += 1

        for flag in report.get("red_flags", []):
            red_flags[flag].append(report["path"])

    conclusions = []

    if summary.get("files_with_gravity_core", 0):
        conclusions.append("B5/RG gravity vocabulary found.")
    if summary.get("files_with_leader_follower", 0):
        conclusions.append("Leader/follower vocabulary found. Verify it is not inferred from rho alone.")
    if summary.get("files_with_zone_core", 0):
        conclusions.append("Zone/EIE/node vocabulary found.")
    if red_flags:
        conclusions.append("Red flags found. Review manually before Lab V7.2.")

    return {
        "summary": dict(summary),
        "red_flags": dict(red_flags),
        "conclusions": conclusions,
    }


def render_markdown(report: Dict[str, Any]) -> str:
    lines = [
        "# PowerFlow V7.2 — Semantic Audit Scanner Report",
        "",
        f"**Generated at:** {report['generated_at']}",
        "",
        "## Summary",
        "",
    ]

    for k, v in sorted(report["classification"]["summary"].items()):
        lines.append(f"- `{k}`: {v}")

    lines += ["", "## Conclusions", ""]
    for item in report["classification"]["conclusions"]:
        lines.append(f"- {item}")

    lines += ["", "## Red flags", ""]
    red_flags = report["classification"]["red_flags"]
    if not red_flags:
        lines.append("- No red flags detected by simple scanner.")
    else:
        for flag, files in sorted(red_flags.items()):
            lines.append(f"### {flag}")
            for f in files:
                lines.append(f"- `{f}`")

    lines += ["", "## Files", ""]
    for file_report in report["files"]:
        lines.append(f"### {file_report['path']}")
        if not file_report.get("exists"):
            lines.append("- Missing")
            continue
        lines.append(f"- Lines: {file_report['line_count']}")
        if file_report.get("red_flags"):
            lines.append(f"- Red flags: {', '.join(file_report['red_flags'])}")
        for group, hits in file_report.get("matches", {}).items():
            if hits:
                lines.append(f"- `{group}` hits: {len(hits)}")
                for hit in hits[:8]:
                    lines.append(f"  - L{hit['line']}: `{hit['text']}`")

    lines += [
        "",
        "## Manual review checklist",
        "",
        "- Verify B5 does not infer leader/follower from Spearman rho alone.",
        "- Verify no BUY/SELL or trade-valid language is emitted by pf_* modules.",
        "- Verify zone logic is behavioral, not support/resistance classical labeling.",
        "- Verify structured-flow footprints remain candidates with technical_risks.",
        "- Verify Lab V7.2 will read, not modify, DB / queues.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    root = Path.cwd()
    file_reports = []

    for rel in TARGET_FILES:
        path = root / rel
        text = read_file(path)
        if text is None:
            file_reports.append({"path": rel, "exists": False})
        else:
            file_reports.append(scan_file(Path(rel), text))

    report = {
        "valid": True,
        "method": "semantic_audit_gravity_zones_scanner_v72",
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "files": file_reports,
        "classification": classify_findings(file_reports),
        "no_code_modified": True,
        "no_db_write": True,
    }

    out_dir = root / "output"
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / "semantic_audit_gravity_zones_report.json"
    md_path = out_dir / "semantic_audit_gravity_zones_report.md"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")

    print(json.dumps({
        "status": "OK",
        "json": str(json_path),
        "markdown": str(md_path),
        "red_flags": report["classification"]["red_flags"],
    }, indent=2, ensure_ascii=False))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
