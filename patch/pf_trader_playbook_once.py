#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
PowerFlow V7.6 - Trader Playbook GBPUSD Only

Lit un terrain_packet GBPUSD et produit une couche playbook d'attention trader.
Ne produit aucun ordre, aucune execution, aucun BUY/SELL, aucun target/stop.
Le playbook nomme le scenario terrain et expose watch/invalidation en francais.

Usage minimal:
  python .\patch\pf_trader_playbook_once.py \
    --symbol GBPUSD \
    --input .\output\dashboard_surface\GBPUSD\terrain_packet.json \
    --output .\output\dashboard_surface\GBPUSD\trader_playbook.json

Usage avec enrichissement non destructif du packet:
  python .\patch\pf_trader_playbook_once.py \
    --symbol GBPUSD \
    --input .\output\dashboard_surface\GBPUSD\terrain_packet.json \
    --output .\output\dashboard_surface\GBPUSD\trader_playbook.json \
    --packet-output .\output\dashboard_surface\GBPUSD\terrain_packet_with_playbook.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

SUPPORTED_SYMBOL = "GBPUSD"

DATA_LIMITED_MARKERS = {
    "READING_PARTIAL",
    "DATA_PARTIAL",
    "MICROFILM_MISSING",
    "M1_MISSING",
    "PACKETS_STALE",
    "CROSS_VALIDATION_DEGRADED",
    "B5_B8_DEGRADED",
    "DEGRADED",
    "MINIMAL",
    "BLIND",
    "HONEST_UNKNOWN",
    "UNKNOWN",
}

HIGH_RISK_MARKERS = {
    "EXHAUSTION",
    "RELEASE_CONSUMED",
    "PRICE_REJECTED_LOW",
    "PRICE_REJECTED_HIGH",
    "FAILED_REINTEGRATION",
    "FAILED_PROPAGATION",
    "RELAY_DEGRADING",
    "NOISY_DETACHMENT",
    "NEWS_SPIKE",
}

PLAYBOOK_ORDER = [
    "HIGH_ZONE_EXHAUSTION_RISK",
    "POST_HIGH_UNWIND",
    "SECOND_LEG_DOWN",
    "POST_RELEASE_COUNTER_BREATH",
    "POST_LOW_COUNTER_BREATH",
    "HONEST_UNKNOWN",
]

DEFAULT_LABELS_FR: Dict[str, Dict[str, str]] = {
    "HIGH_ZONE_EXHAUSTION_RISK": {
        "playbook_label_fr": "Risque d’épuisement en zone haute",
        "playbook_context_fr": "Le flux arrive ou reste en zone haute avec signes de consommation, rejet ou extension tardive. Le playbook ne valide pas une continuation brute; il signale que le mouvement peut être mature ou consomme.",
        "watch_plan_fr": "Ne pas chase. Surveiller acceptation propre au-dessus de la zone haute ou rejet confirmé avec perte de tenue du prix.",
        "invalidation_fr": "Acceptation propre au-dessus de la zone haute avec propagation non dégradée et prix qui tient la zone.",
    },
    "POST_HIGH_UNWIND": {
        "playbook_label_fr": "Deroulement apres rejet de zone haute",
        "playbook_context_fr": "Le dernier film dominant est un rejet ou une fatigue de zone haute. Un biais descendant brut doit être lu comme unwind post-high, pas comme nouvelle structure isolee.",
        "watch_plan_fr": "Surveiller si le prix accepte sous la zone de rejet et si la propagation descendante reste propre.",
        "invalidation_fr": "Reintegration claire de la zone haute puis acceptation au-dessus de la zone rejetee.",
    },
    "SECOND_LEG_DOWN": {
        "playbook_label_fr": "Second mouvement descendant",
        "playbook_context_fr": "Le counter-breath ou la reintegration a echoue; le flux peut reprendre le film descendant deja installe.",
        "watch_plan_fr": "Observer reprise de pression apres rejet du counter-breath, cassure du dernier bas local ou acceptation sous la zone basse.",
        "invalidation_fr": "Counter-breath absorbe avec acceptation prix au-dessus de la zone de reaction.",
    },
    "POST_RELEASE_COUNTER_BREATH": {
        "playbook_label_fr": "Respiration inverse apres release",
        "playbook_context_fr": "Apres une release structurelle, le mouvement inverse est d'abord une respiration/counter-breath tant que le prix ne reintegre pas proprement la structure precedente.",
        "watch_plan_fr": "Surveiller si le counter-breath est absorbe, rejete ou accepte. Le role principal est reaction, pas nouvelle phase tant que le prix ne confirmé pas.",
        "invalidation_fr": "Reintegration propre avec acceptation prix et propagation qui transforme la reaction en nouvelle phase.",
    },
    "POST_LOW_COUNTER_BREATH": {
        "playbook_label_fr": "Reaction depuis zone basse",
        "playbook_context_fr": "Le prix reagit depuis une zone basse ou apres retest de low. Le biais haussier brut doit être lu comme reaction/counter-breath post-low tant que l'acceptation haute n'est pas visible.",
        "watch_plan_fr": "Surveiller acceptation au-dessus de la borne haute de zone ou rejet rapide de la reaction.",
        "invalidation_fr": "Cassure ou acceptation sous la zone basse, ou rejet net du counter-breath.",
    },
    "HONEST_UNKNOWN": {
        "playbook_label_fr": "Lecture limitee / inconnue honnete",
        "playbook_context_fr": "Les champs terrain ne permettent pas de nommer un scenario prioritaire sans surinterpreter. La sortie expose la limite plutot qu'une fausse certitude.",
        "watch_plan_fr": "Attendre un indice terrain plus net: prix, propagation, texture ou data visibility meilleure.",
        "invalidation_fr": "Nouveau packet avec prix confirmé, data visible et role terrain coherent.",
    },
}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_as_text(v) for v in value)
    if isinstance(value, dict):
        return " ".join(f"{k} {_as_text(v)}" for k, v in value.items())
    return str(value)


