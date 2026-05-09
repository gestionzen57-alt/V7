#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - Force Kinematics V0.1

Read-only module.

Purpose:
    Extract what PowerFlow can measure from force_snapshots for a sequence:
    - coverage by timeframe
    - force velocity / slope per minute
    - force angle in degrees
    - force acceleration between segments
    - bid delta and pips per minute
    - fastest rising/falling currencies
    - insufficient-data warnings

Current supported schema:
    created_at, symbol, timeframe, bid,
    force_gbp, force_usd, force_eur, force_jpy,
    force_cad, force_chf, force_aud

No dependencies.
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]

FORCE_COLS = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
}


@dataclass
class ForceRow:
    created_at: str
    dt: datetime
    symbol: str
    timeframe: int
    bid: Optional[float]
    forces: Dict[str, float]


@dataclass
class KinematicSegment:
    timeframe: int
    start_time: str
    end_time: str
    minutes: float
    bid_start: Optional[float]
    bid_end: Optional[float]
    bid_delta: Optional[float]
    pip_delta: Optional[float]
    pip_velocity_per_min: Optional[float]
    force_delta: Dict[str, float]
    force_velocity_per_min: Dict[str, float]
    force_angle_deg: Dict[str, float]
    fastest_up: List[Tuple[str, float]]
    fastest_down: List[Tuple[str, float]]
    energy: float
    tags: List[str]

    def to_dict(self) -> Dict:
        return asdict(self)


def parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def load_rows(db_path: str, symbol: str, timeframe: int, start: str, end: str) -> List[ForceRow]:
    cols = ["created_at", "symbol", "timeframe", "bid"] + list(FORCE_COLS.values())
    sql_cols = ", ".join(cols)

    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        f"""
        SELECT {sql_cols}
        FROM force_snapshots
        WHERE symbol = ?
          AND timeframe = ?
          AND created_at >= ?
          AND created_at <= ?
        ORDER BY created_at ASC
        """,
        (symbol, timeframe, start, end),
    )

    out: List[ForceRow] = []
    for r in cur.fetchall():
        forces: Dict[str, float] = {}
        for c, col in FORCE_COLS.items():
            v = safe_float(r[col])
            if v is not None:
                forces[c] = v
        out.append(
            ForceRow(
                created_at=str(r["created_at"]),
                dt=parse_dt(str(r["created_at"])),
                symbol=str(r["symbol"]),
                timeframe=int(r["timeframe"]),
                bid=safe_float(r["bid"]),
                forces=forces,
            )
        )

    con.close()
    return out


def angle_from_velocity(v_per_min: float) -> float:
    """
    Angle representation:
        x = 1 minute
        y = force units per minute
    This is a geometric proxy, not a chart-pixel angle.
    """
    return round(math.degrees(math.atan(v_per_min)), 2)


def classify_segment(
    force_velocity: Dict[str, float],
    pip_velocity: Optional[float],
    energy: float,
    minutes: float,
) -> List[str]:
    tags: List[str] = []

    strong_up = [c for c, v in force_velocity.items() if v >= 1.50]
    medium_up = [c for c, v in force_velocity.items() if 0.75 <= v < 1.50]
    strong_down = [c for c, v in force_velocity.items() if v <= -1.50]
    medium_down = [c for c, v in force_velocity.items() if -1.50 < v <= -0.75]

    if strong_up:
        tags.append("FAST_UP_" + "+".join(strong_up))
    elif medium_up:
        tags.append("UP_" + "+".join(medium_up))

    if strong_down:
        tags.append("FAST_DOWN_" + "+".join(strong_down))
    elif medium_down:
        tags.append("DOWN_" + "+".join(medium_down))

    if energy >= 40:
        tags.append("HIGH_FORCE_ENERGY")
    elif energy >= 20:
        tags.append("MEDIUM_FORCE_ENERGY")

    if pip_velocity is not None:
        if pip_velocity <= -0.80:
            tags.append("PRICE_FAST_DOWN")
        elif pip_velocity >= 0.80:
            tags.append("PRICE_FAST_UP")
        elif abs(pip_velocity) <= 0.15 and energy >= 20:
            tags.append("PRICE_LAG_OR_ABSORPTION")

    if "USD" in strong_up or ("USD" in medium_up and pip_velocity is not None and pip_velocity < 0):
        tags.append("USD_PRESSURE_UP")
    if "GBP" in strong_down or ("GBP" in medium_down and pip_velocity is not None and pip_velocity < 0):
        tags.append("GBP_PRESSURE_DOWN")

    return tags


