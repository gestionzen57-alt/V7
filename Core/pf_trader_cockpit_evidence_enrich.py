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


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


def strip_block(text: str, title: str) -> str:
    marker = "\n" + title + "\n"
    idx = text.find(marker)
    if idx == -1:
        return text
    return text[:idx].rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cockpit-json", default="output/dashboard_surface/trader_cockpit.json")
    parser.add_argument("--cockpit-txt", default="output/dashboard_surface/trader_cockpit.txt")
    parser.add_argument("--evidence-reading", default="output/dashboard_surface/evidence_reading.json")
    parser.add_argument("--evidence-bus", default="output/dashboard_surface/evidence_bus.json")
    args = parser.parse_args()

    cockpit = load_json(args.cockpit_json)
    reading = load_json(args.evidence_reading)
    bus = load_json(args.evidence_bus)

    cockpit["evidence_bus"] = {
        "global_attention": bus.get("global_attention"),
        "dominant_phase": bus.get("dominant_phase"),
        "dominant_bias": bus.get("dominant_bias"),
        "confidence": bus.get("confidence"),
        "bias_weights": bus.get("bias_weights"),
    }

    cockpit["evidence_reading"] = {
        "attention": reading.get("attention"),
        "phase": reading.get("phase"),
        "bias": reading.get("bias"),
        "confidence": reading.get("confidence"),
        "phrase": reading.get("phrase"),
        "watch": reading.get("watch") or [],
        "technical_risks": reading.get("technical_risks") or [],
    }

    write_json(args.cockpit_json, cockpit)

    txt_path = Path(args.cockpit_txt)
    base = txt_path.read_text(encoding="utf-8") if txt_path.exists() else ""
    base = strip_block(base, "EVIDENCE BUS READING")

    lines = [
        "",
        "EVIDENCE BUS READING",
        f"attention={reading.get('attention')}",
        f"phase={reading.get('phase')}",
        f"bias={reading.get('bias')}",
        f"confidence={reading.get('confidence')}",
        f"phrase={reading.get('phrase')}",
    ]

    watch = reading.get("watch") or []
    if watch:
        lines.append("watch=" + " | ".join(str(x) for x in watch))

    risks = reading.get("technical_risks") or []
    if risks:
        lines.append("risks=" + " | ".join(str(x) for x in risks[:12]))

    txt_path.write_text(base.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")

    print(
        f"TRADER_COCKPIT_EVIDENCE_READING_ENRICH_OK | "
        f"phase={reading.get('phase')} | bias={reading.get('bias')} | cockpit={args.cockpit_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