def _norm(value: Any) -> str:
    return _as_text(value).strip().upper().replace("-", "_").replace(" ", "_")


def _contains_any(value: Any, markers: Iterable[str]) -> bool:
    text = _norm(value)
    return any(marker in text for marker in markers)


def _first_present(packet: Mapping[str, Any], keys: Iterable[str], default: Any = "UNKNOWN") -> Any:
    """Lecture robuste des champs plats ou imbriques du terrain_packet."""
    containers: List[Mapping[str, Any]] = [packet]
    for container_key in ("terrain", "packet", "trader_packet", "surface", "state", "playbook_source"):
        nested = packet.get(container_key)
        if isinstance(nested, Mapping):
            containers.append(nested)

    for key in keys:
        for container in containers:
            if key in container and container[key] not in (None, ""):
                return container[key]
    return default


def extract_source_fields(packet: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "symbol": _first_present(packet, ["symbol", "pair"], SUPPORTED_SYMBOL),
        "film_state": _first_present(packet, ["film_state", "film", "current_film"], "UNKNOWN"),
        "last_structural_event": _first_present(packet, ["last_structural_event", "last_event"], "UNKNOWN"),
        "current_move_role": _first_present(packet, ["current_move_role", "move_role", "move"], "UNKNOWN"),
        "raw_bias": _first_present(packet, ["raw_bias", "bias", "pair_bias"], "UNKNOWN"),
        "qualified_bias": _first_present(packet, ["qualified_bias", "qualified_state", "terrain_bias"], "UNKNOWN"),
        "packet_quality": _first_present(packet, ["packet_quality", "quality"], "UNKNOWN"),
        "price_confirmation": _first_present(packet, ["price_confirmation", "price_state"], "UNKNOWN"),
        "propagation_state": _first_present(packet, ["propagation_state", "propagation"], "UNKNOWN"),
        "detachment_texture": _first_present(packet, ["detachment_texture", "texture", "volatility_texture"], "UNKNOWN"),
        "data_visibility": _first_present(packet, ["data_visibility", "data", "visibility"], "UNKNOWN"),
        "watch_condition": _first_present(packet, ["watch_condition", "watch"], ""),
        "invalidation_condition": _first_present(packet, ["invalidation_condition", "invalidation"], ""),
        "current_zone": _first_present(packet, ["current_zone", "zone"], "UNKNOWN"),
        "current_zone_status": _first_present(packet, ["current_zone_status", "zone_status"], "UNKNOWN"),
    }


def is_data_limited(fields: Mapping[str, Any]) -> bool:
    data_text = " ".join(
        _as_text(fields.get(key, ""))
        for key in ("data_visibility", "packet_quality", "propagation_state", "detachment_texture")
    )
    return _contains_any(data_text, DATA_LIMITED_MARKERS)


