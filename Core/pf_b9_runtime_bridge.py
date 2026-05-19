"""
PowerFlow V7.6.7 B9 runtime bridge.

Purpose:
- Initialize PowerFlowEngineB9 once.
- Convert live runtime tick-window dictionaries into the engine window format.
- Call engine.process_window(window) for each tick window.
- Push created nodes to cockpit_b9_feed.push_b9_node().
- Keep Telegram disabled by default for DRY-RUN.

Doctrine:
- Perception transmitted, not a trading decision.
- No BUY/SELL wording.
- Fast alerting, qualified by runtime status and source quality.
"""
from __future__ import annotations

import os
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Mapping, MutableMapping, Optional


DEFAULT_REQUIRED_FIELDS = (
    "timestamp",
    "zone_low",
    "zone_high",
    "current_price",
    "price_min",
    "price_max",
    "price_open",
    "price_close",
    "ticks_total",
)

RAW_BIAS_MAP = {
    "BULLISH": "UP",
    "BEARISH": "DOWN",
    "PAIR_UP": "UP",
    "PAIR_DOWN": "DOWN",
    "UP": "UP",
    "DOWN": "DOWN",
    "NEUTRAL": "NEUTRAL",
    "MIXED": "NEUTRAL",
    "UNKNOWN": "NEUTRAL",
    None: "NEUTRAL",
}


class B9RuntimeIntegrationError(RuntimeError):
    """Raised when B9 runtime integration cannot build a valid engine window."""


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_raw_bias(raw_bias: Any) -> str:
    """Map legacy/live bias labels into the B9 requalifier vocabulary."""
    if isinstance(raw_bias, str):
        key = raw_bias.strip().upper()
    else:
        key = raw_bias
    return RAW_BIAS_MAP.get(key, "NEUTRAL")


