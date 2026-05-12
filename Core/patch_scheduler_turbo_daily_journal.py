#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
MARKER = "run_daily_journal_all_once.py"


def main() -> int:
    if not TARGET.exists():
        print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing"); return 1
    text = TARGET.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        print("PATCH_OK | daily journal already present"); return 0
    backup = TARGET.with_suffix(".py.bak_daily_journal_v732")
    backup.write_text(text, encoding="utf-8")
    insertion = '''
    run_step("daily_journal_all", [
        sys.executable, "run_daily_journal_all_once.py",
        "--db", "powerflow.db",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/daily_journal.json",
    ])
    run_step("daily_journal_normalize", [
        sys.executable, "dashboard_normalize_daily_journal.py",
        "--input", "output/dashboard_surface/daily_journal.json",
        "--output", "output/dashboard_surface/daily_journal_dashboard.json",
    ])
'''
    idx = text.find("topdown_reader_normalize")
    if idx >= 0:
        end = text.find("])", idx)
        end = text.find("\n", end) if end >= 0 else -1
        patched = text[:end+1] + insertion + text[end+1:] if end >= 0 else text + insertion
    else:
        success_idx = text.find("TURBO_V73_CYCLE_OK")
        if success_idx >= 0:
            line_start = text.rfind("\n", 0, success_idx)
            patched = text[:line_start] + insertion + text[line_start:]
        else:
            patched = text + "\n" + insertion
    TARGET.write_text(patched, encoding="utf-8")
    print(f"PATCH_OK | scheduler_powerflow_turbo_wrapper.py patched | backup={backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
