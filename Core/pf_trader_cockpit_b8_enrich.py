from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cockpit-json", default="output/dashboard_surface/trader_cockpit.json")
    parser.add_argument("--cockpit-txt", default="output/dashboard_surface/trader_cockpit.txt")
    parser.add_argument("--b8", default="output/dashboard_surface/b8_cross_surface.json")
    args = parser.parse_args()

    cockpit_path = Path(args.cockpit_json)
    txt_path = Path(args.cockpit_txt)
    b8_path = Path(args.b8)

    cockpit = load_json(cockpit_path)
    b8 = load_json(b8_path)

    if not b8:
        print("B8_COCKPIT_ENRICH_SKIP | b8_missing")
        return 0

    cockpit["b8_cross_symbol"] = {
        "status": b8.get("status"),
        "attention": b8.get("attention"),
        "coverage_state": b8.get("coverage_state"),
        "message": b8.get("message"),
        "technical_risks": b8.get("technical_risks") or [],
    }

    cockpit_path.write_text(json.dumps(cockpit, indent=2, ensure_ascii=False), encoding="utf-8")

    block = [
        "",
        "B8 CROSS-SYMBOL",
        f"status={b8.get('status')}",
        f"attention={b8.get('attention')}",
        f"coverage={b8.get('coverage_state')}",
        f"message={b8.get('message')}",
    ]

    risks = b8.get("technical_risks") or []
    if risks:
        block.append("risks=" + ",".join(str(r) for r in risks))

    old = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""
    marker = "\nB8 CROSS-SYMBOL\n"
    if marker in old:
        old = old.split(marker)[0].rstrip() + "\n"

    txt_path.write_text(old.rstrip() + "\n" + "\n".join(block) + "\n", encoding="utf-8")

    print(
        f"B8_COCKPIT_ENRICH_OK | status={b8.get('status')} | "
        f"coverage={b8.get('coverage_state')} | cockpit={args.cockpit_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
