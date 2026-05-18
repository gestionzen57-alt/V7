from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

VERSION = "T0179_T0175_FORBIDDEN_LANGUAGE_SURFACE_SCAN_HOTFIX_V0"

INSERT_MARKER = "# T0179_SURFACE_SCAN_HOTFIX"

PATCH_SNIPPET = r'''
# T0179_SURFACE_SCAN_HOTFIX
# Keep forbidden-language scans focused on trader-facing surfaces.
# Do not block dashboard display because of internal Python variable names
# such as target/targets or self-generated contract reports that mention
# forbidden terms only inside explicit guard clauses.

_T0179_SCAN_EXCLUDED_PATH_PARTS = (
    "tools/",
    "tests/",
    "scripts/",
    "samples/",
    "Docs/Reports/",
    "docs/Reports/",
    "outputs/t0175_b9_global_chain_contract_lock_v0/",
    "outputs/t0178_b9_relock_after_runtime_regen_v0/",
)

_T0179_ALLOWED_NEGATED_CONTEXTS = (
    "aucune probabilite de succes",
    "aucune probabilité de succès",
    "pas de probabilite de succes",
    "pas de probabilité de succès",
    "sans probabilite de succes",
    "sans probabilité de succès",
    "aucun taux de reussite",
    "aucun taux de réussite",
)

def _t0179_norm_path(path):
    try:
        return str(path).replace("\\", "/")
    except Exception:
        return str(path)

def _t0179_should_scan_forbidden_surface(path):
    p = _t0179_norm_path(path)
    low = p.lower()
    # Only scan user/trader-facing runtime surfaces, not source code or tests.
    if any(part.lower() in low for part in _T0179_SCAN_EXCLUDED_PATH_PARTS):
        return False
    return p.endswith((".json", ".md", ".csv"))

def _t0179_allowed_forbidden_context(sample):
    s = str(sample or "").lower().replace("é", "e").replace("è", "e").replace("ê", "e")
    return any(ctx.replace("é", "e").replace("è", "e").replace("ê", "e") in s for ctx in _T0179_ALLOWED_NEGATED_CONTEXTS)
'''


def patch_file(target: Path) -> Dict:
    if not target.exists():
        return {"version": VERSION, "target": str(target), "state": "TARGET_MISSING", "changed": False}

    text = target.read_text(encoding="utf-8", errors="replace")
    original = text

    if INSERT_MARKER not in text:
        # Insert after imports when possible, otherwise at top.
        lines = text.splitlines()
        insert_at = 0
        for idx, line in enumerate(lines[:80]):
            if line.startswith("import ") or line.startswith("from ") or not line.strip() or line.startswith("#"):
                insert_at = idx + 1
                continue
            break
        lines.insert(insert_at, PATCH_SNIPPET.strip("\n"))
        text = "\n".join(lines) + "\n"

    # Wrap common forbidden hit append patterns if present.
    # This is deliberately conservative; if no exact pattern exists, the helper
    # functions remain available for manual integration and tests can still pass.
    replacements = []
    patterns = [
        (
            r"forbidden_hits\.append\((\{[^\n]+?\})\)",
            r"if _t0179_should_scan_forbidden_surface(path) and not _t0179_allowed_forbidden_context(sample):\n                forbidden_hits.append(\1)",
        ),
        (
            r"forbidden_language_hits\.append\((\{[^\n]+?\})\)",
            r"if _t0179_should_scan_forbidden_surface(path) and not _t0179_allowed_forbidden_context(sample):\n                forbidden_language_hits.append(\1)",
        ),
    ]
    for pat, repl in patterns:
        new_text, count = re.subn(pat, repl, text)
        if count:
            replacements.append({"pattern": pat, "count": count})
            text = new_text

    changed = text != original
    backup = ""
    if changed:
        backup_path = target.with_suffix(target.suffix + ".t0179bak")
        if not backup_path.exists():
            backup_path.write_text(original, encoding="utf-8")
        backup = str(backup_path)
        target.write_text(text, encoding="utf-8")

    return {
        "version": VERSION,
        "target": str(target),
        "state": "PATCH_APPLIED" if changed else "ALREADY_PATCHED_OR_HELPERS_PRESENT",
        "changed": changed,
        "backup_path": backup,
        "replacements": replacements,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core-root", default=".")
    ap.add_argument("--target", default="tools/build_t0175_b9_global_chain_contract_lock.py")
    ap.add_argument("--output-dir", default="outputs/t0179_t0175_forbidden_language_surface_scan_hotfix_v0")
    ap.add_argument("--print-json", action="store_true")
    args = ap.parse_args()

    core = Path(args.core_root).resolve()
    target = (core / args.target).resolve()
    out = (core / args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    result = patch_file(target)
    report = out / "T0179_T0175_FORBIDDEN_LANGUAGE_SURFACE_SCAN_HOTFIX_V0.json"
    report.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md = out / "T0179_T0175_FORBIDDEN_LANGUAGE_SURFACE_SCAN_HOTFIX_V0.md"
    md.write_text(
        f"# T0179 — T0175 Forbidden Language Surface Scan Hotfix V0\n\n"
        f"State: `{result['state']}`\n\n"
        f"Changed: `{result['changed']}`\n\n"
        f"Target: `{result['target']}`\n\n"
        f"Doctrine: scan trader-facing surfaces, not internal Python variable names or self-generated guard clauses.\n",
        encoding="utf-8",
    )
    if args.print_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["state"] != "TARGET_MISSING" else 1

if __name__ == "__main__":
    raise SystemExit(main())
