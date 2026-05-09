# pf_replay_engine.py
from __future__ import annotations

import dataclasses
import datetime as dt
import json
import math
import os
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

UTC = dt.timezone.utc

DEFAULT_TABLE = "force_snapshots"
DEFAULT_TIMESTAMP_COLUMNS: tuple[str, ...] = (
    "created_at",
    "timestamp",
    "ts",
    "datetime",
    "time",
    "bar_time",
    "snapshot_time",
)
DEFAULT_SYMBOL_COLUMNS: tuple[str, ...] = (
    "symbol",
    "pair",
    "instrument",
)
DEFAULT_TIMEFRAME_COLUMN = "timeframe"


class ReplayEngineError(RuntimeError):
    pass


@dataclasses.dataclass(frozen=True)
class ReplayWindow:
    date: str
    start: str
    end: str
    start_utc: str
    end_utc: str
    inclusive_end: bool = True

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ReplayRow:
    timestamp: str
    minute: str
    timeframe: int | None
    symbol: str | None
    values: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ReplayFrame:
    minute: str
    rows_count: int
    timeframes: dict[str, list[dict[str, Any]]]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class ReplayReport:
    module: str
    version: str
    generated_at: str
    db_path: str
    table: str
    symbol: str
    window: dict[str, Any]
    timestamp_column: str
    symbol_column: str | None
    timeframe_column: str | None
    columns: list[str]
    frames_count: int
    rows_count: int
    timeframes_found: list[int]
    technical_risks: list[str]
    frames: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return dataclasses.asdict(self)


def connect_readonly(db_path: str | os.PathLike[str]) -> sqlite3.Connection:
    db_path_str = str(db_path)
    conn = sqlite3.connect(f"file:{db_path_str}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def quote_identifier(identifier: str) -> str:
    if "\x00" in identifier:
        raise ValueError("Invalid SQLite identifier")
    return '"' + identifier.replace('"', '""') + '"'


def parse_timestamp(value: Any) -> dt.datetime | None:
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
        except (OSError, OverflowError, ValueError):
            return None
    else:
        text = str(value).strip()
        if not text:
            return None

        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        parsed = None
        try:
            parsed = dt.datetime.fromisoformat(text)
        except ValueError:
            pass

        if parsed is None:
            for fmt in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y.%m.%d %H:%M:%S",
            ):
                try:
                    parsed = dt.datetime.strptime(text, fmt)
                    break
                except ValueError:
                    continue

        if parsed is None:
            return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)

    return parsed.astimezone(UTC)


def isoformat_utc(value: dt.datetime) -> str:
    return value.astimezone(UTC).replace(microsecond=0).isoformat()


def floor_to_minute(value: dt.datetime) -> dt.datetime:
    value_utc = value.astimezone(UTC)
    return value_utc.replace(second=0, microsecond=0)


def parse_replay_bounds(date_value: str, start: str, end: str) -> tuple[dt.datetime, dt.datetime]:
    try:
        base_date = dt.date.fromisoformat(date_value)
    except ValueError as exc:
        raise ReplayEngineError(f"Invalid --date value {date_value!r}; expected YYYY-MM-DD") from exc

    try:
        start_time = dt.time.fromisoformat(start)
    except ValueError as exc:
        raise ReplayEngineError(f"Invalid --start value {start!r}; expected HH:MM or HH:MM:SS") from exc

    try:
        end_time = dt.time.fromisoformat(end)
    except ValueError as exc:
        raise ReplayEngineError(f"Invalid --end value {end!r}; expected HH:MM or HH:MM:SS") from exc

    start_dt = dt.datetime.combine(base_date, start_time, tzinfo=UTC)
    end_dt = dt.datetime.combine(base_date, end_time, tzinfo=UTC)

    if end_dt < start_dt:
        end_dt += dt.timedelta(days=1)

    return start_dt, end_dt


def minute_range(start_dt: dt.datetime, end_dt: dt.datetime) -> list[dt.datetime]:
    current = floor_to_minute(start_dt)
    last = floor_to_minute(end_dt)
    minutes: list[dt.datetime] = []

    while current <= last:
        minutes.append(current)
        current += dt.timedelta(minutes=1)

    return minutes


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def get_columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f"PRAGMA table_info({quote_identifier(table)})").fetchall()
    return [str(row["name"]) for row in rows]


