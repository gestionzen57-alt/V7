# -*- coding: utf-8 -*-
"""
PowerFlow V6 - DB Freshness Probe (read-only)

Mission:
    Diagnose whether powerflow.db is fresh enough for live perception.

No DB writes.
No capture_bridge modification.
No Telegram.
"""

from __future__ import annotations

import json
import os
import sqlite3
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


TIME_COLUMN_CANDIDATES = ("created_at", "timestamp", "time", "datetime", "ts")
SYMBOL_COLUMN_CANDIDATES = ("symbol", "pair", "instrument")
TIMEFRAME_COLUMN_CANDIDATES = ("timeframe", "tf", "period")
FORCE_TABLE_CANDIDATES = ("force_snapshots", "force_snapshots_v2")


@dataclass
class TableFreshness:
    table: str
    exists: bool
    row_count: int = 0
    latest_timestamp: Optional[str] = None
    data_age_minutes: Optional[float] = None
    status: str = "UNKNOWN"
    time_column: Optional[str] = None
    symbol_column: Optional[str] = None
    timeframe_column: Optional[str] = None


def build_db_freshness_state(
    db_path: str | Path = "powerflow.db",
    symbol: str = "GBPUSD",
    stale_minutes: int = 5,
    tactical_stale_minutes: int = 180,
    include_process_probe: bool = True,
) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    db_path = Path(db_path)

    state: Dict[str, Any] = {
        "meta": {
            "generated_at": _iso(now),
            "source": "pf_db_freshness_probe",
            "version": "0.3-readonly",
            "symbol": symbol.upper(),
            "stale_minutes": stale_minutes,
            "tactical_stale_minutes": tactical_stale_minutes,
        },
        "files": _file_state(db_path),
        "tables": [],
        "processes": {},
        "verdict": {
            "status": "UNKNOWN",
            "latest_timestamp": None,
            "data_age_minutes": None,
            "probable_cause": None,
            "next_action": [],
            "risks_technical": [],
        },
    }

    if not db_path.exists():
        state["verdict"]["status"] = "DATA_BLIND"
        state["verdict"]["probable_cause"] = "powerflow.db_not_found"
        state["verdict"]["next_action"].append("verify_current_directory_or_db_path")
        return state

    try:
        with _connect_readonly(db_path) as conn:
            conn.row_factory = sqlite3.Row
            tables = _list_tables(conn)
            for table in sorted(tables):
                if table in FORCE_TABLE_CANDIDATES or "snapshot" in table.lower() or "diagnostic" in table.lower() or table in {"signals", "nodes_v6"}:
                    state["tables"].append(asdict(_inspect_table(conn, table, now, symbol.upper())))

    except sqlite3.Error as exc:
        state["verdict"]["status"] = "DATA_BLIND"
        state["verdict"]["probable_cause"] = f"sqlite_error:{exc}"
        state["verdict"]["risks_technical"].append("sqlite_read_error")
        return state

    if include_process_probe:
        state["processes"] = _process_probe()

    _fill_verdict(state)
    return state


def write_db_freshness_state(state: Dict[str, Any], out_path: str | Path, pretty: bool = False) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(state, ensure_ascii=False, indent=2 if pretty else None) + "\n", encoding="utf-8")


def _connect_readonly(db_path: Path) -> sqlite3.Connection:
    if db_path.is_absolute():
        uri = db_path.as_uri() + "?mode=ro"
    else:
        uri = f"file:{db_path.as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [str(r[0]) for r in rows]


def _inspect_table(conn: sqlite3.Connection, table: str, now: datetime, symbol: str) -> TableFreshness:
    columns = _table_columns(conn, table)
    time_col = _pick_column(columns, TIME_COLUMN_CANDIDATES)
    symbol_col = _pick_column(columns, SYMBOL_COLUMN_CANDIDATES)
    tf_col = _pick_column(columns, TIMEFRAME_COLUMN_CANDIDATES)

    row_count = _safe_count(conn, table)
    latest = None
    age = None
    status = "NO_TIME_COLUMN"

    if time_col:
        latest_raw = _latest_value(conn, table, time_col, symbol_col, symbol)
        latest_dt = _parse_datetime(latest_raw)
        if latest_dt:
            latest = _iso(latest_dt)
            age = round(max(0.0, (now - latest_dt).total_seconds() / 60.0), 1)
            if age <= 5:
                status = "LIVE_OK"
            elif age <= 180:
                status = "TACTICAL_STALE"
            else:
                status = "DATA_STALE"
        else:
            status = "NO_PARSEABLE_TIMESTAMP"

    return TableFreshness(
        table=table,
        exists=True,
        row_count=row_count,
        latest_timestamp=latest,
        data_age_minutes=age,
        status=status,
        time_column=time_col,
        symbol_column=symbol_col,
        timeframe_column=tf_col,
    )


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({_q(table)})").fetchall()]


