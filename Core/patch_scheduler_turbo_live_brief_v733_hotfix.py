#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import shutil
from pathlib import Path

TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
BACKUP = Path("scheduler_powerflow_turbo_wrapper.py.bak_live_brief_v733")
MARKER = "dashboard_normalize_live_brief.py"
SUCCESS_MARKER = "TURBO_V73_CYCLE_OK"

INSERTION = """
    run_step("gbpusd_live_decision", [
        sys.executable, "pf_gbpusd_live_decision_once.py",
    ])
    run_step("cockpit_live_status", [
        sys.executable, "pf_cockpit_live_status_once.py",
    ])
    run_step("powerflow_live_brief", [
        sys.executable, "pf_powerflow_live_brief_once.py",
    ])
    run_step("live_brief_normalize", [
        sys.executable, "dashboard_normalize_live_brief.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/live_brief_dashboard.json",
    ])
"""


def restore_if_needed() -> None:
    # If the failed V7.3.3 patch backup exists, restore from it first.
    if BACKUP.exists():
        shutil.copy2(BACKUP, TARGET)
        print(f"RESTORE_OK | restored scheduler from {BACKUP}")


def find_insert_position(text: str) -> int:
    marker_pos = text.find(SUCCESS_MARKER)
    if marker_pos < 0:
        # Fallback: append before end of main if possible is too risky; append near EOF as last resort.
        return len(text)

    # The previous patch broke by inserting between print( and its f-string.
    # This hotfix inserts BEFORE the whole print(...) block containing TURBO_V73_CYCLE_OK.
    prefix = text[:marker_pos]

    candidates = [
        prefix.rfind("\n    print("),
        prefix.rfind("\nprint("),
    ]
    candidates = [c for c in candidates if c >= 0]
    if candidates:
        return max(candidates) + 1

    # Fallback: insert before the line containing the marker.
    return text.rfind("\n", 0, marker_pos) + 1


def main() -> int:
    if not TARGET.exists():
        print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
        return 1

    restore_if_needed()

    text = TARGET.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        print("PATCH_OK | live brief already present after restore/check")
        return 0

    safety_backup = TARGET.with_suffix(".py.bak_live_brief_v733_hotfix")
    safety_backup.write_text(text, encoding="utf-8")

    insert_pos = find_insert_position(text)
    patched = text[:insert_pos] + INSERTION + text[insert_pos:]
    TARGET.write_text(patched, encoding="utf-8")

    print(f"PATCH_OK | scheduler patched safely | backup={safety_backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
