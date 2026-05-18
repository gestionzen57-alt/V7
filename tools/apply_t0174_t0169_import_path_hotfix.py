#!/usr/bin/env python3
"""
T0174 - T0169 Surface Adapter Import Path Hotfix V0.

Purpose:
- Locate the T0169 Reality Board Surface Adapter builder.
- Add the repository root to sys.path before root-level pf_* imports.
- Produce a clear report if the builder is missing.

Read/write behavior:
- Read-only by default.
- Writes only when --apply is provided and the target builder exists.
- No DB, dashboard, Telegram, credential, or network access.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

VERSION = "T0174_T0169_IMPORT_PATH_HOTFIX_V0"
TARGET_BASENAME = "build_t0169_b9_reality_board_surface_adapter_candidate.py"
TARGET_RELATIVE = Path("tools") / TARGET_BASENAME
REQUIRED_KEYS = ["Path(__file__).resolve().parents[1]", "sys.path.insert(0, str(ROOT))"]
ROOT_IMPORT_HINTS = [
    "from pf_t009_reality_board_surface_adapter_candidate import",
    "import pf_t009_reality_board_surface_adapter_candidate",
]

HOTFIX_BLOCK = '''from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

'''

FORBIDDEN_OUTPUT_TERMS = ["BUY", "SELL", "probability of success", "taux de réussite"]


@dataclass
class HotfixResult:
    version: str
    core_root: str
    target_relative_path: str
    target_exists: bool
    hotfix_state: str
    changed: bool
    backup_path: str
    located_candidates: list[str]
    git_tracked_candidates: list[str]
    keys_present_before: list[str]
    keys_present_after: list[str]
    technical_limits: list[str]
    forbidden_language_hits: list[str]


def run_git(core_root: Path, args: list[str]) -> list[str]:
    try:
        proc = subprocess.run(
            ["git", *args],
            cwd=str(core_root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except Exception:
        return []
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def find_worktree_candidates(core_root: Path) -> list[Path]:
    candidates: list[Path] = []
    exact = core_root / TARGET_RELATIVE
    if exact.exists():
        candidates.append(exact)
    patterns = [
        "**/build_t0169*b9*reality*board*surface*adapter*.py",
        "**/*t0169*surface*adapter*.py",
        "**/*reality_board_surface_adapter*.py",
    ]
    for pattern in patterns:
        for path in core_root.glob(pattern):
            if not path.is_file():
                continue
            parts = {part.lower() for part in path.parts}
            if ".git" in parts or "_extract" in parts:
                continue
            if path not in candidates:
                candidates.append(path)
    return candidates


def find_git_candidates(core_root: Path) -> list[str]:
    files = run_git(core_root, ["ls-files"])
    hits = []
    for name in files:
        low = name.lower().replace("\\", "/")
        if "t0169" in low and "surface" in low and low.endswith(".py"):
            hits.append(name)
        elif low.endswith(str(TARGET_RELATIVE).replace("\\", "/").lower()):
            hits.append(name)
    return sorted(set(hits))


def keys_present(text: str) -> list[str]:
    return [key for key in REQUIRED_KEYS if key in text]


def is_patched(text: str) -> bool:
    return all(key in text for key in REQUIRED_KEYS)


def insert_hotfix(text: str) -> str:
    if is_patched(text):
        return text

    lines = text.splitlines(keepends=True)
    insert_at = 0

    # Preserve shebang and coding comment.
    if lines and lines[0].startswith("#!"):
        insert_at = 1
    if len(lines) > insert_at and "coding" in lines[insert_at].lower():
        insert_at += 1

    # If a module docstring is present at the top, insert after it.
    probe = "".join(lines[insert_at:insert_at + 8])
    stripped = probe.lstrip()
    if stripped.startswith('"""') or stripped.startswith("'''"):
        quote = '"""' if stripped.startswith('"""') else "'''"
        doc_start_line = insert_at
        # If docstring starts later due to blank lines, move to first nonblank.
        for idx in range(insert_at, len(lines)):
            if lines[idx].strip():
                doc_start_line = idx
                break
        found_end = False
        for idx in range(doc_start_line, len(lines)):
            if quote in lines[idx] and idx != doc_start_line:
                insert_at = idx + 1
                found_end = True
                break
            if idx == doc_start_line and lines[idx].count(quote) >= 2:
                insert_at = idx + 1
                found_end = True
                break
        if not found_end:
            insert_at = doc_start_line

    # Prefer inserting immediately before the first root pf_* import.
    for idx, line in enumerate(lines):
        if any(hint in line for hint in ROOT_IMPORT_HINTS):
            insert_at = idx
            break

    return "".join(lines[:insert_at]) + HOTFIX_BLOCK + "".join(lines[insert_at:])


def scan_forbidden_output_terms(result: HotfixResult) -> list[str]:
    # Scan the generated human-readable fields only, not the source code.
    visible_text = "\n".join(
        [
            result.hotfix_state,
            "\n".join(result.technical_limits),
        ]
    )
    hits = []
    low_visible = visible_text.lower()
    for term in FORBIDDEN_OUTPUT_TERMS:
        if term.lower() in low_visible:
            hits.append(term)
    return hits


