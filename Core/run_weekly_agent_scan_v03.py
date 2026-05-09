"""
PowerFlow V6 — Weekly Agent Scan V0.3

Fix vs V0.2:
    - Historical gaps / sparse legacy DB can create sticky clusters.
    - V0.2 grouped too much into giant daily blocks.
    - V0.3 splits clusters by:
        1) calendar day
        2) maximum cluster duration
        3) start gap between best windows
        4) optional minimum rows per scanned window

Example:
    python run_weekly_agent_scan_v03.py --db powerflow.db --symbol GBPUSD --start 2026-04-27T00:00:00 --end 2026-05-04T00:00:00 --timeframes 1,5,15 --window-minutes 90 --step-minutes 30 --cluster-gap-minutes 45 --max-cluster-minutes 180 --top 20 --out weekly_scan_gbpusd_v03.txt
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple
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
    start_dt: datetime
    end_dt: datetime
    scene_name: str
    window_state: str
    next_watch: str
    confidence: float
    one_liner: str
    node_line: str
    score: float
    rows_total: int

    @property
    def time_span(self) -> str:
        return f"{self.start_dt.strftime('%Y-%m-%d %H:%M')}->{self.end_dt.strftime('%H:%M')}"


@dataclass(frozen=True)
class ScanCluster:
    start_dt: datetime
    end_dt: datetime
    best_hit: ScanHit
    hits_count: int
    scenes: Dict[str, int]
    rows_total: int

    @property
    def duration_min(self) -> float:
        return round((self.end_dt - self.start_dt).total_seconds() / 60.0, 1)

    @property
    def time_span(self) -> str:
        if self.start_dt.date() == self.end_dt.date():
            return f"{self.start_dt.strftime('%Y-%m-%d %H:%M')}->{self.end_dt.strftime('%H:%M')}"
        return f"{self.start_dt.strftime('%Y-%m-%d %H:%M')}->{self.end_dt.strftime('%Y-%m-%d %H:%M')}"


def _score_scene(scene_name: str, window_state: str, confidence: float, one_liner: str, rows_total: int) -> float:
    score = confidence * 100.0

    if scene_name == "GRAVITY_RESPRING_NODE":
        score += 35.0
    elif scene_name == "RAW_NODE_BIRTH":
        score += 18.0
    elif scene_name != "DATA_PARTIAL_REVIEW_REQUIRED":
        score += 12.0

    if "AFTER_BREATH" in window_state:
        score += 28.0
    elif "ACTIVE_COUNTER_BREATH" in window_state:
        score += 22.0
    elif "ACTIVE" in window_state:
        score += 18.0
    elif "YOUNG" in window_state:
        score += 8.0

    if "USD" in one_liner and "CAD" in one_liner:
        score += 6.0
    if "JPY" in one_liner:
        score += 3.0

    # Legacy sparse windows get a mild penalty.
    if rows_total < 20:
        score -= 15.0
    elif rows_total < 40:
        score -= 6.0

    return round(score, 2)


def _node_line(events) -> str:
    for ev in events:
        if ev.phase == "NODE_BIRTH":
            return (
                f"{ev.start}->{ev.end} NODE_BIRTH "
                f"up={'+'.join(ev.up_block) or '-'} "
                f"down={'+'.join(ev.down_block) or '-'} "
                f"price={ev.price_response}"
            )
    return "NODE_BIRTH none"


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
    min_rows_window: int,
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
        except Exception:
            cur += timedelta(minutes=step_minutes)
            continue

        rows_total = sum(extraction.rows_loaded.values())

        if rows_total < min_rows_window:
            cur += timedelta(minutes=step_minutes)
            continue

        if scene.scene_name != "DATA_PARTIAL_REVIEW_REQUIRED" and scene.confidence >= min_confidence:
            score = _score_scene(scene.scene_name, scene.window_state, scene.confidence, scene.one_liner, rows_total)
            hits.append(
                ScanHit(
                    start_dt=cur,
                    end_dt=w_end,
                    scene_name=scene.scene_name,
                    window_state=scene.window_state,
                    next_watch=scene.next_watch,
                    confidence=scene.confidence,
                    one_liner=scene.one_liner,
                    node_line=_node_line(extraction.events),
                    score=score,
                    rows_total=rows_total,
                )
            )

        cur += timedelta(minutes=step_minutes)

    return sorted(hits, key=lambda h: (h.score, h.start_dt), reverse=True)


def cluster_hits(
    hits: Sequence[ScanHit],
    cluster_gap_minutes: int,
    max_cluster_minutes: int,
) -> List[ScanCluster]:
    if not hits:
        return []

    chronological = sorted(hits, key=lambda h: h.start_dt)
    groups: List[List[ScanHit]] = []
    current: List[ScanHit] = [chronological[0]]
    current_start = chronological[0].start_dt
    current_end = chronological[0].end_dt
    last_start = chronological[0].start_dt

    for hit in chronological[1:]:
        same_day = hit.start_dt.date() == current_start.date()
        start_gap = (hit.start_dt - last_start).total_seconds() / 60.0
        projected_duration = (max(current_end, hit.end_dt) - current_start).total_seconds() / 60.0

        should_split = (
            not same_day
            or start_gap > cluster_gap_minutes
            or projected_duration > max_cluster_minutes
        )

        if should_split:
            groups.append(current)
            current = [hit]
            current_start = hit.start_dt
            current_end = hit.end_dt
        else:
            current.append(hit)
            current_end = max(current_end, hit.end_dt)

        last_start = hit.start_dt

    groups.append(current)

    clusters: List[ScanCluster] = []
    for group in groups:
        best = sorted(group, key=lambda h: (h.score, h.confidence, h.rows_total), reverse=True)[0]
        scenes: Dict[str, int] = {}
        for hit in group:
            scenes[hit.scene_name] = scenes.get(hit.scene_name, 0) + 1

        clusters.append(
            ScanCluster(
                start_dt=min(h.start_dt for h in group),
                end_dt=max(h.end_dt for h in group),
                best_hit=best,
                hits_count=len(group),
                scenes=scenes,
                rows_total=sum(h.rows_total for h in group),
            )
        )

    return sorted(clusters, key=lambda c: (c.best_hit.score, c.hits_count), reverse=True)


def format_report(
    db: str,
    symbol: str,
    start: datetime,
    end: datetime,
    timeframes: Sequence[int],
    hits: Sequence[ScanHit],
    clusters: Sequence[ScanCluster],
    top: int,
    min_rows_window: int,
) -> str:
    lines: List[str] = []
    lines.append("=== POWERFLOW WEEKLY AGENT SCAN ===")
    lines.append("VERSION: 0.3_GAP_AWARE")
    lines.append(f"DB: {db}")
    lines.append(f"SYMBOL: {symbol}")
    lines.append(f"RANGE: {start.isoformat()} -> {end.isoformat()}")
    lines.append(f"TIMEFRAMES: {','.join(str(tf) for tf in timeframes)}")
    lines.append("")
    lines.append("MODE:")
    lines.append("LEGACY_FORCE_ONLY compatible. Gap-aware clustered scan.")
    lines.append(f"min_rows_window: {min_rows_window}")
    lines.append("")
    lines.append(f"RAW_HITS: {len(hits)}")
    lines.append(f"CLUSTERS: {len(clusters)}")
    lines.append("")
    lines.append("TOP CLUSTERS:")
    if not clusters:
        lines.append("none")
    else:
        for i, cluster in enumerate(clusters[:top], start=1):
            best = cluster.best_hit
            scene_mix = ", ".join(f"{k}:{v}" for k, v in sorted(cluster.scenes.items()))
            lines.append(
                f"{i:02d}. cluster={cluster.time_span} duration={cluster.duration_min:.0f}m "
                f"hits={cluster.hits_count} scenes=[{scene_mix}]"
            )
            lines.append(
                f"    BEST {best.time_span} score={best.score:.1f} rows={best.rows_total} "
                f"scene={best.scene_name} state={best.window_state} conf={best.confidence:.2f} next={best.next_watch}"
            )
            lines.append(f"    {best.node_line}")
            lines.append(f"    {best.one_liner}")
    lines.append("")
    lines.append("NEXT:")
    lines.append("Open the BEST windows with run_scene_report_once.py for full film details.")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 Weekly Agent Scan V0.3")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframes", default="1,5,15")
    parser.add_argument("--source-table", default=None)
    parser.add_argument("--window-minutes", type=int, default=90)
    parser.add_argument("--step-minutes", type=int, default=30)
    parser.add_argument("--cluster-gap-minutes", type=int, default=45)
    parser.add_argument("--max-cluster-minutes", type=int, default=180)
    parser.add_argument("--min-confidence", type=float, default=0.65)
    parser.add_argument("--min-rows-window", type=int, default=20)
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--out", default="weekly_scan_v03.txt")

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
        min_rows_window=args.min_rows_window,
    )
    clusters = cluster_hits(
        hits,
        cluster_gap_minutes=args.cluster_gap_minutes,
        max_cluster_minutes=args.max_cluster_minutes,
    )

    report = format_report(
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

    Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
