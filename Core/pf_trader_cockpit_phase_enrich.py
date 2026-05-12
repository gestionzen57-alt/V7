from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cockpit-json", default="output/dashboard_surface/trader_cockpit.json")
    parser.add_argument("--cockpit-txt", default="output/dashboard_surface/trader_cockpit.txt")
    parser.add_argument("--phase", default="output/dashboard_surface/phase_synthesis.json")
    args = parser.parse_args()

    cockpit_path = Path(args.cockpit_json)
    txt_path = Path(args.cockpit_txt)
    phase = load_json(args.phase)

    if not phase:
        print("PHASE_COCKPIT_ENRICH_SKIP | phase_missing")
        return 0

    cockpit = load_json(cockpit_path)
    cockpit["phase_synthesis"] = {
        "attention": phase.get("attention"),
        "phase_state": phase.get("phase_state"),
        "dominant_bias": phase.get("dominant_bias"),
        "confidence": phase.get("confidence"),
        "reading": phase.get("reading"),
        "technical_risks": phase.get("technical_risks") or [],
    }

    cockpit_path.write_text(json.dumps(cockpit, indent=2, ensure_ascii=False), encoding="utf-8")

    block = [
        "",
        "PHASE SYNTHESIS",
        f"attention={phase.get('attention')}",
        f"phase={phase.get('phase_state')}",
        f"bias={phase.get('dominant_bias')}",
        f"confidence={phase.get('confidence')}",
        f"reading={phase.get('reading')}",
    ]

    risks = phase.get("technical_risks") or []
    if risks:
        block.append("risks=" + ",".join(str(r) for r in risks))

    old = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""
    marker = "\nPHASE SYNTHESIS\n"
    if marker in old:
        old = old.split(marker)[0].rstrip() + "\n"

    txt_path.write_text(old.rstrip() + "\n" + "\n".join(block) + "\n", encoding="utf-8")

    print(
        f"PHASE_COCKPIT_ENRICH_OK | phase={phase.get('phase_state')} | "
        f"attention={phase.get('attention')} | cockpit={args.cockpit_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
