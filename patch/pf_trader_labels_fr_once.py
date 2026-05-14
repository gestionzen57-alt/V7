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

    playbook_label = packet.get("playbook_label_fr")
    if playbook_label:
        lines.append("")
        lines.append(f"Scénario trader : {playbook_label}")
    playbook_context = packet.get("playbook_context_fr")
    if playbook_context:
        lines.append(f"Contexte scénario : {playbook_context}")
    watch_plan = packet.get("watch_plan_fr")
    if watch_plan:
        lines.append(f"Plan de surveillance : {watch_plan}")
    playbook_invalidation = packet.get("invalidation_fr")
    if playbook_invalidation:
        lines.append(f"Invalidation scénario : {playbook_invalidation}")
    no_trade_warning = packet.get("no_trade_warning_fr")
    if no_trade_warning:
        lines.append(f"Avertissement : {no_trade_warning}")

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

# V7.6.6 condition alias normalization
# Purpose: keep Telegram/playbook FR readable when an enum was already partially
# translated by the generic terrain label layer before the condition-specific
# renderer gets it.
def _v766_condition_alias_cleanup(value):
    _map = {
        "vraie acceptation prix, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "vraie acceptation prix, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "rejet haut confirmé ou déroulement inverse": "rejet haut confirmé ou déroulement inverse",
        "condition dâ€™invalidation non traduite : rejet haut confirmé ou déroulement inverse": "rejet haut confirmé ou déroulement inverse",
        "vraie acceptation prix, pas extension tardive.": "vraie acceptation prix, pas extension tardive.",
        "rejet haut confirmé ou déroulement inverse.": "rejet haut confirmé ou déroulement inverse.",
    }
    if isinstance(value, str):
        out = value
        for bad, good in _map.items():
            out = out.replace(bad, good)
        return out
    if isinstance(value, list):
        return [_v766_condition_alias_cleanup(x) for x in value]
    if isinstance(value, tuple):
        return tuple(_v766_condition_alias_cleanup(x) for x in value)
    if isinstance(value, dict):
        return {k: _v766_condition_alias_cleanup(v) for k, v in value.items()}
    return value

try:
    for _dict_name in list(globals()):
        _dict_obj = globals().get(_dict_name)
        if isinstance(_dict_obj, dict):
            _dict_obj.setdefault("vraie acceptation prix, pas extension tardive.", "vraie acceptation prix, pas extension tardive.")
            _dict_obj.setdefault("rejet haut confirmé ou déroulement inverse.", "rejet haut confirmé ou déroulement inverse.")
            _dict_obj.setdefault("vraie acceptation prix, pas extension tardive.", "vraie acceptation prix, pas extension tardive.")
            _dict_obj.setdefault("rejet haut confirmé ou déroulement inverse.", "rejet haut confirmé ou déroulement inverse.")
except Exception:
    pass

try:
    import inspect as _inspect_v766
    import functools as _functools_v766

    def _v766_wrap_string_return(_func):
        @_functools_v766.wraps(_func)
        def _wrapped(*args, **kwargs):
            return _v766_condition_alias_cleanup(_func(*args, **kwargs))
        return _wrapped

    for _name, _obj in list(globals().items()):
        if _name.startswith("_v766_"):
            continue
        if _inspect_v766.isfunction(_obj) and getattr(_obj, "__module__", None) == __name__:
            globals()[_name] = _v766_wrap_string_return(_obj)
except Exception:
    pass

# V7.6.6 final condition cleanup V3
# Last-pass cleanup for condition labels that were already partially translated
# before the condition-specific renderer handled them.
def _v766_final_condition_cleanup(value):
    _mojibake = {
        "\u00c3\u00a9": "\u00e9",
        "\u00c3\u00a8": "\u00e8",
        "\u00c3\u00aa": "\u00ea",
        "\u00c3\u00a0": "\u00e0",
        "\u00c3\u0089": "\u00c9",
        "\u00c3\u008a": "\u00ca",
        "\u00c3\u00a7": "\u00e7",
    }
    _repl = {
        "WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION": "vraie acceptation prix, pas extension tardive.",
        "HIGH_REJECTION_OR_UNWIND": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse.",
        "Surveiller acceptation propre, pas extension tardive.": "vraie acceptation prix, pas extension tardive.",
        "Surveiller acceptation propre, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "Rejet de zone haute ou unwind.": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse.",
        "Rejet de zone haute ou unwind": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse",
        "condition \u00e0 surveiller non traduite : Surveiller acceptation propre, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "condition a surveiller non traduite : Surveiller acceptation propre, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "condition \u00e0 surveiller non traduite : vraie acceptation prix, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "condition a surveiller non traduite : vraie acceptation prix, pas extension tardive": "vraie acceptation prix, pas extension tardive",
        "condition d'invalidation non traduite : Rejet de zone haute ou unwind": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse",
        "condition d\u2019invalidation non traduite : Rejet de zone haute ou unwind": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse",
        "condition d'invalidation non traduite : rejet haut confirm\u00e9 ou d\u00e9roulement inverse": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse",
        "condition d\u2019invalidation non traduite : rejet haut confirm\u00e9 ou d\u00e9roulement inverse": "rejet haut confirm\u00e9 ou d\u00e9roulement inverse",
    }
    if isinstance(value, str):
        out = value
        for bad, good in _mojibake.items():
            out = out.replace(bad, good)
        for _ in range(2):
            for bad, good in _repl.items():
                out = out.replace(bad, good)
        return out
    if isinstance(value, list):
        return [_v766_final_condition_cleanup(x) for x in value]
    if isinstance(value, tuple):
        return tuple(_v766_final_condition_cleanup(x) for x in value)
    if isinstance(value, dict):
        return {k: _v766_final_condition_cleanup(v) for k, v in value.items()}
    return value

try:
    for _dict_name in list(globals()):
        _dict_obj = globals().get(_dict_name)
        if isinstance(_dict_obj, dict):
            _dict_obj["WATCH_FOR_TRUE_ACCEPTANCE_NOT_LATE_EXTENSION"] = "vraie acceptation prix, pas extension tardive."
            _dict_obj["HIGH_REJECTION_OR_UNWIND"] = "rejet haut confirm\u00e9 ou d\u00e9roulement inverse."
            _dict_obj["Surveiller acceptation propre, pas extension tardive."] = "vraie acceptation prix, pas extension tardive."
            _dict_obj["Rejet de zone haute ou unwind."] = "rejet haut confirm\u00e9 ou d\u00e9roulement inverse."
except Exception:
    pass

try:
    import inspect as _inspect_v766_final
    import functools as _functools_v766_final

    def _v766_final_wrap(_func):
        @_functools_v766_final.wraps(_func)
        def _wrapped(*args, **kwargs):
            return _v766_final_condition_cleanup(_func(*args, **kwargs))
        return _wrapped

    for _name, _obj in list(globals().items()):
        if _name.startswith("_v766_"):
            continue
        if _inspect_v766_final.isfunction(_obj) and getattr(_obj, "__module__", None) == __name__:
            globals()[_name] = _v766_final_wrap(_obj)
except Exception:
    pass

