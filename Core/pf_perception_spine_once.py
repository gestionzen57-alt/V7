#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.6 Turbo — Perception Spine Once

Mission:
- Read V7-ready perception surfaces.
- Fuse TEMPORAL + LEGACY_BEHAVIORAL into a short trader-readable film.
- Do not decide trades.
- Do not emit BUY/SELL.
- Produce a spine surface consumed later by Trader Attention Packet / dashboard / telegram.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_SYMBOLS = "GBPUSD"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if default is None:
        default = {}
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"_read_error": str(exc), "_path": str(path)}
    return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def norm_symbol(symbol: str) -> str:
    return (symbol or "").strip().upper()


def split_symbols(raw: str | Iterable[str]) -> list[str]:
    if isinstance(raw, str):
        parts = raw.split(",")
    else:
        parts = list(raw)
    symbols = [norm_symbol(x) for x in parts if norm_symbol(x)]
    return symbols or ["GBPUSD"]


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def extract_counts(state: dict[str, Any], names: list[str]) -> dict[str, int]:
    """Extract Counter-like fields from V7 surfaces.

    Accepts several schema variants:
    - {"events_by_type": {"TIME_COMP_LOCK": 25}}
    - {"roles_by_type": {"TEMPORAL_LOCK": 25}}
    - {"event_types": "TIME_COMP_LOCK:25,COMPRESSION:10"}
    - {"roles": ["TEMPORAL_LOCK", "ELASTIC_LOADING_LEGACY"]}
    """
    out: dict[str, int] = {}
    for key in names:
        raw = state.get(key)
        if isinstance(raw, dict):
            for k, v in raw.items():
                kk = str(k).strip().upper()
                if not kk or kk == "NONE":
                    continue
                try:
                    out[kk] = out.get(kk, 0) + int(float(v))
                except Exception:
                    out[kk] = out.get(kk, 0) + 1
        elif isinstance(raw, str):
            for part in raw.split(","):
                part = part.strip()
                if not part or part.upper() == "NONE":
                    continue
                if ":" in part:
                    k, v = part.split(":", 1)
                    kk = k.strip().upper()
                    try:
                        out[kk] = out.get(kk, 0) + int(float(v.strip()))
                    except Exception:
                        out[kk] = out.get(kk, 0) + 1
                else:
                    out[part.upper()] = out.get(part.upper(), 0) + 1
        elif isinstance(raw, list):
            for item in raw:
                kk = str(item).strip().upper()
                if kk and kk != "NONE":
                    out[kk] = out.get(kk, 0) + 1
    return out


def infer_bias(legacy: dict[str, Any], temporal: dict[str, Any]) -> str:
    votes: dict[str, float] = {}
    for c in [legacy.get("bias"), legacy.get("dominant_bias"), temporal.get("bias"), temporal.get("direction")]:
        if c in ("PAIR_UP", "PAIR_DOWN"):
            votes[c] = votes.get(c, 0.0) + 1.0

    role_counts = extract_counts(legacy, ["role_counts", "roles", "roles_by_type"])
    for role, count in role_counts.items():
        role_u = role.upper()
        if "RELEASE_DOWN" in role_u or "PAIR_DOWN" in role_u:
            votes["PAIR_DOWN"] = votes.get("PAIR_DOWN", 0.0) + count * 0.25
        elif "RELEASE_UP" in role_u or "PAIR_UP" in role_u:
            votes["PAIR_UP"] = votes.get("PAIR_UP", 0.0) + count * 0.25

    if not votes:
        return "UNKNOWN"
    if abs(votes.get("PAIR_UP", 0.0) - votes.get("PAIR_DOWN", 0.0)) < 0.5:
        return "MIXED"
    return max(votes.items(), key=lambda item: item[1])[0]


def layer_set(legacy: dict[str, Any], temporal: dict[str, Any]) -> list[str]:
    layers: set[str] = set()
    for source in (legacy, temporal):
        raw = source.get("layers")
        if isinstance(raw, dict):
            for part, count in raw.items():
                try:
                    if int(float(count)) <= 0:
                        continue
                except Exception:
                    pass
                val = str(part).strip().upper()
                if val and val != "NONE":
                    layers.add(val)
        elif isinstance(raw, str):
            for part in raw.split(","):
                val = part.strip().upper()
                if val and val != "NONE":
                    layers.add(val)
        elif isinstance(raw, list):
            for part in raw:
                val = str(part).strip().upper()
                if val and val != "NONE":
                    layers.add(val)
        layer = source.get("layer")
        if layer:
            val = str(layer).strip().upper()
            if val and val != "NONE":
                layers.add(val)
    return sorted(layers)


