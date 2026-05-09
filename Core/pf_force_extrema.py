#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — pf_force_extrema.py V0.1

Read-only module.

Purpose:
    Detect local VALLEY and PEAK in force curves.
    A valley is NOT a random dip. It is a meaningful force minimum:
        - the curve descends, reaches a low, then rises again
        - the depth is significant relative to context
        - the asymmetry (entry speed vs exit speed) tells a story

    ASYMMETRY is key:
        SLOW_ENTRY_FAST_EXIT = energy built up, explosive release (bear trap)
        FAST_ENTRY_SLOW_EXIT = impulsive then absorption
        BALANCED             = no directional edge
        FAST_ENTRY_FAST_EXIT = pass-through (less interesting)

    This module feeds:
        - pf_orchestral_gravity.py (who is in valley / peak at this moment)
        - lab.py (query: "GBP valley AND JPY peak AND H1")

Architecture:
    - Read-only (no DB writes)
    - No Telegram dependencies
    - Input: DB + window
    - Output: list of ExtremaEvent
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

# Minimum force amplitude to qualify as valley/peak
MIN_AMPLITUDE: Dict[int, float] = {
    1:   3.0,    # M1: small dips visible
    5:   5.0,    # M5: meaningful swing
    15:  6.0,    # M15: tactical valley
    30:  7.0,    # M30: structural valley
    60:  8.0,    # H1: gravitational valley
    240: 10.0,   # H4: memory valley
}
MIN_AMPLITUDE_DEFAULT = 6.0

# Window to look before/after the extremum for asymmetry
ASYMMETRY_WINDOW = 3


