#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow Orchestral Scene Report V0.1

Reads multi-TF force kinematics and produces an orchestral narrative:
- H1 leaders / followers / antagonists
- M15 tactical inflections and valleys
- M5 relay confirmation
- M1 microfilm birth events

Uses existing pf_force_kinematics.py logic.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]


@dataclass
class ForceRow:
    created_at: str
    dt: datetime
    symbol: str
    timeframe: int
    bid: Optional[float]
    forces: Dict[str, float]


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


def load_rows(db_path: str, symbol: str, tf: int, start: str, end: str) -> List[ForceRow]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        """
        SELECT created_at, symbol, timeframe, bid,
               force_gbp, force_usd, force_eur, force_jpy,
               force_cad, force_chf, force_aud
        FROM force_snapshots
        WHERE symbol = ? AND timeframe = ?
          AND created_at >= ? AND created_at <= ?
        ORDER BY created_at ASC
        """,
        (symbol, tf, start, end),
    )
    
    rows: List[ForceRow] = []
    for r in cur.fetchall():
        forces = {
            "GBP": safe_float(r["force_gbp"]),
            "USD": safe_float(r["force_usd"]),
            "EUR": safe_float(r["force_eur"]),
            "JPY": safe_float(r["force_jpy"]),
            "CAD": safe_float(r["force_cad"]),
            "CHF": safe_float(r["force_chf"]),
            "AUD": safe_float(r["force_aud"]),
        }
        forces = {k: v for k, v in forces.items() if v is not None}
        rows.append(
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
    return rows


def compute_angle_velocity(rows: List[ForceRow]) -> Dict[str, List[Tuple[str, float, float]]]:
    """Returns {currency: [(timestamp, angle_deg, velocity_per_min), ...]}"""
    if len(rows) < 2:
        return {}
    
    result: Dict[str, List[Tuple[str, float, float]]] = {c: [] for c in CURRENCIES}
    
    for a, b in zip(rows, rows[1:]):
        seconds = (b.dt - a.dt).total_seconds()
        if seconds <= 0:
            continue
        minutes = seconds / 60.0
        
        for c in CURRENCIES:
            if c not in a.forces or c not in b.forces:
                continue
            delta = b.forces[c] - a.forces[c]
            velocity = delta / minutes
            import math
            angle = round(math.degrees(math.atan(velocity)), 2)
            result[c].append((b.created_at, angle, velocity))
    
    return result


def detect_h1_leaders(rows: List[ForceRow], threshold: float = 5.0) -> Dict:
    """Identify H1 leaders, followers, antagonists based on angle strength."""
    angles = compute_angle_velocity(rows)
    
    # Average angle over the window for each currency
    avg_angles = {}
    for c, data in angles.items():
        if not data:
            continue
        avg_angles[c] = sum(a for _, a, _ in data) / len(data)
    
    if not avg_angles:
        return {"leaders": [], "followers": [], "antagonists": [], "neutral": [], "coalitions": []}
    
    # Sort by absolute angle
    sorted_by_strength = sorted(avg_angles.items(), key=lambda kv: abs(kv[1]), reverse=True)
    
    leaders = []
    antagonists = []
    neutral = []
    
    for c, angle in sorted_by_strength:
        if abs(angle) >= threshold:
            if angle > 0:
                leaders.append((c, angle))
            else:
                antagonists.append((c, angle))
        else:
            neutral.append((c, angle))
    
    # Detect coalitions (similar angles)
    coalitions = []
    if len(leaders) >= 2:
        for i, (c1, a1) in enumerate(leaders):
            for c2, a2 in leaders[i+1:]:
                if abs(a1 - a2) < 3.0:  # synchro threshold
                    coalitions.append((c1, c2, "UP_SYNCHRO"))
    
    if len(antagonists) >= 2:
        for i, (c1, a1) in enumerate(antagonists):
            for c2, a2 in antagonists[i+1:]:
                if abs(a1 - a2) < 3.0:
                    coalitions.append((c1, c2, "DOWN_SYNCHRO"))
    
    # Detect followers (currencies pulled by leaders)
    followers = []
    if leaders and neutral:
        dominant_leader = leaders[0][0]  # strongest leader
        for c, angle in neutral:
            if 0 < angle < 4.0:  # weak positive = following
                followers.append((c, angle, dominant_leader))
    
    return {
        "leaders": leaders,
        "antagonists": antagonists,
        "neutral": neutral,
        "coalitions": coalitions,
        "followers": followers,
    }


def detect_m15_inflections(rows: List[ForceRow], min_delta: float = 15.0) -> List[Dict]:
    """Detect brutal angle changes (inflections) on M15."""
    angles = compute_angle_velocity(rows)
    
    inflections = []
    for c, data in angles.items():
        if len(data) < 3:
            continue
        
        for i in range(1, len(data) - 1):
            prev_angle = data[i-1][1]
            curr_angle = data[i][1]
            next_angle = data[i+1][1]
            
            delta_prev = curr_angle - prev_angle
            delta_next = next_angle - curr_angle
            
            # Brutal change: large delta + sign flip
            if abs(delta_prev) > min_delta and prev_angle * curr_angle < 0:
                inflections.append({
                    "currency": c,
                    "timestamp": data[i][0],
                    "angle_before": round(prev_angle, 1),
                    "angle_after": round(curr_angle, 1),
                    "delta": round(delta_prev, 1),
                    "type": "CONTRESENS_PLIURE_UP" if curr_angle > 0 else "CONTRESENS_PLIURE_DOWN"
                })
    
    return sorted(inflections, key=lambda x: x["timestamp"])


def detect_valleys_peaks(rows: List[ForceRow], min_depth: float = 8.0) -> List[Dict]:
    """Detect local force minima (valleys) and maxima (peaks)."""
    if len(rows) < 5:
        return []
    
    extrema = []
    
    for c in CURRENCIES:
        forces = [(r.created_at, r.forces.get(c)) for r in rows]
        forces = [(t, f) for t, f in forces if f is not None]
        
        if len(forces) < 5:
            continue
        
        for i in range(2, len(forces) - 2):
            curr_force = forces[i][1]
            left = [forces[j][1] for j in range(i-2, i)]
            right = [forces[j][1] for j in range(i+1, i+3)]
            
            # Valley: lower than neighbors
            if all(curr_force < f for f in left + right):
                depth = min(left + right) - curr_force
                if depth >= min_depth:
                    extrema.append({
                        "currency": c,
                        "timestamp": forces[i][0],
                        "type": "VALLEY",
                        "force": round(curr_force, 1),
                        "depth": round(depth, 1),
                    })
            
            # Peak: higher than neighbors
            elif all(curr_force > f for f in left + right):
                height = curr_force - max(left + right)
                if height >= min_depth:
                    extrema.append({
                        "currency": c,
                        "timestamp": forces[i][0],
                        "type": "PEAK",
                        "force": round(curr_force, 1),
                        "height": round(height, 1),
                    })
    
    return sorted(extrema, key=lambda x: x["timestamp"])


def make_orchestral_report(db_path: str, symbol: str, start: str, end: str) -> str:
    lines = []
    lines.append("# POWERFLOW ORCHESTRAL SCENE REPORT V0.1")
    lines.append("")
    lines.append(f"**Window:** {start} → {end}")
    lines.append(f"**Symbol:** {symbol}")
    lines.append("")
    
    # Load data
    h1_rows = load_rows(db_path, symbol, 60, start, end)
    m15_rows = load_rows(db_path, symbol, 15, start, end)
    m5_rows = load_rows(db_path, symbol, 5, start, end)
    m1_rows = load_rows(db_path, symbol, 1, start, end)
    
    lines.append(f"**Coverage:** H1={len(h1_rows)} bars, M15={len(m15_rows)}, M5={len(m5_rows)}, M1={len(m1_rows)}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # H1 LEADERS
    lines.append("## H1 ORCHESTRAL GRAVITY")
    lines.append("")
    h1_analysis = detect_h1_leaders(h1_rows, threshold=4.0)
    
    if h1_analysis["leaders"]:
        lines.append("**LEADERS (angle > +4°):**")
        for c, angle in h1_analysis["leaders"]:
            lines.append(f"- **{c}**: {angle:+.1f}° (STRONG UP)")
        lines.append("")
    
    if h1_analysis["antagonists"]:
        lines.append("**ANTAGONISTS (angle < -4°):**")
        for c, angle in h1_analysis["antagonists"]:
            lines.append(f"- **{c}**: {angle:+.1f}° (DOWN)")
        lines.append("")
    
    if h1_analysis["coalitions"]:
        lines.append("**COALITIONS SYNCHRO:**")
        for c1, c2, typ in h1_analysis["coalitions"]:
            lines.append(f"- {c1} + {c2} ({typ})")
        lines.append("")
    
    if h1_analysis.get("followers"):
        lines.append("**FOLLOWERS (pulled by leaders):**")
        for c, angle, leader in h1_analysis["followers"]:
            lines.append(f"- {c} ({angle:+.1f}°) following {leader}")
        lines.append("")
    
    if h1_analysis["neutral"]:
        lines.append("**NEUTRAL (|angle| < 4°):**")
        neutral_str = ", ".join(f"{c} ({a:+.1f}°)" for c, a in h1_analysis["neutral"])
        lines.append(f"- {neutral_str}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # M15 INFLECTIONS
    lines.append("## M15 TACTICAL INFLECTIONS")
    lines.append("")
    m15_inflections = detect_m15_inflections(m15_rows, min_delta=12.0)
    
    if m15_inflections:
        for inf in m15_inflections[:10]:  # Top 10
            lines.append(
                f"- **{inf['timestamp'][-14:-6]}** — {inf['currency']} {inf['type']}: "
                f"{inf['angle_before']:+.1f}° → {inf['angle_after']:+.1f}° (Δ {inf['delta']:+.1f}°)"
            )
        if len(m15_inflections) > 10:
            lines.append(f"- *(+{len(m15_inflections) - 10} more inflections...)*")
    else:
        lines.append("*No significant inflections detected on M15.*")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # M15 VALLEYS/PEAKS
    lines.append("## M15 FORCE EXTREMA (Valleys / Peaks)")
    lines.append("")
    m15_extrema = detect_valleys_peaks(m15_rows, min_depth=6.0)
    
    if m15_extrema:
        for ext in m15_extrema[:10]:
            if ext["type"] == "VALLEY":
                lines.append(
                    f"- **{ext['timestamp'][-14:-6]}** — {ext['currency']} VALLEY "
                    f"(force {ext['force']}, depth {ext['depth']})"
                )
            else:
                lines.append(
                    f"- **{ext['timestamp'][-14:-6]}** — {ext['currency']} PEAK "
                    f"(force {ext['force']}, height {ext['height']})"
                )
        if len(m15_extrema) > 10:
            lines.append(f"- *(+{len(m15_extrema) - 10} more extrema...)*")
    else:
        lines.append("*No significant valleys/peaks detected on M15.*")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # M5 TOP EVENTS
    lines.append("## M5 RELAY CONFIRMATION")
    lines.append("")
    m5_angles = compute_angle_velocity(m5_rows)
    
    # Find strongest M5 movements
    m5_events = []
    for c, data in m5_angles.items():
        for ts, angle, vel in data:
            if abs(angle) > 20.0:
                m5_events.append((ts, c, angle, vel))
    
    m5_events = sorted(m5_events, key=lambda x: abs(x[2]), reverse=True)[:15]
    
    if m5_events:
        for ts, c, angle, vel in m5_events:
            direction = "UP" if angle > 0 else "DOWN"
            lines.append(f"- **{ts[-14:-6]}** — {c} {direction} relay: {angle:+.1f}° ({vel:+.2f}/min)")
    else:
        lines.append("*No strong M5 relay events.*")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # M1 MICROFILM BIRTHS
    lines.append("## M1 MICROFILM BIRTH EVENTS")
    lines.append("")
    m1_angles = compute_angle_velocity(m1_rows)
    
    # Find M1 extreme angles (birth candidates)
    m1_births = []
    for c, data in m1_angles.items():
        for ts, angle, vel in data:
            if abs(angle) > 60.0:  # brutal M1 shift
                m1_births.append((ts, c, angle, vel))
    
    m1_births = sorted(m1_births, key=lambda x: abs(x[2]), reverse=True)[:20]
    
    if m1_births:
        for ts, c, angle, vel in m1_births:
            direction = "BIRTH_UP" if angle > 0 else "BIRTH_DOWN"
            lines.append(f"- **{ts[-14:-6]}** — {c} {direction}: {angle:+.0f}° ({vel:+.1f}/min)")
    else:
        lines.append("*No extreme M1 births detected.*")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("**END ORCHESTRAL REPORT**")
    
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    
    if not Path(args.db).exists():
        raise SystemExit(f"DB not found: {args.db}")
    
    report = make_orchestral_report(args.db, args.symbol, args.start, args.end)
    
    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"✅ Orchestral report written: {args.out}")
    else:
        print(report)
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
