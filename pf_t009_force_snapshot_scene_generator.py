"""PowerFlow T009/B9 force snapshot derived scene generator.

Read-only bridge:
    powerflow.db / force_snapshots_v2 -> t009_sequence_summary.json

This module does not claim to recover existing B9 summaries. It creates a
source-aware deterministic proxy summary from explicit force_snapshots_v2 bars.
It never writes to powerflow.db or tick_archive.db.
"""
from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable, Mapping, Sequence

VERSION = "T009_FORCE_SNAPSHOT_SCENE_GENERATOR_V0"
SUMMARY_RECOVERY_TYPE = "FORCE_SNAPSHOT_DERIVED"
DEFAULT_RAW_LIMITS = [
    "force_snapshots_v2 proxy source, not recovered existing B9 summary",
    "M1_BAR_PROXY / RECONSTRUCTED when timeframe=1",
    "higher timeframe proxy if M1 coverage is missing or partial",
    "not MT5 raw tick footprint",
    "no participant identification",
    "no central orderbook",
]

DATE_TARGETS_DEFAULT = (
    "2026-05-04",
    "2026-05-05",
    "2026-05-07",
    "2026-05-08",
    "2026-05-11",
    "2026-05-12",
    "2026-05-13",
    "2026-05-14",
)

@dataclass(frozen=True)
class GeneratorConfig:
    db_path: Path
    output_dir: Path
    symbol: str = "GBPUSD"
    dates: tuple[str, ...] = DATE_TARGETS_DEFAULT
    preferred_timeframes: tuple[int, ...] = (1, 5, 15, 30, 60)
    pip_size: float = 0.0001
    max_window_minutes: int = 60
    max_gap_factor: float = 2.5
    min_rows_by_timeframe: dict[int, int] = field(default_factory=lambda: {
        1: 30,
        5: 8,
        15: 4,
        30: 3,
        60: 2,
    })
    confidence_cap_m1: float = 0.35
    confidence_cap_higher_tf: float = 0.25
    allow_partial_days: bool = True

@dataclass(frozen=True)
class SnapshotBar:
    ts: datetime
    symbol: str
    timeframe: int
    open: float
    high: float
    low: float
    close: float
    mid: float | None
    spread_pips: float | None
    tick_volume: float | None
    pip_range: float | None
    pip_body: float | None
    pip_change: float | None
    force_gbp: float | None
    force_usd: float | None
    force_eur: float | None
    force_jpy: float | None
    force_cad: float | None
    force_chf: float | None
    force_aud: float | None
    force_nzd: float | None


def parse_iso_dt(value: Any) -> datetime | None:
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "+00:00")


def safe_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return f


