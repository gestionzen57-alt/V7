#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - Analyse sequence 06:00 -> now from SQLite DB.

Read-only.
Default:
    DB      = powerflow.db
    symbol  = GBPUSD
    start   = 06:00 on the latest date found in force_snapshots
    end     = MAX(created_at) from force_snapshots

Usage:
    python analyze_powerflow_from_0600_today.py
    python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start 2026-05-04T06:00:00+00:00
    python analyze_powerflow_from_0600_today.py --db powerflow.db --symbol GBPUSD --start-hour 6 --out report_0600.md
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


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
class Row:
    created_at: str
    dt: datetime
    symbol: str
    timeframe: int
    bid: Optional[float]
    forces: Dict[str, float]


def parse_dt(s: str) -> datetime:
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    return datetime.fromisoformat(s)


def iso(dt: datetime) -> str:
    return dt.isoformat(timespec="seconds")


def safe_float(x) -> Optional[float]:
    if x is None:
        return None
    try:
        return float(x)
    except Exception:
        return None


def fmt(x: Optional[float], digits: int = 2) -> str:
    if x is None:
        return "NA"
    return f"{x:.{digits}f}"


def signed(x: Optional[float], digits: int = 2) -> str:
    if x is None:
        return "NA"
    return f"{x:+.{digits}f}"


def load_rows(db_path: str, symbol: str, start: datetime, end: datetime) -> List[Row]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    cols = ", ".join(["created_at", "symbol", "timeframe", "bid"] + list(FORCE_COLS.values()))
    cur.execute(
        f"""
        SELECT {cols}
        FROM force_snapshots
        WHERE symbol = ?
          AND created_at >= ?
          AND created_at <= ?
        ORDER BY timeframe, created_at
        """,
        (symbol, iso(start), iso(end)),
    )
    rows: List[Row] = []
    for r in cur.fetchall():
        dt = parse_dt(r["created_at"])
        forces = {}
        for c, col in FORCE_COLS.items():
            val = safe_float(r[col])
            if val is not None:
                forces[c] = val
        rows.append(
            Row(
                created_at=r["created_at"],
                dt=dt,
                symbol=r["symbol"],
                timeframe=int(r["timeframe"]),
                bid=safe_float(r["bid"]),
                forces=forces,
            )
        )
    con.close()
    return rows


def get_db_range(db_path: str, symbol: str) -> Tuple[str, str, int]:
    con = sqlite3.connect(db_path)
    cur = con.cursor()
    cur.execute(
        "SELECT MIN(created_at), MAX(created_at), COUNT(*) FROM force_snapshots WHERE symbol=?",
        (symbol,),
    )
    out = cur.fetchone()
    con.close()
    return out[0], out[1], out[2]


def latest_date_start(db_path: str, symbol: str, start_hour: int) -> Tuple[datetime, datetime]:
    mn, mx, _ = get_db_range(db_path, symbol)
    if not mx:
        raise SystemExit(f"No rows found for symbol={symbol}")
    end = parse_dt(mx)
    start = end.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if start > end:
        start = end.replace(hour=0, minute=0, second=0, microsecond=0)
    return start, end


def by_tf(rows: Sequence[Row]) -> Dict[int, List[Row]]:
    out: Dict[int, List[Row]] = defaultdict(list)
    for r in rows:
        out[r.timeframe].append(r)
    return dict(sorted(out.items()))


def nearest_row(rows: Sequence[Row], target: datetime) -> Optional[Row]:
    if not rows:
        return None
    return min(rows, key=lambda r: abs((r.dt - target).total_seconds()))


def force_summary(rows: Sequence[Row]) -> Dict[str, Dict[str, float]]:
    out = {}
    if not rows:
        return out
    first = rows[0]
    last = rows[-1]
    for c in CURRENCIES:
        vals = [r.forces[c] for r in rows if c in r.forces]
        if not vals:
            continue
        out[c] = {
            "start": first.forces.get(c, float("nan")),
            "end": last.forces.get(c, float("nan")),
            "delta": last.forces.get(c, float("nan")) - first.forces.get(c, float("nan")),
            "min": min(vals),
            "max": max(vals),
            "range": max(vals) - min(vals),
            "std": pstdev(vals) if len(vals) > 1 else 0.0,
        }
    return out


def top_bottom(forces: Dict[str, float], n: int = 3) -> Tuple[List[Tuple[str, float]], List[Tuple[str, float]]]:
    items = sorted(forces.items(), key=lambda kv: kv[1], reverse=True)
    return items[:n], list(reversed(items[-n:]))


