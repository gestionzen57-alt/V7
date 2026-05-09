"""
PowerFlow V6 — DBVisionGuard V0.1

Mission:
    Read-only SQLite guard that verifies whether powerflow.db can actually
    see the market across tactical and structural timeframes.

Doctrine:
    - capture_* writes DB.
    - pf_* reads/calculates.
    - cockpit_* displays only.
    - This module is read-only and produces no trading decision.

Supports:
    - Legacy force_snapshots schema.
    - Extended schema if new columns/tables exist.
    - Known historical gaps without declaring the live DB dead.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import argparse
import json
import sqlite3


FORCE_COLUMNS_LEGACY: Tuple[str, ...] = (
    "force_gbp",
    "force_usd",
    "force_eur",
    "force_jpy",
    "force_cad",
    "force_chf",
    "force_aud",
)

EXTENDED_EXPECTED_COLUMNS: Tuple[str, ...] = (
    "force_nzd",
    "open",
    "high",
    "low",
    "close",
    "tick_volume",
    "pip_range",
    "pip_body",
    "pip_change",
    "spread_points",
    "spread_price",
    "spread_pips",
    "ask",
    "mid",
    "bar_time",
    "bar_close_time",
    "server_time",
    "capture_time",
    "is_closed_bar",
)

TACTICAL_TFS: Tuple[int, ...] = (1, 5, 15)
STRUCTURAL_TFS: Tuple[int, ...] = (30, 60, 240)


@dataclass(frozen=True)
class TableSchema:
    table: str
    exists: bool
    columns: List[str]
    legacy_force_columns_present: List[str]
    extended_columns_present: List[str]
    extended_columns_missing: List[str]

    @property
    def extended_ratio(self) -> float:
        if not EXTENDED_EXPECTED_COLUMNS:
            return 0.0
        return len(self.extended_columns_present) / len(EXTENDED_EXPECTED_COLUMNS)

    @property
    def schema_state(self) -> str:
        if not self.exists:
            return "TABLE_MISSING"
        if self.extended_ratio >= 0.90:
            return "SCHEMA_EXTENDED_OK"
        if self.extended_ratio > 0.0:
            return "SCHEMA_EXTENDED_PARTIAL"
        if all(col in self.columns for col in FORCE_COLUMNS_LEGACY):
            return "LEGACY_FORCE_ONLY"
        return "SCHEMA_UNKNOWN"


@dataclass(frozen=True)
class TimeframeVision:
    timeframe: int
    rows_total: int
    rows_recent: int
    latest_created_at: Optional[str]
    latest_age_sec: Optional[float]
    max_gap_minutes: Optional[float]
    status: str


@dataclass(frozen=True)
class GapReport:
    timeframe: int
    start: str
    end: str
    gap_minutes: float
    status: str


@dataclass(frozen=True)
class DBVisionReport:
    db_path: str
    symbol: str
    checked_at_utc: str
    source_table: Optional[str]
    schema_state: str
    live_state: str
    vision_state: str
    can_detect_ltf_birth: bool
    can_validate_htf_gravity: bool
    table_schemas: List[TableSchema]
    timeframes: List[TimeframeVision]
    gaps: List[GapReport]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    # SQLite/project timestamps may be "YYYY-MM-DD HH:MM:SS",
    # ISO strings, or ISO strings with Z.
    candidates = [
        text,
        text.replace("Z", "+00:00"),
        text.replace(" ", "T"),
        text.replace(" ", "T").replace("Z", "+00:00"),
    ]

    for candidate in candidates:
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                # Treat DB/broker naive timestamps as UTC for age proxy.
                # The exact age is less important than freshness ranking.
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def _connect_readonly(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    if not p.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")

    uri = f"file:{p.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    return [str(r["name"]) for r in rows]


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.Error:
        return []
    return [str(r["name"]) for r in rows]


def _build_table_schema(conn: sqlite3.Connection, table: str, tables: Sequence[str]) -> TableSchema:
    exists = table in tables
    columns = _table_columns(conn, table) if exists else []

    legacy_present = [c for c in FORCE_COLUMNS_LEGACY if c in columns]
    extended_present = [c for c in EXTENDED_EXPECTED_COLUMNS if c in columns]
    extended_missing = [c for c in EXTENDED_EXPECTED_COLUMNS if c not in columns]

    return TableSchema(
        table=table,
        exists=exists,
        columns=columns,
        legacy_force_columns_present=legacy_present,
        extended_columns_present=extended_present,
        extended_columns_missing=extended_missing,
    )


def _candidate_source_tables(tables: Sequence[str]) -> List[str]:
    # Prefer extended-looking tables if present, but keep force_snapshots as core fallback.
    preferred_names = [
        "force_snapshots_extended",
        "extended_force_snapshots",
        "market_snapshots",
        "snapshots_extended",
        "force_snapshots",
    ]

    candidates: List[str] = []
    for name in preferred_names:
        if name in tables and name not in candidates:
            candidates.append(name)

    for table in tables:
        lowered = table.lower()
        if "snapshot" in lowered and table not in candidates:
            candidates.append(table)

    return candidates


def _quote_identifier(name: str) -> str:
    safe = name.replace('"', '""')
    return f'"{safe}"'


def _latest_row_for_tf(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    timeframe: int,
) -> Optional[sqlite3.Row]:
    qtable = _quote_identifier(table)
    return conn.execute(
        f"""
        SELECT *
        FROM {qtable}
        WHERE symbol = ? AND timeframe = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (symbol, timeframe),
    ).fetchone()


