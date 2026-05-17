# -*- coding: utf-8 -*-
"""
PowerFlow T009 / B9 raw calibration helpers.

V3.6 adds read-only deduplicated raw tick reads for MT5 historical raw data.
The raw database keeps the full broker feed unchanged. B9 calibration computes
its texture metrics on a DISTINCT read over:

    ts_utc, bid, ask, mid, spread

Doctrine:
    La DB garde la verite brute. B9 calibre sur une lecture dedupliquee.

This module does not write to powerflow.db or tick_archive.db. It is intended to
be used by validation scripts and offline calibration reports.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

RAW_DEDUP_MODE = "DISTINCT_TS_BID_ASK_MID_SPREAD"
SOURCE_MODE_HISTORICAL_RAW = "HISTORICAL_RAW"
DATA_VISIBILITY_RAW_ALIGNED = "MT5_RAW_ALIGNED"
DEFAULT_BROKER_RELATIVE_NOTE = (
    "Lecture raw MT5 broker-relative : texture locale vérifiée, "
    "pas footprint global centralisé."
)

TickRow = Dict[str, Any]


@dataclass(frozen=True)
class RawCalibrationMetrics:
    """Deduplicated raw calibration metrics for one time window."""

    source_mode: str
    data_visibility: str
    raw_dedup_mode: str
    raw_tick_count_raw: int
    raw_tick_count_dedup: int
    raw_duplicate_count: int
    raw_duplicate_ratio: float
    raw_delta_pips: float
    raw_range_pips: float
    raw_density_ticks_per_minute: float
    raw_avg_gap_seconds: Optional[float]
    raw_max_gap_seconds: Optional[float]
    raw_gap_count_gt_5s: int
    raw_gap_count_gt_30s: int
    first_ts_utc: Optional[str]
    last_ts_utc: Optional[str]
    first_mid: Optional[float]
    last_mid: Optional[float]
    min_mid: Optional[float]
    max_mid: Optional[float]
    broker_relative: bool
    broker_note_fr: str
    limitations: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    """Open a SQLite database in read-only URI mode."""

    path = Path(db_path)
    uri = f"file:{path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _parse_dt(value: Any) -> datetime:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value).strip()
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        # SQLite / MT5 exports sometimes use a space instead of T.
        text = text.replace(" ", "T") if " " in text and "T" not in text else text
        dt = datetime.fromisoformat(text)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _fmt_dt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def deduplicate_tick_rows(rows: Iterable[Mapping[str, Any]]) -> List[TickRow]:
    """Return rows deduplicated by (ts_utc, bid, ask, mid, spread), sorted by time.

    The first occurrence is retained for any exact duplicate. The DB is not
    mutated; this is a pure in-memory read model mirroring SQL DISTINCT.
    """

    seen: set[Tuple[Any, Any, Any, Any, Any]] = set()
    deduped: List[TickRow] = []
    for row in rows:
        ts = row.get("ts_utc") or row.get("timestamp") or row.get("time")
        bid = _as_float(row.get("bid"))
        ask = _as_float(row.get("ask"))
        mid = _as_float(row.get("mid"))
        spread = _as_float(row.get("spread"))
        if mid is None and bid is not None and ask is not None:
            mid = (bid + ask) / 2.0
        if spread is None and bid is not None and ask is not None:
            spread = ask - bid
        key = (str(ts), bid, ask, mid, spread)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            {
                "ts_utc": str(ts),
                "bid": bid,
                "ask": ask,
                "mid": mid,
                "spread": spread,
            }
        )
    deduped.sort(key=lambda r: _parse_dt(r["ts_utc"]))
    return deduped


def compute_raw_calibration_metrics(
    rows: Sequence[Mapping[str, Any]],
    *,
    pip_size: float = 0.0001,
    broker_note_fr: str = DEFAULT_BROKER_RELATIVE_NOTE,
) -> Dict[str, Any]:
    """Compute raw metrics using deduplicated tick rows.

    raw_delta_pips, raw_range_pips, dwell/density proxies and gap metrics are all
    computed on the deduplicated view. The raw and dedup counts are exposed so
    the caller can see how much duplicate pressure existed in the source.
    """

    raw_count = len(rows)
    deduped = deduplicate_tick_rows(rows)
    dedup_count = len(deduped)
    duplicate_count = max(0, raw_count - dedup_count)
    duplicate_ratio = (duplicate_count / raw_count) if raw_count else 0.0

    if dedup_count == 0:
        metrics = RawCalibrationMetrics(
            source_mode=SOURCE_MODE_HISTORICAL_RAW,
            data_visibility=DATA_VISIBILITY_RAW_ALIGNED,
            raw_dedup_mode=RAW_DEDUP_MODE,
            raw_tick_count_raw=raw_count,
            raw_tick_count_dedup=0,
            raw_duplicate_count=duplicate_count,
            raw_duplicate_ratio=round(duplicate_ratio, 6),
            raw_delta_pips=0.0,
            raw_range_pips=0.0,
            raw_density_ticks_per_minute=0.0,
            raw_avg_gap_seconds=None,
            raw_max_gap_seconds=None,
            raw_gap_count_gt_5s=0,
            raw_gap_count_gt_30s=0,
            first_ts_utc=None,
            last_ts_utc=None,
            first_mid=None,
            last_mid=None,
            min_mid=None,
            max_mid=None,
            broker_relative=True,
            broker_note_fr=broker_note_fr,
            limitations=[
                "RAW_UNAVAILABLE_OR_EMPTY_WINDOW",
                "BROKER_RELATIVE",
                "NO_FOOTPRINT_EXACT_CLAIM",
            ],
        )
        return metrics.to_dict()

    dts = [_parse_dt(r["ts_utc"]) for r in deduped]
    mids = [float(r["mid"]) for r in deduped if r.get("mid") is not None]
    if not mids:
        raise ValueError("Cannot compute raw calibration metrics without mid values")

    first_mid = float(deduped[0]["mid"])
    last_mid = float(deduped[-1]["mid"])
    min_mid = min(mids)
    max_mid = max(mids)
    raw_delta_pips = (last_mid - first_mid) / pip_size
    raw_range_pips = (max_mid - min_mid) / pip_size

    gaps: List[float] = []
    for left, right in zip(dts, dts[1:]):
        gaps.append(max(0.0, (right - left).total_seconds()))

    total_seconds = max(0.0, (dts[-1] - dts[0]).total_seconds())
    density = (dedup_count / (total_seconds / 60.0)) if total_seconds > 0 else float(dedup_count)

    limitations = ["BROKER_RELATIVE", "NO_FOOTPRINT_EXACT_CLAIM"]
    if duplicate_count > 0:
        limitations.append("RAW_DUPLICATES_DEDUPED_FOR_CALIBRATION")

    metrics = RawCalibrationMetrics(
        source_mode=SOURCE_MODE_HISTORICAL_RAW,
        data_visibility=DATA_VISIBILITY_RAW_ALIGNED,
        raw_dedup_mode=RAW_DEDUP_MODE,
        raw_tick_count_raw=raw_count,
        raw_tick_count_dedup=dedup_count,
        raw_duplicate_count=duplicate_count,
        raw_duplicate_ratio=round(duplicate_ratio, 6),
        raw_delta_pips=round(raw_delta_pips, 6),
        raw_range_pips=round(raw_range_pips, 6),
        raw_density_ticks_per_minute=round(density, 6),
        raw_avg_gap_seconds=round(sum(gaps) / len(gaps), 6) if gaps else None,
        raw_max_gap_seconds=round(max(gaps), 6) if gaps else None,
        raw_gap_count_gt_5s=sum(1 for g in gaps if g > 5.0),
        raw_gap_count_gt_30s=sum(1 for g in gaps if g > 30.0),
        first_ts_utc=_fmt_dt(dts[0]),
        last_ts_utc=_fmt_dt(dts[-1]),
        first_mid=first_mid,
        last_mid=last_mid,
        min_mid=min_mid,
        max_mid=max_mid,
        broker_relative=True,
        broker_note_fr=broker_note_fr,
        limitations=limitations,
    )
    return metrics.to_dict()


def _table_columns(conn: sqlite3.Connection, table_name: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return [str(row[1]) for row in rows]


def _available_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [str(row[0]) for row in rows]


def _choose_tick_table(conn: sqlite3.Connection, preferred: Optional[str] = None) -> str:
    candidates = [preferred] if preferred else []
    candidates.extend([
        "ticks",
        "raw_ticks",
        "mt5_ticks",
        "mt5_raw_ticks",
        "tick_archive",
        "tick_archive_raw",
    ])
    tables = set(_available_tables(conn))
    for table in candidates:
        if table and table in tables:
            cols = set(_table_columns(conn, table))
            if {"ts_utc", "bid", "ask"}.issubset(cols) or {"timestamp", "bid", "ask"}.issubset(cols):
                return table
    for table in tables:
        cols = set(_table_columns(conn, table))
        if {"ts_utc", "bid", "ask"}.issubset(cols) or {"timestamp", "bid", "ask"}.issubset(cols):
            return table
    raise ValueError("No raw tick table found with ts_utc/timestamp, bid and ask columns")


def read_raw_ticks(
    conn: sqlite3.Connection,
    *,
    symbol: str,
    start_utc: str,
    end_utc: str,
    table_name: Optional[str] = None,
    deduplicated: bool = True,
) -> List[TickRow]:
    """Read raw ticks in a window, optionally using SQL DISTINCT.

    The deduplicated query is:
        SELECT DISTINCT ts_utc, bid, ask, mid, spread ...

    If the table lacks mid/spread columns, they are reconstructed in memory from
    bid/ask after read. This remains read-only.
    """

    table = _choose_tick_table(conn, table_name)
    cols = _table_columns(conn, table)
    col_set = set(cols)
    ts_col = "ts_utc" if "ts_utc" in col_set else "timestamp"
    mid_expr = "mid" if "mid" in col_set else "((bid + ask) / 2.0) AS mid"
    spread_expr = "spread" if "spread" in col_set else "(ask - bid) AS spread"
    distinct = "DISTINCT " if deduplicated else ""

    where = [f"{ts_col} >= ?", f"{ts_col} <= ?"]
    params: List[Any] = [start_utc, end_utc]
    if "symbol" in col_set:
        where.insert(0, "symbol = ?")
        params.insert(0, symbol)

    sql = (
        f"SELECT {distinct}{ts_col} AS ts_utc, bid, ask, {mid_expr}, {spread_expr} "
        f"FROM {table} WHERE " + " AND ".join(where) + f" ORDER BY {ts_col} ASC"
    )
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def calibrate_raw_window(
    db_path: str | Path,
    *,
    symbol: str,
    start_utc: str,
    end_utc: str,
    table_name: Optional[str] = None,
    pip_size: float = 0.0001,
) -> Dict[str, Any]:
    """Read raw ticks read-only and return deduplicated calibration metrics."""

    with connect_readonly(db_path) as conn:
        raw_rows = read_raw_ticks(
            conn,
            symbol=symbol,
            start_utc=start_utc,
            end_utc=end_utc,
            table_name=table_name,
            deduplicated=False,
        )
        dedup_rows = read_raw_ticks(
            conn,
            symbol=symbol,
            start_utc=start_utc,
            end_utc=end_utc,
            table_name=table_name,
            deduplicated=True,
        )

    # Compute on raw_rows so raw/dedup counts are exposed from the same pipeline.
    metrics = compute_raw_calibration_metrics(raw_rows, pip_size=pip_size)
    metrics["raw_tick_count_dedup_sql"] = len(dedup_rows)
    metrics["raw_dedup_sql_matches_memory"] = metrics["raw_tick_count_dedup"] == len(dedup_rows)
    return metrics


__all__ = [
    "RAW_DEDUP_MODE",
    "SOURCE_MODE_HISTORICAL_RAW",
    "DATA_VISIBILITY_RAW_ALIGNED",
    "RawCalibrationMetrics",
    "connect_readonly",
    "deduplicate_tick_rows",
    "compute_raw_calibration_metrics",
    "read_raw_ticks",
    "calibrate_raw_window",
]
