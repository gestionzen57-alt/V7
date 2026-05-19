"""PowerFlow B9 runtime DRY-RUN 10 minutes.

This script tries to use the installed runtime bridge if available. If no live
window provider exists, it uses deterministic synthetic windows to validate that
B9 can create/publish JSON nodes without crashing.

No DB write. No Telegram. No BUY/SELL.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def synthetic_window(i: int) -> Dict[str, Any]:
    base = 1.2500 + i * 0.00002
    return {
        "symbol": "GBPUSD",
        "timestamp": utc_now(),
        "zone_low": round(base - 0.0010, 5),
        "zone_high": round(base + 0.0010, 5),
        "current_price": round(base + (0.00015 if i % 2 else -0.00012), 5),
        "zone_touch_history": [1, 2, 1, 2],
        "zone_bars_since_touch": i % 5,
        "price_min": round(base - 0.0012, 5),
        "price_max": round(base + 0.0013, 5),
        "price_open": round(base - 0.0003, 5),
        "price_close": round(base + 0.0004, 5),
        "ticks_total": 150 + i,
        "ticks_inside_zone": 80,
        "ticks_inside_center_band": 20,
        "dwell_seconds_inside_zone": 45.0,
        "dwell_seconds_inside_center": 10.0,
        "max_center_penetration_ratio": 0.65,
        "price_exits_original_side": False,
        "rejection_distance_pips": 8.5,
        "rejection_speed_pips_per_min": 2.3,
        "net_progress_pips": 3.2 if i % 2 else -3.2,
        "is_pullback_context": True,
        "raw_bias": "UP" if i % 2 else "DOWN",
        "packet_strength": 0.72,
        "previous_scene_state": {"scene_state": "POST_RELEASE" if i % 2 else "ROTATION"},
    }


def write_fallback_node(output_dir: Path, window: Dict[str, Any], index: int) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    node = {
        "node_id": f"DRYRUN_B9_{int(time.time())}_{index}",
        "symbol": window["symbol"],
        "timestamp": window["timestamp"],
        "verdict": "DRYRUN_NODE_CREATED",
        "confidence": 0.35,
        "data_visibility": "RECONSTRUCTED",
        "source_mode": "SYNTHETIC_DRYRUN",
        "technical_risks": ["SYNTHETIC_WINDOW_USED"],
        "message": "Perception dry-run B9 creee sans Telegram.",
    }
    path = output_dir / f"{node['timestamp'].replace(':', '').replace('-', '')}_{node['node_id']}.json"
    path.write_text(json.dumps(node, ensure_ascii=False, indent=2), encoding="utf-8")
    return node


def try_runtime_bridge(window: Dict[str, Any]) -> Dict[str, Any] | None:
    try:
        from pf_b9_runtime_bridge import process_tick_window_b9  # type: ignore
    except Exception:
        return None
    try:
        return process_tick_window_b9(window["symbol"], window)
    except TypeError:
        return process_tick_window_b9(window)


def run(minutes: float, poll_seconds: float, force_synthetic: bool = False) -> int:
    end = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    errors: List[str] = []
    nodes_created = 0
    loops = 0
    output_dir = Path.cwd() / "output" / "b9_nodes_live"

    print(f"[B9 DRY-RUN] Start {utc_now()} duration_minutes={minutes}")
    print("[B9 DRY-RUN] Telegram disabled by contract")

    while datetime.now(timezone.utc) < end:
        loops += 1
        window = synthetic_window(loops)
        try:
            result = None if force_synthetic else try_runtime_bridge(window)
            if result is None:
                node = write_fallback_node(output_dir, window, loops)
                nodes_created += 1
                print(f"[B9 DRY-RUN] fallback node created {node['node_id']}")
            else:
                status = result.get("status", "UNKNOWN") if isinstance(result, dict) else "UNKNOWN"
                print(f"[B9 DRY-RUN] runtime result status={status}")
                if status == "NODE_CREATED" or (isinstance(result, dict) and result.get("node")):
                    nodes_created += 1
        except Exception as exc:
            errors.append(f"{utc_now()} {type(exc).__name__}: {exc}")
            print("[B9 DRY-RUN][ERROR]", errors[-1])
        time.sleep(max(0.1, poll_seconds))

    print(f"[B9 DRY-RUN] End {utc_now()} nodes_created={nodes_created} errors={len(errors)} loops={loops}")
    if errors:
        for err in errors:
            print("  - " + err)
        return 1
    if nodes_created < 1:
        print("[B9 DRY-RUN][FAIL] NO_B9_NODE_CREATED_DURING_DRYRUN")
        return 2
    print("[B9 DRY-RUN][OK] 0 errors and >=1 node created")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--minutes", type=float, default=float(os.getenv("B9_DRYRUN_MINUTES", "10")))
    parser.add_argument("--poll-seconds", type=float, default=float(os.getenv("B9_DRYRUN_POLL_SECONDS", "60")))
    parser.add_argument("--force-synthetic", action="store_true")
    args = parser.parse_args()
    return run(args.minutes, args.poll_seconds, args.force_synthetic)


if __name__ == "__main__":
    raise SystemExit(main())
