#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7 — Legacy Behavioral Bridge reader.

Reads fast legacy observations emitted by engine.py:
- output/dashboard_surface/<SYMBOL>/legacy_behavioral_events.jsonl
- output/dashboard_surface/<SYMBOL>/legacy_timecomp_events.jsonl (fallback/merge)

Writes:
- output/dashboard_surface/<SYMBOL>/legacy_behavioral_state.json
- output/dashboard_surface/<SYMBOL>/legacy_behavioral_state.txt

Doctrine: perception only. No trade decision.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

METHOD = "LEGACY_BEHAVIORAL_BRIDGE_V7A"

ROLE_WEIGHTS = {
    "TEMPORAL_LOCK": 1.5,
    "TEMPORAL_RELEASE": 3.0,
    "TACTICAL_REARM_RELEASE": 2.5,
    "ZONE_REPULSION": 2.5,
    "ELASTIC_LOADING_LEGACY": 1.8,
    "ELASTIC_RELEASE_LEGACY": 3.0,
    "PRESSURE_SQUEEZE": 2.6,
    "CROSS_OR_REJECT_IMMINENT": 1.7,
    "ZONE_PRESSURE_HIGH": 1.5,
    "ZONE_PRESSURE_LOW": 1.5,
    "TRAP_OR_REINTEGRATION": 2.0,
    "FORCE_SWITCH": 2.6,
    "MULTI_TF_CONVERGENCE": 2.8,
    "DOMINANCE_CROSS": 1.2,
}

