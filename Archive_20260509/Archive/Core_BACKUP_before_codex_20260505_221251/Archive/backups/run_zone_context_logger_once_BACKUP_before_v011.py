"""
PowerFlow V6 - run_zone_context_logger_once.py
Version: V0.1

Mission:
    Read force_snapshots from powerflow.db, compute rolling behavioral Z-series
    versus USD, run pf_zone_dynamics, and persist the latest diagnosis for each
    timeframe/currency into zone_diagnostics.

Usage:
    python run_zone_context_logger_once.py --db powerflow.db
    python run_zone_context_logger_once.py --db powerflow.db --replace
    python run_zone_context_logger_once.py --db powerflow.db --timeframes 1,5,15,30,60

This script is intentionally read-light/write-small:
    - it reads force_snapshots
    - it writes only zone_diagnostics
    - it does not mutate force data
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from datetime import datetime
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from pf_zone_dynamics import analyze_zone_dynamics, get_zone_profile
from pf_zone_context_logger import ensure_zone_diagnostics_table, log_zone_diagnosis, print_summary


CURRENCIES = ["GBP", "EUR", "JPY", "CAD", "CHF", "AUD"]
ALL_RANK_CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]
FORCE_COLS = {c: f"force_{c.lower()}" for c in ALL_RANK_CURRENCIES}


def rolling_z(values: Sequence[Optional[float]], lookback: int) -> List[Optional[float]]:
    """Rolling z-score with clipping to [-3, +3]."""
    out: List[Optional[float]] = []
    for i, value in enumerate(values):
        if value is None:
            out.append(None)
            continue
        start = max(0, i - lookback + 1)
        window = [x for x in values[start : i + 1] if x is not None]
        if len(window) < 5:
            out.append(None)
            continue
        mean = sum(window) / len(window)
        var = sum((x - mean) ** 2 for x in window) / len(window)
        sd = math.sqrt(var)
        if sd <= 1e-9:
            out.append(0.0)
        else:
            z = (value - mean) / sd
            out.append(max(-3.0, min(3.0, z)))
    return out


def parse_timeframes(value: Optional[str]) -> Optional[List[int]]:
    if not value:
        return None
    out: List[int] = []
    for part in value.split(","):
        part = part.strip()
        if not part:
            continue
        out.append(int(part))
    return out


def infer_session_phase(source_created_at: Optional[str]) -> Optional[str]:
    """Very light UTC session tag. Caller can override later if needed."""
    if not source_created_at:
        return None
    try:
        dt = datetime.fromisoformat(source_created_at.replace("Z", "+00:00"))
    except ValueError:
        return None
    hour = dt.hour
    if 0 <= hour < 7:
        return "ASIA"
    if 7 <= hour < 11:
        return "LONDON_OPEN"
    if 11 <= hour < 13:
        return "LONDON"
    if 13 <= hour < 15:
        return "PRE_US"
    if 15 <= hour < 21:
        return "US"
    return "LATE_US"


def get_force_value(row: sqlite3.Row, currency: str) -> Optional[float]:
    value = row[FORCE_COLS[currency]]
    if value is None:
        return None
    return float(value)


def rank_for_row(row: sqlite3.Row, currency: str) -> Tuple[Optional[int], Optional[int]]:
    values: List[Tuple[str, float]] = []
    for cur in ALL_RANK_CURRENCIES:
        value = get_force_value(row, cur)
        if value is not None:
            values.append((cur, value))
    if not values:
        return None, None
    values.sort(key=lambda item: item[1], reverse=True)
    for idx, (cur, _) in enumerate(values, start=1):
        if cur == currency:
            return idx, len(values)
    return None, len(values)


def rank_duration_bars(rows: Sequence[sqlite3.Row], currency: str) -> Tuple[Optional[int], Optional[int], int]:
    """Consecutive latest bars where the currency stayed at the same rank."""
    if not rows:
        return None, None, 0
    current_rank, rank_total = rank_for_row(rows[-1], currency)
    if current_rank is None:
        return None, rank_total, 0
    duration = 0
    for row in reversed(rows):
        rank, total = rank_for_row(row, currency)
        if rank != current_rank or total != rank_total:
            break
        duration += 1
    return current_rank, rank_total, duration


def fetch_timeframes(conn: sqlite3.Connection, selected: Optional[List[int]]) -> List[int]:
    rows = conn.execute("SELECT DISTINCT timeframe FROM force_snapshots ORDER BY timeframe").fetchall()
    available = [int(row[0]) for row in rows]
    if selected is None:
        return available
    wanted = set(selected)
    return [tf for tf in available if tf in wanted]


def analyze_latest_for_timeframe(
    conn: sqlite3.Connection,
    *,
    timeframe: int,
    symbol: Optional[str],
    currencies: Sequence[str],
    duplicate_policy: str,
) -> List[int]:
    sql = "SELECT * FROM force_snapshots WHERE timeframe = ?"
    params: List[object] = [timeframe]
    if symbol:
        sql += " AND symbol = ?"
        params.append(symbol)
    sql += " ORDER BY created_at"

    rows = conn.execute(sql, params).fetchall()
    if len(rows) < 5:
        return []

    latest = rows[-1]
    source_created_at = latest["created_at"]
    source_snapshot_id = int(latest["id"])
    latest_symbol = latest["symbol"]
    session_phase = infer_session_phase(source_created_at)

    inserted: List[int] = []
    for currency in currencies:
        prof = get_zone_profile(timeframe=timeframe, currency=currency)
        spreads: List[Optional[float]] = []
        for row in rows:
            cur_force = row[FORCE_COLS[currency]]
            usd_force = row["force_usd"]
            if cur_force is None or usd_force is None:
                spreads.append(None)
            else:
                spreads.append(float(cur_force) - float(usd_force))

        z_series = rolling_z(spreads, prof.lookback)
        recent_z = z_series[-prof.lookback :]
        valid_recent = [z for z in recent_z if z is not None]
        if len(valid_recent) < 5:
            continue

        rank_position, rank_total, rank_duration = rank_duration_bars(rows, currency)
        diag = analyze_zone_dynamics(
            recent_z,
            timeframe=timeframe,
            currency=currency,
            session_phase=session_phase,
            rank_position=rank_position,
            rank_total=rank_total,
            rank_duration_bars=rank_duration,
        )

        row_id = log_zone_diagnosis(
            conn,
            diagnosis=diag,
            symbol=latest_symbol,
            timeframe=timeframe,
            currency=currency,
            source_created_at=source_created_at,
            source_snapshot_id=source_snapshot_id,
            session_phase=session_phase,
            rank_position=rank_position,
            rank_total=rank_total,
            rank_duration_bars=rank_duration,
            duplicate_policy=duplicate_policy,
        )
        inserted.append(row_id)
    return inserted


def main() -> int:
    parser = argparse.ArgumentParser(description="Log latest PowerFlow zone diagnostics into SQLite.")
    parser.add_argument("--db", default="powerflow.db", help="Path to powerflow.db")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter, e.g. GBPUSD")
    parser.add_argument("--timeframes", default=None, help="Comma-separated TF list, e.g. 1,5,15,30,60")
    parser.add_argument("--currencies", default=",".join(CURRENCIES), help="Comma-separated currencies")
    parser.add_argument("--replace", action="store_true", help="Replace existing rows for same snapshot/currency/profile")
    parser.add_argument("--summary", action="store_true", help="Print summary after logging")
    args = parser.parse_args()

    currencies = [c.strip().upper() for c in args.currencies.split(",") if c.strip()]
    selected_tfs = parse_timeframes(args.timeframes)
    duplicate_policy = "replace" if args.replace else "ignore"

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row
    ensure_zone_diagnostics_table(conn)

    try:
        timeframes = fetch_timeframes(conn, selected_tfs)
        all_ids: List[int] = []
        for tf in timeframes:
            ids = analyze_latest_for_timeframe(
                conn,
                timeframe=tf,
                symbol=args.symbol,
                currencies=currencies,
                duplicate_policy=duplicate_policy,
            )
            all_ids.extend(ids)
        conn.commit()
    finally:
        conn.close()

    print(f"OK logged/kept {len(all_ids)} zone diagnostics into {args.db}")
    if args.summary:
        print_summary(args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
