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


# --- T0103_RAW_CALIBRATION_API_COMPAT_SHIM_START ---
class RawCalibrationConfig:
    """Flexible legacy-compatible configuration object for raw calibration runners."""

    _ordered_fields = [
        "summary_json", "tick_db", "output", "symbol", "broker",
        "broker_time_shift_min", "raw_source_mode", "raw_data_visibility",
    ]

    _defaults = {
        "summary_json": None,
        "tick_db": None,
        "output": None,
        "symbol": "GBPUSD",
        "broker": "UNKNOWN",
        "broker_time_shift_min": 0,
        "raw_source_mode": "HISTORICAL_RAW",
        "raw_data_visibility": "MT5_RAW_ALIGNED",
    }

    _aliases = {
        "db_path": "tick_db",
        "tick_db_path": "tick_db",
        "summary_path": "summary_json",
        "output_dir": "output",
        "raw_time_shift_min": "broker_time_shift_min",
        "time_shift_min": "broker_time_shift_min",
        "data_visibility": "raw_data_visibility",
        "source_mode": "raw_source_mode",
    }

    def __init__(self, *args, **kwargs):
        values = dict(self._defaults)
        for key, value in zip(self._ordered_fields, args):
            values[key] = value
        for key, value in kwargs.items():
            values[self._aliases.get(key, key)] = value
        for key, value in values.items():
            setattr(self, key, value)

    def as_dict(self):
        return dict(self.__dict__)

    def to_dict(self):
        return self.as_dict()
# --- T0103_RAW_CALIBRATION_API_COMPAT_SHIM_END ---

# --- T0103_RAW_CALIBRATION_FULL_API_COMPAT_V5_START ---
# Compatibility API for run_t009_raw_calibration_once.py.
# This block is intentionally read-only with respect to databases.

import json as _t0103_json
import sqlite3 as _t0103_sqlite3
from pathlib import Path as _T0103Path
from datetime import datetime as _T0103DateTime, timezone as _T0103Timezone, timedelta as _T0103Timedelta
from copy import deepcopy as _t0103_deepcopy
from typing import Any as _T0103Any


if "RawCalibrationConfig" not in globals():
    class RawCalibrationConfig:
        _ordered_fields = [
            "summary_json", "tick_db", "output", "symbol", "broker",
            "broker_time_shift_min", "raw_source_mode", "raw_data_visibility",
        ]

        _defaults = {
            "summary_json": None,
            "tick_db": None,
            "tick_db_path": None,
            "output": None,
            "symbol": "GBPUSD",
            "broker": "UNKNOWN",
            "broker_time_shift_min": 0,
            "raw_source_mode": "HISTORICAL_RAW",
            "raw_data_visibility": "MT5_RAW_ALIGNED",
            "raw_confidence_cap": 0.55,
            "pip_size": 0.0001,
        }

        _aliases = {
            "db_path": "tick_db_path",
            "tick_db": "tick_db_path",
            "tick_db_path": "tick_db_path",
            "summary_path": "summary_json",
            "output_dir": "output",
            "raw_time_shift_min": "broker_time_shift_min",
            "time_shift_min": "broker_time_shift_min",
            "data_visibility": "raw_data_visibility",
            "source_mode": "raw_source_mode",
        }

        def __init__(self, *args, **kwargs):
            values = dict(self._defaults)
            for key, value in zip(self._ordered_fields, args):
                values[self._aliases.get(key, key)] = value
            for key, value in kwargs.items():
                values[self._aliases.get(key, key)] = value
            if values.get("tick_db_path") is None and values.get("tick_db") is not None:
                values["tick_db_path"] = values["tick_db"]
            if values.get("tick_db") is None and values.get("tick_db_path") is not None:
                values["tick_db"] = values["tick_db_path"]
            for key, value in values.items():
                setattr(self, key, value)

        def as_dict(self):
            return dict(self.__dict__)

        def to_dict(self):
            return self.as_dict()


def load_json(path):
    return _t0103_json.loads(_T0103Path(path).read_text(encoding="utf-8-sig"))


