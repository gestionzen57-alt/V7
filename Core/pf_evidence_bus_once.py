from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"_missing": True, "_path": str(path)}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_error": str(exc), "_path": str(path)}


def write_json(path: str | Path, data: dict[str, Any], pretty: bool = False) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, indent=2 if pretty else None, ensure_ascii=False),
        encoding="utf-8",
    )


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def first_non_empty(*values: Any, default: str = "UNKNOWN") -> str:
    for v in values:
        if v is None:
            continue
        s = str(v).strip()
        if s and s.lower() not in {"none", "null", "unknown"}:
            return s
    return default


def walk(obj: Any):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from walk(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from walk(v)


def recursive_first(obj: Any, keys: list[str], default: str = "UNKNOWN") -> str:
    for d in walk(obj):
        for k in keys:
            v = d.get(k)
            if v is not None and str(v).strip() not in {"", "None", "null"}:
                return str(v).strip()
    return default


def profile_by_name(time_profiles: dict[str, Any], name: str) -> dict[str, Any]:
    profiles = time_profiles.get("profiles")
    if isinstance(profiles, list):
        for p in profiles:
            if str(p.get("profile", "")).upper() == name.upper():
                return p
    return {}


def last_event(profile: dict[str, Any]) -> dict[str, Any]:
    mem = profile.get("memory") if isinstance(profile, dict) else {}
    if isinstance(mem, dict) and isinstance(mem.get("last_event"), dict):
        return mem["last_event"]
    events = profile.get("recent_important_events") if isinstance(profile, dict) else []
    if isinstance(events, list) and events:
        return events[-1]
    return {}


def add_evidence(
    bucket: list[dict[str, Any]],
    *,
    layer: str,
    state: str = "UNKNOWN",
    attention: str = "INFO",
    bias: str = "UNKNOWN",
    weight: float = 0.0,
    confidence: float | None = None,
    source: str = "",
    message: str = "",
    details: dict[str, Any] | None = None,
    risks: list[str] | None = None,
) -> None:
    bucket.append(
        {
            "layer": layer,
            "state": state,
            "attention": attention,
            "bias": bias,
            "weight": round(float(weight), 4),
            "confidence": confidence,
            "source": source,
            "message": message,
            "details": details or {},
            "technical_risks": risks or [],
        }
    )


def collect_time_profile_evidence(evidence: list[dict[str, Any]], time_profiles: dict[str, Any]) -> None:
    weights = {"LTF": 0.18, "MTF": 0.22, "HTF": 0.18}
    for name in ["LTF", "MTF", "HTF"]:
        p = profile_by_name(time_profiles, name)
        if not p:
            add_evidence(
                evidence,
                layer=name,
                state="MISSING",
                attention="DEGRADED",
                weight=0.0,
                message=f"{name} profile missing",
                risks=[f"{name}_PROFILE_MISSING"],
            )
            continue

        ev = last_event(p)
        add_evidence(
            evidence,
            layer=name,
            state=first_non_empty(p.get("main_state"), p.get("cycle_phase")),
            attention=first_non_empty(p.get("attention"), default="INFO"),
            bias=first_non_empty(p.get("dominant_bias")),
            weight=weights[name],
            source=str(p.get("paths", {}).get("profile", "")),
            message=first_non_empty(p.get("cockpit_phrase"), default=""),
            details={
                "fake_risk": p.get("fake_risk"),
                "compression_quality": p.get("compression_quality"),
                "elastic_state": p.get("elastic_state"),
                "last_event": {
                    "timeframe": ev.get("timeframe"),
                    "event_type": ev.get("event_type"),
                    "price": ev.get("price"),
                    "timestamp_utc": ev.get("timestamp_utc"),
                    "timestamp_broker": ev.get("timestamp_broker"),
                    "timestamp_local_reference": ev.get("timestamp_local_reference"),
                },
            },
            risks=list(p.get("technical_risks") or []),
        )


def collect_cockpit_evidence(evidence: list[dict[str, Any]], cockpit: dict[str, Any]) -> None:
    action = recursive_first(cockpit, ["action", "attention", "status", "global_status"], "UNKNOWN")
    state = recursive_first(cockpit, ["state", "etat", "main_state", "market_state"], "UNKNOWN")
    synthesis = recursive_first(cockpit, ["synthesis", "live_synthesis", "multiread_synthesis", "reading"], "UNKNOWN")
    bias = recursive_first(cockpit, ["bias", "dominant_bias", "machine_direction"], "UNKNOWN")

    add_evidence(
        evidence,
        layer="COCKPIT",
        state=state,
        attention=action,
        bias=bias,
        weight=0.14,
        source="output/dashboard_surface/trader_cockpit.json",
        message=synthesis,
        details={
            "synthesis": synthesis,
            "reading": recursive_first(cockpit, ["reading"], ""),
        },
        risks=list(cockpit.get("technical_risks") or cockpit.get("risks") or []),
    )


def collect_phase_evidence(evidence: list[dict[str, Any]], phase: dict[str, Any]) -> None:
    add_evidence(
        evidence,
        layer="PHASE_SYNTHESIS",
        state=first_non_empty(phase.get("phase_state")),
        attention=first_non_empty(phase.get("attention"), default="INFO"),
        bias=first_non_empty(phase.get("dominant_bias")),
        weight=0.24,
        confidence=as_float(phase.get("confidence"), 0.0),
        source="output/dashboard_surface/phase_synthesis.json",
        message=first_non_empty(phase.get("reading"), default=""),
        details={
            "evidence": phase.get("evidence") or [],
        },
        risks=list(phase.get("technical_risks") or []),
    )


def collect_b8_evidence(evidence: list[dict[str, Any]], b8: dict[str, Any]) -> None:
    status = first_non_empty(b8.get("status"), b8.get("global_status"), default="UNKNOWN")
    coverage = first_non_empty(b8.get("coverage"), b8.get("coverage_status"), default="UNKNOWN")
    attention = first_non_empty(b8.get("attention"), default="WATCH_CONTEXT" if status == "DEGRADED" else "INFO")

    weight = 0.0 if status.upper() == "DEGRADED" else 0.10
    add_evidence(
        evidence,
        layer="B8_CROSS_SYMBOL",
        state=status,
        attention=attention,
        bias=first_non_empty(b8.get("bias"), b8.get("dominant_bias")),
        weight=weight,
        source="output/dashboard_surface/b8_cross_surface.json",
        message=first_non_empty(b8.get("message"), b8.get("summary"), default=""),
        details={
            "coverage": coverage,
        },
        risks=list(b8.get("technical_risks") or b8.get("risks") or []),
    )


def collect_b6_evidence(evidence: list[dict[str, Any]], b6: dict[str, Any]) -> None:
    add_evidence(
        evidence,
        layer="B6_LIVE_FUSION",
        state=recursive_first(b6, ["state", "status", "action_level"], "UNKNOWN"),
        attention=recursive_first(b6, ["level", "attention", "action_level"], "INFO"),
        bias=recursive_first(b6, ["bias", "direction"], "UNKNOWN"),
        weight=0.08,
        source="output/dashboard_surface/b6_live_fusion_dashboard.json",
        message=recursive_first(b6, ["message", "reading"], ""),
        details={
            "tension": recursive_first(b6, ["tension"], ""),
            "absorption": recursive_first(b6, ["absorption"], ""),
            "imbalance": recursive_first(b6, ["imbalance"], ""),
        },
        risks=list(b6.get("technical_risks") or b6.get("risks") or []),
    )


def collect_live_brief_evidence(evidence: list[dict[str, Any]], live: dict[str, Any]) -> None:
    add_evidence(
        evidence,
        layer="LIVE_BRIEF",
        state=recursive_first(live, ["synthesis", "state", "status"], "UNKNOWN"),
        attention=recursive_first(live, ["action", "attention", "status", "global_status"], "INFO"),
        bias=recursive_first(live, ["bias"], "UNKNOWN"),
        weight=0.10,
        source="output/dashboard_surface/live_brief_dashboard.json",
        message=recursive_first(live, ["reading", "message"], ""),
        details={},
        risks=list(live.get("technical_risks") or live.get("risks") or []),
    )


def collect_multiread_evidence(evidence: list[dict[str, Any]], multiread: dict[str, Any]) -> None:
    add_evidence(
        evidence,
        layer="MULTIREAD",
        state=recursive_first(multiread, ["synthesis", "global_status", "status"], "UNKNOWN"),
        attention=recursive_first(multiread, ["attention", "global_status"], "INFO"),
        bias=recursive_first(multiread, ["bias", "dominant_bias", "machine_direction"], "UNKNOWN"),
        weight=0.12,
        source="output/dashboard_surface/powerflow_multiread_synthesis.json",
        message=recursive_first(multiread, ["reading", "message"], ""),
        details={},
        risks=list(multiread.get("technical_risks") or multiread.get("risks") or []),
    )


def collect_data_health_evidence(evidence: list[dict[str, Any]], data_health: dict[str, Any]) -> None:
    status = first_non_empty(data_health.get("global_status"), data_health.get("status"), default="UNKNOWN")
    risks = []
    for d in walk(data_health):
        for k in ["technical_risks", "risks", "issues"]:
            v = d.get(k)
            if isinstance(v, list):
                risks.extend(str(x) for x in v)
    risks = sorted(set(risks))

    add_evidence(
        evidence,
        layer="DATA_HEALTH",
        state=status,
        attention="DEGRADED" if "STALE" in status or "INCOMPLETE" in status or "NOT_READY" in status else "INFO",
        bias="NONE",
        weight=0.0,
        source="output/dashboard_surface/data_health.json",
        message=status,
        details={},
        risks=risks,
    )


def derive_global(evidence: list[dict[str, Any]]) -> dict[str, Any]:
    attention_rank = {
        "NO_ALERT": 0,
        "INFO": 1,
        "WATCH_CONTEXT": 2,
        "WATCH": 3,
        "WATCH_ATTENTION": 4,
        "ALERT_READY": 5,
        "WAKE_TRADER": 6,
        "HOT": 7,
        "ACTIVE": 8,
        "LIVE_ATTENTION_PRESENT": 5,
        "MULTIREAD_WAKE_TRADER": 6,
        "DEGRADED": 2,
    }

    max_attention = "INFO"
    for e in evidence:
        att = str(e.get("attention") or "INFO").upper()
        if attention_rank.get(att, 1) > attention_rank.get(max_attention, 1):
            max_attention = att

    phase_item = next((e for e in evidence if e.get("layer") == "PHASE_SYNTHESIS"), {})
    dominant_phase = first_non_empty(phase_item.get("state"), default="UNKNOWN")
    phase_bias = first_non_empty(phase_item.get("bias"), default="UNKNOWN")
    confidence = as_float(phase_item.get("confidence"), 0.0)

    bias_weights: dict[str, float] = {}
    layer_votes: dict[str, list[str]] = {"PAIR_UP": [], "PAIR_DOWN": []}

    # PHASE_SYNTHESIS is a result layer, not a raw vote when phase is unclear.
    for e in evidence:
        layer = str(e.get("layer") or "").upper()
        b = str(e.get("bias") or "").upper()
        if b not in {"PAIR_UP", "PAIR_DOWN"}:
            continue

        w = as_float(e.get("weight"), 0.0)

        if layer == "PHASE_SYNTHESIS" and dominant_phase in {"NO_CLEAR_PHASE", "MIXED_PHASE", "CONFLICT"}:
            w = 0.0

        bias_weights[b] = bias_weights.get(b, 0.0) + w
        if w > 0:
            layer_votes[b].append(layer)

    up_w = bias_weights.get("PAIR_UP", 0.0)
    down_w = bias_weights.get("PAIR_DOWN", 0.0)

    total_directional = up_w + down_w
    conflict_gap = abs(up_w - down_w)

    if up_w > 0.0 and down_w > 0.0 and conflict_gap <= 0.18:
        dominant_bias = "CONFLICT"
        dominant_phase = "DIRECTIONAL_CONFLICT"
        confidence = min(confidence, 0.45)

    elif up_w >= 0.25 and down_w >= 0.25:
        dominant_bias = "PAIR_UP" if up_w > down_w else "PAIR_DOWN"

        up_layers = set(layer_votes.get("PAIR_UP") or [])
        down_layers = set(layer_votes.get("PAIR_DOWN") or [])

        if {"LTF", "MTF"}.issubset(up_layers) and {"HTF", "COCKPIT"}.intersection(down_layers):
            dominant_phase = "STRUCTURAL_BEARISH_WITH_LTF_MTF_COUNTERFLOW"
            confidence = min(confidence, 0.55)
        elif {"LTF", "MTF"}.issubset(down_layers) and {"HTF", "COCKPIT"}.intersection(up_layers):
            dominant_phase = "STRUCTURAL_BULLISH_WITH_LTF_MTF_COUNTERFLOW"
            confidence = min(confidence, 0.55)
        else:
            dominant_phase = "DIRECTIONAL_CONFLICT"
            confidence = min(confidence, 0.55)

    elif total_directional > 0:
        dominant_bias = "PAIR_UP" if up_w > down_w else "PAIR_DOWN"
    else:
        dominant_bias = phase_bias

    risks = []
    for e in evidence:
        risks.extend(e.get("technical_risks") or [])
    risks = sorted(set(str(r) for r in risks if r))

    if dominant_bias == "CONFLICT":
        risks.append("EVIDENCE_BUS_DIRECTIONAL_CONFLICT")

    return {
        "global_attention": max_attention,
        "dominant_phase": dominant_phase,
        "dominant_bias": dominant_bias,
        "confidence": round(confidence, 4),
        "bias_weights": {k: round(v, 4) for k, v in sorted(bias_weights.items())},
        "bias_votes": layer_votes,
        "technical_risks": sorted(set(risks)),
    }

def write_txt(path: str | Path, data: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        f"EVIDENCE BUS | {data.get('symbol')} | {data.get('global_attention')} | {data.get('dominant_phase')}",
        f"bias={data.get('dominant_bias')}",
        f"confidence={data.get('confidence')}",
        "",
        "EVIDENCE",
    ]

    for e in data.get("evidence", []):
        details = e.get("details") or {}
        extra = ""
        if details.get("fake_risk"):
            extra += f" fake={details.get('fake_risk')}"
        if details.get("coverage"):
            extra += f" coverage={details.get('coverage')}"
        if details.get("last_event"):
            le = details.get("last_event") or {}
            extra += f" last={le.get('timeframe')}/{le.get('event_type')}/price={le.get('price')}"
        lines.append(
            f"- {e.get('layer')}: {e.get('attention')} | {e.get('state')} | "
            f"{e.get('bias')} | w={e.get('weight')}{extra}"
        )
        msg = str(e.get("message") or "").strip()
        if msg:
            lines.append(f"  message={msg}")

    risks = data.get("technical_risks") or []
    if risks:
        lines += ["", "TECHNICAL RISKS"]
        for r in risks:
            lines.append(f"- {r}")

    p.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--time-profiles", default="output/dashboard_surface/time_profiles_dashboard.json")
    parser.add_argument("--cockpit", default="output/dashboard_surface/trader_cockpit.json")
    parser.add_argument("--phase", default="output/dashboard_surface/phase_synthesis.json")
    parser.add_argument("--b8", default="output/dashboard_surface/b8_cross_surface.json")
    parser.add_argument("--b6", default="output/dashboard_surface/b6_live_fusion_dashboard.json")
    parser.add_argument("--live-brief", default="output/dashboard_surface/live_brief_dashboard.json")
    parser.add_argument("--multiread", default="output/dashboard_surface/powerflow_multiread_synthesis.json")
    parser.add_argument("--data-health", default="output/dashboard_surface/data_health.json")
    parser.add_argument("--output", default="output/dashboard_surface/evidence_bus.json")
    parser.add_argument("--txt", default="output/dashboard_surface/evidence_bus.txt")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    time_profiles = load_json(args.time_profiles)
    cockpit = load_json(args.cockpit)
    phase = load_json(args.phase)
    b8 = load_json(args.b8)
    b6 = load_json(args.b6)
    live = load_json(args.live_brief)
    multiread = load_json(args.multiread)
    data_health = load_json(args.data_health)

    evidence: list[dict[str, Any]] = []

    collect_time_profile_evidence(evidence, time_profiles)
    collect_cockpit_evidence(evidence, cockpit)
    collect_phase_evidence(evidence, phase)
    collect_b8_evidence(evidence, b8)
    collect_b6_evidence(evidence, b6)
    collect_live_brief_evidence(evidence, live)
    collect_multiread_evidence(evidence, multiread)
    collect_data_health_evidence(evidence, data_health)

    global_part = derive_global(evidence)

    data = {
        "method": "EVIDENCE_BUS_V739",
        "timestamp_utc": utc_now(),
        "symbol": args.symbol.upper(),
        **global_part,
        "evidence": evidence,
        "inputs": {
            "time_profiles": args.time_profiles,
            "cockpit": args.cockpit,
            "phase": args.phase,
            "b8": args.b8,
            "b6": args.b6,
            "live_brief": args.live_brief,
            "multiread": args.multiread,
            "data_health": args.data_health,
        },
        "note": "Evidence Bus centralizes PowerFlow perception layers. It does not decide trades.",
    }

    write_json(args.output, data, pretty=args.pretty)
    write_txt(args.txt, data)

    print(
        f"EVIDENCE_BUS_OK | symbol={data['symbol']} | "
        f"attention={data['global_attention']} | phase={data['dominant_phase']} | "
        f"bias={data['dominant_bias']} | evidence={len(evidence)} | out={args.output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
