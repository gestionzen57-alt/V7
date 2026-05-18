"""PowerFlow T010 / B9 tick archive writer.

This module owns the local SQLite archive used by B9 / T009 raw-tick
experiments. It intentionally writes to ``tick_archive.db`` only and does not
modify ``powerflow.db``.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

SOURCE_MODES = {
    "ONTICK_RAW",
    "HISTORICAL_RAW",
    "TIMER_1S_SAMPLE",
    "M1_BAR_PROXY",
}

DEFAULT_DB_NAME = "tick_archive.db"


@dataclass(frozen=True)
class InsertResult:
    """Small result object returned by insert operations."""

    inserted: int
    ignored: int
    rowids: List[int]


class TickArchiveWriter:
    """SQLite writer/query helper for the B9 raw tick archive.

    The schema is intentionally compact and append-oriented:
    ``tick_stream`` stores one row per raw or reconstructed tick/sample. A
    uniqueness guard on ``symbol + ts_epoch_ms + source_mode + capture_seq``
    prevents accidental duplicate writes while allowing multiple ticks inside
    the same millisecond when their capture sequence differs.
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_NAME) -> None:
        self.db_path = Path(db_path)
        if self.db_path.name.lower() == "powerflow.db":
            raise ValueError("TickArchiveWriter must not write to powerflow.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        return conn

    def _ensure_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tick_stream (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    ts_utc TEXT NOT NULL,
                    ts_epoch_ms INTEGER NOT NULL,
                    bid REAL,
                    ask REAL,
                    last REAL,
                    mid REAL,
                    spread REAL,
                    volume INTEGER,
                    volume_real REAL,
                    flags INTEGER,
                    source TEXT NOT NULL DEFAULT 'MT5',
                    source_mode TEXT NOT NULL,
                    broker TEXT,
                    server_time TEXT,
                    capture_seq INTEGER NOT NULL DEFAULT 0,
                    gap_ms INTEGER,
                    quality_flags TEXT NOT NULL DEFAULT 'OK',
                    created_at_utc TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
                    CHECK (source_mode IN ('ONTICK_RAW','HISTORICAL_RAW','TIMER_1S_SAMPLE','M1_BAR_PROXY'))
                )
                """
            )
            conn.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ux_tick_stream_symbol_ts_mode_seq
                ON tick_stream(symbol, ts_epoch_ms, source_mode, capture_seq)
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_tick_stream_symbol_ts ON tick_stream(symbol, ts_epoch_ms)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS ix_tick_stream_source_mode ON tick_stream(source_mode)"
            )
            conn.commit()

    def journal_mode(self) -> str:
        with self.connect() as conn:
            row = conn.execute("PRAGMA journal_mode").fetchone()
            return str(row[0]).upper() if row else "UNKNOWN"

    def insert_tick(self, tick: Dict[str, Any]) -> InsertResult:
        """Insert one normalized tick/sample into ``tick_stream``.

        Missing ``mid`` and ``spread`` are derived from bid/ask when possible.
        Missing ``gap_ms`` is computed from the previous tick of the same symbol
        and source mode.
        """

        normalized = self._normalize_tick(tick)
        with self.connect() as conn:
            before = conn.total_changes
            cursor = conn.execute(
                """
                INSERT OR IGNORE INTO tick_stream (
                    symbol, ts_utc, ts_epoch_ms, bid, ask, last, mid, spread,
                    volume, volume_real, flags, source, source_mode, broker,
                    server_time, capture_seq, gap_ms, quality_flags
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    normalized["symbol"],
                    normalized["ts_utc"],
                    normalized["ts_epoch_ms"],
                    normalized.get("bid"),
                    normalized.get("ask"),
                    normalized.get("last"),
                    normalized.get("mid"),
                    normalized.get("spread"),
                    normalized.get("volume"),
                    normalized.get("volume_real"),
                    normalized.get("flags"),
                    normalized.get("source", "MT5"),
                    normalized["source_mode"],
                    normalized.get("broker"),
                    normalized.get("server_time"),
                    normalized.get("capture_seq", 0),
                    normalized.get("gap_ms"),
                    normalized.get("quality_flags", "OK"),
                ],
            )
            conn.commit()
            inserted = conn.total_changes - before
            rowid = int(cursor.lastrowid) if inserted else -1
        return InsertResult(inserted=inserted, ignored=0 if inserted else 1, rowids=[rowid] if inserted else [])

    def insert_ticks(self, ticks: Iterable[Dict[str, Any]]) -> InsertResult:
        inserted = 0
        ignored = 0
        rowids: List[int] = []
        for tick in ticks:
            result = self.insert_tick(tick)
            inserted += result.inserted
            ignored += result.ignored
            rowids.extend(result.rowids)
        return InsertResult(inserted=inserted, ignored=ignored, rowids=rowids)

    def query_lookback(
        self,
        symbol: str,
        lookback_sec: int = 60,
        source_mode: Optional[str] = None,
        end_epoch_ms: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Return ticks for ``symbol`` within the lookback window."""

        symbol = symbol.upper().strip()
        end_ms = end_epoch_ms if end_epoch_ms is not None else utc_now_ms()
        start_ms = end_ms - int(lookback_sec * 1000)
        params: List[Any] = [symbol, start_ms, end_ms]
        mode_sql = ""
        if source_mode:
            self._validate_source_mode(source_mode)
            mode_sql = " AND source_mode = ?"
            params.append(source_mode)
        with self.connect() as conn:
            rows = conn.execute(
                f"""
                SELECT * FROM tick_stream
                WHERE symbol = ? AND ts_epoch_ms >= ? AND ts_epoch_ms <= ?{mode_sql}
                ORDER BY ts_epoch_ms ASC, capture_seq ASC, id ASC
                """,
                params,
            ).fetchall()
        return [dict(row) for row in rows]

    def count_ticks(self, symbol: Optional[str] = None) -> int:
        with self.connect() as conn:
            if symbol:
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM tick_stream WHERE symbol = ?",
                    [symbol.upper().strip()],
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) AS cnt FROM tick_stream").fetchone()
        return int(row["cnt"] if row else 0)

    def _normalize_tick(self, tick: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(tick, dict):
            raise TypeError("tick must be a dict")

        symbol = str(tick.get("symbol", "")).upper().strip()
        if not symbol:
            raise ValueError("tick.symbol is required")

        source_mode = str(tick.get("source_mode") or "ONTICK_RAW").upper().strip()
        self._validate_source_mode(source_mode)

        ts_epoch_ms = self._extract_epoch_ms(tick)
        bid = to_float_or_none(tick.get("bid"))
        ask = to_float_or_none(tick.get("ask"))
        last = to_float_or_none(tick.get("last"))
        mid = to_float_or_none(tick.get("mid"))
        spread = to_float_or_none(tick.get("spread"))

        derived_flags: List[str] = []
        if mid is None:
            if bid is not None and ask is not None and bid > 0 and ask > 0:
                mid = (bid + ask) / 2.0
                derived_flags.append("MID_RECONSTRUCTED")
            elif last is not None and last > 0:
                mid = last
                derived_flags.append("MID_FROM_LAST")

        if spread is None and bid is not None and ask is not None:
            spread = ask - bid
            derived_flags.append("SPREAD_RECONSTRUCTED")

        quality_flags = self._build_quality_flags(
            tick.get("quality_flags"), bid=bid, ask=ask, spread=spread, derived_flags=derived_flags
        )

        capture_seq = to_int_or_default(tick.get("capture_seq"), 0)
        gap_ms = tick.get("gap_ms")
        if gap_ms in (None, ""):
            gap_ms = self._compute_gap_ms(symbol, source_mode, ts_epoch_ms)
        else:
            gap_ms = to_int_or_default(gap_ms, 0)

        return {
            "symbol": symbol,
            "ts_utc": epoch_ms_to_utc(ts_epoch_ms),
            "ts_epoch_ms": ts_epoch_ms,
            "bid": bid,
            "ask": ask,
            "last": last,
            "mid": mid,
            "spread": spread,
            "volume": to_int_or_none(tick.get("volume")),
            "volume_real": to_float_or_none(tick.get("volume_real")),
            "flags": to_int_or_none(tick.get("flags")),
            "source": str(tick.get("source") or "MT5"),
            "source_mode": source_mode,
            "broker": empty_to_none(tick.get("broker")),
            "server_time": empty_to_none(tick.get("server_time")),
            "capture_seq": capture_seq,
            "gap_ms": gap_ms,
            "quality_flags": quality_flags,
        }

    def _extract_epoch_ms(self, tick: Dict[str, Any]) -> int:
        for key in ("ts_epoch_ms", "time_msc"):
            value = tick.get(key)
            if value not in (None, ""):
                return int(float(value))
        value = tick.get("time") or tick.get("ts_utc")
        if value in (None, ""):
            raise ValueError("tick time_msc or ts_epoch_ms is required")
        return parse_time_to_epoch_ms(str(value))

    def _compute_gap_ms(self, symbol: str, source_mode: str, ts_epoch_ms: int) -> int:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT ts_epoch_ms FROM tick_stream
                WHERE symbol = ? AND source_mode = ?
                ORDER BY ts_epoch_ms DESC, capture_seq DESC, id DESC
                LIMIT 1
                """,
                [symbol, source_mode],
            ).fetchone()
        if not row:
            return 0
        return max(0, ts_epoch_ms - int(row["ts_epoch_ms"]))

    def _build_quality_flags(
        self,
        raw_flags: Any,
        *,
        bid: Optional[float],
        ask: Optional[float],
        spread: Optional[float],
        derived_flags: Sequence[str],
    ) -> str:
        flags: List[str] = []
        if raw_flags not in (None, ""):
            flags.extend(split_quality_flags(str(raw_flags)))
        if bid is None or ask is None or bid <= 0 or ask <= 0:
            flags.append("BID_ASK_MISSING")
        if spread is not None and spread < 0:
            flags.append("SPREAD_NEGATIVE")
        flags.extend(derived_flags)
        if not flags:
            flags.append("OK")
        return "|".join(sorted(set(flags)))

    def _validate_source_mode(self, source_mode: str) -> None:
        if source_mode not in SOURCE_MODES:
            raise ValueError(f"unsupported source_mode={source_mode!r}; expected one of {sorted(SOURCE_MODES)}")