def _tf_label(value: Any) -> str | None:
    s = str(value).strip().upper()
    if not s or s == "NONE" or s == "0":
        return None
    if s in ("1", "5", "15", "30"):
        return f"M{s}"
    if s == "60":
        return "H1"
    if s == "240":
        return "H4"
    return s


def tf_set(legacy: dict[str, Any], temporal: dict[str, Any]) -> list[str]:
    tfs: set[str] = set()
    for source in (legacy, temporal):
        for key in ("tfs", "tf_labels", "timeframes"):
            raw = source.get(key)
            if isinstance(raw, str):
                for part in raw.split(","):
                    lab = _tf_label(part)
                    if lab:
                        tfs.add(lab)
            elif isinstance(raw, list):
                for part in raw:
                    lab = _tf_label(part)
                    if lab:
                        tfs.add(lab)
        for key in ("tf_label", "timeframe"):
            lab = _tf_label(source.get(key)) if source.get(key) is not None else None
            if lab:
                tfs.add(lab)
    order = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240}
    return sorted(tfs, key=lambda x: order.get(x, 9999))


def infer_film(legacy: dict[str, Any], temporal: dict[str, Any]) -> tuple[str, str, list[str]]:
    state_l = str(legacy.get("state") or legacy.get("status") or "").upper()
    state_t = str(temporal.get("state") or temporal.get("status") or "").upper()

    roles = extract_counts(legacy, ["role_counts", "roles", "roles_by_type"])
    event_counts = extract_counts(legacy, ["event_counts", "event_types", "events_by_type"])

    time_breaks = event_counts.get("TIME_COMP_BREAK", 0)
    time_locks = event_counts.get("TIME_COMP_LOCK", 0)
    elastic_release = roles.get("ELASTIC_RELEASE_LEGACY", 0) + event_counts.get("COMPRESSION_BREAK", 0)
    elastic_loading = roles.get("ELASTIC_LOADING_LEGACY", 0) + event_counts.get("COMPRESSION", 0)
    zone_repulsion = roles.get("ZONE_REPULSION", 0) + event_counts.get("KISS_REJECT", 0)
    slingshot = roles.get("TACTICAL_REARM_RELEASE", 0) + event_counts.get("SLINGSHOT", 0)
    trap = roles.get("TRAP_OR_REINTEGRATION", 0) + event_counts.get("FAKEOUT", 0)
    force_switch = roles.get("FORCE_SWITCH", 0) + event_counts.get("SUPER_SWITCH", 0)

    evidence: list[str] = []
    if time_breaks:
        evidence.append("TEMPORAL_BREAK")
    if time_locks:
        evidence.append("TEMPORAL_LOCK")
    if elastic_release:
        evidence.append("ELASTIC_RELEASE")
    if elastic_loading:
        evidence.append("ELASTIC_LOADING")
    if zone_repulsion:
        evidence.append("ZONE_REPULSION")
    if slingshot:
        evidence.append("SLINGSHOT")
    if trap:
        evidence.append("TRAP")
    if force_switch:
        evidence.append("FORCE_SWITCH")

    if time_breaks and elastic_release:
        return "ELASTIC_RELEASE_WITH_TEMPORAL_BREAK", "ACTIVE", evidence
    if time_breaks and (zone_repulsion or slingshot or force_switch):
        return "TEMPORAL_BREAK_WITH_TACTICAL_CONFIRMATION", "ACTIVE", evidence
    if elastic_release and (zone_repulsion or slingshot):
        return "TACTICAL_ELASTIC_RELEASE", "ACTIVE", evidence
    if time_breaks:
        return "TEMPORAL_RELEASE", "WATCH", evidence
    if elastic_release:
        return "ELASTIC_RELEASE_LEGACY", "WATCH", evidence
    if zone_repulsion:
        return "ZONE_REJECTION_ACTIVE", "WATCH", evidence
    if slingshot:
        return "TACTICAL_REARM_RELEASE", "WATCH", evidence
    if time_locks >= 3 and elastic_loading >= 2:
        return "MULTI_TF_ELASTIC_LOADING", "INFO", evidence
    if time_locks >= 3:
        return "MULTI_TF_TEMPORAL_LOCK", "INFO", evidence
    if elastic_loading >= 2:
        return "ELASTIC_LOADING", "INFO", evidence

    if "IDLE" in state_l and "IDLE" in state_t:
        return "NO_ACTIVE_FILM", "IDLE", evidence
    return "LOW_SIGNAL_FILM", "IDLE", evidence


def collect_risks(*states: dict[str, Any]) -> list[str]:
    risks: set[str] = set()
    for state in states:
        raw = state.get("technical_risks")
        if isinstance(raw, str):
            for part in raw.split(","):
                val = part.strip().upper()
                if val and val not in ("NONE", "NO_RISK"):
                    risks.add(val)
        elif isinstance(raw, list):
            for r in raw:
                val = str(r).strip().upper()
                if val and val not in ("NONE", "NO_RISK"):
                    risks.add(val)
    return sorted(risks)


