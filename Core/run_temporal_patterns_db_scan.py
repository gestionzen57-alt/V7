"""
PowerFlow V6 - run_temporal_patterns_db_scan.py
Version: V0.3

Mission:
  Scanner powerflow.db en lecture seule pour detecter les patterns temporels avances,
  regrouper les evenements en champs temporels PowerFlow,
  et produire une lecture cockpit plus agressive / moins bavarde.

Source:
  table force_snapshots

Detecteurs:
  - temporal_density
  - extreme_zone_breathing
  - detect_angular_alignment

V0.3:
  - --density-percentile pour couper automatiquement la densite molle
  - --cockpit-only pour une sortie courte exploitable cockpit
  - label PULLURE_ABSORPTION_FIELD plus agressif
  - filtrage post-scan des densites selon cutoff effectif
  - cockpit synthesis renforcee

Architecture:
  Read-only DB.
  Aucune ecriture.
  Aucun signal BUY/SELL.
  Rapport texte uniquement.
"""

from __future__ import annotations

import argparse
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


def parse_int_list(value: str) -> List[int]:
    return [int(x.strip()) for x in str(value).split(",") if x.strip()]


def parse_currency_list(value: str) -> List[str]:
    if not value:
        return list(DEFAULT_CURRENCIES)
    return [x.strip().upper() for x in str(value).split(",") if x.strip()]


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
        raise RuntimeError("No force_* columns found in force_snapshots for requested currencies.")
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
    """
    Retourne:
      rows = [(created_at, force_gbp, force_usd, ...), ...]
      devise_cols = [("TIME","0"), ("GBP","1"), ...]

    recent_minutes:
      filtre depuis le dernier timestamp disponible de ce TF.
      Donc fonctionne meme si la DB est offline / historique.
    """
    mapping = resolve_force_columns(conn, currencies)
    selected_currencies = [cur for cur in currencies if cur in mapping]

    select_cols = ["created_at"] + [mapping[cur] for cur in selected_currencies]
    sql = (
        "SELECT " + ", ".join(select_cols) +
        " FROM force_snapshots WHERE symbol = ? AND timeframe = ? "
        " ORDER BY created_at ASC"
    )
    db_rows = conn.execute(sql, [symbol, int(timeframe)]).fetchall()

    if recent_minutes and recent_minutes > 0 and db_rows:
        latest_dt = parse_time(db_rows[-1]["created_at"])
        if latest_dt:
            cutoff = latest_dt - timedelta(minutes=int(recent_minutes))
            db_rows = [
                r for r in db_rows
                if parse_time(r["created_at"]) is None or parse_time(r["created_at"]) >= cutoff
            ]

    if limit_bars and limit_bars > 0:
        db_rows = db_rows[-int(limit_bars):]

    rows: List[Tuple[Any, ...]] = []
    for r in db_rows:
        values = [r["created_at"]]
        for cur in selected_currencies:
            v = r[mapping[cur]]
            values.append(float(v) if v is not None else 0.0)
        rows.append(tuple(values))

    devise_cols: List[Tuple[str, str]] = [("TIME", "0")]
    for idx, cur in enumerate(selected_currencies, start=1):
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
    density_events: Sequence[DensityEvent],
    min_density: float,
    density_percentile: float,
) -> Tuple[List[DensityEvent], float]:
    """
    Filtre les densites trop molles apres scan.

    cutoff effectif:
      max(min_density, percentile(density_values, density_percentile))
    """
    if not density_events:
        return [], float(min_density)

    values = [e.density for e in density_events]
    pct_cutoff = percentile(values, density_percentile) if density_percentile and density_percentile > 0 else min(values)
    effective_cutoff = max(float(min_density), float(pct_cutoff))
    filtered = [e for e in density_events if e.density >= effective_cutoff]
    return filtered, effective_cutoff


def density_label(events: Sequence[DensityEvent]) -> str:
    if not events:
        return "TEMPORAL_DENSITY_FIELD"
    max_density = max(e.density for e in events)
    if max_density >= 5.0:
        return "HIGH_TEMPORAL_COMPRESSION_FIELD"
    if max_density >= 2.0:
        return "TEMPORAL_DENSITY_FIELD"
    return "SOFT_TEMPORAL_DENSITY_FIELD"