def _count_rows(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    timeframe: int,
) -> int:
    qtable = _quote_identifier(table)
    row = conn.execute(
        f"""
        SELECT COUNT(*) AS n
        FROM {qtable}
        WHERE symbol = ? AND timeframe = ?
        """,
        (symbol, timeframe),
    ).fetchone()
    return int(row["n"]) if row else 0


def _count_recent_rows(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    timeframe: int,
    recent_minutes: int,
) -> int:
    latest = _latest_row_for_tf(conn, table, symbol, timeframe)
    if latest is None:
        return 0

    latest_dt = _parse_dt(latest["created_at"])
    if latest_dt is None:
        return 0

    cutoff_ts = latest_dt.timestamp() - (recent_minutes * 60)
    qtable = _quote_identifier(table)

    rows = conn.execute(
        f"""
        SELECT created_at
        FROM {qtable}
        WHERE symbol = ? AND timeframe = ?
        ORDER BY created_at DESC
        """,
        (symbol, timeframe),
    ).fetchall()

    count = 0
    for row in rows:
        dt = _parse_dt(row["created_at"])
        if dt is not None and dt.timestamp() >= cutoff_ts:
            count += 1

    return count


def _gap_reports(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    timeframe: int,
    gap_threshold_minutes: int,
) -> Tuple[Optional[float], List[GapReport]]:
    qtable = _quote_identifier(table)

    rows = conn.execute(
        f"""
        SELECT created_at
        FROM {qtable}
        WHERE symbol = ? AND timeframe = ?
        ORDER BY created_at ASC
        """,
        (symbol, timeframe),
    ).fetchall()

    dts = [_parse_dt(r["created_at"]) for r in rows]
    dts = [dt for dt in dts if dt is not None]

    if len(dts) < 2:
        return None, []

    max_gap = 0.0
    gaps: List[GapReport] = []

    for prev, cur in zip(dts, dts[1:]):
        gap_min = (cur - prev).total_seconds() / 60.0
        if gap_min > max_gap:
            max_gap = gap_min

        if gap_min >= gap_threshold_minutes:
            status = "HISTORICAL_GAP_DETECTED"
            gaps.append(
                GapReport(
                    timeframe=timeframe,
                    start=prev.isoformat(),
                    end=cur.isoformat(),
                    gap_minutes=round(gap_min, 2),
                    status=status,
                )
            )

    return round(max_gap, 2), gaps


def _timeframe_status(
    timeframe: int,
    rows_total: int,
    rows_recent: int,
    latest_age_sec: Optional[float],
    recent_minutes: int,
) -> str:
    if rows_total <= 0:
        return "NO_ROWS"

    if latest_age_sec is None:
        return "TIME_PARSE_UNKNOWN"

    if rows_recent <= 0:
        return "STALE_OR_SPARSE"

    # Tactical TFs need stronger freshness than structural TFs.
    if timeframe in TACTICAL_TFS:
        if latest_age_sec <= recent_minutes * 60:
            return "OK"
        return "STALE"

    if latest_age_sec <= max(recent_minutes, 240) * 60:
        return "OK"

    return "STALE"