def write_outputs(output_dir: Path, result: HotfixResult) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    result.forbidden_language_hits = scan_forbidden_output_terms(result)

    json_path = output_dir / "T0174_T0169_IMPORT_PATH_HOTFIX_REPORT.json"
    json_path.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2), encoding="utf-8")

    md_lines = [
        "# T0174 — T0169 Import Path Hotfix Report",
        "",
        f"Version : `{result.version}`",
        f"State : `{result.hotfix_state}`",
        f"Target : `{result.target_relative_path}`",
        f"Target exists : `{result.target_exists}`",
        f"Changed : `{result.changed}`",
        "",
        "## Located candidates",
    ]
    if result.located_candidates:
        md_lines.extend([f"- `{item}`" for item in result.located_candidates])
    else:
        md_lines.append("- Aucun builder T0169 trouvé dans le working tree courant.")
    md_lines.extend(["", "## Technical limits"])
    md_lines.extend([f"- {item}" for item in result.technical_limits] or ["- Aucune limite technique bloquante."])
    md_lines.extend([
        "",
        "## Doctrine",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "Ce hotfix corrige un contrat d'import CLI ; il ne déclenche aucune action live.",
    ])
    (output_dir / "T0174_T0169_IMPORT_PATH_HOTFIX_REPORT.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    csv_path = output_dir / "T0174_T0169_IMPORT_PATH_HOTFIX_ROWS.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["key", "value"])
        writer.writeheader()
        for key, value in asdict(result).items():
            writer.writerow({"key": key, "value": json.dumps(value, ensure_ascii=False) if isinstance(value, (list, dict)) else value})


def apply_or_report(core_root: Path, output_dir: Path, apply: bool) -> HotfixResult:
    core_root = core_root.resolve()
    worktree_candidates = find_worktree_candidates(core_root)
    git_candidates = find_git_candidates(core_root)

    target = core_root / TARGET_RELATIVE
    if not target.exists() and worktree_candidates:
        target = worktree_candidates[0]

    located_rel = []
    for path in worktree_candidates:
        try:
            located_rel.append(str(path.relative_to(core_root)))
        except ValueError:
            located_rel.append(str(path))

    if not target.exists():
        result = HotfixResult(
            version=VERSION,
            core_root=str(core_root),
            target_relative_path=str(TARGET_RELATIVE).replace("\\", "/"),
            target_exists=False,
            hotfix_state="BLOCKED_T0169_BUILDER_NOT_FOUND",
            changed=False,
            backup_path="",
            located_candidates=located_rel,
            git_tracked_candidates=git_candidates,
            keys_present_before=[],
            keys_present_after=[],
            technical_limits=[
                "Le builder T0169 n'est pas présent dans la branche ou le working tree courant.",
                "Installer ou checkout la branche T0169 avant d'appliquer le hotfix import path.",
                "Aucune modification source n'a été appliquée.",
            ],
            forbidden_language_hits=[],
        )
        write_outputs(output_dir, result)
        return result

    text = target.read_text(encoding="utf-8", errors="replace")
    before = keys_present(text)
    if is_patched(text):
        result = HotfixResult(
            version=VERSION,
            core_root=str(core_root),
            target_relative_path=str(target.relative_to(core_root)).replace("\\", "/"),
            target_exists=True,
            hotfix_state="ALREADY_PATCHED",
            changed=False,
            backup_path="",
            located_candidates=located_rel,
            git_tracked_candidates=git_candidates,
            keys_present_before=before,
            keys_present_after=before,
            technical_limits=["Le bloc sys.path racine est déjà présent dans le builder T0169."],
            forbidden_language_hits=[],
        )
        write_outputs(output_dir, result)
        return result

    if not apply:
        result = HotfixResult(
            version=VERSION,
            core_root=str(core_root),
            target_relative_path=str(target.relative_to(core_root)).replace("\\", "/"),
            target_exists=True,
            hotfix_state="PATCH_AVAILABLE_NOT_APPLIED",
            changed=False,
            backup_path="",
            located_candidates=located_rel,
            git_tracked_candidates=git_candidates,
            keys_present_before=before,
            keys_present_after=before,
            technical_limits=["Exécuter avec --apply pour appliquer le bloc sys.path racine."],
            forbidden_language_hits=[],
        )
        write_outputs(output_dir, result)
        return result

    patched = insert_hotfix(text)
    backup = target.with_suffix(target.suffix + ".t0174_backup")
    backup.write_text(text, encoding="utf-8")
    target.write_text(patched, encoding="utf-8")
    after = keys_present(patched)
    result = HotfixResult(
        version=VERSION,
        core_root=str(core_root),
        target_relative_path=str(target.relative_to(core_root)).replace("\\", "/"),
        target_exists=True,
        hotfix_state="PATCH_APPLIED",
        changed=True,
        backup_path=str(backup.relative_to(core_root)).replace("\\", "/"),
        located_candidates=located_rel,
        git_tracked_candidates=git_candidates,
        keys_present_before=before,
        keys_present_after=after,
        technical_limits=["Patch import path appliqué. Vérifier le CLI sample T0169 après installation."],
        forbidden_language_hits=[],
    )
    write_outputs(output_dir, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T0174 T0169 import path hotfix")
    parser.add_argument("--core-root", default=".")
    parser.add_argument("--output-dir", default="outputs/t0174_t0169_import_path_hotfix_v0")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    args = parser.parse_args(argv)

    result = apply_or_report(Path(args.core_root), Path(args.output_dir), args.apply)
    if args.print_json:
        print(json.dumps(asdict(result), ensure_ascii=False, indent=2))

    # Missing builder is not an installer failure; it is an explicit blocked state.
    if result.hotfix_state in {"BLOCKED_T0169_BUILDER_NOT_FOUND", "PATCH_AVAILABLE_NOT_APPLIED"}:
        return 0
    if result.forbidden_language_hits:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
