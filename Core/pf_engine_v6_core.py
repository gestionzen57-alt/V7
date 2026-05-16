# pf_engine_v6_core.py
# PowerFlow V7.6.7 - T002 detached pure helpers
#
# This module is a safe extraction destination for legacy engine.py.
# It is intentionally NOT wired into runtime yet.
#
# Rules:
# - no legacy engine dependency
# - no capture bridge dependency
# - no DB write
# - no UI or outbound transmission dependency
# - no alert sending
# - pure tick/prev derived context only

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


CORE_VERSION = "T002_V6_CORE_DETACHED_V2_LEGACY_SURFACE"


@dataclass(frozen=True)
class EngineTickContext:
    # Derived tick context for future extraction from engine.process_tick.
    # This is a small immutable measurement packet, not a decision object.

    symbol: str | None
    timestamp: Any
    price: float | None
    prev_price: float | None
    price_delta: float | None
    bid: float | None
    ask: float | None
    spread: float | None


@dataclass(frozen=True)
class LegacyTickSurface:
    # Static legacy field surface seen in engine.process_tick.
    # This is a compatibility measurement object only.

    dev_a: str | None
    dev_b: str | None
    val_a: float | None
    val_b: float | None
    gap: float | None
    timeframe: Any
    spread: float | None


def _read_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _derive_price(tick: Any) -> float | None:
    # Priority: explicit price/mid/close, then bid/ask midpoint, then bid or ask alone.
    for field in ("price", "mid", "close"):
        value = _to_float(_read_attr(tick, field))
        if value is not None:
            return value

    bid = _to_float(_read_attr(tick, "bid"))
    ask = _to_float(_read_attr(tick, "ask"))

    if bid is not None and ask is not None:
        return (bid + ask) / 2.0
    if bid is not None:
        return bid
    if ask is not None:
        return ask

    return None


def derive_tick_context(tick: Any, prev: Any, symbol: str | None = None) -> EngineTickContext:
    # Build an immutable pure context from current and previous ticks.

    price = _derive_price(tick)
    prev_price = _derive_price(prev)

    bid = _to_float(_read_attr(tick, "bid"))
    ask = _to_float(_read_attr(tick, "ask"))

    spread = None
    if bid is not None and ask is not None:
        spread = ask - bid

    price_delta = None
    if price is not None and prev_price is not None:
        price_delta = price - prev_price

    resolved_symbol = symbol
    if resolved_symbol is None:
        resolved_symbol = _read_attr(tick, "symbol", None)

    timestamp = _read_attr(tick, "timestamp", _read_attr(tick, "time", None))

    return EngineTickContext(
        symbol=resolved_symbol,
        timestamp=timestamp,
        price=price,
        prev_price=prev_price,
        price_delta=price_delta,
        bid=bid,
        ask=ask,
        spread=spread,
    )


def derive_legacy_tick_surface(tick: Any) -> LegacyTickSurface:
    # Build the static legacy tick surface used by engine.process_tick.
    # It supports object-like ticks and dict-like ticks.

    explicit_spread = _to_float(_read_attr(tick, "spread"))
    bid = _to_float(_read_attr(tick, "bid"))
    ask = _to_float(_read_attr(tick, "ask"))

    derived_spread = None
    if bid is not None and ask is not None:
        derived_spread = ask - bid

    spread = explicit_spread if explicit_spread is not None else derived_spread

    return LegacyTickSurface(
        dev_a=_read_attr(tick, "dev_a", None),
        dev_b=_read_attr(tick, "dev_b", None),
        val_a=_to_float(_read_attr(tick, "val_a", None)),
        val_b=_to_float(_read_attr(tick, "val_b", None)),
        gap=_to_float(_read_attr(tick, "gap", None)),
        timeframe=_read_attr(tick, "timeframe", None),
        spread=spread,
    )


def tick_context_to_dict(context: EngineTickContext) -> dict[str, Any]:
    return asdict(context)


def legacy_tick_surface_to_dict(surface: LegacyTickSurface) -> dict[str, Any]:
    return asdict(surface)


__all__ = [
    "CORE_VERSION",
    "EngineTickContext",
    "LegacyTickSurface",
    "derive_tick_context",
    "derive_legacy_tick_surface",
    "tick_context_to_dict",
    "legacy_tick_surface_to_dict",
]