def infer_main_conflict(legacy: dict[str, Any], temporal: dict[str, Any], bias: str) -> str:
    event_counts = extract_counts(legacy, ["event_counts", "event_types", "events_by_type"])
    role_counts = extract_counts(legacy, ["role_counts", "roles", "roles_by_type"])
    tfs = tf_set(legacy, temporal)

    has_loading = role_counts.get("ELASTIC_LOADING_LEGACY", 0) or event_counts.get("COMPRESSION", 0)
    has_lock = role_counts.get("TEMPORAL_LOCK", 0) or event_counts.get("TIME_COMP_LOCK", 0)
    has_break = role_counts.get("TEMPORAL_BREAK", 0) or event_counts.get("TIME_COMP_BREAK", 0)
    has_zone_pressure = (
        role_counts.get("ZONE_PRESSURE_HIGH", 0)
        + role_counts.get("ZONE_PRESSURE_LOW", 0)
        + event_counts.get("EXTREME_HIGH", 0)
        + event_counts.get("EXTREME_LOW", 0)
    )

    if has_lock and has_loading and not has_break:
        if len(tfs) >= 4:
            return "MULTI_TF_COMPRESSION_WITHOUT_RELEASE"
        return "COMPRESSION_WITHOUT_RELEASE"
    if has_break and has_loading:
        return "RELEASE_VS_LOADING_MEMORY"
    if has_zone_pressure and has_loading:
        return "ZONE_PRESSURE_VS_ELASTIC_LOADING"
    if bias == "MIXED":
        return "BIAS_CONFLICT"
    return "NONE"


def infer_watch(film: str) -> list[str]:
    if "LOADING" in film or "LOCK" in film:
        return ["TIME_COMP_BREAK", "COMPRESSION_BREAK", "KISS_REJECT", "SLINGSHOT"]
    if "RELEASE" in film or "BREAK" in film:
        return ["LOCK_ACCEPTANCE_AFTER_RELEASE", "SECOND_LEG", "COUNTER_BREATH", "ZONE_REJECTION"]
    return ["NEW_TEMPORAL_LOCK", "FIRST_DETACHMENT", "ZONE_REPULSION"]


def compute_score(legacy: dict[str, Any], temporal: dict[str, Any], film: str, intensity: str) -> float:
    score = fnum(legacy.get("score"), 0.0) + fnum(legacy.get("score_hint"), 0.0)
    score += fnum(temporal.get("score"), 0.0)
    if intensity == "ACTIVE":
        score += 10
    elif intensity == "WATCH":
        score += 5
    elif intensity == "INFO":
        score += 1.5
    if "TEMPORAL" in film:
        score += 1.5
    if "ELASTIC" in film:
        score += 1.5
    return round(score, 2)


def infer_attention(film: str, intensity: str, score: float, risks: list[str]) -> str:
    if intensity == "ACTIVE":
        return "WAKE_TRADER"
    if intensity == "WATCH":
        return "WATCH_CLOSE"
    if score >= 20 and intensity == "INFO":
        return "OBSERVE"
    if risks and film != "NO_ACTIVE_FILM":
        return "OBSERVE_WITH_TECHNICAL_RISK"
    return "OBSERVE" if film != "NO_ACTIVE_FILM" else "QUIET"


