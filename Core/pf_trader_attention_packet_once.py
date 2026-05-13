#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.6 — Trader Attention Packet (Turbo B)

Purpose:
- Read the Perception Spine + local surface states.
- Compress the market film into a short trader-facing packet.
- No trade decision. No BUY/SELL. No risk nanny.

Doctrine:
- Machine perceives, qualifies, wakes attention.
- Trader filters, arbitrates, acts.
- Early alert is qualified, not censored.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


VERSION = "V7.6_TURBO_B"


FILM_TRANSLATIONS = {
    "MULTI_TF_ELASTIC_LOADING": "Élastique multi-TF chargé — attendre détachement ou répulsion.",
    "ELASTIC_RELEASE_LEGACY": "Élastique legacy relâché — attendre acceptation, second leg ou rejet de zone.",
    "ELASTIC_RELEASE_WITH_TEMPORAL_BREAK": "Relâchement élastique confirmé par cassure temporelle — surveiller acceptation.",
    "TEMPORAL_RELEASE_ACTIVE": "Cassure temporelle active — attention au rattrapage prix.",
    "ZONE_REPULSION_ACTIVE": "Répulsion de zone détectée — surveiller contre-souffle ou réintégration.",
    "TACTICAL_REARM_RELEASE": "Slingshot / réarmement tactique actif — impulsion en naissance.",
    "LOW_SIGNAL_FILM": "Film faible ou incomplet.",
    "IDLE": "Pas de film exploitable.",
}


WAKE_ROLES = {
    "TIME_COMP_BREAK",
    "COMPRESSION_BREAK",
    "SLINGSHOT",
    "KISS_REJECT",
    "FAKEOUT",
    "SUPER_SWITCH",
    "TEMPORAL_RELEASE",
    "ELASTIC_RELEASE_LEGACY",
    "ZONE_REPULSION",
    "TACTICAL_REARM_RELEASE",
}


CRITICAL_FILMS = {
    "ELASTIC_RELEASE_WITH_TEMPORAL_BREAK",
    "TEMPORAL_RELEASE_ACTIVE",
    "TACTICAL_REARM_RELEASE",
    "ZONE_REPULSION_ACTIVE",
}


RISK_PRIORITY = [
    "EVENT_TIME_AHEAD_OF_DETECTED_AT",
    "EVIDENCE_BUS_LTF_MTF_COUNTERFLOW_ACTIVE",
    "GBPUSD_TEMPORAL_GAPS",
    "GBPUSD_HTF_INCOMPLETE",
    "TIME_SYNC",
    "B8_INSUFFICIENT_CROSS_PAIR_COVERAGE",
]


@dataclass
class AttentionPacket:
    symbol: str
    generated_at: str
    version: str
    attention: str
    packet_state: str
    main_film: str
    bias: str
    score: float
    next_wake: str
    line_1: str
    line_2: str
    line_3: str
    line_4: str
    line_5: str
    line_6: str
    film_reading: str
    watch: list[str]
    evidence: list[str]
    layers: list[str]
    timeframes: list[str]
    conflicts: list[str]
    weak_layers: list[str]
    technical_risks: list[str]
    displayed_risks: list[str]
    neutralized_layers: list[str]
    source_files: dict[str, str]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    try:
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}
    return {}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if str(x)]
    if isinstance(value, tuple):
        return [str(x) for x in value if str(x)]
    if isinstance(value, dict):
        return [str(k) for k, v in value.items() if v]
    text = str(value).strip()
    if not text or text.upper() == "NONE":
        return []
    raw = text.replace("|", ",").split(",")
    return [part.strip() for part in raw if part.strip() and part.strip().upper() != "NONE"]


def compact_join(values: Iterable[str], default: str = "NONE", sep: str = ",") -> str:
    cleaned = []
    for v in values:
        s = str(v).strip()
        if s and s.upper() != "NONE" and s not in cleaned:
            cleaned.append(s)
    return sep.join(cleaned) if cleaned else default


def unique(values: Iterable[str]) -> list[str]:
    out = []
    for value in values:
        text = str(value).strip()
        if text and text.upper() != "NONE" and text not in out:
            out.append(text)
    return out


def first_existing(paths: list[Path]) -> Path | None:
    for path in paths:
        if path.exists():
            return path
    return None


