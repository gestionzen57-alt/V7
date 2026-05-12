# PF_BROKER_TIME_ALIGNMENT_V737E
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def _pf_compact_tf_time(tf_data):
    proj = {}
    if isinstance(tf_data, dict):
        proj = tf_data.get("time_projection") or {}
    return {
        "broker": proj.get("timestamp_broker") or tf_data.get("last_timestamp_utc") if isinstance(tf_data, dict) else None,
        "local_reference": proj.get("timestamp_local_reference"),
        "broker_offset_hours": proj.get("broker_offset_hours"),
        "freshness_seconds_local": proj.get("freshness_seconds_local"),
    }



PROFILES = ["LTF", "MTF", "HTF"]


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2 if pretty else None, ensure_ascii=False),
        encoding="utf-8",
    )


def summarize_memory(memory: Dict[str, Any]) -> Dict[str, Any]:
    events = memory.get("events") or []
    last_events = events[-8:] if isinstance(events, list) else []
    return {
        "events_total": len(events) if isinstance(events, list) else 0,
        "last_events": last_events,
        "last_event": last_events[-1] if last_events else None,
    }


def summarize_profile(symbol: str, profile_name: str) -> Dict[str, Any]:
    p = profile_name.lower()
    base = Path("output/dashboard_surface") / symbol

    profile_path = base / f"{p}_profile.json"
    memory_path = base / f"{p}_session_memory.json"
    memory_md_path = base / f"{p}_session_memory.md"

    profile = read_json(profile_path, {})
    memory = read_json(memory_path, {})

    if not profile:
        return {
            "symbol": symbol,
            "profile": profile_name,
            "status": "MISSING",
            "attention": "UNKNOWN",
            "main_state": "UNKNOWN",
            "dominant_bias": "UNKNOWN",
            "fake_risk": "UNKNOWN",
            "compression_quality": "UNKNOWN",
            "elastic_state": "UNKNOWN",
            "timeframes": {},
            "memory": {"events_total": 0, "last_events": []},
            "paths": {
                "profile": str(profile_path),
                "memory_json": str(memory_path),
                "memory_md": str(memory_md_path),
            },
            "technical_risks": [f"{profile_name}_PROFILE_MISSING"],
        }

    return {
        "symbol": symbol,
        "profile": profile_name,
        "status": "OK",
        "timestamp_utc": profile.get("timestamp_utc"),
        "attention": profile.get("attention", "UNKNOWN"),
        "main_state": profile.get("main_state", "UNKNOWN"),
        "cycle_phase": profile.get("cycle_phase", "UNKNOWN"),
        "dominant_bias": profile.get("dominant_bias", "UNKNOWN"),
        "fake_risk": profile.get("fake_risk", "UNKNOWN"),
        "compression_quality": profile.get("compression_quality", "UNKNOWN"),
        "elastic_state": profile.get("elastic_state", "UNKNOWN"),
        "cockpit_phrase": profile.get("cockpit_phrase", ""),
        "timeframes": profile.get("timeframes", {}),
        "recent_important_events": profile.get("recent_important_events", []),
        "memory": summarize_memory(memory),
        "paths": {
            "profile": str(profile_path),
            "memory_json": str(memory_path),
            "memory_md": str(memory_md_path),
        },
        "technical_risks": profile.get("technical_risks", []),
    }


def infer_global_status(rows: list[Dict[str, Any]]) -> str:
    attentions = [str(r.get("attention", "")).upper() for r in rows]
    if "WAKE_TRADER" in attentions:
        return "TIME_PROFILE_WAKE_TRADER"
    if "WATCH" in attentions:
        return "TIME_PROFILE_WATCH"
    if all(str(r.get("status")) == "MISSING" for r in rows):
        return "TIME_PROFILE_MISSING"
    return "TIME_PROFILE_QUIET"


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Normalize PowerFlow time profiles for dashboard")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--output", default="output/dashboard_surface/time_profiles_dashboard.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    profiles = [summarize_profile(args.symbol, p) for p in PROFILES]
    out = {
        "method": "TIME_PROFILES_DASHBOARD_NORMALIZED_V737C",
        "symbol": args.symbol,
        "global_status": infer_global_status(profiles),
        "profiles": profiles,
        "note": "One readable page per time profile: LTF, MTF, HTF. Memory keeps important session moments.",
    }

    write_json(Path(args.output), out, pretty=args.pretty)
    print(
        f"TIME_PROFILES_NORMALIZE_OK | symbol={args.symbol} | "
        f"global_status={out['global_status']} | profiles={len(profiles)} | out={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
