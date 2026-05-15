# pf_engine_v6_adapter.py
# PowerFlow V7.6.7 - T002 runtime adapter boundary
#
# Role:
# - preserve the legacy process_tick public contract;
# - keep runtime safe by defaulting to legacy engine path;
# - allow controlled V6 core runtime activation via environment flag;
# - no UI, cockpit, or alert transport dependencies.

import os
from typing import Any, Callable, Optional

import models
import engine as _legacy_engine

try:
    import pf_engine_v6_core as _v6_core
    _V6_CORE_IMPORT_ERROR = None
except Exception as _exc:  # pragma: no cover
    _v6_core = None
    _V6_CORE_IMPORT_ERROR = _exc


ENGINE_ADAPTER_VERSION = "T002_RUNTIME_ADAPTER_V1"
ENV_FLAG = "POWERFLOW_T002_USE_V6_CORE"
STRICT_ENV_FLAG = "POWERFLOW_T002_V6_CORE_STRICT"

_CORE_ENTRYPOINT_CANDIDATES = (
    "process_tick",
    "process_tick_v6",
    "process_tick_core",
)


def _truthy(value: Any) -> bool:
    if value is None:
        return False
    text = str(value).strip().lower()
    return text in {"1", "true", "yes", "on", "y"}


def v6_core_runtime_enabled() -> bool:
    return _truthy(os.environ.get(ENV_FLAG))


def v6_core_strict_enabled() -> bool:
    return _truthy(os.environ.get(STRICT_ENV_FLAG))


def _find_v6_core_entrypoint() -> Optional[Callable[..., Any]]:
    if _v6_core is None:
        return None
    for name in _CORE_ENTRYPOINT_CANDIDATES:
        fn = getattr(_v6_core, name, None)
        if callable(fn):
            return fn
    return None


def runtime_adapter_status() -> dict:
    fn = _find_v6_core_entrypoint()
    return {
        "version": ENGINE_ADAPTER_VERSION,
        "env_flag": ENV_FLAG,
        "strict_env_flag": STRICT_ENV_FLAG,
        "v6_enabled": v6_core_runtime_enabled(),
        "v6_strict": v6_core_strict_enabled(),
        "v6_core_imported": _v6_core is not None,
        "v6_core_import_error": repr(_V6_CORE_IMPORT_ERROR) if _V6_CORE_IMPORT_ERROR else None,
        "v6_core_entrypoint": getattr(fn, "__name__", None) if fn else None,
        "fallback": "legacy_engine.process_tick",
    }


def _call_legacy(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    return _legacy_engine.process_tick(tick, prev, brain, send_alert)


def _call_v6_core(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    fn = _find_v6_core_entrypoint()
    if fn is None:
        msg = "T002 V6 core runtime requested but no compatible process_tick entrypoint is available"
        if v6_core_strict_enabled():
            raise RuntimeError(msg)
        return _call_legacy(tick, prev, brain, send_alert)

    try:
        return fn(tick, prev, brain, send_alert)
    except TypeError:
        if v6_core_strict_enabled():
            raise
        return _call_legacy(tick, prev, brain, send_alert)
    except Exception:
        if v6_core_strict_enabled():
            raise
        return _call_legacy(tick, prev, brain, send_alert)


def process_tick(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    if v6_core_runtime_enabled():
        return _call_v6_core(tick, prev, brain, send_alert)
    return _call_legacy(tick, prev, brain, send_alert)


__all__ = [
    "ENGINE_ADAPTER_VERSION",
    "ENV_FLAG",
    "STRICT_ENV_FLAG",
    "process_tick",
    "runtime_adapter_status",
    "v6_core_runtime_enabled",
    "v6_core_strict_enabled",
]