def detect_timestamp_column(
    conn: sqlite3.Connection,
    table: str,
    candidates: Sequence[str] = DEFAULT_TIMESTAMP_COLUMNS,
) -> str:
    columns = get_columns(conn, table)
    lower_to_real = {column.lower(): column for column in columns}

    for candidate in candidates:
        found = lower_to_real.get(candidate.lower())
        if found:
            return found

    timestamp_like = [
        column
        for column in columns
        if "time" in column.lower()
        or "date" in column.lower()
        or column.lower() == "ts"
    ]
    if timestamp_like:
        return timestamp_like[0]

    raise ReplayEngineError(
        f"No timestamp-like column found in {table!r}. Columns: {columns}"
    )


def detect_symbol_column(
    conn: sqlite3.Connection,
    table: str,
    candidates: Sequence[str] = DEFAULT_SYMBOL_COLUMNS,
) -> str | None:
    columns = get_columns(conn, table)
    lower_to_real = {column.lower(): column for column in columns}

    for candidate in candidates:
        found = lower_to_real.get(candidate.lower())
        if found:
            return found

    return None


def detect_timeframe_column(conn: sqlite3.Connection, table: str) -> str | None:
    columns = get_columns(conn, table)
    lower_to_real = {column.lower(): column for column in columns}
    return lower_to_real.get(DEFAULT_TIMEFRAME_COLUMN)


def json_safe(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value

    if isinstance(value, float):
        if math.isfinite(value):
            return value
        return None

    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")

    if isinstance(value, dt.datetime):
        return isoformat_utc(value)

    if isinstance(value, dt.date):
        return value.isoformat()

    text = str(value)
    numeric = _parse_numeric_if_clean(text)
    if numeric is not None:
        return numeric
    return text


def _parse_numeric_if_clean(text: str) -> int | float | None:
    stripped = text.strip()
    if not stripped:
        return None

    try:
        if stripped.isdigit() or (stripped.startswith("-") and stripped[1:].isdigit()):
            return int(stripped)
        if any(char in stripped for char in (".", "e", "E")):
            value = float(stripped)
            if math.isfinite(value):
                return value
    except ValueError:
        return None

    return None


def normalize_row(
    row: sqlite3.Row,
    timestamp_column: str,
    symbol_column: str | None,
    timeframe_column: str | None,
) -> ReplayRow | None:
    raw_timestamp = row[timestamp_column]
    parsed_timestamp = parse_timestamp(raw_timestamp)
    if parsed_timestamp is None:
        return None

    timeframe: int | None = None
    if timeframe_column is not None:
        raw_tf = row[timeframe_column]
        try:
            timeframe = int(raw_tf)
        except (TypeError, ValueError):
            timeframe = None

    symbol: str | None = None
    if symbol_column is not None:
        raw_symbol = row[symbol_column]
        symbol = None if raw_symbol is None else str(raw_symbol)

    values = {key: json_safe(row[key]) for key in row.keys()}

    return ReplayRow(
        timestamp=isoformat_utc(parsed_timestamp),
        minute=isoformat_utc(floor_to_minute(parsed_timestamp)),
        timeframe=timeframe,
        symbol=symbol,
        values=values,
    )


def fetch_snapshot_rows(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    start_dt: dt.datetime,
    end_dt: dt.datetime,
    timestamp_column: str,
    symbol_column: str | None,
) -> list[sqlite3.Row]:
    where = [
        f"{quote_identifier(timestamp_column)} >= ?",
        f"{quote_identifier(timestamp_column)} <= ?",
    ]
    params: list[Any] = [
        start_dt.replace(tzinfo=None).isoformat(sep=" "),
        end_dt.replace(tzinfo=None).isoformat(sep=" "),
    ]

    if symbol_column is not None:
        where.append(f"{quote_identifier(symbol_column)} = ?")
        params.append(symbol)

    sql = (
        f"SELECT * FROM {quote_identifier(table)} "
        f"WHERE {' AND '.join(where)} "
        f"ORDER BY {quote_identifier(timestamp_column)} ASC"
    )

    return list(conn.execute(sql, params).fetchall())


def build_frames(
    rows: Sequence[ReplayRow],
    start_dt: dt.datetime,
    end_dt: dt.datetime,
) -> list[ReplayFrame]:
    grouped: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))

    for row in rows:
        tf_key = str(row.timeframe) if row.timeframe is not None else "unknown"
        grouped[row.minute][tf_key].append(row.to_dict())

    frames: list[ReplayFrame] = []
    for minute in minute_range(start_dt, end_dt):
        minute_key = isoformat_utc(minute)
        tf_payload = {
            timeframe: sorted(items, key=lambda item: item["timestamp"])
            for timeframe, items in sorted(
                grouped.get(minute_key, {}).items(),
                key=lambda item: _timeframe_sort_key(item[0]),
            )
        }
        rows_count = sum(len(items) for items in tf_payload.values())
        frames.append(
            ReplayFrame(
                minute=minute_key,
                rows_count=rows_count,
                timeframes=tf_payload,
            )
        )

    return frames


