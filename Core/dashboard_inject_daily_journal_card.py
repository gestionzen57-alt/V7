#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

START = "<!-- POWERFLOW_V732_DAILY_JOURNAL_CARD_START -->"
END = "<!-- POWERFLOW_V732_DAILY_JOURNAL_CARD_END -->"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dashboard", default="dashboard_live.html")
    parser.add_argument("--card", default="dashboard_daily_journal_card_patch.html")
    args = parser.parse_args(argv)
    dashboard, card = Path(args.dashboard), Path(args.card)
    if not dashboard.exists():
        print({"status": "FAIL", "reason": "DASHBOARD_MISSING", "dashboard": str(dashboard)}); return 1
    if not card.exists():
        print({"status": "FAIL", "reason": "CARD_MISSING", "card": str(card)}); return 1
    html = dashboard.read_text(encoding="utf-8", errors="replace")
    patch = card.read_text(encoding="utf-8", errors="replace")
    if START in html and END in html:
        new_html = html.split(START)[0] + patch + html.split(END, 1)[1]
        reason = "REPLACED"
    else:
        pos = html.lower().rfind("</body>")
        new_html = html[:pos] + "\n" + patch + "\n" + html[pos:] if pos >= 0 else html + "\n" + patch + "\n"
        reason = "INJECTED"
    backup = dashboard.with_name(dashboard.name + ".bak_daily_journal_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup.write_text(html, encoding="utf-8")
    dashboard.write_text(new_html, encoding="utf-8")
    print({"status": "PASS", "reason": reason, "dashboard": str(dashboard), "backup": str(backup)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
