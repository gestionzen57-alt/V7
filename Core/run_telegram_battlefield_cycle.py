#!/usr/bin/env python3
"""
T009 Phase 2B - Telegram LIVE Battlefield Flux cycle.

Default behavior is safe: without --enable-telegram it prints dry-run packets only.
LIVE send requires:
- --enable-telegram
- POWERFLOW_T009_ENABLE_TELEGRAM=1
- POWERFLOW_T009_DRY_RUN=0
- TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID for actual API routing
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pf_telegram_battlefield import send_battlefield_alert  # noqa: E402


def _flag_int(value: Any, default: int = 0) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, int):
        return 1 if value != 0 else 0
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "on", "enabled"}:
        return 1
    if text in {"0", "false", "no", "off", "disabled"}:
        return 0
    return default


def get_t009_flags() -> Dict[str, Any]:
    """Read Phase 2B flags directly from env to avoid config import hard-fails."""
    return {
        "POWERFLOW_T009_ENABLE_TELEGRAM": _flag_int(os.getenv("POWERFLOW_T009_ENABLE_TELEGRAM"), 0),
        "POWERFLOW_T009_DRY_RUN": _flag_int(os.getenv("POWERFLOW_T009_DRY_RUN"), 1),
        "POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION": _flag_int(os.getenv("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION"), 0),
        "POWERFLOW_T009_MAX_LOOKBACK_MIN": int(os.getenv("POWERFLOW_T009_MAX_LOOKBACK_MIN", "120")),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID", "YOUR_CHAT_ID"),
    }


def _fallback_packet_from_event(event: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    zone = event.get("zone") or {}
    scores = event.get("scores") if isinstance(event.get("scores"), dict) else {}
    battle = event.get("battle_score", scores.get("battle_score", 0.0))
    absorption = event.get("absorption_score", scores.get("absorption_score", 0.0))
    confidence = event.get("confidence")
    if confidence is None:
        confidence = max(float(battle or 0.0), float(absorption or 0.0))
    return {
        "event_type": event.get("event_type", "T009_BATTLEFIELD_EVENT"),
        "symbol": event.get("symbol", symbol),
        "timestamp": event.get("timestamp") or event.get("ts_utc"),
        "zone": zone,
        "battle_score": float(battle or 0.0),
        "absorption_score": float(absorption or 0.0),
        "confidence": float(confidence or 0.0),
        "data_visibility": event.get("data_visibility", "LIVE"),
        "source_mode": event.get("source_mode", "UNKNOWN"),
        "live_telegram_allowed": event.get("live_telegram_allowed", event.get("data_visibility") != "RECONSTRUCTED"),
    }


def _packet_from_event(event: Dict[str, Any], state: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    try:
        from pf_battlefield_flux_dashboard import format_trader_alert_packet  # type: ignore

        context = state.get("context", {}) if isinstance(state, dict) else {}
        packet = format_trader_alert_packet(event, context)
        # Ensure Phase 2B fields exist even if Phase 1B packet format is lean.
        fallback = _fallback_packet_from_event(event, symbol)
        fallback.update(packet)
        return fallback
    except Exception:
        return _fallback_packet_from_event(event, symbol)


def compute_state(symbol: str, lookback_min: int, output: str = "output") -> Dict[str, Any]:
    """Compute Phase 1A/1B battlefield state when local modules are present."""
    try:
        from run_battlefield_flux_with_dashboard import compute_state as phase1b_compute_state  # type: ignore

        flags = get_t009_flags()
        return phase1b_compute_state(symbol, lookback_min, flags)
    except Exception:
        pass

    try:
        from pf_battlefield_flux import BattlefieldFlux  # type: ignore

        bf = BattlefieldFlux()
        return bf.compute_state(symbol=symbol, lookback_min=lookback_min)
    except Exception:
        return {
            "symbol": symbol,
            "lookback_min": lookback_min,
            "events": [],
            "context": {
                "symbol": symbol,
                "data_visibility": "UNKNOWN",
                "source_mode": "UNKNOWN",
            },
            "output": output,
        }


def _load_events_file(path: str, symbol: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return [event for event in payload if isinstance(event, dict)]
    if isinstance(payload, dict):
        events = payload.get("events", [])
        if isinstance(events, list):
            return [event for event in events if isinstance(event, dict)]
    raise ValueError(f"No events list found in {path} for {symbol}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T009 Phase 2B - Telegram LIVE battlefield alerts")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--lookback-min", type=int, default=30)
    parser.add_argument("--enable-telegram", action="store_true")
    parser.add_argument("--events-file", default="", help="Optional JSON events file for controlled validation")
    parser.add_argument("--output", default="output")
    args = parser.parse_args(argv)

    flags = get_t009_flags()

    if args.enable_telegram:
        if int(flags.get("POWERFLOW_T009_ENABLE_TELEGRAM", 0)) != 1:
            print("ERROR: --enable-telegram requires POWERFLOW_T009_ENABLE_TELEGRAM=1")
            return 1
        if int(flags.get("POWERFLOW_T009_DRY_RUN", 1)) != 0:
            print("ERROR: LIVE Telegram requires POWERFLOW_T009_DRY_RUN=0")
            return 1

    if args.events_file:
        events = _load_events_file(args.events_file, args.symbol)
        state: Dict[str, Any] = {"symbol": args.symbol, "events": events, "context": {"symbol": args.symbol}}
    else:
        state = compute_state(args.symbol, args.lookback_min, args.output)
        events = state.get("events", []) if isinstance(state, dict) else []

    if not events:
        print("No battlefield events detected.")
        return 0

    print(f"Detected {len(events)} battlefield events for {args.symbol}")
    for index, event in enumerate(events, 1):
        packet = _packet_from_event(event, state, args.symbol)
        if args.enable_telegram:
            result = send_battlefield_alert(packet, flags)
            print(f"Event {index}/{len(events)}: {result}")
        else:
            message = packet.get("message_trader_fr") or packet.get("event_type", "battlefield event")
            print(f"Event {index}/{len(events)}: {message} (dry-run, use --enable-telegram for LIVE)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