def has_elevated_technical_risk(fields: Mapping[str, Any]) -> bool:
    risk_text = " ".join(
        _as_text(fields.get(key, ""))
        for key in ("qualified_bias", "current_move_role", "price_confirmation", "propagation_state", "detachment_texture", "packet_quality")
    )
    return _contains_any(risk_text, HIGH_RISK_MARKERS)


def detect_playbook_state(fields: Mapping[str, Any]) -> str:
    film = _norm(fields.get("film_state"))
    last_event = _norm(fields.get("last_structural_event"))
    move = _norm(fields.get("current_move_role"))
    qbias = _norm(fields.get("qualified_bias"))
    raw = _norm(fields.get("raw_bias"))
    price = _norm(fields.get("price_confirmation"))
    zone = _norm(fields.get("current_zone_status"))
    texture = _norm(fields.get("detachment_texture"))
    data = _norm(fields.get("data_visibility"))

    combined = " ".join([film, last_event, move, qbias, raw, price, zone, texture, data])

    if any(token in combined for token in ("HIGH_ZONE_EXHAUSTION_RISK", "HIGH_EXHAUSTION", "EXHAUSTION_DETACHMENT")):
        return "HIGH_ZONE_EXHAUSTION_RISK"
    if "HIGH_ZONE_ACTIVE" in combined and any(token in combined for token in ("EXHAUSTION", "RELEASE_CONSUMED", "LATE_UP")):
        return "HIGH_ZONE_EXHAUSTION_RISK"

    if any(token in combined for token in ("POST_HIGH_UNWIND", "DEEP_POST_HIGH_UNWIND")):
        return "POST_HIGH_UNWIND"
    if "HIGH_ZONE_REJECTION" in combined and any(token in combined for token in ("PAIR_DOWN", "DOWN", "PRICE_REJECTED")):
        return "POST_HIGH_UNWIND"

    if any(token in combined for token in ("SECOND_LEG_DOWN", "SECOND_LOW_TEST")):
        return "SECOND_LEG_DOWN"
    if "SECOND_LEG" in combined and any(token in combined for token in ("DOWN", "LOWER_LOCK", "COUNTER_BREATH_REJECTED")):
        return "SECOND_LEG_DOWN"
    if "COUNTER_BREATH_REJECTED" in combined and any(token in combined for token in ("PAIR_DOWN", "DOWN", "LOWER_LOW")):
        return "SECOND_LEG_DOWN"

    if any(token in combined for token in ("POST_LOW_COUNTER_BREATH", "POST_LOW_REACTION")):
        return "POST_LOW_COUNTER_BREATH"
    if any(token in combined for token in ("LOWER_ZONE_ACTIVE", "LOWER_ZONE_RANGE_ACTIVE", "REJECTION_LOW", "SECOND_LOW_TEST")) and any(token in combined for token in ("PAIR_UP", "COUNTER_BREATH", "REACTION")):
        return "POST_LOW_COUNTER_BREATH"

    if any(token in combined for token in ("POST_RELEASE_COUNTER_BREATH", "COUNTER_BREATH_UP", "COUNTER_BREATH")):
        return "POST_RELEASE_COUNTER_BREATH"
    if any(token in combined for token in ("RELEASE_DOWN_VALIDATED", "RELEASE_UP_VALIDATED", "POST_RELEASE")) and any(token in combined for token in ("PAIR_UP", "PAIR_DOWN", "REACTION")):
        return "POST_RELEASE_COUNTER_BREATH"

    if is_data_limited(fields):
        return "HONEST_UNKNOWN"

    return "HONEST_UNKNOWN"


def build_no_trade_warning_fr(fields: Mapping[str, Any]) -> str:
    reasons: List[str] = []
    if is_data_limited(fields):
        reasons.append("Lecture partielle")
    if has_elevated_technical_risk(fields):
        reasons.append("risque technique eleve")

    if not reasons:
        return ""

    details = []
    data = _norm(fields.get("data_visibility"))
    quality = _norm(fields.get("packet_quality"))
    propagation = _norm(fields.get("propagation_state"))
    texture = _norm(fields.get("detachment_texture"))

    if data and data != "UNKNOWN":
        details.append(f"DATA={data}")
    if quality and quality != "UNKNOWN":
        details.append(f"QUALITY={quality}")
    if propagation and propagation in {"FAILED_PROPAGATION", "RELAY_DEGRADING", "LTF_ONLY"}:
        details.append(f"PROPAGATION={propagation}")
    if texture and texture in {"NOISY_DETACHMENT", "NEWS_SPIKE", "FALSE_REACTION_DETACHMENT"}:
        details.append(f"TEXTURE={texture}")

    suffix = f" ({'; '.join(details)})" if details else ""
    return f"{', '.join(reasons)} : prudence analytique, ne pas traiter comme lecture complete{suffix}."


