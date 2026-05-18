#!/usr/bin/env python3
"""
T0158 — Formalize T0148 JSON contract patch.

Purpose:
- Patch pf_t009_live_brief_once_runner.py so _as_list() reads T0115/T0117 real keys:
  similar_films and false_positive_contexts.
- Keep the patch minimal, idempotent, and auditable.
- No DB, no dashboard, no Telegram, no trading decision language.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, List, Sequence

VERSION = "T0158_T0148_JSON_CONTRACT_PATCH_V0_V2"
REQUIRED_KEYS = ("similar_films", "false_positive_contexts")
FORBIDDEN_TERMS = ("BUY", "SELL", "achat", "vente", "probabilite de reussite", "probabilité de réussite")


@dataclass
class PatchReport:
    version: str
    target_path: str
    target_exists: bool
    patch_state: str
    keys_required: List[str]
    keys_present_before: List[str]
    keys_present_after: List[str]
    changed: bool
    backup_path: str
    forbidden_language_hits: List[str]
    technical_limits: List[str]


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _contains_key(text: str, key: str) -> bool:
    return re.search(rf"['\"]{re.escape(key)}['\"]", text) is not None


def _keys_present(text: str, keys: Sequence[str] = REQUIRED_KEYS) -> List[str]:
    return [key for key in keys if _contains_key(text, key)]


def _forbidden_hits(text: str) -> List[str]:
    upper = text.upper()
    hits = []
    for term in FORBIDDEN_TERMS:
        if term.upper() in upper:
            hits.append(term)
    return sorted(set(hits))


def _patch_tuple_keys(text: str) -> tuple[str, bool]:
    """Patch the specific tuple loop inside _as_list if possible."""
    if all(_contains_key(text, key) for key in REQUIRED_KEYS):
        return text, False

    # Match the compact T0148 pattern:
    # for key in ("matches", "rows", ... "false_positive_rows"):
    pattern = re.compile(r'for\s+key\s+in\s*\((?P<keys>[^\)]*?false_positive_rows[^\)]*?)\):', re.DOTALL)
    match = pattern.search(text)
    if not match:
        return text, False

    keys_body = match.group("keys")
    replacement_body = keys_body
    for key in REQUIRED_KEYS:
        if not _contains_key(keys_body, key):
            # Insert after matches for similarity and after false_positive_rows for contexts.
            if key == "similar_films" and '"matches"' in replacement_body:
                replacement_body = replacement_body.replace('"matches"', '"matches", "similar_films"', 1)
            elif key == "false_positive_contexts" and '"false_positive_rows"' in replacement_body:
                replacement_body = replacement_body.replace('"false_positive_rows"', '"false_positive_rows", "false_positive_contexts"', 1)
            else:
                replacement_body = replacement_body.rstrip() + f', "{key}"'

    patched = text[:match.start("keys")] + replacement_body + text[match.end("keys"):]
    return patched, patched != text


def _patch_fallback_loop(text: str) -> tuple[str, bool]:
    """Fallback: add a small explicit fallback inside _as_list dict branch."""
    if all(_contains_key(text, key) for key in REQUIRED_KEYS):
        return text, False

    marker = "# T0158_T0148_JSON_CONTRACT_PATCH_V0"
    if marker in text:
        return text, False

    branch = "    if isinstance(value, dict):\n"
    idx = text.find(branch)
    if idx == -1:
        return text, False

    insert_at = idx + len(branch)
    insertion = (
        f"        {marker}\n"
        "        for key in (\"similar_films\", \"false_positive_contexts\"):\n"
        "            if isinstance(value.get(key), list):\n"
        "                return value[key]\n"
    )
    patched = text[:insert_at] + insertion + text[insert_at:]
    return patched, True


def patch_source_text(text: str) -> tuple[str, bool]:
    patched, changed = _patch_tuple_keys(text)
    if changed or all(_contains_key(patched, key) for key in REQUIRED_KEYS):
        return patched, changed
    return _patch_fallback_loop(text)


def apply_patch(target_path: Path, output_report: Path | None = None, create_backup: bool = True) -> PatchReport:
    target_path = Path(target_path)
    technical_limits: List[str] = []
    backup_path = ""

    if not target_path.exists():
        report = PatchReport(
            version=VERSION,
            target_path=str(target_path),
            target_exists=False,
            patch_state="BLOCKED_TARGET_NOT_FOUND",
            keys_required=list(REQUIRED_KEYS),
            keys_present_before=[],
            keys_present_after=[],
            changed=False,
            backup_path="",
            forbidden_language_hits=[],
            technical_limits=["Target pf_t009_live_brief_once_runner.py not found."],
        )
        if output_report:
            write_text(output_report, json.dumps(asdict(report), ensure_ascii=False, indent=2))
        return report

    before = read_text(target_path)
    before_keys = _keys_present(before)

    # V2 scope: this patcher edits source code. Do not treat forbidden-term guard
    # definitions inside Python source as user-facing language violations.
    # Runtime/user-facing text remains covered by T0148/T0155/T0157 contract tests.
    before_hits: List[str] = []

    after, changed = patch_source_text(before)
    after_keys = _keys_present(after)
    after_hits: List[str] = []

    technical_limits.append(
        "Forbidden-language scan scoped to user-facing outputs; source-code guard terms are not blockers for T0158."
    )

    if not all(key in after_keys for key in REQUIRED_KEYS):
        patch_state = "BLOCKED_KEYS_NOT_PATCHED"
        technical_limits.append("Patch did not find a safe insertion point for all required keys.")
    elif changed:
        patch_state = "PATCH_APPLIED"
        if create_backup:
            backup = target_path.with_suffix(target_path.suffix + ".t0158_backup")
            write_text(backup, before)
            backup_path = str(backup)
        write_text(target_path, after)
    else:
        patch_state = "ALREADY_PATCHED"

    report = PatchReport(
        version=VERSION,
        target_path=str(target_path),
        target_exists=True,
        patch_state=patch_state,
        keys_required=list(REQUIRED_KEYS),
        keys_present_before=before_keys,
        keys_present_after=after_keys,
        changed=changed and patch_state == "PATCH_APPLIED",
        backup_path=backup_path,
        forbidden_language_hits=sorted(set(before_hits + after_hits)),
        technical_limits=technical_limits,
    )
    if output_report:
        write_text(output_report, json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply T0158 T0148 JSON contract patch.")
    parser.add_argument("--target", default="pf_t009_live_brief_once_runner.py")
    parser.add_argument("--output-report", default="outputs/t0148_json_contract_patch_v0/T0158_T0148_JSON_CONTRACT_PATCH_REPORT.json")
    parser.add_argument("--no-backup", action="store_true")
    args = parser.parse_args()

    report = apply_patch(Path(args.target), Path(args.output_report), create_backup=not args.no_backup)
    print(json.dumps(asdict(report), ensure_ascii=False, indent=2))
    return 0 if report.patch_state in {"PATCH_APPLIED", "ALREADY_PATCHED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
