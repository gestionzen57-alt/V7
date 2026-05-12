#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — DATA_HEALTH_MONITOR

Read-only DB monitor for symbol/timeframe data health.

Measures:
- last_data_utc
- age_minutes
- row_count
- temporal_gaps > 2x expected interval
- per-symbol status
- global_status

No DB writes.
No BUY/SELL.
No external dependencies.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]
DEFAULT_TIMEFRAMES = [1, 5, 15, 30, 60, 240, 1440]

LIVE_TFS = [1, 5, 15]
HTF_TFS = [240, 1440]

# Density thresholds are deliberately light: the goal is data health, not signal validation.
MIN_ROWS_BY_TF = {
    1: 20,
    5: 10,
    15: 5,
    30: 3,
    60: 2,
    240: 50,
    1440: 50,
}

MAX_GAPS_RETURNED_PER_TF = 20
GAP_SCAN_LIMIT = 5000

TABLE_CANDIDATES = [
    "force_snapshots",
    "currency_force_snapshots",
    "force_snapshot",
    "market_snapshots",
    "snapshots",
]

SYMBOL_COLUMNS = ["symbol", "pair", "instrument"]
TIMEFRAME_COLUMNS = ["timeframe", "tf", "tf_minutes", "timeframe_minutes", "period"]
TIMESTAMP_COLUMNS = [
    "created_at",
    "timestamp_utc",
    "timestamp",
    "time_utc",
    "datetime_utc",
    "datetime",
    "time",
    "ts",
    "date",
]


@dataclass
class TableSchema:
    table: str
    symbol_col: str
    timeframe_col: str
    timestamp_col: str


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat().replace("+00:00", "Z")


def parse_csv_symbols(value: str) -> List[str]:
    return [x.strip().upper() for x in str(value).split(",") if x.strip()]


def parse_csv_ints(value: str) -> List[int]:
    result = []
    for item in str(value).split(","):
        item = item.strip()
        if item:
            result.append(int(item))
    return result


def db_uri(db_path: str) -> str:
    p = Path(db_path)
    # Keep relative DB paths relative to current Core directory.
    if p.is_absolute():
        path = p.as_posix()
    else:
        path = str(p).replace("\\", "/")
    return f"file:{path}?mode=ro"


def connect_readonly(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_uri(db_path), uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(r["name"]) for r in rows]


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    try:
        rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
        return [str(r["name"]) for r in rows]
    except Exception:
        return []


def first_matching(cols: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in cols}
    for cand in candidates:
        if cand.lower() in lower_map:
            return lower_map[cand.lower()]
    return None


