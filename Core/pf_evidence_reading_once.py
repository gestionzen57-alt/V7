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


def write_json(path: str | Path, data: dict[str, Any], pretty: bool = False) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2 if pretty else None, ensure_ascii=False), encoding="utf-8")


def write_txt(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"EVIDENCE READING | {data.get('symbol')} | {data.get('attention')} | {data.get('phase')}",
        f"bias={data.get('bias')}",
        f"confidence={data.get('confidence')}",
        "",
        f"PHRASE={data.get('phrase')}",
    ]

    watch = data.get("watch") or []
    if watch:
        lines += ["", "WATCH"]
        for w in watch:
            lines.append(f"- {w}")

    risks = data.get("technical_risks") or []
    if risks:
        lines += ["", "TECHNICAL RISKS"]
        for r in risks:
            lines.append(f"- {r}")

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def find_layer(bus: dict[str, Any], layer: str) -> dict[str, Any]:
    for e in bus.get("evidence") or []:
        if str(e.get("layer") or "").upper() == layer.upper():
            return e
    return {}


def build_phrase(bus: dict[str, Any]) -> dict[str, Any]:
    symbol = str(bus.get("symbol") or "GBPUSD").upper()
    phase = str(bus.get("dominant_phase") or "UNKNOWN").upper()
    bias = str(bus.get("dominant_bias") or "UNKNOWN").upper()
    attention = str(bus.get("global_attention") or "INFO").upper()
    confidence = bus.get("confidence")

    ltf = find_layer(bus, "LTF")
    mtf = find_layer(bus, "MTF")
    htf = find_layer(bus, "HTF")
    cockpit = find_layer(bus, "COCKPIT")
    b8 = find_layer(bus, "B8_CROSS_SYMBOL")

    phrase = "Lecture contextuelle. Aucune forme de flux dominante nommée."
    watch: list[str] = []

    if phase == "STRUCTURAL_BEARISH_WITH_LTF_MTF_COUNTERFLOW":
        phrase = (
            "Structure baissière dominante, mais LTF/MTF respirent à contre-sens. "
            "Surveiller absorption du pullback, échec de reprise, puis second leg baissier."
        )
        watch = [
            "LTF/MTF PAIR_UP contre HTF/cockpit PAIR_DOWN",
            "pullback absorbé",
            "réintégration après reprise",
            "bascule LTF vers PAIR_DOWN",
            "second leg baissier si relais propre",
        ]

    elif phase == "STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW":
        phrase = (
            "Structure haussière dominante, mais LTF/MTF respirent à contre-sens. "
            "Surveiller absorption du repli, échec de cassure basse, puis second leg haussier."
        )
        watch = [
            "LTF/MTF PAIR_DOWN contre HTF/cockpit PAIR_UP",
            "repli absorbé",
            "réintégration après cassure basse",
            "bascule LTF vers PAIR_UP",
            "second leg haussier si relais propre",
        ]

    elif phase == "DIRECTIONAL_CONFLICT":
        phrase = (
            "Conflit directionnel actif entre couches. Le flux n'est pas neutre : il est en friction. "
            "Surveiller résolution par alignement LTF/MTF avec la structure."
        )
        watch = [
            "friction directionnelle",
            "résolution LTF/MTF",
            "invalidation de la poussée opposée",
        ]

    elif phase == "RELEASE_VALIDATED":
        phrase = (
            f"Release multi-TF validé en {bias}. Flux actif. "
            "Surveiller continuation, relais propre et fatigue éventuelle."
        )
        watch = [
            "continuation",
            "relais propre",
            "fatigue",
            "contre-respiration tardive",
        ]

    elif phase in {"NO_CLEAR_PHASE", "UNKNOWN"}:
        phrase = (
            "Pas de phase dominante nette. Lecture de contexte uniquement. "
            "Surveiller naissance de compression ou résolution de conflit."
        )
        watch = [
            "naissance compression",
            "résolution de conflit",
            "premier relais clair",
        ]

    risks = list(bus.get("technical_risks") or [])

    if str(b8.get("state") or "").upper() == "DEGRADED":
        watch.append("B8 dégradé : ne pas utiliser comme confirmation structurelle")
        if "B8_INSUFFICIENT_CROSS_PAIR_COVERAGE" not in risks:
            risks.append("B8_INSUFFICIENT_CROSS_PAIR_COVERAGE")

    return {
        "method": "EVIDENCE_READING_V739E",
        "symbol": symbol,
        "attention": attention,
        "phase": phase,
        "bias": bias,
        "confidence": confidence,
        "phrase": phrase,
        "watch": watch,
        "layer_snapshot": {
            "ltf": {
                "state": ltf.get("state"),
                "bias": ltf.get("bias"),
                "attention": ltf.get("attention"),
            },
            "mtf": {
                "state": mtf.get("state"),
                "bias": mtf.get("bias"),
                "attention": mtf.get("attention"),
            },
            "htf": {
                "state": htf.get("state"),
                "bias": htf.get("bias"),
                "attention": htf.get("attention"),
            },
            "cockpit": {
                "state": cockpit.get("state"),
                "bias": cockpit.get("bias"),
                "attention": cockpit.get("attention"),
            },
            "b8": {
                "state": b8.get("state"),
                "attention": b8.get("attention"),
            },
        },
        "technical_risks": sorted(set(str(r) for r in risks if r)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence-bus", default="output/dashboard_surface/evidence_bus.json")
    parser.add_argument("--output", default="output/dashboard_surface/evidence_reading.json")
    parser.add_argument("--txt", default="output/dashboard_surface/evidence_reading.txt")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    bus = load_json(args.evidence_bus)
    data = build_phrase(bus)

    write_json(args.output, data, pretty=args.pretty)
    write_txt(args.txt, data)

    print(
        f"EVIDENCE_READING_OK | symbol={data['symbol']} | "
        f"attention={data['attention']} | phase={data['phase']} | bias={data['bias']} | out={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
