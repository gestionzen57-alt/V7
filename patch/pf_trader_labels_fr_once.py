from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

DEFAULT_LABELS_PATH = Path("schema") / "terrain_packet_labels_fr_v76.json"


def load_labels(path: str | Path = DEFAULT_LABELS_PATH) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        return json.load(handle)


def _humanize_unknown_enum(value: Any) -> str:
    """Return a readable fallback without changing the internal enum.

    Internal PowerFlow values stay in English. This is display-only.
    """
    if value is None:
        return "inconnu"

    text = str(value).strip()
    if not text:
        return "inconnu"

    # Keep existing French/free text readable.
    if " " in text and "_" not in text:
        return text

    # Strip common technical prefixes before rendering a trader-readable fallback.
    prefixes = (
        "WATCH_FOR_",
        "WATCH_",
        "INVALIDATION_",
        "INVALIDATE_IF_",
        "IF_",
    )
    human = text
    for prefix in prefixes:
        if human.upper().startswith(prefix):
            human = human[len(prefix):]
            break

    human = human.replace("_", " ").replace("-", " ").lower()
    human = re.sub(r"\s+", " ", human).strip()
    return human or "inconnu"


def _sentence(text: str) -> str:
    text = str(text).strip()
    if not text:
        return "Inconnu."
    if text[-1] not in ".!?":
        text += "."
    return text


def label_value(value: Any, labels: Dict[str, Any]) -> str:
    if value is None:
        return "Inconnu"
    text = str(value)
    translated = labels.get("values", {}).get(text)
    if translated:
        return translated
    return _humanize_unknown_enum(text)


def label_condition(value: Any, labels: Dict[str, Any], *, kind: str) -> str:
    """Translate watch_condition / invalidation_condition for display only.

    kind must be "watch" or "invalidation". Unknown enums are rendered as clean
    French fallback phrases instead of leaking raw uppercase enum names to Telegram.
    """
    if value is None or value == "":
        return "condition non renseignée."

    if isinstance(value, list):
        rendered = [label_condition(v, labels, kind=kind).rstrip(".") for v in value if str(v).strip()]
        return _sentence(" ; ".join(rendered)) if rendered else "condition non renseignée."

    text = str(value).strip()
    translated = labels.get("values", {}).get(text)
    if translated:
        return _sentence(translated[:1].lower() + translated[1:])

    fallback = _humanize_unknown_enum(text)
    if kind == "watch":
        return _sentence(f"condition à surveiller non traduite : {fallback}")
    if kind == "invalidation":
        return _sentence(f"condition d'invalidation non traduite : {fallback}")
    return _sentence(fallback)


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
    watch_condition = label_condition(packet.get("watch_condition"), labels, kind="watch")
    invalidation_condition = label_condition(
        packet.get("invalidation_condition"), labels, kind="invalidation"
    )

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
        f"À surveiller : {watch_condition}",
        f"Invalidation : {invalidation_condition}",
    ]

    memory = packet.get("memory_match")
    if memory:
        lines.append(f"Mémoire B6 : {label_value(memory, labels)}")
    memory_reason = packet.get("memory_reason_fr")
    if memory_reason:
        lines.append(f"Raison B6 : {memory_reason}")
    similar_days = packet.get("similar_historical_days") or []
    if similar_days:
        short_days = []
        for item in similar_days[:3]:
            if isinstance(item, dict):
                day = item.get("day", "?")
                label = item.get("label_fr") or item.get("film_id", "?")
                confidence = item.get("confidence", "?")
                short_days.append(f"{day} — {label} ({confidence})")
        if short_days:
            lines.append("Films proches : " + " | ".join(short_days))

    return "\n".join(lines).strip() + "\n"


def _read_json(path: str | Path) -> Dict[str, Any]:
    with Path(path).open("r", encoding="utf-8-sig") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("terrain packet JSON must be an object")
    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Format a terrain_packet in French for trader/Telegram display."
    )
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