def build_segments(rows: Sequence[ForceRow]) -> List[KinematicSegment]:
    segments: List[KinematicSegment] = []

    if len(rows) < 2:
        return segments

    for a, b in zip(rows, rows[1:]):
        seconds = (b.dt - a.dt).total_seconds()
        if seconds <= 0:
            continue

        minutes = seconds / 60.0
        force_delta: Dict[str, float] = {}
        velocity: Dict[str, float] = {}
        angle: Dict[str, float] = {}

        for c in CURRENCIES:
            if c not in a.forces or c not in b.forces:
                continue
            d = b.forces[c] - a.forces[c]
            v = d / minutes
            force_delta[c] = round(d, 4)
            velocity[c] = round(v, 4)
            angle[c] = angle_from_velocity(v)

        bid_delta = None
        pip_delta = None
        pip_velocity = None
        if a.bid is not None and b.bid is not None:
            bid_delta = round(b.bid - a.bid, 6)
            pip_delta = round(bid_delta / 0.0001, 2)
            pip_velocity = round(pip_delta / minutes, 4)

        energy = round(sum(abs(v) for v in force_delta.values()), 4)
        ordered = sorted(velocity.items(), key=lambda kv: kv[1], reverse=True)
        fastest_up = [(c, round(v, 4)) for c, v in ordered[:3]]
        fastest_down = [(c, round(v, 4)) for c, v in sorted(velocity.items(), key=lambda kv: kv[1])[:3]]

        tags = classify_segment(velocity, pip_velocity, energy, minutes)

        segments.append(
            KinematicSegment(
                timeframe=a.timeframe,
                start_time=a.created_at,
                end_time=b.created_at,
                minutes=round(minutes, 2),
                bid_start=a.bid,
                bid_end=b.bid,
                bid_delta=bid_delta,
                pip_delta=pip_delta,
                pip_velocity_per_min=pip_velocity,
                force_delta=force_delta,
                force_velocity_per_min=velocity,
                force_angle_deg=angle,
                fastest_up=fastest_up,
                fastest_down=fastest_down,
                energy=energy,
                tags=tags,
            )
        )

    return segments


def acceleration_table(segments: Sequence[KinematicSegment]) -> List[Dict]:
    """
    Acceleration = change of force velocity between adjacent segments.
    Needs at least 2 segments.
    """
    out: List[Dict] = []
    if len(segments) < 2:
        return out

    for prev, cur in zip(segments, segments[1:]):
        acc: Dict[str, float] = {}
        for c in CURRENCIES:
            if c in prev.force_velocity_per_min and c in cur.force_velocity_per_min:
                acc[c] = round(cur.force_velocity_per_min[c] - prev.force_velocity_per_min[c], 4)

        ordered_up = sorted(acc.items(), key=lambda kv: kv[1], reverse=True)[:3]
        ordered_down = sorted(acc.items(), key=lambda kv: kv[1])[:3]
        out.append(
            {
                "timeframe": cur.timeframe,
                "at": cur.end_time,
                "from_segment": f"{prev.start_time}->{prev.end_time}",
                "to_segment": f"{cur.start_time}->{cur.end_time}",
                "acceleration": acc,
                "accel_up": ordered_up,
                "accel_down": ordered_down,
            }
        )

    return out


