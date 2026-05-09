from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pf_behavioral_alert_mapper import map_behavioral_alerts


DEFAULT_TEMPORAL = Path("output") / "temporal_node_state.json"
DEFAULT_OUT = Path("output") / "behavioral_alert_queue.json"
DEFAULT_COCKPIT = Path("output") / "cockpit_agentic_state_v01.json"

DEFAULT_ENERGY_M1 = Path("output") / "currency_energy_state_m1.json"
DEFAULT_ENERGY_M5 = Path("output") / "currency_energy_state_m5.json"
DEFAULT_ENERGY_M15 = Path("output") / "currency_energy_state_m15.json"

LEGACY_ENERGY_CANDIDATES = [
    Path("output") / "currency_energy_state.json",
    Path("output") / "currency_energy_state_m1_after_v08b.json",
]


def load_json(path: Path, required: bool = False) -> dict[str, Any] | None:
    """Charge un JSON objet. Zéro mutation, zéro écriture DB."""
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


def _existing_path(value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    return path if path.exists() else None


def _load_energy_bundle(args: argparse.Namespace) -> tuple[dict[str, Any] | None, str, list[int]]:
    """
    Charge Energy en priorité multi-TF M1/M5/M15.

    Backward compatible : --energy force un fichier standalone unique.
    Sinon le runner charge automatiquement :
      output/currency_energy_state_m1.json
      output/currency_energy_state_m5.json
      output/currency_energy_state_m15.json
    """
    explicit_energy = _existing_path(args.energy)
    if explicit_energy:
        data = load_json(explicit_energy, required=False)
        return data, str(explicit_energy), []

    requested = {
        1: Path(args.energy_m1),
        5: Path(args.energy_m5),
        15: Path(args.energy_m15),
    }

    by_timeframe: dict[str, Any] = {}
    sources: dict[str, str] = {}
    available: list[int] = []

    for tf, path in requested.items():
        data = load_json(path, required=False) if path.exists() else None
        if data is None:
            continue
        by_timeframe[str(tf)] = data
        sources[str(tf)] = str(path)
        available.append(tf)

    if by_timeframe:
        primary_tf = 1 if "1" in by_timeframe else sorted(available)[0]
        return (
            {
                "mode": "MULTI_TF_ENERGY_STANDALONE",
                "primary_timeframe": primary_tf,
                "available_timeframes": sorted(available),
                "sources": sources,
                "by_timeframe": by_timeframe,
            },
            ", ".join(f"M{tf}={sources[str(tf)]}" for tf in sorted(available)),
            sorted(available),
        )

    for legacy_path in LEGACY_ENERGY_CANDIDATES:
        data = load_json(legacy_path, required=False) if legacy_path.exists() else None
        if data is not None:
            return data, str(legacy_path), []

    return None, "NONE", []


def _load_relational_gravity(cockpit_path: Path | None) -> dict[str, Any] | None:
    """Charge relational_gravity depuis cockpit_agentic_state_v01.json si disponible."""
    if cockpit_path is None:
        return None
    cockpit_state = load_json(cockpit_path, required=False)
    if not cockpit_state:
        return None
    rg_block = cockpit_state.get("relational_gravity")
    return rg_block if isinstance(rg_block, dict) else None


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
        help="Optional legacy single currency_energy_state.json path. If set, overrides --energy-m1/m5/m15.",
    )
    parser.add_argument(
        "--energy-m1",
        default=str(DEFAULT_ENERGY_M1),
        help="Path to currency_energy_state_m1.json",
    )
    parser.add_argument(
        "--energy-m5",
        default=str(DEFAULT_ENERGY_M5),
        help="Path to currency_energy_state_m5.json",
    )
    parser.add_argument(
        "--energy-m15",
        default=str(DEFAULT_ENERGY_M15),
        help="Path to currency_energy_state_m15.json",
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

    temporal_state = load_json(temporal_path, required=True)
    energy_state, energy_label, energy_tfs = _load_energy_bundle(args)
    rg_block = _load_relational_gravity(cockpit_path)

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
        rg_guard = result.get("relational_gravity_guard", {})
        energy_guard = result.get("energy_guard", {})

        print("BEHAVIORAL_ALERT_QUEUE_OK")
        print(f"temporal={temporal_path}")
        print(f"energy={energy_label}")
        print(f"energy_tfs={energy_tfs if energy_tfs else 'SINGLE_OR_NONE'}")
        print(f"cockpit={cockpit_path if cockpit_path else 'NONE'}")
        print(f"relational_gravity={'PRESENT' if rg_block else 'NONE'}")
        print(f"rg_read_mode={rg_guard.get('read_mode', 'UNKNOWN')}")
        print(f"rg_topline_reliable={rg_guard.get('topline_reliable', False)}")
        print(f"rg_tf_details_required={rg_guard.get('tf_details_required', False)}")
        print(f"energy_source={energy_guard.get('source', 'NONE')}")
        print(f"energy_primary_tf={energy_guard.get('primary_timeframe', '')}")
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