@dataclass
class ExtremaEvent:
    """A local valley or peak in a force curve."""
    currency: str
    timeframe: int
    timestamp: str              # timestamp of the extremum
    extrema_type: str           # VALLEY / PEAK
    force_value: float          # force at the extremum
    force_before: float         # average force in window before
    force_after: float          # average force in window after
    amplitude: float            # depth (valley) or height (peak)
    entry_velocity: float       # force change per bar entering the extremum
    exit_velocity: float        # force change per bar exiting the extremum
    asymmetry: str              # SLOW_ENTRY_FAST_EXIT / FAST_ENTRY_SLOW_EXIT / BALANCED / FAST_ENTRY_FAST_EXIT
    asymmetry_ratio: float      # |exit_velocity / entry_velocity| (>1 = faster exit)
    bid_at: Optional[float]

    def to_dict(self) -> dict:
        return {
            "currency": self.currency,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp,
            "extrema_type": self.extrema_type,
            "force_value": self.force_value,
            "force_before": self.force_before,
            "force_after": self.force_after,
            "amplitude": self.amplitude,
            "entry_velocity": self.entry_velocity,
            "exit_velocity": self.exit_velocity,
            "asymmetry": self.asymmetry,
            "asymmetry_ratio": self.asymmetry_ratio,
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
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cols = ["created_at", "bid"] + list(FORCE_COLS.values())
    cur.execute(
        f"SELECT {', '.join(cols)} FROM force_snapshots "
        "WHERE symbol = ? AND timeframe = ? AND created_at >= ? AND created_at <= ? "
        "ORDER BY created_at ASC",
        (symbol, tf, start, end),
    )
    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def _classify_asymmetry(entry_vel: float, exit_vel: float) -> Tuple[str, float]:
    """
    Classify entry vs exit velocity asymmetry.

    Convention:
        entry_vel = |velocity entering extremum| (positive scalar)
        exit_vel  = |velocity exiting extremum|  (positive scalar)

    Returns (label, ratio).
    """
    if entry_vel < 1e-6:
        return "BALANCED", 1.0

    ratio = exit_vel / entry_vel

    fast_threshold = 1.4
    slow_threshold = 0.7

    entry_fast = entry_vel > 5.0
    exit_fast  = exit_vel  > 5.0

    if ratio >= fast_threshold:
        if entry_fast:
            return "FAST_ENTRY_FAST_EXIT", round(ratio, 2)
        return "SLOW_ENTRY_FAST_EXIT", round(ratio, 2)
    if ratio <= slow_threshold:
        if exit_fast:
            return "FAST_ENTRY_FAST_EXIT", round(ratio, 2)
        return "FAST_ENTRY_SLOW_EXIT", round(ratio, 2)
    return "BALANCED", round(ratio, 2)


def detect_extrema(
    db_path: str,
    symbol: str,
    timeframe: int,
    start: str,
    end: str,
    window: int = ASYMMETRY_WINDOW,
    currencies: Optional[List[str]] = None,
) -> List[ExtremaEvent]:
    """
    Detect valleys and peaks for all currencies at a given TF.

    Algorithm:
        For each currency, look at the force series.
        A local minimum at index i (VALLEY):
            - force[i] < force[i-1] and force[i] < force[i+1]
            - amplitude = min(force[i-1..i-window]) - force[i] >= threshold
        A local maximum at index i (PEAK):
            - force[i] > force[i-1] and force[i] > force[i+1]
            - amplitude = force[i] - max(force[i+1..i+window]) >= threshold
    """
    rows = _load_rows(db_path, symbol, timeframe, start, end)
    min_amp = MIN_AMPLITUDE.get(timeframe, MIN_AMPLITUDE_DEFAULT)
    targets = currencies or CURRENCIES

    if len(rows) < window * 2 + 3:
        return []

    events: List[ExtremaEvent] = []

    for c in targets:
        col = FORCE_COLS.get(c)
        if not col:
            continue

        # Build (timestamp, force, bid) series
        series: List[Tuple[str, float, Optional[float]]] = []
        for r in rows:
            f = _safe_float(r.get(col))
            if f is not None:
                series.append((str(r["created_at"]), f, _safe_float(r.get("bid"))))

        n = len(series)
        if n < window * 2 + 3:
            continue

        for i in range(window, n - window):
            ts, force, bid = series[i]
            forces_before = [series[j][1] for j in range(max(0, i - window), i)]
            forces_after  = [series[j][1] for j in range(i + 1, min(n, i + window + 1))]

            if not forces_before or not forces_after:
                continue

            avg_before = sum(forces_before) / len(forces_before)
            avg_after  = sum(forces_after) / len(forces_after)

            # Entry velocity: average change per bar entering
            entry_delta = abs(force - forces_before[0]) if forces_before else 0.0
            entry_vel = entry_delta / len(forces_before) if forces_before else 0.0

            # Exit velocity: average change per bar exiting
            exit_delta = abs(forces_after[-1] - force) if forces_after else 0.0
            exit_vel = exit_delta / len(forces_after) if forces_after else 0.0

            asymmetry_label, asym_ratio = _classify_asymmetry(entry_vel, exit_vel)

            # VALLEY: local minimum
            is_valley = force < min(forces_before) and force < min(forces_after)
            if is_valley:
                amplitude = avg_before - force
                if amplitude >= min_amp:
                    events.append(ExtremaEvent(
                        currency=c,
                        timeframe=timeframe,
                        timestamp=ts,
                        extrema_type="VALLEY",
                        force_value=round(force, 2),
                        force_before=round(avg_before, 2),
                        force_after=round(avg_after, 2),
                        amplitude=round(amplitude, 2),
                        entry_velocity=round(entry_vel, 3),
                        exit_velocity=round(exit_vel, 3),
                        asymmetry=asymmetry_label,
                        asymmetry_ratio=asym_ratio,
                        bid_at=bid,
                    ))
                continue

            # PEAK: local maximum
            is_peak = force > max(forces_before) and force > max(forces_after)
            if is_peak:
                amplitude = force - avg_after
                if amplitude >= min_amp:
                    events.append(ExtremaEvent(
                        currency=c,
                        timeframe=timeframe,
                        timestamp=ts,
                        extrema_type="PEAK",
                        force_value=round(force, 2),
                        force_before=round(avg_before, 2),
                        force_after=round(avg_after, 2),
                        amplitude=round(amplitude, 2),
                        entry_velocity=round(entry_vel, 3),
                        exit_velocity=round(exit_vel, 3),
                        asymmetry=asymmetry_label,
                        asymmetry_ratio=asym_ratio,
                        bid_at=bid,
                    ))

    return sorted(events, key=lambda e: (e.timestamp, e.currency))


def detect_extrema_multi_tf(
    db_path: str,
    symbol: str,
    timeframes: List[int],
    start: str,
    end: str,
    window: int = ASYMMETRY_WINDOW,
    currencies: Optional[List[str]] = None,
) -> Dict[int, List[ExtremaEvent]]:
    """Run extrema detection over multiple timeframes."""
    result: Dict[int, List[ExtremaEvent]] = {}
    for tf in timeframes:
        result[tf] = detect_extrema(db_path, symbol, tf, start, end, window, currencies)
    return result


def extrema_summary(events: List[ExtremaEvent]) -> dict:
    """Summary for cockpit / alerting."""
    if not events:
        return {
            "count": 0,
            "valleys": 0,
            "peaks": 0,
            "by_currency": {},
            "slow_entry_fast_exit": 0,
            "most_recent": None,
        }

    valleys = [e for e in events if e.extrema_type == "VALLEY"]
    peaks   = [e for e in events if e.extrema_type == "PEAK"]

    by_currency: Dict[str, Dict[str, int]] = {}
    for e in events:
        if e.currency not in by_currency:
            by_currency[e.currency] = {"VALLEY": 0, "PEAK": 0}
        by_currency[e.currency][e.extrema_type] += 1

    slow_entry_fast = sum(1 for e in events if e.asymmetry == "SLOW_ENTRY_FAST_EXIT")
    most_recent = max(events, key=lambda e: e.timestamp)

    return {
        "count": len(events),
        "valleys": len(valleys),
        "peaks": len(peaks),
        "by_currency": by_currency,
        "slow_entry_fast_exit": slow_entry_fast,
        "most_recent": most_recent.to_dict(),
    }
