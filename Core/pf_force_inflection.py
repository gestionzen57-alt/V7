#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — pf_force_inflection.py V0.1

Read-only module.

Purpose:
    Detect PLIURE: brutal angle change at countersense of dominant slope.
    A pliure is NOT a simple angle change.
    A pliure is a force curve that FOLDS against its own momentum.

    Example:
        GBP angle series: [-15, -18, -22, +8]  ← CONTRESENS_PLIURE_UP
        EUR angle series: [+14, +11, +16, -7]  ← CONTRESENS_PLIURE_DOWN

    Rules:
        1. Dominant slope must be established (N bars in same direction)
        2. Current angle must flip sign (contresens)
        3. Delta must exceed threshold (brutal = meaningful fold)
        4. Severity is classified: MICRO / MODERATE / BRUTAL / EXTREME

Architecture:
    - Read-only (no DB writes)
    - No Telegram dependencies
    - Input: list of (timestamp, angle_deg) per currency per TF
    - Output: list of InflectionEvent
"""

from __future__ import annotations

import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


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

# Minimum bars to establish dominant slope
MIN_SLOPE_BARS = 2

# Minimum angle delta to qualify as a pliure (degrees)
PLIURE_DELTA_MIN: Dict[int, float] = {
    1:   15.0,   # M1 microfilm: very reactive
    5:   12.0,   # M5 relay
    15:  10.0,   # M15 tactical
    30:   8.0,   # M30 gravity
    60:   6.0,   # H1 structural
    240:  5.0,   # H4 memory
}
PLIURE_DELTA_DEFAULT = 10.0

# Severity thresholds (delta angle)
SEVERITY_MICRO    = 10.0
SEVERITY_MODERATE = 20.0
SEVERITY_BRUTAL   = 35.0
SEVERITY_EXTREME  = 55.0


def _severity(delta: float) -> str:
    abs_delta = abs(delta)
    if abs_delta >= SEVERITY_EXTREME:
        return "EXTREME"
    if abs_delta >= SEVERITY_BRUTAL:
        return "BRUTAL"
    if abs_delta >= SEVERITY_MODERATE:
        return "MODERATE"
    return "MICRO"


@dataclass
class InflectionEvent:
    """A pliure: brutal contresens angle change for one currency at one TF."""
    currency: str
    timeframe: int
    timestamp: str
    angle_before: float          # angle just before the fold
    angle_after: float           # angle at the fold
    slope_dominant: float        # average angle over slope_bars before
    delta: float                 # angle_after - angle_before
    contresens: bool             # True if sign flip
    severity: str                # MICRO / MODERATE / BRUTAL / EXTREME
    pliure_type: str             # CONTRESENS_PLIURE_UP / CONTRESENS_PLIURE_DOWN / SAME_DIRECTION_INFLECTION
    slope_bars: int              # number of bars used to compute dominant slope
    bid_at: Optional[float]

    def to_dict(self) -> dict:
        return {
            "currency": self.currency,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "angle_before": self.angle_before,
            "angle_after": self.angle_after,
            "slope_dominant": self.slope_dominant,
            "delta": self.delta,
            "contresens": self.contresens,
            "severity": self.severity,
            "pliure_type": self.pliure_type,
            "slope_bars": self.slope_bars,
            "bid_at": self.bid_at,
        }


def _parse_dt(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def _safe_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except Exception:
        return None


def _load_rows(db_path: str, symbol: str, tf: int, start: str, end: str) -> List[dict]:
    """Load force rows for one TF, ordered by time."""
    cols = ["created_at", "bid"] + list(FORCE_COLS.values())
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute(
        f"SELECT {', '.join(cols)} FROM force_snapshots "
        "WHERE symbol = ? AND timeframe = ? AND created_at >= ? AND created_at <= ? "
        "ORDER BY created_at ASC",
        (symbol, tf, start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def _compute_angle_series(rows: List[dict]) -> List[Tuple[str, Dict[str, float], Optional[float]]]:
    """
    Returns list of (timestamp, {currency: angle_deg}, bid).
    Angle computed between consecutive rows.
    First row is skipped (no previous row).
    """
    if len(rows) < 2:
        return []

    result = []
    for a, b in zip(rows, rows[1:]):
        ts_a = _parse_dt(str(a["created_at"]))
        ts_b = _parse_dt(str(b["created_at"]))
        seconds = (ts_b - ts_a).total_seconds()
        if seconds <= 0:
            continue
        minutes = seconds / 60.0

        angles: Dict[str, float] = {}
        for c, col in FORCE_COLS.items():
            va = _safe_float(a.get(col))
            vb = _safe_float(b.get(col))
            if va is None or vb is None:
                continue
            velocity = (vb - va) / minutes
            angles[c] = round(math.degrees(math.atan(velocity)), 2)

        bid = _safe_float(b.get("bid"))
        result.append((str(b["created_at"]), angles, bid))

    return result


def detect_inflections(
    db_path: str,
    symbol: str,
    timeframe: int,
    start: str,
    end: str,
    min_slope_bars: int = MIN_SLOPE_BARS,
    currencies: Optional[List[str]] = None,
) -> List[InflectionEvent]:
    """
    Detect pliure/inflection events for all currencies at a given TF.

    Returns list of InflectionEvent sorted by timestamp.
    """
    rows = _load_rows(db_path, symbol, timeframe, start, end)
    if len(rows) < min_slope_bars + 2:
        return []

    angle_series = _compute_angle_series(rows)
    if len(angle_series) < min_slope_bars + 1:
        return []

    targets = currencies or CURRENCIES
    min_delta = PLIURE_DELTA_MIN.get(timeframe, PLIURE_DELTA_DEFAULT)
    events: List[InflectionEvent] = []

    for c in targets:
        # Extract angle series for this currency
        c_series: List[Tuple[str, float]] = []
        c_bids: List[Optional[float]] = []

        for ts, angles, bid in angle_series:
            if c in angles:
                c_series.append((ts, angles[c]))
                c_bids.append(bid)

        if len(c_series) < min_slope_bars + 1:
            continue

        # Slide through: for each point i, look at slope over i-N..i-1 vs angle at i
        for i in range(min_slope_bars, len(c_series)):
            ts_curr, angle_curr = c_series[i]
            bid_curr = c_bids[i]

            # Dominant slope = average of previous min_slope_bars angles
            prev_angles = [c_series[j][1] for j in range(i - min_slope_bars, i)]
            slope_dominant = sum(prev_angles) / len(prev_angles)
            angle_before = prev_angles[-1]

            delta = angle_curr - angle_before

            # Must exceed threshold
            if abs(delta) < min_delta:
                continue

            # Check contresens (sign flip between dominant slope and current)
            contresens = (slope_dominant * angle_curr < 0)

            # Determine type
            if contresens:
                pliure_type = (
                    "CONTRESENS_PLIURE_UP"
                    if angle_curr > 0
                    else "CONTRESENS_PLIURE_DOWN"
                )
            else:
                # Same direction but acceleration/deceleration
                pliure_type = "SAME_DIRECTION_INFLECTION"

            # Only emit events (contresens = pliure, same_dir = inflection)
            severity = _severity(delta)

            events.append(InflectionEvent(
                currency=c,
                timeframe=timeframe,
                timestamp=ts_curr,
                angle_before=round(angle_before, 1),
                angle_after=round(angle_curr, 1),
                slope_dominant=round(slope_dominant, 1),
                delta=round(delta, 1),
                contresens=contresens,
                severity=severity,
                pliure_type=pliure_type,
                slope_bars=min_slope_bars,
                bid_at=bid_curr,
            ))

    return sorted(events, key=lambda e: (e.timestamp, e.currency))


def detect_inflections_multi_tf(
    db_path: str,
    symbol: str,
    timeframes: List[int],
    start: str,
    end: str,
    min_slope_bars: int = MIN_SLOPE_BARS,
    currencies: Optional[List[str]] = None,
    contresens_only: bool = False,
) -> Dict[int, List[InflectionEvent]]:
    """
    Run inflection detection over multiple timeframes.

    Returns dict {tf: [events]}.
    """
    result: Dict[int, List[InflectionEvent]] = {}
    for tf in timeframes:
        events = detect_inflections(db_path, symbol, tf, start, end, min_slope_bars, currencies)
        if contresens_only:
            events = [e for e in events if e.contresens]
        result[tf] = events
    return result


def inflection_summary(events: List[InflectionEvent]) -> dict:
    """
    Quick summary for cockpit / logging:
      - count by currency
      - most severe event
      - most recent event
      - brutal+ count
    """
    if not events:
        return {
            "count": 0,
            "brutal_plus": 0,
            "by_currency": {},
            "most_severe": None,
            "most_recent": None,
        }

    by_currency: Dict[str, int] = {}
    for e in events:
        by_currency[e.currency] = by_currency.get(e.currency, 0) + 1

    severity_rank = {"MICRO": 0, "MODERATE": 1, "BRUTAL": 2, "EXTREME": 3}
    most_severe = max(events, key=lambda e: severity_rank.get(e.severity, 0))
    most_recent = max(events, key=lambda e: e.timestamp)
    brutal_plus = sum(1 for e in events if severity_rank.get(e.severity, 0) >= 2)

    return {
        "count": len(events),
        "brutal_plus": brutal_plus,
        "by_currency": by_currency,
        "most_severe": most_severe.to_dict(),
        "most_recent": most_recent.to_dict(),
    }
