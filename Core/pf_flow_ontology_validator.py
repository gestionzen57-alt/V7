#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — FLOW_ONTOLOGY_V0 Validator

Reads a behavioral alert queue JSON and classifies alerts into formal flow ontology categories.

Read-only:
- No DB access.
- No mutation of input queue.
- No BUY/SELL output.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple


CATEGORIES = (
    "INFLEXION",
    "COMPRESSION",
    "RELEASE",
    "ABSORPTION",
    "TENSION",
    "ROTATION",
    "STRUCTURE",
)

ONTOLOGY_MAP: Dict[str, Tuple[str, str]] = {
    # INFLEXION
    "FIRST_DETACHMENT_MICRO": ("INFLEXION", "Naissance"),
    "FIRST_DETACHMENT_WITH_CLEAN_RELAY": ("INFLEXION", "Premier détachement"),
    "KINEMATIC_SHIFT": ("INFLEXION", "Changement cinématique"),
    "COUNTER_RELEASE_ATTEMPT": ("INFLEXION", "Tentative contre-relâchement"),
    "COUNTER_RELEASE_ATTEMPT_ALERT": ("INFLEXION", "Tentative contre-relâchement"),
    "EARLY_SHIFT": ("INFLEXION", "Bascule micro"),
    "MICRO_BEND": ("INFLEXION", "Bascule micro"),
    "CURVATURE_CHANGE": ("INFLEXION", "Changement cinématique"),
    "NODE_BIRTH": ("INFLEXION", "Naissance"),
    "FIRST_IMPULSE": ("INFLEXION", "Naissance"),

    # COMPRESSION
    "CYCLE_COMPRESSING": ("COMPRESSION", "Temporelle"),
    "ELASTIC_LOADED": ("COMPRESSION", "Élastique"),
    "ORCHESTRAL_COMPRESSION": ("COMPRESSION", "Orchestrale"),
    "REGIME_COMPRESSION": ("COMPRESSION", "Régime"),
    "COMPRESSION": ("COMPRESSION", "Structurelle"),
    "TEMPORAL_DENSITY_ACTIVE": ("COMPRESSION", "Temporelle"),
    "TIGHT_GRAVITY_CLUSTER_ALERT": ("COMPRESSION", "Gravitationnelle"),
    "SAME_ANGLE_CLUSTER_ALERT": ("COMPRESSION", "Structurelle"),
    "COMPRESSION_CLUSTER": ("COMPRESSION", "Structurelle"),
    "DENSITY_RISE": ("COMPRESSION", "Temporelle"),
    "PRE_RELEASE_COMPRESSION": ("COMPRESSION", "Élastique"),

    # RELEASE
    "RUPTURE": ("RELEASE", "Libération"),
    "CASCADE_BUILDING": ("RELEASE", "Cascade"),
    "SEQUENCE_VELOCITY_HIGH": ("RELEASE", "Accélération"),
    "RELEASE": ("RELEASE", "Libération"),
    "COUNTER_RELEASE": ("RELEASE", "Libération"),
    "DETACHMENT_RELEASE": ("RELEASE", "Libération"),
    "CASCADE_RELEASE": ("RELEASE", "Cascade"),
    "EXPANSION": ("RELEASE", "Expansion"),
    "BREAKOUT_FLOW": ("RELEASE", "Rupture"),
    "IMPULSE_RELEASE": ("RELEASE", "Accélération"),

    # ABSORPTION
    "LEAKING": ("ABSORPTION", "Pré-rejet"),
    "PULLBACK_ABSORBED": ("ABSORPTION", "Pullback absorbé"),
    "PULLURES_ABSORBED": ("ABSORPTION", "Pullures absorbées"),
    "COUNTER_BREATH": ("ABSORPTION", "Contre-souffle"),
    "ABSORPTION": ("ABSORPTION", "Absorption locale"),
    "REJECTION_ABSORBED": ("ABSORPTION", "Pré-rejet"),
    "COUNTER_FORCE_DIGESTED": ("ABSORPTION", "Digestion force adverse"),
    "FAILED_PULLBACK": ("ABSORPTION", "Pullback absorbé"),
    "SUPPLY_ABSORBED": ("ABSORPTION", "Absorption locale"),
    "DEMAND_ABSORBED": ("ABSORPTION", "Absorption locale"),

    # TENSION
    "ACCUMULATING": ("TENSION", "Accumulation"),
    "PRE_EXTREME": ("TENSION", "Pré-extrême"),
    "ELASTIC_TENSION_SCORE": ("TENSION", "Score tension"),
    "ELASTIC_TENSION_HIGH": ("TENSION", "Élastique chargé"),
    "NODE_HEAT_ENERGY_DIVERGENCE": ("TENSION", "Chaleur node / énergie"),
    "TENSION_RISE": ("TENSION", "Pression latente"),
    "PRESSURE_BUILDUP": ("TENSION", "Pression latente"),
    "HOT_NODE": ("TENSION", "Chaleur node"),
    "NODE_HEAT": ("TENSION", "Chaleur node"),
    "LATENT_FORCE": ("TENSION", "Pression latente"),

    # ROTATION
    "REGIME_TRANSITION": ("ROTATION", "Transition"),
    "SPEARMAN_DRIFT": ("ROTATION", "Drift relationnel"),
    "DIVERGENT_EXTREME_TO_SYNCHRO": ("ROTATION", "Synchro naissante"),
    "DIVERGENT_EXTREME": ("ROTATION", "Bascule distribution"),
    "SYNCHRO": ("ROTATION", "Synchro"),
    "ROTATION": ("ROTATION", "Rotation"),
    "STATE_ROTATION": ("ROTATION", "Bascule distribution"),
    "CORRELATION_DRIFT": ("ROTATION", "Drift relationnel"),
    "GRAVITY_ROTATION": ("ROTATION", "Rotation gravitationnelle"),
    "REGIME_SHIFT": ("ROTATION", "Transition"),

    # STRUCTURE
    "LEADER": ("STRUCTURE", "Leader"),
    "FOLLOWER": ("STRUCTURE", "Follower"),
    "LEADER_FOLLOWER": ("STRUCTURE", "Leader / follower"),
    "COALITION": ("STRUCTURE", "Coalition"),
    "ANTAGONISTE": ("STRUCTURE", "Antagonisme"),
    "ANTAGONIST": ("STRUCTURE", "Antagonisme"),
    "FRACTAL_RESONANCE": ("STRUCTURE", "Résonance fractale"),
    "STRUCTURE": ("STRUCTURE", "Structure relative"),
    "RELATIVE_FORCE_FIELD": ("STRUCTURE", "Structure relative"),
    "CROSS_SYMBOL_DRIVER": ("STRUCTURE", "Driver cross-symbol"),
    "USD_WEAKNESS_DOMINANT": ("STRUCTURE", "Driver cross-symbol"),
    "GBP_STRENGTH_GENUINE": ("STRUCTURE", "Driver cross-symbol"),
    "EUR_DIVERGENT": ("STRUCTURE", "Driver cross-symbol"),
    "JPY_SAFE_HAVEN": ("STRUCTURE", "Driver cross-symbol"),
}