def build_engine_config(
    enable_telegram: Optional[bool] = None,
    db_path: str = "powerflow.db",
    telegram_bot_token: Optional[str] = None,
    telegram_chat_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build a safe engine config. Telegram is disabled unless explicitly enabled."""
    if enable_telegram is None:
        enable_telegram = os.getenv("B9_ENABLE_TELEGRAM", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }

    return {
        "ENABLE_TELEGRAM": bool(enable_telegram),
        "DB_PATH": db_path,
        "TELEGRAM_CONFIG": {
            "bot_token": telegram_bot_token if telegram_bot_token is not None else os.getenv("TELEGRAM_BOT_TOKEN", ""),
            "chat_id": telegram_chat_id if telegram_chat_id is not None else os.getenv("TELEGRAM_CHAT_ID", ""),
        },
    }


def validate_window_data(window_data: Mapping[str, Any], required_fields: Iterable[str] = DEFAULT_REQUIRED_FIELDS) -> None:
    missing = [field for field in required_fields if field not in window_data]
    if missing:
        raise B9RuntimeIntegrationError(f"Missing runtime window fields for B9: {', '.join(missing)}")


def build_b9_window(symbol: str, window_data: Mapping[str, Any]) -> Dict[str, Any]:
    """Convert runtime window_data into the exact B9 engine window dict."""
    validate_window_data(window_data)

    price_path = {
        "price_min": _as_float(window_data.get("price_min")),
        "price_max": _as_float(window_data.get("price_max")),
        "price_open": _as_float(window_data.get("price_open")),
        "price_close": _as_float(window_data.get("price_close")),
        "ticks_total": _as_int(window_data.get("ticks_total")),
        "ticks_inside_zone": _as_int(window_data.get("ticks_inside_zone", 0)),
        "ticks_inside_center_band": _as_int(window_data.get("ticks_inside_center_band", 0)),
        "dwell_seconds_inside_zone": _as_float(window_data.get("dwell_seconds_inside_zone", 0.0)),
        "dwell_seconds_inside_center": _as_float(window_data.get("dwell_seconds_inside_center", 0.0)),
        "max_center_penetration_ratio": _as_float(window_data.get("max_center_penetration_ratio", 0.0)),
        "price_exits_original_side": bool(window_data.get("price_exits_original_side", False)),
        "rejection_distance_pips": _as_float(window_data.get("rejection_distance_pips", 0.0)),
        "rejection_speed_pips_per_min": _as_float(window_data.get("rejection_speed_pips_per_min", 0.0)),
        "net_progress_pips": _as_float(window_data.get("net_progress_pips", 0.0)),
        "is_pullback_context": bool(window_data.get("is_pullback_context", False)),
    }

    return {
        "symbol": str(symbol or window_data.get("symbol", "GBPUSD")),
        "timestamp": str(window_data["timestamp"]),
        "zone_low": _as_float(window_data["zone_low"]),
        "zone_high": _as_float(window_data["zone_high"]),
        "current_price": _as_float(window_data["current_price"]),
        "zone_touch_history": list(window_data.get("zone_touch_history", [])),
        "zone_bars_since_touch": _as_int(window_data.get("zone_bars_since_touch", 0)),
        "price_path": price_path,
        "raw_bias": normalize_raw_bias(window_data.get("raw_bias", "NEUTRAL")),
        "packet_strength": _as_float(window_data.get("packet_strength", 0.5), 0.5),
        "previous_scene_state": dict(window_data.get("previous_scene_state", {}) or {}),
    }


def _default_log_path() -> Path:
    return Path("output") / "b9_runtime_integration.log"


def append_runtime_log(message: str, log_path: Optional[Path] = None) -> None:
    """Append a timestamped runtime log line. Logging failure must never kill runtime."""
    try:
        target = log_path or _default_log_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.utcnow().isoformat(timespec="seconds")
        with target.open("a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {message}\n")
    except Exception:
        # Runtime must keep flowing even if logging path is unavailable.
        pass


@dataclass
class B9RuntimeBridge:
    """Bridge used by the live scheduler to call B9 on every tick window."""

    enable_telegram: Optional[bool] = None
    db_path: str = "powerflow.db"
    engine_factory: Optional[Callable[[Dict[str, Any]], Any]] = None
    push_node: Optional[Callable[[Dict[str, Any]], Any]] = None
    log_path: Optional[Path] = None
    fail_soft: bool = True
    _engine: Any = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._engine = self._build_engine()
        if self.push_node is None:
            self.push_node = self._import_push_node()

    def _build_engine(self) -> Any:
        config = build_engine_config(enable_telegram=self.enable_telegram, db_path=self.db_path)
        if self.engine_factory is not None:
            return self.engine_factory(config)
        try:
            from pf_engine_b9 import PowerFlowEngineB9  # type: ignore
        except Exception as exc:  # pragma: no cover - covered via fake factory in tests
            raise B9RuntimeIntegrationError(f"Cannot import PowerFlowEngineB9: {exc}") from exc
        return PowerFlowEngineB9(config)

    @staticmethod
    def _import_push_node() -> Optional[Callable[[Dict[str, Any]], Any]]:
        try:
            from cockpit_b9_feed import push_b9_node  # type: ignore

            return push_b9_node
        except Exception:
            return None

    @property
    def engine(self) -> Any:
        return self._engine

    def process_tick_window(self, symbol: str, window_data: Mapping[str, Any]) -> Dict[str, Any]:
        """Build B9 window, run engine, push node if created, and return engine result."""
        try:
            window = build_b9_window(symbol, window_data)
            result = self._engine.process_window(window)
            if not isinstance(result, MutableMapping):
                result = {"status": "INVALID_ENGINE_RESULT", "raw_result": result}

            if result.get("status") == "NODE_CREATED" and result.get("node"):
                if self.push_node is not None:
                    self.push_node(result["node"])
                else:
                    append_runtime_log("NODE_CREATED but cockpit_b9_feed.push_b9_node unavailable", self.log_path)
            return dict(result)
        except Exception as exc:
            append_runtime_log(f"B9_RUNTIME_ERROR {exc}\n{traceback.format_exc()}", self.log_path)
            if not self.fail_soft:
                raise
            return {
                "status": "B9_RUNTIME_ERROR",
                "error": str(exc),
                "node": None,
            }


def sample_runtime_window(timestamp: str = "2026-05-19T14:30:00") -> Dict[str, Any]:
    """Synthetic GBPUSD runtime window used for smoke tests and dry-run boot validation."""
    return {
        "symbol": "GBPUSD",
        "timestamp": timestamp,
        "zone_low": 1.2500,
        "zone_high": 1.2520,
        "current_price": 1.2510,
        "zone_touch_history": [1, 2, 1],
        "zone_bars_since_touch": 3,
        "price_min": 1.2495,
        "price_max": 1.2525,
        "price_open": 1.2500,
        "price_close": 1.2510,
        "ticks_total": 150,
        "ticks_inside_zone": 80,
        "ticks_inside_center_band": 20,
        "dwell_seconds_inside_zone": 45.0,
        "dwell_seconds_inside_center": 10.0,
        "max_center_penetration_ratio": 0.65,
        "price_exits_original_side": False,
        "rejection_distance_pips": 8.5,
        "rejection_speed_pips_per_min": 2.3,
        "net_progress_pips": -3.2,
        "is_pullback_context": True,
        "raw_bias": "BEARISH",
        "packet_strength": 0.72,
        "previous_scene_state": {},
    }


def infer_symbol_and_window_from_call(args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> tuple[Optional[str], Optional[Mapping[str, Any]]]:
    """Infer symbol/window_data from a live process_tick_window call without knowing its exact signature."""
    if "symbol" in kwargs and "window_data" in kwargs:
        return str(kwargs["symbol"]), kwargs["window_data"]
    if "window_data" in kwargs:
        wd = kwargs["window_data"]
        return str(kwargs.get("symbol") or getattr(wd, "get", lambda *_: "GBPUSD")("symbol", "GBPUSD")), wd
    if len(args) >= 2 and isinstance(args[1], Mapping):
        return str(args[0]), args[1]
    if len(args) >= 1 and isinstance(args[0], Mapping):
        wd = args[0]
        return str(wd.get("symbol", "GBPUSD")), wd
    return None, None


def attach_b9_to_existing_process_tick_window(globals_dict: MutableMapping[str, Any], bridge: B9RuntimeBridge) -> bool:
    """Wrap an existing process_tick_window function so B9 runs after the base runtime processing.

    Returns True if wrapping was applied, False otherwise.
    """
    original = globals_dict.get("process_tick_window")
    if original is None or getattr(original, "_b9_wrapped", False):
        return False

    def wrapped_process_tick_window(*args: Any, **kwargs: Any) -> Any:
        base_result = original(*args, **kwargs)
        symbol, window_data = infer_symbol_and_window_from_call(args, kwargs)
        if symbol is not None and window_data is not None:
            b9_result = bridge.process_tick_window(symbol, window_data)
            if isinstance(base_result, dict):
                base_result.setdefault("b9_runtime_result", b9_result)
                return base_result
            return {"base_result": base_result, "b9_runtime_result": b9_result}
        append_runtime_log("B9 wrapper active but could not infer symbol/window_data")
        return base_result

    wrapped_process_tick_window._b9_wrapped = True  # type: ignore[attr-defined]
    globals_dict["process_tick_window"] = wrapped_process_tick_window
    return True
