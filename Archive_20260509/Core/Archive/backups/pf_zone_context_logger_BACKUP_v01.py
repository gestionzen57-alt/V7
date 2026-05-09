"""
PowerFlow V6 - pf_zone_context_logger.py
Version: V0.1

Mission:
    Persist pf_zone_dynamics.ZoneDiagnosis outputs into SQLite so PowerFlow can
    calibrate dynamic zones from real observations instead of frozen theory.

Doctrine:
    - This module does not decide.
    - This module does not alter zone perception.
    - It stores what the zone engine saw, when it saw it, and under which context.

Typical usage:
    from pf_zone_dynamics import analyze_zone_dynamics
    from pf_zone_context_logger import ensure_zone_diagnostics_table, log_zone_diagnosis

    diag = analyze_zone_dynamics(z_series, timeframe=15, currency="GBP")

    with sqlite3.connect("powerflow.db") as conn:
        ensure_zone_diagnostics_table(conn)
        log_zone_diagnosis(
            conn,
            diagnosis=diag,
            symbol="GBPUSD",
            source_created_at="2026-05-01T12:00:00+00:00",
        )
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union


SQLiteTarget = Union[str, Path, sqlite3.Connection]


ZONE_DIAGNOSTICS_DDL = """
CREATE TABLE IF NOT EXISTS zone_diagnostics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    logged_at TEXT NOT NULL,
    source_created_at TEXT,
    source_snapshot_id INTEGER,

    symbol TEXT,
    timeframe INTEGER NOT NULL,
    currency TEXT NOT NULL,

    state TEXT NOT NULL,
    zone_level TEXT,
    z_current REAL,
    z_extreme_dir TEXT,

    bars_in_extreme INTEGER,
    pullback_count INTEGER,
    absorbed_pullback_count INTEGER,
    latest_pullback_depth REAL,
    latest_pullback_absorbed INTEGER,

    depth_slope REAL,
    depth_acceleration REAL,
    absorption_factor REAL,
    tension_score REAL,
    context_score REAL,

    profile_name TEXT,
    profile_horizon TEXT,
    session_phase TEXT,
    rank_position INTEGER,
    rank_total INTEGER,
    rank_duration_bars INTEGER,
    price_wall INTEGER NOT NULL DEFAULT 0,

    context_tags_json TEXT,
    pullbacks_json TEXT,
    note TEXT,
    raw_diagnosis_json TEXT
);
"""


ZONE_DIAGNOSTICS_INDEXES = (
    "CREATE INDEX IF NOT EXISTS idx_zone_diag_source_time ON zone_diagnostics(source_created_at);",
    "CREATE INDEX IF NOT EXISTS idx_zone_diag_tf_currency ON zone_diagnostics(timeframe, currency);",
    "CREATE INDEX IF NOT EXISTS idx_zone_diag_state_zone ON zone_diagnostics(state, zone_level);",
    "CREATE INDEX IF NOT EXISTS idx_zone_diag_scores ON zone_diagnostics(context_score, tension_score);",
    "CREATE INDEX IF NOT EXISTS idx_zone_diag_profile ON zone_diagnostics(profile_name, profile_horizon);",
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_zone_diag_snapshot_currency_profile "
    "ON zone_diagnostics(source_snapshot_id, currency, profile_name, profile_horizon) "
    "WHERE source_snapshot_id IS NOT NULL;",
)


INSERT_ZONE_DIAGNOSIS_SQL = """
INSERT INTO zone_diagnostics (
    logged_at,
    source_created_at,
    source_snapshot_id,
    symbol,
    timeframe,
    currency,
    state,
    zone_level,
    z_current,
    z_extreme_dir,
    bars_in_extreme,
    pullback_count,
    absorbed_pullback_count,
    latest_pullback_depth,
    latest_pullback_absorbed,
    depth_slope,
    depth_acceleration,
    absorption_factor,
    tension_score,
    context_score,
    profile_name,
    profile_horizon,
    session_phase,
    rank_position,
    rank_total,
    rank_duration_bars,
    price_wall,
    context_tags_json,
    pullbacks_json,
    note,
    raw_diagnosis_json
) VALUES (
    :logged_at,
    :source_created_at,
    :source_snapshot_id,
    :symbol,
    :timeframe,
    :currency,
    :state,
    :zone_level,
    :z_current,
    :z_extreme_dir,
    :bars_in_extreme,
    :pullback_count,
    :absorbed_pullback_count,
    :latest_pullback_depth,
    :latest_pullback_absorbed,
    :depth_slope,
    :depth_acceleration,
    :absorption_factor,
    :tension_score,
    :context_score,
    :profile_name,
    :profile_horizon,
    :session_phase,
    :rank_position,
    :rank_total,
    :rank_duration_bars,
    :price_wall,
    :context_tags_json,
    :pullbacks_json,
    :note,
    :raw_diagnosis_json
);
"""


def utc_now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class _ManagedConnection:
    """Small context manager that accepts a path or an existing connection."""

    def __init__(self, target: SQLiteTarget) -> None:
        self.target = target
        self.conn: Optional[sqlite3.Connection] = None
        self.created = False

    def __enter__(self) -> sqlite3.Connection:
        if isinstance(self.target, sqlite3.Connection):
            self.conn = self.target
            return self.conn
        self.conn = sqlite3.connect(str(self.target))
        self.created = True
        return self.conn

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.conn is None:
            return
        if exc_type is None:
            self.conn.commit()
        else:
            self.conn.rollback()
        if self.created:
            self.conn.close()


def ensure_zone_diagnostics_table(target: SQLiteTarget) -> None:
    """Create the zone_diagnostics table and indexes if missing."""
    with _ManagedConnection(target) as conn:
        conn.execute(ZONE_DIAGNOSTICS_DDL)
        for ddl in ZONE_DIAGNOSTICS_INDEXES:
            conn.execute(ddl)
        conn.commit()


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _safe_get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _diagnosis_to_dict(diagnosis: Any) -> Dict[str, Any]:
    if hasattr(diagnosis, "to_dict") and callable(diagnosis.to_dict):
        data = diagnosis.to_dict()
    elif is_dataclass(diagnosis):
        data = asdict(diagnosis)
    elif isinstance(diagnosis, Mapping):
        data = dict(diagnosis)
    else:
        raise TypeError("diagnosis must be a ZoneDiagnosis, dataclass, mapping, or expose to_dict()")
    return data


def _pullbacks_from_diagnosis(diagnosis: Any, data: Mapping[str, Any]) -> List[Dict[str, Any]]:
    raw = data.get("pullbacks")
    if raw is None:
        raw = _safe_get(diagnosis, "pullbacks", [])

    out: List[Dict[str, Any]] = []
    for item in raw or []:
        if hasattr(item, "to_dict") and callable(item.to_dict):
            out.append(item.to_dict())
        elif is_dataclass(item):
            out.append(asdict(item))
        elif isinstance(item, Mapping):
            out.append(dict(item))
    return out


def build_zone_diagnostic_row(
    diagnosis: Any,
    *,
    symbol: Optional[str] = None,
    timeframe: Optional[int] = None,
    currency: Optional[str] = None,
    source_created_at: Optional[str] = None,
    source_snapshot_id: Optional[int] = None,
    session_phase: Optional[str] = None,
    rank_position: Optional[int] = None,
    rank_total: Optional[int] = None,
    rank_duration_bars: Optional[int] = None,
    price_wall: Optional[bool] = None,
    logged_at: Optional[str] = None,
) -> Dict[str, Any]:
    """Flatten one ZoneDiagnosis into an insertable database row."""
    data = _diagnosis_to_dict(diagnosis)
    pullbacks = _pullbacks_from_diagnosis(diagnosis, data)
    pullback_count = len(pullbacks)
    absorbed_count = sum(1 for p in pullbacks if bool(p.get("absorbed")))
    latest = pullbacks[-1] if pullbacks else None

    resolved_timeframe = timeframe if timeframe is not None else data.get("timeframe")
    resolved_currency = (currency or data.get("currency") or "UNKNOWN").upper()
    resolved_session = session_phase if session_phase is not None else data.get("session_phase")
    resolved_price_wall = bool(price_wall) if price_wall is not None else False

    context_tags = data.get("contextual_tags", []) or []

    raw_json = dict(data)
    raw_json["pullbacks"] = pullbacks

    return {
        "logged_at": logged_at or utc_now_iso(),
        "source_created_at": source_created_at,
        "source_snapshot_id": source_snapshot_id,
        "symbol": symbol,
        "timeframe": int(resolved_timeframe) if resolved_timeframe is not None else 0,
        "currency": resolved_currency,
        "state": data.get("state", "UNKNOWN"),
        "zone_level": data.get("zone_level"),
        "z_current": data.get("z_current"),
        "z_extreme_dir": data.get("z_extreme_dir"),
        "bars_in_extreme": data.get("bars_in_extreme"),
        "pullback_count": pullback_count,
        "absorbed_pullback_count": absorbed_count,
        "latest_pullback_depth": latest.get("depth") if latest else None,
        "latest_pullback_absorbed": int(bool(latest.get("absorbed"))) if latest else None,
        "depth_slope": data.get("depth_slope"),
        "depth_acceleration": data.get("depth_acceleration"),
        "absorption_factor": data.get("absorption_factor"),
        "tension_score": data.get("tension_score"),
        "context_score": data.get("context_score", data.get("tension_score")),
        "profile_name": data.get("profile_name"),
        "profile_horizon": data.get("profile_horizon"),
        "session_phase": resolved_session,
        "rank_position": rank_position,
        "rank_total": rank_total,
        "rank_duration_bars": rank_duration_bars,
        "price_wall": int(resolved_price_wall),
        "context_tags_json": _json_dumps(list(context_tags)),
        "pullbacks_json": _json_dumps(pullbacks),
        "note": data.get("note"),
        "raw_diagnosis_json": _json_dumps(raw_json),
    }


def _existing_id_for_source(
    conn: sqlite3.Connection,
    row: Mapping[str, Any],
) -> Optional[int]:
    source_snapshot_id = row.get("source_snapshot_id")
    if source_snapshot_id is None:
        return None
    result = conn.execute(
        """
        SELECT id
        FROM zone_diagnostics
        WHERE source_snapshot_id = ?
          AND currency = ?
          AND profile_name IS ?
          AND profile_horizon IS ?
        ORDER BY id DESC
        LIMIT 1;
        """,
        (
            source_snapshot_id,
            row.get("currency"),
            row.get("profile_name"),
            row.get("profile_horizon"),
        ),
    ).fetchone()
    return int(result[0]) if result else None


def log_zone_diagnosis(
    target: SQLiteTarget,
    *,
    diagnosis: Any,
    symbol: Optional[str] = None,
    timeframe: Optional[int] = None,
    currency: Optional[str] = None,
    source_created_at: Optional[str] = None,
    source_snapshot_id: Optional[int] = None,
    session_phase: Optional[str] = None,
    rank_position: Optional[int] = None,
    rank_total: Optional[int] = None,
    rank_duration_bars: Optional[int] = None,
    price_wall: Optional[bool] = None,
    duplicate_policy: str = "ignore",
) -> int:
    """Persist one zone diagnosis and return its row id.

    duplicate_policy:
        - "ignore": if source_snapshot_id/currency/profile already exists, return existing id
        - "replace": delete existing matching row then insert the new one
        - "insert": always insert; may raise sqlite3.IntegrityError if unique index applies
    """
    policy = duplicate_policy.lower().strip()
    if policy not in {"ignore", "replace", "insert"}:
        raise ValueError("duplicate_policy must be 'ignore', 'replace', or 'insert'")

    row = build_zone_diagnostic_row(
        diagnosis,
        symbol=symbol,
        timeframe=timeframe,
        currency=currency,
        source_created_at=source_created_at,
        source_snapshot_id=source_snapshot_id,
        session_phase=session_phase,
        rank_position=rank_position,
        rank_total=rank_total,
        rank_duration_bars=rank_duration_bars,
        price_wall=price_wall,
    )

    with _ManagedConnection(target) as conn:
        ensure_zone_diagnostics_table(conn)
        existing_id = _existing_id_for_source(conn, row)
        if existing_id is not None:
            if policy == "ignore":
                return existing_id
            if policy == "replace":
                conn.execute("DELETE FROM zone_diagnostics WHERE id = ?", (existing_id,))

        cur = conn.execute(INSERT_ZONE_DIAGNOSIS_SQL, row)
        conn.commit()
        return int(cur.lastrowid)


def log_zone_diagnoses(
    target: SQLiteTarget,
    rows: Iterable[Mapping[str, Any]],
    *,
    duplicate_policy: str = "ignore",
) -> List[int]:
    """Persist many diagnoses.

    Each item must contain at least diagnosis, and may contain symbol/timeframe/
    currency/source_created_at/source_snapshot_id/session/rank fields.
    """
    inserted: List[int] = []
    ensure_zone_diagnostics_table(target)
    with _ManagedConnection(target) as conn:
        for item in rows:
            diagnosis = item.get("diagnosis")
            if diagnosis is None:
                raise ValueError("each row must contain a 'diagnosis'")
            row_id = log_zone_diagnosis(
                conn,
                diagnosis=diagnosis,
                symbol=item.get("symbol"),
                timeframe=item.get("timeframe"),
                currency=item.get("currency"),
                source_created_at=item.get("source_created_at"),
                source_snapshot_id=item.get("source_snapshot_id"),
                session_phase=item.get("session_phase"),
                rank_position=item.get("rank_position"),
                rank_total=item.get("rank_total"),
                rank_duration_bars=item.get("rank_duration_bars"),
                price_wall=item.get("price_wall"),
                duplicate_policy=duplicate_policy,
            )
            inserted.append(row_id)
        conn.commit()
    return inserted


def fetch_latest_zone_diagnostics(
    target: SQLiteTarget,
    *,
    limit: int = 50,
    currency: Optional[str] = None,
    timeframe: Optional[int] = None,
    min_context_score: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Read latest logged diagnostics as dictionaries."""
    where: List[str] = []
    params: List[Any] = []

    if currency:
        where.append("currency = ?")
        params.append(currency.upper())
    if timeframe is not None:
        where.append("timeframe = ?")
        params.append(int(timeframe))
    if min_context_score is not None:
        where.append("context_score >= ?")
        params.append(float(min_context_score))

    sql = "SELECT * FROM zone_diagnostics"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY COALESCE(source_created_at, logged_at) DESC, id DESC LIMIT ?"
    params.append(int(limit))

    with _ManagedConnection(target) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        return [dict(row) for row in rows]


