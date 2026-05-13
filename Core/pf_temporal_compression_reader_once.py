#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_temporal_compression_reader_once.py

PowerFlow V7 — TEMPORAL_COMPRESSION_BRIDGE

Rôle :
- lit les alertes legacy TIME-COMP BREAK / LOCK écrites en JSONL
- normalise en état V7 TEMPORAL
- détecte propagation multi-TF, break, lock, acceptance zone
- sort time_compression_state.json/txt pour Perception Spine

Entrée :
    output/dashboard_surface/<SYMBOL>/legacy_timecomp_events.jsonl

Sorties :
    output/dashboard_surface/<SYMBOL>/time_compression_state.json
    output/dashboard_surface/<SYMBOL>/time_compression_state.txt

Usage :
    python pf_temporal_compression_reader_once.py --symbol GBPUSD --lookback-minutes 240 --pretty
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from statistics import median
from typing import Any, Iterable


TF_ORDER = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "M60": 60, "H4": 240, "M240": 240}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_dt(value: Any) -> datetime | None:
    if value in (None, "", 0, "0"):
        return None
    try:
        if isinstance(value, (int, float)) or str(value).replace(".", "", 1).isdigit():
            ts = float(value)
            if ts > 10_000_000_000:
                ts /= 1000.0
            return datetime.fromtimestamp(ts, tz=timezone.utc)
    except Exception:
        pass
    try:
        s = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def iso(dt: datetime | None) -> str | None:
    return dt.astimezone(timezone.utc).isoformat() if dt else None


def norm_tf(raw: Any) -> str:
    if raw is None:
        return "UNKNOWN"
    s = str(raw).upper().strip()
    if s.startswith("M") or s.startswith("H"):
        return s
    if s.isdigit():
        n = int(s)
        if n == 60:
            return "H1"
        if n == 240:
            return "H4"
        return f"M{n}"
    return s


def tf_rank(tf: str) -> int:
    return TF_ORDER.get(norm_tf(tf), 9999)


def safe_float(v: Any) -> float | None:
    try:
        if v is None:
            return None
        x = float(v)
        return None if x != x else x
    except Exception:
        return None


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except Exception:
            continue
    return rows


def event_kind(ev: dict[str, Any]) -> str:
    raw = str(ev.get("event_type") or ev.get("event") or ev.get("type") or ev.get("state") or "").upper()
    if "LOCK" in raw:
        return "LOCK"
    if "BREAK" in raw:
        return "BREAK"
    return "EVENT"


def event_bias(ev: dict[str, Any]) -> str:
    raw = str(ev.get("bias") or "").upper()
    if raw in {"PAIR_DOWN", "DOWN", "BEARISH"}:
        return "PAIR_DOWN"
    if raw in {"PAIR_UP", "UP", "BULLISH"}:
        return "PAIR_UP"

    pf = safe_float(ev.get("price_from"))
    pt = safe_float(ev.get("price_to"))
    if pf is not None and pt is not None:
        if pt < pf:
            return "PAIR_DOWN"
        if pt > pf:
            return "PAIR_UP"
    return "UNKNOWN"


def choose_acceptance_zone(lock_events: list[dict[str, Any]], all_events: list[dict[str, Any]]) -> float | None:
    values = []
    for ev in lock_events:
        for key in ("center", "price_to", "bid"):
            v = safe_float(ev.get(key))
            if v is not None and v > 0:
                values.append(v)
                break
    if not values:
        for ev in all_events[-5:]:
            v = safe_float(ev.get("price_to") or ev.get("bid"))
            if v is not None and v > 0:
                values.append(v)
    if not values:
        return None
    try:
        return round(float(median(values)), 5)
    except Exception:
        return values[-1]


