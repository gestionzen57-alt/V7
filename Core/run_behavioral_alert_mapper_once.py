# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from pf_behavioral_alert_mapper import map_behavioral_alerts


def _load_json(path: Path, required: bool = False) -> dict[str, Any] | None:
    if not path.exists():
        if required:
            raise FileNotFoundError(f"Required JSON not found: {path}")
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        if required:
            raise ValueError(f"JSON root must be object: {path}")
        return None
    return data


def _default_temporal(symbol: str) -> str:
    return f"output/dashboard_surface/{symbol.upper()}/node.json"


def _default_energy(symbol: str) -> str:
    return f"output/dashboard_surface/{symbol.upper()}/energy.json"


def _default_out(symbol: str) -> str:
    return f"output/behavioral_alert_queue_{symbol.upper()}.json"


def _legacy_alias(symbol: str, src: Path) -> None:
    if symbol.upper() != "GBPUSD" or not src.exists():
        return
    legacy = Path("output/behavioral_alert_queue.json")
    legacy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, legacy)


def _load_relational_gravity(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    cockpit_state = _load_json(path, required=False)
    if not cockpit_state:
        return None
    rg = cockpit_state.get("relational_gravity")
    return rg if isinstance(rg, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow — Behavioral Alert Mapper, symbol-parametric")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--temporal", default=None)
    parser.add_argument("--energy", default=None)
    parser.add_argument("--cockpit", default="output/cockpit_agentic_state_v01.json")
    parser.add_argument("--out", default=None)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    temporal_path = Path(args.temporal or _default_temporal(symbol))
    energy_path = Path(args.energy or _default_energy(symbol))
    out_path = Path(args.out or _default_out(symbol))
    cockpit_path = Path(args.cockpit) if args.cockpit else None

    temporal_state = _load_json(temporal_path, required=True) or {}
    energy_state = _load_json(energy_path, required=False)
    rg_block = _load_relational_gravity(cockpit_path)
    result = map_behavioral_alerts(
        temporal_node_state=temporal_state,
        currency_energy_state=energy_state,
        relational_gravity=rg_block,
    )
    result.setdefault("meta", {})["symbol"] = symbol
    result.setdefault("meta", {})["method"] = "P2_BEHAVIORAL_MAPPER_SYMBOL_PARAMETRIC"
    result.setdefault("symbol", symbol)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None) + "\n", encoding="utf-8")
    _legacy_alias(symbol, out_path)
    if args.summary:
        print("BEHAVIORAL_ALERT_QUEUE_OK")
        print(f"symbol={symbol}")
        print(f"temporal={temporal_path}")
        print(f"energy={energy_path if energy_path.exists() else 'NONE'}")
        print(f"out={out_path}")
        print(f"behavioral_count={len(result.get('behavioral_alerts', []))}")
        print(f"degraded_count={len(result.get('degraded_alerts', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