def prioritize_risks(risks: list[str], symbol: str, limit: int = 3) -> list[str]:
    if not risks:
        return []
    sym = symbol.upper()
    cleaned = unique(risks)
    scored: list[tuple[int, str]] = []
    for risk in cleaned:
        score = 100
        if risk in RISK_PRIORITY:
            score = RISK_PRIORITY.index(risk)
        elif risk.startswith(sym):
            score = 10
        elif "TIME" in risk or "TEMPORAL" in risk:
            score = 20
        elif risk.startswith("EURUSD") or risk.startswith("USDJPY"):
            score = 90
        scored.append((score, risk))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [risk for _, risk in scored[:limit]]


def normalize_conflicts(conflicts: list[str], main_film: str, evidence: list[str]) -> list[str]:
    blob = " ".join([main_film] + evidence + conflicts).upper()
    out = []
    for conflict in conflicts:
        if conflict == "MULTI_TF_COMPRESSION_WITHOUT_RELEASE" and "ELASTIC_RELEASE" in blob:
            out.append("FIRST_RELEASE_NOT_YET_ACCEPTED")
        else:
            out.append(conflict)
    if "ELASTIC_RELEASE" in blob and not any(c in out for c in ("FIRST_RELEASE_NOT_YET_ACCEPTED", "PARTIAL_RELEASE_INSIDE_MULTI_TF_COMPRESSION")):
        out.append("FIRST_RELEASE_NOT_YET_ACCEPTED")
    return unique(out)


def infer_packet_state(main_film: str, attention: str, next_wake: str, evidence: list[str], score: float, conflicts: list[str]) -> str:
    upper_blob = " ".join([main_film, attention, next_wake, " ".join(evidence), " ".join(conflicts)]).upper()
    if main_film in CRITICAL_FILMS:
        return "WAKE"
    if any(role in upper_blob for role in WAKE_ROLES):
        return "WAKE"
    if main_film == "MULTI_TF_ELASTIC_LOADING":
        return "WATCH"
    if score >= 70 and ("TEMPORAL_LOCK" in upper_blob or "ELASTIC_LOADING" in upper_blob):
        return "WATCH"
    if score >= 35:
        return "OBSERVE"
    return "IDLE"


def normalize_attention(packet_state: str, displayed_risks: list[str]) -> str:
    suffix = "_WITH_TECH_RISK" if displayed_risks else ""
    if packet_state == "WAKE":
        return "WAKE_TRADER" + suffix
    if packet_state == "WATCH":
        return "WATCH" + suffix
    if packet_state == "OBSERVE":
        return "OBSERVE" + suffix
    return "IDLE" + suffix


def wake_phrase(next_wake: str) -> str:
    phrases = {
        "TIME_COMP_BREAK": "Réveil suivant : cassure temporelle.",
        "LOCK_ACCEPTANCE_AFTER_RELEASE": "Réveil suivant : acceptation post-release.",
        "COMPRESSION_BREAK": "Réveil suivant : sortie de compression.",
        "KISS_REJECT": "Réveil suivant : kiss & reject / répulsion.",
        "SLINGSHOT": "Réveil suivant : slingshot / réarmement tactique.",
        "SECOND_LEG": "Réveil suivant : second leg.",
        "COUNTER_BREATH": "Réveil suivant : counter breath.",
        "ZONE_REJECTION": "Réveil suivant : rejet de zone.",
    }
    return phrases.get(next_wake, f"Réveil suivant : {next_wake}.")


