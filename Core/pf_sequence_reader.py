#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - Sequence Reader V0.1

Read-only module.

Purpose:
    Read force_snapshots and detect raw sequence events:
    - respring block
    - folding block
    - node birth with price lag
    - confirmation leg on higher timeframe
    - high energy rotations

Current DB schema supported:
    created_at, symbol, timeframe, bid,
    force_gbp, force_usd, force_eur, force_jpy,
    force_cad, force_chf, force_aud

No dependency.
"""

from __future__ import annotations

import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
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
class ForceRow:
    created_at: str
    dt: datetime
    symbol: str
    timeframe: int
    bid: Optional[float]
    forces: Dict[str, float]


@dataclass
class SequenceEvent:
    start_time: str
    end_time: str
    timeframe: int
    event_type: str
    score: float
    energy: float
    bid_start: Optional[float]
    bid_end: Optional[float]
    bid_delta: Optional[float]
    up_block: List[str]
    down_block: List[str]
    up_deltas: Dict[str, float]
    down_deltas: Dict[str, float]
    tags: List[str]
    cockpit_sentence: str
    note: str

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


def fmt_price(value: Optional[float]) -> str:
    if value is None:
        return "NA"
    return f"{value:.5f}"


def fmt_signed(value: Optional[float], digits: int = 5) -> str:
    if value is None:
        return "NA"
    return f"{value:+.{digits}f}"


def load_force_rows(
    db_path: str,
    symbol: str,
    timeframe: int,
    start: str,
    end: str,
) -> List[ForceRow]:
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

    rows: List[ForceRow] = []
    for r in cur.fetchall():
        forces: Dict[str, float] = {}
        for c, col in FORCE_COLS.items():
            v = safe_float(r[col])
            if v is not None:
                forces[c] = v
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


def nearest_future_row(
    rows: Sequence[ForceRow],
    start_index: int,
    target_seconds: float,
    tolerance_seconds: float,
) -> Optional[ForceRow]:
    if start_index >= len(rows) - 1:
        return None

    a = rows[start_index]
    best: Optional[ForceRow] = None
    best_gap: Optional[float] = None

    for b in rows[start_index + 1:]:
        delta = (b.dt - a.dt).total_seconds()
        if delta <= 0:
            continue
        gap = abs(delta - target_seconds)
        if gap <= tolerance_seconds and (best_gap is None or gap < best_gap):
            best = b
            best_gap = gap
        if delta > target_seconds + tolerance_seconds:
            break

    return best


def classify_direction(up_block: Sequence[str], down_block: Sequence[str]) -> str:
    up = set(up_block)
    down = set(down_block)

    if "USD" in up and "GBP" in down:
        return "GBPUSD_BEARISH_FORCE"
    if "GBP" in up and "USD" in down:
        return "GBPUSD_BULLISH_FORCE"
    if "USD" in up:
        return "USD_GRAVITY_UP"
    if "USD" in down:
        return "USD_GRAVITY_DOWN"
    return "MIXED_FORCE_ROTATION"


def detect_event_type(
    timeframe: int,
    energy: float,
    up_block: Sequence[str],
    down_block: Sequence[str],
    bid_delta: Optional[float],
    min_energy_birth: float,
    min_energy_confirm: float,
    price_lag_abs: float,
    price_pay_abs: float,
) -> Tuple[str, List[str]]:
    tags: List[str] = []

    if len(up_block) >= 2:
        tags.append("SYNC_RESPRING")
    if len(down_block) >= 2:
        tags.append("SYNC_FOLD")
    if len(up_block) >= 2 and len(down_block) >= 2:
        tags.append("OPPOSITE_BLOCK_ROTATION")

    price_lag = bid_delta is not None and abs(bid_delta) <= price_lag_abs
    price_pay = bid_delta is not None and abs(bid_delta) >= price_pay_abs

    if price_lag:
        tags.append("PRICE_LAG")
    if price_pay:
        tags.append("PRICE_PAYING")

    direction = classify_direction(up_block, down_block)
    tags.append(direction)

    if timeframe == 1 and energy >= min_energy_birth and len(up_block) >= 2 and len(down_block) >= 2 and price_lag:
        return "NODE_BIRTH_FAST", tags

    if timeframe in (5, 15) and energy >= min_energy_confirm and len(up_block) >= 2 and len(down_block) >= 2 and price_pay:
        return "NODE_CONFIRMATION_LEG", tags

    if energy >= min_energy_birth and len(up_block) >= 2 and len(down_block) >= 2 and price_lag:
        return "COUNTER_FORCE_BREATH_OR_RAW_NODE", tags

    if energy >= min_energy_confirm and len(up_block) >= 2 and len(down_block) >= 2:
        return "HIGH_ENERGY_ROTATION", tags

    return "RAW_SEQUENCE_MOVE", tags


def score_event(
    energy: float,
    up_block: Sequence[str],
    down_block: Sequence[str],
    bid_delta: Optional[float],
    price_lag_abs: float,
) -> float:
    block_part = min(1.0, (len(up_block) + len(down_block)) / 6.0)
    energy_part = min(1.0, energy / 120.0)
    lag_part = 0.15 if bid_delta is not None and abs(bid_delta) <= price_lag_abs else 0.0
    return round(min(1.0, 0.55 * energy_part + 0.30 * block_part + lag_part), 4)


def make_sentence(event_type: str, tf: int, up_block: Sequence[str], down_block: Sequence[str], bid_delta: Optional[float], score: float) -> str:
    up = "+".join(up_block) if up_block else "NO_UP_BLOCK"
    down = "+".join(down_block) if down_block else "NO_DOWN_BLOCK"

    if event_type == "NODE_BIRTH_FAST":
        return f"[TF{tf}] NODE NAISSANT - {up} respring contre {down}. Prix encore retenu. score={score:.2f}"

    if event_type == "NODE_CONFIRMATION_LEG":
        return f"[TF{tf}] NODE CONFIRME - {up} poursuit contre {down}. Bid paie {fmt_signed(bid_delta)}. score={score:.2f}"

    if event_type == "COUNTER_FORCE_BREATH_OR_RAW_NODE":
        return f"[TF{tf}] RESPIRATION / RAW NODE - {up} contre {down}. Prix faible. score={score:.2f}"

    if event_type == "HIGH_ENERGY_ROTATION":
        return f"[TF{tf}] ROTATION FORTE - {up} contre {down}. bid_delta={fmt_signed(bid_delta)} score={score:.2f}"

    return f"[TF{tf}] mouvement brut - {up} / {down}. score={score:.2f}"


def scan_timeframe(
    rows: Sequence[ForceRow],
    window_minutes: int,
    min_delta: float,
    min_energy_birth: float,
    min_energy_confirm: float,
    price_lag_abs: float,
    price_pay_abs: float,
    tolerance_ratio: float = 0.55,
) -> List[SequenceEvent]:
    if len(rows) < 2:
        return []

    target_seconds = window_minutes * 60.0
    tolerance_seconds = max(60.0, target_seconds * tolerance_ratio)

    events: List[SequenceEvent] = []

    for i, a in enumerate(rows[:-1]):
        b = nearest_future_row(rows, i, target_seconds, tolerance_seconds)
        if b is None:
            continue

        deltas: Dict[str, float] = {}
        for c in CURRENCIES:
            if c in a.forces and c in b.forces:
                deltas[c] = b.forces[c] - a.forces[c]

        if not deltas:
            continue

        up_deltas = {c: round(v, 4) for c, v in sorted(deltas.items(), key=lambda kv: kv[1], reverse=True) if v >= min_delta}
        down_deltas = {c: round(v, 4) for c, v in sorted(deltas.items(), key=lambda kv: kv[1]) if v <= -min_delta}

        up_block = list(up_deltas.keys())
        down_block = list(down_deltas.keys())
        energy = round(sum(abs(v) for v in deltas.values()), 4)

        bid_delta: Optional[float] = None
        if a.bid is not None and b.bid is not None:
            bid_delta = round(b.bid - a.bid, 6)

        event_type, tags = detect_event_type(
            a.timeframe,
            energy,
            up_block,
            down_block,
            bid_delta,
            min_energy_birth,
            min_energy_confirm,
            price_lag_abs,
            price_pay_abs,
        )

        # keep useful events only
        if event_type == "RAW_SEQUENCE_MOVE" and energy < min_energy_confirm:
            continue
        if not up_block and not down_block:
            continue

        score = score_event(energy, up_block, down_block, bid_delta, price_lag_abs)
        sentence = make_sentence(event_type, a.timeframe, up_block, down_block, bid_delta, score)

        note = (
            f"Window {a.created_at} -> {b.created_at}; "
            f"energy={energy:.1f}; bid {fmt_price(a.bid)} -> {fmt_price(b.bid)} "
            f"({fmt_signed(bid_delta)})."
        )

        events.append(
            SequenceEvent(
                start_time=a.created_at,
                end_time=b.created_at,
                timeframe=a.timeframe,
                event_type=event_type,
                score=score,
                energy=energy,
                bid_start=a.bid,
                bid_end=b.bid,
                bid_delta=bid_delta,
                up_block=up_block,
                down_block=down_block,
                up_deltas=up_deltas,
                down_deltas=down_deltas,
                tags=tags,
                cockpit_sentence=sentence,
                note=note,
            )
        )

    # Deduplicate close windows with same type/blocks by keeping strongest score.
    # V0 simple: sort by score/energy and return all; caller limits.
    events.sort(key=lambda e: (e.score, e.energy), reverse=True)
    return events


def scan_sequence(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    timeframes: Sequence[int] = (1, 5, 15),
    min_delta: float = 8.0,
    price_lag_abs: float = 0.00020,
    price_pay_abs: float = 0.00045,
) -> Dict:
    tf_windows = {
        1: 3,
        5: 10,
        15: 15,
        30: 30,
        60: 60,
    }

    min_energy_birth = 85.0
    min_energy_confirm = 32.0

    per_tf = []
    all_events: List[SequenceEvent] = []

    for tf in timeframes:
        rows = load_force_rows(db_path, symbol, tf, start, end)
        window = tf_windows.get(tf, max(3, tf))
        events = scan_timeframe(
            rows=rows,
            window_minutes=window,
            min_delta=min_delta,
            min_energy_birth=min_energy_birth,
            min_energy_confirm=min_energy_confirm,
            price_lag_abs=price_lag_abs,
            price_pay_abs=price_pay_abs,
        )
        all_events.extend(events)
        per_tf.append(
            {
                "timeframe": tf,
                "rows": len(rows),
                "first": rows[0].created_at if rows else None,
                "last": rows[-1].created_at if rows else None,
                "events": [e.to_dict() for e in events],
            }
        )

    # Cockpit priority:
    priority_order = {
        "NODE_BIRTH_FAST": 5,
        "NODE_CONFIRMATION_LEG": 4,
        "COUNTER_FORCE_BREATH_OR_RAW_NODE": 3,
        "HIGH_ENERGY_ROTATION": 2,
        "RAW_SEQUENCE_MOVE": 1,
    }
    all_events.sort(key=lambda e: (priority_order.get(e.event_type, 0), e.score, e.energy), reverse=True)

    global_sentence = "No sequence event detected."
    if all_events:
        global_sentence = all_events[0].cockpit_sentence

    return {
        "module": "pf_sequence_reader",
        "version": "V0.1",
        "db": db_path,
        "symbol": symbol,
        "start": start,
        "end": end,
        "timeframes": list(timeframes),
        "global_sentence": global_sentence,
        "event_count": len(all_events),
        "top_events": [e.to_dict() for e in all_events[:20]],
        "per_timeframe": per_tf,
    }
