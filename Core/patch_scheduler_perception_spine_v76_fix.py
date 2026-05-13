#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix/patch scheduler_powerflow_turbo_wrapper.py for Perception Spine V7.6 Turbo.

Safe behavior:
- If scheduler is currently broken and a backup from the previous patch exists,
  restore the backup first.
- Remove any prior Perception Spine injected block between markers.
- Insert a clean block before trader_journal_j1, or before final TURBO OK print.
"""
from __future__ import annotations

import argparse
import py_compile
import re
import shutil
from pathlib import Path

START = "    # --- PERCEPTION SPINE V7.6 TURBO START ---\n"
END = "    # --- PERCEPTION SPINE V7.6 TURBO END ---\n"

BLOCK = f"""{START}    for _spine_symbol in symbols.split(\",\"):\n        _spine_symbol = _spine_symbol.strip().upper()\n        if not _spine_symbol:\n            continue\n        run_step(f\"perception_spine_{{_spine_symbol.lower()}}\", [\n            sys.executable, \"pf_perception_spine_once.py\",\n            \"--symbol\", _spine_symbol,\n        ], core, required=False)\n{END}\n"""


def _compiles(path: Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True)
        return True
    except Exception:
        return False


def _strip_old_blocks(text: str) -> str:
    # Remove clean marker blocks.
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END) + r"\n?", re.DOTALL)
    text = pattern.sub("", text)

    # Remove a likely malformed block from the first mention of perception_spine until
    # the next known run_step or final print. Conservative fallback for previous bad patch.
    lines = text.splitlines(True)
    out = []
    skipping = False
    for line in lines:
        if (not skipping) and ("pf_perception_spine_once.py" in line or "perception_spine_" in line):
            skipping = True
            continue
        if skipping:
            stripped = line.lstrip()
            if stripped.startswith('run_step("trader_journal_j1"') or stripped.startswith('print(') or stripped.startswith('return 0'):
                skipping = False
                out.append(line)
            continue
        out.append(line)
    return "".join(out)


def patch_scheduler(path: Path) -> None:
    backup = path.with_name(path.name + ".bak_perception_spine_v76_turbo")

    # If current file is broken and backup exists, restore the backup first.
    if backup.exists() and not _compiles(path):
        shutil.copy2(backup, path)
        print(f"[OK] restored broken scheduler from {backup.name}")

    text = path.read_text(encoding="utf-8")
    text = _strip_old_blocks(text)

    # Prefer to insert before the trader journal tail, still inside main().
    anchor = '    run_step("trader_journal_j1", ['
    if anchor in text:
        text = text.replace(anchor, BLOCK + anchor, 1)
    else:
        # Fallback: insert before final TURBO OK print.
        anchor2 = '    print(\n        "TURBO_V73_CYCLE_OK | "'
        if anchor2 not in text:
            raise RuntimeError("Could not find insertion anchor in scheduler")
        text = text.replace(anchor2, BLOCK + anchor2, 1)

    # Write backup of pre-fix if not already present from v1.
    fix_backup = path.with_name(path.name + ".bak_perception_spine_v76_fix_prewrite")
    if not fix_backup.exists():
        shutil.copy2(path, fix_backup)

    path.write_text(text, encoding="utf-8")

    try:
        py_compile.compile(str(path), doraise=True)
    except Exception as exc:
        # restore last prewrite backup to avoid leaving scheduler broken
        shutil.copy2(fix_backup, path)
        raise RuntimeError(f"patched scheduler did not compile; restored prewrite backup: {exc}") from exc

    print(f"[OK] patched {path}")
    print(f"[OK] compile passed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--scheduler", default="scheduler_powerflow_turbo_wrapper.py")
    args = parser.parse_args()
    patch_scheduler(Path(args.scheduler))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
