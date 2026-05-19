"""Smoke runner for PowerFlow B9 runtime integration."""
from __future__ import annotations

import json
from datetime import datetime

from pf_b9_runtime_bridge import B9RuntimeBridge, sample_runtime_window


def main() -> int:
    bridge = B9RuntimeBridge(enable_telegram=False, db_path="powerflow.db")
    window_data = sample_runtime_window(datetime.utcnow().isoformat(timespec="seconds"))
    result = bridge.process_tick_window("GBPUSD", window_data)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    status = result.get("status")
    if status in {"NODE_CREATED", "NODE_SUPPRESSED", "B9_RUNTIME_ERROR"}:
        return 0 if status != "B9_RUNTIME_ERROR" else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
