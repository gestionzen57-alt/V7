"""
PowerFlow V6 — Cockpit Agentic State V0.1

Mission:
    Build a stable JSON state for the dashboard from the 4 runtime agents:

        DBVisionGuard
        FlowEventExtractor
        SceneNamer
        FractalWindowEngine

Architecture:
    - cockpit_* reads.
    - no DB write.
    - no Telegram.
    - no BUY/SELL.
    - output JSON only.

Output:
    output/cockpit_agentic_state_v01.json
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
import argparse
import json

from pf_db_vision_guard import analyze_db_vision
from pf_flow_event_extractor import extract_flow_events
from pf_scene_namer import name_scene
from pf_fractal_window_engine import analyze_fractal_window
from pf_flow_event_extractor_v02_extended import extract_flow_events_extended


COCKPIT_AGENTIC_STATE_VERSION = "0.1.1"


def _phase_times(events) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for ev in events:
        out[ev.phase] = {
            "start": ev.start,
            "end": ev.end,
            "timeframe": ev.timeframe,
            "up_block": ev.up_block,
            "down_block": ev.down_block,
            "force_energy": ev.force_energy,
            "price_response": ev.price_response,
            "confidence": ev.confidence,
        }
    return out


def _compact_agent_summary(vision, extraction, scene, fractal) -> Dict[str, Any]:
    return {
        "vision_state": vision.vision_state,
        "live_state": vision.live_state,
        "schema_state": vision.schema_state,
        "source_table": vision.source_table,
        "scene": scene.scene_name,
        "window_state": scene.window_state,
        "dominant_phase": scene.dominant_phase,
        "next_watch": scene.next_watch,
        "fractal_state": fractal.fractal_state,
        "temporal_state": fractal.temporal_state,
        "htf_relation": fractal.htf_relation,
        "higher_story": fractal.higher_story_state,
        "contradiction": fractal.contradiction_state,
        "flags": fractal.flags,
    }


def build_cockpit_agentic_state(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    ltf_timeframes: Iterable[int] = (1, 5, 15),
    htf_timeframes: Iterable[int] = (30, 60, 240),
    visual_htf_story: str = "none",
) -> Dict[str, Any]:
    ltf_tfs = [int(tf) for tf in ltf_timeframes]
    htf_tfs = [int(tf) for tf in htf_timeframes]
    all_tfs = sorted(set(ltf_tfs + htf_tfs))

    generated_at = datetime.now(timezone.utc).isoformat()

    vision = analyze_db_vision(
        db_path=db_path,
        symbol=symbol,
        timeframes=all_tfs,
        recent_minutes=60,
        gap_threshold_minutes=180,
    )

    extraction = extract_flow_events(
        db_path=db_path,
        symbol=symbol,
        start=start,
        end=end,
        timeframes=ltf_tfs,
    )

    scene = name_scene(extraction)

    fractal = analyze_fractal_window(
        db_path=db_path,
        symbol=symbol,
        start=start,
        end=end,
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        visual_htf_story=visual_htf_story,
    )

    try:
        extended = extract_flow_events_extended(
            db_path=db_path,
            symbol=symbol,
            start=start,
            end=end,
            timeframes=ltf_tfs,
            source_table="force_snapshots_v2",
            fallback_to_legacy=False,
        )
        extended_state = extended.to_dict()
    except Exception as exc:
        extended_state = {
            "mode": "EXTENDED_V02_ERROR",
            "extended_schema_state": "ERROR",
            "extended_rows_loaded": {},
            "extended_flags": [],
            "extended_summary": f"EXTENDED ERROR: {type(exc).__name__}: {exc}",
            "extended_event_metrics": [],
            "warnings": [str(exc)],
        }

    agent_summary = _compact_agent_summary(vision, extraction, scene, fractal)
    agent_summary["extended_summary"] = extended_state.get("extended_summary")
    agent_summary["extended_flags"] = extended_state.get("extended_flags", [])
    agent_summary["extended_schema_state"] = extended_state.get("extended_schema_state")

    # Minimal dashboard status logic.
    if vision.vision_state == "DATA_BLIND":
        cockpit_status = "DATA_BLIND"
    elif "LTF_BIRTH" in fractal.fractal_state or scene.scene_name != "DATA_PARTIAL_REVIEW_REQUIRED":
        cockpit_status = "AGENTIC_WINDOW_ACTIVE"
    elif vision.vision_state == "DATA_PARTIAL":
        cockpit_status = "DATA_PARTIAL_AGENTIC_READY"
    else:
        cockpit_status = "AGENTIC_READY"

    if fractal.temporal_state == "TEMPORAL_ELASTICITY_FIELD":
        headline = "FENÊTRE FRACTALE — temps compressé puis étiré"
    elif scene.scene_name != "DATA_PARTIAL_REVIEW_REQUIRED":
        headline = f"SCÈNE ACTIVE — {scene.scene_name}"
    else:
        headline = "AGENTS PRÊTS — aucune scène majeure"

    return {
        "version": COCKPIT_AGENTIC_STATE_VERSION,
        "generated_at_utc": generated_at,
        "symbol": symbol,
        "window": {
            "start": start,
            "end": end,
            "ltf_timeframes": ltf_tfs,
            "htf_timeframes": htf_tfs,
            "visual_htf_story": visual_htf_story,
        },
        "cockpit_status": cockpit_status,
        "headline": headline,
        "agent_summary": agent_summary,
        "db_vision": {
            "schema_state": vision.schema_state,
            "live_state": vision.live_state,
            "vision_state": vision.vision_state,
            "source_table": vision.source_table,
            "can_detect_ltf_birth": vision.can_detect_ltf_birth,
            "can_validate_htf_gravity": vision.can_validate_htf_gravity,
            "timeframes": [asdict(tf) for tf in vision.timeframes],
            "gaps": [asdict(gap) for gap in vision.gaps],
            "notes": vision.notes,
        },
        "flow_events": {
            "mode": extraction.mode,
            "source_table": extraction.source_table,
            "rows_loaded": extraction.rows_loaded,
            "phases": _phase_times(extraction.events),
            "events": [asdict(ev) for ev in extraction.events],
            "warnings": extraction.warnings,
        },
        "scene": scene.to_dict(),
        "fractal": fractal.to_dict(),
        "extended": extended_state,
        "dashboard_cards": [
            {
                "title": "VISION DB",
                "status": vision.vision_state,
                "line": f"{vision.live_state} | {vision.schema_state} | source={vision.source_table}",
            },
            {
                "title": "SCÈNE",
                "status": scene.scene_name,
                "line": scene.one_liner,
            },
            {
                "title": "FRACTALITÉ",
                "status": fractal.fractal_state,
                "line": fractal.summary,
            },
            {
                "title": "EXTENDED V0.2",
                "status": extended_state.get("extended_summary", "EXTENDED_UNKNOWN"),
                "line": " | ".join(extended_state.get("extended_flags", [])[:6]) if extended_state.get("extended_flags") else "no extended flags",
            },
            {
                "title": "NEXT WATCH",
                "status": fractal.next_watch,
                "line": f"scene={scene.next_watch} | fractal={fractal.next_watch}",
            },
        ],
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 Cockpit Agentic State V0.1")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--ltf-timeframes", default="1,5,15")
    parser.add_argument("--htf-timeframes", default="30,60,240")
    parser.add_argument("--visual-htf-story", default="none", choices=["none", "pending", "review", "confirmed", "yes", "true", "1"])
    parser.add_argument("--out", default="output/cockpit_agentic_state_v01.json")
    parser.add_argument("--pretty", action="store_true")

    args = parser.parse_args(argv)

    ltf_tfs = [int(x.strip()) for x in args.ltf_timeframes.split(",") if x.strip()]
    htf_tfs = [int(x.strip()) for x in args.htf_timeframes.split(",") if x.strip()]

    state = build_cockpit_agentic_state(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        visual_htf_story=args.visual_htf_story,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    indent = 2 if args.pretty else None
    out_path.write_text(json.dumps(state, ensure_ascii=False, indent=indent), encoding="utf-8")

    print(f"COCKPIT_AGENTIC_STATE_WRITTEN: {out_path}")
    print(f"STATUS: {state['cockpit_status']}")
    print(f"HEADLINE: {state['headline']}")
    print(f"SCENE: {state['agent_summary']['scene']}")
    print(f"FRACTAL: {state['agent_summary']['fractal_state']}")
    print(f"EXTENDED: {state['agent_summary'].get('extended_summary')}")
    print(f"NEXT: {state['agent_summary']['next_watch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