def breathing_label(events: Sequence[BreathingEvent]) -> str:
    """
    V0.3 plus agressif:
      - une vraie somme de pullures suffit a nommer l'absorption,
        meme si energy_max reste sous 7.
      - la compression sans pullure reste EXTREME_BREATHING_FIELD.
    """
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


def group_density_events(events: Sequence[DensityEvent], field_gap_minutes: int) -> List[DensityField]:
    groups: Dict[Tuple[int, str], List[DensityEvent]] = {}
    for ev in events:
        groups.setdefault((ev.timeframe, ev.currency), []).append(ev)

    fields: List[DensityField] = []
    for (tf, currency), evs in groups.items():
        evs = sorted(evs, key=lambda e: e.bar_time)
        current: List[DensityEvent] = []
        for ev in evs:
            if not current:
                current = [ev]
                continue
            if minutes_between(current[-1].bar_time, ev.bar_time) <= field_gap_minutes:
                current.append(ev)
            else:
                fields.append(make_density_field(tf, currency, current))
                current = [ev]
        if current:
            fields.append(make_density_field(tf, currency, current))

    return sorted(fields, key=lambda f: f.density_max, reverse=True)


def make_density_field(tf: int, currency: str, events: Sequence[DensityEvent]) -> DensityField:
    densities = [e.density for e in events]
    return DensityField(
        timeframe=tf,
        currency=currency,
        start_time=events[0].bar_time,
        end_time=events[-1].bar_time,
        event_count=len(events),
        density_max=max(densities),
        density_avg=sum(densities) / len(densities),
        label=density_label(events),
    )


def group_breathing_events(events: Sequence[BreathingEvent], field_gap_minutes: int) -> List[BreathingField]:
    groups: Dict[Tuple[int, str, str], List[BreathingEvent]] = {}
    for ev in events:
        groups.setdefault((ev.timeframe, ev.currency, ev.side), []).append(ev)

    fields: List[BreathingField] = []
    for (tf, currency, side), evs in groups.items():
        evs = sorted(evs, key=lambda e: e.bar_time)
        current: List[BreathingEvent] = []
        for ev in evs:
            if not current:
                current = [ev]
                continue
            if minutes_between(current[-1].bar_time, ev.bar_time) <= field_gap_minutes:
                current.append(ev)
            else:
                fields.append(make_breathing_field(tf, currency, side, current))
                current = [ev]
        if current:
            fields.append(make_breathing_field(tf, currency, side, current))

    return sorted(fields, key=lambda f: f.energy_max, reverse=True)


def make_breathing_field(tf: int, currency: str, side: str, events: Sequence[BreathingEvent]) -> BreathingField:
    energies = [e.energy_accumulation for e in events]
    return BreathingField(
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
    )


def fmt_range(start: str, end: str) -> str:
    if start == end:
        return start
    return f"{start} -> {end}"


def field_score_breathing(f: BreathingField) -> float:
    return f.energy_max + 0.05 * f.pullures_total + 0.015 * f.compressions_total + 0.25 * f.event_count


def field_score_density(f: DensityField) -> float:
    return f.density_max + 0.05 * f.event_count


def node_score_angular(ev: AngularEvent) -> float:
    return ev.alignment_quality * 10.0 + ev.direction_changed_count