def build_symbol_spine(symbol: str, root: Path) -> dict[str, Any]:
    sym = norm_symbol(symbol)
    surface = root / "output" / "dashboard_surface"
    sym_dir = surface / sym

    temporal = read_json(sym_dir / "time_compression_state.json", {})
    legacy = read_json(sym_dir / "legacy_behavioral_state.json", {})
    evidence_bus = read_json(surface / "evidence_bus.json", {})
    evidence_reading = read_json(surface / "evidence_reading.json", {})
    data_health = read_json(surface / "data_health.json", {})

    film, intensity, evidence = infer_film(legacy, temporal)
    bias = infer_bias(legacy, temporal)
    risks = collect_risks(legacy, temporal, evidence_bus, evidence_reading, data_health)
    score = compute_score(legacy, temporal, film, intensity)
    attention = infer_attention(film, intensity, score, risks)
    main_conflict = infer_main_conflict(legacy, temporal, bias)
    watch = infer_watch(film)

    weak_layers: list[str] = []
    if "EVENT_TIME_AHEAD_OF_DETECTED_AT" in risks:
        weak_layers.append("TIME_SYNC")
    if not temporal:
        weak_layers.append("TEMPORAL_MISSING")
    if not legacy:
        weak_layers.append("LEGACY_BEHAVIORAL_MISSING")
    if not evidence_bus:
        weak_layers.append("EVIDENCE_BUS_MISSING")

    neutralized_layers: list[str] = []
    if film in ("NO_ACTIVE_FILM", "LOW_SIGNAL_FILM"):
        neutralized_layers.append("LEGACY_FAST_DETECTORS")

    return {
        "generated_at": utc_now(),
        "symbol": sym,
        "module": "pf_perception_spine_once",
        "version": "V7.6_TURBO_B",
        "status": intensity,
        "attention": attention,
        "main_film": film,
        "bias": bias,
        "score": score,
        "layers": layer_set(legacy, temporal),
        "timeframes": tf_set(legacy, temporal),
        "evidence": evidence,
        "main_conflict": main_conflict,
        "watch": watch,
        "next_wake": watch[0] if watch else None,
        "weak_layers": sorted(set(weak_layers)),
        "neutralized_layers": sorted(set(neutralized_layers)),
        "technical_risks": risks,
        "inputs": {
            "temporal_state": str(temporal.get("state") or temporal.get("status") or "UNKNOWN"),
            "legacy_behavioral_state": str(legacy.get("state") or legacy.get("status") or "UNKNOWN"),
            "legacy_attention": legacy.get("attention"),
            "legacy_events": legacy.get("events") or legacy.get("event_total") or legacy.get("count") or legacy.get("event_count"),
            "temporal_events": temporal.get("events") or temporal.get("event_total") or temporal.get("count"),
        },
        "raw_refs": {
            "time_compression_state": str(sym_dir / "time_compression_state.json"),
            "legacy_behavioral_state": str(sym_dir / "legacy_behavioral_state.json"),
        },
    }


def render_text(packet: dict[str, Any]) -> str:
    def csv(key: str) -> str:
        value = packet.get(key)
        if isinstance(value, list):
            return ",".join(str(x) for x in value) if value else "NONE"
        return str(value or "NONE")

    lines = [
        f"{packet['symbol']} | PERCEPTION SPINE V7.6 TURBO | {packet['status']} | {packet['main_film']}",
        f"attention={packet['attention']} bias={packet['bias']} score={packet['score']}",
        f"layers={csv('layers')} tfs={csv('timeframes')}",
        f"evidence={csv('evidence')}",
        f"main_conflict={packet.get('main_conflict') or 'NONE'}",
        f"watch={csv('watch')}",
        f"next_wake={packet.get('next_wake') or 'NONE'}",
        f"weak_layers={csv('weak_layers')}",
        f"neutralized_layers={csv('neutralized_layers')}",
        f"technical_risks={csv('technical_risks')}",
    ]
    return "\n".join(lines) + "\n"


def write_outputs(root: Path, packets: list[dict[str, Any]], output: str | None, txt: str | None) -> tuple[Path, Path, str]:
    surface = root / "output" / "dashboard_surface"

    for packet in packets:
        sym_dir = surface / packet["symbol"]
        write_json(sym_dir / "perception_spine.json", packet)
        write_text(sym_dir / "perception_spine.txt", render_text(packet))

    if len(packets) == 1:
        aggregate: Any = packets[0]
        agg_text = render_text(packets[0])
    else:
        rank = {"WAKE_TRADER": 4, "WATCH_CLOSE": 3, "OBSERVE_WITH_TECHNICAL_RISK": 2, "OBSERVE": 1, "QUIET": 0}
        aggregate = {
            "generated_at": utc_now(),
            "module": "pf_perception_spine_once",
            "version": "V7.6_TURBO_B",
            "symbols": [p["symbol"] for p in packets],
            "items": packets,
            "top_attention": max(packets, key=lambda p: rank.get(str(p.get("attention")), 0)).get("attention") if packets else "QUIET",
        }
        agg_text = "\n".join(render_text(p).strip() for p in packets) + "\n"

    out_json = Path(output) if output else surface / "perception_spine.json"
    out_txt = Path(txt) if txt else surface / "perception_spine.txt"
    if not out_json.is_absolute():
        out_json = root / out_json
    if not out_txt.is_absolute():
        out_txt = root / out_txt

    write_json(out_json, aggregate)
    write_text(out_txt, agg_text)
    return out_json, out_txt, agg_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.6 Turbo Perception Spine")
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--symbols", default=None)
    parser.add_argument("--root", default=".")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", default=None)
    parser.add_argument("--txt", default=None)
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    raw_symbols = args.symbols or args.symbol or DEFAULT_SYMBOLS
    symbols = split_symbols(raw_symbols)
    packets = [build_symbol_spine(sym, root) for sym in symbols]
    out_json, out_txt, agg_text = write_outputs(root, packets, args.output, args.txt)

    if args.pretty:
        print(agg_text, end="")
        print(f"json={out_json}")
        print(f"txt={out_txt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
