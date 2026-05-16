#!/usr/bin/env python3
"""T009 Phase 1B CLI: Battlefield Flux + dashboard + Telegram dry-run."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Dict, List


def _import_phase1a():
    try:
        import pf_battlefield_flux
        return pf_battlefield_flux
    except ImportError:
        from Core import pf_battlefield_flux
        return pf_battlefield_flux


def _import_dashboard():
    try:
        import pf_battlefield_flux_dashboard
        return pf_battlefield_flux_dashboard
    except ImportError:
        from Core import pf_battlefield_flux_dashboard
        return pf_battlefield_flux_dashboard


def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


def get_t009_flags() -> Dict[str, Any]:
    defaults = {
        "POWERFLOW_T009_TICK_ARCHIVE_WRITE": _env_int("POWERFLOW_T009_TICK_ARCHIVE_WRITE", 0),
        "POWERFLOW_T009_USE_BATTLEFIELD_FLUX": _env_int("POWERFLOW_T009_USE_BATTLEFIELD_FLUX", 0),
        "POWERFLOW_T009_SOURCE_MODE": os.getenv("POWERFLOW_T009_SOURCE_MODE", "auto"),
        "POWERFLOW_T009_ALLOW_M1_FALLBACK": _env_int("POWERFLOW_T009_ALLOW_M1_FALLBACK", 1),
        "POWERFLOW_T009_ENABLE_TELEGRAM": _env_int("POWERFLOW_T009_ENABLE_TELEGRAM", 0),
        "POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION": _env_int("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION", 0),
        "POWERFLOW_T009_ENABLE_DASHBOARD": _env_int("POWERFLOW_T009_ENABLE_DASHBOARD", 1),
        "POWERFLOW_T009_MAX_LOOKBACK_MIN": _env_int("POWERFLOW_T009_MAX_LOOKBACK_MIN", 120),
        "POWERFLOW_T009_DRY_RUN": _env_int("POWERFLOW_T009_DRY_RUN", 1),
    }
    try:
        import config_t009_flags
    except Exception:
        # config_t009_flags validates at import time. In safety tests, invalid env
        # combinations can raise ValueError before the CLI can print its explicit
        # Phase 1B safety message. Fall back to raw env-derived defaults so
        # safety_checks() handles the failure in stdout with a controlled exit.
        return defaults
    if hasattr(config_t009_flags, "get_t009_flags"):
        loaded = config_t009_flags.get_t009_flags()
        if isinstance(loaded, dict):
            defaults.update(loaded)
            return defaults
    obj = getattr(config_t009_flags, "FLAGS", None)
    if obj is None:
        return defaults
    raw = asdict(obj) if is_dataclass(obj) else {k: v for k, v in getattr(obj, "__dict__", {}).items() if not k.startswith("_")}
    mapping = {
        "TICK_ARCHIVE_WRITE": "POWERFLOW_T009_TICK_ARCHIVE_WRITE",
        "USE_BATTLEFIELD_FLUX": "POWERFLOW_T009_USE_BATTLEFIELD_FLUX",
        "SOURCE_MODE": "POWERFLOW_T009_SOURCE_MODE",
        "ALLOW_M1_FALLBACK": "POWERFLOW_T009_ALLOW_M1_FALLBACK",
        "ENABLE_TELEGRAM": "POWERFLOW_T009_ENABLE_TELEGRAM",
        "ENABLE_ENGINE_INTEGRATION": "POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION",
        "ENABLE_DASHBOARD": "POWERFLOW_T009_ENABLE_DASHBOARD",
        "MAX_LOOKBACK_MIN": "POWERFLOW_T009_MAX_LOOKBACK_MIN",
        "DRY_RUN": "POWERFLOW_T009_DRY_RUN",
    }
    for short, full in mapping.items():
        if short in raw:
            defaults[full] = int(raw[short]) if isinstance(raw[short], bool) else raw[short]
    return defaults


def _manual_state(phase1a: Any, symbol: str, lookback_min: int) -> Dict[str, Any]:
    if not hasattr(phase1a, "BattlefieldFlux"):
        return {"symbol": symbol, "lookback_min": lookback_min, "source_mode": "UNKNOWN", "data_visibility": "BLIND", "tick_count": 0, "events": [], "clusters": [], "context": {"symbol": symbol, "source_mode": "UNKNOWN", "data_visibility": "BLIND", "lookback_min": lookback_min}}
    bf = phase1a.BattlefieldFlux()
    ticks = bf.load_ticks_primary(symbol, lookback_min)
    source_used = "primary_ticks"
    if not ticks:
        ticks = bf.load_ticks_fallback(symbol, lookback_min)
        source_used = "fallback_m1_bars"
    buckets = bf.build_time_price_buckets(ticks) if ticks else []
    events: List[Dict[str, Any]] = []
    for bucket in buckets:
        features = bucket.get("features", {})
        battle = bf.score_battle(features)
        absorp = bf.score_absorption(features)
        if battle >= 0.70:
            events.append(bf.build_event_evidence_packet("T009_BATTLE_LEVEL_BORN", (features.get("price_min"), features.get("price_max")), {"battle_score": battle, "absorption_score": absorp}, bucket.get("ticks", []), features))
        if absorp >= 0.65:
            events.append(bf.build_event_evidence_packet("T009_ABSORPTION_CLUSTER", (features.get("price_min"), features.get("price_max")), {"battle_score": battle, "absorption_score": absorp}, bucket.get("ticks", []), features))
    source_mode = ticks[0].get("source_mode", "UNKNOWN") if ticks else "UNKNOWN"
    visibility = ticks[0].get("data_visibility", "LIVE" if source_mode in {"TIMER_1S_SAMPLE", "ONTICK_RAW"} else "BLIND") if ticks else "BLIND"
    return {"symbol": symbol, "lookback_min": lookback_min, "source_used": source_used, "source_mode": source_mode, "data_visibility": visibility, "tick_count": len(ticks), "events": events, "clusters": buckets, "context": {"symbol": symbol, "source_mode": source_mode, "data_visibility": visibility, "lookback_min": lookback_min}}


def compute_state(symbol: str, lookback_min: int, flags: Dict[str, Any]) -> Dict[str, Any]:
    phase1a = _import_phase1a()
    if hasattr(phase1a, "compute_state"):
        try:
            return phase1a.compute_state(symbol=symbol, lookback_min=lookback_min, flags=flags)
        except TypeError:
            return phase1a.compute_state(symbol=symbol, lookback_min=lookback_min)
    return _manual_state(phase1a, symbol, lookback_min)


def write_json(path: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def safety_checks(flags: Dict[str, Any]):
    if int(flags.get("POWERFLOW_T009_ENABLE_TELEGRAM", 0)) != 0:
        print("ERROR: Phase 1B requires POWERFLOW_T009_ENABLE_TELEGRAM=0")
        sys.exit(1)
    if int(flags.get("POWERFLOW_T009_DRY_RUN", 1)) != 1:
        print("ERROR: Phase 1B requires POWERFLOW_T009_DRY_RUN=1")
        sys.exit(1)
    if int(flags.get("POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION", 0)) != 0:
        print("ERROR: Phase 1B requires POWERFLOW_T009_ENABLE_ENGINE_INTEGRATION=0")
        sys.exit(1)


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T009 Phase 1B - Battlefield Flux with Dashboard")
    parser.add_argument("--symbol", required=True)
    parser.add_argument("--lookback-min", type=int, default=30)
    parser.add_argument("--output", default="output")
    parser.add_argument("--enable-dashboard", action="store_true")
    parser.add_argument("--dry-run-telegram", action="store_true")
    args = parser.parse_args(argv)
    flags = get_t009_flags()
    flags["POWERFLOW_T009_OUTPUT_DIR"] = args.output
    safety_checks(flags)
    if args.lookback_min > int(flags.get("POWERFLOW_T009_MAX_LOOKBACK_MIN", 120)):
        print("ERROR: lookback exceeds POWERFLOW_T009_MAX_LOOKBACK_MIN")
        return 1
    dashboard = _import_dashboard()
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)
    state = compute_state(args.symbol, args.lookback_min, flags)
    state.setdefault("symbol", args.symbol)
    state.setdefault("lookback_min", args.lookback_min)
    state.setdefault("context", {})
    if isinstance(state["context"], dict):
        state["context"].setdefault("symbol", args.symbol)
        state["context"].setdefault("lookback_min", args.lookback_min)
    events = state.get("events", []) if isinstance(state.get("events", []), list) else []
    state_path, events_path = out / "battlefield_flux_state.json", out / "battlefield_flux_events.json"
    write_json(state_path, state)
    write_json(events_path, events)
    if args.enable_dashboard:
        widget = dashboard.build_dashboard_evidence_widget(state=state, events=events)
        widget_path = out / "battlefield_flux_dashboard_widget.json"
        write_json(widget_path, widget)
        dashboard.log_phase1b_event("DASHBOARD_WIDGET_BUILT", {"path": str(widget_path), "events": len(events)}, str(out))
        print(f"Dashboard widget: {widget_path}")
    if args.dry_run_telegram:
        if not events:
            write_json(out / "telegram_dry_run_log.json", [])
        for event in events:
            packet = dashboard.format_trader_alert_packet(event, state.get("context", {}))
            result = dashboard.route_to_telegram_dry_run(packet, flags)
            dashboard.log_phase1b_event("TELEGRAM_DRY_RUN", result, str(out))
            print(f"Telegram dry-run: {result}")
    print(f"State: {state_path}")
    print(f"Events: {events_path}")
    print(f"Source: {state.get('source_mode', 'unknown')}")
    print(f"Ticks: {state.get('tick_count', 0)}")
    print(f"Events count: {len(events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

