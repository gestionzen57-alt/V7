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