def summarize(symbol: str, rows: list[dict[str, Any]], lookback_minutes: int) -> dict[str, Any]:
    now = utc_now()
    cutoff = now - timedelta(minutes=lookback_minutes)

    cleaned = []
    for ev in rows:
        if str(ev.get("symbol", symbol)).upper() != symbol.upper():
            continue
        dt = parse_dt(ev.get("event_at") or ev.get("detected_at"))
        if dt is None:
            continue
        if dt < cutoff:
            continue
        e = dict(ev)
        e["_dt"] = dt
        e["_kind"] = event_kind(ev)
        e["_tf"] = norm_tf(ev.get("timeframe") or ev.get("tf"))
        e["_bias"] = event_bias(ev)
        cleaned.append(e)

    cleaned.sort(key=lambda x: x["_dt"])

    breaks = [e for e in cleaned if e["_kind"] == "BREAK"]
    locks = [e for e in cleaned if e["_kind"] == "LOCK"]

    break_tfs = sorted({e["_tf"] for e in breaks}, key=tf_rank)
    lock_tfs = sorted({e["_tf"] for e in locks}, key=tf_rank)
    all_tfs = sorted({e["_tf"] for e in cleaned}, key=tf_rank)

    down_breaks = [e for e in breaks if e["_bias"] == "PAIR_DOWN"]
    up_breaks = [e for e in breaks if e["_bias"] == "PAIR_UP"]

    if len(down_breaks) > len(up_breaks):
        bias = "PAIR_DOWN"
    elif len(up_breaks) > len(down_breaks):
        bias = "PAIR_UP"
    else:
        bias = cleaned[-1]["_bias"] if cleaned else "UNKNOWN"

    multi_tf_break = len(break_tfs) >= 2
    post_release_lock = len(locks) >= 1 and bool(breaks) and locks[-1]["_dt"] >= breaks[0]["_dt"]
    lower_or_upper_acceptance = post_release_lock and bias in {"PAIR_DOWN", "PAIR_UP"}

    evidence = []
    if multi_tf_break:
        evidence.append("MULTI_TF_BREAK")
    if post_release_lock:
        evidence.append("POST_RELEASE_LOCK")
    if lower_or_upper_acceptance and bias == "PAIR_DOWN":
        evidence.append("LOWER_PRICE_ACCEPTANCE")
    if lower_or_upper_acceptance and bias == "PAIR_UP":
        evidence.append("HIGHER_PRICE_ACCEPTANCE")

    for tf in all_tfs:
        tf_break = any(e["_tf"] == tf for e in breaks)
        tf_lock = any(e["_tf"] == tf for e in locks)
        if tf_break and tf_lock:
            evidence.append(f"{tf}_BREAK_THEN_LOCK")

    if multi_tf_break and post_release_lock and bias == "PAIR_DOWN":
        state = "TIME_COMP_RELEASE_DOWN_LOCKED"
        event_type = "MULTI_TF_TIME_COMPRESSION_RELEASE"
    elif multi_tf_break and post_release_lock and bias == "PAIR_UP":
        state = "TIME_COMP_RELEASE_UP_LOCKED"
        event_type = "MULTI_TF_TIME_COMPRESSION_RELEASE"
    elif multi_tf_break and bias == "PAIR_DOWN":
        state = "TIME_COMP_RELEASE_DOWN"
        event_type = "MULTI_TF_TIME_COMPRESSION_RELEASE"
    elif multi_tf_break and bias == "PAIR_UP":
        state = "TIME_COMP_RELEASE_UP"
        event_type = "MULTI_TF_TIME_COMPRESSION_RELEASE"
    elif breaks:
        state = "TIME_COMP_BREAK_ACTIVE"
        event_type = "TIME_COMPRESSION_BREAK"
    elif locks:
        state = "TIME_COMP_LOCK_ACTIVE"
        event_type = "TIME_COMPRESSION_LOCK"
    else:
        state = "TIME_COMP_IDLE"
        event_type = "NONE"

    score = 0.0
    score += min(len(breaks), 4) * 1.4
    score += min(len(locks), 4) * 0.9
    score += max(0, len(break_tfs) - 1) * 1.2
    score += 1.0 if post_release_lock else 0.0
    score = round(min(score, 10.0), 2)

    if score >= 6.5:
        level = "ACTIVE"
    elif score >= 3.5:
        level = "WATCH"
    elif cleaned:
        level = "INFO"
    else:
        level = "IDLE"

    leader_tf = break_tfs[0] if break_tfs else (all_tfs[0] if all_tfs else None)
    relay_tf = break_tfs[1] if len(break_tfs) >= 2 else None
    confirmation_tf = break_tfs[-1] if len(break_tfs) >= 3 else None

    technical_risks = []
    if not cleaned:
        technical_risks.append("NO_LEGACY_TIMECOMP_EVENTS")
    if breaks and not locks:
        technical_risks.append("RELEASE_WITHOUT_POST_LOCK")
    if len(break_tfs) == 1 and breaks:
        technical_risks.append("SINGLE_TF_BREAK_ONLY")
    if bias == "UNKNOWN" and cleaned:
        technical_risks.append("TIMECOMP_DIRECTION_UNCLEAR")

    public_events = []
    for e in cleaned[-20:]:
        public_events.append({
            "event_type": e.get("event_type"),
            "event_at": iso(e["_dt"]),
            "detected_at": e.get("detected_at"),
            "timeframe": e["_tf"],
            "bias": e["_bias"],
            "price_from": e.get("price_from"),
            "price_to": e.get("price_to"),
            "ticks": e.get("ticks"),
        })

    return {
        "symbol": symbol.upper(),
        "layer": "TEMPORAL",
        "state": state,
        "level": level,
        "bias": bias,
        "score": score,
        "timeframes": all_tfs,
        "breaks": len(breaks),
        "locks": len(locks),
        "acceptance_zone": choose_acceptance_zone(locks, cleaned),
        "leader_tf": leader_tf,
        "relay_tf": relay_tf,
        "confirmation_tf": confirmation_tf,
        "event_type": event_type,
        "evidence": sorted(set(evidence), key=evidence.index),
        "technical_risks": technical_risks,
        "lookback_minutes": lookback_minutes,
        "last_event_at": iso(cleaned[-1]["_dt"]) if cleaned else None,
        "events": public_events,
    }


