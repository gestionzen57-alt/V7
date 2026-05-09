"""
PowerFlow V6 — FlowEventExtractor V0.1.3.1

Mission:
    Read force_snapshots / force_snapshots_v2 in read-only mode and extract
    the raw film phases for a given window:
        PRE_FIELD, NODE_BIRTH, CONFIRMATION, COUNTER_BREATH, ABSORPTION.

Combat target:
    LAB_004 — GBPUSD 2026-05-04 09:00 -> 10:15

Doctrine:
    - This module measures and classifies raw sequence phases.
    - It does not decide, trade, alert BUY/SELL, or write to DB.
    - It must not confuse a counter-breath after confirmation with a new main node.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
import argparse
import json
import math
import sqlite3


EXTRACTOR_VERSION = "0.1.3"


BASE_FORCE_COLUMNS: Tuple[str, ...] = (
    "force_gbp",
    "force_usd",
    "force_eur",
    "force_jpy",
    "force_cad",
    "force_chf",
    "force_aud",
    "force_nzd",
)

LEGACY_FORCE_COLUMNS: Tuple[str, ...] = (
    "force_gbp",
    "force_usd",
    "force_eur",
    "force_jpy",
    "force_cad",
    "force_chf",
    "force_aud",
)

SOURCE_TABLE_PRIORITY: Tuple[str, ...] = (
    "force_snapshots_v2",
    "force_snapshots_extended",
    "extended_force_snapshots",
    "market_snapshots",
    "snapshots_extended",
    "force_snapshots",
)


@dataclass(frozen=True)
class SnapshotRow:
    created_at: str
    dt: datetime
    symbol: str
    timeframe: int
    bid: Optional[float]
    forces: Dict[str, float]


@dataclass(frozen=True)
class Segment:
    timeframe: int
    start: str
    end: str
    start_dt_iso: str
    end_dt_iso: str
    duration_min: float
    deltas: Dict[str, float]
    up_block: List[str]
    down_block: List[str]
    force_energy: float
    bid_delta: Optional[float]
    pip_delta: Optional[float]
    price_response: str
    score: float
    raw_event: str


@dataclass(frozen=True)
class FlowEvent:
    phase: str
    timeframe: int
    start: str
    end: str
    start_dt_iso: str
    end_dt_iso: str
    up_block: List[str]
    down_block: List[str]
    force_energy: float
    bid_delta: Optional[float]
    pip_delta: Optional[float]
    price_response: str
    confidence: float
    raw_event: str
    note: str


@dataclass(frozen=True)
class FlowExtractionReport:
    symbol: str
    mode: str
    source_table: str
    start: str
    end: str
    timeframes: List[int]
    rows_loaded: Dict[str, int]
    events: List[FlowEvent]
    candidates: List[Segment]
    warnings: List[str]

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
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def _short_time(dt_iso: str) -> str:
    dt = _parse_dt(dt_iso)
    if dt is None:
        return dt_iso
    return dt.strftime("%H:%M")


def _connect_readonly(db_path: str) -> sqlite3.Connection:
    p = Path(db_path)
    if not p.exists():
        raise FileNotFoundError(f"DB not found: {db_path}")
    uri = f"file:{p.resolve().as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _quote_identifier(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _list_tables(conn: sqlite3.Connection) -> List[str]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [str(r["name"]) for r in rows]


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({_quote_identifier(table)})").fetchall()
    return [str(r["name"]) for r in rows]


def _pip_factor(symbol: str) -> float:
    return 100.0 if "JPY" in symbol.upper() else 10000.0


def _available_force_columns(columns: Sequence[str]) -> List[str]:
    return [c for c in BASE_FORCE_COLUMNS if c in columns]


def _detect_mode(table: str, force_cols: Sequence[str], columns: Sequence[str]) -> str:
    extended_markers = {
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
    }
    present = len([c for c in extended_markers if c in columns])
    if present >= 17:
        return "EXTENDED"
    if all(c in force_cols for c in LEGACY_FORCE_COLUMNS):
        return "LEGACY_FORCE_ONLY"
    return "UNKNOWN_SCHEMA"


def _load_rows_from_table(
    conn: sqlite3.Connection,
    table: str,
    symbol: str,
    timeframe: int,
    start_dt: datetime,
    end_dt: datetime,
) -> List[SnapshotRow]:
    columns = _table_columns(conn, table)
    force_cols = _available_force_columns(columns)

    required = {"created_at", "symbol", "timeframe"}
    if not required.issubset(set(columns)):
        return []

    qtable = _quote_identifier(table)
    rows = conn.execute(
        f"""
        SELECT *
        FROM {qtable}
        WHERE symbol = ? AND timeframe = ?
        ORDER BY created_at ASC
        """,
        (symbol, timeframe),
    ).fetchall()

    out: List[SnapshotRow] = []
    for row in rows:
        dt = _parse_dt(row["created_at"])
        if dt is None:
            continue
        if dt < start_dt or dt > end_dt:
            continue

        bid = None
        if "bid" in columns and row["bid"] is not None:
            try:
                bid = float(row["bid"])
            except (TypeError, ValueError):
                bid = None

        forces: Dict[str, float] = {}
        for col in force_cols:
            value = row[col]
            if value is None:
                continue
            try:
                forces[col.replace("force_", "").upper()] = float(value)
            except (TypeError, ValueError):
                continue

        if forces:
            out.append(
                SnapshotRow(
                    created_at=str(row["created_at"]),
                    dt=dt,
                    symbol=symbol,
                    timeframe=timeframe,
                    bid=bid,
                    forces=forces,
                )
            )

    return out


def _choose_source_table(
    conn: sqlite3.Connection,
    symbol: str,
    timeframes: Sequence[int],
    start_dt: datetime,
    end_dt: datetime,
    forced_table: Optional[str] = None,
) -> Tuple[str, Dict[int, List[SnapshotRow]], str, List[str]]:
    warnings: List[str] = []
    tables = _list_tables(conn)

    if forced_table:
        candidates = [forced_table]
    else:
        candidates = [t for t in SOURCE_TABLE_PRIORITY if t in tables]
        for table in tables:
            if "snapshot" in table.lower() and table not in candidates:
                candidates.append(table)

    if not candidates:
        raise RuntimeError("No snapshot table found.")

    best_table = candidates[0]
    best_rows: Dict[int, List[SnapshotRow]] = {}
    best_count = -1
    best_mode = "UNKNOWN_SCHEMA"

    for table in candidates:
        columns = _table_columns(conn, table)
        force_cols = _available_force_columns(columns)
        if not force_cols:
            continue

        rows_by_tf: Dict[int, List[SnapshotRow]] = {}
        count = 0
        for tf in timeframes:
            rows = _load_rows_from_table(conn, table, symbol, int(tf), start_dt, end_dt)
            rows_by_tf[int(tf)] = rows
            count += len(rows)

        mode = _detect_mode(table, force_cols, columns)

        # For historical LAB windows, force_snapshots may beat v2 because v2 starts later.
        if count > best_count:
            best_table = table
            best_rows = rows_by_tf
            best_count = count
            best_mode = mode

    if best_count <= 0:
        warnings.append("No rows found in requested window for candidate snapshot tables.")

    return best_table, best_rows, best_mode, warnings


def _compute_segment(
    rows: Sequence[SnapshotRow],
    i: int,
    j: int,
    symbol: str,
    min_force_delta: float,
    price_lag_pips: float,
) -> Optional[Segment]:
    a = rows[i]
    b = rows[j]
    duration_min = max((b.dt - a.dt).total_seconds() / 60.0, 0.0)
    if duration_min <= 0:
        return None

    currencies = sorted(set(a.forces) & set(b.forces))
    if len(currencies) < 4:
        return None

    deltas = {cur: b.forces[cur] - a.forces[cur] for cur in currencies}
    force_energy = sum(abs(v) for v in deltas.values())

    up_block = [cur for cur, delta in sorted(deltas.items(), key=lambda kv: kv[1], reverse=True) if delta >= min_force_delta]
    down_block = [cur for cur, delta in sorted(deltas.items(), key=lambda kv: kv[1]) if delta <= -min_force_delta]

    bid_delta: Optional[float] = None
    pip_delta: Optional[float] = None
    if a.bid is not None and b.bid is not None:
        bid_delta = b.bid - a.bid
        pip_delta = bid_delta * _pip_factor(symbol)

    price_response = "PRICE_UNKNOWN"
    if pip_delta is not None:
        if abs(pip_delta) <= price_lag_pips:
            price_response = "PRICE_LAG"
        else:
            # Simple GBPUSD logic generalized by force relation:
            # if quote side USD strengthens while base GBP weakens, price usually pays down.
            if "USD" in up_block and "GBP" in down_block and pip_delta < -price_lag_pips:
                price_response = "PRICE_PAYING"
            elif "GBP" in up_block and "USD" in down_block and pip_delta > price_lag_pips:
                price_response = "PRICE_PAYING"
            elif abs(pip_delta) <= price_lag_pips * 2.5:
                price_response = "WEAK_PRICE_RESPONSE"
            else:
                price_response = "PRICE_MOVED"

    raw_event = "LOW_ENERGY"
    if len(up_block) >= 2 and len(down_block) >= 2:
        raw_event = "SIMULTANEOUS_RESPRING_VS_FOLD"
    elif len(up_block) >= 2:
        raw_event = "SYNC_RESPRING"
    elif len(down_block) >= 2:
        raw_event = "SYNC_FOLD"

    # Aggressive but simple score.
    block_score = (len(up_block) + len(down_block)) * 8.0
    lag_bonus = 15.0 if price_response == "PRICE_LAG" else 0.0
    paying_bonus = 10.0 if price_response == "PRICE_PAYING" else 0.0
    compact_bonus = max(0.0, 12.0 - duration_min) if duration_min <= 15 else 0.0
    score = force_energy + block_score + lag_bonus + paying_bonus + compact_bonus

    return Segment(
        timeframe=a.timeframe,
        start=_short_time(a.dt.isoformat()),
        end=_short_time(b.dt.isoformat()),
        start_dt_iso=a.dt.isoformat(),
        end_dt_iso=b.dt.isoformat(),
        duration_min=round(duration_min, 2),
        deltas={k: round(v, 4) for k, v in deltas.items()},
        up_block=up_block,
        down_block=down_block,
        force_energy=round(force_energy, 4),
        bid_delta=round(bid_delta, 8) if bid_delta is not None else None,
        pip_delta=round(pip_delta, 3) if pip_delta is not None else None,
        price_response=price_response,
        score=round(score, 4),
        raw_event=raw_event,
    )


def _build_segments(
    rows_by_tf: Dict[int, List[SnapshotRow]],
    symbol: str,
    min_window_minutes: float,
    max_window_minutes: float,
    min_force_delta: float,
    price_lag_pips: float,
) -> List[Segment]:
    segments: List[Segment] = []

    for tf, rows in rows_by_tf.items():
        if len(rows) < 2:
            continue

        for i in range(len(rows) - 1):
            for j in range(i + 1, len(rows)):
                duration = (rows[j].dt - rows[i].dt).total_seconds() / 60.0
                if duration < min_window_minutes:
                    continue
                if duration > max_window_minutes:
                    break
                seg = _compute_segment(rows, i, j, symbol, min_force_delta, price_lag_pips)
                if seg is not None:
                    segments.append(seg)

    return sorted(segments, key=lambda s: s.score, reverse=True)


def _overlap(a: Sequence[str], b: Sequence[str]) -> int:
    return len(set(a) & set(b))


def _same_direction(seg: Segment, ref: Segment) -> float:
    up_overlap = _overlap(seg.up_block, ref.up_block)
    down_overlap = _overlap(seg.down_block, ref.down_block)
    denom = max(1, len(set(ref.up_block + ref.down_block)))
    return (up_overlap + down_overlap) / denom


def _opposite_direction(seg: Segment, ref: Segment) -> float:
    up_vs_down = _overlap(seg.up_block, ref.down_block)
    down_vs_up = _overlap(seg.down_block, ref.up_block)
    denom = max(1, len(set(ref.up_block + ref.down_block)))
    return (up_vs_down + down_vs_up) / denom


def _dt_from_segment_start(seg: Segment) -> datetime:
    dt = _parse_dt(seg.start_dt_iso)
    assert dt is not None
    return dt


def _dt_from_segment_end(seg: Segment) -> datetime:
    dt = _parse_dt(seg.end_dt_iso)
    assert dt is not None
    return dt


def _event_from_segment(phase: str, seg: Segment, confidence: float, note: str) -> FlowEvent:
    return FlowEvent(
        phase=phase,
        timeframe=seg.timeframe,
        start=seg.start,
        end=seg.end,
        start_dt_iso=seg.start_dt_iso,
        end_dt_iso=seg.end_dt_iso,
        up_block=seg.up_block,
        down_block=seg.down_block,
        force_energy=seg.force_energy,
        bid_delta=seg.bid_delta,
        pip_delta=seg.pip_delta,
        price_response=seg.price_response,
        confidence=round(max(0.0, min(confidence, 1.0)), 3),
        raw_event=seg.raw_event,
        note=note,
    )


def _select_node_birth(segments: Sequence[Segment], start_dt: datetime) -> Optional[Segment]:
    """
    V0.1.3 deterministic node selector.

    Rule:
        NODE_BIRTH is the first major opposite-block rotation of the window.
        A later opposite PRICE_LAG move is treated as possible COUNTER_BREATH,
        not as the primary node.

    This is intentionally aggressive and early.
    """
    candidates = [
        s for s in segments
        if s.raw_event == "SIMULTANEOUS_RESPRING_VS_FOLD"
        and len(s.up_block) >= 2
        and len(s.down_block) >= 2
        and 2.5 <= s.duration_min <= 20.0
    ]

    if not candidates:
        candidates = [
            s for s in segments
            if len(s.up_block) >= 2
            and len(s.down_block) >= 2
            and 2.5 <= s.duration_min <= 20.0
        ]

    if not candidates:
        return None

    max_energy = max(s.force_energy for s in candidates)
    floor = max(25.0, max_energy * 0.65)
    major = [s for s in candidates if s.force_energy >= floor] or candidates

    # Bucket by start minute and keep only the first strong wave.
    major_sorted = sorted(major, key=lambda s: _dt_from_segment_start(s))
    first_start = _dt_from_segment_start(major_sorted[0])
    first_wave_limit_min = 12.0

    first_wave = [
        s for s in major_sorted
        if (_dt_from_segment_start(s) - first_start).total_seconds() / 60.0 <= first_wave_limit_min
    ] or major_sorted[:1]

    def rank_first_wave(s: Segment) -> Tuple[float, float, float, float]:
        # In the first wave, prefer energy + clean blocks.
        block_bonus = (len(s.up_block) + len(s.down_block)) * 6.0
        tf_bonus = 15.0 if s.timeframe == 1 else 7.0 if s.timeframe == 5 else 0.0
        duration_penalty = max(0.0, s.duration_min - 8.0) * 0.8
        score = s.force_energy + block_bonus + tf_bonus - duration_penalty
        return (score, s.force_energy, -s.duration_min, -float(s.timeframe))

    return sorted(first_wave, key=rank_first_wave, reverse=True)[0]

def _compact_node_from_anchor(
    rows_by_tf: Dict[int, List[SnapshotRow]],
    anchor: Segment,
    symbol: str,
    min_force_delta: float,
    price_lag_pips: float,
) -> Segment:
    """
    Compress a broad high-energy anchor into a short birth window.

    Example:
        anchor 09:22->09:42 can become 09:22->09:27 if the first
        3-6 minute segment already carries the same block rotation.
    """
    if anchor.duration_min <= 8.0:
        return anchor

    rows = rows_by_tf.get(anchor.timeframe, [])
    if len(rows) < 2:
        return anchor

    anchor_start = _dt_from_segment_start(anchor)
    anchor_end = _dt_from_segment_end(anchor)

    start_indices = [
        i for i, row in enumerate(rows)
        if abs((row.dt - anchor_start).total_seconds()) <= 90
    ]
    if not start_indices:
        start_indices = [
            i for i, row in enumerate(rows)
            if anchor_start <= row.dt <= anchor_start.replace(second=0, microsecond=0)
        ]
    if not start_indices:
        # fallback: first row inside anchor
        start_indices = [i for i, row in enumerate(rows) if row.dt >= anchor_start]
    if not start_indices:
        return anchor

    i0 = start_indices[0]
    candidates: List[Segment] = []

    for j in range(i0 + 1, len(rows)):
        duration = (rows[j].dt - rows[i0].dt).total_seconds() / 60.0
        if duration < 3.0:
            continue
        if duration > 7.0:
            break
        if rows[j].dt > anchor_end:
            break

        seg = _compute_segment(rows, i0, j, symbol, min_force_delta, price_lag_pips)
        if seg is None:
            continue

        same = _same_direction(seg, anchor)
        if same >= 0.45 and len(seg.up_block) >= 2 and len(seg.down_block) >= 2:
            candidates.append(seg)

    if not candidates:
        return anchor

    def rank(seg: Segment) -> Tuple[float, float, float]:
        same = _same_direction(seg, anchor)
        compact_bonus = max(0.0, 7.0 - seg.duration_min) * 5.0
        return (same * 80.0 + seg.force_energy + compact_bonus, -seg.duration_min, seg.force_energy)

    return sorted(candidates, key=rank, reverse=True)[0]

def _select_after(
    segments: Sequence[Segment],
    after_dt: datetime,
    ref: Segment,
    mode: str,
    min_delay_min: float,
    max_delay_min: float,
) -> Optional[Segment]:
    candidates: List[Tuple[float, Segment]] = []

    for seg in segments:
        seg_start = _dt_from_segment_start(seg)
        delay = (seg_start - after_dt).total_seconds() / 60.0
        if delay < min_delay_min or delay > max_delay_min:
            continue

        if mode == "same":
            relation = _same_direction(seg, ref)
            price_bonus = 15.0 if seg.price_response in ("PRICE_PAYING", "PRICE_MOVED") else 0.0
            tf_bonus = 8.0 if seg.timeframe in (5, 15) else 0.0
            if relation < 0.25:
                continue
            score = seg.score + relation * 50.0 + price_bonus + tf_bonus
        elif mode == "opposite":
            relation = _opposite_direction(seg, ref)
            price_bonus = 15.0 if seg.price_response in ("WEAK_PRICE_RESPONSE", "PRICE_LAG") else 0.0
            if relation < 0.25:
                continue
            score = seg.score + relation * 55.0 + price_bonus
        else:
            continue

        candidates.append((score, seg))

    if not candidates:
        return None
    return sorted(candidates, key=lambda x: x[0], reverse=True)[0][1]


def _pre_field_event(rows_by_tf: Dict[int, List[SnapshotRow]], node: Optional[Segment], symbol: str) -> Optional[FlowEvent]:
    if node is None:
        return None

    node_start = _dt_from_segment_start(node)

    # Use earliest TF1/TF5 row before node and node start row proxy.
    for tf in (1, 5, 15):
        rows = [r for r in rows_by_tf.get(tf, []) if r.dt < node_start]
        if len(rows) >= 2:
            seg = _compute_segment(rows, 0, len(rows) - 1, symbol, min_force_delta=2.0, price_lag_pips=2.0)
            if seg is not None:
                return _event_from_segment(
                    "PRE_FIELD",
                    seg,
                    confidence=0.55,
                    note="Pré-champ mesuré avant la naissance du node.",
                )

    return None


def extract_flow_events(
    db_path: str,
    symbol: str,
    start: str,
    end: str,
    timeframes: Iterable[int] = (1, 5, 15),
    source_table: Optional[str] = None,
    min_window_minutes: float = 3.0,
    max_window_minutes: float = 20.0,
    min_force_delta: float = 4.0,
    price_lag_pips: float = 2.0,
    include_candidates: int = 10,
) -> FlowExtractionReport:
    start_dt = _parse_dt(start)
    end_dt = _parse_dt(end)
    if start_dt is None or end_dt is None:
        raise ValueError("Invalid --start or --end datetime.")
    if end_dt <= start_dt:
        raise ValueError("--end must be after --start.")

    tfs = [int(tf) for tf in timeframes]
    warnings: List[str] = []

    with _connect_readonly(db_path) as conn:
        table, rows_by_tf, mode, table_warnings = _choose_source_table(
            conn=conn,
            symbol=symbol,
            timeframes=tfs,
            start_dt=start_dt,
            end_dt=end_dt,
            forced_table=source_table,
        )
        warnings.extend(table_warnings)

    rows_loaded = {f"TF{tf}": len(rows_by_tf.get(tf, [])) for tf in tfs}

    if sum(rows_loaded.values()) <= 0:
        warnings.append("DATA_BLIND for requested window.")
        return FlowExtractionReport(
            symbol=symbol,
            mode=mode,
            source_table=table,
            start=start_dt.isoformat(),
            end=end_dt.isoformat(),
            timeframes=tfs,
            rows_loaded=rows_loaded,
            events=[],
            candidates=[],
            warnings=warnings,
        )

    if any(rows_loaded.get(f"TF{tf}", 0) == 0 for tf in tfs):
        warnings.append("DATA_PARTIAL: at least one requested timeframe has no rows.")

    segments = _build_segments(
        rows_by_tf=rows_by_tf,
        symbol=symbol,
        min_window_minutes=min_window_minutes,
        max_window_minutes=max_window_minutes,
        min_force_delta=min_force_delta,
        price_lag_pips=price_lag_pips,
    )

    events: List[FlowEvent] = []
    node = _select_node_birth(segments, start_dt)
    if node is not None:
        node = _compact_node_from_anchor(
            rows_by_tf=rows_by_tf,
            anchor=node,
            symbol=symbol,
            min_force_delta=min_force_delta,
            price_lag_pips=price_lag_pips,
        )

    pre = _pre_field_event(rows_by_tf, node, symbol)
    if pre is not None:
        events.append(pre)

    if node is not None:
        node_conf = 0.65
        if node.price_response == "PRICE_LAG":
            node_conf += 0.15
        if len(node.up_block) >= 3 and len(node.down_block) >= 3:
            node_conf += 0.12
        events.append(
            _event_from_segment(
                "NODE_BIRTH",
                node,
                confidence=node_conf,
                note="Basculement collectif des forces. Prix encore retenu si PRICE_LAG.",
            )
        )

        node_end = _dt_from_segment_end(node)

        confirmation = _select_after(
            segments=segments,
            after_dt=node_end,
            ref=node,
            mode="same",
            min_delay_min=2.0,
            max_delay_min=25.0,
        )
        if confirmation is not None:
            conf_conf = 0.70 + (0.15 if confirmation.price_response == "PRICE_PAYING" else 0.0)
            events.append(
                _event_from_segment(
                    "CONFIRMATION",
                    confirmation,
                    confidence=conf_conf,
                    note="Même camp dominant après node. Le prix commence à payer si PRICE_PAYING.",
                )
            )

            conf_end = _dt_from_segment_end(confirmation)
            counter = _select_after(
                segments=segments,
                after_dt=conf_end,
                ref=node,
                mode="opposite",
                min_delay_min=0.0,
                max_delay_min=25.0,
            )

            if counter is not None:
                counter_conf = 0.72
                if counter.price_response in ("WEAK_PRICE_RESPONSE", "PRICE_LAG"):
                    counter_conf += 0.13
                events.append(
                    _event_from_segment(
                        "COUNTER_BREATH",
                        counter,
                        confidence=counter_conf,
                        note="Respiration contraire après confirmation. Ne pas classer comme nouveau node principal.",
                    )
                )

                counter_end = _dt_from_segment_end(counter)
                absorption = _select_after(
                    segments=segments,
                    after_dt=counter_end,
                    ref=node,
                    mode="same",
                    min_delay_min=0.0,
                    max_delay_min=35.0,
                )
                if absorption is not None:
                    abs_conf = 0.72 + (0.10 if absorption.price_response in ("PRICE_PAYING", "PRICE_MOVED") else 0.0)
                    events.append(
                        _event_from_segment(
                            "ABSORPTION",
                            absorption,
                            confidence=abs_conf,
                            note="Le camp dominant reprend après respiration contraire.",
                        )
                    )
    else:
        warnings.append("No NODE_BIRTH candidate found.")

    # Sort by time to preserve film order, then remove accidental duplicate phases keeping first.
    events = sorted(events, key=lambda e: (_parse_dt(e.start_dt_iso) or start_dt, e.phase))
    deduped: List[FlowEvent] = []
    seen = set()
    for ev in events:
        if ev.phase in seen:
            continue
        seen.add(ev.phase)
        deduped.append(ev)

    return FlowExtractionReport(
        symbol=symbol,
        mode=mode,
        source_table=table,
        start=start_dt.isoformat(),
        end=end_dt.isoformat(),
        timeframes=tfs,
        rows_loaded=rows_loaded,
        events=deduped,
        candidates=segments[:include_candidates],
        warnings=warnings,
    )


def format_report(report: FlowExtractionReport) -> str:
    lines: List[str] = []
    lines.append("=== POWERFLOW FLOW EVENT EXTRACTOR ===")
    lines.append(f"VERSION: {EXTRACTOR_VERSION}")
    lines.append(f"SYMBOL: {report.symbol}")
    lines.append(f"WINDOW: {report.start} -> {report.end}")
    lines.append(f"SOURCE_TABLE: {report.source_table}")
    lines.append(f"MODE: {report.mode}")
    lines.append("")
    lines.append("ROWS:")
    for tf, n in report.rows_loaded.items():
        lines.append(f"{tf}: {n}")
    lines.append("")
    lines.append("EVENTS:")
    if not report.events:
        lines.append("none")
    else:
        for ev in report.events:
            lines.append(
                f"{ev.start}->{ev.end} TF{ev.timeframe} {ev.phase:<15} "
                f"energy={ev.force_energy:<8} price={ev.price_response:<20} "
                f"up={'+'.join(ev.up_block) or '-'} down={'+'.join(ev.down_block) or '-'} "
                f"conf={ev.confidence:.2f}"
            )
            lines.append(f"  note: {ev.note}")
    lines.append("")
    lines.append("TOP CANDIDATES:")
    for cand in report.candidates[:10]:
        lines.append(
            f"{cand.start}->{cand.end} TF{cand.timeframe} score={cand.score:<8} "
            f"energy={cand.force_energy:<8} price={cand.price_response:<20} "
            f"raw={cand.raw_event:<28} up={'+'.join(cand.up_block) or '-'} down={'+'.join(cand.down_block) or '-'}"
        )
    if report.warnings:
        lines.append("")
        lines.append("WARNINGS:")
        for w in report.warnings:
            lines.append(f"- {w}")
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V6 FlowEventExtractor V0.1.3.1")
    parser.add_argument("--db", required=True)
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--timeframes", default="1,5,15")
    parser.add_argument("--source-table", default=None)
    parser.add_argument("--min-window-minutes", type=float, default=3.0)
    parser.add_argument("--max-window-minutes", type=float, default=20.0)
    parser.add_argument("--min-force-delta", type=float, default=4.0)
    parser.add_argument("--price-lag-pips", type=float, default=2.0)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--out", default=None)

    args = parser.parse_args(argv)
    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]

    report = extract_flow_events(
        db_path=args.db,
        symbol=args.symbol,
        start=args.start,
        end=args.end,
        timeframes=tfs,
        source_table=args.source_table,
        min_window_minutes=args.min_window_minutes,
        max_window_minutes=args.max_window_minutes,
        min_force_delta=args.min_force_delta,
        price_lag_pips=args.price_lag_pips,
    )

    output = report.to_json() if args.json else format_report(report)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")

    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