def analyze_db_vision(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframes: Iterable[int] = (1, 5, 15, 30, 60, 240),
    recent_minutes: int = 60,
    gap_threshold_minutes: int = 180,
) -> DBVisionReport:
    checked_at = datetime.now(timezone.utc)
    notes: List[str] = []

    with _connect_readonly(db_path) as conn:
        tables = _list_tables(conn)

        candidates = _candidate_source_tables(tables)
        if not candidates:
            table_schemas = []
            return DBVisionReport(
                db_path=db_path,
                symbol=symbol,
                checked_at_utc=checked_at.isoformat(),
                source_table=None,
                schema_state="NO_SNAPSHOT_TABLE",
                live_state="DATA_BLIND",
                vision_state="DATA_BLIND",
                can_detect_ltf_birth=False,
                can_validate_htf_gravity=False,
                table_schemas=table_schemas,
                timeframes=[],
                gaps=[],
                notes=["No snapshot table found."],
            )

        table_schemas = [_build_table_schema(conn, table, tables) for table in candidates]

        # Pick strongest source: highest extended ratio, then force_snapshots fallback.
        source_schema = sorted(
            table_schemas,
            key=lambda s: (s.extended_ratio, s.table == "force_snapshots", len(s.legacy_force_columns_present)),
            reverse=True,
        )[0]

        source_table = source_schema.table
        schema_state = source_schema.schema_state

        if schema_state == "LEGACY_FORCE_ONLY":
            notes.append("Legacy force-only schema available.")
        elif schema_state == "SCHEMA_EXTENDED_OK":
            notes.append("Extended schema appears active.")
        elif schema_state == "SCHEMA_EXTENDED_PARTIAL":
            notes.append("Extended schema partially available.")

        tf_reports: List[TimeframeVision] = []
        all_gaps: List[GapReport] = []

        for tf in timeframes:
            rows_total = _count_rows(conn, source_table, symbol, int(tf))
            rows_recent = _count_recent_rows(conn, source_table, symbol, int(tf), recent_minutes)

            latest = _latest_row_for_tf(conn, source_table, symbol, int(tf))
            latest_created_at = str(latest["created_at"]) if latest is not None else None
            latest_dt = _parse_dt(latest_created_at)
            latest_age_sec = None
            if latest_dt is not None:
                latest_age_sec = max(0.0, (checked_at - latest_dt).total_seconds())

            max_gap, gaps = _gap_reports(
                conn=conn,
                table=source_table,
                symbol=symbol,
                timeframe=int(tf),
                gap_threshold_minutes=gap_threshold_minutes,
            )
            all_gaps.extend(gaps)

            status = _timeframe_status(
                timeframe=int(tf),
                rows_total=rows_total,
                rows_recent=rows_recent,
                latest_age_sec=latest_age_sec,
                recent_minutes=recent_minutes,
            )

            tf_reports.append(
                TimeframeVision(
                    timeframe=int(tf),
                    rows_total=rows_total,
                    rows_recent=rows_recent,
                    latest_created_at=latest_created_at,
                    latest_age_sec=round(latest_age_sec, 2) if latest_age_sec is not None else None,
                    max_gap_minutes=max_gap,
                    status=status,
                )
            )

    tf_status = {r.timeframe: r.status for r in tf_reports}
    tactical_ok = all(tf_status.get(tf) == "OK" for tf in TACTICAL_TFS if tf in list(timeframes))
    structural_present = any(tf_status.get(tf) == "OK" for tf in STRUCTURAL_TFS if tf in list(timeframes))
    any_ok = any(r.status == "OK" for r in tf_reports)

    can_detect_ltf_birth = tactical_ok
    can_validate_htf_gravity = structural_present

    if can_detect_ltf_birth and can_validate_htf_gravity:
        vision_state = "TACTICAL_OK"
    elif any_ok:
        vision_state = "DATA_PARTIAL"
    else:
        vision_state = "DATA_BLIND"

    if schema_state == "SCHEMA_EXTENDED_OK" and any_ok:
        live_state = "LIVE_EXTENDED_ACTIVE"
    elif schema_state == "SCHEMA_EXTENDED_PARTIAL" and any_ok:
        live_state = "LIVE_EXTENDED_PARTIAL"
    elif schema_state == "LEGACY_FORCE_ONLY" and any_ok:
        live_state = "LIVE_LEGACY_FORCE_ONLY"
    else:
        live_state = vision_state

    if all_gaps:
        notes.append("Historical gaps detected; do not treat old gaps as live failure automatically.")

    return DBVisionReport(
        db_path=db_path,
        symbol=symbol,
        checked_at_utc=checked_at.isoformat(),
        source_table=source_table,
        schema_state=schema_state,
        live_state=live_state,
        vision_state=vision_state,
        can_detect_ltf_birth=can_detect_ltf_birth,
        can_validate_htf_gravity=can_validate_htf_gravity,
        table_schemas=table_schemas,
        timeframes=tf_reports,
        gaps=all_gaps,
        notes=notes,
    )