def classify_snapshot(r: Row, prev: Optional[Row] = None) -> str:
    top, low = top_bottom(r.forces, 3)
    high = [c for c, v in top if v >= 60]
    lowc = [c for c, v in low if v <= 40]
    tags = []

    if high:
        tags.append("HIGH_BLOCK_" + "+".join(high))
    if lowc:
        tags.append("LOW_BLOCK_" + "+".join(lowc))

    usd = r.forces.get("USD")
    cad = r.forces.get("CAD")
    eur = r.forces.get("EUR")
    gbp = r.forces.get("GBP")
    aud = r.forces.get("AUD")
    jpy = r.forces.get("JPY")
    chf = r.forces.get("CHF")

    if usd is not None and usd >= 65:
        tags.append("USD_GRAVITY_HIGH")
    if cad is not None and cad >= 65:
        tags.append("CAD_GRAVITY_HIGH")
    if jpy is not None and jpy >= 65:
        tags.append("JPY_REFUGE_HIGH")
    if chf is not None and chf <= 25:
        tags.append("CHF_LOW_PRESSURE")
    if aud is not None and aud <= 30:
        tags.append("AUD_LOW_PRESSURE")
    if gbp is not None and gbp <= 35:
        tags.append("GBP_LOW_PRESSURE")
    if eur is not None and eur >= 70:
        tags.append("EUR_HIGH_PRESSURE")

    if prev is not None:
        deltas = {c: r.forces.get(c, 0.0) - prev.forces.get(c, 0.0) for c in CURRENCIES if c in r.forces and c in prev.forces}
        rising = [c for c, d in sorted(deltas.items(), key=lambda kv: kv[1], reverse=True) if d >= 8]
        falling = [c for c, d in sorted(deltas.items(), key=lambda kv: kv[1]) if d <= -8]
        if rising:
            tags.append("RISING_" + "+".join(rising[:3]))
        if falling:
            tags.append("FALLING_" + "+".join(falling[:3]))

    return " | ".join(tags) if tags else "NEUTRAL_FIELD"


def strongest_windows(rows: Sequence[Row], min_minutes: int = 5, topn: int = 8) -> List[Tuple[float, Row, Row, Dict[str, float]]]:
    if len(rows) < 2:
        return []
    out = []
    for i, a in enumerate(rows):
        target_seconds = min_minutes * 60
        candidates = [b for b in rows[i+1:] if abs((b.dt - a.dt).total_seconds() - target_seconds) <= target_seconds * 0.55]
        if not candidates:
            continue
        b = candidates[0]
        deltas = {c: b.forces.get(c, 0.0) - a.forces.get(c, 0.0) for c in CURRENCIES if c in a.forces and c in b.forces}
        energy = sum(abs(v) for v in deltas.values())
        out.append((energy, a, b, deltas))
    out.sort(key=lambda x: x[0], reverse=True)
    return out[:topn]


def detect_coalitions_at_row(r: Row, threshold_high: float = 60.0, threshold_low: float = 40.0) -> Tuple[List[str], List[str]]:
    highs = [c for c, v in sorted(r.forces.items(), key=lambda kv: kv[1], reverse=True) if v >= threshold_high]
    lows = [c for c, v in sorted(r.forces.items(), key=lambda kv: kv[1]) if v <= threshold_low]
    return highs, lows