def export_json(payload, path):
    out = _T0103Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(_t0103_json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def _t0103_parse_dt(value):
    if value is None:
        return None
    if isinstance(value, _T0103DateTime):
        dt = value
    else:
        s = str(value).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = _T0103DateTime.fromisoformat(s)
    if dt.tzinfo is not None:
        dt = dt.astimezone(_T0103Timezone.utc).replace(tzinfo=None)
    return dt


def _t0103_fmt_dt(dt):
    return dt.replace(microsecond=0).isoformat() + "Z"


def _t0103_db_columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _t0103_connect_ro(db_path):
    p = str(db_path).replace("\\", "/")
    return _t0103_sqlite3.connect(f"file:{p}?mode=ro", uri=True)


def _t0103_mid(row):
    mid = row.get("mid")
    if mid is not None:
        return float(mid)
    bid = row.get("bid")
    ask = row.get("ask")
    if bid is not None and ask is not None:
        return (float(bid) + float(ask)) / 2.0
    return None


def _t0103_read_raw_rows(cfg, start_raw, end_raw):
    db = getattr(cfg, "tick_db_path", None) or getattr(cfg, "tick_db", None)
    if not db:
        return [], 0

    symbol = getattr(cfg, "symbol", "GBPUSD")
    raw_source_mode = getattr(cfg, "raw_source_mode", "HISTORICAL_RAW")

    start_s = _t0103_fmt_dt(start_raw)
    end_s = _t0103_fmt_dt(end_raw)

    conn = _t0103_connect_ro(db)
    try:
        cols = _t0103_db_columns(conn, "tick_stream")
        select_cols = [c for c in ["ts_utc", "bid", "ask", "mid", "spread", "source_mode", "symbol", "capture_seq", "gap_ms"] if c in cols]
        if not {"ts_utc", "bid", "ask"}.issubset(set(cols)):
            return [], 0

        where = ["ts_utc >= ?", "ts_utc <= ?"]
        params = [start_s, end_s]
        if "symbol" in cols:
            where.append("symbol = ?")
            params.append(symbol)
        if "source_mode" in cols:
            where.append("source_mode = ?")
            params.append(raw_source_mode)

        where_sql = " AND ".join(where)
        raw_count = conn.execute(f"SELECT COUNT(*) FROM tick_stream WHERE {where_sql}", params).fetchone()[0]

        sql = f"SELECT {', '.join(select_cols)} FROM tick_stream WHERE {where_sql} ORDER BY ts_utc"
        raw_rows = [dict(zip(select_cols, row)) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

    seen = set()
    dedup = []
    for row in raw_rows:
        key = (row.get("ts_utc"), row.get("bid"), row.get("ask"), row.get("mid"), row.get("spread"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)

    return dedup, int(raw_count)


def _t0103_proxy_delta(moment):
    for key in ("center_delta_pips", "delta_pips", "proxy_delta_pips"):
        if moment.get(key) is not None:
            try:
                return float(moment[key])
            except Exception:
                pass
    cs = moment.get("center_start")
    ce = moment.get("center_end")
    if cs is not None and ce is not None:
        try:
            return (float(ce) - float(cs)) / 0.0001
        except Exception:
            return None
    return None


def _t0103_calibrate_one_moment(moment, cfg):
    out = dict(moment)
    start = _t0103_parse_dt(moment.get("time_start"))
    end = _t0103_parse_dt(moment.get("time_end"))
    shift = int(getattr(cfg, "broker_time_shift_min", 0) or 0)
    pip_size = float(getattr(cfg, "pip_size", 0.0001) or 0.0001)

    out["raw_source_mode"] = getattr(cfg, "raw_source_mode", "HISTORICAL_RAW")
    out["raw_data_visibility"] = getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED")
    out["raw_broker"] = getattr(cfg, "broker", "UNKNOWN")
    out["raw_time_shift_min"] = shift
    out["raw_dedup_mode"] = "DISTINCT_TS_BID_ASK_MID_SPREAD"

    if start is None or end is None:
        out.update({
            "raw_coverage": "RAW_UNAVAILABLE",
            "proxy_vs_raw_verdict": "RAW_UNAVAILABLE",
            "raw_texture_role": "RAW_UNAVAILABLE",
            "raw_tick_count": 0,
            "raw_tick_count_raw": 0,
            "raw_tick_count_dedup": 0,
            "raw_duplicate_count": 0,
            "raw_duplicate_ratio": 0.0,
        })
        return out

    zero_duration = end <= start
    if zero_duration:
        end = start + _T0103Timedelta(seconds=1)

    raw_start = start - _T0103Timedelta(minutes=shift)
    raw_end = end - _T0103Timedelta(minutes=shift)
    out["raw_window_start_mt5"] = _t0103_fmt_dt(raw_start)
    out["raw_window_end_mt5"] = _t0103_fmt_dt(raw_end)

    rows, raw_count = _t0103_read_raw_rows(cfg, raw_start, raw_end)
    dedup_count = len(rows)
    duplicate_count = max(0, raw_count - dedup_count)
    duplicate_ratio = (duplicate_count / raw_count) if raw_count else 0.0

    mids = [_t0103_mid(r) for r in rows]
    mids = [m for m in mids if m is not None]

    out["raw_tick_count_raw"] = raw_count
    out["raw_tick_count_dedup"] = dedup_count
    out["raw_tick_count"] = dedup_count
    out["raw_duplicate_count"] = duplicate_count
    out["raw_duplicate_ratio"] = round(duplicate_ratio, 6)

    if not mids:
        out["raw_delta_pips"] = 0.0
        out["raw_range_pips"] = 0.0
        out["raw_coverage"] = "RAW_UNAVAILABLE"
        out["proxy_vs_raw_verdict"] = "RAW_UNAVAILABLE"
        out["raw_texture_role"] = "RAW_UNAVAILABLE"
        out["progressive_wave_state"] = out.get("progressive_wave_state") or "RAW_UNAVAILABLE"
        return out

    raw_delta = (mids[-1] - mids[0]) / pip_size
    raw_range = (max(mids) - min(mids)) / pip_size
    out["raw_delta_pips"] = round(raw_delta, 4)
    out["raw_range_pips"] = round(raw_range, 4)
    out["raw_coverage"] = "PARTIAL" if zero_duration else "FULL"

    if zero_duration:
        out["zero_duration_status"] = "ZERO_DURATION_MOMENT"
        out["proxy_vs_raw_verdict"] = "ZERO_DURATION_MOMENT"
        out["raw_texture_role"] = "ZERO_DURATION_MOMENT"
        return out

    proxy_delta = _t0103_proxy_delta(moment)
    moment_type = str(moment.get("moment_type", "")).upper()
    same_sign = proxy_delta is not None and ((proxy_delta >= 0 and raw_delta >= 0) or (proxy_delta <= 0 and raw_delta <= 0))

    if "PROGRESSIVE" in moment_type:
        if abs(raw_delta) >= 4.0 and same_sign:
            out["proxy_vs_raw_verdict"] = "CONFIRMED_BY_RAW"
            out["raw_texture_role"] = "RAW_PROGRESS_CONFIRMED"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_CONFIRMED"
        elif raw_range >= 4.0 and abs(raw_delta) < max(3.0, raw_range * 0.35):
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_ROTATION_CONFIRMED"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_ROTATIONAL"
        else:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_PROXY_DIVERGENCE" if proxy_delta is not None and not same_sign else "RAW_WEAK_PROGRESS"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_WEAK_RAW"
    else:
        if proxy_delta is not None and same_sign and abs(raw_delta) >= 2.0:
            out["proxy_vs_raw_verdict"] = "CONFIRMED_BY_RAW"
            out["raw_texture_role"] = "RAW_PROGRESS_CONFIRMED"
        elif raw_range >= 4.0:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_ROTATION_CONFIRMED"
        else:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_FRICTION_CONFIRMED"

    return out


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0103_API_COMPAT_V5",
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "raw_dedup_mode": "DISTINCT_TS_BID_ASK_MID_SPREAD",
        "limits": [
            "raw tick broker-relative",
            "deduplicated read-only calibration",
            "no central FX footprint claimed"
        ],
    })
    return payload


def export_markdown(payload, path):
    out = _T0103Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    moments = payload.get("moments", [])
    lines = [
        "# B9 raw calibration",
        "",
        "Lecture raw broker-relative, dédupliquée, read-only.",
        "",
        "| Time | Moment | Verdict | Raw texture | Coverage | Ticks |",
        "|---|---|---|---|---|---:|",
    ]
    for m in moments:
        lines.append(
            f"| {m.get('time_start','')} → {m.get('time_end','')} "
            f"| `{m.get('moment_type','')}` {m.get('label_fr','')} "
            f"| `{m.get('proxy_vs_raw_verdict','')}` "
            f"| `{m.get('raw_texture_role','')}` "
            f"| `{m.get('raw_coverage','')}` "
            f"| {m.get('raw_tick_count_dedup', m.get('raw_tick_count', 0))} |"
        )
    lines += [
        "",
        "Limites : raw MT5 broker-relative ; aucune prétention de footprint centralisé ; aucun langage décisionnel.",
    ]
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return out
# --- T0103_RAW_CALIBRATION_FULL_API_COMPAT_V5_END ---

# --- T0103_RAW_CALIBRATION_CONFIG_OVERRIDE_V51_START ---
# Final compatibility override for run_t009_raw_calibration_once.py.
class RawCalibrationConfig:
    _ordered_fields = [
        "summary_json",
        "tick_db_path",
        "output",
        "symbol",
        "broker",
        "broker_time_shift_min",
        "raw_source_mode",
        "raw_data_visibility",
    ]

    _defaults = {
        "summary_json": None,
        "tick_db": None,
        "tick_db_path": None,
        "output": None,
        "symbol": "GBPUSD",
        "broker": "UNKNOWN",
        "broker_time_shift_min": 0,
        "raw_source_mode": "HISTORICAL_RAW",
        "raw_data_visibility": "MT5_RAW_ALIGNED",
        "raw_confidence_cap": 0.55,
        "pip_size": 0.0001,
    }

    _aliases = {
        "db_path": "tick_db_path",
        "tick_db": "tick_db_path",
        "tick_db_path": "tick_db_path",
        "summary_path": "summary_json",
        "output_dir": "output",
        "raw_time_shift_min": "broker_time_shift_min",
        "time_shift_min": "broker_time_shift_min",
        "data_visibility": "raw_data_visibility",
        "source_mode": "raw_source_mode",
    }

    def __init__(self, *args, **kwargs):
        values = dict(self._defaults)

        for key, value in zip(self._ordered_fields, args):
            canonical = self._aliases.get(key, key)
            values[canonical] = value

        for key, value in kwargs.items():
            canonical = self._aliases.get(key, key)
            values[canonical] = value

        if values.get("tick_db_path") is None and values.get("tick_db") is not None:
            values["tick_db_path"] = values["tick_db"]

        if values.get("tick_db") is None and values.get("tick_db_path") is not None:
            values["tick_db"] = values["tick_db_path"]

        for key, value in values.items():
            setattr(self, key, value)

    def as_dict(self):
        return dict(self.__dict__)

    def to_dict(self):
        return self.as_dict()
# --- T0103_RAW_CALIBRATION_CONFIG_OVERRIDE_V51_END ---

# --- T0105_B9_RAW_ACTIVITY_METRICS_V0_START ---
# Raw activity metrics V0 for B9 microfilm intrinsic time.
# Read-only DB behavior: this block only reads tick_stream in mode=ro.

from statistics import median as _t0105_median, mean as _t0105_mean


def _t0105_safe_float(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _t0105_safe_round(value, ndigits=6, default=None):
    try:
        if value is None:
            return default
        return round(float(value), ndigits)
    except Exception:
        return default


def _t0105_duration_seconds(start, end):
    try:
        seconds = (end - start).total_seconds()
        return max(0.0, float(seconds))
    except Exception:
        return 0.0


def _t0105_dt_from_tick(row):
    return _t0103_parse_dt(row.get("ts_utc"))


def _t0105_compute_gaps_ms(rows):
    times = []
    for row in rows:
        dt = _t0105_dt_from_tick(row)
        if dt is not None:
            times.append(dt)
    times = sorted(times)
    gaps = []
    for a, b in zip(times, times[1:]):
        gaps.append(max(0.0, (b - a).total_seconds() * 1000.0))
    return gaps


def _t0105_activity_profile(dedup_count, duration_seconds, gaps_ms):
    if dedup_count <= 0 or duration_seconds <= 0:
        return "RAW_ACTIVITY_UNKNOWN"

    density_per_second = dedup_count / duration_seconds
    max_gap = max(gaps_ms) if gaps_ms else None

    if max_gap is not None and max_gap >= 10000:
        return "RAW_ACTIVITY_GAPPY"
    if density_per_second >= 3.0:
        return "RAW_ACTIVITY_BURST"
    if density_per_second >= 0.75:
        return "RAW_ACTIVITY_DENSE"
    if density_per_second <= 0.05:
        return "RAW_ACTIVITY_THIN"
    return "RAW_ACTIVITY_NORMAL"


def _t0105_spread_metrics(rows, pip_size):
    spreads = []
    for row in rows:
        spread = _t0105_safe_float(row.get("spread"))
        if spread is None:
            bid = _t0105_safe_float(row.get("bid"))
            ask = _t0105_safe_float(row.get("ask"))
            if bid is not None and ask is not None:
                spread = ask - bid
        if spread is not None:
            spreads.append(spread / pip_size)

    if not spreads:
        return {
            "raw_spread_mean_pips": None,
            "raw_spread_min_pips": None,
            "raw_spread_max_pips": None,
            "raw_spread_expansion_pips": None,
            "raw_spread_stability_state": "SPREAD_UNKNOWN",
        }

    spread_min = min(spreads)
    spread_max = max(spreads)
    spread_mean = _t0105_mean(spreads)
    expansion = spread_max - spread_min

    if len(spreads) < 3:
        state = "SPREAD_THIN_DATA"
    elif expansion <= 0.2:
        state = "SPREAD_STABLE"
    elif expansion <= 0.8:
        state = "SPREAD_EXPANDING"
    else:
        state = "SPREAD_UNSTABLE"

    return {
        "raw_spread_mean_pips": round(spread_mean, 4),
        "raw_spread_min_pips": round(spread_min, 4),
        "raw_spread_max_pips": round(spread_max, 4),
        "raw_spread_expansion_pips": round(expansion, 4),
        "raw_spread_stability_state": state,
    }


def _t0105_volume_metrics(rows, duration_seconds):
    volume_keys = ["tick_volume", "volume", "real_volume", "vol"]
    values = []
    present_key = None

    for row in rows:
        for key in volume_keys:
            if key in row and row.get(key) is not None:
                present_key = key
                value = _t0105_safe_float(row.get(key))
                if value is not None:
                    values.append(value)
                break

    if present_key is None:
        return {
            "raw_volume_visibility_state": "VOLUME_NOT_PRESENT",
            "raw_volume_field": None,
            "raw_tick_volume_sum": None,
            "raw_tick_volume_density": None,
            "raw_volume_confidence_cap": 0.0,
        }

    total = sum(values) if values else 0.0
    density = total / duration_seconds if duration_seconds > 0 else None

    return {
        "raw_volume_visibility_state": "VOLUME_PRESENT_BROKER_RELATIVE",
        "raw_volume_field": present_key,
        "raw_tick_volume_sum": round(total, 4),
        "raw_tick_volume_density": _t0105_safe_round(density, 6),
        "raw_volume_confidence_cap": 0.20,
    }


def _t0105_read_raw_rows_with_activity(cfg, start_raw, end_raw):
    db = getattr(cfg, "tick_db_path", None) or getattr(cfg, "tick_db", None)
    if not db:
        return [], 0

    symbol = getattr(cfg, "symbol", "GBPUSD")
    raw_source_mode = getattr(cfg, "raw_source_mode", "HISTORICAL_RAW")

    start_s = _t0103_fmt_dt(start_raw)
    end_s = _t0103_fmt_dt(end_raw)

    conn = _t0103_connect_ro(db)
    try:
        cols = _t0103_db_columns(conn, "tick_stream")
        preferred = [
            "ts_utc", "bid", "ask", "mid", "spread",
            "volume", "tick_volume", "real_volume", "vol",
            "source_mode", "symbol", "capture_seq", "gap_ms",
        ]
        select_cols = [c for c in preferred if c in cols]
        if not {"ts_utc", "bid", "ask"}.issubset(set(cols)):
            return [], 0

        where = ["ts_utc >= ?", "ts_utc <= ?"]
        params = [start_s, end_s]
        if "symbol" in cols:
            where.append("symbol = ?")
            params.append(symbol)
        if "source_mode" in cols:
            where.append("source_mode = ?")
            params.append(raw_source_mode)

        where_sql = " AND ".join(where)
        raw_count = conn.execute(f"SELECT COUNT(*) FROM tick_stream WHERE {where_sql}", params).fetchone()[0]
        sql = f"SELECT {', '.join(select_cols)} FROM tick_stream WHERE {where_sql} ORDER BY ts_utc"
        raw_rows = [dict(zip(select_cols, row)) for row in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

    seen = set()
    dedup = []
    for row in raw_rows:
        key = (row.get("ts_utc"), row.get("bid"), row.get("ask"), row.get("mid"), row.get("spread"))
        if key in seen:
            continue
        seen.add(key)
        dedup.append(row)

    return dedup, int(raw_count)


# Override V5 reader so the V5-compatible calibration can see optional volume columns.
_t0103_read_raw_rows = _t0105_read_raw_rows_with_activity


def _t0105_enrich_raw_activity(out, moment, cfg, rows, start, end, raw_delta, raw_range):
    pip_size = float(getattr(cfg, "pip_size", 0.0001) or 0.0001)
    duration_seconds = _t0105_duration_seconds(start, end)
    dedup_count = int(out.get("raw_tick_count_dedup", out.get("raw_tick_count", len(rows))) or 0)
    gaps = _t0105_compute_gaps_ms(rows)

    density_second = (dedup_count / duration_seconds) if duration_seconds > 0 else None
    density_minute = density_second * 60.0 if density_second is not None else None

    out["b9_dwell_seconds"] = round(duration_seconds, 3)
    out["b9_microfilm_duration_seconds"] = round(duration_seconds, 3)
    out["b9_compression_seconds"] = round(duration_seconds, 3) if "COMPRESSION" in str(moment.get("moment_type", "")).upper() else None
    out["b9_release_seconds"] = round(duration_seconds, 3) if ("PROGRESSIVE" in str(moment.get("moment_type", "")).upper() or abs(raw_delta or 0.0) >= 4.0) else None
    out["b9_retest_delay_seconds"] = None
    out["b9_center_migration_speed_pips_per_min"] = _t0105_safe_round((raw_delta / duration_seconds) * 60.0 if duration_seconds > 0 else None, 6)

    out["raw_tick_density_per_second"] = _t0105_safe_round(density_second, 6)
    out["raw_tick_density_per_minute"] = _t0105_safe_round(density_minute, 4)
    out["raw_gap_count"] = len(gaps)
    out["raw_gap_median_ms"] = _t0105_safe_round(_t0105_median(gaps) if gaps else None, 3)
    out["raw_gap_mean_ms"] = _t0105_safe_round(_t0105_mean(gaps) if gaps else None, 3)
    out["raw_gap_max_ms"] = _t0105_safe_round(max(gaps) if gaps else None, 3)
    out["raw_activity_profile"] = _t0105_activity_profile(dedup_count, duration_seconds, gaps)
    out["raw_activity_regime"] = out["raw_activity_profile"]

    out.update(_t0105_spread_metrics(rows, pip_size))
    out.update(_t0105_volume_metrics(rows, duration_seconds))

    out["raw_activity_limits"] = [
        "tick density is broker-relative",
        "MT5 volume is experimental if present",
        "spread stability is a texture filter, not a decision",
        "no global Forex volume claim",
    ]
    return out


def _t0103_calibrate_one_moment(moment, cfg):
    out = dict(moment)
    start = _t0103_parse_dt(moment.get("time_start"))
    end = _t0103_parse_dt(moment.get("time_end"))
    shift = int(getattr(cfg, "broker_time_shift_min", 0) or 0)
    pip_size = float(getattr(cfg, "pip_size", 0.0001) or 0.0001)

    out["raw_source_mode"] = getattr(cfg, "raw_source_mode", "HISTORICAL_RAW")
    out["raw_data_visibility"] = getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED")
    out["raw_broker"] = getattr(cfg, "broker", "UNKNOWN")
    out["raw_time_shift_min"] = shift
    out["raw_dedup_mode"] = "DISTINCT_TS_BID_ASK_MID_SPREAD"
    out["b9_intrinsic_temporality_scope"] = "MICROFILM_INTERNAL_ONLY"
    out["external_temporality_dependency"] = False

    if start is None or end is None:
        out.update({
            "raw_coverage": "RAW_UNAVAILABLE",
            "proxy_vs_raw_verdict": "RAW_UNAVAILABLE",
            "raw_texture_role": "RAW_UNAVAILABLE",
            "raw_tick_count": 0,
            "raw_tick_count_raw": 0,
            "raw_tick_count_dedup": 0,
            "raw_duplicate_count": 0,
            "raw_duplicate_ratio": 0.0,
            "raw_activity_profile": "RAW_ACTIVITY_UNKNOWN",
            "raw_spread_stability_state": "SPREAD_UNKNOWN",
            "raw_volume_visibility_state": "VOLUME_NOT_PRESENT",
        })
        return out

    zero_duration = end <= start
    effective_end = end
    if zero_duration:
        effective_end = start + _T0103Timedelta(seconds=1)

    raw_start = start - _T0103Timedelta(minutes=shift)
    raw_end = effective_end - _T0103Timedelta(minutes=shift)
    out["raw_window_start_mt5"] = _t0103_fmt_dt(raw_start)
    out["raw_window_end_mt5"] = _t0103_fmt_dt(raw_end)

    rows, raw_count = _t0103_read_raw_rows(cfg, raw_start, raw_end)
    dedup_count = len(rows)
    duplicate_count = max(0, raw_count - dedup_count)
    duplicate_ratio = (duplicate_count / raw_count) if raw_count else 0.0

    mids = [_t0103_mid(r) for r in rows]
    mids = [m for m in mids if m is not None]

    out["raw_tick_count_raw"] = raw_count
    out["raw_tick_count_dedup"] = dedup_count
    out["raw_tick_count"] = dedup_count
    out["raw_duplicate_count"] = duplicate_count
    out["raw_duplicate_ratio"] = round(duplicate_ratio, 6)

    if not mids:
        out["raw_delta_pips"] = 0.0
        out["raw_range_pips"] = 0.0
        out["raw_coverage"] = "RAW_UNAVAILABLE"
        out["proxy_vs_raw_verdict"] = "RAW_UNAVAILABLE"
        out["raw_texture_role"] = "RAW_UNAVAILABLE"
        out["progressive_wave_state"] = out.get("progressive_wave_state") or "RAW_UNAVAILABLE"
        out = _t0105_enrich_raw_activity(out, moment, cfg, rows, start, effective_end, 0.0, 0.0)
        return out

    raw_delta = (mids[-1] - mids[0]) / pip_size
    raw_range = (max(mids) - min(mids)) / pip_size
    out["raw_delta_pips"] = round(raw_delta, 4)
    out["raw_range_pips"] = round(raw_range, 4)
    out["raw_coverage"] = "PARTIAL" if zero_duration else "FULL"

    out = _t0105_enrich_raw_activity(out, moment, cfg, rows, start, effective_end, raw_delta, raw_range)

    if zero_duration:
        out["zero_duration_status"] = "ZERO_DURATION_MOMENT"
        out["proxy_vs_raw_verdict"] = "ZERO_DURATION_MOMENT"
        out["raw_texture_role"] = "ZERO_DURATION_MOMENT"
        return out

    proxy_delta = _t0103_proxy_delta(moment)
    moment_type = str(moment.get("moment_type", "")).upper()
    same_sign = proxy_delta is not None and ((proxy_delta >= 0 and raw_delta >= 0) or (proxy_delta <= 0 and raw_delta <= 0))
    spread_state = out.get("raw_spread_stability_state")
    activity_state = out.get("raw_activity_profile")

    if "PROGRESSIVE" in moment_type:
        if spread_state == "SPREAD_UNSTABLE":
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_SPREAD_UNSTABLE"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_SPREAD_UNSTABLE"
        elif activity_state in {"RAW_ACTIVITY_THIN", "RAW_ACTIVITY_GAPPY"}:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_THIN_OR_GAPPY_ACTIVITY"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_THIN_ACTIVITY"
        elif abs(raw_delta) >= 4.0 and same_sign:
            out["proxy_vs_raw_verdict"] = "CONFIRMED_BY_RAW"
            out["raw_texture_role"] = "RAW_PROGRESS_CONFIRMED"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_CONFIRMED"
        elif raw_range >= 4.0 and abs(raw_delta) < max(3.0, raw_range * 0.35):
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_ROTATION_CONFIRMED"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_ROTATIONAL"
        else:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_PROXY_DIVERGENCE" if proxy_delta is not None and not same_sign else "RAW_WEAK_PROGRESS"
            out["progressive_wave_state"] = "PROGRESSIVE_WAVE_WEAK_RAW"
    else:
        if proxy_delta is not None and same_sign and abs(raw_delta) >= 2.0:
            out["proxy_vs_raw_verdict"] = "CONFIRMED_BY_RAW"
            out["raw_texture_role"] = "RAW_PROGRESS_CONFIRMED"
        elif raw_range >= 4.0:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_ROTATION_CONFIRMED"
        else:
            out["proxy_vs_raw_verdict"] = "NUANCED_BY_RAW"
            out["raw_texture_role"] = "RAW_FRICTION_CONFIRMED"

    return out


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0105_RAW_ACTIVITY_METRICS_V0",
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "raw_dedup_mode": "DISTINCT_TS_BID_ASK_MID_SPREAD",
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "raw_activity_metrics": [
            "raw_tick_density_per_second",
            "raw_gap_median_ms",
            "raw_gap_max_ms",
            "raw_spread_stability_state",
            "raw_volume_visibility_state",
            "b9_dwell_seconds",
            "b9_center_migration_speed_pips_per_min",
        ],
        "limits": [
            "raw tick broker-relative",
            "MT5 volume experimental and broker-relative if present",
            "no external Temporalité dependency",
            "no central FX footprint claimed",
        ],
    })
    return payload
# --- T0105_B9_RAW_ACTIVITY_METRICS_V0_END ---

# --- T0106_B9_DIRECT_RAW_FACTORS_V0_START ---
# Direct B9 factor integration V0.
# This is not the B6 Lab and not the external Temporalité brick.
# It enriches B9 moments directly with internal temporal / raw / spread / volume factors.

_T0106_PREVIOUS_CALIBRATE_ONE_MOMENT = _t0103_calibrate_one_moment


def _t0106_clamp(value, low=0.0, high=1.0):
    try:
        value = float(value)
    except Exception:
        return low
    return max(low, min(high, value))


def _t0106_num(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _t0106_temporal_pressure_state(out):
    dwell = _t0106_num(out.get("b9_dwell_seconds"), 0.0) or 0.0
    verdict = str(out.get("proxy_vs_raw_verdict", ""))

    if verdict == "ZERO_DURATION_MOMENT" or dwell <= 0:
        return "TEMPORAL_ZERO_DURATION_ARTIFACT"
    if dwell <= 60:
        return "TEMPORAL_SHORT_IMPULSE"
    if dwell <= 300:
        return "TEMPORAL_ACTIVE_MICROFILM"
    if dwell <= 900:
        return "TEMPORAL_EXTENDED_DWELL"
    return "TEMPORAL_LONG_COMPRESSION_OR_ROTATION"


def _t0106_activity_factor(out):
    profile = str(out.get("raw_activity_profile") or "RAW_ACTIVITY_UNKNOWN")
    mapping = {
        "RAW_ACTIVITY_BURST": "ACTIVITY_BURST",
        "RAW_ACTIVITY_DENSE": "ACTIVITY_DENSE",
        "RAW_ACTIVITY_NORMAL": "ACTIVITY_NORMAL",
        "RAW_ACTIVITY_THIN": "ACTIVITY_THIN_LIMIT",
        "RAW_ACTIVITY_GAPPY": "ACTIVITY_GAPPY_LIMIT",
        "RAW_ACTIVITY_UNKNOWN": "ACTIVITY_UNKNOWN",
    }
    return mapping.get(profile, "ACTIVITY_UNKNOWN")


def _t0106_spread_factor(out):
    spread = str(out.get("raw_spread_stability_state") or "SPREAD_UNKNOWN")
    mapping = {
        "SPREAD_STABLE": "SPREAD_CLEAN",
        "SPREAD_EXPANDING": "SPREAD_EXPANDING_CAUTION",
        "SPREAD_UNSTABLE": "SPREAD_UNSTABLE_LIMIT",
        "SPREAD_THIN_DATA": "SPREAD_THIN_DATA_LIMIT",
        "SPREAD_UNKNOWN": "SPREAD_UNKNOWN",
    }
    return mapping.get(spread, "SPREAD_UNKNOWN")


def _t0106_volume_factor(out):
    visibility = str(out.get("raw_volume_visibility_state") or "VOLUME_NOT_PRESENT")
    density = _t0106_num(out.get("raw_tick_volume_density"), None)

    if visibility == "VOLUME_NOT_PRESENT":
        return "VOLUME_ABSENT"
    if density is None:
        return "VOLUME_VISIBLE_BROKER_RELATIVE_NO_DENSITY"
    if density <= 0:
        return "VOLUME_VISIBLE_BROKER_RELATIVE_EMPTY"
    if density < 0.5:
        return "VOLUME_VISIBLE_BROKER_RELATIVE_THIN"
    if density < 5.0:
        return "VOLUME_VISIBLE_BROKER_RELATIVE_NORMAL"
    return "VOLUME_VISIBLE_BROKER_RELATIVE_ACTIVE"


def _t0106_center_speed_factor(out):
    speed = abs(_t0106_num(out.get("b9_center_migration_speed_pips_per_min"), 0.0) or 0.0)
    if speed <= 0:
        return "CENTER_SPEED_FLAT_OR_UNKNOWN"
    if speed < 0.5:
        return "CENTER_SPEED_SLOW"
    if speed < 2.0:
        return "CENTER_SPEED_ACTIVE"
    if speed < 5.0:
        return "CENTER_SPEED_FAST"
    return "CENTER_SPEED_EXTREME"


def _t0106_microfilm_texture_score(out):
    score = 0.50

    coverage = str(out.get("raw_coverage") or "")
    verdict = str(out.get("proxy_vs_raw_verdict") or "")
    activity = str(out.get("raw_activity_profile") or "")
    spread = str(out.get("raw_spread_stability_state") or "")
    volume = str(out.get("raw_volume_visibility_state") or "")
    texture = str(out.get("raw_texture_role") or "")

    if coverage == "FULL":
        score += 0.10
    elif coverage == "PARTIAL":
        score -= 0.05
    elif coverage == "RAW_UNAVAILABLE":
        score -= 0.25

    if verdict == "CONFIRMED_BY_RAW":
        score += 0.12
    elif verdict == "NUANCED_BY_RAW":
        score += 0.02
    elif verdict == "ZERO_DURATION_MOMENT":
        score -= 0.35

    if activity in {"RAW_ACTIVITY_DENSE", "RAW_ACTIVITY_BURST"}:
        score += 0.10
    elif activity == "RAW_ACTIVITY_NORMAL":
        score += 0.03
    elif activity in {"RAW_ACTIVITY_THIN", "RAW_ACTIVITY_GAPPY"}:
        score -= 0.15

    if spread == "SPREAD_STABLE":
        score += 0.08
    elif spread == "SPREAD_EXPANDING":
        score -= 0.03
    elif spread == "SPREAD_UNSTABLE":
        score -= 0.18
    elif spread == "SPREAD_THIN_DATA":
        score -= 0.10

    if volume == "VOLUME_PRESENT_BROKER_RELATIVE":
        score += 0.03

    if texture in {"RAW_PROXY_DIVERGENCE", "RAW_WEAK_PROGRESS", "RAW_THIN_OR_GAPPY_ACTIVITY", "RAW_SPREAD_UNSTABLE"}:
        score -= 0.10

    return round(_t0106_clamp(score), 4)


def _t0106_quality_state(score, out):
    verdict = str(out.get("proxy_vs_raw_verdict") or "")
    if verdict == "ZERO_DURATION_MOMENT":
        return "MICROFILM_ARTIFACT"
    if score >= 0.75:
        return "MICROFILM_TEXTURE_HIGH"
    if score >= 0.55:
        return "MICROFILM_TEXTURE_MEDIUM"
    if score >= 0.35:
        return "MICROFILM_TEXTURE_LOW"
    return "MICROFILM_TEXTURE_LIMITED"


def _t0106_profile(out):
    verdict = str(out.get("proxy_vs_raw_verdict") or "")
    prog = str(out.get("progressive_wave_state") or "")
    activity = str(out.get("raw_activity_profile") or "")
    spread = str(out.get("raw_spread_stability_state") or "")
    texture = str(out.get("raw_texture_role") or "")

    if verdict == "ZERO_DURATION_MOMENT":
        return "ZERO_DURATION_ARTIFACT"
    if spread == "SPREAD_UNSTABLE":
        return "SPREAD_UNSTABLE_MICROFILM"
    if activity == "RAW_ACTIVITY_GAPPY":
        return "GAPPY_MICROFILM_LIMIT"
    if "ROTATIONAL" in prog:
        return "PROGRESSIVE_ROTATIONAL_TRAP"
    if "WEAK_RAW" in prog:
        return "WEAK_RAW_PROGRESS"
    if "CONFIRMED" in prog and verdict == "CONFIRMED_BY_RAW":
        return "CLEAN_PROGRESSIVE_MICROFILM"
    if texture == "RAW_ROTATION_CONFIRMED":
        return "ROTATIONAL_MICROFILM"
    if texture == "RAW_PROGRESS_CONFIRMED":
        return "RAW_CONFIRMED_MICROFILM"
    return "MIXED_MICROFILM"


def _t0106_flags(out):
    flags = []

    if str(out.get("proxy_vs_raw_verdict")) == "ZERO_DURATION_MOMENT":
        flags.append("ZERO_DURATION_ARTIFACT")
    if str(out.get("raw_activity_profile")) == "RAW_ACTIVITY_GAPPY":
        flags.append("GAPPY_RAW_CADENCE")
    if str(out.get("raw_activity_profile")) == "RAW_ACTIVITY_THIN":
        flags.append("THIN_RAW_ACTIVITY")
    if str(out.get("raw_spread_stability_state")) == "SPREAD_UNSTABLE":
        flags.append("SPREAD_UNSTABLE")
    if str(out.get("raw_spread_stability_state")) == "SPREAD_EXPANDING":
        flags.append("SPREAD_EXPANDING")
    if str(out.get("raw_volume_visibility_state")) == "VOLUME_PRESENT_BROKER_RELATIVE":
        flags.append("VOLUME_BROKER_RELATIVE_VISIBLE")
    if str(out.get("progressive_wave_state")) == "PROGRESSIVE_WAVE_ROTATIONAL":
        flags.append("PROGRESSIVE_ROTATIONAL_TRAP")
    if str(out.get("progressive_wave_state")) == "PROGRESSIVE_WAVE_WEAK_RAW":
        flags.append("PROGRESSIVE_WEAK_RAW")
    if abs(_t0106_num(out.get("b9_center_migration_speed_pips_per_min"), 0.0) or 0.0) >= 2.0:
        flags.append("FAST_CENTER_MIGRATION")
    if not flags:
        flags.append("NO_MAJOR_RAW_FACTOR_LIMIT")
    return flags


def _t0106_apply_direct_factors(out):
    out["b9_direct_factor_version"] = "T0106_DIRECT_RAW_FACTORS_V0"
    out["b9_temporal_pressure_state"] = _t0106_temporal_pressure_state(out)
    out["b9_raw_activity_factor"] = _t0106_activity_factor(out)
    out["b9_spread_factor"] = _t0106_spread_factor(out)
    out["b9_volume_factor_state"] = _t0106_volume_factor(out)
    out["b9_center_speed_factor"] = _t0106_center_speed_factor(out)

    score = _t0106_microfilm_texture_score(out)
    out["b9_microfilm_texture_score"] = score
    out["b9_microfilm_quality_state"] = _t0106_quality_state(score, out)
    out["b9_microfilm_profile"] = _t0106_profile(out)
    out["b9_factor_flags"] = _t0106_flags(out)

    out["b9_volume_use_policy"] = "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL"
    out["b9_temporality_policy"] = "INTRINSIC_MICROFILM_TIME_ONLY_NO_EXTERNAL_TEMPORALITE"
    out["b9_direct_factor_limits"] = [
        "temporal factor is B9 intrinsic microfilm time only",
        "MT5 volume is broker-relative and experimental",
        "spread and activity are texture filters, not trade decisions",
        "no global Forex volume claim",
        "no BUY/SELL language",
    ]
    return out


def _t0103_calibrate_one_moment(moment, cfg):
    out = _T0106_PREVIOUS_CALIBRATE_ONE_MOMENT(moment, cfg)
    return _t0106_apply_direct_factors(out)


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0106_DIRECT_RAW_FACTORS_V0",
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "direct_factors": [
            "b9_temporal_pressure_state",
            "b9_raw_activity_factor",
            "b9_spread_factor",
            "b9_volume_factor_state",
            "b9_center_speed_factor",
            "b9_microfilm_texture_score",
            "b9_microfilm_profile",
            "b9_factor_flags",
        ],
        "limits": [
            "direct factors are interpretability factors, not trading signals",
            "MT5 volume is not global Forex volume",
            "external Temporalité brick is not used",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0106_B9_DIRECT_RAW_FACTORS_V0_END ---

# --- T0107_B9_NATURAL_FLOW_READING_V0_START ---
# B9 Natural Flow Reading V0.
# Inspired by generic order-flow / auction-reading principles:
# effort vs result, initiative vs response, absorption-like friction,
# rotation vs displacement, exhaustion, and trap texture.
# This is an adaptation for PowerFlow B9, not a DeltaRiver clone.
# No trading decision, no BUY/SELL, no dashboard mutation, no DB write.

_T0107_PREVIOUS_CALIBRATE_ONE_MOMENT = _t0103_calibrate_one_moment


def _t0107_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _t0107_str(value):
    return "" if value is None else str(value)


def _t0107_clamp(value, low=0.0, high=1.0):
    try:
        value = float(value)
    except Exception:
        return low
    return max(low, min(high, value))


def _t0107_effort_result_ratio(out):
    ticks = max(0.0, _t0107_float(out.get("raw_tick_count_dedup", out.get("raw_tick_count")), 0.0))
    dwell = max(1.0, _t0107_float(out.get("b9_dwell_seconds"), 1.0))
    raw_delta = abs(_t0107_float(out.get("raw_delta_pips"), 0.0))
    raw_range = max(0.000001, abs(_t0107_float(out.get("raw_range_pips"), 0.0)))
    density = ticks / dwell

    # High effort with low directional result means friction / absorption-like texture.
    directional_efficiency = raw_delta / raw_range
    effort_load = density * raw_range
    return {
        "b9_directional_efficiency": round(_t0107_clamp(directional_efficiency), 4),
        "b9_effort_load": round(effort_load, 6),
        "b9_effort_result_ratio": round(effort_load / max(0.25, raw_delta), 6),
    }


def _t0107_flow_intent_state(out):
    verdict = _t0107_str(out.get("proxy_vs_raw_verdict"))
    texture = _t0107_str(out.get("raw_texture_role"))
    profile = _t0107_str(out.get("b9_microfilm_profile"))
    activity = _t0107_str(out.get("raw_activity_profile"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    efficiency = _t0107_float(out.get("b9_directional_efficiency"), 0.0)
    raw_delta = abs(_t0107_float(out.get("raw_delta_pips"), 0.0))
    raw_range = abs(_t0107_float(out.get("raw_range_pips"), 0.0))

    if verdict == "ZERO_DURATION_MOMENT" or profile == "ZERO_DURATION_ARTIFACT":
        return "FLOW_ARTIFACT"
    if spread == "SPREAD_UNSTABLE":
        return "FLOW_UNSTABLE_QUOTE_TEXTURE"
    if activity == "RAW_ACTIVITY_GAPPY":
        return "FLOW_GAPPY_LIMIT"
    if "ROTATIONAL" in profile or texture == "RAW_ROTATION_CONFIRMED" or efficiency < 0.35 and raw_range >= 4.0:
        return "FLOW_ROTATIONAL"
    if "WEAK_RAW" in profile or texture == "RAW_WEAK_PROGRESS":
        return "FLOW_WEAK_DIRECTIONAL"
    if verdict == "CONFIRMED_BY_RAW" and raw_delta >= 4.0 and efficiency >= 0.55:
        return "FLOW_DIRECTIONAL_DISPLACEMENT"
    if raw_range >= 6.0 and efficiency < 0.45:
        return "FLOW_BALANCED_AUCTION"
    return "FLOW_MIXED"


def _t0107_absorption_like_state(out):
    efficiency = _t0107_float(out.get("b9_directional_efficiency"), 0.0)
    effort_ratio = _t0107_float(out.get("b9_effort_result_ratio"), 0.0)
    raw_range = abs(_t0107_float(out.get("raw_range_pips"), 0.0))
    raw_delta = abs(_t0107_float(out.get("raw_delta_pips"), 0.0))
    activity = _t0107_str(out.get("raw_activity_profile"))
    texture = _t0107_str(out.get("raw_texture_role"))

    if raw_range < 2.0:
        return "ABSORPTION_NOT_ENOUGH_RANGE"
    if activity in {"RAW_ACTIVITY_THIN", "RAW_ACTIVITY_GAPPY"}:
        return "ABSORPTION_UNREADABLE_ACTIVITY_LIMIT"
    if texture == "RAW_ROTATION_CONFIRMED" and efficiency < 0.35:
        return "ABSORPTION_LIKE_ROTATIONAL_FRICTION"
    if effort_ratio >= 2.5 and raw_delta <= max(2.0, raw_range * 0.30):
        return "ABSORPTION_LIKE_EFFORT_WITHOUT_RESULT"
    if effort_ratio >= 1.5 and efficiency < 0.45:
        return "ABSORPTION_LIKE_PARTIAL_FRICTION"
    return "ABSORPTION_NOT_DETECTED"


def _t0107_exhaustion_like_state(out):
    raw_delta = abs(_t0107_float(out.get("raw_delta_pips"), 0.0))
    raw_range = abs(_t0107_float(out.get("raw_range_pips"), 0.0))
    speed = abs(_t0107_float(out.get("b9_center_migration_speed_pips_per_min"), 0.0))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    activity = _t0107_str(out.get("raw_activity_profile"))
    efficiency = _t0107_float(out.get("b9_directional_efficiency"), 0.0)

    if raw_range < 4.0:
        return "EXHAUSTION_NOT_ENOUGH_RANGE"
    if spread == "SPREAD_UNSTABLE" and raw_delta >= 3.0:
        return "EXHAUSTION_LIKE_SPREAD_STRESS"
    if speed >= 2.0 and efficiency < 0.45:
        return "EXHAUSTION_LIKE_FAST_BUT_INEFFICIENT"
    if activity == "RAW_ACTIVITY_GAPPY" and raw_range >= 6.0:
        return "EXHAUSTION_UNREADABLE_GAPPY_LIMIT"
    return "EXHAUSTION_NOT_DETECTED"


def _t0107_initiative_response_state(out):
    dwell = _t0107_float(out.get("b9_dwell_seconds"), 0.0)
    raw_delta = abs(_t0107_float(out.get("raw_delta_pips"), 0.0))
    speed = abs(_t0107_float(out.get("b9_center_migration_speed_pips_per_min"), 0.0))
    efficiency = _t0107_float(out.get("b9_directional_efficiency"), 0.0)
    profile = _t0107_str(out.get("b9_microfilm_profile"))

    if profile == "ZERO_DURATION_ARTIFACT":
        return "INIT_RESPONSE_ARTIFACT"
    if dwell <= 90 and raw_delta >= 4.0 and speed >= 1.0 and efficiency >= 0.50:
        return "INITIATIVE_DISPLACEMENT"
    if dwell >= 300 and raw_delta < 3.0:
        return "RESPONSIVE_BALANCING"
    if "ROTATIONAL" in profile:
        return "RESPONSIVE_ROTATION"
    if raw_delta >= 4.0:
        return "MIXED_INITIATIVE_RESPONSE"
    return "INIT_RESPONSE_NEUTRAL"


def _t0107_auction_state(out):
    flow = _t0107_str(out.get("b9_flow_intent_state"))
    absorption = _t0107_str(out.get("b9_absorption_like_state"))
    exhaustion = _t0107_str(out.get("b9_exhaustion_like_state"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    activity = _t0107_str(out.get("raw_activity_profile"))

    if flow == "FLOW_ARTIFACT":
        return "AUCTION_ARTIFACT"
    if activity == "RAW_ACTIVITY_GAPPY":
        return "AUCTION_READ_LIMIT_GAPPY"
    if spread == "SPREAD_UNSTABLE":
        return "AUCTION_READ_LIMIT_SPREAD"
    if absorption.startswith("ABSORPTION_LIKE"):
        return "AUCTION_FRICTION_ABSORPTION_LIKE"
    if exhaustion.startswith("EXHAUSTION_LIKE"):
        return "AUCTION_EXHAUSTION_LIKE"
    if flow == "FLOW_DIRECTIONAL_DISPLACEMENT":
        return "AUCTION_DIRECTIONAL_ACCEPTANCE"
    if flow in {"FLOW_ROTATIONAL", "FLOW_BALANCED_AUCTION"}:
        return "AUCTION_ROTATIONAL_BALANCE"
    return "AUCTION_MIXED"


def _t0107_trap_risk_state(out):
    profile = _t0107_str(out.get("b9_microfilm_profile"))
    flow = _t0107_str(out.get("b9_flow_intent_state"))
    absorption = _t0107_str(out.get("b9_absorption_like_state"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    activity = _t0107_str(out.get("raw_activity_profile"))

    if profile == "ZERO_DURATION_ARTIFACT":
        return "TRAP_RISK_ARTIFACT"
    if "ROTATIONAL_TRAP" in profile:
        return "TRAP_RISK_HIGH_PROGRESSIVE_ROTATIONAL"
    if "WEAK_RAW_PROGRESS" in profile:
        return "TRAP_RISK_HIGH_WEAK_RAW"
    if flow in {"FLOW_GAPPY_LIMIT", "FLOW_UNSTABLE_QUOTE_TEXTURE"}:
        return "TRAP_RISK_DATA_TEXTURE_LIMIT"
    if absorption.startswith("ABSORPTION_LIKE"):
        return "TRAP_RISK_MEDIUM_EFFORT_WITHOUT_RESULT"
    if spread == "SPREAD_EXPANDING" or activity == "RAW_ACTIVITY_GAPPY":
        return "TRAP_RISK_MEDIUM_TEXTURE_CAUTION"
    return "TRAP_RISK_LOW"


def _t0107_market_readability_state(out):
    score = _t0107_float(out.get("b9_microfilm_texture_score"), 0.0)
    activity = _t0107_str(out.get("raw_activity_profile"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    verdict = _t0107_str(out.get("proxy_vs_raw_verdict"))

    if verdict == "ZERO_DURATION_MOMENT":
        return "READABILITY_ARTIFACT"
    if activity == "RAW_ACTIVITY_GAPPY" or spread == "SPREAD_UNSTABLE":
        return "READABILITY_LIMITED_BY_TEXTURE"
    if score >= 0.75:
        return "READABILITY_HIGH"
    if score >= 0.55:
        return "READABILITY_MEDIUM"
    if score >= 0.35:
        return "READABILITY_LOW"
    return "READABILITY_VERY_LOW"


def _t0107_natural_flow_sentence(out):
    flow = _t0107_str(out.get("b9_flow_intent_state"))
    auction = _t0107_str(out.get("b9_auction_state"))
    trap = _t0107_str(out.get("b9_trap_risk_state"))
    read = _t0107_str(out.get("b9_market_readability_state"))

    if flow == "FLOW_DIRECTIONAL_DISPLACEMENT" and read in {"READABILITY_HIGH", "READABILITY_MEDIUM"}:
        return "Flux directionnel lisible: déplacement raw avec texture exploitable."
    if flow == "FLOW_ROTATIONAL":
        return "Flux rotationnel: mouvement visible mais résultat directionnel limité."
    if flow == "FLOW_GAPPY_LIMIT":
        return "Lecture limitée: cadence raw irrégulière."
    if flow == "FLOW_UNSTABLE_QUOTE_TEXTURE":
        return "Lecture limitée: spread instable."
    if trap.startswith("TRAP_RISK_HIGH"):
        return "Piège probable: le proxy peut surlire la progression."
    if auction == "AUCTION_FRICTION_ABSORPTION_LIKE":
        return "Friction type absorption: effort visible sans résultat directionnel propre."
    return "Flux mixte: conserver comme lecture de contexte, pas comme décision."


def _t0107_apply_natural_flow(out):
    ratios = _t0107_effort_result_ratio(out)
    out.update(ratios)

    out["b9_natural_flow_version"] = "T0107_NATURAL_FLOW_READING_V0"
    out["b9_flow_intent_state"] = _t0107_flow_intent_state(out)
    out["b9_absorption_like_state"] = _t0107_absorption_like_state(out)
    out["b9_exhaustion_like_state"] = _t0107_exhaustion_like_state(out)
    out["b9_initiative_response_state"] = _t0107_initiative_response_state(out)
    out["b9_auction_state"] = _t0107_auction_state(out)
    out["b9_trap_risk_state"] = _t0107_trap_risk_state(out)
    out["b9_market_readability_state"] = _t0107_market_readability_state(out)
    out["b9_natural_flow_reading_fr"] = _t0107_natural_flow_sentence(out)

    flags = list(out.get("b9_factor_flags") or [])
    for value in [
        out["b9_flow_intent_state"],
        out["b9_absorption_like_state"],
        out["b9_exhaustion_like_state"],
        out["b9_auction_state"],
        out["b9_trap_risk_state"],
    ]:
        if value and value not in flags:
            flags.append(value)
    out["b9_factor_flags"] = flags

    out["b9_natural_flow_policy"] = "INTERPRETATION_ONLY_NO_DECISION"
    out["b9_natural_flow_limits"] = [
        "adapted PowerFlow reading, not a DeltaRiver clone",
        "broker-relative raw and MT5 volume",
        "no global Forex footprint claim",
        "no external Temporalité dependency",
        "no BUY/SELL language",
    ]
    return out


def _t0103_calibrate_one_moment(moment, cfg):
    out = _T0107_PREVIOUS_CALIBRATE_ONE_MOMENT(moment, cfg)
    return _t0107_apply_natural_flow(out)


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0107_NATURAL_FLOW_READING_V0",
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "natural_flow_factors": [
            "b9_flow_intent_state",
            "b9_absorption_like_state",
            "b9_exhaustion_like_state",
            "b9_initiative_response_state",
            "b9_auction_state",
            "b9_trap_risk_state",
            "b9_market_readability_state",
            "b9_natural_flow_reading_fr",
        ],
        "inspiration_note": "generic order-flow / auction reading principles adapted to PowerFlow B9",
        "limits": [
            "interpretation-only",
            "not a DeltaRiver clone",
            "MT5 volume is not global Forex volume",
            "external Temporalité brick is not used",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0107_B9_NATURAL_FLOW_READING_V0_END ---

# --- T0107A_B9_NATURAL_FLOW_GAPPY_THRESHOLD_HOTFIX_START ---
# Hotfix: do not let a moderate raw gap dominate directional/rotational reading.
# T0105 currently marks any max gap >= 10s as RAW_ACTIVITY_GAPPY.
# For B9 natural flow, gappy becomes a hard flow limit only when material:
# - very large max gap,
# - very low density,
# - too few ticks,
# - or long microfilm with substantial gap.
# Moderate gaps remain visible in flags but do not erase effort/result reading.

def _t0107a_is_hard_gappy(out):
    activity = _t0107_str(out.get("raw_activity_profile"))
    if activity != "RAW_ACTIVITY_GAPPY":
        return False

    max_gap = _t0107_float(out.get("raw_gap_max_ms"), 0.0)
    density_minute = _t0107_float(out.get("raw_tick_density_per_minute"), 0.0)
    dwell = _t0107_float(out.get("b9_dwell_seconds"), 0.0)
    ticks = _t0107_float(out.get("raw_tick_count_dedup", out.get("raw_tick_count")), 0.0)

    if max_gap >= 60000:
        return True
    if density_minute > 0 and density_minute <= 3.0:
        return True
    if ticks > 0 and ticks <= 3:
        return True
    if dwell >= 600 and max_gap >= 30000:
        return True
    return False


def _t0107_flow_intent_state(out):
    verdict = _t0107_str(out.get("proxy_vs_raw_verdict"))
    texture = _t0107_str(out.get("raw_texture_role"))
    profile = _t0107_str(out.get("b9_microfilm_profile"))
    activity = _t0107_str(out.get("raw_activity_profile"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    efficiency = _t0107_float(out.get("b9_directional_efficiency"), 0.0)
    raw_delta = abs(_t0107_float(out.get("raw_delta_pips"), 0.0))
    raw_range = abs(_t0107_float(out.get("raw_range_pips"), 0.0))

    if verdict == "ZERO_DURATION_MOMENT" or profile == "ZERO_DURATION_ARTIFACT":
        return "FLOW_ARTIFACT"
    if spread == "SPREAD_UNSTABLE":
        return "FLOW_UNSTABLE_QUOTE_TEXTURE"
    if _t0107a_is_hard_gappy(out):
        return "FLOW_GAPPY_LIMIT"
    if "ROTATIONAL" in profile or texture == "RAW_ROTATION_CONFIRMED" or (efficiency < 0.35 and raw_range >= 4.0):
        return "FLOW_ROTATIONAL"
    if "WEAK_RAW" in profile or texture == "RAW_WEAK_PROGRESS":
        return "FLOW_WEAK_DIRECTIONAL"
    if verdict == "CONFIRMED_BY_RAW" and raw_delta >= 4.0 and efficiency >= 0.55:
        return "FLOW_DIRECTIONAL_DISPLACEMENT"
    if raw_range >= 6.0 and efficiency < 0.45:
        return "FLOW_BALANCED_AUCTION"
    if activity == "RAW_ACTIVITY_GAPPY":
        return "FLOW_MIXED"
    return "FLOW_MIXED"


def _t0107_auction_state(out):
    flow = _t0107_str(out.get("b9_flow_intent_state"))
    absorption = _t0107_str(out.get("b9_absorption_like_state"))
    exhaustion = _t0107_str(out.get("b9_exhaustion_like_state"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))

    if flow == "FLOW_ARTIFACT":
        return "AUCTION_ARTIFACT"
    if flow == "FLOW_GAPPY_LIMIT":
        return "AUCTION_READ_LIMIT_GAPPY"
    if spread == "SPREAD_UNSTABLE":
        return "AUCTION_READ_LIMIT_SPREAD"
    if absorption.startswith("ABSORPTION_LIKE"):
        return "AUCTION_FRICTION_ABSORPTION_LIKE"
    if exhaustion.startswith("EXHAUSTION_LIKE"):
        return "AUCTION_EXHAUSTION_LIKE"
    if flow == "FLOW_DIRECTIONAL_DISPLACEMENT":
        return "AUCTION_DIRECTIONAL_ACCEPTANCE"
    if flow in {"FLOW_ROTATIONAL", "FLOW_BALANCED_AUCTION"}:
        return "AUCTION_ROTATIONAL_BALANCE"
    return "AUCTION_MIXED"


def _t0107_trap_risk_state(out):
    profile = _t0107_str(out.get("b9_microfilm_profile"))
    flow = _t0107_str(out.get("b9_flow_intent_state"))
    absorption = _t0107_str(out.get("b9_absorption_like_state"))
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    activity = _t0107_str(out.get("raw_activity_profile"))

    if profile == "ZERO_DURATION_ARTIFACT":
        return "TRAP_RISK_ARTIFACT"
    if "ROTATIONAL_TRAP" in profile:
        return "TRAP_RISK_HIGH_PROGRESSIVE_ROTATIONAL"
    if "WEAK_RAW_PROGRESS" in profile:
        return "TRAP_RISK_HIGH_WEAK_RAW"
    if flow in {"FLOW_GAPPY_LIMIT", "FLOW_UNSTABLE_QUOTE_TEXTURE"}:
        return "TRAP_RISK_DATA_TEXTURE_LIMIT"
    if absorption.startswith("ABSORPTION_LIKE"):
        return "TRAP_RISK_MEDIUM_EFFORT_WITHOUT_RESULT"
    if spread == "SPREAD_EXPANDING" or activity == "RAW_ACTIVITY_GAPPY":
        return "TRAP_RISK_MEDIUM_TEXTURE_CAUTION"
    return "TRAP_RISK_LOW"


def _t0107_market_readability_state(out):
    score = _t0107_float(out.get("b9_microfilm_texture_score"), 0.0)
    spread = _t0107_str(out.get("raw_spread_stability_state"))
    verdict = _t0107_str(out.get("proxy_vs_raw_verdict"))

    if verdict == "ZERO_DURATION_MOMENT":
        return "READABILITY_ARTIFACT"
    if _t0107a_is_hard_gappy(out) or spread == "SPREAD_UNSTABLE":
        return "READABILITY_LIMITED_BY_TEXTURE"
    if score >= 0.75:
        return "READABILITY_HIGH"
    if score >= 0.55:
        return "READABILITY_MEDIUM"
    if score >= 0.35:
        return "READABILITY_LOW"
    return "READABILITY_VERY_LOW"
# --- T0107A_B9_NATURAL_FLOW_GAPPY_THRESHOLD_HOTFIX_END ---

# --- T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_START ---
# B9 Natural Retest & FLOW_MIXED Split V0.
# This block refines natural flow reading without adding any decision language.
# It splits FLOW_MIXED into digestion / transition / friction / read-limit states
# and adds a natural retest reading based on B9 intrinsic microfilm factors.

_T0108_PREVIOUS_CALIBRATE_ONE_MOMENT = _t0103_calibrate_one_moment


def _t0108_s(value):
    return "" if value is None else str(value)


def _t0108_f(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _t0108_retest_source_state(moment_or_out):
    for key in ("retest_status", "retest_state", "zone_retest_status"):
        value = _t0108_s(moment_or_out.get(key)).upper()
        if value:
            return value
    return ""


def _t0108_mixed_split_state(out):
    flow = _t0108_s(out.get("b9_flow_intent_state"))
    auction = _t0108_s(out.get("b9_auction_state"))
    trap = _t0108_s(out.get("b9_trap_risk_state"))
    read = _t0108_s(out.get("b9_market_readability_state"))
    absorption = _t0108_s(out.get("b9_absorption_like_state"))
    exhaustion = _t0108_s(out.get("b9_exhaustion_like_state"))
    activity = _t0108_s(out.get("raw_activity_profile"))
    spread = _t0108_s(out.get("raw_spread_stability_state"))
    efficiency = _t0108_f(out.get("b9_directional_efficiency"))
    raw_range = abs(_t0108_f(out.get("raw_range_pips")))
    raw_delta = abs(_t0108_f(out.get("raw_delta_pips")))
    dwell = _t0108_f(out.get("b9_dwell_seconds"))

    if flow == "FLOW_ARTIFACT" or auction == "AUCTION_ARTIFACT":
        return "MIXED_SPLIT_ARTIFACT"
    if flow != "FLOW_MIXED":
        return "MIXED_SPLIT_NOT_MIXED"
    if read == "READABILITY_LIMITED_BY_TEXTURE" or activity == "RAW_ACTIVITY_GAPPY" or spread == "SPREAD_UNSTABLE":
        return "MIXED_SPLIT_READ_LIMIT"
    if trap.startswith("TRAP_RISK_HIGH"):
        return "MIXED_SPLIT_TRAP_RISK"
    if absorption.startswith("ABSORPTION_LIKE"):
        return "MIXED_SPLIT_FRICTION"
    if exhaustion.startswith("EXHAUSTION_LIKE"):
        return "MIXED_SPLIT_STRESS"
    if raw_range >= 6.0 and efficiency < 0.45:
        return "MIXED_SPLIT_BALANCED_AUCTION"
    if raw_delta >= 3.0 and efficiency >= 0.45:
        return "MIXED_SPLIT_TRANSITION"
    if dwell >= 300 and raw_delta < 3.0:
        return "MIXED_SPLIT_DIGESTION"
    return "MIXED_SPLIT_CONTEXT"


def _t0108_retest_natural_state(out):
    retest = _t0108_retest_source_state(out)
    flow = _t0108_s(out.get("b9_flow_intent_state"))
    auction = _t0108_s(out.get("b9_auction_state"))
    trap = _t0108_s(out.get("b9_trap_risk_state"))
    absorption = _t0108_s(out.get("b9_absorption_like_state"))
    activity = _t0108_s(out.get("raw_activity_profile"))
    spread = _t0108_s(out.get("raw_spread_stability_state"))
    raw_delta = abs(_t0108_f(out.get("raw_delta_pips")))
    raw_range = abs(_t0108_f(out.get("raw_range_pips")))
    efficiency = _t0108_f(out.get("b9_directional_efficiency"))

    if flow == "FLOW_ARTIFACT":
        return "RETEST_ARTIFACT"
    if spread == "SPREAD_UNSTABLE" or flow == "FLOW_GAPPY_LIMIT":
        return "RETEST_UNREADABLE_TEXTURE"
    if "FAILED" in retest or "REJECT" in retest:
        return "RETEST_REJECTED_OR_FAILED"
    if "ACCEPT" in retest or "VALID" in retest:
        if absorption.startswith("ABSORPTION_LIKE"):
            return "RETEST_ACCEPTED_WITH_FRICTION"
        return "RETEST_ACCEPTED"
    if "PENDING" in retest:
        if trap.startswith("TRAP_RISK_HIGH"):
            return "RETEST_PENDING_TRAP_RISK"
        if flow == "FLOW_DIRECTIONAL_DISPLACEMENT" and efficiency >= 0.50:
            return "RETEST_PENDING_AFTER_DISPLACEMENT"
        return "RETEST_PENDING_TEXTURE"
    if absorption.startswith("ABSORPTION_LIKE") and raw_range >= 4.0:
        return "RETEST_ABSORPTION_LIKE"
    if auction == "AUCTION_ROTATIONAL_BALANCE" and raw_range >= 4.0:
        return "RETEST_ROTATIONAL_BALANCE"
    if raw_delta >= 4.0 and efficiency >= 0.55:
        return "RETEST_NOT_VISIBLE_DIRECTIONAL_FLOW"
    return "RETEST_NOT_VISIBLE"


def _t0108_retest_quality_state(out):
    state = _t0108_s(out.get("b9_retest_natural_state"))
    read = _t0108_s(out.get("b9_market_readability_state"))
    score = _t0108_f(out.get("b9_microfilm_texture_score"))

    if state in {"RETEST_ARTIFACT"}:
        return "RETEST_QUALITY_ARTIFACT"
    if state in {"RETEST_UNREADABLE_TEXTURE"} or read == "READABILITY_LIMITED_BY_TEXTURE":
        return "RETEST_QUALITY_UNREADABLE"
    if state in {"RETEST_ACCEPTED"} and score >= 0.55:
        return "RETEST_QUALITY_CLEAN"
    if state in {"RETEST_ACCEPTED_WITH_FRICTION", "RETEST_ABSORPTION_LIKE", "RETEST_ROTATIONAL_BALANCE"}:
        return "RETEST_QUALITY_FRICTIONAL"
    if state in {"RETEST_PENDING_TRAP_RISK", "RETEST_REJECTED_OR_FAILED"}:
        return "RETEST_QUALITY_RISK"
    if state.startswith("RETEST_PENDING"):
        return "RETEST_QUALITY_PENDING"
    return "RETEST_QUALITY_NOT_APPLICABLE"


def _t0108_context_resolution_state(out):
    split = _t0108_s(out.get("b9_mixed_split_state"))
    retest = _t0108_s(out.get("b9_retest_natural_state"))
    flow = _t0108_s(out.get("b9_flow_intent_state"))
    auction = _t0108_s(out.get("b9_auction_state"))
    trap = _t0108_s(out.get("b9_trap_risk_state"))

    if "ARTIFACT" in split or "ARTIFACT" in retest:
        return "CONTEXT_ARTIFACT"
    if "UNREADABLE" in retest or split == "MIXED_SPLIT_READ_LIMIT":
        return "CONTEXT_READ_LIMIT"
    if trap.startswith("TRAP_RISK_HIGH") or split == "MIXED_SPLIT_TRAP_RISK":
        return "CONTEXT_TRAP_RISK"
    if retest in {"RETEST_ACCEPTED", "RETEST_ACCEPTED_WITH_FRICTION"}:
        return "CONTEXT_RETEST_ACCEPTANCE"
    if retest in {"RETEST_REJECTED_OR_FAILED"}:
        return "CONTEXT_RETEST_REJECTION"
    if auction == "AUCTION_DIRECTIONAL_ACCEPTANCE" or flow == "FLOW_DIRECTIONAL_DISPLACEMENT":
        return "CONTEXT_DIRECTIONAL_ACCEPTANCE"
    if auction == "AUCTION_ROTATIONAL_BALANCE" or split == "MIXED_SPLIT_BALANCED_AUCTION":
        return "CONTEXT_ROTATIONAL_BALANCE"
    if split in {"MIXED_SPLIT_DIGESTION", "MIXED_SPLIT_CONTEXT"}:
        return "CONTEXT_DIGESTION"
    if split == "MIXED_SPLIT_TRANSITION":
        return "CONTEXT_TRANSITION"
    return "CONTEXT_MIXED"


def _t0108_reading_fr(out):
    split = _t0108_s(out.get("b9_mixed_split_state"))
    retest = _t0108_s(out.get("b9_retest_natural_state"))
    context = _t0108_s(out.get("b9_context_resolution_state"))

    if context == "CONTEXT_DIRECTIONAL_ACCEPTANCE":
        return "Lecture B9: déplacement accepté par la texture raw, sans transformer en signal."
    if context == "CONTEXT_ROTATIONAL_BALANCE":
        return "Lecture B9: équilibre rotationnel, le flux travaille plus qu'il ne déplace."
    if context == "CONTEXT_RETEST_ACCEPTANCE":
        return "Lecture B9: retest accepté ou accepté avec friction, à lire comme état de scène."
    if context == "CONTEXT_RETEST_REJECTION":
        return "Lecture B9: retest rejeté ou échoué, scène à risque de surlecture."
    if context == "CONTEXT_TRAP_RISK":
        return "Lecture B9: risque de piège, le proxy peut surlire la progression."
    if context == "CONTEXT_READ_LIMIT":
        return "Lecture B9 limitée par la texture raw, cadence ou spread."
    if split == "MIXED_SPLIT_TRANSITION":
        return "Lecture B9: flux en transition, ni équilibre pur ni déplacement pleinement propre."
    if split == "MIXED_SPLIT_DIGESTION":
        return "Lecture B9: digestion de microfilm, le temps travaille plus que le déplacement."
    if retest == "RETEST_PENDING_TEXTURE":
        return "Lecture B9: retest en attente, texture encore insuffisante pour qualifier."
    return "Lecture B9: contexte mixte, information utile mais non décisionnelle."


def _t0108_apply(out):
    out["b9_retest_mixed_split_version"] = "T0108_RETEST_MIXED_SPLIT_V0"
    out["b9_mixed_split_state"] = _t0108_mixed_split_state(out)
    out["b9_retest_natural_state"] = _t0108_retest_natural_state(out)
    out["b9_retest_quality_state"] = _t0108_retest_quality_state(out)
    out["b9_context_resolution_state"] = _t0108_context_resolution_state(out)
    out["b9_retest_mixed_reading_fr"] = _t0108_reading_fr(out)
    out["b9_retest_mixed_policy"] = "INTERPRETATION_ONLY_NO_DECISION"

    flags = list(out.get("b9_factor_flags") or [])
    for item in [
        out["b9_mixed_split_state"],
        out["b9_retest_natural_state"],
        out["b9_retest_quality_state"],
        out["b9_context_resolution_state"],
    ]:
        if item and item not in flags:
            flags.append(item)
    out["b9_factor_flags"] = flags

    out["b9_retest_mixed_limits"] = [
        "B9 intrinsic microfilm reading only",
        "no external Temporalité dependency",
        "no BUY/SELL language",
        "retest reading is interpretive, not predictive",
        "MT5 raw and volume remain broker-relative",
    ]
    return out


def _t0103_calibrate_one_moment(moment, cfg):
    out = _T0108_PREVIOUS_CALIBRATE_ONE_MOMENT(moment, cfg)
    return _t0108_apply(out)


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0108_RETEST_MIXED_SPLIT_V0",
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "retest_mixed_fields": [
            "b9_mixed_split_state",
            "b9_retest_natural_state",
            "b9_retest_quality_state",
            "b9_context_resolution_state",
            "b9_retest_mixed_reading_fr",
        ],
        "limits": [
            "interpretation-only",
            "retest reading is not a signal",
            "external Temporalité brick is not used",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_END ---

# --- T0108A_B9_RETEST_MIXED_METADATA_TEST_COMPAT_HOTFIX_START ---
# Hotfix: T0108 is an additive layer over T0107.
# The top raw_calibration.version is expected to become T0108_RETEST_MIXED_SPLIT_V0,
# but T0107 natural_flow_factors must remain visible for compatibility and traceability.

def _t0108a_natural_flow_factors():
    return [
        "b9_flow_intent_state",
        "b9_absorption_like_state",
        "b9_exhaustion_like_state",
        "b9_initiative_response_state",
        "b9_auction_state",
        "b9_trap_risk_state",
        "b9_market_readability_state",
        "b9_natural_flow_reading_fr",
    ]


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0108_RETEST_MIXED_SPLIT_V0",
        "parent_versions": [
            "T0107_NATURAL_FLOW_READING_V0",
            "T0107A_GAPPY_THRESHOLD_HOTFIX",
        ],
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "natural_flow_factors": _t0108a_natural_flow_factors(),
        "retest_mixed_fields": [
            "b9_mixed_split_state",
            "b9_retest_natural_state",
            "b9_retest_quality_state",
            "b9_context_resolution_state",
            "b9_retest_mixed_reading_fr",
        ],
        "limits": [
            "interpretation-only",
            "T0108 extends T0107; it does not erase natural flow fields",
            "retest reading is not a signal",
            "external Temporalité brick is not used",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0108A_B9_RETEST_MIXED_METADATA_TEST_COMPAT_HOTFIX_END ---

# --- T0109_B9_RETEST_SOURCE_SIGNALS_V0_START ---
# B9 Retest Source Signals V0.
# This block gives T0108 better retest material using B9 source fields
# plus raw-derived texture. It stays interpretive: no signal, no decision.

_T0109_PREVIOUS_CALIBRATE_ONE_MOMENT = _t0103_calibrate_one_moment


def _t0109_s(value):
    return "" if value is None else str(value)


def _t0109_f(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _t0109_i(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def _t0109_clamp(value, low=0.0, high=1.0):
    try:
        value = float(value)
    except Exception:
        return low
    return max(low, min(high, value))


def _t0109_upper_blob(*values):
    return " ".join(_t0109_s(v).upper() for v in values if _t0109_s(v))


def _t0109_zone_memory(out):
    zm = out.get("zone_memory")
    if isinstance(zm, dict):
        return zm
    return {}


def _t0109_first_present(mapping, keys):
    for key in keys:
        if key in mapping and mapping.get(key) not in (None, ""):
            return mapping.get(key)
    return None


def _t0109_retest_status_blob(out):
    zm = _t0109_zone_memory(out)
    values = [
        out.get("retest_status"),
        out.get("retest_state"),
        out.get("zone_retest_status"),
        out.get("memory_state"),
        zm.get("retest_status"),
        zm.get("last_retest_status"),
        zm.get("state"),
    ]
    return _t0109_upper_blob(*values)


def _t0109_touch_count(out):
    zm = _t0109_zone_memory(out)
    candidates = [
        out.get("retest_touch_count"),
        out.get("zone_touch_count"),
        out.get("touch_count"),
        out.get("test_count"),
        zm.get("retest_touch_count"),
        zm.get("zone_touch_count"),
        zm.get("touch_count"),
        zm.get("test_count"),
        zm.get("retest_count"),
        zm.get("tests"),
    ]
    return max([_t0109_i(v, 0) for v in candidates] + [0])


def _t0109_seconds_between(a, b):
    try:
        da = _t0103_parse_dt(a)
        db = _t0103_parse_dt(b)
        if da is None or db is None:
            return None
        return round((db - da).total_seconds(), 3)
    except Exception:
        return None


def _t0109_delay_seconds(out):
    zm = _t0109_zone_memory(out)
    start = out.get("time_start")
    candidates = [
        out.get("last_tested"),
        out.get("last_retest_time"),
        out.get("retest_time"),
        zm.get("last_tested"),
        zm.get("last_retest_time"),
        zm.get("last_seen"),
    ]
    for value in candidates:
        if value:
            delta = _t0109_seconds_between(value, start)
            if delta is not None:
                return delta
    return None


def _t0109_source_status(out):
    blob = _t0109_retest_status_blob(out)
    natural = _t0109_s(out.get("b9_retest_natural_state"))

    if "FAILED" in blob or "FAIL" in blob or "REJECT" in blob or "INVALID" in blob:
        return "RETEST_SOURCE_REJECTED_EXPLICIT"
    if "ACCEPT" in blob or "VALID" in blob or "CONFIRM" in blob:
        return "RETEST_SOURCE_ACCEPTED_EXPLICIT"
    if "PENDING" in blob or "WAIT" in blob or "WATCH" in blob:
        return "RETEST_SOURCE_PENDING_EXPLICIT"
    if natural in {"RETEST_ACCEPTED", "RETEST_ACCEPTED_WITH_FRICTION"}:
        return "RETEST_SOURCE_ACCEPTED_INFERRED"
    if natural in {"RETEST_REJECTED_OR_FAILED"}:
        return "RETEST_SOURCE_REJECTED_INFERRED"
    if natural in {"RETEST_ABSORPTION_LIKE", "RETEST_ROTATIONAL_BALANCE"}:
        return "RETEST_SOURCE_FRICTION_INFERRED"
    if natural.startswith("RETEST_PENDING"):
        return "RETEST_SOURCE_PENDING_INFERRED"
    return "RETEST_SOURCE_NOT_VISIBLE"


def _t0109_visibility(out):
    status = _t0109_s(out.get("b9_retest_source_status"))
    touches = _t0109_touch_count(out)
    delay = _t0109_delay_seconds(out)
    natural = _t0109_s(out.get("b9_retest_natural_state"))
    raw_ticks = _t0109_i(out.get("raw_tick_count_dedup", out.get("raw_tick_count")), 0)

    if status.endswith("EXPLICIT"):
        return "RETEST_VISIBILITY_HIGH"
    if touches >= 2 and raw_ticks >= 10:
        return "RETEST_VISIBILITY_HIGH"
    if touches >= 1 or delay is not None or natural not in {"", "RETEST_NOT_VISIBLE"}:
        return "RETEST_VISIBILITY_MEDIUM"
    if raw_ticks > 0:
        return "RETEST_VISIBILITY_LOW_RAW_ONLY"
    return "RETEST_VISIBILITY_UNKNOWN"


def _t0109_evidence_score(out):
    score = 0.0
    status = _t0109_s(out.get("b9_retest_source_status"))
    visibility = _t0109_s(out.get("b9_retest_source_visibility"))
    quality = _t0109_s(out.get("b9_retest_quality_state"))
    touches = _t0109_touch_count(out)
    delay = _t0109_delay_seconds(out)
    raw_ticks = _t0109_i(out.get("raw_tick_count_dedup", out.get("raw_tick_count")), 0)

    if status.endswith("EXPLICIT"):
        score += 0.40
    elif status != "RETEST_SOURCE_NOT_VISIBLE":
        score += 0.25

    if visibility == "RETEST_VISIBILITY_HIGH":
        score += 0.25
    elif visibility == "RETEST_VISIBILITY_MEDIUM":
        score += 0.15
    elif visibility == "RETEST_VISIBILITY_LOW_RAW_ONLY":
        score += 0.05

    score += min(0.20, touches * 0.05)

    if delay is not None:
        score += 0.10

    if quality in {"RETEST_QUALITY_CLEAN", "RETEST_QUALITY_FRICTIONAL", "RETEST_QUALITY_RISK"}:
        score += 0.10

    if raw_ticks >= 20:
        score += 0.05

    return round(_t0109_clamp(score), 4)


def _t0109_signal_state(out):
    status = _t0109_s(out.get("b9_retest_source_status"))
    absorption = _t0109_s(out.get("b9_absorption_like_state"))
    auction = _t0109_s(out.get("b9_auction_state"))
    trap = _t0109_s(out.get("b9_trap_risk_state"))
    score = _t0109_f(out.get("b9_retest_source_evidence_score"))

    if status.startswith("RETEST_SOURCE_ACCEPTED") and score >= 0.45:
        return "RETEST_SIGNAL_ACCEPTANCE_EVIDENCE"
    if status.startswith("RETEST_SOURCE_REJECTED") and score >= 0.45:
        return "RETEST_SIGNAL_REJECTION_EVIDENCE"
    if status.startswith("RETEST_SOURCE_PENDING"):
        return "RETEST_SIGNAL_PENDING_EVIDENCE"
    if status == "RETEST_SOURCE_FRICTION_INFERRED" or absorption.startswith("ABSORPTION_LIKE"):
        return "RETEST_SIGNAL_FRICTION_EVIDENCE"
    if auction == "AUCTION_ROTATIONAL_BALANCE":
        return "RETEST_SIGNAL_ROTATIONAL_CONTEXT"
    if trap.startswith("TRAP_RISK_HIGH"):
        return "RETEST_SIGNAL_TRAP_RISK_CONTEXT"
    return "RETEST_SIGNAL_NOT_VISIBLE"


def _t0109_readiness(out):
    signal = _t0109_s(out.get("b9_retest_source_signal_state"))
    visibility = _t0109_s(out.get("b9_retest_source_visibility"))
    read = _t0109_s(out.get("b9_market_readability_state"))
    score = _t0109_f(out.get("b9_retest_source_evidence_score"))

    if read in {"READABILITY_ARTIFACT", "READABILITY_LIMITED_BY_TEXTURE"}:
        return "RETEST_CONTEXT_LIMITED_BY_TEXTURE"
    if signal in {"RETEST_SIGNAL_ACCEPTANCE_EVIDENCE", "RETEST_SIGNAL_REJECTION_EVIDENCE"} and score >= 0.60:
        return "RETEST_CONTEXT_STRONG"
    if signal != "RETEST_SIGNAL_NOT_VISIBLE" and visibility in {"RETEST_VISIBILITY_HIGH", "RETEST_VISIBILITY_MEDIUM"}:
        return "RETEST_CONTEXT_USABLE"
    if signal == "RETEST_SIGNAL_NOT_VISIBLE":
        return "RETEST_CONTEXT_NOT_VISIBLE"
    return "RETEST_CONTEXT_WEAK"


def _t0109_reading_fr(out):
    readiness = _t0109_s(out.get("b9_retest_source_readiness"))
    signal = _t0109_s(out.get("b9_retest_source_signal_state"))
    visibility = _t0109_s(out.get("b9_retest_source_visibility"))

    if readiness == "RETEST_CONTEXT_STRONG" and "ACCEPTANCE" in signal:
        return "Retest lisible: acceptation soutenue par les champs source et la texture raw."
    if readiness == "RETEST_CONTEXT_STRONG" and "REJECTION" in signal:
        return "Retest lisible: rejet ou échec soutenu par les champs source et la texture raw."
    if signal == "RETEST_SIGNAL_FRICTION_EVIDENCE":
        return "Retest frictionnel: effort visible mais résultat directionnel imparfait."
    if signal == "RETEST_SIGNAL_PENDING_EVIDENCE":
        return "Retest en attente: la scène existe mais demande confirmation contextuelle."
    if signal == "RETEST_SIGNAL_ROTATIONAL_CONTEXT":
        return "Retest dans équilibre rotationnel: lecture utile mais non directionnelle."
    if signal == "RETEST_SIGNAL_TRAP_RISK_CONTEXT":
        return "Retest exposé au piège: le proxy peut surlire la progression."
    if readiness == "RETEST_CONTEXT_LIMITED_BY_TEXTURE":
        return "Retest difficile à lire: texture raw ou segmentation limite l'interprétation."
    if visibility == "RETEST_VISIBILITY_LOW_RAW_ONLY":
        return "Retest peu visible: seule la texture raw donne un contexte faible."
    return "Retest non visible dans les champs source actuels."


def _t0109_apply(out):
    out["b9_retest_source_version"] = "T0109_RETEST_SOURCE_SIGNALS_V0"
    out["b9_retest_source_status"] = _t0109_source_status(out)
    out["b9_retest_touch_count_proxy"] = _t0109_touch_count(out)
    out["b9_retest_delay_proxy_seconds"] = _t0109_delay_seconds(out)
    out["b9_retest_source_visibility"] = _t0109_visibility(out)
    out["b9_retest_source_evidence_score"] = _t0109_evidence_score(out)
    out["b9_retest_source_signal_state"] = _t0109_signal_state(out)
    out["b9_retest_source_readiness"] = _t0109_readiness(out)
    out["b9_retest_source_reading_fr"] = _t0109_reading_fr(out)

    flags = list(out.get("b9_factor_flags") or [])
    for item in [
        out["b9_retest_source_status"],
        out["b9_retest_source_visibility"],
        out["b9_retest_source_signal_state"],
        out["b9_retest_source_readiness"],
    ]:
        if item and item not in flags:
            flags.append(item)
    out["b9_factor_flags"] = flags

    out["b9_retest_source_limits"] = [
        "retest source signals are interpretive, not predictive",
        "missing retest fields reduce visibility",
        "MT5 raw and volume remain broker-relative",
        "no external Temporalité dependency",
        "no BUY/SELL language",
    ]
    return out


def _t0103_calibrate_one_moment(moment, cfg):
    out = _T0109_PREVIOUS_CALIBRATE_ONE_MOMENT(moment, cfg)
    return _t0109_apply(out)


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0109_RETEST_SOURCE_SIGNALS_V0",
        "parent_versions": [
            "T0108_RETEST_MIXED_SPLIT_V0",
            "T0107_NATURAL_FLOW_READING_V0",
            "T0107A_GAPPY_THRESHOLD_HOTFIX",
        ],
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "natural_flow_factors": _t0108a_natural_flow_factors() if "_t0108a_natural_flow_factors" in globals() else [],
        "retest_mixed_fields": [
            "b9_mixed_split_state",
            "b9_retest_natural_state",
            "b9_retest_quality_state",
            "b9_context_resolution_state",
            "b9_retest_mixed_reading_fr",
        ],
        "retest_source_fields": [
            "b9_retest_source_status",
            "b9_retest_touch_count_proxy",
            "b9_retest_delay_proxy_seconds",
            "b9_retest_source_visibility",
            "b9_retest_source_evidence_score",
            "b9_retest_source_signal_state",
            "b9_retest_source_readiness",
            "b9_retest_source_reading_fr",
        ],
        "limits": [
            "interpretation-only",
            "retest source reading is not a signal",
            "external Temporalité brick is not used",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0109_B9_RETEST_SOURCE_SIGNALS_V0_END ---

# --- T0110_B9_RETEST_SOURCE_FIELDS_V0_START ---
# B9 Retest Source Fields V0.
# This layer enriches moments with canonical retest source fields BEFORE T0109
# computes retest source signals. It is a bridge until the sequence summarizer
# emits these fields natively.
# Interpretation only: no signal, no BUY/SELL, no DB write.

_T0110_PREVIOUS_CALIBRATE_ONE_MOMENT = _t0103_calibrate_one_moment


def _t0110_s(value):
    return "" if value is None else str(value)


def _t0110_f(value, default=None):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def _t0110_i(value, default=0):
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def _t0110_dt(value):
    try:
        return _t0103_parse_dt(value)
    except Exception:
        return None


def _t0110_fmt(value):
    dt = _t0110_dt(value)
    if dt is None:
        return None
    return _t0103_fmt_dt(dt)


def _t0110_seconds_between(a, b):
    da = _t0110_dt(a)
    db = _t0110_dt(b)
    if da is None or db is None:
        return None
    return round((db - da).total_seconds(), 3)


def _t0110_zone_memory(moment):
    zm = moment.get("zone_memory")
    if isinstance(zm, dict):
        return dict(zm)
    return {}


def _t0110_pick(moment, zone, keys):
    for key in keys:
        if key in moment and moment.get(key) not in (None, ""):
            return moment.get(key)
        if key in zone and zone.get(key) not in (None, ""):
            return zone.get(key)
    return None


def _t0110_status_blob(moment, zone):
    values = [
        moment.get("retest_status"),
        moment.get("retest_state"),
        moment.get("zone_retest_status"),
        moment.get("memory_state"),
        moment.get("retest_outcome_hint"),
        zone.get("retest_status"),
        zone.get("last_retest_status"),
        zone.get("state"),
        zone.get("memory_state"),
    ]
    return " ".join(_t0110_s(v).upper() for v in values if _t0110_s(v))


def _t0110_outcome_hint(moment, zone):
    blob = _t0110_status_blob(moment, zone)

    if "FAILED" in blob or "FAIL" in blob or "REJECT" in blob or "INVALID" in blob:
        return "RETEST_OUTCOME_REJECTED_OR_FAILED"
    if "ACCEPT" in blob or "VALID" in blob or "CONFIRM" in blob:
        return "RETEST_OUTCOME_ACCEPTED"
    if "PENDING" in blob or "WATCH" in blob or "WAIT" in blob:
        return "RETEST_OUTCOME_PENDING"
    if "ABSORB" in blob or "FRICTION" in blob:
        return "RETEST_OUTCOME_FRICTION"
    if "ROTATION" in blob:
        return "RETEST_OUTCOME_ROTATIONAL"
    return "RETEST_OUTCOME_NOT_VISIBLE"


def _t0110_confidence_state(moment, zone, touch_count, first_touch, last_touch, outcome_hint):
    blob = _t0110_status_blob(moment, zone)

    explicit_markers = ["ACCEPT", "VALID", "CONFIRM", "FAILED", "FAIL", "REJECT", "INVALID", "PENDING", "WATCH", "WAIT"]
    if any(marker in blob for marker in explicit_markers):
        return "RETEST_SOURCE_FIELDS_EXPLICIT"
    if touch_count > 0 or first_touch or last_touch:
        return "RETEST_SOURCE_FIELDS_PARTIAL"
    if outcome_hint != "RETEST_OUTCOME_NOT_VISIBLE":
        return "RETEST_SOURCE_FIELDS_INFERRED"
    return "RETEST_SOURCE_FIELDS_NOT_VISIBLE"


def _t0110_touch_count(moment, zone):
    candidates = [
        moment.get("retest_touch_count"),
        moment.get("zone_touch_count"),
        moment.get("touch_count"),
        moment.get("test_count"),
        zone.get("retest_touch_count"),
        zone.get("zone_touch_count"),
        zone.get("touch_count"),
        zone.get("test_count"),
        zone.get("retest_count"),
        zone.get("tests"),
    ]
    return max([_t0110_i(v, 0) for v in candidates] + [0])


def _t0110_first_touch(moment, zone):
    return _t0110_pick(moment, zone, [
        "retest_first_touch_time",
        "first_retest_time",
        "first_touch_time",
        "zone_first_touch_time",
        "first_tested",
    ])


def _t0110_last_touch(moment, zone):
    return _t0110_pick(moment, zone, [
        "retest_last_touch_time",
        "last_retest_time",
        "last_touch_time",
        "zone_last_touch_time",
        "last_tested",
        "last_seen",
    ])


def _t0110_acceptance_dwell(moment, zone):
    value = _t0110_pick(moment, zone, [
        "retest_acceptance_dwell_seconds",
        "acceptance_dwell_seconds",
        "retest_dwell_seconds",
    ])
    if value is not None:
        return _t0110_f(value, None)

    first_touch = _t0110_first_touch(moment, zone)
    last_touch = _t0110_last_touch(moment, zone)
    outcome = _t0110_outcome_hint(moment, zone)
    if outcome == "RETEST_OUTCOME_ACCEPTED" and first_touch and last_touch:
        seconds = _t0110_seconds_between(first_touch, last_touch)
        if seconds is not None and seconds >= 0:
            return seconds
    return None


def _t0110_rejection_speed(moment, zone):
    value = _t0110_pick(moment, zone, [
        "retest_rejection_speed_pips_per_min",
        "rejection_speed_pips_per_min",
    ])
    if value is not None:
        return _t0110_f(value, None)

    outcome = _t0110_outcome_hint(moment, zone)
    if outcome != "RETEST_OUTCOME_REJECTED_OR_FAILED":
        return None

    delta = abs(_t0110_f(moment.get("raw_delta_pips"), 0.0) or 0.0)
    start = moment.get("time_start")
    end = moment.get("time_end")
    seconds = _t0110_seconds_between(start, end)
    if seconds is None or seconds <= 0:
        return None
    return round((delta / seconds) * 60.0, 6)


def _t0110_zone_distance(moment, zone):
    value = _t0110_pick(moment, zone, [
        "retest_zone_distance_pips",
        "zone_distance_pips",
        "distance_to_zone_pips",
    ])
    return _t0110_f(value, None)


def _t0110_enrich_moment_source_fields(moment):
    out = dict(moment)
    zone = _t0110_zone_memory(out)

    touch_count = _t0110_touch_count(out, zone)
    first_touch = _t0110_first_touch(out, zone)
    last_touch = _t0110_last_touch(out, zone)
    outcome = _t0110_outcome_hint(out, zone)

    # If an explicit retest status exists but no touch count is present, expose one minimum touch.
    if touch_count <= 0 and outcome != "RETEST_OUTCOME_NOT_VISIBLE":
        touch_count = 1

    # If an explicit retest exists and first/last touch are missing, use the moment bounds as proxy evidence.
    if outcome != "RETEST_OUTCOME_NOT_VISIBLE":
        if not first_touch:
            first_touch = out.get("time_start")
        if not last_touch:
            last_touch = out.get("time_end") or out.get("time_start")

    first_touch = _t0110_fmt(first_touch)
    last_touch = _t0110_fmt(last_touch)

    delay = None
    if last_touch and out.get("time_start"):
        delay = _t0110_seconds_between(last_touch, out.get("time_start"))

    out["retest_source_fields_version"] = "T0110_RETEST_SOURCE_FIELDS_V0"
    out["retest_touch_count"] = touch_count
    out["retest_first_touch_time"] = first_touch
    out["retest_last_touch_time"] = last_touch
    out["retest_delay_seconds"] = delay
    out["retest_acceptance_dwell_seconds"] = _t0110_acceptance_dwell(out, zone)
    out["retest_rejection_speed_pips_per_min"] = _t0110_rejection_speed(out, zone)
    out["retest_zone_distance_pips"] = _t0110_zone_distance(out, zone)
    out["retest_outcome_hint"] = outcome
    out["retest_source_field_confidence"] = _t0110_confidence_state(out, zone, touch_count, first_touch, last_touch, outcome)

    # Keep zone memory synchronized without mutating DB.
    if zone:
        if touch_count and "touch_count" not in zone:
            zone["touch_count"] = touch_count
        if last_touch and "last_tested" not in zone:
            zone["last_tested"] = last_touch
        if outcome != "RETEST_OUTCOME_NOT_VISIBLE" and "retest_status" not in zone:
            zone["retest_status"] = outcome
        out["zone_memory"] = zone

    out["retest_source_fields_limits"] = [
        "canonical retest source fields are derived from summary payload only",
        "no DB write",
        "missing source fields remain visible as NOT_VISIBLE",
        "values may be proxy-derived until sequence summarizer emits them natively",
        "no BUY/SELL language",
    ]
    return out


def _t0103_calibrate_one_moment(moment, cfg):
    enriched_moment = _t0110_enrich_moment_source_fields(moment)
    out = _T0110_PREVIOUS_CALIBRATE_ONE_MOMENT(enriched_moment, cfg)

    # Preserve canonical fields in final calibrated output.
    for key in [
        "retest_source_fields_version",
        "retest_touch_count",
        "retest_first_touch_time",
        "retest_last_touch_time",
        "retest_delay_seconds",
        "retest_acceptance_dwell_seconds",
        "retest_rejection_speed_pips_per_min",
        "retest_zone_distance_pips",
        "retest_outcome_hint",
        "retest_source_field_confidence",
        "retest_source_fields_limits",
    ]:
        if key in enriched_moment:
            out[key] = enriched_moment[key]
    if "zone_memory" in enriched_moment:
        out["zone_memory"] = enriched_moment["zone_memory"]
    return out


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0110_RETEST_SOURCE_FIELDS_V0",
        "parent_versions": [
            "T0109_RETEST_SOURCE_SIGNALS_V0",
            "T0108_RETEST_MIXED_SPLIT_V0",
            "T0107_NATURAL_FLOW_READING_V0",
            "T0107A_GAPPY_THRESHOLD_HOTFIX",
        ],
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "retest_source_fields": [
            "retest_touch_count",
            "retest_first_touch_time",
            "retest_last_touch_time",
            "retest_delay_seconds",
            "retest_acceptance_dwell_seconds",
            "retest_rejection_speed_pips_per_min",
            "retest_zone_distance_pips",
            "retest_outcome_hint",
            "retest_source_field_confidence",
        ],
        "retest_source_signals": [
            "b9_retest_source_status",
            "b9_retest_source_visibility",
            "b9_retest_source_evidence_score",
            "b9_retest_source_signal_state",
            "b9_retest_source_readiness",
            "b9_retest_source_reading_fr",
        ],
        "limits": [
            "interpretation-only",
            "T0110 is a source-field bridge until native summarizer support",
            "external Temporalité brick is not used",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0110_B9_RETEST_SOURCE_FIELDS_V0_END ---

# --- T0110A_B9_RETEST_SOURCE_FIELDS_METADATA_COMPAT_HOTFIX_START ---
# Hotfix: T0110 is the active top layer, but it must preserve
# the metadata traceability expected by T0107/T0108/T0109 tests:
# - natural_flow_factors
# - retest_mixed_fields
# - retest_source_fields
# - retest_source_signals
#
# T0110A does not change the moment semantics. It only restores
# additive-layer metadata contract.

def _t0110a_natural_flow_factors():
    return [
        "b9_flow_intent_state",
        "b9_absorption_like_state",
        "b9_exhaustion_like_state",
        "b9_initiative_response_state",
        "b9_auction_state",
        "b9_trap_risk_state",
        "b9_market_readability_state",
        "b9_natural_flow_reading_fr",
    ]


def _t0110a_retest_mixed_fields():
    return [
        "b9_mixed_split_state",
        "b9_retest_natural_state",
        "b9_retest_quality_state",
        "b9_context_resolution_state",
        "b9_retest_mixed_reading_fr",
    ]


def _t0110a_retest_source_fields():
    return [
        "retest_touch_count",
        "retest_first_touch_time",
        "retest_last_touch_time",
        "retest_delay_seconds",
        "retest_acceptance_dwell_seconds",
        "retest_rejection_speed_pips_per_min",
        "retest_zone_distance_pips",
        "retest_outcome_hint",
        "retest_source_field_confidence",
    ]


def _t0110a_retest_source_signals():
    return [
        "b9_retest_source_status",
        "b9_retest_source_visibility",
        "b9_retest_source_evidence_score",
        "b9_retest_source_signal_state",
        "b9_retest_source_readiness",
        "b9_retest_source_reading_fr",
    ]


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0110_RETEST_SOURCE_FIELDS_V0",
        "parent_versions": [
            "T0109_RETEST_SOURCE_SIGNALS_V0",
            "T0108_RETEST_MIXED_SPLIT_V0",
            "T0107_NATURAL_FLOW_READING_V0",
            "T0107A_GAPPY_THRESHOLD_HOTFIX",
        ],
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "natural_flow_factors": _t0110a_natural_flow_factors(),
        "retest_mixed_fields": _t0110a_retest_mixed_fields(),
        "retest_source_fields": _t0110a_retest_source_fields(),
        "retest_source_signals": _t0110a_retest_source_signals(),
        "metadata_compat_hotfix": "T0110A_RETEST_SOURCE_FIELDS_METADATA_COMPAT",
        "limits": [
            "interpretation-only",
            "T0110 is a source-field bridge until native summarizer support",
            "T0110A preserves natural_flow_factors metadata for additive-layer compatibility",
            "external Temporalité brick is not used",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0110A_B9_RETEST_SOURCE_FIELDS_METADATA_COMPAT_HOTFIX_END ---

# --- T0110B_B9_RETEST_SOURCE_FIELDS_LEGACY_METADATA_HOTFIX_START ---
# Hotfix: keep T0110 metadata clean AND legacy-compatible.
#
# T0109 historical tests expect `b9_retest_source_status` to appear in
# raw_calibration["retest_source_fields"]. T0110A separated canonical source
# fields from computed source signals, which is semantically cleaner, but broke
# the legacy additive-layer contract.
#
# T0110B therefore keeps both:
# - retest_source_fields includes canonical retest fields + legacy signal aliases
# - retest_source_signals keeps the computed signal fields explicitly
#
# No moment semantics are changed.

def _t0110b_retest_source_fields_legacy_compatible():
    return [
        # Canonical source fields introduced by T0110.
        "retest_touch_count",
        "retest_first_touch_time",
        "retest_last_touch_time",
        "retest_delay_seconds",
        "retest_acceptance_dwell_seconds",
        "retest_rejection_speed_pips_per_min",
        "retest_zone_distance_pips",
        "retest_outcome_hint",
        "retest_source_field_confidence",

        # Legacy compatibility aliases expected by T0109 metadata tests.
        "b9_retest_source_status",
        "b9_retest_source_visibility",
        "b9_retest_source_evidence_score",
        "b9_retest_source_signal_state",
        "b9_retest_source_readiness",
        "b9_retest_source_reading_fr",
    ]


def calibrate_summary_with_raw(summary, cfg):
    payload = _t0103_deepcopy(summary)
    moments = payload.get("moments", [])
    payload["moments"] = [_t0103_calibrate_one_moment(m, cfg) for m in moments]
    payload.setdefault("raw_calibration", {})
    payload["raw_calibration"].update({
        "version": "T0110_RETEST_SOURCE_FIELDS_V0",
        "parent_versions": [
            "T0109_RETEST_SOURCE_SIGNALS_V0",
            "T0108_RETEST_MIXED_SPLIT_V0",
            "T0107_NATURAL_FLOW_READING_V0",
            "T0107A_GAPPY_THRESHOLD_HOTFIX",
        ],
        "symbol": getattr(cfg, "symbol", "GBPUSD"),
        "broker": getattr(cfg, "broker", "UNKNOWN"),
        "broker_time_shift_min": getattr(cfg, "broker_time_shift_min", 0),
        "raw_source_mode": getattr(cfg, "raw_source_mode", "HISTORICAL_RAW"),
        "raw_data_visibility": getattr(cfg, "raw_data_visibility", "MT5_RAW_ALIGNED"),
        "b9_temporality_scope": "INTRINSIC_MICROFILM_ONLY",
        "external_temporality_dependency": False,
        "volume_policy": "BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL",
        "natural_flow_factors": _t0110a_natural_flow_factors() if "_t0110a_natural_flow_factors" in globals() else [
            "b9_flow_intent_state",
            "b9_absorption_like_state",
            "b9_exhaustion_like_state",
            "b9_initiative_response_state",
            "b9_auction_state",
            "b9_trap_risk_state",
            "b9_market_readability_state",
            "b9_natural_flow_reading_fr",
        ],
        "retest_mixed_fields": _t0110a_retest_mixed_fields() if "_t0110a_retest_mixed_fields" in globals() else [
            "b9_mixed_split_state",
            "b9_retest_natural_state",
            "b9_retest_quality_state",
            "b9_context_resolution_state",
            "b9_retest_mixed_reading_fr",
        ],
        "retest_source_fields": _t0110b_retest_source_fields_legacy_compatible(),
        "retest_source_signals": _t0110a_retest_source_signals() if "_t0110a_retest_source_signals" in globals() else [
            "b9_retest_source_status",
            "b9_retest_source_visibility",
            "b9_retest_source_evidence_score",
            "b9_retest_source_signal_state",
            "b9_retest_source_readiness",
            "b9_retest_source_reading_fr",
        ],
        "metadata_compat_hotfix": "T0110B_RETEST_SOURCE_FIELDS_LEGACY_METADATA",
        "limits": [
            "interpretation-only",
            "T0110 is a source-field bridge until native summarizer support",
            "T0110B preserves T0109 legacy metadata expectations",
            "external Temporalité brick is not used",
            "MT5 volume is not global Forex volume",
            "no BUY/SELL language",
        ],
    })
    return payload
# --- T0110B_B9_RETEST_SOURCE_FIELDS_LEGACY_METADATA_HOTFIX_END ---
