from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pf_behavioral_alert_mapper import map_behavioral_alerts


DEFAULT_TEMPORAL = Path("output") / "temporal_node_state.json"
DEFAULT_OUT = Path("output") / "behavioral_alert_queue.json"
DEFAULT_COCKPIT = Path("output") / "cockpit_agentic_state_v01.json"

ENERGY_CANDIDATES = [
    Path("output") / "currency_energy_state.json",
    Path("output") / "currency_energy_state_m1.json",
    Path("output") / "currency_energy_state_m1_after_v08b.json",
]


def load_json(path: Path, required: bool = False) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required JSON not found: {path}")
        return None

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, dict):
        if required:
            raise ValueError(f"JSON root must be an object: {path}")
        return None

    return data


def resolve_energy_path(explicit: str | None) -> Path | None:
    if explicit:
        p = Path(explicit)
        return p if p.exists() else None

    for p in ENERGY_CANDIDATES:
        if p.exists():
            return p

    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PowerFlow V6 — run Behavioral Alert Mapper once."
    )
    parser.add_argument(
        "--temporal",
        default=str(DEFAULT_TEMPORAL),
        help="Path to temporal_node_state.json",
    )
    parser.add_argument(
        "--energy",
        default=None,
        help="Optional path to currency_energy_state.json",
    )
    parser.add_argument(
        "--cockpit",
        default=str(DEFAULT_COCKPIT),
        help="Optional path to cockpit_agentic_state_v01.json for relational_gravity",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT),
        help="Output path for behavioral_alert_queue.json",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print output JSON",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print compact execution summary",
    )

    args = parser.parse_args()

    temporal_path = Path(args.temporal)
    out_path = Path(args.out)
    cockpit_path = Path(args.cockpit) if args.cockpit else None
    energy_path = resolve_energy_path(args.energy)

    temporal_state = load_json(temporal_path, required=True)
    energy_state = load_json(energy_path, required=False) if energy_path else None

    # Relational Gravity Guard-Aware P2
    # Source optionnelle : cockpit_agentic_state_v01.json
    # Si absent ou corrompu : rg_block reste None, les checkers RG restent silencieux.
    rg_block = None
    if cockpit_path:
        cockpit_state = load_json(cockpit_path, required=False)
        if cockpit_state:
            rg_block = cockpit_state.get("relational_gravity")

    result = map_behavioral_alerts(
        temporal_node_state=temporal_state or {},
        currency_energy_state=energy_state,
        relational_gravity=rg_block,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2 if args.pretty else None,
        )

    if args.summary:
        behavioral_count = len(result.get("behavioral_alerts", []))
        degraded_count = len(result.get("degraded_alerts", []))
        film_count = len(result.get("film_steps", []))
        next_watch_count = len(result.get("next_watch_enriched", []))

        print("BEHAVIORAL_ALERT_QUEUE_OK")
        print(f"temporal={temporal_path}")
        print(f"energy={energy_path if energy_path else 'NONE'}")
        print(f"cockpit={cockpit_path if cockpit_path else 'NONE'}")
        print(f"relational_gravity={'PRESENT' if rg_block else 'NONE'}")
        print(f"out={out_path}")
        print(f"behavioral_count={behavioral_count}")
        print(f"degraded_count={degraded_count}")
        print(f"film_steps_count={film_count}")
        print(f"next_watch_count={next_watch_count}")

        for alert in result.get("behavioral_alerts", []):
            print(f"[{alert.get('level')}] {alert.get('name')}")

        for alert in result.get("degraded_alerts", []):
            print(f"[{alert.get('level')}] {alert.get('name')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())