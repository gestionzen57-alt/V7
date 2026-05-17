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
