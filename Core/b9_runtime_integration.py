"""PowerFlow B9 runtime bridge.

Read-only integration layer between the live scheduler and PowerFlowEngineB9.
It builds the engine window contract, calls process_window(), and persists created
nodes as JSON files under output/b9_nodes_live/.

Design constraints:
- no DB write here;
- Telegram disabled by default;
- no dashboard mutation;
- no import from cockpit/dashboard/telegram modules;
- failures are returned as structured runtime errors instead of crashing the scheduler.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


VALID_STATUSES = {"NODE_CREATED", "FALSE_BIRTH", "NO_EVENT", "NODE_SUPPRESSED"}


def _utc_now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _sanitize_timestamp_for_filename(timestamp: Any) -> str:
    raw = str(timestamp or _utc_now_iso())
    return (
        raw.replace(":", "")
        .replace("-", "")
        .replace(".", "")
        .replace(" ", "T")
        .replace("/", "")
        .replace("\\", "")
    )


def _get_price_path_value(window_data: Dict[str, Any], key: str, default: Any = None) -> Any:
    price_path = window_data.get("price_path")
    if isinstance(price_path, dict) and key in price_path:
        return price_path.get(key, default)
    return window_data.get(key, default)


def build_engine_window(symbol: str, window_data: Dict[str, Any]) -> Dict[str, Any]:
    """Build the stable PowerFlowEngineB9 process_window() payload.

    The scheduler may provide a flat payload or a payload already containing
    price_path. This helper normalizes both forms without mutating the source.
    """
    if not isinstance(window_data, dict):
        raise TypeError("window_data must be a dict")

    symbol = str(symbol or window_data.get("symbol") or "GBPUSD").upper()
    timestamp = window_data.get("timestamp") or window_data.get("time") or _utc_now_iso()

    zone_low = _safe_float(window_data.get("zone_low"), _safe_float(window_data.get("low"), 0.0))
    zone_high = _safe_float(window_data.get("zone_high"), _safe_float(window_data.get("high"), zone_low))
    current_price = _safe_float(
        window_data.get("current_price"),
        _safe_float(window_data.get("price"), (zone_low + zone_high) / 2 if zone_high else zone_low),
    )

    price_path = {
        "price_min": _safe_float(_get_price_path_value(window_data, "price_min", zone_low), zone_low),
        "price_max": _safe_float(_get_price_path_value(window_data, "price_max", zone_high), zone_high),
        "price_open": _safe_float(_get_price_path_value(window_data, "price_open", current_price), current_price),
        "price_close": _safe_float(_get_price_path_value(window_data, "price_close", current_price), current_price),
        "ticks_total": _safe_int(_get_price_path_value(window_data, "ticks_total", 0), 0),
        "ticks_inside_zone": _safe_int(_get_price_path_value(window_data, "ticks_inside_zone", 0), 0),
        "ticks_inside_center_band": _safe_int(_get_price_path_value(window_data, "ticks_inside_center_band", 0), 0),
        "dwell_seconds_inside_zone": _safe_float(_get_price_path_value(window_data, "dwell_seconds_inside_zone", 0.0), 0.0),
        "dwell_seconds_inside_center": _safe_float(_get_price_path_value(window_data, "dwell_seconds_inside_center", 0.0), 0.0),
        "max_center_penetration_ratio": _safe_float(_get_price_path_value(window_data, "max_center_penetration_ratio", 0.0), 0.0),
        "price_exits_original_side": bool(_get_price_path_value(window_data, "price_exits_original_side", False)),
        "rejection_distance_pips": _safe_float(_get_price_path_value(window_data, "rejection_distance_pips", 0.0), 0.0),
        "rejection_speed_pips_per_min": _safe_float(_get_price_path_value(window_data, "rejection_speed_pips_per_min", 0.0), 0.0),
        "net_progress_pips": _safe_float(_get_price_path_value(window_data, "net_progress_pips", 0.0), 0.0),
        "is_pullback_context": bool(_get_price_path_value(window_data, "is_pullback_context", False)),
    }

    return {
        "symbol": symbol,
        "timestamp": timestamp,
        "zone_low": zone_low,
        "zone_high": zone_high,
        "current_price": current_price,
        "source_stack": window_data.get("source_stack", "SCHEDULER_RUNTIME_WINDOW"),
        "zone_touch_history": window_data.get("zone_touch_history", []),
        "zone_bars_since_touch": _safe_int(window_data.get("zone_bars_since_touch", 0), 0),
        "price_path": price_path,
        "raw_bias": window_data.get("raw_bias", "NEUTRAL"),
        "packet_strength": _safe_float(window_data.get("packet_strength", 0.5), 0.5),
        "previous_scene_state": window_data.get("previous_scene_state", {}),
    }


class B9RuntimeBridge:
    """Runtime adapter around PowerFlowEngineB9."""

    def __init__(self, config: Optional[Dict[str, Any]] = None, output_dir: Optional[str | Path] = None) -> None:
        self.config = dict(config or {})
        self.config.setdefault("ENABLE_TELEGRAM", False)
        self.config.setdefault("DB_PATH", "powerflow.db")
        self.output_dir = Path(output_dir or self.config.get("OUTPUT_DIR", "output/b9_nodes_live"))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._engine = None
        self._engine_error: Optional[str] = None

    def _load_engine(self):
        if self._engine is not None:
            return self._engine
        try:
            from pf_engine_b9 import PowerFlowEngineB9  # type: ignore

            self._engine = PowerFlowEngineB9(self.config)
            return self._engine
        except Exception as exc:  # pragma: no cover - depends on live repo
            self._engine_error = f"{type(exc).__name__}: {exc}"
            raise

    def save_node(self, symbol: str, node: Dict[str, Any]) -> Path:
        timestamp = node.get("timestamp") or node.get("time") or _utc_now_iso()
        filename = f"{symbol}_{_sanitize_timestamp_for_filename(timestamp)}.json"
        filepath = self.output_dir / filename
        with filepath.open("w", encoding="utf-8") as handle:
            json.dump(node, handle, indent=2, ensure_ascii=False)
        return filepath

    def process_tick_window(self, symbol: str, window_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            window = build_engine_window(symbol, window_data)
            engine = self._load_engine()
            result = engine.process_window(window)
            if not isinstance(result, dict):
                return {
                    "status": "B9_RUNTIME_ERROR",
                    "symbol": window["symbol"],
                    "error": "PowerFlowEngineB9.process_window returned non-dict result",
                }

            result.setdefault("symbol", window["symbol"])
            if result.get("status") == "NODE_CREATED" and isinstance(result.get("node"), dict):
                node = dict(result["node"])
                node.setdefault("symbol", window["symbol"])
                node.setdefault("timestamp", window["timestamp"])
                saved_path = self.save_node(window["symbol"], node)
                result["node_saved_path"] = str(saved_path)
                print(f"[B9] Node created: {node.get('verdict', node.get('price_verdict_candidate', 'UNKNOWN'))} @ {node.get('current_price', window['current_price'])}")

            if result.get("status") not in VALID_STATUSES:
                result.setdefault("runtime_note", "Unexpected B9 status observed by runtime bridge")
            return result
        except Exception as exc:
            return {
                "status": "B9_RUNTIME_ERROR",
                "symbol": str(symbol or "GBPUSD").upper(),
                "error": f"{type(exc).__name__}: {exc}",
            }


_BRIDGE: Optional[B9RuntimeBridge] = None


def init_b9_runtime(config: Optional[Dict[str, Any]] = None, output_dir: Optional[str | Path] = None) -> B9RuntimeBridge:
    global _BRIDGE
    _BRIDGE = B9RuntimeBridge(config=config, output_dir=output_dir)
    return _BRIDGE


def get_b9_runtime() -> B9RuntimeBridge:
    global _BRIDGE
    if _BRIDGE is None:
        _BRIDGE = B9RuntimeBridge({"ENABLE_TELEGRAM": False, "DB_PATH": os.environ.get("POWERFLOW_DB_PATH", "powerflow.db")})
    return _BRIDGE


def process_tick_window_b9(symbol: str, window_data: Dict[str, Any]) -> Dict[str, Any]:
    """Scheduler-facing function: call this once per GBPUSD tick window."""
    return get_b9_runtime().process_tick_window(symbol, window_data)