def render_cockpit_only(
    symbol: str,
    timeframes: Sequence[int],
    rows_by_tf: Dict[int, int],
    breathing_fields: Sequence[BreathingField],
    density_fields: Sequence[DensityField],
    angular_events: Sequence[AngularEvent],
    recent_minutes: Optional[int],
    window: int,
    field_gap_minutes: int,
    density_cutoff: float,
    density_percentile: float,
    top: int,
) -> str:
    lines: List[str] = []
    lines.append("TEMPORAL PATTERNS COCKPIT")
    lines.append("=" * 76)
    mode = f"recent={recent_minutes}m" if recent_minutes and recent_minutes > 0 else "recent=ALL"
    lines.append(
        f"{symbol} | TF={','.join(tf_label(tf) for tf in timeframes)} | {mode} | "
        f"window={window} | gap={field_gap_minutes}m | density_cutoff={density_cutoff:.6f}"
    )
    if density_percentile and density_percentile > 0:
        lines.append(f"density_percentile={density_percentile:.1f}")
    lines.append("")

    # Global target order.
    candidates: List[Tuple[float, str]] = []

    for f in breathing_fields[:top]:
        score = field_score_breathing(f)
        candidates.append((
            score,
            f"BREATH {f.currency} {tf_label(f.timeframe)} {f.side} | {f.label} | "
            f"energy={f.energy_max:.3f} pullures={f.pullures_total} comp={f.compressions_total} "
            f"| {fmt_range(f.start_time, f.end_time)}"
        ))

    for f in density_fields[:top]:
        score = field_score_density(f)
        candidates.append((
            score,
            f"DENSITY {f.currency} {tf_label(f.timeframe)} | {f.label} | "
            f"dens={f.density_max:.3f} events={f.event_count} "
            f"| {fmt_range(f.start_time, f.end_time)}"
        ))

    sorted_angles = sorted(angular_events, key=node_score_angular, reverse=True)
    for ev in sorted_angles[:top]:
        score = node_score_angular(ev)
        candidates.append((
            score,
            f"ANGLE {','.join(ev.aligned_devises)} {tf_label(ev.timeframe)} | {angular_label(ev)} | "
            f"angle={ev.common_angle:+.2f} q={ev.alignment_quality:.3f} changes={ev.direction_changed_count} "
            f"| {ev.bar_time}"
        ))

    lines.append("TOP TEMPORAL TARGETS")
    lines.append("-" * 76)
    if not candidates:
        lines.append("-")
    for i, (_, text) in enumerate(sorted(candidates, key=lambda x: x[0], reverse=True)[:top], 1):
        lines.append(f"{i:02d}. {text}")

    lines.append("")
    lines.append("FOCUS")
    lines.append("-" * 76)
    if breathing_fields:
        f = breathing_fields[0]
        lines.append(
            f"BREATHING: {f.currency} {tf_label(f.timeframe)} {f.side} {f.label} "
            f"energy={f.energy_max:.3f} range={fmt_range(f.start_time, f.end_time)}"
        )
    if density_fields:
        f = density_fields[0]
        lines.append(
            f"DENSITY: {f.currency} {tf_label(f.timeframe)} {f.label} "
            f"density={f.density_max:.3f} range={fmt_range(f.start_time, f.end_time)}"
        )
    if angular_events:
        ev = sorted_angles[0]
        lines.append(
            f"ANGLE: {','.join(ev.aligned_devises)} {tf_label(ev.timeframe)} {angular_label(ev)} "
            f"angle={ev.common_angle:+.2f} q={ev.alignment_quality:.3f} at {ev.bar_time}"
        )

    lines.append("")
    lines.append("ROWS")
    lines.append("-" * 76)
    lines.append(" | ".join(f"{tf_label(tf)}={rows_by_tf.get(tf, 0)}" for tf in timeframes))

    return "\n".join(lines)


