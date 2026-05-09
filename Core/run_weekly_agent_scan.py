"""
PowerFlow V6 — Weekly Agent Scan V0.1

Mission:
    Scan a historical range with the validated Agentic Core V0.1:
        DB -> FlowEventExtractor -> SceneNamer -> text report

Use case:
    Last week / legacy force-only data without candle info.

Requirements:
    Files in the same Core folder:
        pf_flow_event_extractor.py
        pf_scene_namer.py

Example:
    python run_weekly_agent_scan.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --out weekly_scan.txt

Notes:
    - Read-only DB.
    - No BUY/SELL.
    - If using WAL mode locally, keep powerflow.db + powerflow.db-wal + powerflow.db-shm together.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional, Sequence
import argparse

from pf_flow_event_extractor import extract_flow_events
from pf_scene_namer import name_scene


def _parse_dt(value: str) -> datetime:
    text = value.strip().replace("Z", "+00:00")
    dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class ScanHit:
    start: str
    end: str
    scene_name: str
    window_state: str
    next_watch: str
    confidence: float
    line: str


def _score_scene(scene_name: str, window_state: str, confidence: float) -> float:
    score = confidence * 100.0

    if scene_name == "GRAVITY_RESPRING_NODE":
        score += 35.0
    elif scene_name == "RAW_NODE_BIRTH":
        score += 20.0
    elif scene_name != "DATA_PARTIAL_REVIEW_REQUIRED":
        score += 15.0

    if "ACTIVE" in window_state:
        score += 25.0
    if "AFTER_BREATH" in window_state:
        score += 15.0
    if "YOUNG" in window_state:
        score += 10.0

    return score


def scan_range(
    db: str,
    symbol: str,
    start: datetime,
    end: datetime,
    timeframes: Sequence[int],
    window_minutes: int,
    step_minutes: int,
    source_table: Optional[str],
    min_confidence: float,
) -> List[ScanHit]:
    hits: List[ScanHit] = []
    cur = start

    while cur + timedelta(minutes=window_minutes) <= end:
        w_end = cur + timedelta(minutes=window_minutes)

        try:
            extraction = extract_flow_events(
                db_path=db,
                symbol=symbol,
                start=cur.isoformat(),
                end=w_end.isoformat(),
                timeframes=timeframes,
                source_table=source_table,
            )
            scene = name_scene(extraction)
        except Exception as exc:
            hits.append(
                ScanHit(
                    start=cur.isoformat(),
                    end=w_end.isoformat(),
                    scene_name="SCAN_ERROR",
                    window_state="ERROR",
                    next_watch="REVIEW_SCRIPT",
                    confidence=0.0,
                    line=f"{cur.strftime('%Y-%m-%d %H:%M')}->{w_end.strftime('%H:%M')} ERROR {type(exc).__name__}: {exc}",
                )
            )
            cur += timedelta(minutes=step_minutes)
            continue

        if scene.scene_name != "DATA_PARTIAL_REVIEW_REQUIRED" and scene.confidence >= min_confidence:
            score = _score_scene(scene.scene_name, scene.window_state, scene.confidence)
            line = (
                f"{cur.strftime('%Y-%m-%d %H:%M')}->{w_end.strftime('%H:%M')} "
                f"score={score:.1f} scene={scene.scene_name} state={scene.window_state} "
                f"conf={scene.confidence:.2f} next={scene.next_watch} | {scene.one_liner}"
            )
            hits.append(
                ScanHit(
                    start=cur.isoformat(),
                    end=w_end.isoformat(),
                    scene_name=scene.scene_name,
                    window_state=scene.window_state,
                    next_watch=scene.next_watch,
                    confidence=scene.confidence,
                    line=line,
                )
            )

        cur += timedelta(minutes=step_minutes)

    return sorted(
        hits,
        key=lambda h: (_score_scene(h.scene_name, h.window_state, h.confidence), h.start),
        reverse=True,
    )


def format_weekly_report(
    db: str,
    symbol: str,
    start: datetime,
    end: datetime,
    timeframes: Sequence[int],
    hits: Sequence[ScanHit],
    top: int,
) -> str:
    lines: List[str] = []
    lines.append("=== POWERFLOW WEEKLY AGENT SCAN ===")
    lines.append("VERSION: 0.1")
    lines.append(f"DB: {db}")
    lines.append(f"SYMBOL: {symbol}")
    lines.append(f"RANGE: {start.isoformat()} -> {end.isoformat()}")
    lines.append(f"TIMEFRAMES: {','.join(str(tf) for tf in timeframes)}")
    lines.append("")
    lines.append("MODE:")
    lines.append("LEGACY_FORCE_ONLY compatible. No candle/volume/spread required.")
    lines.append("")
    lines.append(f"HITS: {len(hits)}")
    lines.append("")
    lines.append("TOP HITS:")
    if not hits:
        lines.append("none")
    else:
        for hit in hits[:top]:
            lines.append(hit.line)

    lines.append("")
    lines.append("NEXT:")
    lines.append("Open the best windows with run_scene_report_once.py for full film details.")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 Weekly Agent Scan V0.1")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframes", default="1,5,15")
    parser.add_argument("--source-table", default=None)
    parser.add_argument("--window-minutes", type=int, default=90)
    parser.add_argument("--step-minutes", type=int, default=30)
    parser.add_argument("--min-confidence", type=float, default=0.65)
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--out", default="weekly_scan.txt")

    args = parser.parse_args(argv)

    start = _parse_dt(args.start)
    end = _parse_dt(args.end)
    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]

    hits = scan_range(
        db=args.db,
        symbol=args.symbol,
        start=start,
        end=end,
        timeframes=tfs,
        window_minutes=args.window_minutes,
        step_minutes=args.step_minutes,
        source_table=args.source_table,
        min_confidence=args.min_confidence,
    )

    report = format_weekly_report(
        db=args.db,
        symbol=args.symbol,
        start=start,
        end=end,
        timeframes=tfs,
        hits=hits,
        top=args.top,
    )

    Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
