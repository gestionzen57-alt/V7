#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
MARKER = "dashboard_normalize_live_brief.py"


def main() -> int:
    if not TARGET.exists():
        print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
        return 1

    text = TARGET.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        print("PATCH_OK | live brief already present")
        return 0

    backup = TARGET.with_suffix(".py.bak_live_brief_v733")
    backup.write_text(text, encoding="utf-8")

    insertion = """
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
