from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def profile_line(profile: Dict[str, Any]) -> str:
    name = profile.get("profile", "UNKNOWN")
    state = profile.get("main_state", "UNKNOWN")
    bias = profile.get("dominant_bias", "UNKNOWN")
    fake = profile.get("fake_risk", "UNKNOWN")
    attention = profile.get("attention", "UNKNOWN")
    last = ((profile.get("memory") or {}).get("last_event") or {})
    last_tf = last.get("timeframe", "-")
    last_event = last.get("event_type", "-")
    last_price = last.get("price", "-")
    return f"{name}: {attention} | {state} | {bias} | fake={fake} | last={last_tf}/{last_event}/price={last_price}"


def compact_time_profiles(time_profiles: Dict[str, Any]) -> Dict[str, Any]:
    profiles = time_profiles.get("profiles") or []
    by_profile = {str(p.get("profile", "UNKNOWN")): p for p in profiles if isinstance(p, dict)}

    compact = {
        "global_status": time_profiles.get("global_status", "UNKNOWN"),
        "symbol": time_profiles.get("symbol", "GBPUSD"),
        "summary_lines": [],
        "profiles": {},
    }

    for name in ("LTF", "MTF", "HTF"):
        p = by_profile.get(name) or {}
        last = ((p.get("memory") or {}).get("last_event") or {})
        compact["summary_lines"].append(profile_line(p))
        compact["profiles"][name] = {
            "attention": p.get("attention", "UNKNOWN"),
            "main_state": p.get("main_state", "UNKNOWN"),
            "cycle_phase": p.get("cycle_phase", "UNKNOWN"),
            "dominant_bias": p.get("dominant_bias", "UNKNOWN"),
            "fake_risk": p.get("fake_risk", "UNKNOWN"),
            "compression_quality": p.get("compression_quality", "UNKNOWN"),
            "elastic_state": p.get("elastic_state", "UNKNOWN"),
            "cockpit_phrase": p.get("cockpit_phrase", ""),
            "last_event": {
                "timestamp_utc": last.get("timestamp_utc"),
                "timeframe": last.get("timeframe"),
                "event_type": last.get("event_type"),
                "phase_after": last.get("phase_after"),
                "bias": last.get("bias"),
                "importance": last.get("importance"),
                "price": last.get("price"),
            },
            "technical_risks": p.get("technical_risks", []),
        }

    return compact


def append_txt(base_txt: str, compact: Dict[str, Any]) -> str:
    lines = []
    lines.append("")
    lines.append("TIME PROFILES")
    lines.append(f"global={compact.get('global_status', 'UNKNOWN')}")
    for line in compact.get("summary_lines", []):
        lines.append(f"- {line}")
    lines.append("")
    lines.append("PAGE LINKS")
    lines.append("- dashboard_ltf_profile.html")
    lines.append("- dashboard_mtf_profile.html")
    lines.append("- dashboard_htf_profile.html")
    return base_txt.rstrip() + "\n" + "\n".join(lines) + "\n"


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Enrich trader cockpit with time profile summary")
    parser.add_argument("--cockpit-json", default="output/dashboard_surface/trader_cockpit.json")
    parser.add_argument("--cockpit-txt", default="output/dashboard_surface/trader_cockpit.txt")
    parser.add_argument("--time-profiles", default="output/dashboard_surface/time_profiles_dashboard.json")
    args = parser.parse_args(list(argv) if argv is not None else None)

    cockpit_json_path = Path(args.cockpit_json)
    cockpit_txt_path = Path(args.cockpit_txt)
    time_profiles_path = Path(args.time_profiles)

    cockpit = read_json(cockpit_json_path, {})
    time_profiles = read_json(time_profiles_path, {})

    compact = compact_time_profiles(time_profiles)

    if isinstance(cockpit, dict):
        cockpit["time_profiles"] = compact
        cockpit["time_profile_pages"] = {
            "LTF": "dashboard_ltf_profile.html",
            "MTF": "dashboard_mtf_profile.html",
            "HTF": "dashboard_htf_profile.html",
        }
        write_json(cockpit_json_path, cockpit)

    base_txt = cockpit_txt_path.read_text(encoding="utf-8") if cockpit_txt_path.exists() else ""
    cockpit_txt_path.write_text(append_txt(base_txt, compact), encoding="utf-8")

    print(
        "TRADER_COCKPIT_TIME_PROFILES_ENRICH_OK | "
        f"global={compact.get('global_status')} | json={cockpit_json_path} | txt={cockpit_txt_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