def _connect_read_only(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def _table_columns(con: sqlite3.Connection, table: str) -> set[str]:
    cur = con.cursor()
    cur.execute(f'PRAGMA table_info("{table}")')
    return {row[1] for row in cur.fetchall()}


def _has_force_snapshots_v2(con: sqlite3.Connection) -> bool:
    cur = con.cursor()
    cur.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='force_snapshots_v2'")
    return cur.fetchone() is not None


def _load_bars_for_date(con: sqlite3.Connection, symbol: str, day: str, timeframe: int) -> list[SnapshotBar]:
    if not _has_force_snapshots_v2(con):
        return []
    cols = _table_columns(con, "force_snapshots_v2")
    required = {"created_at", "symbol", "timeframe", "open", "high", "low", "close"}
    if not required.issubset(cols):
        missing = ", ".join(sorted(required - cols))
        raise RuntimeError(f"force_snapshots_v2 missing required columns: {missing}")

    select_cols = [
        "created_at", "bar_time", "symbol", "timeframe", "open", "high", "low", "close", "mid",
        "spread_pips", "tick_volume", "pip_range", "pip_body", "pip_change",
        "force_gbp", "force_usd", "force_eur", "force_jpy", "force_cad", "force_chf", "force_aud", "force_nzd",
    ]
    actual_select = [c if c in cols else f"NULL AS {c}" for c in select_cols]
    sql = f'''
    SELECT {", ".join(actual_select)}
    FROM force_snapshots_v2
    WHERE symbol = ?
      AND timeframe = ?
      AND substr(created_at, 1, 10) = ?
    ORDER BY created_at ASC, bar_time ASC
    '''
    cur = con.cursor()
    cur.execute(sql, (symbol, timeframe, day))
    bars: list[SnapshotBar] = []
    for row in cur.fetchall():
        record = dict(zip(select_cols, row))
        ts = parse_iso_dt(record.get("created_at")) or parse_iso_dt(record.get("bar_time"))
        if ts is None:
            continue
        o = safe_float(record.get("open"))
        h = safe_float(record.get("high"))
        l = safe_float(record.get("low"))
        c = safe_float(record.get("close"))
        if o is None or h is None or l is None or c is None:
            continue
        bars.append(SnapshotBar(
            ts=ts,
            symbol=str(record.get("symbol") or symbol),
            timeframe=int(record.get("timeframe") or timeframe),
            open=o,
            high=h,
            low=l,
            close=c,
            mid=safe_float(record.get("mid")),
            spread_pips=safe_float(record.get("spread_pips")),
            tick_volume=safe_float(record.get("tick_volume")),
            pip_range=safe_float(record.get("pip_range")),
            pip_body=safe_float(record.get("pip_body")),
            pip_change=safe_float(record.get("pip_change")),
            force_gbp=safe_float(record.get("force_gbp")),
            force_usd=safe_float(record.get("force_usd")),
            force_eur=safe_float(record.get("force_eur")),
            force_jpy=safe_float(record.get("force_jpy")),
            force_cad=safe_float(record.get("force_cad")),
            force_chf=safe_float(record.get("force_chf")),
            force_aud=safe_float(record.get("force_aud")),
            force_nzd=safe_float(record.get("force_nzd")),
        ))
    return bars


def choose_timeframe(con: sqlite3.Connection, cfg: GeneratorConfig, day: str) -> tuple[int | None, list[SnapshotBar], dict[int, int]]:
    counts: dict[int, int] = {}
    loaded: dict[int, list[SnapshotBar]] = {}
    for tf in cfg.preferred_timeframes:
        bars = _load_bars_for_date(con, cfg.symbol, day, tf)
        loaded[tf] = bars
        counts[tf] = len(bars)

    # Prefer M1 if there is any usable scene mass. Fallback to coarser TF only when M1 is absent/sparse.
    for tf in cfg.preferred_timeframes:
        min_rows = cfg.min_rows_by_timeframe.get(tf, 2)
        if counts.get(tf, 0) >= min_rows:
            return tf, loaded[tf], counts
    return None, [], counts


def split_into_windows(bars: Sequence[SnapshotBar], timeframe: int, max_window_minutes: int, max_gap_factor: float) -> list[list[SnapshotBar]]:
    if not bars:
        return []
    windows: list[list[SnapshotBar]] = []
    current: list[SnapshotBar] = [bars[0]]
    max_duration = timedelta(minutes=max_window_minutes)
    max_gap = timedelta(minutes=max(1, timeframe) * max_gap_factor)
    for bar in bars[1:]:
        prev = current[-1]
        if (bar.ts - prev.ts) > max_gap or (bar.ts - current[0].ts) >= max_duration:
            windows.append(current)
            current = [bar]
        else:
            current.append(bar)
    if current:
        windows.append(current)
    return windows


def pips(value: float, pip_size: float) -> float:
    return value / pip_size


def _avg(values: Iterable[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return None
    return sum(clean) / len(clean)


def _safe_median(values: Iterable[float | None]) -> float | None:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return None
    return float(median(clean))


def classify_window(bars: Sequence[SnapshotBar], pip_size: float) -> tuple[str, str, str]:
    first, last = bars[0], bars[-1]
    delta_pips = pips(last.close - first.open, pip_size)
    high = max(b.high for b in bars)
    low = min(b.low for b in bars)
    range_pips = max(0.0, pips(high - low, pip_size))
    efficiency = abs(delta_pips) / range_pips if range_pips > 0 else 0.0
    tick_values = [b.tick_volume for b in bars]
    tick_med = _safe_median(tick_values) or 0.0
    tick_avg = _avg(tick_values) or 0.0
    force_delta = None
    if first.force_gbp is not None and first.force_usd is not None and last.force_gbp is not None and last.force_usd is not None:
        force_delta = (last.force_gbp - last.force_usd) - (first.force_gbp - first.force_usd)
    force_abs = abs(force_delta) if force_delta is not None else 0.0

    if range_pips >= 6.0 and abs(delta_pips) <= max(1.25, range_pips * 0.22):
        role = "FLOW_ROTATIONAL"
        auction = "AUCTION_ROTATIONAL_BALANCE"
        label = "Rotation / respiration de zone"
    elif range_pips >= 4.0 and efficiency >= 0.45:
        role = "FLOW_DIRECTIONAL_DISPLACEMENT"
        auction = "AUCTION_DIRECTIONAL_ACCEPTANCE"
        label = "Déplacement directionnel proxy"
    elif range_pips >= 3.0 and tick_avg > 0 and tick_med > 0 and tick_avg >= tick_med * 1.20 and efficiency < 0.35:
        role = "FLOW_FRICTION_ABSORPTION_LIKE"
        auction = "AUCTION_FRICTION_ABSORPTION_LIKE"
        label = "Friction / absorption-like proxy"
    elif range_pips < 2.5 and force_abs < 0.25:
        role = "FLOW_BALANCED_AUCTION"
        auction = "AUCTION_ROTATIONAL_BALANCE"
        label = "Auction équilibrée proxy"
    else:
        role = "FLOW_WEAK_DIRECTIONAL"
        auction = "AUCTION_EXHAUSTION_LIKE" if efficiency < 0.35 else "AUCTION_DIRECTIONAL_ACCEPTANCE"
        label = "Flux faible / transition proxy"
    return role, auction, label


def window_to_moment(bars: Sequence[SnapshotBar], cfg: GeneratorConfig, window_index: int, day_quality: str) -> dict[str, Any]:
    first, last = bars[0], bars[-1]
    high = max(b.high for b in bars)
    low = min(b.low for b in bars)
    delta_pips = round(pips(last.close - first.open, cfg.pip_size), 3)
    range_pips = round(max(0.0, pips(high - low, cfg.pip_size)), 3)
    body_pips = round(pips(last.close - first.open, cfg.pip_size), 3)
    role, auction, label = classify_window(bars, cfg.pip_size)
    confidence_cap = cfg.confidence_cap_m1 if first.timeframe == 1 else cfg.confidence_cap_higher_tf
    tf_source = "M1_BAR_PROXY" if first.timeframe == 1 else f"TF{first.timeframe}_BAR_PROXY"
    data_visibility = "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED"
    return {
        "scene_id": f"FSV2_{cfg.symbol}_{first.ts:%Y%m%d}_{first.ts:%H%M}_{last.ts:%H%M}_{window_index:03d}",
        "time_start": iso_utc(first.ts),
        "time_end": iso_utc(last.ts + timedelta(minutes=max(1, first.timeframe))),
        "symbol": cfg.symbol,
        "window": f"{first.ts:%H%M}_{last.ts:%H%M}",
        "label_fr": label,
        "moment_type": role,
        "b9_natural_flow_role": role,
        "b9_auction_state": auction,
        "source_mode": tf_source,
        "data_visibility": data_visibility,
        "summary_recovery_type": SUMMARY_RECOVERY_TYPE,
        "summary_recovery_version": VERSION,
        "confidence_cap": confidence_cap,
        "b9_confidence_cap": confidence_cap,
        "source_quality": day_quality,
        "raw_limits": DEFAULT_RAW_LIMITS,
        "bar_count": len(bars),
        "timeframe": first.timeframe,
        "center_start": round(first.open, 6),
        "center_end": round(last.close, 6),
        "open": round(first.open, 6),
        "high": round(high, 6),
        "low": round(low, 6),
        "close": round(last.close, 6),
        "proxy_delta_pips": delta_pips,
        "proxy_range_pips": range_pips,
        "proxy_body_pips": body_pips,
        "proxy_tick_volume_sum": round(sum(b.tick_volume or 0 for b in bars), 3),
        "proxy_spread_avg_pips": round(_avg([b.spread_pips for b in bars]) or 0.0, 4),
        "force_gbp_start": first.force_gbp,
        "force_gbp_end": last.force_gbp,
        "force_usd_start": first.force_usd,
        "force_usd_end": last.force_usd,
        "force_gbp_usd_delta": None if None in (first.force_gbp, first.force_usd, last.force_gbp, last.force_usd) else round((last.force_gbp - last.force_usd) - (first.force_gbp - first.force_usd), 6),
        "zone_memory": {
            "touch_count": 0,
            "last_tested": None,
            "retest_status": "RETEST_NOT_VISIBLE_IN_FORCE_SNAPSHOT_DERIVED_V0",
        },
        "retest_touch_count": 0,
        "retest_first_touch_time": None,
        "retest_last_touch_time": None,
        "retest_delay_seconds": None,
        "retest_acceptance_dwell_seconds": None,
        "retest_rejection_speed_pips_per_min": None,
        "retest_zone_distance_pips": None,
        "retest_outcome_hint": "RETEST_OUTCOME_NOT_VISIBLE",
        "retest_source_field_confidence": 0.0,
        "notes": [
            "Deterministic scene derived from force_snapshots_v2 bars.",
            "No scene was invented freely; no raw tick footprint claim.",
        ],
    }


def coverage_status(day: str, timeframe: int, bars: Sequence[SnapshotBar]) -> str:
    if not bars:
        return "NO_PROXY_COVERAGE"
    minutes_span = max(1.0, (bars[-1].ts - bars[0].ts).total_seconds() / 60.0)
    expected = max(1.0, minutes_span / max(1, timeframe))
    ratio = len(bars) / expected
    if timeframe == 1 and len(bars) >= 1200 and ratio >= 0.80:
        return "FULL_DAY_M1_PROXY"
    if timeframe == 5 and len(bars) >= 250 and ratio >= 0.80:
        return "FULL_DAY_TF5_PROXY"
    if len(bars) >= 30:
        return "PARTIAL_PROXY_COVERAGE"
    return "SPARSE_PROXY_COVERAGE"


def build_summary_for_date(con: sqlite3.Connection, cfg: GeneratorConfig, day: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    tf, bars, counts = choose_timeframe(con, cfg, day)
    base_report = {
        "date": day,
        "symbol": cfg.symbol,
        "selected_timeframe": tf,
        "row_counts_by_timeframe": counts,
        "summary_recovery_type": SUMMARY_RECOVERY_TYPE,
    }
    if tf is None or not bars:
        base_report.update({
            "status": "NO_FORCE_SNAPSHOT_PROXY_SOURCE_FOUND",
            "moment_count": 0,
            "notes": "No deterministic summary generated because no usable force_snapshots_v2 coverage was found.",
        })
        return None, base_report

    quality = coverage_status(day, tf, bars)
    if quality == "SPARSE_PROXY_COVERAGE" and not cfg.allow_partial_days:
        base_report.update({
            "status": "SPARSE_PROXY_COVERAGE_SKIPPED",
            "moment_count": 0,
            "notes": "Sparse source coverage skipped by configuration.",
        })
        return None, base_report

    windows = split_into_windows(bars, tf, cfg.max_window_minutes, cfg.max_gap_factor)
    moments = [window_to_moment(w, cfg, i + 1, quality) for i, w in enumerate(windows) if w]
    if not moments:
        base_report.update({
            "status": "NO_MOMENTS_DERIVED",
            "moment_count": 0,
            "notes": "Rows were present but no deterministic moments were produced.",
        })
        return None, base_report

    summary = {
        "version": VERSION,
        "summary_recovery_type": SUMMARY_RECOVERY_TYPE,
        "symbol": cfg.symbol,
        "date": day,
        "time_start": moments[0]["time_start"],
        "time_end": moments[-1]["time_end"],
        "source_mode": "M1_BAR_PROXY" if tf == 1 else f"TF{tf}_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
        "confidence_cap": cfg.confidence_cap_m1 if tf == 1 else cfg.confidence_cap_higher_tf,
        "source_quality": quality,
        "raw_limits": DEFAULT_RAW_LIMITS,
        "metadata": {
            "generator_version": VERSION,
            "summary_recovery_type": SUMMARY_RECOVERY_TYPE,
            "source_table": "force_snapshots_v2",
            "source_db": str(cfg.db_path),
            "read_only_db": True,
            "selected_timeframe": tf,
            "row_counts_by_timeframe": counts,
            "bar_count": len(bars),
            "moment_count": len(moments),
            "coverage_status": quality,
            "no_trade_instruction": True,
            "no_footprint_claim": True,
            "rules": [
                "Select best available force_snapshots_v2 timeframe by deterministic row thresholds.",
                "Split contiguous bars into <= max_window_minutes windows and on large gaps.",
                "Classify each window from OHLC range, displacement efficiency, tick_volume proxy, and force GBP/USD variation.",
                "Retest native evidence is not inferred in V0; retest fields remain NOT_VISIBLE.",
            ],
        },
        "moments": moments,
    }
    base_report.update({
        "status": "GENERATED_FORCE_SNAPSHOT_DERIVED_SUMMARY",
        "moment_count": len(moments),
        "time_start": summary["time_start"],
        "time_end": summary["time_end"],
        "source_quality": quality,
    })
    return summary, base_report


def safe_window_name(summary: Mapping[str, Any]) -> str:
    start = parse_iso_dt(summary.get("time_start"))
    end = parse_iso_dt(summary.get("time_end"))
    date = str(summary.get("date") or (start.strftime("%Y%m%d") if start else "unknown")).replace("-", "")
    if start and end:
        return f"{date}_{start:%H%M}_{end:%H%M}"
    return f"{date}_unknown"


def write_summary(summary: Mapping[str, Any], out_root: Path) -> Path:
    folder = out_root / "force_snapshot_derived_summaries" / safe_window_name(summary)
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / "t009_sequence_summary.json"
    out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def generate(cfg: GeneratorConfig) -> dict[str, Any]:
    cfg.output_dir.mkdir(parents=True, exist_ok=True)
    generated: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []
    with _connect_read_only(cfg.db_path) as con:
        for day in cfg.dates:
            summary, report = build_summary_for_date(con, cfg, day)
            if summary is not None:
                out = write_summary(summary, cfg.output_dir)
                report["output_summary_path"] = str(out)
                generated.append({"date": day, "path": str(out), "moment_count": report.get("moment_count", 0)})
            else:
                report["output_summary_path"] = ""
            reports.append(report)
    write_reports(cfg, reports, generated)
    return {
        "output_dir": str(cfg.output_dir),
        "generated_count": len(generated),
        "generated": generated,
        "reports": reports,
    }


def write_reports(cfg: GeneratorConfig, reports: Sequence[Mapping[str, Any]], generated: Sequence[Mapping[str, Any]]) -> None:
    inv = cfg.output_dir / "B9_FORCE_SNAPSHOT_DERIVED_SUMMARY_INVENTORY_20260504_20260514.md"
    missing = cfg.output_dir / "B9_FORCE_SNAPSHOT_DERIVED_MISSING_20260504_20260514.md"
    plan = cfg.output_dir / "B9_FORCE_SNAPSHOT_DERIVED_CONVERSION_RULES_20260504_20260514.md"
    csv = cfg.output_dir / "B9_FORCE_SNAPSHOT_DERIVED_SUMMARY_INVENTORY_20260504_20260514.csv"

    header = [
        "date", "window", "source_table", "source_type", "contains_explicit_b9_moments_yes_no",
        "moment_count", "conversion_status", "output_summary_path", "notes",
    ]
    lines = [",".join(header)]
    md_rows = []
    missing_rows = []
    for r in reports:
        output = str(r.get("output_summary_path") or "")
        status = str(r.get("status") or "")
        ts = str(r.get("time_start") or "")
        te = str(r.get("time_end") or "")
        window = ""
        if ts and te:
            sdt = parse_iso_dt(ts); edt = parse_iso_dt(te)
            if sdt and edt:
                window = f"{sdt:%H%M}_{edt:%H%M}"
        explicit = "NO_SOURCE_IS_FORCE_SNAPSHOT_DERIVED"
        notes = str(r.get("notes") or r.get("source_quality") or "")
        row = [
            str(r.get("date") or ""), window, "force_snapshots_v2", SUMMARY_RECOVERY_TYPE,
            explicit, str(r.get("moment_count") or 0), status, output, notes,
        ]
        lines.append(",".join('"' + x.replace('"', '""') + '"' for x in row))
        md_rows.append(row)
        if not output:
            missing_rows.append(r)

    csv.write_text("\n".join(lines) + "\n", encoding="utf-8")

    inv_text = [
        "# B9 Force Snapshot Derived Summary Inventory 2026-05-04 -> 2026-05-14",
        "",
        "## Verdict",
        "",
        "```text",
        f"SUMMARY_RECOVERY_TYPE = {SUMMARY_RECOVERY_TYPE}",
        "NOT_RECOVERED_EXISTING_SUMMARY = true",
        f"GENERATED_SUMMARIES = {len(generated)}",
        "SOURCE_TABLE = force_snapshots_v2",
        "POWERFLOW_DB_ACCESS = read-only",
        "TICK_ARCHIVE_DB_ACCESS = none",
        "NO_BUY_SELL = true",
        "NO_FOOTPRINT_CLAIM = true",
        "```",
        "",
        "## Inventory",
        "",
        "| date | window | source_file | source_type | contains_explicit_b9_moments_yes_no | moment_count | conversion_status | output_summary_path | notes |",
        "| --- | --- | --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in md_rows:
        inv_text.append("| " + " | ".join(row) + " |")
    inv.write_text("\n".join(inv_text) + "\n", encoding="utf-8")

    miss_text = [
        "# B9 Force Snapshot Derived Missing Dates 2026-05-04 -> 2026-05-14",
        "",
        "Dates below were not generated because no usable force_snapshots_v2 proxy coverage passed deterministic thresholds.",
        "",
        "| date | status | row_counts_by_timeframe | notes |",
        "| --- | --- | --- | --- |",
    ]
    for r in missing_rows:
        miss_text.append(f"| {r.get('date')} | {r.get('status')} | {r.get('row_counts_by_timeframe')} | {r.get('notes','')} |")
    missing.write_text("\n".join(miss_text) + "\n", encoding="utf-8")

    plan.write_text("\n".join([
        "# B9 Force Snapshot Derived Conversion Rules 2026-05-04 -> 2026-05-14",
        "",
        "This pack does not recover existing summaries. It creates deterministic source-aware summaries from force_snapshots_v2.",
        "",
        "## Rules",
        "",
        "1. Read powerflow.db in SQLite read-only mode only.",
        "2. Never write powerflow.db or tick_archive.db.",
        "3. Use force_snapshots_v2 rows only; no raw MT5-only scene invention.",
        "4. Mark every output with summary_recovery_type = FORCE_SNAPSHOT_DERIVED.",
        "5. Mark data_visibility = RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED.",
        "6. Keep confidence_cap at 0.35 for M1 and 0.25 for higher timeframe fallback.",
        "7. Split bars into deterministic windows and classify flow from OHLC/range/efficiency/tick_volume/force variation.",
        "8. Do not infer native retest proof; retest fields remain NOT_VISIBLE in V0.",
        "9. No BUY/SELL words and no trading recommendation.",
        "10. No footprint, participant, or central orderbook claim.",
        "",
        "## Cap",
        "",
        "Raw MT5 donne la texture. B9 summaries donnent les scènes. Ici, les scènes sont dérivées d'une source proxy explicite, pas inventées depuis le raw.",
    ]) + "\n", encoding="utf-8")
