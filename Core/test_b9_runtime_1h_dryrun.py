"""
Test runtime B9 - 1h DRY-RUN.

Validates that B9 can process runtime windows without crash and can create nodes.
Default duration is 60 minutes. Override for smoke tests with:
  B9_DRYRUN_MINUTES=1 python test_b9_runtime_1h_dryrun.py
"""
from __future__ import annotations

import os
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, Iterable, Optional, Tuple

from pf_b9_runtime_bridge import B9RuntimeBridge, sample_runtime_window


def _minutes_from_env(default: int = 60) -> int:
    try:
        return max(1, int(os.getenv("B9_DRYRUN_MINUTES", str(default))))
    except ValueError:
        return default


def _poll_seconds_from_env(default: float = 60.0) -> float:
    try:
        return max(0.1, float(os.getenv("B9_DRYRUN_POLL_SECONDS", str(default))))
    except ValueError:
        return default


def run_b9_dryrun_1h(
    minutes: Optional[int] = None,
    poll_seconds: Optional[float] = None,
    window_provider: Optional[Callable[[], Dict[str, Any]]] = None,
    bridge: Optional[B9RuntimeBridge] = None,
    max_windows: Optional[int] = None,
) -> Tuple[int, list[tuple[datetime, str]]]:
    """Run B9 engine DRY-RUN, log results, return nodes_created and errors."""
    minutes = _minutes_from_env() if minutes is None else minutes
    poll_seconds = _poll_seconds_from_env() if poll_seconds is None else poll_seconds
    bridge = bridge or B9RuntimeBridge(enable_telegram=False, db_path="powerflow.db")
    window_provider = window_provider or (lambda: sample_runtime_window(datetime.utcnow().isoformat(timespec="seconds")))

    start = datetime.utcnow()
    end = start + timedelta(minutes=minutes)
    nodes_created = 0
    errors: list[tuple[datetime, str]] = []
    windows_processed = 0

    print(f"[B9 DRY-RUN] Start {start.isoformat()} duration_minutes={minutes}")

    while datetime.utcnow() < end:
        if max_windows is not None and windows_processed >= max_windows:
            break
        try:
            window_data = window_provider()
            symbol = str(window_data.get("symbol", "GBPUSD"))
            result = bridge.process_tick_window(symbol, window_data)
            windows_processed += 1
            status = result.get("status")
            print(f"[B9 DRY-RUN] {datetime.utcnow().isoformat()} status={status}")
            if status == "NODE_CREATED":
                nodes_created += 1
            if status == "B9_RUNTIME_ERROR":
                errors.append((datetime.utcnow(), str(result.get("error", "unknown error"))))
        except Exception as exc:
            errors.append((datetime.utcnow(), str(exc)))
        time.sleep(poll_seconds)

    print(
        f"[B9 DRY-RUN] End - Windows: {windows_processed}, "
        f"Nodes created: {nodes_created}, Errors: {len(errors)}"
    )
    if errors:
        for ts, err in errors:
            print(f"  [{ts.isoformat()}] {err}")

    return nodes_created, errors


if __name__ == "__main__":
    run_b9_dryrun_1h()
