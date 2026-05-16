"""
T009 Phase 2A - Battlefield Flux engine integration adapter.

Contract:
- convert Battlefield Flux perception events into engine-compatible events;
- inject events only behind POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION;
- preserve existing engine behavior when the flag is off or Battlefield Flux fails;
- perform no writes to powerflow.db or tick_archive.db.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, MutableSequence, Optional
import os

try:  # Core folder execution
    from pf_battlefield_flux import BattlefieldFlux  # type: ignore
except Exception:  # Repo-root execution
    try:
        from Core.pf_battlefield_flux import BattlefieldFlux  # type: ignore
    except Exception:  # Isolated tests may monkeypatch the adapter.bf object.
        BattlefieldFlux = None  # type: ignore


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _flag_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() in {"1", "true", "yes", "on", "enabled"}


def is_engine_integration_enabled(flags: Optional[Any] = None) -> bool:
    """Return True only when T009 engine integration is explicitly enabled."""
    if flags is not None:
        if isinstance(flags, dict):
            return _flag_bool(
                flags.get("ENABLE_ENGINE_INTEGRATION", flags.get("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION")),
                False,
            )
        return _flag_bool(getattr(flags, "ENABLE_ENGINE_INTEGRATION", False), False)

    env_value = os.getenv("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION")
    if env_value is not None:
        return _flag_bool(env_value, False)

    try:
        from config_t009_flags import FLAGS as T009_FLAGS  # type: ignore
    except Exception:
        try:
            from Core.config_t009_flags import FLAGS as T009_FLAGS  # type: ignore
        except Exception:
            return False
    return _flag_bool(getattr(T009_FLAGS, "ENABLE_ENGINE_INTEGRATION", False), False)


def _normalize_zone(zone: Any) -> Dict[str, Any]:
    if isinstance(zone, dict):
        normalized = dict(zone)
        if "level" not in normalized:
            if normalized.get("center") is not None:
                normalized["level"] = normalized.get("center")
            elif normalized.get("low") is not None and normalized.get("high") is not None:
                normalized["level"] = (float(normalized["low"]) + float(normalized["high"])) / 2.0
        return normalized
    if isinstance(zone, (list, tuple)) and len(zone) >= 2:
        low = float(zone[0])
        high = float(zone[1])
        return {"low": low, "high": high, "level": (low + high) / 2.0}
    return {}


def _extract_score(event: Dict[str, Any], *names: str) -> float:
    for name in names:
        value = event.get(name)
        if value is not None:
            try:
                return float(value)
            except (TypeError, ValueError):
                return 0.0
    scores = event.get("scores")
    if isinstance(scores, dict):
        for name in names:
            value = scores.get(name)
            if value is not None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return 0.0
    return 0.0


class BattlefieldFluxAdapter:
    """Adapter boundary between T009 Battlefield Flux and the engine event queue."""

    def __init__(
        self,
        lookback_min: int = 30,
        battlefield: Optional[Any] = None,
        db_path: str = "tick_archive.db",
        fallback_db: str = "powerflow.db",
    ) -> None:
        self.lookback_min = int(lookback_min)
        if battlefield is not None:
            self.bf = battlefield
        elif BattlefieldFlux is not None:
            self.bf = BattlefieldFlux(db_path=db_path, fallback_db=fallback_db)  # type: ignore[operator]
        else:
            self.bf = None
        self.last_state: Optional[Dict[str, Any]] = None

    def integrate_battlefield_events(
        self,
        tick: Dict[str, Any],
        engine_state: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Compute Battlefield Flux state and return engine-compatible events.

        This method is fail-closed: no Battlefield Flux exception can break the
        existing engine path. The engine hook is responsible for calling this
        only when the feature flag is enabled.
        """
        if self.bf is None:
            self.last_state = {"events": [], "error": "BattlefieldFlux unavailable"}
            return []

        symbol = str(tick.get("symbol") or (engine_state or {}).get("symbol") or "GBPUSD")
        try:
            if hasattr(self.bf, "compute_state"):
                bf_state = self.bf.compute_state(symbol=symbol, lookback_min=self.lookback_min)
            else:
                ticks = self.bf.load_ticks_primary(symbol, self.lookback_min)
                if not ticks and hasattr(self.bf, "load_ticks_fallback"):
                    ticks = self.bf.load_ticks_fallback(symbol, self.lookback_min)
                buckets = self.bf.build_time_price_buckets(ticks) if ticks else []
                bf_state = {"symbol": symbol, "events": [], "ticks": ticks, "buckets": buckets}
        except Exception as exc:
            self.last_state = {"events": [], "error": str(exc), "symbol": symbol}
            return []

        if not isinstance(bf_state, dict):
            bf_state = {"events": [], "raw_state": bf_state, "symbol": symbol}

        bf_events = bf_state.get("events", []) or []
        engine_events = [self._convert_event(event, tick) for event in bf_events if isinstance(event, dict)]
        self.last_state = bf_state
        return engine_events

    def _convert_event(self, bf_event: Dict[str, Any], tick: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a Battlefield Flux event or packet into engine event format."""
        internal_type = str(bf_event.get("event_type") or bf_event.get("type") or "UNKNOWN")
        event_name = internal_type[5:] if internal_type.startswith("T009_") else internal_type
        if not event_name.startswith("BATTLEFIELD_"):
            event_type = f"BATTLEFIELD_{event_name}"
        else:
            event_type = event_name

        zone = _normalize_zone(bf_event.get("zone", {}))
        level = bf_event.get("level")
        if level is None:
            level = zone.get("level") or zone.get("center")
        if level is None and zone.get("low") is not None and zone.get("high") is not None:
            level = (float(zone["low"]) + float(zone["high"])) / 2.0

        battle_score = _extract_score(bf_event, "battle_score")
        absorption_score = _extract_score(bf_event, "absorption_score")
        confidence = bf_event.get("confidence")
        if confidence is None:
            confidence = max(battle_score, absorption_score)
        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        timestamp = bf_event.get("timestamp") or bf_event.get("ts_utc") or tick.get("ts_utc") or _utcnow_iso()
        cluster_features = bf_event.get("cluster_features") or bf_event.get("features") or {}

        return {
            "event_type": event_type,
            "symbol": tick.get("symbol", bf_event.get("symbol", "GBPUSD")),
            "timestamp": timestamp,
            "level": level,
            "zone": zone,
            "confidence": confidence,
            "battle_score": battle_score,
            "absorption_score": absorption_score,
            "source": "battlefield_flux",
            "source_mode": bf_event.get("source_mode", "UNKNOWN"),
            "data_visibility": bf_event.get("data_visibility", "UNKNOWN"),
            "metadata": {
                "dwell_time_sec": zone.get("dwell_time_sec", bf_event.get("dwell_time_sec", 0)),
                "cluster_features": cluster_features,
                "raw_event_type": internal_type,
            },
        }


def maybe_integrate_battlefield_events(
    tick: Dict[str, Any],
    engine_state: Optional[Dict[str, Any]],
    event_queue: MutableSequence[Dict[str, Any]],
    adapter: Optional[BattlefieldFluxAdapter] = None,
    flags: Optional[Any] = None,
) -> MutableSequence[Dict[str, Any]]:
    """
    Inject Battlefield Flux events into an existing event queue when flag is ON.

    Returns the same queue object. If the flag is OFF or adapter fails, the queue
    is returned unchanged to guarantee no regression in existing behavior.
    """
    if not is_engine_integration_enabled(flags):
        return event_queue

    adapter = adapter or BattlefieldFluxAdapter()
    try:
        bf_events = adapter.integrate_battlefield_events(tick, engine_state or {})
    except Exception:
        return event_queue

    for event in bf_events:
        event_queue.append(event)
    return event_queue


__all__ = [
    "BattlefieldFluxAdapter",
    "is_engine_integration_enabled",
    "maybe_integrate_battlefield_events",
]
