"""
PowerFlow V6 — SceneNamer V0.1

Mission:
    Take FlowEventExtractor events and produce a short PowerFlow scene report.

Doctrine:
    - SceneNamer names.
    - SceneNamer does not decide.
    - SceneNamer does not write to DB.
    - SceneNamer does not produce BUY/SELL.
    - It uses the consolidated PowerFlow grammar.

Default runner path:
    powerflow.db -> FlowEventExtractor -> SceneNamer -> text report
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import argparse
import json

from pf_flow_event_extractor import FlowEvent, FlowExtractionReport, extract_flow_events


SCENE_NAMER_VERSION = "0.1.0"


@dataclass(frozen=True)
class NamedScene:
    scene_name: str
    dominant_phase: str
    window_state: str
    next_watch: str
    confidence: float
    one_liner: str
    film_lines: List[str]
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _event_by_phase(events: Sequence[FlowEvent], phase: str) -> Optional[FlowEvent]:
    for event in events:
        if event.phase == phase:
            return event
    return None


def _has_block(event: Optional[FlowEvent], up: Sequence[str], down: Sequence[str], min_hits: int = 2) -> bool:
    if event is None:
        return False
    up_hits = len(set(event.up_block) & set(up))
    down_hits = len(set(event.down_block) & set(down))
    return up_hits >= min_hits and down_hits >= min_hits


def _block_text(items: Sequence[str]) -> str:
    return "+".join(items) if items else "-"


def _scene_name_from_events(events: Sequence[FlowEvent]) -> str:
    node = _event_by_phase(events, "NODE_BIRTH")
    confirmation = _event_by_phase(events, "CONFIRMATION")

    gravity_up = ("USD", "CAD", "JPY")
    risk_down = ("GBP", "EUR", "AUD", "CHF")

    if _has_block(node, gravity_up, risk_down, min_hits=2):
        return "GRAVITY_RESPRING_NODE"

    if node and "USD" in node.up_block and ("GBP" in node.down_block or "EUR" in node.down_block):
        return "USD_RESPRING_AGAINST_RISK_FOLD"

    if confirmation and confirmation.price_response == "PRICE_PAYING":
        return "POST_NODE_GRAVITY_CONFIRMATION_LEG"

    if node:
        return "RAW_NODE_BIRTH"

    return "DATA_PARTIAL_REVIEW_REQUIRED"


def _window_state(events: Sequence[FlowEvent]) -> str:
    phases = [e.phase for e in events]
    if "ABSORPTION" in phases:
        return "WINDOW_ACTIVE_AFTER_BREATH"
    if "COUNTER_BREATH" in phases:
        return "WINDOW_ACTIVE_COUNTER_BREATH"
    if "CONFIRMATION" in phases:
        return "WINDOW_ACTIVE"
    if "NODE_BIRTH" in phases:
        return "WINDOW_YOUNG"
    return "DATA_PARTIAL"


def _next_watch(events: Sequence[FlowEvent]) -> str:
    phases = [e.phase for e in events]
    if "ABSORPTION" in phases:
        return "WATCH_SECOND_LEG"
    if "COUNTER_BREATH" in phases:
        return "WATCH_ABSORPTION"
    if "CONFIRMATION" in phases:
        return "WATCH_COUNTER_BREATH"
    if "NODE_BIRTH" in phases:
        return "WATCH_M5_CONFIRMATION"
    return "REVIEW_DATA"


def _dominant_phase(events: Sequence[FlowEvent]) -> str:
    for phase in ("ABSORPTION", "COUNTER_BREATH", "CONFIRMATION", "NODE_BIRTH", "PRE_FIELD"):
        if _event_by_phase(events, phase):
            return phase
    return "UNKNOWN"


def _event_sentence(event: FlowEvent) -> str:
    base = (
        f"{event.start}→{event.end} {event.phase} — "
        f"{_block_text(event.up_block)} vs {_block_text(event.down_block)}"
    )

    if event.phase == "PRE_FIELD":
        return (
            f"{event.start}→{event.end} PRE_FIELD — champ préparatoire. "
            f"{_block_text(event.up_block)} travaille pendant que {_block_text(event.down_block)} plie."
        )

    if event.phase == "NODE_BIRTH":
        lag = " Prix encore retenu." if event.price_response == "PRICE_LAG" else ""
        return (
            f"{event.start}→{event.end} NODE_BIRTH — "
            f"{_block_text(event.up_block)} respring contre {_block_text(event.down_block)} fold."
            f"{lag}"
        )

    if event.phase == "CONFIRMATION":
        paying = " Le prix commence à payer la structure." if event.price_response == "PRICE_PAYING" else ""
        return (
            f"{event.start}→{event.end} CONFIRMATION — même camp dominant."
            f"{paying}"
        )

    if event.phase == "COUNTER_BREATH":
        return (
            f"{event.start}→{event.end} COUNTER_BREATH — respiration opposée forte. "
            f"Réponse prix: {event.price_response}."
        )

    if event.phase == "ABSORPTION":
        return (
            f"{event.start}→{event.end} ABSORPTION — le camp dominant reprend après respiration."
        )

    return base + f" price={event.price_response}."


def name_scene(report: FlowExtractionReport) -> NamedScene:
    events = list(report.events)
    warnings = list(report.warnings)

    if not events:
        return NamedScene(
            scene_name="DATA_PARTIAL_REVIEW_REQUIRED",
            dominant_phase="UNKNOWN",
            window_state="DATA_PARTIAL",
            next_watch="REVIEW_DATA",
            confidence=0.0,
            one_liner="DATA PARTIAL — aucun événement exploitable extrait.",
            film_lines=[],
            warnings=warnings + ["No events passed to SceneNamer."],
        )

    scene_name = _scene_name_from_events(events)
    window = _window_state(events)
    next_watch = _next_watch(events)
    dom = _dominant_phase(events)

    node = _event_by_phase(events, "NODE_BIRTH")
    confirmation = _event_by_phase(events, "CONFIRMATION")
    counter = _event_by_phase(events, "COUNTER_BREATH")
    absorption = _event_by_phase(events, "ABSORPTION")

    confidence_parts = [e.confidence for e in events if e.phase in {"NODE_BIRTH", "CONFIRMATION", "COUNTER_BREATH", "ABSORPTION"}]
    confidence = sum(confidence_parts) / len(confidence_parts) if confidence_parts else 0.5

    if node and scene_name == "GRAVITY_RESPRING_NODE":
        one_liner = (
            f"{scene_name} — {_block_text(node.up_block)} reprennent contre "
            f"{_block_text(node.down_block)}. {window}. NEXT: {next_watch}."
        )
    elif node:
        one_liner = (
            f"{scene_name} — {_block_text(node.up_block)} vs {_block_text(node.down_block)}. "
            f"{window}. NEXT: {next_watch}."
        )
    else:
        one_liner = f"{scene_name} — {window}. NEXT: {next_watch}."

    film_lines: List[str] = []
    for phase in ("PRE_FIELD", "NODE_BIRTH", "CONFIRMATION", "COUNTER_BREATH", "ABSORPTION"):
        ev = _event_by_phase(events, phase)
        if ev is not None:
            film_lines.append(_event_sentence(ev))

    if counter is not None and absorption is None:
        warnings.append("COUNTER_BREATH present without ABSORPTION; watch continuation.")
    if confirmation is None and node is not None:
        warnings.append("NODE_BIRTH present without confirmation; keep phase as WINDOW_YOUNG.")
    if absorption is not None:
        warnings.append("Absorption detected; next useful watch is SECOND_LEG or new breath.")

    return NamedScene(
        scene_name=scene_name,
        dominant_phase=dom,
        window_state=window,
        next_watch=next_watch,
        confidence=round(confidence, 3),
        one_liner=one_liner,
        film_lines=film_lines,
        warnings=warnings,
    )


def format_scene_report(
    extraction: FlowExtractionReport,
    scene: NamedScene,
    max_lines: int = 10,
) -> str:
    lines: List[str] = []
    lines.append("=== POWERFLOW SCENE REPORT ===")
    lines.append(f"SCENE_NAMER_VERSION: {SCENE_NAMER_VERSION}")
    lines.append(f"SYMBOL: {extraction.symbol}")
    lines.append(f"WINDOW: {extraction.start} -> {extraction.end}")
    lines.append(f"MODE: {extraction.mode}")
    lines.append(f"SOURCE_TABLE: {extraction.source_table}")
    lines.append("")
    lines.append("SCENE:")
    lines.append(scene.scene_name)
    lines.append("")
    lines.append("STATE:")
    lines.append(f"{scene.window_state} | dominant_phase={scene.dominant_phase} | confidence={scene.confidence:.2f}")
    lines.append("")
    lines.append("ONE_LINE:")
    lines.append(scene.one_liner)
    lines.append("")
    lines.append("FILM:")
    if scene.film_lines:
        for line in scene.film_lines[:max_lines]:
            lines.append(line)
    else:
        lines.append("No film lines.")
    lines.append("")
    lines.append("NEXT WATCH:")
    lines.append(scene.next_watch)
    if scene.warnings:
        lines.append("")
        lines.append("NOTES:")
        for warning in scene.warnings[:5]:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 SceneNamer V0.1")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframes", default="1,5,15")
    parser.add_argument("--source-table", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)
    parser.add_argument("--max-lines", type=int, default=10)

    args = parser.parse_args(argv)
    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]

    extraction = extract_flow_events(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        timeframes=tfs,
        source_table=args.source_table,
    )
    scene = name_scene(extraction)

    if args.json:
        output = json.dumps(
            {
                "extraction": extraction.to_dict(),
                "scene": scene.to_dict(),
            },
            ensure_ascii=False,
            indent=2,
        )
    else:
        output = format_scene_report(extraction, scene, max_lines=args.max_lines)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