def summarize_zone_diagnostics(
    target: SQLiteTarget,
) -> Dict[str, Any]:
    """Return compact calibration counters."""
    with _ManagedConnection(target) as conn:
        cur = conn.cursor()
        total = cur.execute("SELECT COUNT(*) FROM zone_diagnostics").fetchone()[0]
        by_state = cur.execute(
            "SELECT state, COUNT(*) FROM zone_diagnostics GROUP BY state ORDER BY COUNT(*) DESC"
        ).fetchall()
        by_tf = cur.execute(
            "SELECT timeframe, COUNT(*) FROM zone_diagnostics GROUP BY timeframe ORDER BY timeframe"
        ).fetchall()
        top = cur.execute(
            """
            SELECT source_created_at, timeframe, currency, state, zone_level,
                   z_current, tension_score, context_score, profile_name, profile_horizon
            FROM zone_diagnostics
            ORDER BY context_score DESC, tension_score DESC
            LIMIT 10
            """
        ).fetchall()

    return {
        "total": total,
        "by_state": [(r[0], r[1]) for r in by_state],
        "by_timeframe": [(r[0], r[1]) for r in by_tf],
        "top_context": [tuple(r) for r in top],
    }


def print_summary(target: SQLiteTarget) -> None:
    """Print a compact human-readable summary."""
    summary = summarize_zone_diagnostics(target)
    print("PowerFlow zone_diagnostics summary")
    print("=" * 72)
    print(f"Total rows: {summary['total']}")
    print("\nBy state:")
    for state, count in summary["by_state"]:
        print(f"  {state:<18} {count}")
    print("\nBy timeframe:")
    for tf, count in summary["by_timeframe"]:
        print(f"  TF={tf:<5} {count}")
    print("\nTop context_score:")
    for row in summary["top_context"]:
        src, tf, cur, state, zone, z, tension, ctx, profile, horizon = row
        print(
            f"  {src or '-':<25} TF={tf:<5} {cur:<3} "
            f"{state:<15} {zone or '-':<11} z={z:+.3f} "
            f"tension={tension:.3f} ctx={ctx:.3f} {profile}/{horizon}"
        )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create/read PowerFlow zone_diagnostics table.")
    parser.add_argument("db", help="Path to powerflow.db")
    parser.add_argument("--summary", action="store_true", help="Print summary after ensuring the table")
    args = parser.parse_args()

    ensure_zone_diagnostics_table(args.db)
    if args.summary:
        print_summary(args.db)
    else:
        print(f"OK zone_diagnostics table ready in {args.db}")
