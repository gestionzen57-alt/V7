#!/usr/bin/env python3
"""
Inject M1_CONTEXT_SCORE dashboard card into dashboard_live.html.

Safe behavior:
- creates backup
- avoids duplicate injection
- injects before </main> if available, otherwise before </body>
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path


MARKER = "data-brick=\"M1_CONTEXT_SCORE\""


def inject(dashboard: Path, card: Path) -> dict:
    if not dashboard.exists():
        return {"status": "FAIL", "reason": "DASHBOARD_NOT_FOUND", "dashboard": str(dashboard)}
    if not card.exists():
        return {"status": "FAIL", "reason": "CARD_NOT_FOUND", "card": str(card)}

    html = dashboard.read_text(encoding="utf-8", errors="replace")
    if MARKER in html:
        return {"status": "PASS", "reason": "ALREADY_PRESENT", "dashboard": str(dashboard)}

    card_html = card.read_text(encoding="utf-8", errors="replace")
    backup = dashboard.with_suffix(dashboard.suffix + f".bak_m1_context_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    backup.write_text(html, encoding="utf-8")

    if "</main>" in html:
        html = html.replace("</main>", card_html + "\n</main>", 1)
    elif "</body>" in html:
        html = html.replace("</body>", card_html + "\n</body>", 1)
    else:
        html = html + "\n" + card_html + "\n"

    dashboard.write_text(html, encoding="utf-8")
    return {"status": "PASS", "reason": "INJECTED", "dashboard": str(dashboard), "backup": str(backup)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Inject M1 context dashboard card.")
    parser.add_argument("--dashboard", default="dashboard_live.html")
    parser.add_argument("--card", default="dashboard_m1_context_card_patch.html")
    args = parser.parse_args()

    result = inject(Path(args.dashboard), Path(args.card))
    print(result)
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
