"""
PowerFlow V6 — 4 Agents Service Runner V0.1

Runs the current operational 4-agent chain in read-only mode:
1. DBVisionGuard
2. FlowEventExtractor
3. SceneNamer
4. WeeklyAgentScan / LabCandidateScanner

Place this file in Core next to:
- pf_db_vision_guard.py
- pf_flow_event_extractor.py
- pf_scene_namer.py
- run_weekly_agent_scan_v03.py

Example:
python run_powerflow_4_agents_service_once.py --db powerflow.db --symbol GBPUSD --lab-start 2026-05-04T09:00:00 --lab-end 2026-05-04T10:15:00 --week-start 2026-04-27T00:00:00 --week-end 2026-05-04T00:00:00
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional, Sequence

from pf_db_vision_guard import analyze_db_vision, format_report as format_vision_report
from pf_flow_event_extractor import extract_flow_events, format_report as format_flow_report
from pf_scene_namer import name_scene, format_scene_report


def _try_weekly_scan(args) -> str:
    try:
        from run_weekly_agent_scan_v03 import scan_range, cluster_hits, format_report
        from run_weekly_agent_scan_v03 import _parse_dt

        start = _parse_dt(args.week_start)
        end = _parse_dt(args.week_end)
        tfs = [int(x.strip()) for x in args.timeframes.split(',') if x.strip()]
        hits = scan_range(
            db=args.db,
            symbol=args.symbol,
            start=start,
            end=end,
            timeframes=tfs,
            window_minutes=args.window_minutes,
            step_minutes=args.step_minutes,
            source_table=None,
            min_confidence=args.min_confidence,
            min_rows_window=args.min_rows_window,
        )
        clusters = cluster_hits(
            hits,
            cluster_gap_minutes=args.cluster_gap_minutes,
            max_cluster_minutes=args.max_cluster_minutes,
        )
        return format_report(
            db=args.db,
            symbol=args.symbol,
            start=start,
            end=end,
            timeframes=tfs,
            hits=hits,
            clusters=clusters,
            top=args.top,
            min_rows_window=args.min_rows_window,
        )
    except Exception as exc:
        return f"=== WEEKLY AGENT SCAN ===\nSTATUS: ERROR\n{type(exc).__name__}: {exc}\n"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 4 Agents Service Runner V0.1")
    parser.add_argument('--db', required=True)
    parser.add_argument('--symbol', default='GBPUSD')
    parser.add_argument('--lab-start', required=True)
    parser.add_argument('--lab-end', required=True)
    parser.add_argument('--timeframes', default='1,5,15')
    parser.add_argument('--week-start', default='2026-04-27T00:00:00')
    parser.add_argument('--week-end', default='2026-05-04T00:00:00')
    parser.add_argument('--window-minutes', type=int, default=90)
    parser.add_argument('--step-minutes', type=int, default=30)
    parser.add_argument('--cluster-gap-minutes', type=int, default=45)
    parser.add_argument('--max-cluster-minutes', type=int, default=180)
    parser.add_argument('--min-confidence', type=float, default=0.65)
    parser.add_argument('--min-rows-window', type=int, default=20)
    parser.add_argument('--top', type=int, default=12)
    parser.add_argument('--out', default='powerflow_4_agents_service_report.txt')

    args = parser.parse_args(argv)
    tfs = [int(x.strip()) for x in args.timeframes.split(',') if x.strip()]

    blocks = []

    vision = analyze_db_vision(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=[1, 5, 15, 30, 60, 240],
        recent_minutes=60,
        gap_threshold_minutes=180,
    )
    blocks.append(format_vision_report(vision))

    extraction = extract_flow_events(
        db_path=args.db,
        symbol=args.symbol,
        start=args.lab_start,
        end=args.lab_end,
        timeframes=tfs,
    )
    blocks.append(format_flow_report(extraction))

    scene = name_scene(extraction)
    blocks.append(format_scene_report(extraction, scene))

    weekly = _try_weekly_scan(args)
    blocks.append(weekly)

    output = "\n\n" + ("\n" + "=" * 90 + "\n").join(blocks)
    Path(args.out).write_text(output, encoding='utf-8')
    print(output)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
