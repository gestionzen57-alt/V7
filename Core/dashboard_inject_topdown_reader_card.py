#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

MARKER = "pf-topdown-reader-card"


def inject(dashboard: str | Path, card: str | Path) -> dict:
    dash = Path(dashboard)
    card_path = Path(card)
    if not dash.exists():
        return {"status": "FAIL", "reason": "DASHBOARD_NOT_FOUND", "dashboard": str(dash)}
    if not card_path.exists():
        return {"status": "FAIL", "reason": "CARD_NOT_FOUND", "card": str(card_path)}
    html = dash.read_text(encoding="utf-8", errors="replace")
    if MARKER in html:
        return {"status": "PASS", "reason": "ALREADY_PRESENT", "dashboard": str(dash)}
    card_html = card_path.read_text(encoding="utf-8", errors="replace")
    backup = dash.with_name(dash.name + ".bak_topdown_reader_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    backup.write_text(html, encoding="utf-8")
    insert = "\n" + card_html + "\n"
    lower = html.lower()
    idx = lower.rfind("</body>")
    if idx >= 0:
        html2 = html[:idx] + insert + html[idx:]
    else:
        html2 = html + insert
    dash.write_text(html2, encoding="utf-8")
    return {"status": "PASS", "reason": "INJECTED", "dashboard": str(dash), "backup": str(backup)}


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inject V7.3 TopDown Market Reader card into dashboard_live.html")
    parser.add_argument("--dashboard", default="dashboard_live.html")
    parser.add_argument("--card", default="dashboard_topdown_reader_card_patch.html")
    args = parser.parse_args(argv)
    print(inject(args.dashboard, args.card))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