def _timeframe_sort_key(value: str) -> tuple[int, str]:
    try:
        return (0, f"{int(value):010d}")
    except ValueError:
        return (1, value)


def replay_window(
    db_path: str | os.PathLike[str],
    symbol: str,
    date: str,
    start: str,
    end: str,
    table: str = DEFAULT_TABLE,
) -> dict[str, Any]:
    symbol_clean = symbol.strip()
    if not symbol_clean:
        raise ReplayEngineError("symbol cannot be empty")

    start_dt, end_dt = parse_replay_bounds(date, start, end)

    with connect_readonly(db_path) as conn:
        if not table_exists(conn, table):
            raise ReplayEngineError(f"Missing table {table!r}")

        columns = get_columns(conn, table)
        timestamp_column = detect_timestamp_column(conn, table)
        symbol_column = detect_symbol_column(conn, table)
        timeframe_column = detect_timeframe_column(conn, table)

        raw_rows = fetch_snapshot_rows(
            conn=conn,
            table=table,
            symbol=symbol_clean,
            start_dt=start_dt,
            end_dt=end_dt,
            timestamp_column=timestamp_column,
            symbol_column=symbol_column,
        )

        normalized_rows = [
            replay_row
            for replay_row in (
                normalize_row(
                    row=row,
                    timestamp_column=timestamp_column,
                    symbol_column=symbol_column,
                    timeframe_column=timeframe_column,
                )
                for row in raw_rows
            )
            if replay_row is not None
        ]

    frames = build_frames(
        rows=normalized_rows,
        start_dt=start_dt,
        end_dt=end_dt,
    )

    timeframes_found = sorted(
        {
            row.timeframe
            for row in normalized_rows
            if row.timeframe is not None
        }
    )

    technical_risks: list[str] = []
    if symbol_column is None:
        technical_risks.append("SYMBOL_COLUMN_MISSING_REPLAY_UNFILTERED")
    if timeframe_column is None:
        technical_risks.append("TIMEFRAME_COLUMN_MISSING")
    if not normalized_rows:
        technical_risks.append("NO_REPLAY_ROWS")
    if any(frame.rows_count == 0 for frame in frames):
        technical_risks.append("EMPTY_REPLAY_FRAMES")

    window = ReplayWindow(
        date=date,
        start=start,
        end=end,
        start_utc=isoformat_utc(start_dt),
        end_utc=isoformat_utc(end_dt),
        inclusive_end=True,
    )

    report = ReplayReport(
        module="pf_replay_engine",
        version="7.1.0",
        generated_at=isoformat_utc(dt.datetime.now(tz=UTC)),
        db_path=str(db_path),
        table=table,
        symbol=symbol_clean,
        window=window.to_dict(),
        timestamp_column=timestamp_column,
        symbol_column=symbol_column,
        timeframe_column=timeframe_column,
        columns=columns,
        frames_count=len(frames),
        rows_count=len(normalized_rows),
        timeframes_found=timeframes_found,
        technical_risks=technical_risks,
        frames=[frame.to_dict() for frame in frames],
    )

    return report.to_dict()


def dumps_replay(report: Mapping[str, Any], pretty: bool = False) -> str:
    return json.dumps(
        report,
        ensure_ascii=False,
        indent=2 if pretty else None,
        sort_keys=pretty,
    )


def write_replay_json(
    report: Mapping[str, Any],
    output_path: str | os.PathLike[str],
    pretty: bool = False,
) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dumps_replay(report, pretty=pretty) + "\n", encoding="utf-8")


__all__ = [
    "ReplayEngineError",
    "ReplayFrame",
    "ReplayReport",
    "ReplayRow",
    "ReplayWindow",
    "connect_readonly",
    "dumps_replay",
    "replay_window",
    "write_replay_json",
]