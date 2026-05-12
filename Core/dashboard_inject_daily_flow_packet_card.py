#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

START = "<!-- POWERFLOW_V731_DAILY_FLOW_PACKET_CARD_START -->"
END = "<!-- POWERFLOW_V731_DAILY_FLOW_PACKET_CARD_END -->"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inject V7.3.1 daily flow packet card into dashboard_live.html.")
    parser.add_argument("--dashboard", default="dashboard_live.html")
    parser.add_argument("--card", default="dashboard_daily_flow_packet_card_patch.html")
    args = parser.parse_args(argv)

    dashboard = Path(args.dashboard)
    card = Path(args.card)
    if not dashboard.exists():
        print({"status": "FAIL", "reason": "DASHBOARD_MISSING", "dashboard": str(dashboard)})
        return 1
    if not card.exists():
        print({"status": "FAIL", "reason": "CARD_MISSING", "card": str(card)})
        return 1

    html = dashboard.read_text(encoding="utf-8", errors="replace")
    patch = card.read_text(encoding="utf-8", errors="replace")

    if START in html and END in html:
        before = html.split(START)[0]
        after = html.split(END, 1)[1]
        new_html = before + patch + after
        reason = "REPLACED"
    else:
        insert_at = html.lower().rfind("</body>")
        if insert_at >= 0:
            new_html = html[:insert_at] + "\n" + patch + "\n" + html[insert_at:]
        else:
            new_html = html + "\n" + patch + "\n"
        reason = "INJECTED"

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = dashboard.with_name(dashboard.name + f".bak_daily_flow_packet_{stamp}")
    backup.write_text(html, encoding="utf-8")
    dashboard.write_text(new_html, encoding="utf-8")

    print({"status": "PASS", "reason": reason, "dashboard": str(dashboard), "backup": str(backup)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
