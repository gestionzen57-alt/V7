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


CORE_VERSION = "T002_V6_CORE_DETACHED_V1"


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


def tick_context_to_dict(context: EngineTickContext) -> dict[str, Any]:
    return asdict(context)


__all__ = [
    "CORE_VERSION",
    "EngineTickContext",
    "derive_tick_context",
    "tick_context_to_dict",
]