def _pick_column(columns: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    lookup = {c.lower(): c for c in columns}
    for candidate in candidates:
        if candidate.lower() in lookup:
            return lookup[candidate.lower()]
    return None


def _safe_count(conn: sqlite3.Connection, table: str) -> int:
    try:
        return int(conn.execute(f"SELECT COUNT(*) FROM {_q(table)}").fetchone()[0])
    except sqlite3.Error:
        return 0


def _latest_value(
    conn: sqlite3.Connection,
    table: str,
    time_col: str,
    symbol_col: Optional[str],
    symbol: str,
) -> Any:
    params: List[Any] = []
    sql = f"SELECT {_q(time_col)} FROM {_q(table)}"
    if symbol_col:
        sql += f" WHERE UPPER({_q(symbol_col)}) = ?"
        params.append(symbol)
    sql += f" ORDER BY {_q(time_col)} DESC LIMIT 1"
    row = conn.execute(sql, params).fetchone()
    return row[0] if row else None


def _file_state(db_path: Path) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    files = {}
    for p in [db_path, Path(str(db_path) + "-wal"), Path(str(db_path) + "-shm")]:
        exists = p.exists()
        item = {
            "path": str(p),
            "exists": exists,
            "size_bytes": p.stat().st_size if exists else None,
            "modified_at": None,
            "modified_age_minutes": None,
        }
        if exists:
            mtime = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc)
            item["modified_at"] = _iso(mtime)
            item["modified_age_minutes"] = round(max(0.0, (now - mtime).total_seconds() / 60.0), 1)
        files[p.name] = item
    return files


def _process_probe() -> Dict[str, Any]:
    """
    Lightweight Windows process probe without psutil.
    If tasklist is unavailable, returns a soft error.
    """
    result: Dict[str, Any] = {
        "tasklist_available": False,
        "python_processes": [],
        "capture_bridge_hint": False,
        "notes": [],
    }
    try:
        proc = subprocess.run(
            ["tasklist", "/V", "/FO", "CSV"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10,
            check=False,
        )
    except Exception as exc:
        result["notes"].append(f"tasklist_verbose_error:{exc}")
        try:
            proc = subprocess.run(
                ["tasklist", "/FO", "CSV"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
                check=False,
            )
        except Exception as exc2:
            result["notes"].append(f"tasklist_basic_error:{exc2}")
            return result

    result["tasklist_available"] = True
    text = proc.stdout or ""
    for line in text.splitlines():
        low = line.lower()
        if "python" in low:
            result["python_processes"].append(line[:500])
        if "capture_bridge" in low:
            result["capture_bridge_hint"] = True
    return result


def _fill_verdict(state: Dict[str, Any]) -> None:
    verdict = state["verdict"]
    meta = state.get("meta", {})
    stale_minutes = float(meta.get("stale_minutes") or 5)
    tactical_stale_minutes = float(meta.get("tactical_stale_minutes") or 180)

    tables = state.get("tables", [])
    force_tables = [t for t in tables if t.get("table") in FORCE_TABLE_CANDIDATES]
    usable = force_tables or tables

    latest_table = None
    for t in usable:
        if t.get("latest_timestamp"):
            if latest_table is None or (t.get("data_age_minutes") or 10**9) < (latest_table.get("data_age_minutes") or 10**9):
                latest_table = t

    if latest_table is None:
        verdict["status"] = "DATA_BLIND"
        verdict["probable_cause"] = "no_parseable_timestamp_in_candidate_tables"
        verdict["next_action"] = ["inspect_force_snapshots_schema", "verify_capture_bridge_insert_columns"]
        verdict["risks_technical"] = ["timestamp_schema_unknown"]
        return

    verdict["latest_timestamp"] = latest_table.get("latest_timestamp")
    verdict["data_age_minutes"] = latest_table.get("data_age_minutes")
    verdict["source_table"] = latest_table.get("table")

    age = float(latest_table.get("data_age_minutes") or 0.0)

    # If latest timestamp is in local broker future vs UTC parsing, age is clamped to 0.0.
    # Treat this as live, but mark clock interpretation.
    clock_note = None
    if age == 0.0:
        clock_note = "timestamp_age_clamped_zero_check_timezone_or_broker_time"

    if age <= stale_minutes:
        verdict["status"] = "LIVE_OK"
        verdict["probable_cause"] = "capture_chain_currently_fresh"
        verdict["next_action"] = ["run_temporal_node_state_again", "then_prepare_telegram_dry_run"]
        verdict["risks_technical"] = []
        if clock_note:
            verdict["risks_technical"].append(clock_note)
    elif age <= tactical_stale_minutes:
        verdict["status"] = "TACTICAL_STALE"
        verdict["probable_cause"] = "capture_recent_but_not_live"
        verdict["next_action"] = ["check_capture_bridge_loop", "check_mt4_feed", "check_socket_55555"]
        verdict["risks_technical"] = ["latency", "partial_freshness"]
    else:
        verdict["status"] = "DATA_STALE"
        verdict["probable_cause"] = "capture_chain_not_updating_force_snapshots"
        verdict["next_action"] = [
            "start_or_check_capture_bridge",
            "verify_MT4_EA_is_connected",
            "check_TCP_127.0.0.1_55555",
            "re-run_probe_after_30_seconds",
        ]
        verdict["risks_technical"] = ["stale_data", "historical_perception_only"]

    processes = state.get("processes") or {}
    if processes.get("tasklist_available") and not processes.get("capture_bridge_hint"):
        verdict["next_action"].append("no_capture_bridge_process_seen_in_tasklist")


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, (int, float)):
        v = float(value)
        if v > 10_000_000_000:
            v /= 1000.0
        try:
            dt = datetime.fromtimestamp(v, tz=timezone.utc)
        except (OSError, ValueError):
            return None
    else:
        text = str(value).strip()
        if not text:
            return None
        text = text.replace("Z", "+00:00")
        try:
            dt = datetime.fromisoformat(text)
        except ValueError:
            for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y.%m.%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
                try:
                    dt = datetime.strptime(text, fmt)
                    break
                except ValueError:
                    dt = None
            if dt is None:
                return None

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'
