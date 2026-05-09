# pf_data_quality_guard.py
"""
PowerFlow V7.1 - Data Quality Guard

Role:
    Scan powerflow.db in read-only mode and report temporal quality by timeframe.

Contract:
    - Strict read-only SQLite connection.
    - No cockpit_* import.
    - No DB writes.
    - JSON-serializable report.

Expected table:
    force_snapshots

Detected dynamically:
    - timestamp column
    - symbol column, optional
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime as dt
import json
import logging
import math
import os
import sqlite3
from typing import Any, Iterable, Mapping, Sequence

LOGGER = logging.getLogger(__name__)

DEFAULT_TABLE = "force_snapshots"
DEFAULT_TIMEFRAMES: tuple[int, ...] = (1, 5, 15, 30, 60, 240, 1440)
DEFAULT_TIMESTAMP_COLUMNS: tuple[str, ...] = (
    "timestamp",
    "ts",
    "datetime",
    "created_at",
    "time",
    "bar_time",
    "snapshot_time",
)

UTC = dt.timezone.utc


@dataclasses.dataclass(frozen=True)
class GapRecord:
    symbol: str | None
    timeframe: int
    previous_timestamp: str
    next_timestamp: str
    gap_seconds: float
    expected_seconds: int
    gap_multiple: float

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class TimeframeQuality:
    timeframe: int
    expected_interval_seconds: int
    rows: int
    symbols: list[str]
    first_timestamp: str | None
    last_timestamp: str | None
    last_age_seconds: float | None
    stale_threshold_seconds: float
    stale: bool | None
    gaps_count: int
    max_gap_seconds: float | None
    max_gap_multiple: float | None
    gaps_sample: list[dict[str, Any]]
    status: str
    technical_risks: list[str]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


class DataQualityGuardError(RuntimeError):
    """Raised when the DB cannot be inspected safely."""


def connect_readonly(db_path: str | os.PathLike[str]) -> sqlite3.Connection:
    """
    Open SQLite DB in strict read-only URI mode.

    Required PowerFlow contract:
        sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    """
    db_path_str = str(db_path)
    conn = sqlite3.connect(f"file:{db_path_str}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def quote_identifier(identifier: str) -> str:
    """Quote an SQLite identifier."""
    if "\x00" in identifier:
        raise ValueError("Invalid SQLite identifier")
    return '"' + identifier.replace('"', '""') + '"'


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    except sqlite3.DatabaseError as exc:
        raise DataQualityGuardError(f"Cannot inspect table {table!r}: {exc}") from exc
    return [str(row["name"]) for row in rows]


def detect_column_case_insensitive(
    conn: sqlite3.Connection,
    table: str,
    wanted: str,
) -> str | None:
    for column in _columns(conn, table):
        if column.lower() == wanted.lower():
            return column
    return None


def detect_timestamp_column(
    conn: sqlite3.Connection,
    table: str = DEFAULT_TABLE,
    candidates: Sequence[str] = DEFAULT_TIMESTAMP_COLUMNS,
) -> str:
    cols = _columns(conn, table)
    normalized = {col.lower(): col for col in cols}

    for candidate in candidates:
        found = normalized.get(candidate.lower())
        if found:
            return found

    timestamp_like = [
        col for col in cols
        if "time" in col.lower() or "date" in col.lower() or col.lower() == "ts"
    ]
    if timestamp_like:
        return timestamp_like[0]

    raise DataQualityGuardError(
        f"No timestamp-like column found in {table!r}. Available columns: {cols}"
    )


def detect_symbol_column(conn: sqlite3.Connection, table: str = DEFAULT_TABLE) -> str | None:
    cols = _columns(conn, table)
    normalized = {col.lower(): col for col in cols}
    for candidate in ("symbol", "pair", "instrument"):
        if candidate in normalized:
            return normalized[candidate]
    return None


def parse_timestamp(value: Any) -> dt.datetime | None:
    """
    Robust timestamp parser for SQLite values.

    Supports:
        - ISO strings
        - ISO strings ending with Z
        - common MT4/SQLite text formats
        - numeric Unix seconds
        - numeric Unix milliseconds
    """
    if value is None:
        return None

    if isinstance(value, dt.datetime):
        parsed = value
    elif isinstance(value, (int, float)):
        raw = float(value)
        if raw > 10_000_000_000:
            raw /= 1000.0
        try:
            parsed = dt.datetime.fromtimestamp(raw, tz=UTC)
        except (OverflowError, OSError, ValueError):
            return None
    else:
        text = str(value).strip()
        if not text:
            return None

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        parsed = None
        with contextlib.suppress(ValueError):
            parsed = dt.datetime.fromisoformat(text)

        if parsed is None:
            formats = (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y.%m.%d %H:%M:%S",
            )
            for fmt in formats:
                with contextlib.suppress(ValueError):
                    parsed = dt.datetime.strptime(text, fmt)
                    break

        if parsed is None:
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def isoformat_utc(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat()


def normalize_since(since: str | dt.datetime | dt.date) -> str:
    if isinstance(since, dt.datetime):
        return since.astimezone(UTC).isoformat()
    if isinstance(since, dt.date):
        return dt.datetime.combine(since, dt.time.min, tzinfo=UTC).isoformat()
    text = str(since).strip()
    if not text:
        raise ValueError("since cannot be empty")
    return text


def _fetch_distinct_symbols(
    conn: sqlite3.Connection,
    table: str,
    symbol_col: str | None,
    ts_col: str,
    since: str,
) -> list[str | None]:
    if symbol_col is None:
        return [None]

    sql = (
        f"SELECT DISTINCT {quote_identifier(symbol_col)} AS symbol "
        f"FROM {quote_identifier(table)} "
        f"WHERE {quote_identifier(ts_col)} >= ? "
        f"ORDER BY {quote_identifier(symbol_col)}"
    )
    rows = conn.execute(sql, (since,)).fetchall()
    values: list[str | None] = []
    for row in rows:
        symbol = row["symbol"]
        values.append(None if symbol is None else str(symbol))
    return values or [None]


def _fetch_timestamps(
    conn: sqlite3.Connection,
    table: str,
    ts_col: str,
    tf_col: str,
    tf: int,
    since: str,
    symbol_col: str | None = None,
    symbol: str | None = None,
) -> list[dt.datetime]:
    where = [
        f"{quote_identifier(tf_col)} = ?",
        f"{quote_identifier(ts_col)} >= ?",
    ]
    params: list[Any] = [tf, since]

    if symbol_col is not None and symbol is not None:
        where.append(f"{quote_identifier(symbol_col)} = ?")
        params.append(symbol)

    sql = (
        f"SELECT {quote_identifier(ts_col)} AS ts "
        f"FROM {quote_identifier(table)} "
        f"WHERE {' AND '.join(where)} "
        f"ORDER BY {quote_identifier(ts_col)} ASC"
    )

    parsed: list[dt.datetime] = []
    for row in conn.execute(sql, params).fetchall():
        ts = parse_timestamp(row["ts"])
        if ts is not None:
            parsed.append(ts)
    return parsed


def _count_rows(
    conn: sqlite3.Connection,
    table: str,
    tf_col: str,
    tf: int,
    since: str,
    ts_col: str,
) -> int:
    sql = (
        f"SELECT COUNT(*) AS n "
        f"FROM {quote_identifier(table)} "
        f"WHERE {quote_identifier(tf_col)} = ? "
        f"AND {quote_identifier(ts_col)} >= ?"
    )
    row = conn.execute(sql, (tf, since)).fetchone()
    return int(row["n"] if row else 0)


def _min_max_timestamp(
    conn: sqlite3.Connection,
    table: str,
    tf_col: str,
    tf: int,
    since: str,
    ts_col: str,
) -> tuple[dt.datetime | None, dt.datetime | None]:
    sql = (
        f"SELECT MIN({quote_identifier(ts_col)}) AS first_ts, "
        f"MAX({quote_identifier(ts_col)}) AS last_ts "
        f"FROM {quote_identifier(table)} "
        f"WHERE {quote_identifier(tf_col)} = ? "
        f"AND {quote_identifier(ts_col)} >= ?"
    )
    row = conn.execute(sql, (tf, since)).fetchone()
    if row is None:
        return None, None
    return parse_timestamp(row["first_ts"]), parse_timestamp(row["last_ts"])


def _detect_gaps(
    timestamps: Sequence[dt.datetime],
    timeframe: int,
    symbol: str | None,
    gap_tolerance: float,
) -> list[GapRecord]:
    expected_seconds = timeframe * 60
    threshold = expected_seconds * gap_tolerance
    gaps: list[GapRecord] = []

    for previous, current in zip(timestamps, timestamps[1:]):
        delta_seconds = (current - previous).total_seconds()
        if delta_seconds > threshold:
            gaps.append(
                GapRecord(
                    symbol=symbol,
                    timeframe=timeframe,
                    previous_timestamp=previous.isoformat(),
                    next_timestamp=current.isoformat(),
                    gap_seconds=round(delta_seconds, 3),
                    expected_seconds=expected_seconds,
                    gap_multiple=round(delta_seconds / expected_seconds, 3)
                    if expected_seconds > 0
                    else math.inf,
                )
            )

    return gaps


def scan_data_quality(
    db_path: str | os.PathLike[str],
    since: str | dt.datetime | dt.date,
    timeframes: Sequence[int] = DEFAULT_TIMEFRAMES,
    table: str = DEFAULT_TABLE,
    now: dt.datetime | None = None,
    stale_multiplier: float = 2.5,
    gap_tolerance: float = 1.05,
    max_gaps_sample: int = 20,
) -> dict[str, Any]:
    """Scan DB quality by timeframe."""
    if stale_multiplier <= 0:
        raise ValueError("stale_multiplier must be > 0")
    if gap_tolerance < 1.0:
        raise ValueError("gap_tolerance must be >= 1.0")
    if max_gaps_sample < 0:
        raise ValueError("max_gaps_sample must be >= 0")

    since_text = normalize_since(since)
    now_utc = (now or dt.datetime.now(tz=UTC)).astimezone(UTC)

    with connect_readonly(db_path) as conn:
        if not _table_exists(conn, table):
            raise DataQualityGuardError(f"Missing table {table!r}")

        tf_col = detect_column_case_insensitive(conn, table, "timeframe")
        if tf_col is None:
            raise DataQualityGuardError(
                f"Table {table!r} has no timeframe column. Columns: {_columns(conn, table)}"
            )

        ts_col = detect_timestamp_column(conn, table)
        symbol_col = detect_symbol_column(conn, table)
        symbols = _fetch_distinct_symbols(conn, table, symbol_col, ts_col, since_text)

        tf_reports: dict[str, Any] = {}
        global_risks: set[str] = set()

        for tf in [int(x) for x in timeframes]:
            expected_seconds = tf * 60
            rows = _count_rows(conn, table, tf_col, tf, since_text, ts_col)
            first_ts, last_ts = _min_max_timestamp(conn, table, tf_col, tf, since_text, ts_col)

            all_gaps: list[GapRecord] = []
            symbol_values: list[str] = []

            for symbol in symbols:
                timestamps = _fetch_timestamps(
                    conn=conn,
                    table=table,
                    ts_col=ts_col,
                    tf_col=tf_col,
                    tf=tf,
                    since=since_text,
                    symbol_col=symbol_col,
                    symbol=symbol,
                )
                if symbol is not None and timestamps:
                    symbol_values.append(symbol)
                all_gaps.extend(
                    _detect_gaps(
                        timestamps=timestamps,
                        timeframe=tf,
                        symbol=symbol,
                        gap_tolerance=gap_tolerance,
                    )
                )

            all_gaps.sort(key=lambda gap: gap.gap_seconds, reverse=True)

            last_age_seconds: float | None = None
            stale: bool | None = None
            stale_threshold_seconds = expected_seconds * stale_multiplier
            technical_risks: list[str] = []

            if rows <= 0:
                status = "FAIL"
                technical_risks.append("NO_ROWS")
                global_risks.add(f"TF{tf}_NO_ROWS")
            elif last_ts is None:
                status = "FAIL"
                technical_risks.append("UNPARSEABLE_LAST_TIMESTAMP")
                global_risks.add(f"TF{tf}_UNPARSEABLE_LAST_TIMESTAMP")
            else:
                last_age_seconds = max(0.0, (now_utc - last_ts).total_seconds())
                stale = last_age_seconds > stale_threshold_seconds

                if stale:
                    technical_risks.append("STALE_DATA")
                    global_risks.add(f"TF{tf}_STALE_DATA")

                if all_gaps:
                    technical_risks.append("TEMPORAL_GAPS")
                    global_risks.add(f"TF{tf}_TEMPORAL_GAPS")

                status = "PASS" if not stale and not all_gaps else "WARN"

            max_gap_seconds = all_gaps[0].gap_seconds if all_gaps else None
            max_gap_multiple = all_gaps[0].gap_multiple if all_gaps else None

            tf_quality = TimeframeQuality(
                timeframe=tf,
                expected_interval_seconds=expected_seconds,
                rows=rows,
                symbols=sorted(set(symbol_values)),
                first_timestamp=isoformat_utc(first_ts),
                last_timestamp=isoformat_utc(last_ts),
                last_age_seconds=round(last_age_seconds, 3)
                if last_age_seconds is not None
                else None,
                stale_threshold_seconds=round(stale_threshold_seconds, 3),
                stale=stale,
                gaps_count=len(all_gaps),
                max_gap_seconds=max_gap_seconds,
                max_gap_multiple=max_gap_multiple,
                gaps_sample=[gap.to_dict() for gap in all_gaps[:max_gaps_sample]],
                status=status,
                technical_risks=technical_risks,
            )
            tf_reports[str(tf)] = tf_quality.to_dict()

        if any(item["status"] == "FAIL" for item in tf_reports.values()):
            overall_status = "FAIL"
        elif any(item["status"] == "WARN" for item in tf_reports.values()):
            overall_status = "WARN"
        else:
            overall_status = "PASS"

        return {
            "module": "pf_data_quality_guard",
            "version": "7.1.0",
            "generated_at": now_utc.isoformat(),
            "db_path": str(db_path),
            "table": table,
            "since": since_text,
            "timeframes": [int(x) for x in timeframes],
            "timestamp_column": ts_col,
            "timeframe_column": tf_col,
            "symbol_column": symbol_col,
            "stale_multiplier": stale_multiplier,
            "gap_tolerance": gap_tolerance,
            "overall_status": overall_status,
            "technical_risks": sorted(global_risks),
            "timeframe_reports": tf_reports,
        }


def dumps_report(report: Mapping[str, Any], pretty: bool = False) -> str:
    return json.dumps(
        report,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def parse_timeframes(value: str | Iterable[int]) -> tuple[int, ...]:
    if isinstance(value, str):
        items = [part.strip() for part in value.split(",") if part.strip()]
        if not items:
            raise argparse.ArgumentTypeError("timeframes cannot be empty")
        try:
            parsed = tuple(int(item) for item in items)
        except ValueError as exc:
            raise argparse.ArgumentTypeError("timeframes must be comma-separated ints") from exc
    else:
        parsed = tuple(int(item) for item in value)

    if any(tf <= 0 for tf in parsed):
        raise argparse.ArgumentTypeError("timeframes must be positive integers")
    return parsed


__all__ = [
    "DataQualityGuardError",
    "DEFAULT_TABLE",
    "DEFAULT_TIMEFRAMES",
    "connect_readonly",
    "detect_symbol_column",
    "detect_timestamp_column",
    "dumps_report",
    "parse_timeframes",
    "scan_data_quality",
]
