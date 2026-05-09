"""
PowerFlow V6 - pf_temporal_patterns_cockpit.py
Version: V0.1

Mission:
  Plug-in read-only pour ajouter les patterns temporels au cockpit sans casser
  run_cockpit_field.py existant.

Source:
  force_snapshots

Depends:
  pf_temporal_patterns.py
    - temporal_density
    - extreme_zone_breathing
    - detect_angular_alignment

Sortie:
  bloc texte compact:
    TEMPORAL_PATTERNS:
    BREATHING: ...
    PULLURE: ...
    DENSITY: ...
    ANGLE: ...

Doctrine:
  Lire vite.
  Nommer le champ.
  Aucune ecriture DB.
"""

from __future__ import annotations

import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple

from pf_temporal_patterns import (
    temporal_density,
    extreme_zone_breathing,
    detect_angular_alignment,
)


DEFAULT_CURRENCIES = ["GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"]


@dataclass
class DensityEvent:
    timeframe: int
    currency: str
    bar_time: str
    density: float
    bar_index: int


@dataclass
class BreathingEvent:
    timeframe: int
    currency: str
    bar_time: str
    pullback_count: int
    compression_count: int
    breathing_density: float
    energy_accumulation: float
    bars_in_zone: int
    side: str
    mode: str
    current_value: float
    bar_index: int


@dataclass
class AngularEvent:
    timeframe: int
    bar_time: str
    aligned_devises: List[str]
    common_angle: float
    alignment_quality: float
    direction_changed_count: int
    angles: Dict[str, float]
    bar_index: int


@dataclass
class DensityField:
    timeframe: int
    currency: str
    start_time: str
    end_time: str
    event_count: int
    density_max: float
    density_avg: float
    label: str
    priority_score: float


@dataclass
class BreathingField:
    timeframe: int
    currency: str
    side: str
    start_time: str
    end_time: str
    event_count: int
    energy_max: float
    energy_avg: float
    pullures_total: int
    compressions_total: int
    breathing_density_max: float
    bars_zone_max: int
    label: str
    priority_score: float


@dataclass
class TemporalCockpitResult:
    lines: List[str]
    breathing_fields: List[BreathingField]
    density_fields: List[DensityField]
    angular_nodes: List[AngularEvent]
    rows_by_tf: Dict[int, int]
    density_cutoff: float


def parse_time(value: str) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S")
        except ValueError:
            try:
                dt = datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def minutes_between(a: str, b: str) -> float:
    da = parse_time(a)
    db = parse_time(b)
    if da is None or db is None:
        return 0.0
    return abs((db - da).total_seconds()) / 60.0


def tf_label(tf: int) -> str:
    labels = {
        1: "M1",
        5: "M5",
        15: "M15",
        30: "M30",
        60: "H1",
        240: "H4",
        1440: "D1",
        10080: "W1",
    }
    return labels.get(int(tf), str(tf))


def fmt_range(start: str, end: str) -> str:
    if start == end:
        return start
    return f"{start} -> {end}"


def connect_readonly(db_path: str) -> sqlite3.Connection:
    abs_path = os.path.abspath(db_path)
    uri = "file:" + abs_path.replace("\\", "/") + "?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def resolve_force_columns(conn: sqlite3.Connection, currencies: Sequence[str]) -> Dict[str, str]:
    cols = set(table_columns(conn, "force_snapshots"))
    mapping: Dict[str, str] = {}
    for cur in currencies:
        col = "force_" + cur.lower()
        if col in cols:
            mapping[cur] = col
    if not mapping:
        raise RuntimeError("No force_* columns found in force_snapshots.")
    return mapping


def percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    pct = max(0.0, min(100.0, float(pct)))
    if pct <= 0:
        return min(values)
    sorted_values = sorted(values)
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = (pct / 100.0) * (len(sorted_values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def load_force_rows(
    conn: sqlite3.Connection,
    symbol: str,
    timeframe: int,
    currencies: Sequence[str],
    recent_minutes: Optional[int] = None,
    limit_bars: Optional[int] = None,
) -> Tuple[List[Tuple[Any, ...]], List[Tuple[str, str]]]:
    mapping = resolve_force_columns(conn, currencies)
    selected = [cur for cur in currencies if cur in mapping]

    cols = ["created_at"] + [mapping[cur] for cur in selected]
    sql = (
        "SELECT " + ", ".join(cols) +
        " FROM force_snapshots WHERE symbol = ? AND timeframe = ? "
        " ORDER BY created_at ASC"
    )
    db_rows = conn.execute(sql, [symbol, int(timeframe)]).fetchall()

    if recent_minutes and recent_minutes > 0 and db_rows:
        latest_dt = parse_time(db_rows[-1]["created_at"])
        if latest_dt:
            cutoff = latest_dt - timedelta(minutes=int(recent_minutes))
            kept = []
            for r in db_rows:
                dt = parse_time(r["created_at"])
                if dt is None or dt >= cutoff:
                    kept.append(r)
            db_rows = kept

    if limit_bars and limit_bars > 0:
        db_rows = db_rows[-int(limit_bars):]

    rows: List[Tuple[Any, ...]] = []
    for r in db_rows:
        values = [r["created_at"]]
        for cur in selected:
            v = r[mapping[cur]]
            values.append(float(v) if v is not None else 0.0)
        rows.append(tuple(values))

    devise_cols = [("TIME", "0")]
    for idx, cur in enumerate(selected, start=1):
        devise_cols.append((cur, str(idx)))

    return rows, devise_cols


def scan_timeframe(
    rows: Sequence[Tuple[Any, ...]],
    devise_cols: Sequence[Tuple[str, str]],
    timeframe: int,
    currencies: Sequence[str],
    window: int,
    angle_tolerance: float,
    min_breathing_energy: float,
    min_density: float,
) -> Tuple[List[DensityEvent], List[BreathingEvent], List[AngularEvent]]:
    density_events: List[DensityEvent] = []
    breathing_events: List[BreathingEvent] = []
    angular_events: List[AngularEvent] = []

    if not rows:
        return density_events, breathing_events, angular_events

    start = max(1, min(window, len(rows) - 1))

    for bar_index in range(start, len(rows)):
        bar_time = str(rows[bar_index][0])

        for cur in currencies:
            try:
                density = temporal_density(cur, rows, bar_index, window, devise_cols)
            except Exception:
                continue

            if density >= min_density:
                density_events.append(DensityEvent(
                    timeframe=timeframe,
                    currency=cur,
                    bar_time=bar_time,
                    density=round(float(density), 6),
                    bar_index=bar_index,
                ))

            try:
                breathing = extreme_zone_breathing(cur, rows, bar_index, window, devise_cols)
            except Exception:
                continue

            if float(breathing.get("energy_accumulation", 0.0)) >= min_breathing_energy:
                breathing_events.append(BreathingEvent(
                    timeframe=timeframe,
                    currency=cur,
                    bar_time=str(breathing.get("bar_time", bar_time)),
                    pullback_count=int(breathing.get("pullback_count", 0)),
                    compression_count=int(breathing.get("compression_count", 0)),
                    breathing_density=float(breathing.get("breathing_density", 0.0)),
                    energy_accumulation=float(breathing.get("energy_accumulation", 0.0)),
                    bars_in_zone=int(breathing.get("bars_in_zone", 0)),
                    side=str(breathing.get("side", "NONE")),
                    mode=str(breathing.get("mode", "unknown")),
                    current_value=float(breathing.get("current_value", 0.0)),
                    bar_index=bar_index,
                ))

        try:
            alignment = detect_angular_alignment(
                devises=list(currencies),
                rows=rows,
                bar_index=bar_index,
                tf=timeframe,
                devise_cols=devise_cols,
                angle_tolerance=angle_tolerance,
            )
        except Exception:
            alignment = None

        if alignment:
            angular_events.append(AngularEvent(
                timeframe=timeframe,
                bar_time=str(alignment.get("bar_time", bar_time)),
                aligned_devises=list(alignment.get("aligned_devises", [])),
                common_angle=float(alignment.get("common_angle", 0.0)),
                alignment_quality=float(alignment.get("alignment_quality", 0.0)),
                direction_changed_count=int(alignment.get("direction_changed_count", 0)),
                angles=dict(alignment.get("angles", {})),
                bar_index=bar_index,
            ))

    return density_events, breathing_events, angular_events


def apply_density_percentile_filter(
    events: Sequence[DensityEvent],
    min_density: float,
    density_percentile: float,
) -> Tuple[List[DensityEvent], float]:
    if not events:
        return [], float(min_density)
    values = [e.density for e in events]
    pct_cutoff = percentile(values, density_percentile) if density_percentile and density_percentile > 0 else min(values)
    cutoff = max(float(min_density), float(pct_cutoff))
    return [e for e in events if e.density >= cutoff], cutoff


def density_label(events: Sequence[DensityEvent]) -> str:
    max_density = max((e.density for e in events), default=0.0)
    if max_density >= 5.0:
        return "HIGH_TEMPORAL_COMPRESSION_FIELD"
    if max_density >= 2.0:
        return "TEMPORAL_DENSITY_FIELD"
    return "SOFT_TEMPORAL_DENSITY_FIELD"


def breathing_label(events: Sequence[BreathingEvent]) -> str:
    pullures = sum(e.pullback_count for e in events)
    compressions = sum(e.compression_count for e in events)
    max_energy = max((e.energy_accumulation for e in events), default=0.0)
    density_max = max((e.breathing_density for e in events), default=0.0)

    if pullures >= 8 and max_energy >= 4.5:
        return "PULLURE_ABSORPTION_FIELD"
    if pullures >= 3 and max_energy >= 5.5:
        return "PULLURE_ABSORPTION_FIELD"
    if pullures >= 2 and max_energy >= 7.0:
        return "PULLURE_ABSORPTION_FIELD"
    if compressions >= 8 and max_energy >= 5.0:
        return "EXTREME_BREATHING_FIELD"
    if density_max >= 0.55 and max_energy >= 5.0:
        return "EXTREME_BREATHING_FIELD"
    if max_energy >= 5.0:
        return "EXTREME_BREATHING_FIELD"
    return "SOFT_BREATHING_FIELD"


def angular_label(ev: AngularEvent) -> str:
    if ev.alignment_quality >= 0.85 and ev.direction_changed_count >= 2:
        return "SAME_ANGLE_INTENTION_NODE"
    return "ANGULAR_ALIGNMENT_NODE"


def tf_priority_bonus(tf: int) -> float:
    if tf == 1:
        return 0.0
    if tf == 5:
        return 0.6
    if tf == 15:
        return 1.0
    if tf == 30:
        return 1.25
    if tf >= 60:
        return 1.5
    return 0.0


def breathing_priority_score(f: "BreathingField") -> float:
    return (
        f.energy_max
        + f.pullures_total * 0.08
        + f.compressions_total * 0.01
        + f.event_count * 0.20
        + tf_priority_bonus(f.timeframe)
    )


def density_priority_score(f: "DensityField") -> float:
    return (
        f.density_max
        + f.event_count * 0.05
        + tf_priority_bonus(f.timeframe)
    )


def angular_priority_score(ev: AngularEvent) -> float:
    return (
        ev.alignment_quality * 10.0
        + ev.direction_changed_count * 0.75
        + tf_priority_bonus(ev.timeframe)
        + max(0, len(ev.aligned_devises) - 3) * 0.5
    )


def group_density_events(events: Sequence[DensityEvent], gap_minutes: int) -> List[DensityField]:
    grouped: Dict[Tuple[int, str], List[DensityEvent]] = {}
    for ev in events:
        grouped.setdefault((ev.timeframe, ev.currency), []).append(ev)

    fields: List[DensityField] = []
    for (tf, currency), evs in grouped.items():
        evs = sorted(evs, key=lambda e: e.bar_time)
        current: List[DensityEvent] = []
        for ev in evs:
            if not current:
                current = [ev]
                continue
            if minutes_between(current[-1].bar_time, ev.bar_time) <= gap_minutes:
                current.append(ev)
            else:
                fields.append(make_density_field(tf, currency, current))
                current = [ev]
        if current:
            fields.append(make_density_field(tf, currency, current))

    return sorted(fields, key=lambda f: f.priority_score, reverse=True)


def make_density_field(tf: int, currency: str, events: Sequence[DensityEvent]) -> DensityField:
    densities = [e.density for e in events]
    tmp = DensityField(
        timeframe=tf,
        currency=currency,
        start_time=events[0].bar_time,
        end_time=events[-1].bar_time,
        event_count=len(events),
        density_max=max(densities),
        density_avg=sum(densities) / len(densities),
        label=density_label(events),
        priority_score=0.0,
    )
    tmp.priority_score = density_priority_score(tmp)
    return tmp


def group_breathing_events(events: Sequence[BreathingEvent], gap_minutes: int) -> List[BreathingField]:
    grouped: Dict[Tuple[int, str, str], List[BreathingEvent]] = {}
    for ev in events:
        grouped.setdefault((ev.timeframe, ev.currency, ev.side), []).append(ev)

    fields: List[BreathingField] = []
    for (tf, currency, side), evs in grouped.items():
        evs = sorted(evs, key=lambda e: e.bar_time)
        current: List[BreathingEvent] = []
        for ev in evs:
            if not current:
                current = [ev]
                continue
            if minutes_between(current[-1].bar_time, ev.bar_time) <= gap_minutes:
                current.append(ev)
            else:
                fields.append(make_breathing_field(tf, currency, side, current))
                current = [ev]
        if current:
            fields.append(make_breathing_field(tf, currency, side, current))

    return sorted(fields, key=lambda f: f.priority_score, reverse=True)


def make_breathing_field(tf: int, currency: str, side: str, events: Sequence[BreathingEvent]) -> BreathingField:
    energies = [e.energy_accumulation for e in events]
    tmp = BreathingField(
        timeframe=tf,
        currency=currency,
        side=side,
        start_time=events[0].bar_time,
        end_time=events[-1].bar_time,
        event_count=len(events),
        energy_max=max(energies),
        energy_avg=sum(energies) / len(energies),
        pullures_total=sum(e.pullback_count for e in events),
        compressions_total=sum(e.compression_count for e in events),
        breathing_density_max=max(e.breathing_density for e in events),
        bars_zone_max=max(e.bars_in_zone for e in events),
        label=breathing_label(events),
        priority_score=0.0,
    )
    tmp.priority_score = breathing_priority_score(tmp)
    return tmp


def build_temporal_patterns_cockpit(
    db_path: str = "powerflow.db",
    symbol: str = "GBPUSD",
    timeframes: Sequence[int] = (1, 5, 15),
    currencies: Sequence[str] = tuple(DEFAULT_CURRENCIES),
    recent_minutes: int = 180,
    window: int = 20,
    min_density: float = 0.0,
    density_percentile: float = 85.0,
    min_breathing_energy: float = 3.0,
    angle_tolerance: float = 4.0,
    field_gap_minutes: int = 10,
    max_lines: int = 6,
    limit_bars: int = 0,
) -> TemporalCockpitResult:
    """
    Fonction principale a appeler depuis run_cockpit_field.py.

    Exemple integration:
      temporal = build_temporal_patterns_cockpit(db_path=args.db, symbol=args.symbol, ...)
      lines.extend(temporal.lines)
    """
    conn = connect_readonly(db_path)

    rows_by_tf: Dict[int, int] = {}
    all_density: List[DensityEvent] = []
    all_breathing: List[BreathingEvent] = []
    all_angular: List[AngularEvent] = []

    try:
        for tf in timeframes:
            rows, devise_cols = load_force_rows(
                conn=conn,
                symbol=symbol,
                timeframe=int(tf),
                currencies=currencies,
                recent_minutes=recent_minutes or None,
                limit_bars=limit_bars or None,
            )
            rows_by_tf[int(tf)] = len(rows)
            available = [pair[0] for pair in devise_cols if pair[0] != "TIME"]

            d_events, b_events, a_events = scan_timeframe(
                rows=rows,
                devise_cols=devise_cols,
                timeframe=int(tf),
                currencies=available,
                window=window,
                angle_tolerance=angle_tolerance,
                min_breathing_energy=min_breathing_energy,
                min_density=min_density,
            )
            all_density.extend(d_events)
            all_breathing.extend(b_events)
            all_angular.extend(a_events)
    finally:
        conn.close()

    filtered_density, density_cutoff = apply_density_percentile_filter(
        events=all_density,
        min_density=min_density,
        density_percentile=density_percentile,
    )

    breathing_fields = group_breathing_events(all_breathing, field_gap_minutes)
    density_fields = group_density_events(filtered_density, field_gap_minutes)
    angular_nodes = sorted(all_angular, key=angular_priority_score, reverse=True)

    lines = render_temporal_patterns_block(
        breathing_fields=breathing_fields,
        density_fields=density_fields,
        angular_nodes=angular_nodes,
        rows_by_tf=rows_by_tf,
        density_cutoff=density_cutoff,
        max_lines=max_lines,
    )

    return TemporalCockpitResult(
        lines=lines,
        breathing_fields=breathing_fields,
        density_fields=density_fields,
        angular_nodes=angular_nodes,
        rows_by_tf=rows_by_tf,
        density_cutoff=density_cutoff,
    )


def render_temporal_patterns_block(
    breathing_fields: Sequence[BreathingField],
    density_fields: Sequence[DensityField],
    angular_nodes: Sequence[AngularEvent],
    rows_by_tf: Dict[int, int],
    density_cutoff: float,
    max_lines: int = 6,
) -> List[str]:
    lines: List[str] = []
    lines.append("TEMPORAL_PATTERNS:")

    if breathing_fields:
        f = breathing_fields[0]
        lines.append(
            f"BREATHING: {f.currency} {tf_label(f.timeframe)} {f.side} {f.label} "
            f"score={f.priority_score:.3f} energy={f.energy_max:.3f} "
            f"pullures={f.pullures_total} comp={f.compressions_total} "
            f"| {fmt_range(f.start_time, f.end_time)}"
        )
    else:
        lines.append("BREATHING: -")

    pullure = next((f for f in breathing_fields if f.label == "PULLURE_ABSORPTION_FIELD"), None)
    if pullure:
        lines.append(
            f"PULLURE: {pullure.currency} {tf_label(pullure.timeframe)} {pullure.side} "
            f"score={pullure.priority_score:.3f} pullures={pullure.pullures_total} "
            f"energy={pullure.energy_max:.3f} | {fmt_range(pullure.start_time, pullure.end_time)}"
        )
    else:
        lines.append("PULLURE: -")

    if density_fields:
        f = density_fields[0]
        lines.append(
            f"DENSITY: {f.currency} {tf_label(f.timeframe)} {f.label} "
            f"score={f.priority_score:.3f} density={f.density_max:.3f} "
            f"cutoff={density_cutoff:.3f} | {fmt_range(f.start_time, f.end_time)}"
        )
    else:
        lines.append(f"DENSITY: - cutoff={density_cutoff:.3f}")

    if angular_nodes:
        ev = angular_nodes[0]
        lines.append(
            f"ANGLE: {','.join(ev.aligned_devises)} {tf_label(ev.timeframe)} {angular_label(ev)} "
            f"score={angular_priority_score(ev):.3f} angle={ev.common_angle:+.2f} "
            f"q={ev.alignment_quality:.3f} changes={ev.direction_changed_count} | {ev.bar_time}"
        )
    else:
        lines.append("ANGLE: -")

    # Additional temporal targets, compact.
    targets: List[Tuple[float, str]] = []
    for f in breathing_fields[:max_lines]:
        targets.append((
            f.priority_score,
            f"{f.currency}/{tf_label(f.timeframe)}/{f.side}/{f.label}/score={f.priority_score:.2f}"
        ))
    for f in density_fields[:max_lines]:
        targets.append((
            f.priority_score,
            f"{f.currency}/{tf_label(f.timeframe)}/DENSITY/score={f.priority_score:.2f}"
        ))
    for ev in angular_nodes[:max_lines]:
        targets.append((
            angular_priority_score(ev),
            f"{','.join(ev.aligned_devises)}/{tf_label(ev.timeframe)}/ANGLE/score={angular_priority_score(ev):.2f}"
        ))

    targets = sorted(targets, key=lambda x: x[0], reverse=True)
    if targets:
        top_text = " | ".join(text for _, text in targets[:max_lines])
        lines.append(f"TEMPORAL_TARGETS: {top_text}")
    else:
        lines.append("TEMPORAL_TARGETS: -")

    lines.append("TEMPORAL_ROWS: " + " | ".join(f"{tf_label(tf)}={rows_by_tf.get(tf, 0)}" for tf in sorted(rows_by_tf)))

    return lines
