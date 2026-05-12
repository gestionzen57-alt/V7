#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path

TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
MARKER = "pf_powerflow_multiread_synthesis_once.py"
SUCCESS_MARKER = "TURBO_V73_CYCLE_OK"

INSERTION = """
    run_step("b6_live_fusion", [
        sys.executable, "pf_b6_live_fusion_once.py",
    ])
    run_step("b6_live_fusion_normalize", [
        sys.executable, "dashboard_normalize_b6_live_fusion.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/b6_live_fusion_dashboard.json",
    ])
    run_step("multiread_synthesis", [
        sys.executable, "pf_powerflow_multiread_synthesis_once.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/powerflow_multiread_synthesis.json",
    ])
    run_step("multiread_synthesis_normalize", [
        sys.executable, "dashboard_normalize_multiread_synthesis.py",
        "--input", "output/dashboard_surface/powerflow_multiread_synthesis.json",
        "--output", "output/dashboard_surface/multiread_synthesis_dashboard.json",
    ])
"""


def find_insert_position(text: str) -> int:
    marker_pos = text.find(SUCCESS_MARKER)
    if marker_pos < 0:
        return len(text)
    prefix = text[:marker_pos]
    candidates = [prefix.rfind("\n    print("), prefix.rfind("\nprint(")]
    candidates = [c for c in candidates if c >= 0]
    if candidates:
        return max(candidates) + 1
    return text.rfind("\n", 0, marker_pos) + 1


def main() -> int:
    if not TARGET.exists():
        print("PATCH_FAIL | scheduler_powerflow_turbo_wrapper.py missing")
        return 1

    text = TARGET.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        print("PATCH_OK | multiread synthesis already present")
        return 0

    backup = TARGET.with_suffix(".py.bak_multiread_v734")
    backup.write_text(text, encoding="utf-8")

    pos = find_insert_position(text)
    patched = text[:pos] + INSERTION + text[pos:]
    TARGET.write_text(patched, encoding="utf-8")

    print(f"PATCH_OK | scheduler patched with B6 + multiread | backup={backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