def make_report(db: str, symbol: str, start: datetime, end: datetime, rows: List[Row]) -> str:
    lines = []
    mn, mx, total = get_db_range(db, symbol)
    grouped = by_tf(rows)

    lines.append("# PowerFlow DB Sequence Report — 06:00 → now")
    lines.append("")
    lines.append(f"- DB: `{db}`")
    lines.append(f"- Symbol: `{symbol}`")
    lines.append(f"- DB global range: `{mn}` → `{mx}` ({total} rows for symbol)")
    lines.append(f"- Analysis window: `{iso(start)}` → `{iso(end)}`")
    lines.append(f"- Rows loaded in window: `{len(rows)}`")
    lines.append("")
    lines.append("> Lecture: timestamps DB/broker. Si ton broker est H+1, convertir selon ton repère visuel.")
    lines.append("")

    lines.append("## 1. Coverage by timeframe")
    lines.append("")
    for tf, tfrows in grouped.items():
        bids = [r.bid for r in tfrows if r.bid is not None]
        bid_delta = (bids[-1] - bids[0]) if len(bids) >= 2 else None
        lines.append(
            f"- TF={tf:<3} rows={len(tfrows):<4} "
            f"{tfrows[0].created_at} → {tfrows[-1].created_at} "
            f"bid_delta={signed(bid_delta, 5)}"
        )
    lines.append("")

    lines.append("## 2. Force deltas by timeframe")
    lines.append("")
    for tf, tfrows in grouped.items():
        lines.append(f"### TF={tf}")
        s = force_summary(tfrows)
        ordered = sorted(s.items(), key=lambda kv: kv[1]["delta"], reverse=True)
        lines.append("")
        lines.append("| Devise | Start | End | Delta | Min | Max | Range | Std |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
        for c, d in ordered:
            lines.append(
                f"| {c} | {fmt(d['start'])} | {fmt(d['end'])} | {signed(d['delta'])} | "
                f"{fmt(d['min'])} | {fmt(d['max'])} | {fmt(d['range'])} | {fmt(d['std'])} |"
            )
        lines.append("")

    lines.append("## 3. Timeline snapshots")
    lines.append("")
    # timeline by 30-min anchors on M1 if available, otherwise smallest TF
    base_tf = 1 if 1 in grouped else (min(grouped) if grouped else None)
    if base_tf is not None:
        base_rows = grouped[base_tf]
        # create 30m anchors
        cur = start.replace(minute=0, second=0, microsecond=0)
        if cur < start:
            cur = cur.replace(minute=30) if start.minute <= 30 else cur
        anchors = []
        t = start
        # include start, each 30m-ish, end
        anchors.append(start)
        h = start.replace(minute=0, second=0, microsecond=0)
        while h <= end:
            for m in (0, 30):
                a = h.replace(minute=m, second=0, microsecond=0)
                if start < a < end:
                    anchors.append(a)
            h = h.replace(hour=h.hour + 1) if h.hour < 23 else h
            if h.hour == 23 and h.minute == 0 and h.date() == end.date() and h > end:
                break
            if len(anchors) > 80:
                break
        anchors.append(end)
        # normalize unique
        seen = set()
        anchors2 = []
        for a in sorted(anchors):
            k = iso(a)
            if k not in seen:
                seen.add(k); anchors2.append(a)

        prev = None
        for a in anchors2:
            r = nearest_row(base_rows, a)
            if r is None:
                continue
            top, low = top_bottom(r.forces, 3)
            tag = classify_snapshot(r, prev)
            lines.append(
                f"- `{r.created_at}` TF={base_tf} bid={fmt(r.bid, 5)} | "
                f"TOP: {', '.join(f'{c}:{v:.1f}' for c,v in top)} | "
                f"LOW: {', '.join(f'{c}:{v:.1f}' for c,v in low)} | {tag}"
            )
            prev = r
    lines.append("")

    lines.append("## 4. Strongest rotation windows")
    lines.append("")
    for tf in sorted(grouped):
        tfrows = grouped[tf]
        # choose a sensible window: TF=1 -> 5 min, TF=5 -> 15 min, otherwise one bar-ish
        minutes = 5 if tf == 1 else (15 if tf == 5 else max(15, tf))
        wins = strongest_windows(tfrows, min_minutes=minutes, topn=5)
        if not wins:
            continue
        lines.append(f"### TF={tf} strongest ~{minutes}m moves")
        for energy, a, b, deltas in wins:
            up = sorted(deltas.items(), key=lambda kv: kv[1], reverse=True)[:3]
            down = sorted(deltas.items(), key=lambda kv: kv[1])[:3]
            lines.append(
                f"- `{a.created_at}` → `{b.created_at}` energy={energy:.1f} | "
                f"UP: {', '.join(f'{c}{d:+.1f}' for c,d in up)} | "
                f"DOWN: {', '.join(f'{c}{d:+.1f}' for c,d in down)} | "
                f"bid {fmt(a.bid,5)} → {fmt(b.bid,5)}"
            )
        lines.append("")

    lines.append("## 5. PowerFlow reading")
    lines.append("")
    lines.append("### What PowerFlow can see with the current DB schema")
    lines.append("")
    lines.append("- Forces by currency: YES")
    lines.append("- Bid movement: YES")
    lines.append("- Multi-timeframe force alignment: YES")
    lines.append("- Coalition blocks high/low: YES")
    lines.append("- Leader/follower deltas: YES, approximated from force changes")
    lines.append("- OHLC candle respiration: NO, not persisted in this DB")
    lines.append("- tick_volume activity: NO, not persisted in this DB")
    lines.append("- pips/body/range/spread friction: NO, not persisted in this DB")
    lines.append("- NZD: NO, not persisted in this DB")
    lines.append("")
    lines.append("### Suggested Flow classification")
    lines.append("")
    lines.append("Use the strongest rotation windows above to name the sequence. Typical labels:")
    lines.append("")
    lines.append("```text")
    lines.append("HIGH_BLOCK_EXTENSION")
    lines.append("RISK_BLOCK_FOLDING")
    lines.append("USD_GRAVITY_RETAKE")
    lines.append("CAD_RESPRING_FROM_LOW")
    lines.append("JPY_REFUGE_RESPONSE")
    lines.append("LATE_CHF_RESPONSE")
    lines.append("CENTER_REBALANCE_FIELD")
    lines.append("```")
    lines.append("")
    lines.append("## 6. Next tactical step")
    lines.append("")
    lines.append("If one window is confirmed visually, rerun a narrower scan around it, for example:")
    lines.append("")
    lines.append("```powershell")
    lines.append("python analyze_powerflow_from_0600_today.py --start 2026-05-04T09:00:00+00:00 --end 2026-05-04T09:45:00+00:00 --out sequence_0900_0945.md")
    lines.append("```")
    lines.append("")

    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--start-hour", type=int, default=6)
    ap.add_argument("--start", default=None)
    ap.add_argument("--end", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"DB not found: {args.db}")

    if args.start and args.end:
        start = parse_dt(args.start)
        end = parse_dt(args.end)
    else:
        start, end = latest_date_start(args.db, args.symbol, args.start_hour)
        if args.start:
            start = parse_dt(args.start)
        if args.end:
            end = parse_dt(args.end)

    rows = load_rows(args.db, args.symbol, start, end)
    report = make_report(args.db, args.symbol, start, end, rows)

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
        print(f"OK wrote report: {args.out}")
    else:
        print(report)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
