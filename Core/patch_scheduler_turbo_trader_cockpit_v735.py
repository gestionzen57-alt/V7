#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from pathlib import Path

TARGET = Path("scheduler_powerflow_turbo_wrapper.py")
MARKER = "pf_trader_cockpit_once.py"

BLOCK = '''
    run_step("trader_cockpit", [
        sys.executable, "pf_trader_cockpit_once.py",
        "--symbols", symbols,
        "--trade-symbol", "GBPUSD",
        "--output", "output/dashboard_surface/trader_cockpit.json",
        "--txt", "output/dashboard_surface/trader_cockpit.txt",
    ], core)
'''


def main() -> int:
    if not TARGET.exists():
        print(f"PATCH_FAIL | missing {TARGET}")
        return 1
    text = TARGET.read_text(encoding="utf-8", errors="replace")
    if MARKER in text:
        print("PATCH_OK | trader cockpit already present")
        return 0
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_suffix(TARGET.suffix + f".bak_trader_cockpit_v735_{stamp}")
    backup.write_text(text, encoding="utf-8")

    # Insert just before the final TURBO summary print if possible, otherwise append before return.
    needle = "    print(\n        f\"TURBO_V73_CYCLE_OK"
    if needle in text:
        text = text.replace(needle, BLOCK + "\n" + needle, 1)
    else:
        needle2 = "    return 0"
        if needle2 not in text:
            print("PATCH_FAIL | insertion point not found")
            return 1
        text = text.replace(needle2, BLOCK + "\n" + needle2, 1)

    # Add layer name in summary if a literal layers list exists.
    old = "topdown_reader,live_brief,b6,multiread,daily_journal"
    new = "topdown_reader,live_brief,b6,multiread,trader_cockpit,daily_journal"
    text = text.replace(old, new)
    old2 = "topdown_reader"
    if new not in text and "layers=data_health" in text:
        text = text.replace(old2, "topdown_reader,trader_cockpit", 1)

    TARGET.write_text(text, encoding="utf-8")
    print(f"PATCH_OK | scheduler patched with trader cockpit | backup={backup.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