EVENT_TO_ROLE = {
    "TIME_COMP_LOCK": "TEMPORAL_LOCK",
    "TIME_COMP_BREAK": "TEMPORAL_RELEASE",
    "SLINGSHOT": "TACTICAL_REARM_RELEASE",
    "KISS_REJECT": "ZONE_REPULSION",
    "COMPRESSION": "ELASTIC_LOADING_LEGACY",
    "COMPRESSION_BREAK": "ELASTIC_RELEASE_LEGACY",
    "COMPRESSION_SQUEEZE": "PRESSURE_SQUEEZE",
    "APPROACH": "CROSS_OR_REJECT_IMMINENT",
    "EXTREME_HIGH": "ZONE_PRESSURE_HIGH",
    "EXTREME_LOW": "ZONE_PRESSURE_LOW",
    "FAKEOUT": "TRAP_OR_REINTEGRATION",
    "SUPER_SWITCH": "FORCE_SWITCH",
    "CONVERGENCE": "MULTI_TF_CONVERGENCE",
    "CROSS": "DOMINANCE_CROSS",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
            except Exception:
                continue
    except Exception:
        return rows
    return rows


def symbol_dir(symbol: str) -> Path:
    return Path("output") / "dashboard_surface" / symbol.upper()


def normalize_event(ev: dict[str, Any]) -> dict[str, Any]:
    out = dict(ev)
    event = str(out.get("event") or "UNKNOWN").upper()
    role = str(out.get("event_role") or EVENT_TO_ROLE.get(event) or event).upper()
    out["event"] = event
    out["event_role"] = role
    out["layer"] = str(out.get("layer") or infer_layer(role)).upper()
    out["timeframe"] = int(out.get("timeframe") or 0)
    out["tf_label"] = str(out.get("tf_label") or (f"M{out['timeframe']}" if out["timeframe"] else "UNKNOWN"))
    out["bias"] = str(out.get("bias") or out.get("direction") or "UNKNOWN").upper()
    out["technical_risks"] = list(out.get("technical_risks") or [])
    return out


def infer_layer(role: str) -> str:
    if role.startswith("TEMPORAL"):
        return "TEMPORAL"
    if "ELASTIC" in role or "SQUEEZE" in role:
        return "ENERGY"
    if "ZONE" in role:
        return "ZONE_REACTION"
    if "CONVERGENCE" in role:
        return "TACTICAL"
    return "TACTICAL"


def load_events(symbol: str, lookback_minutes: int) -> tuple[list[dict[str, Any]], list[str]]:
    base = symbol_dir(symbol)
    sources = [
        base / "legacy_behavioral_events.jsonl",
        base / "legacy_timecomp_events.jsonl",
    ]
    raw: list[dict[str, Any]] = []
    missing: list[str] = []
    seen = set()
    cutoff = utc_now() - timedelta(minutes=lookback_minutes)
    for path in sources:
        rows = read_jsonl(path)
        if not rows:
            missing.append(path.name)
        for ev in rows:
            n = normalize_event(ev)
            dt = parse_dt(n.get("event_at")) or parse_dt(n.get("detected_at"))
            if dt is None:
                n.setdefault("technical_risks", []).append("EVENT_TIME_PARSE_UNCLEAR")
            elif dt < cutoff:
                continue
            key = (
                n.get("event"), n.get("event_at"), n.get("detected_at"),
                n.get("timeframe"), n.get("price"), n.get("price_to"), n.get("note")
            )
            if key in seen:
                continue
            seen.add(key)
            raw.append(n)
    raw.sort(key=lambda e: str(e.get("event_at") or e.get("detected_at") or ""))
    return raw, missing


def score_events(events: list[dict[str, Any]]) -> float:
    score = 0.0
    now = utc_now()
    for ev in events:
        role = str(ev.get("event_role") or "")
        base = ROLE_WEIGHTS.get(role, 1.0)
        dt = parse_dt(ev.get("event_at")) or parse_dt(ev.get("detected_at"))
        if dt:
            age_min = max(0.0, (now - dt).total_seconds() / 60.0)
            decay = 1.0 if age_min <= 15 else 0.7 if age_min <= 60 else 0.45 if age_min <= 240 else 0.25
        else:
            decay = 0.35
        tf = int(ev.get("timeframe") or 0)
        tf_weight = 1.15 if tf in (1, 5, 15) else 1.0 if tf in (30, 60) else 0.9
        score += base * decay * tf_weight
    return round(score, 2)


def choose_bias(events: list[dict[str, Any]]) -> str:
    weights = Counter()
    for ev in events:
        bias = str(ev.get("bias") or "UNKNOWN").upper()
        if bias not in {"PAIR_UP", "PAIR_DOWN"}:
            continue
        role = str(ev.get("event_role") or "")
        weights[bias] += ROLE_WEIGHTS.get(role, 1.0)
    if not weights:
        return "UNKNOWN"
    up = weights.get("PAIR_UP", 0.0)
    down = weights.get("PAIR_DOWN", 0.0)
    if abs(up - down) < 1.0:
        return "MIXED"
    return "PAIR_UP" if up > down else "PAIR_DOWN"


def derive_state(events: list[dict[str, Any]]) -> tuple[str, str, str, list[str]]:
    roles = {str(e.get("event_role")) for e in events}
    events_set = {str(e.get("event")) for e in events}
    risks: list[str] = []

    if not events:
        return "IDLE", "LEGACY_BEHAVIORAL_IDLE", "NONE", ["NO_LEGACY_BEHAVIORAL_EVENTS"]

    # Strong combos first.
    if "TEMPORAL_RELEASE" in roles and "ELASTIC_RELEASE_LEGACY" in roles:
        return "ACTIVE", "ELASTIC_RELEASE_WITH_TEMPORAL_BREAK", "WAKE_TRADER", risks
    if "TEMPORAL_RELEASE" in roles and "TACTICAL_REARM_RELEASE" in roles:
        return "ACTIVE", "TACTICAL_RELEASE_WITH_TEMPORAL_BREAK", "WAKE_TRADER", risks
    if "ELASTIC_RELEASE_LEGACY" in roles and "ZONE_REPULSION" in roles:
        return "ACTIVE", "ZONE_REPULSION_AFTER_ELASTIC_RELEASE", "WAKE_TRADER", risks
    if "PRESSURE_SQUEEZE" in roles and ("TEMPORAL_LOCK" in roles or "ELASTIC_LOADING_LEGACY" in roles):
        return "WATCH", "PRESSURE_SQUEEZE_IN_COMPRESSION", "WATCH_CONTEXT", risks

    # Single-role states.
    if "TEMPORAL_RELEASE" in roles:
        return "WATCH", "TEMPORAL_RELEASE_LEGACY", "WATCH_CONTEXT", risks
    if "ELASTIC_RELEASE_LEGACY" in roles:
        return "WATCH", "ELASTIC_RELEASE_LEGACY", "WATCH_CONTEXT", risks
    if "TACTICAL_REARM_RELEASE" in roles:
        return "WATCH", "SLINGSHOT_REARM_RELEASE", "WATCH_CONTEXT", risks
    if "ZONE_REPULSION" in roles:
        return "WATCH", "KISS_AND_REJECT_REPULSION", "WATCH_CONTEXT", risks
    if "TEMPORAL_LOCK" in roles or "ELASTIC_LOADING_LEGACY" in roles:
        return "INFO", "LEGACY_COMPRESSION_LOADING", "OBSERVE", risks
    if events_set:
        return "INFO", "LEGACY_EVENTS_PRESENT", "OBSERVE", risks
    return "IDLE", "LEGACY_BEHAVIORAL_IDLE", "NONE", ["NO_CLASSIFIABLE_LEGACY_EVENTS"]


def summarize(symbol: str, events: list[dict[str, Any]], missing: list[str], lookback_minutes: int) -> dict[str, Any]:
    status, state, attention, derived_risks = derive_state(events)
    by_event = Counter(str(e.get("event")) for e in events)
    by_role = Counter(str(e.get("event_role")) for e in events)
    by_layer = Counter(str(e.get("layer")) for e in events)
    by_tf = Counter(str(e.get("tf_label")) for e in events)
    all_risks = []
    for ev in events:
        for r in ev.get("technical_risks") or []:
            if r not in all_risks:
                all_risks.append(r)
    for r in derived_risks:
        if r not in all_risks:
            all_risks.append(r)
    if missing and len(missing) == 2:
        if "NO_LEGACY_BEHAVIORAL_EVENTS" not in all_risks:
            all_risks.append("NO_LEGACY_BEHAVIORAL_EVENTS")

    latest = events[-1] if events else None
    tfs = sorted({int(e.get("timeframe") or 0) for e in events if int(e.get("timeframe") or 0)}, key=lambda x: x)

    return {
        "method": METHOD,
        "symbol": symbol.upper(),
        "generated_at": utc_now().isoformat(),
        "lookback_minutes": lookback_minutes,
        "status": status,
        "state": state,
        "attention": attention,
        "bias": choose_bias(events),
        "score": score_events(events),
        "event_count": len(events),
        "events_by_type": dict(by_event),
        "roles_by_type": dict(by_role),
        "layers": dict(by_layer),
        "timeframes": tfs,
        "tf_labels": [f"M{x}" if x not in (60, 240) else ("H1" if x == 60 else "H4") for x in tfs],
        "latest_event": latest,
        "recent_events": events[-12:],
        "technical_risks": all_risks,
        "source_files_missing_or_empty": missing,
    }


def write_outputs(state: dict[str, Any], output: Path | None, txt: Path | None) -> tuple[Path, Path]:
    sym = state["symbol"]
    base = symbol_dir(sym)
    base.mkdir(parents=True, exist_ok=True)
    json_path = output or (base / "legacy_behavioral_state.json")
    txt_path = txt or (base / "legacy_behavioral_state.txt")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    txt_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    events = ",".join(f"{k}:{v}" for k, v in state["events_by_type"].items()) or "NONE"
    roles = ",".join(f"{k}:{v}" for k, v in state["roles_by_type"].items()) or "NONE"
    layers = ",".join(state["layers"].keys()) or "NONE"
    tfs = ",".join(state["tf_labels"]) or "NONE"
    risks = ",".join(state["technical_risks"]) or "NONE"
    latest = state.get("latest_event") or {}
    lines = [
        f"{sym} | LEGACY BEHAVIORAL BRIDGE V7 | {state['status']} | {state['state']}",
        f"attention={state['attention']} bias={state['bias']} score={state['score']} events={state['event_count']}",
        f"layers={layers} tfs={tfs}",
        f"event_types={events}",
        f"roles={roles}",
        f"latest={latest.get('event', 'NONE')} {latest.get('tf_label', '')} {latest.get('event_at', '')}",
        f"technical_risks={risks}",
    ]
    txt_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, txt_path


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Legacy Behavioral Bridge V7 reader")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--lookback-minutes", type=int, default=240)
    parser.add_argument("--output", default=None)
    parser.add_argument("--txt", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    events, missing = load_events(args.symbol, args.lookback_minutes)
    state = summarize(args.symbol, events, missing, args.lookback_minutes)
    json_path, txt_path = write_outputs(
        state,
        Path(args.output) if args.output else None,
        Path(args.txt) if args.txt else None,
    )
    if args.pretty:
        print(txt_path.read_text(encoding="utf-8"))
        print(f"json={json_path}")
        print(f"txt={txt_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
