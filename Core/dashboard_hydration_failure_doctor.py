#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.2 — Dashboard Hydration Failure Doctor

Reads the latest logs/dashboard_hydrate_*.log and extracts failed runner blocks.
It does not modify engine files or powerflow.db.
"""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple


WARN_RE = re.compile(r"\[(?P<time>[^\]]+)\]\s+WARN\s+(?P<name>.*?)\s+-\s+exit code\s+(?P<code>\d+)")
RUN_RE = re.compile(r"\[(?P<time>[^\]]+)\]\s+RUN\s+(?P<name>.*?)\s+-\s+(?P<cmd>.+)")
OK_RE = re.compile(r"\[(?P<time>[^\]]+)\]\s+OK\s+(?P<name>.*)")


def latest_log(log_dir: Path) -> Path | None:
    logs = sorted(log_dir.glob("dashboard_hydrate_*.log"), key=lambda p: p.stat().st_mtime, reverse=True)
    return logs[0] if logs else None


def parse_blocks(lines: List[str]) -> List[Dict[str, object]]:
    blocks: List[Dict[str, object]] = []
    current: Dict[str, object] | None = None

    for line in lines:
        run = RUN_RE.search(line)
        if run:
            if current:
                blocks.append(current)
            current = {
                "name": run.group("name").strip(),
                "cmd": run.group("cmd").strip(),
                "status": "RUN",
                "exit_code": None,
                "output": [],
            }
            continue

        if current is not None:
            warn = WARN_RE.search(line)
            ok = OK_RE.search(line)
            if warn and warn.group("name").strip() == current["name"]:
                current["status"] = "WARN"
                current["exit_code"] = warn.group("code")
                blocks.append(current)
                current = None
                continue
            if ok and ok.group("name").strip() == current["name"]:
                current["status"] = "OK"
                blocks.append(current)
                current = None
                continue

            if line.startswith("    "):
                current["output"].append(line.strip())

    if current:
        blocks.append(current)

    return blocks


def classify_output(output: List[str]) -> str:
    text = "\n".join(output).lower()

    if "unrecognized arguments" in text or "error: argument" in text:
        return "CLI_ARGUMENT_MISMATCH"
    if "no such option" in text or "usage:" in text:
        return "CLI_SIGNATURE_MISMATCH"
    if "no such file" in text or "cannot find" in text:
        return "MISSING_FILE_OR_PATH"
    if "sqlite" in text or "database" in text:
        return "DB_SCHEMA_OR_ACCESS"
    if "importerror" in text or "modulenotfounderror" in text:
        return "PYTHON_IMPORT_DEPENDENCY"
    if "typeerror" in text or "attributeerror" in text or "keyerror" in text:
        return "RUNTIME_SCHEMA_DRIFT"
    if not text.strip():
        return "NO_STDERR_CAPTURED"
    return "RUNNER_RUNTIME_ERROR"


def suggested_action(name: str, classification: str) -> str:
    if classification in {"CLI_ARGUMENT_MISMATCH", "CLI_SIGNATURE_MISMATCH"}:
        return "Run this runner with --help, then update run_dashboard_hydrate_outputs.ps1 arguments only."
    if classification == "DB_SCHEMA_OR_ACCESS":
        return "Inspect DB schema expectations. Do not write DB; adapt runner args/output path if needed."
    if classification == "PYTHON_IMPORT_DEPENDENCY":
        return "Check local Python environment/dependencies."
    if classification == "RUNTIME_SCHEMA_DRIFT":
        return "Capture traceback; patch runner wrapper or output normalizer, not pf_* first."
    if classification == "NO_STDERR_CAPTURED":
        return "Re-run runner manually to capture full error."
    return "Open the runner error block; classify before patching."


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".", help="Core root")
    parser.add_argument("--log", default="", help="Specific hydration log path")
    parser.add_argument("--md-out", default="output/DASHBOARD_HYDRATION_FAILURE_DOCTOR.md")
    parser.add_argument("--json-out", default="output/dashboard_hydration_failure_doctor.json")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    log_path = Path(args.log).resolve() if args.log else latest_log(root / "logs")

    out_md = root / args.md_out
    out_json = root / args.json_out
    out_md.parent.mkdir(parents=True, exist_ok=True)

    if log_path is None or not log_path.exists():
        out_md.write_text("# Dashboard Hydration Failure Doctor\n\nNo hydration log found.\n", encoding="utf-8")
        return 1

    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    blocks = parse_blocks(lines)
    failed = [b for b in blocks if b.get("status") == "WARN"]

    rows: List[Tuple[str, str, str, str, str]] = []
    for b in failed:
        output = b.get("output", [])
        classification = classify_output(output if isinstance(output, list) else [])
        rows.append((
            str(b.get("name")),
            str(b.get("exit_code")),
            classification,
            str(b.get("cmd")),
            suggested_action(str(b.get("name")), classification),
        ))

    md = []
    md.append("# DASHBOARD HYDRATION FAILURE DOCTOR — PowerFlow V7.2")
    md.append("")
    md.append(f"Generated UTC : {datetime.now(timezone.utc).isoformat()}")
    md.append(f"Log analysed  : `{log_path}`")
    md.append("")
    md.append("## Summary")
    md.append("")
    md.append(f"- Steps parsed : {len(blocks)}")
    md.append(f"- WARN/failed  : {len(failed)}")
    md.append("")
    md.append("## Failed runners")
    md.append("")
    md.append("| Runner | Exit | Classification | Suggested action |")
    md.append("|---|---:|---|---|")
    for name, code, classification, cmd, action in rows:
        md.append(f"| {name} | {code} | {classification} | {action} |")

    md.append("")
    md.append("## Commands to inspect manually")
    md.append("")
    for name, code, classification, cmd, action in rows:
        md.append(f"### {name}")
        md.append("")
        md.append("```powershell")
        md.append(cmd.replace("python ", "python .\\", 1) if cmd.startswith("python ") else cmd)
        md.append("```")
        if classification in {"CLI_ARGUMENT_MISMATCH", "CLI_SIGNATURE_MISMATCH"}:
            runner = cmd.split()[1] if len(cmd.split()) > 1 else ""
            if runner:
                md.append("")
                md.append("```powershell")
                md.append(f"python .\\{runner} --help")
                md.append("```")
        md.append("")

    md.append("## Raw error excerpts")
    md.append("")
    for b in failed:
        md.append(f"### {b.get('name')}")
        md.append("")
        md.append("```text")
        output = b.get("output", [])
        if isinstance(output, list) and output:
            md.extend(output[-40:])
        else:
            md.append("(no stderr/stdout captured)")
        md.append("```")
        md.append("")

    out_md.write_text("\n".join(md), encoding="utf-8")

    import json
    payload = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "log": str(log_path),
        "steps_parsed": len(blocks),
        "failed_count": len(failed),
        "failed": [
            {
                "name": r[0],
                "exit_code": r[1],
                "classification": r[2],
                "command": r[3],
                "suggested_action": r[4],
            }
            for r in rows
        ],
    }
    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Dashboard hydration failure doctor wrote: {out_md}")
    print(f"JSON: {out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