# Helper functions


def utc_now_ms() -> int:
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def epoch_ms_to_utc(epoch_ms: int) -> str:
    dt = datetime.fromtimestamp(epoch_ms / 1000.0, tz=timezone.utc)
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def parse_time_to_epoch_ms(value: str) -> int:
    value = value.strip()
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    # MT5 CSV can use either ISO or "YYYY.MM.DD HH:MM:SS" style strings.
    for fmt in (None, "%Y.%m.%d %H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            if fmt is None:
                dt = datetime.fromisoformat(value)
            else:
                dt = datetime.strptime(value, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return int(dt.timestamp() * 1000)
        except ValueError:
            continue
    raise ValueError(f"unsupported time format: {value!r}")


def to_float_or_none(value: Any) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def to_int_or_none(value: Any) -> Optional[int]:
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def to_int_or_default(value: Any, default: int) -> int:
    maybe = to_int_or_none(value)
    return default if maybe is None else maybe


def empty_to_none(value: Any) -> Optional[str]:
    if value in (None, ""):
        return None
    return str(value)


def split_quality_flags(value: str) -> List[str]:
    parts = []
    for token in value.replace(",", "|").split("|"):
        token = token.strip().upper()
        if token:
            parts.append(token)
    return parts


def _cli(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect PowerFlow tick_archive.db")
    parser.add_argument("--db", default=DEFAULT_DB_NAME)
    parser.add_argument("--symbol", default=None)
    parser.add_argument("--lookback-sec", type=int, default=60)
    parser.add_argument("--source-mode", default=None)
    args = parser.parse_args(argv)

    writer = TickArchiveWriter(args.db)
    if args.symbol:
        rows = writer.query_lookback(args.symbol, args.lookback_sec, args.source_mode)
        print(json.dumps({"count": len(rows), "rows": rows[:5]}, indent=2, ensure_ascii=False))
    else:
        print(json.dumps({"db": str(Path(args.db).resolve()), "journal_mode": writer.journal_mode(), "count": writer.count_ticks()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