def build_packet(symbol: str, surface_root: Path) -> AttentionPacket:
    sym = symbol.upper()
    sym_dir = surface_root / sym

    spine_path = first_existing([
        sym_dir / "perception_spine.json",
        surface_root / "perception_spine.json",
    ])
    legacy_path = sym_dir / "legacy_behavioral_state.json"
    temporal_path = sym_dir / "time_compression_state.json"

    spine = read_json(spine_path) if spine_path else {}
    legacy = read_json(legacy_path)
    temporal = read_json(temporal_path)

    main_film = str(
        spine.get("main_film")
        or spine.get("film")
        or spine.get("state")
        or spine.get("status")
        or "IDLE"
    )
    bias = str(spine.get("bias") or legacy.get("bias") or temporal.get("bias") or "UNKNOWN")
    try:
        score = float(spine.get("score", 0.0) or 0.0)
    except Exception:
        score = 0.0

    evidence = as_list(spine.get("evidence")) or as_list(legacy.get("evidence"))
    if not evidence:
        role_blob = json.dumps(legacy.get("roles_by_type", legacy.get("roles", {})), ensure_ascii=False)
        if "TEMPORAL_LOCK" in role_blob:
            evidence.append("TEMPORAL_LOCK")
        if "ELASTIC_RELEASE" in role_blob:
            evidence.append("ELASTIC_RELEASE")
        if "ELASTIC_LOADING" in role_blob or "ELASTIC_LOADING_LEGACY" in role_blob:
            evidence.append("ELASTIC_LOADING")
        if "ZONE_PRESSURE" in role_blob:
            evidence.append("ZONE_PRESSURE")

    layers = as_list(spine.get("layers")) or as_list(legacy.get("layers"))
    timeframes = as_list(spine.get("timeframes") or spine.get("tfs")) or as_list(legacy.get("timeframes") or legacy.get("tf_labels"))
    watch = as_list(spine.get("watch")) or ["TIME_COMP_BREAK", "COMPRESSION_BREAK", "KISS_REJECT", "SLINGSHOT"]
    conflicts = normalize_conflicts(as_list(spine.get("main_conflict") or spine.get("conflicts")), main_film, evidence)
    weak_layers = as_list(spine.get("weak_layers"))
    technical_risks = as_list(spine.get("technical_risks"))
    displayed_risks = prioritize_risks(technical_risks, sym, limit=3)
    neutralized_layers = as_list(spine.get("neutralized_layers"))
    next_wake = str(spine.get("next_wake") or (watch[0] if watch else "NONE"))

    packet_state = infer_packet_state(main_film, str(spine.get("attention", "")), next_wake, evidence, score, conflicts)
    attention = normalize_attention(packet_state, displayed_risks)
    film_reading = FILM_TRANSLATIONS.get(main_film, main_film.replace("_", " ").title())

    line_1 = f"{sym} | {attention} | {main_film}"
    line_2 = f"bias={bias} score={round(score, 2)} next_wake={next_wake}"
    line_3 = film_reading
    line_4 = wake_phrase(next_wake)
    line_5 = f"watch={compact_join(watch, sep=' | ')}"
    line_6 = f"conflict={compact_join(conflicts, default='NONE', sep=' | ')}"

    return AttentionPacket(
        symbol=sym,
        generated_at=utc_now(),
        version=VERSION,
        attention=attention,
        packet_state=packet_state,
        main_film=main_film,
        bias=bias,
        score=round(score, 2),
        next_wake=next_wake,
        line_1=line_1,
        line_2=line_2,
        line_3=line_3,
        line_4=line_4,
        line_5=line_5,
        line_6=line_6,
        film_reading=film_reading,
        watch=watch,
        evidence=evidence,
        layers=layers,
        timeframes=timeframes,
        conflicts=conflicts,
        weak_layers=weak_layers,
        technical_risks=technical_risks,
        displayed_risks=displayed_risks,
        neutralized_layers=neutralized_layers,
        source_files={
            "perception_spine": str(spine_path) if spine_path else "MISSING",
            "legacy_behavioral_state": str(legacy_path),
            "time_compression_state": str(temporal_path),
        },
    )


def packet_to_text(packet: AttentionPacket, compact: bool = False) -> str:
    lines = [
        packet.line_1,
        packet.line_2,
        packet.line_3,
        packet.line_4,
        packet.line_5,
        packet.line_6,
    ]
    if not compact:
        lines.append(
            f"layers={compact_join(packet.layers)} "
            f"tfs={compact_join(packet.timeframes)} "
            f"evidence={compact_join(packet.evidence)}"
        )
        if packet.weak_layers:
            lines.append(f"weak_layers={compact_join(packet.weak_layers)}")
        if packet.neutralized_layers:
            lines.append(f"neutralized_layers={compact_join(packet.neutralized_layers)}")
        if packet.displayed_risks:
            lines.append(f"technical_risks={compact_join(packet.displayed_risks)}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Trader Attention Packet")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--surface-root", default=str(Path("output") / "dashboard_surface"))
    parser.add_argument("--output", default=None)
    parser.add_argument("--txt", default=None)
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--compact", action="store_true", help="Print/write only the short packet lines")
    args = parser.parse_args(argv)

    surface_root = Path(args.surface_root)
    packet = build_packet(args.symbol, surface_root)
    sym_dir = surface_root / packet.symbol

    out_json = Path(args.output) if args.output else sym_dir / "trader_attention_packet.json"
    out_txt = Path(args.txt) if args.txt else sym_dir / "trader_attention_packet.txt"
    global_json = surface_root / "trader_attention_packet.json"
    global_txt = surface_root / "trader_attention_packet.txt"

    payload = asdict(packet)
    text = packet_to_text(packet, compact=args.compact)

    write_json(out_json, payload)
    write_text(out_txt, text)
    write_json(global_json, payload)
    write_text(global_txt, text)

    if args.pretty:
        print(text)
        print(f"json={out_json.resolve()}")
        print(f"txt={out_txt.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
