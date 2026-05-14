from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List


DEFAULT_LABELS_PATH = Path("schema") / "terrain_packet_labels_fr_v76.json"


def load_labels(path: str | Path = DEFAULT_LABELS_PATH) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def label_value(value: Any, labels: Dict[str, Any]) -> str:
    if value is None:
        return "Inconnu"
    text = str(value)
    return labels.get("values", {}).get(text, text)


def label_list(values: Any, labels: Dict[str, Any]) -> str:
    if not values:
        return "Aucun risque signalé"
    if isinstance(values, str):
        values = [values]
    if not isinstance(values, Iterable):
        return label_value(values, labels)
    translated = [label_value(v, labels) for v in values if str(v).strip()]
    return ", ".join(translated) if translated else "Aucun risque signalé"


def format_terrain_packet_fr(packet: Dict[str, Any], labels: Dict[str, Any] | None = None) -> str:
    labels = labels or load_labels()

    def v(key: str) -> str:
        return label_value(packet.get(key, "UNKNOWN"), labels)

    symbol = packet.get("symbol", "UNKNOWN")
    risks = label_list(packet.get("technical_risks", []), labels)

    lines = [
        f"{symbol} — {v('film_state')}",
        "",
        f"Film : {v('film_state')}",
        f"Dernier événement : {v('last_structural_event')}",
        f"Zone : {packet.get('current_zone', 'UNKNOWN')} / {v('current_zone_status')}",
        f"Rôle du mouvement : {v('current_move_role')}",
        f"Lecture : {v('raw_bias')} → {v('qualified_bias')}",
        f"Qualité : {v('packet_quality')}",
        f"Prix : {v('price_confirmation')}",
        f"Propagation : {v('propagation_state')}",
        f"Texture : {v('detachment_texture')}",
        f"Data : {v('data_visibility')}",
        f"Risques : {risks}",
        f"À surveiller : {packet.get('watch_condition', 'UNKNOWN')}",
        f"Invalidation : {packet.get('invalidation_condition', 'UNKNOWN')}",
    ]

    memory = packet.get("memory_match")
    if memory:
        lines.append(f"Mémoire B6 : {label_value(memory, labels)}")

    return "\n".join(lines).strip() + "\n"


def _read_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("terrain packet JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(description="Format a terrain_packet in French for trader/Telegram display.")
    parser.add_argument("--input", required=True, help="Path to terrain_packet.json")
    parser.add_argument("--output", help="Optional output .txt path")
    parser.add_argument("--labels", default=str(DEFAULT_LABELS_PATH), help="French labels JSON")
    args = parser.parse_args()

    labels = load_labels(args.labels)
    packet = _read_json(args.input)
    text = format_terrain_packet_fr(packet, labels)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
    else:
        print(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

