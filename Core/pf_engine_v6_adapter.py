# pf_engine_v6_adapter.py
# PowerFlow V7.6.7 - T002 compatibility boundary
#
# Purpose:
# - expose the stable process_tick contract used by capture_bridge.py;
# - delegate to legacy engine.py without behavior change;
# - create a safe V6 extraction seam for future refactor.
#
# This module must stay lightweight. It must not import cockpit_*, dashboard_*,
# telegram_*, or write to DB. Legacy side effects remain inside engine.py.

import engine as _legacy_engine
import models


ADAPTER_VERSION = "T002_V6_ADAPTER_V1"


def process_tick(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    """Compatibility wrapper around legacy engine.process_tick.

    Contract frozen in:
    Docs/Contracts/T002_ENGINE_PROCESS_TICK_CONTRACT.json

    This wrapper intentionally delegates 1:1 to preserve runtime behavior.
    Future T002 extraction can move internals behind this boundary while
    keeping capture_bridge.py stable.
    """
    return _legacy_engine.process_tick(tick, prev, brain, send_alert)


__all__ = ["process_tick", "ADAPTER_VERSION"]

