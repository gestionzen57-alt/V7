"""
PowerFlow V6 - run_zone_context_logger_history.py
Version: V0.1

Mission:
    Backfill zone_diagnostics from force_snapshots history.

Doctrine:
    - Reads force_snapshots.
    - Writes only zone_diagnostics.
    - Does not mutate force data.
    - Does not decide; it stores the perception produced by pf_zone_dynamics.

Usage Windows PowerShell:
    python run_zone_context_logger_history.py --db powerflow.db --symbol GBPUSD --timeframes 1,5,15,30,60 --limit 50 --replace --summary

Meaning:
    --limit 50 = last 50 source snapshots per timeframe.
"""

from __future__ import annotations

import argparse
import math
import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Sequence, Tuple

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
        if part:
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


def rank_duration_bars(rows: Sequence[sqlite3.Row], currency: str, end_index: int) -> Tuple[Optional[int], Optional[int], int]:
    """Consecutive bars up to end_index where the currency stayed at the same rank."""
    if not rows or end_index < 0:
        return None, None, 0
    current_rank, rank_total = rank_for_row(rows[end_index], currency)
    if current_rank is None:
        return None, rank_total, 0
    duration = 0
    for j in range(end_index, -1, -1):
        rank, total = rank_for_row(rows[j], currency)
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


def fetch_rows_for_timeframe(
    conn: sqlite3.Connection,
    *,
    timeframe: int,
    symbol: Optional[str],
) -> List[sqlite3.Row]:
    sql = "SELECT * FROM force_snapshots WHERE timeframe = ?"
    params: List[object] = [timeframe]
    if symbol:
        sql += " AND symbol = ?"
        params.append(symbol)
    sql += " ORDER BY created_at"
    return conn.execute(sql, params).fetchall()


def source_indexes_for_history(
    rows: Sequence[sqlite3.Row],
    *,
    limit: int,
    since: Optional[str],
) -> List[int]:
    indexes = list(range(len(rows)))
    if since:
        indexes = [i for i in indexes if str(rows[i]["created_at"]) >= since]
    if limit > 0:
        indexes = indexes[-limit:]
    return indexes


def build_z_cache(
    rows: Sequence[sqlite3.Row],
    *,
    timeframe: int,
    currencies: Sequence[str],
) -> Dict[str, List[Optional[float]]]:
    cache: Dict[str, List[Optional[float]]] = {}
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
        cache[currency] = rolling_z(spreads, prof.lookback)
    return cache


def analyze_history_for_timeframe(
    conn: sqlite3.Connection,
    *,
    timeframe: int,
    symbol: Optional[str],
    currencies: Sequence[str],
    limit: int,
    since: Optional[str],
    duplicate_policy: str,
) -> List[int]:
    rows = fetch_rows_for_timeframe(conn, timeframe=timeframe, symbol=symbol)
    if len(rows) < 5:
        return []

    source_indexes = source_indexes_for_history(rows, limit=limit, since=since)
    if not source_indexes:
        return []

    z_cache = build_z_cache(rows, timeframe=timeframe, currencies=currencies)
    inserted: List[int] = []

    for source_index in source_indexes:
        source_row = rows[source_index]
        source_created_at = source_row["created_at"]
        source_snapshot_id = int(source_row["id"])
        latest_symbol = source_row["symbol"]
        session_phase = infer_session_phase(source_created_at)

        for currency in currencies:
            prof = get_zone_profile(timeframe=timeframe, currency=currency)
            z_series = z_cache[currency]
            start = max(0, source_index - prof.lookback + 1)
            recent_z = z_series[start : source_index + 1]
            valid_recent = [z for z in recent_z if z is not None]
            if len(valid_recent) < 5:
                continue

            rank_position, rank_total, rank_duration = rank_duration_bars(rows, currency, source_index)
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


def print_history_run_report(conn: sqlite3.Connection, all_ids: Sequence[int], db_path: str) -> None:
    print(f"OK logged/kept {len(all_ids)} historical zone diagnostics into {db_path}")
    stats = conn.execute(
        """
        SELECT COUNT(*) AS n,
               COUNT(DISTINCT source_created_at) AS timestamps,
               COUNT(DISTINCT timeframe) AS timeframes,
               COUNT(DISTINCT currency) AS currencies
        FROM zone_diagnostics;
        """
    ).fetchone()
    print(
        "History memory: "
        f"rows={stats['n']} timestamps={stats['timestamps']} "
        f"timeframes={stats['timeframes']} currencies={stats['currencies']}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill PowerFlow zone diagnostics history into SQLite.")
    parser.add_argument("--db", default="powerflow.db", help="Path to powerflow.db")
    parser.add_argument("--symbol", default=None, help="Optional symbol filter, e.g. GBPUSD")
    parser.add_argument("--timeframes", default=None, help="Comma-separated TF list, e.g. 1,5,15,30,60")
    parser.add_argument("--currencies", default=",".join(CURRENCIES), help="Comma-separated currencies")
    parser.add_argument("--limit", type=int, default=50, help="Last N source snapshots per timeframe. Use 0 for all.")
    parser.add_argument("--since", default=None, help="Optional ISO timestamp lower bound, e.g. 2026-05-01T12:00:00+00:00")
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
            ids = analyze_history_for_timeframe(
                conn,
                timeframe=tf,
                symbol=args.symbol,
                currencies=currencies,
                limit=args.limit,
                since=args.since,
                duplicate_policy=duplicate_policy,
            )
            all_ids.extend(ids)
        conn.commit()
        print_history_run_report(conn, all_ids, args.db)
    finally:
        conn.close()

    if args.summary:
        print_summary(args.db)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
