"""
PowerFlow V6 — FractalWindowEngine V0.1

Mission:
    Fourth runtime agent after:
        DBVisionGuard -> FlowEventExtractor -> SceneNamer -> FractalWindowEngine

    This agent links the LTF film to HTF context and qualifies:
        - HTF_PRE_NODE_FIELD
        - LTF_BIRTH_ACTIVE
        - H4_CROSS_CONFIRMATION_LATE
        - FRACTAL_CONTRADICTION_FIELD
        - TIME_COMPRESSION_PHASE
        - TIME_STRETCHING_PHASE
        - TEMPORAL_ELASTICITY_FIELD
        - HIGHER_STORY_FIELD

Doctrine:
    - Read-only DB.
    - No BUY/SELL.
    - Does not write DB.
    - Does not depend on cockpit.
    - Names the fractal state; it does not decide.

V0.1 scope:
    Uses FlowEventExtractor on LTF and HTF windows, then compares timing and phases.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import argparse
import json

from pf_flow_event_extractor import FlowEvent, FlowExtractionReport, extract_flow_events
from pf_scene_namer import NamedScene, name_scene


FRACTAL_WINDOW_ENGINE_VERSION = "0.1.1"


@dataclass(frozen=True)
class FractalWindowState:
    symbol: str
    start: str
    end: str
    ltf_timeframes: List[int]
    htf_timeframes: List[int]
    ltf_scene: str
    ltf_window_state: str
    fractal_state: str
    temporal_state: str
    htf_relation: str
    contradiction_state: str
    higher_story_state: str
    node_timing: Dict[str, Optional[str]]
    metrics: Dict[str, Any]
    flags: List[str]
    summary: str
    next_watch: str
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        try:
            dt = datetime.fromisoformat(text.replace(" ", "T"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _event_by_phase(events: Sequence[FlowEvent], phase: str) -> Optional[FlowEvent]:
    for ev in events:
        if ev.phase == phase:
            return ev
    return None


def _first_event(events: Sequence[FlowEvent], phases: Sequence[str]) -> Optional[FlowEvent]:
    filtered = [ev for ev in events if ev.phase in set(phases)]
    if not filtered:
        return None
    return sorted(filtered, key=lambda ev: _parse_dt(ev.start_dt_iso) or datetime.max.replace(tzinfo=timezone.utc))[0]


def _duration_minutes(event: Optional[FlowEvent]) -> Optional[float]:
    if event is None:
        return None
    a = _parse_dt(event.start_dt_iso)
    b = _parse_dt(event.end_dt_iso)
    if a is None or b is None:
        return None
    return round(max(0.0, (b - a).total_seconds() / 60.0), 2)


def _energy_per_minute(event: Optional[FlowEvent]) -> Optional[float]:
    duration = _duration_minutes(event)
    if event is None or not duration or duration <= 0:
        return None
    return round(event.force_energy / duration, 4)


def _delay_minutes(a: Optional[FlowEvent], b: Optional[FlowEvent]) -> Optional[float]:
    if a is None or b is None:
        return None
    da = _parse_dt(a.start_dt_iso)
    db = _parse_dt(b.start_dt_iso)
    if da is None or db is None:
        return None
    return round((db - da).total_seconds() / 60.0, 2)


def _tf_label(tfs: Sequence[int]) -> str:
    return ",".join(str(tf) for tf in tfs)


def _classify_temporal_state(
    ltf_events: Sequence[FlowEvent],
) -> Tuple[str, List[str], Dict[str, Any]]:
    flags: List[str] = []
    metrics: Dict[str, Any] = {}

    node = _event_by_phase(ltf_events, "NODE_BIRTH")
    confirmation = _event_by_phase(ltf_events, "CONFIRMATION")
    counter = _event_by_phase(ltf_events, "COUNTER_BREATH")
    absorption = _event_by_phase(ltf_events, "ABSORPTION")

    node_duration = _duration_minutes(node)
    node_epm = _energy_per_minute(node)
    counter_duration = _duration_minutes(counter)
    absorption_duration = _duration_minutes(absorption)

    metrics["node_duration_min"] = node_duration
    metrics["node_energy_per_min"] = node_epm
    metrics["counter_breath_duration_min"] = counter_duration
    metrics["absorption_duration_min"] = absorption_duration

    if node is None:
        return "NO_LTF_NODE", flags, metrics

    compressed = False
    stretched = False

    if node_duration is not None and node_duration <= 8.0 and node_epm is not None and node_epm >= 15.0:
        compressed = True
        flags.append("TIME_COMPRESSION_PHASE")

    if counter is not None and counter_duration is not None and node_duration is not None:
        if counter_duration >= max(8.0, node_duration * 1.8):
            stretched = True
            flags.append("TIME_STRETCHING_PHASE")

    if absorption is not None and absorption_duration is not None and node_duration is not None:
        if absorption_duration >= node_duration:
            flags.append("ABSORPTION_TIME_EXTENSION")

    if compressed and stretched:
        flags.append("TEMPORAL_ELASTICITY_FIELD")
        return "TEMPORAL_ELASTICITY_FIELD", flags, metrics

    if compressed:
        return "TIME_COMPRESSED", flags, metrics

    if stretched:
        return "TIME_STRETCHED", flags, metrics

    return "TIME_NEUTRAL_ACTIVE", flags, metrics


def _classify_htf_relation(
    ltf_report: FlowExtractionReport,
    htf_report: FlowExtractionReport,
) -> Tuple[str, str, Dict[str, Optional[str]], List[str], Dict[str, Any]]:
    flags: List[str] = []
    metrics: Dict[str, Any] = {}

    ltf_node = _event_by_phase(ltf_report.events, "NODE_BIRTH")
    htf_node = _first_event(htf_report.events, ("NODE_BIRTH", "CONFIRMATION", "ABSORPTION"))

    node_timing: Dict[str, Optional[str]] = {
        "ltf_node_start": ltf_node.start_dt_iso if ltf_node else None,
        "ltf_node_end": ltf_node.end_dt_iso if ltf_node else None,
        "htf_event_start": htf_node.start_dt_iso if htf_node else None,
        "htf_event_phase": htf_node.phase if htf_node else None,
    }

    if ltf_node is None:
        return "NO_LTF_BIRTH", "NO_FRACTAL_READING", node_timing, flags, metrics

    if htf_node is None:
        rows_htf = sum(htf_report.rows_loaded.values())
        metrics["htf_rows_total"] = rows_htf
        if rows_htf > 0:
            flags.append("FRACTAL_CONTRADICTION_FIELD")
            return "HTF_SILENT_OR_FLAT", "FRACTAL_CONTRADICTION_FIELD", node_timing, flags, metrics
        return "HTF_DATA_PARTIAL", "DATA_PARTIAL", node_timing, flags, metrics

    delay = _delay_minutes(ltf_node, htf_node)
    metrics["htf_delay_minutes_from_ltf_node"] = delay

    if delay is None:
        return "HTF_RELATION_UNKNOWN", "FRACTAL_UNKNOWN", node_timing, flags, metrics

    if delay >= 20:
        flags.append("H4_CROSS_CONFIRMATION_LATE")
        flags.append("HIGHER_STORY_FIELD")
        return "HTF_CONFIRMATION_LATE", "LTF_BIRTH_INSIDE_HTF_STORY", node_timing, flags, metrics

    if delay >= 0:
        flags.append("HTF_RELAY_AFTER_LTF_BIRTH")
        return "HTF_RELAY_AFTER_LTF", "LTF_BIRTH_WITH_HTF_RELAY", node_timing, flags, metrics

    if delay < 0:
        flags.append("HTF_PRE_NODE_FIELD")
        flags.append("HIGHER_STORY_FIELD")
        return "HTF_PRE_NODE_FIELD", "LTF_BIRTH_UNDER_HTF_PRE_FIELD", node_timing, flags, metrics

    return "HTF_RELATION_UNKNOWN", "FRACTAL_UNKNOWN", node_timing, flags, metrics


def analyze_fractal_window(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    ltf_timeframes: Iterable[int] = (1, 5, 15),
    htf_timeframes: Iterable[int] = (30, 60, 240),
    source_table: Optional[str] = None,
    htf_padding_minutes: int = 240,
    visual_htf_story: str = "none",
) -> FractalWindowState:
    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)
    if start_dt is None or end_dt is None:
        raise ValueError("Invalid start/end datetime.")
    if end_dt <= start_dt:
        raise ValueError("end must be after start.")

    ltf_tfs = [int(tf) for tf in ltf_timeframes]
    htf_tfs = [int(tf) for tf in htf_timeframes]
    visual_htf_story = (visual_htf_story or "none").strip().lower()

    htf_start = (start_dt - timedelta(minutes=htf_padding_minutes)).isoformat()
    htf_end = (end_dt + timedelta(minutes=htf_padding_minutes)).isoformat()

    warnings: List[str] = []

    ltf_report = extract_flow_events(
        db_path=db_path,
        symbol=symbol,
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        timeframes=ltf_tfs,
        source_table=source_table,
    )
    ltf_scene = name_scene(ltf_report)

    htf_report = extract_flow_events(
        db_path=db_path,
        symbol=symbol,
        start=htf_start,
        end=htf_end,
        timeframes=htf_tfs,
        source_table=source_table,
        # HTF events can span longer windows.
        min_window_minutes=15.0,
        max_window_minutes=240.0,
        min_force_delta=4.0,
        price_lag_pips=2.0,
    )

    temporal_state, temporal_flags, temporal_metrics = _classify_temporal_state(ltf_report.events)
    htf_relation, fractal_state, node_timing, htf_flags, htf_metrics = _classify_htf_relation(ltf_report, htf_report)

    flags = []
    for flag in temporal_flags + htf_flags:
        if flag not in flags:
            flags.append(flag)

    metrics: Dict[str, Any] = {}
    metrics.update(temporal_metrics)
    metrics.update(htf_metrics)
    metrics["ltf_rows_total"] = sum(ltf_report.rows_loaded.values())
    metrics["htf_rows_total"] = sum(htf_report.rows_loaded.values())
    metrics["ltf_events_count"] = len(ltf_report.events)
    metrics["htf_events_count"] = len(htf_report.events)

    if ltf_report.warnings:
        warnings.extend([f"LTF: {w}" for w in ltf_report.warnings])
    if htf_report.warnings:
        warnings.extend([f"HTF: {w}" for w in htf_report.warnings])

    # V0.1.1 — manual visual HTF layer.
    # The DB can be young / sparse while screenshots already show the HTF story.
    # In that case, do not conclude that the higher story is absent.
    if visual_htf_story in {"confirmed", "yes", "true", "1"}:
        for flag in ("VISUAL_HTF_STORY_CONFIRMED", "HIGHER_STORY_FIELD"):
            if flag not in flags:
                flags.append(flag)

        if htf_relation == "HTF_SILENT_OR_FLAT":
            htf_relation = "DB_HTF_SILENT_OR_FLAT"
            fractal_state = "LTF_BIRTH_INSIDE_VISUAL_HTF_STORY"
            contradiction_state = "DB_VISUAL_FRACTAL_GAP"
            for flag in ("DB_VISUAL_FRACTAL_GAP",):
                if flag not in flags:
                    flags.append(flag)
        else:
            contradiction_state = "VISUAL_HTF_CONFIRMS_OR_RELAYS_DB_CONTEXT"
            if fractal_state in {"DATA_PARTIAL", "FRACTAL_UNKNOWN", "NO_FRACTAL_READING"}:
                fractal_state = "VISUAL_HTF_STORY_CONFIRMED"

        higher_story_state = "VISUAL_HIGHER_STORY_CONFIRMED"
    elif visual_htf_story in {"pending", "review"}:
        higher_story_state = "HIGHER_STORY_PENDING_VISUAL_CONFIRMATION"
        contradiction_state = "FRACTAL_CONTRADICTION_FIELD" if "FRACTAL_CONTRADICTION_FIELD" in flags else "VISUAL_REVIEW_PENDING"
    else:
        higher_story_state = "HIGHER_STORY_FIELD" if "HIGHER_STORY_FIELD" in flags else "HIGHER_STORY_NOT_CONFIRMED"
        contradiction_state = "FRACTAL_CONTRADICTION_FIELD" if "FRACTAL_CONTRADICTION_FIELD" in flags else "NO_MAJOR_FRACTAL_CONTRADICTION"

    if "TEMPORAL_ELASTICITY_FIELD" in flags:
        temporal_readable = "temps compressé puis étiré"
    elif temporal_state == "TIME_COMPRESSED":
        temporal_readable = "temps compressé"
    elif temporal_state == "TIME_STRETCHED":
        temporal_readable = "temps étiré"
    else:
        temporal_readable = "temps actif non extrême"

    summary = (
        f"{symbol} | {ltf_scene.scene_name} | {fractal_state} | "
        f"{temporal_readable} | HTF={htf_relation} | NEXT={ltf_scene.next_watch}"
    )

    next_watch = ltf_scene.next_watch
    if fractal_state == "LTF_BIRTH_INSIDE_HTF_STORY":
        next_watch = "WATCH_HTF_RELAY_OR_SECOND_LEG"
    elif fractal_state == "FRACTAL_CONTRADICTION_FIELD":
        next_watch = "WATCH_MICROSTRUCTURE_CONFIRMATION"
    elif temporal_state == "TEMPORAL_ELASTICITY_FIELD":
        next_watch = "WATCH_ABSORPTION_OR_SECOND_LEG"

    return FractalWindowState(
        symbol=symbol,
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        ltf_scene=ltf_scene.scene_name,
        ltf_window_state=ltf_scene.window_state,
        fractal_state=fractal_state,
        temporal_state=temporal_state,
        htf_relation=htf_relation,
        contradiction_state=contradiction_state,
        higher_story_state=higher_story_state,
        node_timing=node_timing,
        metrics=metrics,
        flags=flags,
        summary=summary,
        next_watch=next_watch,
        warnings=warnings,
    )


def format_fractal_report(state: FractalWindowState) -> str:
    lines: List[str] = []
    lines.append("=== POWERFLOW FRACTAL WINDOW ENGINE ===")
    lines.append(f"VERSION: {FRACTAL_WINDOW_ENGINE_VERSION}")
    lines.append(f"SYMBOL: {state.symbol}")
    lines.append(f"WINDOW: {state.start} -> {state.end}")
    lines.append(f"LTF: {_tf_label(state.ltf_timeframes)}")
    lines.append(f"HTF: {_tf_label(state.htf_timeframes)}")
    lines.append("")
    lines.append("LTF_SCENE:")
    lines.append(f"{state.ltf_scene} | {state.ltf_window_state}")
    lines.append("")
    lines.append("FRACTAL_STATE:")
    lines.append(state.fractal_state)
    lines.append("")
    lines.append("TEMPORAL_STATE:")
    lines.append(state.temporal_state)
    lines.append("")
    lines.append("HTF_RELATION:")
    lines.append(state.htf_relation)
    lines.append("")
    lines.append("HIGHER_STORY:")
    lines.append(state.higher_story_state)
    lines.append("")
    lines.append("CONTRADICTION:")
    lines.append(state.contradiction_state)
    lines.append("")
    lines.append("FLAGS:")
    if state.flags:
        for flag in state.flags:
            lines.append(f"- {flag}")
    else:
        lines.append("none")
    lines.append("")
    lines.append("NODE_TIMING:")
    for k, v in state.node_timing.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    lines.append("METRICS:")
    for k, v in state.metrics.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    lines.append("SUMMARY:")
    lines.append(state.summary)
    lines.append("")
    lines.append("NEXT WATCH:")
    lines.append(state.next_watch)
    if state.warnings:
        lines.append("")
        lines.append("WARNINGS:")
        for w in state.warnings:
            lines.append(f"- {w}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 FractalWindowEngine V0.1")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--ltf-timeframes", default="1,5,15")
    parser.add_argument("--htf-timeframes", default="30,60,240")
    parser.add_argument("--source-table", default=None)
    parser.add_argument("--htf-padding-minutes", type=int, default=240)
    parser.add_argument(
        "--visual-htf-story",
        default="none",
        choices=["none", "pending", "review", "confirmed", "yes", "true", "1"],
        help="Manual visual HTF layer from screenshots: none/pending/confirmed",
    )
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    ltf_tfs = [int(x.strip()) for x in args.ltf_timeframes.split(",") if x.strip()]
    htf_tfs = [int(x.strip()) for x in args.htf_timeframes.split(",") if x.strip()]

    state = analyze_fractal_window(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        source_table=args.source_table,
        htf_padding_minutes=args.htf_padding_minutes,
        visual_htf_story=args.visual_htf_story,
    )

    output = state.to_json() if args.json else format_fractal_report(state)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