def render_report(
    symbol: str,
    timeframes: Sequence[int],
    rows_by_tf: Dict[int, int],
    density_events: Sequence[DensityEvent],
    density_events_before_filter: int,
    breathing_events: Sequence[BreathingEvent],
    angular_events: Sequence[AngularEvent],
    density_fields: Sequence[DensityField],
    breathing_fields: Sequence[BreathingField],
    window: int,
    top: int,
    min_breathing_energy: float,
    min_density: float,
    angle_tolerance: float,
    recent_minutes: Optional[int],
    field_gap_minutes: int,
    density_percentile: float,
    density_cutoff: float,
    show_raw: bool,
    cockpit_only: bool,
) -> str:
    if cockpit_only:
        return render_cockpit_only(
            symbol=symbol,
            timeframes=timeframes,
            rows_by_tf=rows_by_tf,
            breathing_fields=breathing_fields,
            density_fields=density_fields,
            angular_events=angular_events,
            recent_minutes=recent_minutes,
            window=window,
            field_gap_minutes=field_gap_minutes,
            density_cutoff=density_cutoff,
            density_percentile=density_percentile,
            top=top,
        )

    lines: List[str] = []
    lines.append("PowerFlow Temporal Patterns DB Scan V0.3 - READ ONLY")
    lines.append("=" * 108)
    lines.append(f"Symbol: {symbol}")
    lines.append(f"Timeframes: {', '.join(tf_label(tf) for tf in timeframes)}")
    mode = f"recent={recent_minutes}m" if recent_minutes and recent_minutes > 0 else "recent=ALL"
    lines.append(
        f"Mode: {mode} | window={window} | field_gap={field_gap_minutes}m | "
        f"min_density={min_density} | density_percentile={density_percentile} | "
        f"density_cutoff={density_cutoff:.6f} | min_breathing_energy={min_breathing_energy} | "
        f"angle_tolerance={angle_tolerance}"
    )
    lines.append("")

    lines.append("Rows by timeframe:")
    lines.append("-" * 108)
    for tf in timeframes:
        lines.append(f"{tf_label(tf):<4} rows={rows_by_tf.get(tf, 0)}")
    lines.append(f"Density events: before_filter={density_events_before_filter} after_filter={len(density_events)}")

    lines.append("")
    lines.append(f"Top {min(top, len(breathing_fields))} breathing fields:")
    lines.append("-" * 108)
    if not breathing_fields:
        lines.append("-")
    for i, f in enumerate(breathing_fields[:top], 1):
        lines.append(
            f"{i:02d}. {f.currency:<3} {tf_label(f.timeframe):<4} {f.side:<4} {f.label:<28} "
            f"energy_max={f.energy_max:.3f} avg={f.energy_avg:.3f} "
            f"pullures={f.pullures_total} compressions={f.compressions_total} "
            f"events={f.event_count} range={fmt_range(f.start_time, f.end_time)}"
        )

    lines.append("")
    lines.append(f"Top {min(top, len(density_fields))} temporal density fields:")
    lines.append("-" * 108)
    if not density_fields:
        lines.append("-")
    for i, f in enumerate(density_fields[:top], 1):
        lines.append(
            f"{i:02d}. {f.currency:<3} {tf_label(f.timeframe):<4} {f.label:<32} "
            f"density_max={f.density_max:.6f} avg={f.density_avg:.6f} "
            f"events={f.event_count} range={fmt_range(f.start_time, f.end_time)}"
        )

    lines.append("")
    lines.append(f"Top {min(top, len(angular_events))} angular nodes:")
    lines.append("-" * 108)
    if not angular_events:
        lines.append("-")
    sorted_angles = sorted(angular_events, key=lambda e: (e.alignment_quality, e.direction_changed_count), reverse=True)
    for i, ev in enumerate(sorted_angles[:top], 1):
        devises = ",".join(ev.aligned_devises)
        label = angular_label(ev)
        angles = ", ".join(f"{k}:{v:+.2f}" for k, v in ev.angles.items())
        lines.append(
            f"{i:02d}. {ev.bar_time} {tf_label(ev.timeframe):<4} {label:<28} "
            f"aligned={devises:<25} angle={ev.common_angle:+.3f} "
            f"quality={ev.alignment_quality:.3f} changes={ev.direction_changed_count} | {angles}"
        )

    lines.append("")
    lines.append("Cockpit reading:")
    lines.append("-" * 108)
    if breathing_fields:
        f = breathing_fields[0]
        lines.append(
            f"Strongest breathing field: {f.currency} {tf_label(f.timeframe)} {f.side} "
            f"{f.label} energy_max={f.energy_max:.3f} range={fmt_range(f.start_time, f.end_time)}."
        )
    if density_fields:
        f = density_fields[0]
        lines.append(
            f"Highest temporal density field: {f.currency} {tf_label(f.timeframe)} "
            f"{f.label} density_max={f.density_max:.6f} range={fmt_range(f.start_time, f.end_time)}."
        )
    if angular_events:
        ev = sorted_angles[0]
        lines.append(
            f"Best angular node: {','.join(ev.aligned_devises)} {tf_label(ev.timeframe)} "
            f"{angular_label(ev)} angle={ev.common_angle:+.3f} "
            f"quality={ev.alignment_quality:.3f} at {ev.bar_time}."
        )
    if not breathing_fields and not density_fields and not angular_events:
        lines.append("No temporal pattern above thresholds.")

    if show_raw:
        lines.append("")
        lines.append(f"Raw events snapshot: density={len(density_events)} breathing={len(breathing_events)} angular={len(angular_events)}")
        lines.append("-" * 108)
        for ev in sorted(breathing_events, key=lambda e: e.energy_accumulation, reverse=True)[:min(top, len(breathing_events))]:
            lines.append(
                f"BREATH {ev.bar_time} {tf_label(ev.timeframe)} {ev.currency} {ev.side} "
                f"energy={ev.energy_accumulation:.3f} pullures={ev.pullback_count} compressions={ev.compression_count}"
            )

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow temporal patterns DB scan V0.3 - read only")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15,30,60")
    parser.add_argument("--currencies", default="GBP,USD,EUR,JPY,CAD,CHF,AUD")
    parser.add_argument("--window", type=int, default=20)
    parser.add_argument("--recent-minutes", type=int, default=0,
                        help="Filter each timeframe from its own latest DB timestamp. 0 = all.")
    parser.add_argument("--limit-bars", type=int, default=0)
    parser.add_argument("--field-gap-minutes", type=int, default=20,
                        help="Max gap between raw events to group them into one field.")
    parser.add_argument("--top", type=int, default=20)
    parser.add_argument("--min-density", type=float, default=0.0)
    parser.add_argument("--density-percentile", type=float, default=0.0,
                        help="Post-scan density cutoff percentile. Example: 85 keeps only top 15 percent density events.")
    parser.add_argument("--min-breathing-energy", type=float, default=5.0)
    parser.add_argument("--angle-tolerance", type=float, default=3.0)
    parser.add_argument("--cockpit-only", action="store_true")
    parser.add_argument("--show-raw", action="store_true")
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    timeframes = parse_int_list(args.timeframes)
    currencies = parse_currency_list(args.currencies)

    conn = connect_readonly(args.db)

    rows_by_tf: Dict[int, int] = {}
    all_density: List[DensityEvent] = []
    all_breathing: List[BreathingEvent] = []
    all_angular: List[AngularEvent] = []

    try:
        for tf in timeframes:
            rows, devise_cols = load_force_rows(
                conn=conn,
                symbol=args.symbol,
                timeframe=tf,
                currencies=currencies,
                recent_minutes=args.recent_minutes or None,
                limit_bars=args.limit_bars or None,
            )
            rows_by_tf[tf] = len(rows)
            available_currencies = [pair[0] for pair in devise_cols if pair[0] != "TIME"]

            d_events, b_events, a_events = scan_timeframe(
                rows=rows,
                devise_cols=devise_cols,
                timeframe=tf,
                currencies=available_currencies,
                window=args.window,
                angle_tolerance=args.angle_tolerance,
                min_breathing_energy=args.min_breathing_energy,
                min_density=args.min_density,
            )
            all_density.extend(d_events)
            all_breathing.extend(b_events)
            all_angular.extend(a_events)
    finally:
        conn.close()

    density_before_filter = len(all_density)
    filtered_density, density_cutoff = apply_density_percentile_filter(
        density_events=all_density,
        min_density=args.min_density,
        density_percentile=args.density_percentile,
    )

    density_fields = group_density_events(filtered_density, args.field_gap_minutes)
    breathing_fields = group_breathing_events(all_breathing, args.field_gap_minutes)

    report = render_report(
        symbol=args.symbol,
        timeframes=timeframes,
        rows_by_tf=rows_by_tf,
        density_events=filtered_density,
        density_events_before_filter=density_before_filter,
        breathing_events=all_breathing,
        angular_events=all_angular,
        density_fields=density_fields,
        breathing_fields=breathing_fields,
        window=args.window,
        top=args.top,
        min_breathing_energy=args.min_breathing_energy,
        min_density=args.min_density,
        angle_tolerance=args.angle_tolerance,
        recent_minutes=args.recent_minutes or None,
        field_gap_minutes=args.field_gap_minutes,
        density_percentile=args.density_percentile,
        density_cutoff=density_cutoff,
        show_raw=args.show_raw,
        cockpit_only=args.cockpit_only,
    )

    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nOK wrote temporal patterns report: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