def format_report(report: DBVisionReport) -> str:
    lines: List[str] = []
    lines.append("=== DB VISION GUARD ===")
    lines.append(f"DB: {report.db_path}")
    lines.append(f"SYMBOL: {report.symbol}")
    lines.append(f"CHECKED_AT_UTC: {report.checked_at_utc}")
    lines.append("")
    lines.append("SCHEMA:")
    lines.append(f"source_table: {report.source_table}")
    lines.append(f"schema_state: {report.schema_state}")
    for schema in report.table_schemas:
        lines.append(
            f"- {schema.table}: {schema.schema_state} | "
            f"legacy_force={len(schema.legacy_force_columns_present)}/{len(FORCE_COLUMNS_LEGACY)} | "
            f"extended={len(schema.extended_columns_present)}/{len(EXTENDED_EXPECTED_COLUMNS)}"
        )
    lines.append("")
    lines.append("LIVE:")
    for tf in report.timeframes:
        label = f"TF{tf.timeframe}"
        age = "unknown" if tf.latest_age_sec is None else f"{tf.latest_age_sec:.0f}s"
        gap = "unknown" if tf.max_gap_minutes is None else f"{tf.max_gap_minutes:.1f}m"
        lines.append(
            f"{label:<5} {tf.status:<18} latest={tf.latest_created_at} "
            f"age={age:<8} rows_recent={tf.rows_recent:<5} rows_total={tf.rows_total:<7} max_gap={gap}"
        )
    lines.append("")
    lines.append("GAPS:")
    if not report.gaps:
        lines.append("none")
    else:
        # Show strongest gaps first, keep console compact.
        for gap in sorted(report.gaps, key=lambda g: g.gap_minutes, reverse=True)[:20]:
            lines.append(
                f"TF{gap.timeframe}: {gap.start} -> {gap.end} "
                f"{gap.gap_minutes:.1f}m {gap.status}"
            )
    lines.append("")
    lines.append("VERDICT:")
    lines.append(f"live_state: {report.live_state}")
    lines.append(f"vision_state: {report.vision_state}")
    lines.append(f"can_detect_ltf_birth: {report.can_detect_ltf_birth}")
    lines.append(f"can_validate_htf_gravity: {report.can_validate_htf_gravity}")
    if report.notes:
        lines.append("")
        lines.append("NOTES:")
        for note in report.notes:
            lines.append(f"- {note}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 DBVisionGuard V0.1")
    parser.add_argument("--db", required=True, help="Path to powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15,30,60,240")
    parser.add_argument("--recent-minutes", type=int, default=60)
    parser.add_argument("--gap-threshold-minutes", type=int, default=180)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of text report")
    parser.add_argument("--out", default=None, help="Optional output file")

    args = parser.parse_args(argv)
    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]

    report = analyze_db_vision(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=tfs,
        recent_minutes=args.recent_minutes,
        gap_threshold_minutes=args.gap_threshold_minutes,
    )

    output = report.to_json() if args.json else format_report(report)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