def render_txt(state: dict[str, Any]) -> str:
    lines = []
    lines.append(
        f"{state['symbol']} | TEMPORAL COMPRESSION V7 | {state['level']} | {state['state']}"
    )
    lines.append(
        f"bias={state['bias']} score={state['score']} breaks={state['breaks']} locks={state['locks']} "
        f"tfs={','.join(state['timeframes']) if state['timeframes'] else 'NONE'}"
    )
    if state.get("acceptance_zone") is not None:
        lines.append(f"acceptance_zone={state['acceptance_zone']}")
    lines.append(
        f"leader_tf={state.get('leader_tf')} relay_tf={state.get('relay_tf')} confirmation_tf={state.get('confirmation_tf')}"
    )
    if state["evidence"]:
        lines.append("evidence=" + " | ".join(state["evidence"]))
    if state["technical_risks"]:
        lines.append("technical_risks=" + " | ".join(state["technical_risks"]))
    if state.get("last_event_at"):
        lines.append(f"last_event_at={state['last_event_at']}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--lookback-minutes", type=int, default=240)
    parser.add_argument("--base-output", default="output/dashboard_surface")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbol = args.symbol.upper()
    out_dir = Path(args.base_output) / symbol
    out_dir.mkdir(parents=True, exist_ok=True)

    input_path = out_dir / "legacy_timecomp_events.jsonl"
    state = summarize(symbol, load_jsonl(input_path), args.lookback_minutes)

    json_path = out_dir / "time_compression_state.json"
    txt_path = out_dir / "time_compression_state.txt"

    json_path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    txt_path.write_text(render_txt(state), encoding="utf-8")

    if args.pretty:
        print(render_txt(state).rstrip())
        print(f"\njson={json_path}")
        print(f"txt={txt_path}")


if __name__ == "__main__":
    main()