# === T002-S V6 CORE RUNTIME ENTRYPOINT START ===
# Pure runtime entrypoint for the feature-flagged adapter boundary.
# The function below keeps the legacy call signature while returning a deterministic
# V6 tick surface. It does not write storage, mutate UI layers, or transmit messages.

import models


PF_ENGINE_V6_CORE_RUNTIME_VERSION = "T002_S_V6_CORE_RUNTIME_ENTRYPOINT_V1"


def _pf_v6_get_tick_attr(tick, name: str, default=None):
    if tick is None:
        return default
    if isinstance(tick, dict):
        return tick.get(name, default)
    return getattr(tick, name, default)


def _pf_v6_float_or_none(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pf_v6_string_or_none(value):
    if value is None:
        return None
    return str(value)


def _pf_v6_tick_surface(tick) -> dict:
    fields = {
        "symbol": _pf_v6_string_or_none(_pf_v6_get_tick_attr(tick, "symbol")),
        "timestamp": _pf_v6_string_or_none(_pf_v6_get_tick_attr(tick, "timestamp")),
        "timeframe": _pf_v6_string_or_none(_pf_v6_get_tick_attr(tick, "timeframe")),
        "val_a": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "val_a")),
        "val_b": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "val_b")),
        "dev_a": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "dev_a")),
        "dev_b": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "dev_b")),
        "gap": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "gap")),
        "spread": _pf_v6_float_or_none(_pf_v6_get_tick_attr(tick, "spread")),
    }

    val_a = fields["val_a"]
    val_b = fields["val_b"]
    if fields["gap"] is None and val_a is not None and val_b is not None:
        fields["gap"] = val_a - val_b

    return fields


def _pf_v6_tick_delta(current: dict, previous: dict) -> dict:
    deltas = {}
    for key in ("val_a", "val_b", "dev_a", "dev_b", "gap", "spread"):
        cur = current.get(key)
        prev = previous.get(key)
        if cur is not None and prev is not None:
            deltas[key] = cur - prev
        else:
            deltas[key] = None
    return deltas


def process_tick(tick: models.Tick, prev: models.Tick, brain: dict, send_alert):
    current_surface = _pf_v6_tick_surface(tick)
    previous_surface = _pf_v6_tick_surface(prev)
    delta = _pf_v6_tick_delta(current_surface, previous_surface)

    return {
        "engine": "pf_engine_v6_core",
        "version": PF_ENGINE_V6_CORE_RUNTIME_VERSION,
        "event_type": "V6_CORE_TICK_SURFACE",
        "symbol": current_surface.get("symbol"),
        "timestamp": current_surface.get("timestamp"),
        "timeframe": current_surface.get("timeframe"),
        "surface": current_surface,
        "previous_surface": previous_surface,
        "delta": delta,
        "alerts": [],
        "side_effects": False,
        "brain_mutated": False,
        "route": "v6_core",
    }


try:
    __all__ = list(__all__)
except NameError:
    __all__ = []

for _name in [
    "PF_ENGINE_V6_CORE_RUNTIME_VERSION",
    "process_tick",
]:
    if _name not in __all__:
        __all__.append(_name)
# === T002-S V6 CORE RUNTIME ENTRYPOINT END ===

# T009_PHASE2A_ENGINE_HOOK_START
# Battlefield Flux engine integration wrapper. Appended by install_t009_phase2a_from_zip.ps1.
# It is fail-closed and preserves existing behavior when POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION=0.
try:
    _t009_original_process_tick = process_tick  # type: ignore[name-defined]
except NameError:
    _t009_original_process_tick = None

if _t009_original_process_tick is not None:
    def process_tick(*args, **kwargs):  # type: ignore[no-redef]
        _t009_result = _t009_original_process_tick(*args, **kwargs)
        try:
            from pf_engine_battlefield_adapter import maybe_integrate_battlefield_events
            _t009_tick = args[0] if len(args) >= 1 and isinstance(args[0], dict) else kwargs.get("tick", {})
            _t009_state = args[1] if len(args) >= 2 and isinstance(args[1], dict) else kwargs.get("state", {})
            if isinstance(_t009_result, list):
                maybe_integrate_battlefield_events(_t009_tick, _t009_state, _t009_result)
            elif isinstance(_t009_result, dict) and isinstance(_t009_result.get("events"), list):
                maybe_integrate_battlefield_events(_t009_tick, _t009_state, _t009_result["events"])
        except Exception:
            return _t009_result
        return _t009_result
# T009_PHASE2A_ENGINE_HOOK_END
