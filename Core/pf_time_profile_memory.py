from __future__ import annotations

import argparse
import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


COOLDOWN_MINUTES = {
    "LTF": {"M1": 2, "M5": 7, "M15": 20},
    "MTF": {"M15": 20, "M30": 45, "H1": 90},
    "HTF": {"H1": 90, "H4": 360, "D1": 1440},
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def write_json(path: Path, data: Any, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2 if pretty else None, ensure_ascii=False), encoding="utf-8")


def event_key(event: Dict[str, Any]) -> str:
    raw = "|".join([
        str(event.get("symbol")),
        str(event.get("profile")),
        str(event.get("timeframe")),
        str(event.get("event_type")),
        str(event.get("phase_after") or event.get("phase")),
        str(event.get("bias")),
    ])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def event_from_profile(profile: Dict[str, Any], item: Dict[str, Any]) -> Dict[str, Any]:
    symbol = profile.get("symbol")
    profile_name = profile.get("profile")
    tf = item.get("timeframe")
    tf_state = (profile.get("timeframes") or {}).get(tf, {})

    return {
        "timestamp_utc": item.get("timestamp_utc") or profile.get("timestamp_utc") or now_utc(),
        "created_utc": now_utc(),
        "symbol": symbol,
        "profile": profile_name,
        "timeframe": tf,
        "event_type": item.get("event_type"),
        "phase_before": None,
        "phase_after": item.get("phase") or tf_state.get("phase"),
        "bias": item.get("bias") or tf_state.get("bias"),
        "importance": item.get("importance") or profile.get("attention") or "WATCH",
        "price": item.get("price") or tf_state.get("last_close"),
        "context": {
            "profile_state": profile.get("main_state"),
            "cycle_phase": profile.get("cycle_phase"),
            "dominant_bias": profile.get("dominant_bias"),
            "compression_quality": profile.get("compression_quality"),
            "fake_risk": profile.get("fake_risk"),
            "elastic_state": profile.get("elastic_state"),
            "tf_phase": tf_state.get("phase"),
            "tf_force": tf_state.get("force"),
            "tf_freshness_seconds": tf_state.get("freshness_seconds"),
        },
        "machine_phrase": profile.get("cockpit_phrase"),
        "trader_note": None,
        "review_result": None,
        "lesson": None,
    }


def should_add(memory: Dict[str, Any], event: Dict[str, Any]) -> bool:
    profile = str(event.get("profile") or "")
    tf = str(event.get("timeframe") or "")
    key = event_key(event)
    cooldown = COOLDOWN_MINUTES.get(profile, {}).get(tf, 15)

    now_dt = parse_dt(event.get("timestamp_utc")) or datetime.now(timezone.utc)
    for old in memory.get("events", []):
        if old.get("key") != key:
            continue
        old_dt = parse_dt(old.get("timestamp_utc")) or parse_dt(old.get("created_utc"))
        if old_dt is None:
            return False
        elapsed = (now_dt - old_dt).total_seconds() / 60.0
        if elapsed < cooldown:
            return False
    return True


def render_md(memory: Dict[str, Any]) -> str:
    symbol = memory.get("symbol")
    profile = memory.get("profile")
    lines = [
        f"# PowerFlow V7.3.7 - {profile} Session Memory - {symbol}",
        "",
        f"Updated UTC: {memory.get('updated_utc')}",
        "",
        "## Moments marquants",
        "",
    ]

    events = memory.get("events", [])
    if not events:
        lines.append("- Aucun moment marquant memorise pour cette session.")
    else:
        for e in events[-80:]:
            lines.append(
                f"- {e.get('timestamp_utc')} | {e.get('timeframe')} | "
                f"{e.get('event_type')} | {e.get('phase_after')} | "
                f"{e.get('bias')} | {e.get('importance')} | price={e.get('price')}"
            )
            phrase = e.get("machine_phrase")
            if phrase:
                lines.append(f"  - Machine: {phrase}")

    lines += [
        "",
        "## Revue trader",
        "",
        "### Ce que j'ai vu",
        "- ",
        "",
        "### Ce que j'ai ressenti",
        "- ",
        "",
        "### Ce que PowerFlow a vu avant moi",
        "- ",
        "",
        "### Ce que PowerFlow a rate",
        "- ",
        "",
        "### Lecon",
        "- ",
        "",
    ]
    return "\n".join(lines)


def archive_memory(memory: Dict[str, Any], active_path: Path) -> None:
    symbol = memory.get("symbol") or "UNKNOWN"
    profile = str(memory.get("profile") or "profile").lower()
    date = now_utc()[:10]
    archive_dir = Path("output/journal_sessions") / symbol
    archive_json = archive_dir / f"{date}_{profile}_session_memory.json"
    archive_md = archive_dir / f"{date}_{profile}_session_memory.md"
    archive_dir.mkdir(parents=True, exist_ok=True)
    write_json(archive_json, memory, pretty=True)
    archive_md.write_text(render_md(memory), encoding="utf-8")


def update_memory(profile_path: Path, memory_path: Path, md_path: Path, pretty: bool = False) -> Dict[str, Any]:
    profile = read_json(profile_path, {})
    if not profile:
        raise FileNotFoundError(f"profile not found or invalid: {profile_path}")

    symbol = profile.get("symbol") or "UNKNOWN"
    profile_name = profile.get("profile") or "UNKNOWN"

    memory = read_json(memory_path, {
        "method": "TIME_PROFILE_SESSION_MEMORY_V737B",
        "symbol": symbol,
        "profile": profile_name,
        "created_utc": now_utc(),
        "updated_utc": now_utc(),
        "events": [],
    })

    memory["symbol"] = symbol
    memory["profile"] = profile_name
    memory["updated_utc"] = now_utc()

    added = 0
    for item in profile.get("recent_important_events", []):
        ev = event_from_profile(profile, item)
        ev["key"] = event_key(ev)
        if should_add(memory, ev):
            memory.setdefault("events", []).append(ev)
            added += 1

    memory["events"] = memory.get("events", [])[-300:]
    memory["summary"] = {
        "events_total": len(memory.get("events", [])),
        "events_added": added,
        "last_event": memory.get("events", [{}])[-1] if memory.get("events") else None,
    }

    write_json(memory_path, memory, pretty=pretty)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(render_md(memory), encoding="utf-8")
    archive_memory(memory, memory_path)
    return memory


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.3.7 time profile session memory")
    parser.add_argument("--profile-json", required=True)
    parser.add_argument("--memory-json", required=True)
    parser.add_argument("--memory-md", required=True)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    memory = update_memory(
        profile_path=Path(args.profile_json),
        memory_path=Path(args.memory_json),
        md_path=Path(args.memory_md),
        pretty=args.pretty,
    )

    print(
        f"TIME_PROFILE_MEMORY_OK | symbol={memory.get('symbol')} | profile={memory.get('profile')} | "
        f"events={memory.get('summary', {}).get('events_total')} | "
        f"added={memory.get('summary', {}).get('events_added')} | out={args.memory_json}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
