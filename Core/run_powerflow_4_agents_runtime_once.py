"""
PowerFlow V6 — 4 Runtime Agents Service V0.2.1

Agents:
    1. DBVisionGuard
    2. FlowEventExtractor
    3. SceneNamer
    4. FractalWindowEngine

WeeklyAgentScan remains a Lab tool, not the fourth runtime agent.

Usage:
    python run_powerflow_4_agents_runtime_once.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T09:00:00 --end 2026-05-04T10:15:00 --out powerflow_4_runtime_agents_report.txt
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Sequence
import argparse

from pf_db_vision_guard import analyze_db_vision, format_report as format_db_vision
from pf_flow_event_extractor import extract_flow_events, format_report as format_flow_events
from pf_scene_namer import name_scene, format_scene_report
from pf_fractal_window_engine import analyze_fractal_window, format_fractal_report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow 4 Runtime Agents Service V0.2")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--ltf-timeframes", default="1,5,15")
    parser.add_argument("--htf-timeframes", default="30,60,240")
    parser.add_argument("--visual-htf-story", default="none", choices=["none", "pending", "review", "confirmed", "yes", "true", "1"])
    parser.add_argument("--out", default="powerflow_4_runtime_agents_report.txt")

    args = parser.parse_args(argv)
    ltf_tfs = [int(x.strip()) for x in args.ltf_timeframes.split(",") if x.strip()]
    htf_tfs = [int(x.strip()) for x in args.htf_timeframes.split(",") if x.strip()]

    parts = []

    vision = analyze_db_vision(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=ltf_tfs + htf_tfs,
        recent_minutes=60,
        gap_threshold_minutes=180,
    )
    parts.append(format_db_vision(vision))

    extraction = extract_flow_events(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        timeframes=ltf_tfs,
    )
    parts.append(format_flow_events(extraction))

    scene = name_scene(extraction)
    parts.append(format_scene_report(extraction, scene))

    fractal = analyze_fractal_window(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        ltf_timeframes=ltf_tfs,
        htf_timeframes=htf_tfs,
        visual_htf_story=args.visual_htf_story,
    )
    parts.append(format_fractal_report(fractal))

    output = "\n" + ("\n" + "=" * 90 + "\n").join(parts)
    Path(args.out).write_text(output, encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