CATEGORY_PRIORITY = {cat: i for i, cat in enumerate(CATEGORIES)}

TEXT_KEYS = {
    "type",
    "event",
    "alert",
    "alert_type",
    "name",
    "label",
    "status",
    "state",
    "category",
    "message",
    "description",
    "reason",
    "signature",
    "behavior",
    "brick",
    "top_alert",
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def normalize_token(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).upper()
    text = re.sub(r"[^A-Z0-9_]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def flatten_text_values(obj: Any, key_hint: Optional[str] = None, depth: int = 0) -> List[str]:
    """Extract classification-bearing text from nested alert object."""
    if depth > 8:
        return []

    values: List[str] = []

    if isinstance(obj, Mapping):
        for k, v in obj.items():
            lk = str(k).lower()
            if lk in TEXT_KEYS or any(part in lk for part in ("alert", "event", "state", "signal", "tag", "status", "reason")):
                if isinstance(v, (str, int, float, bool)) or v is None:
                    values.append(str(v))
                elif isinstance(v, list):
                    for item in v:
                        if isinstance(item, (str, int, float, bool)):
                            values.append(str(item))
                        else:
                            values.extend(flatten_text_values(item, lk, depth + 1))
                elif isinstance(v, Mapping):
                    values.extend(flatten_text_values(v, lk, depth + 1))
            else:
                if isinstance(v, (Mapping, list)):
                    values.extend(flatten_text_values(v, lk, depth + 1))

    elif isinstance(obj, list):
        for item in obj:
            values.extend(flatten_text_values(item, key_hint, depth + 1))

    elif isinstance(obj, (str, int, float, bool)):
        if key_hint and key_hint.lower() in TEXT_KEYS:
            values.append(str(obj))

    return values


def tokenize_alert(alert: Mapping[str, Any]) -> Set[str]:
    raw_values = flatten_text_values(alert)
    tokens: Set[str] = set()

    for raw in raw_values:
        norm = normalize_token(raw)
        if not norm:
            continue
        tokens.add(norm)

        # Add phrase fragments to catch embedded alert text.
        for key in ONTOLOGY_MAP:
            if key in norm:
                tokens.add(key)

        # Split long phrases but keep meaningful multiword snake fragments.
        parts = norm.split("_")
        for n in range(2, min(6, len(parts)) + 1):
            for i in range(0, len(parts) - n + 1):
                tokens.add("_".join(parts[i:i+n]))

    return tokens


def classify_alert(alert: Mapping[str, Any]) -> Dict[str, Any]:
    tokens = tokenize_alert(alert)
    hits: List[Dict[str, str]] = []

    for token in sorted(tokens):
        if token in ONTOLOGY_MAP:
            cat, subcat = ONTOLOGY_MAP[token]
            hits.append({"event": token, "category": cat, "subcategory": subcat})

    if not hits:
        return {
            "classified": False,
            "category": "UNMAPPED",
            "subcategory": "ONTOLOGY_UNMAPPED_ALERT",
            "matched_events": [],
        }

    hits.sort(key=lambda h: (CATEGORY_PRIORITY.get(h["category"], 99), h["event"]))
    chosen = hits[0]

    return {
        "classified": True,
        "category": chosen["category"],
        "subcategory": chosen["subcategory"],
        "matched_events": hits,
    }


def extract_alerts(queue: Any) -> List[Mapping[str, Any]]:
    """Schema-flex queue extraction."""
    if isinstance(queue, list):
        return [a for a in queue if isinstance(a, Mapping)]

    if not isinstance(queue, Mapping):
        return []

    candidate_keys = [
        "alerts",
        "behavioral_alerts",
        "queue",
        "items",
        "events",
        "signals",
        "behavioral_queue",
    ]

    for key in candidate_keys:
        value = queue.get(key)
        if isinstance(value, list):
            return [a for a in value if isinstance(a, Mapping)]

    # Some PowerFlow states expose nested behavioral_flow.alerts.
    for nested_key in ("behavioral_flow", "flow", "state", "data", "payload"):
        nested = queue.get(nested_key)
        if isinstance(nested, Mapping):
            alerts = extract_alerts(nested)
            if alerts:
                return alerts

    # If the object itself looks like one alert.
    if any(str(k).lower() in TEXT_KEYS for k in queue.keys()):
        return [queue]

    return []


def build_ontology_report(queue_path: str) -> Dict[str, Any]:
    path = Path(queue_path)
    queue = read_json(path)
    alerts = extract_alerts(queue)

    counts = {cat: 0 for cat in CATEGORIES}
    classified_alerts: List[Dict[str, Any]] = []
    unmapped_alerts: List[Dict[str, Any]] = []

    for i, alert in enumerate(alerts):
        classification = classify_alert(alert)
        item = {
            "index": i,
            "category": classification["category"],
            "subcategory": classification["subcategory"],
            "classified": classification["classified"],
            "matched_events": classification["matched_events"],
            "source_preview": source_preview(alert),
        }

        if classification["classified"]:
            counts[classification["category"]] += 1
            classified_alerts.append(item)
        else:
            unmapped_alerts.append(item)

    total = len(alerts)
    covered = len(classified_alerts)
    coverage = round((covered / total), 6) if total else 0.0

    technical_risks: List[str] = []
    if not path.exists():
        technical_risks.append("QUEUE_FILE_MISSING")
    if total == 0:
        technical_risks.append("NO_ALERTS_EXTRACTED")
    if unmapped_alerts:
        technical_risks.append("ONTOLOGY_UNMAPPED_ALERTS_PRESENT")

    return {
        "timestamp_utc": utc_now_iso(),
        "method": "FLOW_ONTOLOGY_V0_VALIDATOR",
        "queue_path": queue_path,
        "alerts_total": total,
        "alerts_classified": covered,
        "alerts_unmapped": len(unmapped_alerts),
        "alerts_by_category": counts,
        "ontology_coverage": coverage,
        "classified_alerts": classified_alerts,
        "unmapped_alerts": unmapped_alerts,
        "technical_risks": technical_risks,
        "note": "Ontology names flow behavior. It does not produce trade decisions.",
    }


def source_preview(alert: Mapping[str, Any]) -> Dict[str, Any]:
    keys = [
        "type",
        "event",
        "alert",
        "alert_type",
        "name",
        "label",
        "status",
        "state",
        "level",
        "message",
        "reason",
    ]
    out: Dict[str, Any] = {}
    for key in keys:
        if key in alert:
            out[key] = alert[key]
    if not out:
        for k, v in list(alert.items())[:6]:
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[str(k)] = v
            else:
                out[str(k)] = type(v).__name__
    return out


def write_json(data: Mapping[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate behavioral alert queue against FLOW_ONTOLOGY_V0.")
    parser.add_argument("--queue", default="output/behavioral_alert_queue.json")
    parser.add_argument("--output", "--out", dest="output", default="output/flow_ontology_report.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = build_ontology_report(args.queue)
    write_json(report, args.output)

    if args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(
            "FLOW_ONTOLOGY_VALIDATOR_OK | "
            f"alerts={report['alerts_total']} | "
            f"classified={report['alerts_classified']} | "
            f"coverage={report['ontology_coverage']} | "
            f"out={args.output}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