def load_labels(path: Optional[Path]) -> Dict[str, Dict[str, str]]:
    if not path or not path.exists():
        return DEFAULT_LABELS_FR
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    labels = data.get("playbooks", data)
    merged = dict(DEFAULT_LABELS_FR)
    for key, value in labels.items():
        if isinstance(value, dict):
            base = dict(merged.get(key, {}))
            base.update({str(k): str(v) for k, v in value.items()})
            merged[key] = base
    return merged


def build_playbook(packet: Mapping[str, Any], labels: Optional[Dict[str, Dict[str, str]]] = None) -> Dict[str, Any]:
    labels = labels or DEFAULT_LABELS_FR
    fields = extract_source_fields(packet)
    state = detect_playbook_state(fields)
    label = labels.get(state, labels["HONEST_UNKNOWN"])

    watch_plan = label.get("watch_plan_fr", "")
    invalidation = label.get("invalidation_fr", "")

    packet_watch = _as_text(fields.get("watch_condition", "")).strip()
    packet_invalidation = _as_text(fields.get("invalidation_condition", "")).strip()

    if packet_watch:
        watch_plan = f"{watch_plan} Terrain packet: {packet_watch}"
    if packet_invalidation:
        invalidation = f"{invalidation} Terrain packet: {packet_invalidation}"

    playbook = {
        "symbol": SUPPORTED_SYMBOL,
        "playbook_version": "v76_trader_playbook_gbpusd_0.1",
        "playbook_state": state,
        "playbook_label_fr": label.get("playbook_label_fr", state),
        "playbook_context_fr": label.get("playbook_context_fr", ""),
        "watch_plan_fr": watch_plan,
        "invalidation_fr": invalidation,
        "no_trade_warning_fr": build_no_trade_warning_fr(fields),
        "source_fields": fields,
        "do_not_execute": True,
        "trader_decides": True,
    }
    return playbook


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def write_json(path: Path, payload: Mapping[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        if pretty:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        else:
            json.dump(payload, f, ensure_ascii=False, separators=(",", ":"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PowerFlow V7.6 trader playbook GBPUSD only")
    parser.add_argument("--symbol", default=SUPPORTED_SYMBOL, help="Supported: GBPUSD only")
    parser.add_argument("--input", default="output/dashboard_surface/GBPUSD/terrain_packet.json", help="Input terrain_packet JSON")
    parser.add_argument("--labels", default="schema/playbook_labels_fr_v76.json", help="Optional labels JSON")
    parser.add_argument("--output", default="output/dashboard_surface/GBPUSD/trader_playbook.json", help="Output playbook JSON")
    parser.add_argument("--packet-output", default="", help="Optional enriched terrain_packet output path")
    parser.add_argument("--compact", action="store_true", help="Write compact JSON")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    symbol = _norm(args.symbol)
    if symbol != SUPPORTED_SYMBOL:
        raise SystemExit(f"Unsupported symbol {args.symbol!r}. V7.6 playbooks mission is GBPUSD only.")

    input_path = Path(args.input)
    labels_path = Path(args.labels) if args.labels else None
    output_path = Path(args.output)

    packet = read_json(input_path)
    labels = load_labels(labels_path)
    playbook = build_playbook(packet, labels)
    write_json(output_path, playbook, pretty=not args.compact)

    if args.packet_output:
        enriched = dict(packet)
        enriched["playbook"] = playbook
        # Convenience flat fields for cockpit/formatter consumption.
        for key in (
            "playbook_state",
            "playbook_label_fr",
            "playbook_context_fr",
            "watch_plan_fr",
            "invalidation_fr",
            "no_trade_warning_fr",
        ):
            enriched[key] = playbook.get(key, "")
        write_json(Path(args.packet_output), enriched, pretty=not args.compact)

    print(f"[OK] trader playbook written: {output_path}")
    print(f"[OK] playbook_state={playbook['playbook_state']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