def fmt(value, digits=2) -> str:
    if value is None:
        return "NA"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def make_markdown_report(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    timeframes: Sequence[int],
) -> str:
    lines: List[str] = []
    lines.append("# PowerFlow Force Kinematics Report")
    lines.append("")
    lines.append(f"- DB: `{db_path}`")
    lines.append(f"- Symbol: `{symbol}`")
    lines.append(f"- Window: `{start}` → `{end}`")
    lines.append(f"- Timeframes: `{','.join(str(tf) for tf in timeframes)}`")
    lines.append("")
    lines.append("> Angles are force-units/min geometric proxies: `atan(force_velocity_per_min)`.")
    lines.append("")

    for tf in timeframes:
        rows = load_rows(db_path, symbol, tf, start, end)
        segments = build_segments(rows)
        acc = acceleration_table(segments)

        lines.append(f"## TF={tf}")
        lines.append("")
        if not rows:
            lines.append("```text")
            lines.append("No rows in this window.")
            lines.append("```")
            lines.append("")
            continue

        lines.append(f"- Rows: `{len(rows)}`")
        lines.append(f"- Coverage: `{rows[0].created_at}` → `{rows[-1].created_at}`")
        if len(rows) < 2:
            lines.append("- Status: `INSUFFICIENT_ROWS_FOR_KINEMATICS`")
            lines.append("")
            continue

        lines.append(f"- Segments: `{len(segments)}`")
        lines.append("")

        lines.append("### Segments")
        lines.append("")
        lines.append("| Window | Minutes | Bid | Pips | Fastest up | Fastest down | Energy | Tags |")
        lines.append("|---|---:|---:|---:|---|---|---:|---|")
        for s in segments:
            up = ", ".join(f"{c}:{v:+.2f}/m" for c, v in s.fastest_up)
            down = ", ".join(f"{c}:{v:+.2f}/m" for c, v in s.fastest_down)
            tags = ", ".join(s.tags)
            lines.append(
                f"| {s.start_time[-14:-6]}→{s.end_time[-14:-6]} "
                f"| {s.minutes:.1f} | {fmt(s.bid_start,5)}→{fmt(s.bid_end,5)} "
                f"| {fmt(s.pip_delta,2)} | {up} | {down} | {s.energy:.1f} | {tags} |"
            )
        lines.append("")

        lines.append("### Force angles by segment")
        lines.append("")
        lines.append("| Window | GBP | USD | EUR | JPY | CAD | CHF | AUD |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for s in segments:
            vals = [s.force_angle_deg.get(c) for c in CURRENCIES]
            lines.append(
                f"| {s.start_time[-14:-6]}→{s.end_time[-14:-6]} "
                + " | "
                + " | ".join(fmt(v, 1) for v in vals)
                + " |"
            )
        lines.append("")

        if acc:
            lines.append("### Acceleration pivots")
            lines.append("")
            for a in acc:
                up = ", ".join(f"{c}:{v:+.2f}" for c, v in a["accel_up"])
                down = ", ".join(f"{c}:{v:+.2f}" for c, v in a["accel_down"])
                lines.append(f"- `{a['at']}` accel_up: {up} | accel_down: {down}")
            lines.append("")

    return "\n".join(lines)


def kinematics_summary(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    timeframes: Sequence[int],
) -> Dict:
    out = {
        "module": "pf_force_kinematics",
        "version": "V0.1",
        "db": db_path,
        "symbol": symbol,
        "start": start,
        "end": end,
        "timeframes": [],
    }

    for tf in timeframes:
        rows = load_rows(db_path, symbol, tf, start, end)
        segments = build_segments(rows)
        out["timeframes"].append(
            {
                "timeframe": tf,
                "rows": len(rows),
                "first": rows[0].created_at if rows else None,
                "last": rows[-1].created_at if rows else None,
                "segments": [s.to_dict() for s in segments],
                "accelerations": acceleration_table(segments),
            }
        )

    return out