def discover_schema(conn: sqlite3.Connection, preferred_table: Optional[str] = None) -> Tuple[Optional[TableSchema], List[str]]:
    risks: List[str] = []
    tables = list_tables(conn)

    candidates: List[str] = []
    if preferred_table:
        candidates.append(preferred_table)
    candidates.extend([t for t in TABLE_CANDIDATES if t not in candidates])
    candidates.extend([t for t in tables if t not in candidates])

    for table in candidates:
        if table not in tables:
            continue
        cols = table_columns(conn, table)
        symbol_col = first_matching(cols, SYMBOL_COLUMNS)
        timeframe_col = first_matching(cols, TIMEFRAME_COLUMNS)
        timestamp_col = first_matching(cols, TIMESTAMP_COLUMNS)

        if symbol_col and timeframe_col and timestamp_col:
            return TableSchema(table, symbol_col, timeframe_col, timestamp_col), risks

    risks.append("NO_COMPATIBLE_SNAPSHOT_TABLE_FOUND")
    return None, risks


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        # Accept unix seconds or milliseconds.
        val = float(value)
        if val > 10_000_000_000:
            val = val / 1000.0
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except Exception:
            return None

    text = str(value).strip()
    if not text:
        return None

    # Normalize common ISO variants.
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    for fmt in (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%d/%m/%Y %H:%M:%S",
    ):
        try:
            return datetime.strptime(text, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            continue

    return None


def iso_or_none(dt: Optional[datetime]) -> Optional[str]:
    if not dt:
        return None
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def fetch_count(conn: sqlite3.Connection, schema: TableSchema, symbol: str, tf: int) -> int:
    sql = (
        f"SELECT COUNT(*) AS n FROM {safe_ident(schema.table)} "
        f"WHERE UPPER({safe_ident(schema.symbol_col)}) = ? "
        f"AND CAST({safe_ident(schema.timeframe_col)} AS INTEGER) = ?"
    )
    row = conn.execute(sql, (symbol.upper(), int(tf))).fetchone()
    return int(row["n"] or 0) if row else 0


def fetch_recent_timestamps(
    conn: sqlite3.Connection,
    schema: TableSchema,
    symbol: str,
    tf: int,
    limit: int = GAP_SCAN_LIMIT,
) -> List[datetime]:
    sql = (
        f"SELECT {safe_ident(schema.timestamp_col)} AS ts "
        f"FROM {safe_ident(schema.table)} "
        f"WHERE UPPER({safe_ident(schema.symbol_col)}) = ? "
        f"AND CAST({safe_ident(schema.timeframe_col)} AS INTEGER) = ? "
        f"ORDER BY {safe_ident(schema.timestamp_col)} DESC "
        f"LIMIT ?"
    )
    rows = conn.execute(sql, (symbol.upper(), int(tf), int(limit))).fetchall()
    times: List[datetime] = []
    for row in rows:
        dt = parse_timestamp(row["ts"])
        if dt:
            times.append(dt)
    times.sort()
    return times


def compute_temporal_gaps(times: List[datetime], tf: int) -> List[Dict[str, Any]]:
    expected = max(1, int(tf))
    threshold = 2 * expected
    gaps: List[Dict[str, Any]] = []

    for prev, cur in zip(times, times[1:]):
        gap_min = (cur - prev).total_seconds() / 60.0
        if gap_min > threshold:
            gaps.append({
                "from_utc": iso_or_none(prev),
                "to_utc": iso_or_none(cur),
                "gap_minutes": round(gap_min, 3),
                "expected_interval_minutes": expected,
                "threshold_minutes": threshold,
            })

    # Keep the newest gaps first, capped.
    return list(reversed(gaps))[:MAX_GAPS_RETURNED_PER_TF]


def compute_tf_health(
    conn: sqlite3.Connection,
    schema: TableSchema,
    symbol: str,
    tf: int,
    now: datetime,
) -> Dict[str, Any]:
    count = fetch_count(conn, schema, symbol, tf)
    times = fetch_recent_timestamps(conn, schema, symbol, tf)
    last_dt = times[-1] if times else None
    age = None
    if last_dt:
        age = round(max(0.0, (now - last_dt).total_seconds() / 60.0), 3)

    gaps = compute_temporal_gaps(times, tf)

    return {
        "last_data_utc": iso_or_none(last_dt),
        "age_minutes": age,
        "row_count": count,
        "gaps": gaps,
        "temporal_gaps": gaps,  # alias explicit for downstream tools
        "gap_count": len(gaps),
        "scan_rows": len(times),
        "expected_interval_minutes": int(tf),
    }


def is_live_tf_ok(tf_payload: Mapping[str, Any], tf: int) -> bool:
    age = tf_payload.get("age_minutes")
    rows = int(tf_payload.get("row_count") or 0)
    min_rows = MIN_ROWS_BY_TF.get(int(tf), 1)
    return age is not None and float(age) < 30.0 and rows >= min_rows


def symbol_latest_age(timeframes: Mapping[str, Mapping[str, Any]]) -> Optional[float]:
    ages = [
        float(payload["age_minutes"])
        for payload in timeframes.values()
        if payload.get("age_minutes") is not None
    ]
    return min(ages) if ages else None


def htf_incomplete(timeframes: Mapping[str, Mapping[str, Any]]) -> bool:
    for tf in HTF_TFS:
        payload = timeframes.get(str(tf))
        if payload is not None:
            if int(payload.get("row_count") or 0) < MIN_ROWS_BY_TF[tf]:
                return True
    return False


def live_stack_ok(timeframes: Mapping[str, Mapping[str, Any]]) -> bool:
    for tf in LIVE_TFS:
        payload = timeframes.get(str(tf))
        if payload is None or not is_live_tf_ok(payload, tf):
            return False
    return True


def classify_symbol_status(timeframes: Mapping[str, Mapping[str, Any]]) -> str:
    latest_age = symbol_latest_age(timeframes)

    if latest_age is None:
        return "DATA_STALE"

    if latest_age > 60.0:
        return "DATA_STALE"

    if htf_incomplete(timeframes):
        # HTF incompleteness is a structural data health issue, but not necessarily a live failure.
        # It takes precedence over LIVE_OK to keep the dashboard honest.
        return "HTF_INCOMPLETE"

    if live_stack_ok(timeframes):
        return "LIVE_OK"

    # At least one live TF is weak/stale while the symbol still has some recent data.
    return "PARTIAL_STALE"


def classify_global_status(symbols_payload: Mapping[str, Mapping[str, Any]]) -> str:
    statuses = [str(v.get("status", "DATA_STALE")) for v in symbols_payload.values()]
    if not statuses:
        return "CRITICAL_STALE"

    stale_like = {"DATA_STALE", "DATA_MISSING"}
    if all(s in stale_like for s in statuses):
        return "CRITICAL_STALE"

    # GBPUSD is the principal validated symbol; stale GBPUSD means global critical.
    gbp = symbols_payload.get("GBPUSD")
    if gbp and str(gbp.get("status")) in stale_like:
        return "CRITICAL_STALE"

    if any(s != "LIVE_OK" for s in statuses):
        return "PARTIAL_STALE"

    return "LIVE_OK"


def compute_data_health(
    db_path: str,
    symbols: Sequence[str] = DEFAULT_SYMBOLS,
    timeframes: Sequence[int] = DEFAULT_TIMEFRAMES,
    table: Optional[str] = None,
) -> Dict[str, Any]:
    now = utc_now()
    technical_risks: List[str] = []

    try:
        conn = connect_readonly(db_path)
    except Exception as exc:
        return {
            "timestamp_utc": utc_now_iso(),
            "db_path": db_path,
            "db_mode": "READ_ONLY",
            "symbols": {
                s.upper(): {
                    "status": "DATA_STALE",
                    "timeframes": {},
                    "technical_risks": ["DB_READONLY_CONNECT_FAILED"],
                }
                for s in symbols
            },
            "global_status": "CRITICAL_STALE",
            "technical_risks": [f"DB_READONLY_CONNECT_FAILED:{exc}"],
        }

    try:
        schema, risks = discover_schema(conn, table)
        technical_risks.extend(risks)

        if schema is None:
            return {
                "timestamp_utc": utc_now_iso(),
                "db_path": db_path,
                "db_mode": "READ_ONLY",
                "schema": None,
                "symbols": {
                    s.upper(): {
                        "status": "DATA_STALE",
                        "timeframes": {},
                        "technical_risks": ["NO_COMPATIBLE_SNAPSHOT_TABLE_FOUND"],
                    }
                    for s in symbols
                },
                "global_status": "CRITICAL_STALE",
                "technical_risks": technical_risks,
            }

        symbols_payload: Dict[str, Any] = {}

        for symbol in [s.upper() for s in symbols]:
            tf_payload: Dict[str, Any] = {}
            symbol_risks: List[str] = []

            for tf in timeframes:
                try:
                    tf_payload[str(int(tf))] = compute_tf_health(conn, schema, symbol, int(tf), now)
                except Exception as exc:
                    tf_payload[str(int(tf))] = {
                        "last_data_utc": None,
                        "age_minutes": None,
                        "row_count": 0,
                        "gaps": [],
                        "temporal_gaps": [],
                        "gap_count": 0,
                        "technical_error": str(exc),
                    }
                    symbol_risks.append(f"TF{tf}_HEALTH_FAILED")

            status = classify_symbol_status(tf_payload)

            if status == "DATA_STALE":
                symbol_risks.append(f"{symbol}_STALE_DATA")
            if htf_incomplete(tf_payload):
                symbol_risks.append(f"{symbol}_HTF_INCOMPLETE")
            if any(int(v.get("gap_count") or 0) > 0 for v in tf_payload.values()):
                symbol_risks.append(f"{symbol}_TEMPORAL_GAPS_PRESENT")

            latest_age = symbol_latest_age(tf_payload)

            symbols_payload[symbol] = {
                "status": status,
                "last_update_age_min": latest_age,
                "timeframes": tf_payload,
                "technical_risks": symbol_risks,
            }

        global_status = classify_global_status(symbols_payload)

        return {
            "timestamp_utc": utc_now_iso(),
            "db_path": db_path,
            "db_mode": "READ_ONLY",
            "schema": asdict(schema),
            "symbols": symbols_payload,
            "global_status": global_status,
            "technical_risks": technical_risks,
            "note": "Data health monitors capture freshness, density and temporal gaps. It does not produce trade decisions.",
        }

    finally:
        conn.close()


def write_json(data: Mapping[str, Any], output_path: str) -> None:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow DATA_HEALTH_MONITOR")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default=",".join(DEFAULT_SYMBOLS))
    parser.add_argument("--timeframes", default=",".join(str(x) for x in DEFAULT_TIMEFRAMES))
    parser.add_argument("--table", default=None, help="Optional snapshot table override.")
    parser.add_argument("--output", "--out", dest="output", default="output/data_health_monitor.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    result = compute_data_health(
        db_path=args.db,
        symbols=parse_csv_symbols(args.symbols),
        timeframes=parse_csv_ints(args.timeframes),
        table=args.table,
    )

    write_json(result, args.output)

    if args.pretty:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(
            "DATA_HEALTH_MONITOR_OK | "
            f"global_status={result.get('global_status')} | "
            f"symbols={','.join(result.get('symbols', {}).keys())} | "
            f"out={args.output}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
