"""
PowerFlow V6 — FlowEventExtractor V0.2 Extended

Mission:
    Add the extended candle/microstructure layer on top of the validated
    FlowEventExtractor V0.1.3 film.

Base film:
    PRE_FIELD
    NODE_BIRTH
    CONFIRMATION
    COUNTER_BREATH
    ABSORPTION

Extended layer:
    MICRO_WINDOW_ACTIVE
    M1_NODE_BIRTH
    VOLUME_PRESSURE_SPIKE
    PIP_RANGE_EXPANSION
    PRICE_LAG_THEN_CATCHUP
    SPREAD_FRICTION_FIELD / SPREAD_CLEAN_FIELD
    M5_TACTICAL_CONFIRMATION
    NZD_AVAILABLE

Doctrine:
    - Read-only DB.
    - No BUY/SELL.
    - No DB write.
    - No cockpit dependency.
    - V0.1.3 remains the validated legacy film engine.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import argparse
import json
import sqlite3

from pf_flow_event_extractor import (
    FlowExtractionReport,
    FlowEvent,
    extract_flow_events,
    format_report as format_base_report,
)


EXTENDED_EXTRACTOR_VERSION = "0.2.1"

EXTENDED_COLUMNS: Tuple[str, ...] = (
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


@dataclass(frozen=True)
class ExtendedRow:
    created_at: str
    dt: datetime
    symbol: str
    timeframe: int
    bid: Optional[float]
    ask: Optional[float]
    mid: Optional[float]
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    tick_volume: Optional[float]
    pip_range: Optional[float]
    pip_body: Optional[float]
    pip_change: Optional[float]
    spread_pips: Optional[float]
    force_nzd: Optional[float]
    is_closed_bar: Optional[int]


@dataclass(frozen=True)
class EventExtendedMetrics:
    phase: str
    timeframe: int
    start: str
    end: str
    rows: int
    avg_tick_volume: Optional[float]
    max_tick_volume: Optional[float]
    avg_pip_range: Optional[float]
    max_pip_range: Optional[float]
    avg_pip_body: Optional[float]
    max_abs_pip_change: Optional[float]
    avg_spread_pips: Optional[float]
    max_spread_pips: Optional[float]
    volume_ratio: Optional[float]
    pip_range_ratio: Optional[float]
    spread_ratio: Optional[float]
    flags: List[str]
    note: str


@dataclass(frozen=True)
class ExtendedFlowReport:
    symbol: str
    source_table: str
    mode: str
    start: str
    end: str
    base: Dict[str, Any]
    extended_schema_state: str
    extended_rows_loaded: Dict[str, int]
    extended_event_metrics: List[EventExtendedMetrics]
    extended_flags: List[str]
    extended_summary: str
    warnings: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


def _parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip().replace("Z", "+00:00")
    if not text:
        return None
    for candidate in (text, text.replace(" ", "T")):
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
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


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({_quote(table)})").fetchall()
    except sqlite3.Error:
        return []
    return [str(r["name"]) for r in rows]


def _has_table(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 AS ok FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return row is not None


def _f(row: sqlite3.Row, col: str, columns: Sequence[str]) -> Optional[float]:
    if col not in columns:
        return None
    value = row[col]
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _i(row: sqlite3.Row, col: str, columns: Sequence[str]) -> Optional[int]:
    if col not in columns:
        return None
    value = row[col]
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _load_extended_rows(
    db_path: str,
    symbol: str,
    start_dt: datetime,
    end_dt: datetime,
    timeframes: Sequence[int],
    source_table: str = "force_snapshots_v2",
) -> Tuple[Dict[int, List[ExtendedRow]], str, List[str]]:
    warnings: List[str] = []
    rows_by_tf: Dict[int, List[ExtendedRow]] = {int(tf): [] for tf in timeframes}

    with _connect_readonly(db_path) as conn:
        if not _has_table(conn, source_table):
            return rows_by_tf, "TABLE_MISSING", [f"{source_table} not found."]

        columns = _table_columns(conn, source_table)
        present = [c for c in EXTENDED_COLUMNS if c in columns]
        if len(present) >= 17:
            schema_state = "EXTENDED_SCHEMA_OK"
        elif len(present) > 0:
            schema_state = "EXTENDED_SCHEMA_PARTIAL"
        else:
            schema_state = "NOT_EXTENDED"

        if schema_state != "EXTENDED_SCHEMA_OK":
            warnings.append(f"Extended schema incomplete: {len(present)}/{len(EXTENDED_COLUMNS)} columns.")

        qtable = _quote(source_table)
        for tf in timeframes:
            db_rows = conn.execute(
                f"""
                SELECT *
                FROM {qtable}
                WHERE symbol = ? AND timeframe = ?
                ORDER BY created_at ASC
                """,
                (symbol, int(tf)),
            ).fetchall()

            out: List[ExtendedRow] = []
            for row in db_rows:
                dt = _parse_dt(row["created_at"]) if "created_at" in columns else None
                if dt is None or dt < start_dt or dt > end_dt:
                    continue
                out.append(
                    ExtendedRow(
                        created_at=str(row["created_at"]),
                        dt=dt,
                        symbol=symbol,
                        timeframe=int(tf),
                        bid=_f(row, "bid", columns),
                        ask=_f(row, "ask", columns),
                        mid=_f(row, "mid", columns),
                        open=_f(row, "open", columns),
                        high=_f(row, "high", columns),
                        low=_f(row, "low", columns),
                        close=_f(row, "close", columns),
                        tick_volume=_f(row, "tick_volume", columns),
                        pip_range=_f(row, "pip_range", columns),
                        pip_body=_f(row, "pip_body", columns),
                        pip_change=_f(row, "pip_change", columns),
                        spread_pips=_f(row, "spread_pips", columns),
                        force_nzd=_f(row, "force_nzd", columns),
                        is_closed_bar=_i(row, "is_closed_bar", columns),
                    )
                )
            rows_by_tf[int(tf)] = out

    return rows_by_tf, schema_state, warnings


def _vals(rows: Sequence[ExtendedRow], attr: str) -> List[float]:
    vals: List[float] = []
    for row in rows:
        value = getattr(row, attr)
        if value is None:
            continue
        try:
            vals.append(float(value))
        except (TypeError, ValueError):
            continue
    return vals


def _avg(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _mx(values: Sequence[float]) -> Optional[float]:
    if not values:
        return None
    return round(max(values), 6)


def _safe_ratio(a: Optional[float], b: Optional[float]) -> Optional[float]:
    if a is None or b is None or abs(b) < 1e-12:
        return None
    return round(a / b, 4)


def _event_rows(rows: Sequence[ExtendedRow], event: FlowEvent) -> List[ExtendedRow]:
    a = _parse_dt(event.start_dt_iso)
    b = _parse_dt(event.end_dt_iso)
    if a is None or b is None:
        return []
    return [row for row in rows if a <= row.dt <= b]


def _baseline(rows: Sequence[ExtendedRow], attr: str) -> Optional[float]:
    values = _vals(rows, attr)
    if not values:
        return None
    return round(float(median(values)), 6)


def _analyze_event_extended(
    event: FlowEvent,
    rows_by_tf: Dict[int, List[ExtendedRow]],
    baseline_rows_by_tf: Dict[int, List[ExtendedRow]],
) -> EventExtendedMetrics:
    # Use event timeframe rows first; if sparse, fallback to all LTF rows inside event.
    rows = _event_rows(rows_by_tf.get(event.timeframe, []), event)
    if not rows:
        merged: List[ExtendedRow] = []
        for tf_rows in rows_by_tf.values():
            merged.extend(_event_rows(tf_rows, event))
        rows = sorted(merged, key=lambda r: (r.dt, r.timeframe))

    baseline_rows = baseline_rows_by_tf.get(event.timeframe, [])
    if not baseline_rows:
        merged_base: List[ExtendedRow] = []
        for tf_rows in baseline_rows_by_tf.values():
            merged_base.extend(tf_rows)
        baseline_rows = merged_base

    vols = _vals(rows, "tick_volume")
    ranges = _vals(rows, "pip_range")
    bodies = [abs(v) for v in _vals(rows, "pip_body")]
    changes = [abs(v) for v in _vals(rows, "pip_change")]
    spreads = _vals(rows, "spread_pips")

    avg_volume = _avg(vols)
    max_volume = _mx(vols)
    avg_range = _avg(ranges)
    max_range = _mx(ranges)
    avg_body = _avg(bodies)
    max_change = _mx(changes)
    avg_spread = _avg(spreads)
    max_spread = _mx(spreads)

    base_volume = _baseline(baseline_rows, "tick_volume")
    base_range = _baseline(baseline_rows, "pip_range")
    base_spread = _baseline(baseline_rows, "spread_pips")

    volume_ratio = _safe_ratio(avg_volume, base_volume)
    range_ratio = _safe_ratio(avg_range, base_range)
    spread_ratio = _safe_ratio(avg_spread, base_spread)

    flags: List[str] = []

    if event.phase == "NODE_BIRTH" and event.timeframe in (1, 5):
        flags.append("M1_NODE_BIRTH" if event.timeframe == 1 else "M5_NODE_BIRTH")

    if volume_ratio is not None and volume_ratio >= 1.50:
        flags.append("VOLUME_PRESSURE_SPIKE")

    if range_ratio is not None and range_ratio >= 1.35:
        flags.append("PIP_RANGE_EXPANSION")

    if spread_ratio is not None and spread_ratio >= 1.60:
        flags.append("SPREAD_FRICTION_FIELD")
    elif avg_spread is not None:
        flags.append("SPREAD_CLEAN_FIELD")

    if event.phase == "NODE_BIRTH" and event.price_response == "PRICE_LAG":
        flags.append("PRICE_LAG_AT_NODE")

    if event.phase == "CONFIRMATION" and event.price_response == "PRICE_PAYING":
        flags.append("PRICE_CATCHUP_CONFIRMATION")

    if event.phase == "CONFIRMATION" and event.timeframe in (5, 15):
        flags.append("M5_TACTICAL_CONFIRMATION" if event.timeframe == 5 else "M15_SCENE_CONFIRMATION")

    if any(row.force_nzd is not None for row in rows):
        flags.append("NZD_AVAILABLE")

    if event.phase == "NODE_BIRTH":
        is_micro_node = "M1_NODE_BIRTH" in flags or "M5_NODE_BIRTH" in flags
        has_price_lag = "PRICE_LAG_AT_NODE" in flags
        has_pressure = "VOLUME_PRESSURE_SPIKE" in flags or "PIP_RANGE_EXPANSION" in flags

        if is_micro_node and has_price_lag and has_pressure:
            flags.append("MICRO_WINDOW_ACTIVE_STRONG")
            flags.append("MICRO_WINDOW_ACTIVE")
        elif is_micro_node and (has_price_lag or has_pressure):
            flags.append("MICRO_WINDOW_ACTIVE_WEAK")
            flags.append("MICRO_WINDOW_ACTIVE")

    note_parts: List[str] = []
    if not rows:
        note_parts.append("No extended rows inside event range.")
    if "MICRO_WINDOW_ACTIVE_STRONG" in flags:
        note_parts.append("Strong micro-window evidence: node + lag/pressure confirmation.")
    elif "MICRO_WINDOW_ACTIVE_WEAK" in flags:
        note_parts.append("Weak micro-window evidence: node detected but pressure layer is not yet strong.")
    elif "MICRO_WINDOW_ACTIVE" in flags:
        note_parts.append("Node has extended micro-window evidence.")
    if "SPREAD_FRICTION_FIELD" in flags:
        note_parts.append("Spread friction detected in event.")
    if "PRICE_LAG_AT_NODE" in flags:
        note_parts.append("Forces moved before price response.")
    if "PRICE_CATCHUP_CONFIRMATION" in flags:
        note_parts.append("Price catch-up visible on confirmation.")

    return EventExtendedMetrics(
        phase=event.phase,
        timeframe=event.timeframe,
        start=event.start,
        end=event.end,
        rows=len(rows),
        avg_tick_volume=avg_volume,
        max_tick_volume=max_volume,
        avg_pip_range=avg_range,
        max_pip_range=max_range,
        avg_pip_body=avg_body,
        max_abs_pip_change=max_change,
        avg_spread_pips=avg_spread,
        max_spread_pips=max_spread,
        volume_ratio=volume_ratio,
        pip_range_ratio=range_ratio,
        spread_ratio=spread_ratio,
        flags=flags,
        note=" ".join(note_parts) if note_parts else "Extended event measured.",
    )


def _dedupe(items: Iterable[str]) -> List[str]:
    out: List[str] = []
    for item in items:
        if item not in out:
            out.append(item)
    return out


def extract_flow_events_extended(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    timeframes: Iterable[int] = (1, 5, 15),
    source_table: str = "force_snapshots_v2",
    fallback_to_legacy: bool = True,
) -> ExtendedFlowReport:
    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)
    if start_dt is None or end_dt is None:
        raise ValueError("Invalid start/end datetime.")
    if end_dt <= start_dt:
        raise ValueError("end must be after start.")

    tfs = [int(tf) for tf in timeframes]
    warnings: List[str] = []

    # Base film. Force V2 first. If V2 has not enough rows, fallback to auto/legacy.
    base_report = extract_flow_events(
        db_path=db_path,
        symbol=symbol,
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        timeframes=tfs,
        source_table=source_table,
    )

    total_base_rows = sum(base_report.rows_loaded.values())
    if fallback_to_legacy and total_base_rows <= 1:
        warnings.append("V2 sparse for base film; fallback to auto/legacy base extractor.")
        base_report = extract_flow_events(
            db_path=db_path,
            symbol=symbol,
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
            timeframes=tfs,
            source_table=None,
        )

    rows_by_tf, schema_state, ext_warnings = _load_extended_rows(
        db_path=db_path,
        symbol=symbol,
        start_dt=start_dt,
        end_dt=end_dt,
        timeframes=tfs,
        source_table=source_table,
    )
    warnings.extend(ext_warnings)

    rows_loaded = {f"TF{tf}": len(rows_by_tf.get(tf, [])) for tf in tfs}

    metrics: List[EventExtendedMetrics] = []
    for ev in base_report.events:
        metrics.append(_analyze_event_extended(ev, rows_by_tf, rows_by_tf))

    all_flags = _dedupe(flag for m in metrics for flag in m.flags)

    # Sequence-level flags.
    has_node_lag = any(m.phase == "NODE_BIRTH" and "PRICE_LAG_AT_NODE" in m.flags for m in metrics)
    has_confirm_catchup = any(m.phase == "CONFIRMATION" and "PRICE_CATCHUP_CONFIRMATION" in m.flags for m in metrics)
    if has_node_lag and has_confirm_catchup:
        all_flags.append("PRICE_LAG_THEN_CATCHUP")

    if any(m.phase == "NODE_BIRTH" and "MICRO_WINDOW_ACTIVE_STRONG" in m.flags for m in metrics):
        all_flags.append("MICRO_WINDOW_ACTIVE_STRONG")
        all_flags.append("MICRO_WINDOW_ACTIVE")
    elif any(m.phase == "NODE_BIRTH" and "MICRO_WINDOW_ACTIVE_WEAK" in m.flags for m in metrics):
        all_flags.append("MICRO_WINDOW_ACTIVE_WEAK")
        all_flags.append("MICRO_WINDOW_ACTIVE")
    elif any(m.phase == "NODE_BIRTH" and "MICRO_WINDOW_ACTIVE" in m.flags for m in metrics):
        all_flags.append("MICRO_WINDOW_ACTIVE")

    if any("NZD_AVAILABLE" in m.flags for m in metrics):
        all_flags.append("NZD_AVAILABLE")

    all_flags = _dedupe(all_flags)

    if sum(rows_loaded.values()) == 0:
        warnings.append("No extended V2 rows in selected window.")

    if "MICRO_WINDOW_ACTIVE_STRONG" in all_flags:
        summary = "EXTENDED MICRO WINDOW ACTIVE STRONG"
    elif "MICRO_WINDOW_ACTIVE_WEAK" in all_flags:
        summary = "EXTENDED MICRO WINDOW ACTIVE WEAK"
    elif "MICRO_WINDOW_ACTIVE" in all_flags:
        summary = "EXTENDED MICRO WINDOW ACTIVE"
    elif schema_state == "EXTENDED_SCHEMA_OK" and sum(rows_loaded.values()) > 0:
        summary = "EXTENDED DATA PRESENT — NO MICRO SPIKE CONFIRMED"
    else:
        summary = "EXTENDED DATA PARTIAL"

    return ExtendedFlowReport(
        symbol=symbol,
        source_table=source_table,
        mode="EXTENDED_V02",
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        base=base_report.to_dict(),
        extended_schema_state=schema_state,
        extended_rows_loaded=rows_loaded,
        extended_event_metrics=metrics,
        extended_flags=all_flags,
        extended_summary=summary,
        warnings=warnings,
    )


def format_extended_report(report: ExtendedFlowReport, include_base: bool = True) -> str:
    lines: List[str] = []
    lines.append("=== POWERFLOW FLOW EVENT EXTRACTOR EXTENDED ===")
    lines.append(f"VERSION: {EXTENDED_EXTRACTOR_VERSION}")
    lines.append(f"SYMBOL: {report.symbol}")
    lines.append(f"WINDOW: {report.start} -> {report.end}")
    lines.append(f"SOURCE_TABLE: {report.source_table}")
    lines.append(f"MODE: {report.mode}")
    lines.append(f"EXTENDED_SCHEMA: {report.extended_schema_state}")
    lines.append("")
    lines.append("EXTENDED ROWS:")
    for tf, n in report.extended_rows_loaded.items():
        lines.append(f"{tf}: {n}")

    lines.append("")
    lines.append("EXTENDED FLAGS:")
    if report.extended_flags:
        for flag in report.extended_flags:
            lines.append(f"- {flag}")
    else:
        lines.append("none")

    lines.append("")
    lines.append("EXTENDED EVENTS:")
    if not report.extended_event_metrics:
        lines.append("none")
    else:
        for m in report.extended_event_metrics:
            flags = ",".join(m.flags) if m.flags else "-"
            lines.append(
                f"{m.start}->{m.end} TF{m.timeframe} {m.phase:<15} rows={m.rows:<3} "
                f"vol={m.avg_tick_volume} vr={m.volume_ratio} "
                f"range={m.avg_pip_range} rr={m.pip_range_ratio} "
                f"spread={m.avg_spread_pips} sr={m.spread_ratio} flags={flags}"
            )
            lines.append(f"  note: {m.note}")

    lines.append("")
    lines.append("SUMMARY:")
    lines.append(report.extended_summary)

    if report.warnings:
        lines.append("")
        lines.append("WARNINGS:")
        for w in report.warnings:
            lines.append(f"- {w}")

    if include_base:
        try:
            base_report = FlowExtractionReport(
                symbol=report.base["symbol"],
                mode=report.base["mode"],
                source_table=report.base["source_table"],
                start=report.base["start"],
                end=report.base["end"],
                timeframes=report.base["timeframes"],
                rows_loaded=report.base["rows_loaded"],
                events=[FlowEvent(**ev) for ev in report.base["events"]],
                candidates=[],
                warnings=report.base.get("warnings", []),
            )
            lines.append("")
            lines.append("=" * 90)
            lines.append(format_base_report(base_report))
        except Exception:
            lines.append("")
            lines.append("BASE_REPORT: available in JSON only.")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 FlowEventExtractor V0.2 Extended")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframes", default="1,5,15")
    parser.add_argument("--source-table", default="force_snapshots_v2")
    parser.add_argument("--no-fallback-legacy", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-base", action="store_true")
    parser.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]

    report = extract_flow_events_extended(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        timeframes=tfs,
        source_table=args.source_table,
        fallback_to_legacy=not args.no_fallback_legacy,
    )

    output = report.to_json() if args.json else format_extended_report(report, include_base=not args.no_base)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
