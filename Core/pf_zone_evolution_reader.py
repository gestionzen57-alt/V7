"""
PowerFlow V6 - pf_zone_evolution_reader.py
Mission : Lire le film de zone depuis la table zone_diagnostics.

Ce module ne calcule pas les Z-scores et ne modifie pas la perception.
Il transforme les diagnostics stockés en sequences temporelles lisibles :
PRE_EXTREME qui dure, ACCUMULATING persistant, fuite, rupture, microfilm isole,
scenarios relayes par M15/M30/H1, etc.

Entree : powerflow.db avec table zone_diagnostics creee par pf_zone_context_logger.py
Sortie : rapport texte + structures Python pures.

Compatibilite : Python standard library only.
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ACTIVE_STATES = {
    "PRE_EXTREME",
    "EARLY_EXTREME",
    "ACCUMULATING",
    "LEAKING",
    "RUPTURE",
    "DISORDER_FIELD",
    "POST_ZONE",
}

STATE_POWER = {
    "NEUTRAL": 0.0,
    "PRE_EXTREME": 0.70,
    "EARLY_EXTREME": 0.92,
    "POST_ZONE": 0.80,
    "DISORDER_FIELD": 0.85,
    "LEAKING": 1.10,
    "RUPTURE": 1.25,
    "ACCUMULATING": 1.35,
}

TF_LABELS = {
    1: "M1",
    5: "M5",
    15: "M15",
    30: "M30",
    60: "H1",
    240: "H4",
    1440: "D1",
    10080: "W1",
}

SHORT_TF = {1, 5, 15}
MEDIUM_TF = {15, 30, 60}
LONG_TF = {240, 1440, 10080}


def tf_label(timeframe: int) -> str:
    return TF_LABELS.get(int(timeframe), f"TF{timeframe}")


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def fmt_ts(value: Optional[str]) -> str:
    dt = parse_dt(value)
    if not dt:
        return str(value or "?")
    return dt.strftime("%Y-%m-%d %H:%M")


def fmt_duration(minutes: float) -> str:
    if minutes < 1:
        return "<1m"
    if minutes < 90:
        return f"{minutes:.0f}m"
    hours = minutes / 60.0
    if hours < 48:
        return f"{hours:.1f}h"
    return f"{hours / 24.0:.1f}d"


def normalize_state(state: str, zone_level: str, tension_score: float, context_score: float) -> str:
    """Clean old rows: NEUTRAL + active zone/tension becomes EARLY_EXTREME.

    This keeps the reader useful even if zone_diagnostics was logged before
    pf_zone_dynamics V0.2.3 introduced EARLY_EXTREME.
    """
    st = (state or "NEUTRAL").upper()
    zl = (zone_level or "NORMAL").upper()
    if st == "NEUTRAL" and zl not in ("", "NORMAL", "NONE", "UNKNOWN"):
        if float(tension_score or 0.0) > 0.0 or float(context_score or 0.0) > 0.0:
            return "EARLY_EXTREME"
    return st


def state_is_active(state: str, zone_level: str, tension_score: float, context_score: float) -> bool:
    state = (state or "").upper()
    zone_level = (zone_level or "").upper()
    if state in ACTIVE_STATES:
        return True
    if zone_level not in ("", "NORMAL", "NONE", "UNKNOWN"):
        return True
    return float(tension_score or 0.0) > 0.0 or float(context_score or 0.0) > 0.0


@dataclass(frozen=True)
class ZoneEvent:
    id: int
    source_created_at: str
    symbol: str
    timeframe: int
    currency: str
    state: str
    zone_level: str
    z_current: float
    z_extreme_dir: str
    bars_in_extreme: int
    pullback_count: int
    absorbed_pullback_count: int
    depth_slope: float
    depth_acceleration: float
    tension_score: float
    context_score: float
    profile_name: str
    profile_horizon: str
    session_phase: str
    rank_position: Optional[int]
    rank_total: Optional[int]
    rank_duration_bars: Optional[int]
    price_wall: bool
    context_tags: Tuple[str, ...]
    note: str

    @property
    def timestamp(self) -> Optional[datetime]:
        return parse_dt(self.source_created_at)

    @property
    def active(self) -> bool:
        return state_is_active(self.state, self.zone_level, self.tension_score, self.context_score)

    @property
    def side(self) -> str:
        direction = (self.z_extreme_dir or "").upper()
        if direction in ("HIGH", "LOW"):
            return direction
        if self.z_current > 0:
            return "HIGH"
        if self.z_current < 0:
            return "LOW"
        return "NONE"


@dataclass
class ZoneSequence:
    symbol: str
    timeframe: int
    currency: str
    side: str
    events: List[ZoneEvent] = field(default_factory=list)

    @property
    def start_at(self) -> str:
        return self.events[0].source_created_at if self.events else ""

    @property
    def end_at(self) -> str:
        return self.events[-1].source_created_at if self.events else ""

    @property
    def bar_count(self) -> int:
        return len(self.events)

    @property
    def duration_minutes(self) -> float:
        if not self.events:
            return 0.0
        start = self.events[0].timestamp
        end = self.events[-1].timestamp
        tf = max(1, int(self.timeframe))
        if start and end:
            span = max(0.0, (end - start).total_seconds() / 60.0)
            return span + tf
        return float(tf * len(self.events))

    @property
    def states(self) -> List[str]:
        return [e.state for e in self.events]

    @property
    def unique_states(self) -> List[str]:
        out: List[str] = []
        for st in self.states:
            if not out or out[-1] != st:
                out.append(st)
        return out

    @property
    def state_path(self) -> str:
        return "->".join(self.unique_states)

    @property
    def start_state(self) -> str:
        return self.events[0].state if self.events else "NONE"

    @property
    def end_state(self) -> str:
        return self.events[-1].state if self.events else "NONE"

    @property
    def state_span(self) -> str:
        if not self.events:
            return "NONE"
        if self.start_state == self.end_state:
            return self.start_state
        return f"{self.start_state}->{self.end_state}"

    @property
    def dominant_state(self) -> str:
        counts: Dict[str, int] = {}
        for st in self.states:
            counts[st] = counts.get(st, 0) + 1
        if not counts:
            return "NONE"
        return sorted(counts.items(), key=lambda kv: (kv[1], STATE_POWER.get(kv[0], 0.0)), reverse=True)[0][0]

    @property
    def max_context_score(self) -> float:
        return max((e.context_score for e in self.events), default=0.0)

    @property
    def avg_context_score(self) -> float:
        if not self.events:
            return 0.0
        return sum(e.context_score for e in self.events) / len(self.events)

    @property
    def max_tension_score(self) -> float:
        return max((e.tension_score for e in self.events), default=0.0)

    @property
    def z_start(self) -> float:
        return self.events[0].z_current if self.events else 0.0

    @property
    def z_end(self) -> float:
        return self.events[-1].z_current if self.events else 0.0

    @property
    def z_peak_abs(self) -> float:
        return max((abs(e.z_current) for e in self.events), default=0.0)

    @property
    def session_phases(self) -> List[str]:
        out: List[str] = []
        for e in self.events:
            phase = e.session_phase or "UNKNOWN"
            if phase not in out:
                out.append(phase)
        return out

    @property
    def profile_horizons(self) -> List[str]:
        out: List[str] = []
        for e in self.events:
            h = e.profile_horizon or "UNKNOWN"
            if h not in out:
                out.append(h)
        return out

    @property
    def tags(self) -> List[str]:
        out: List[str] = []
        for e in self.events:
            for tag in e.context_tags:
                if tag not in out:
                    out.append(tag)
        return out

    @property
    def transition_bonus(self) -> float:
        path = self.unique_states
        bonus = 0.0
        pairs = list(zip(path, path[1:]))
        for a, b in pairs:
            if a == "PRE_EXTREME" and b == "EARLY_EXTREME":
                bonus += 0.8
            elif a == "EARLY_EXTREME" and b == "ACCUMULATING":
                bonus += 1.6
            elif a == "PRE_EXTREME" and b == "ACCUMULATING":
                bonus += 2.0
            elif a == "ACCUMULATING" and b == "LEAKING":
                bonus += 1.5
            elif b == "RUPTURE":
                bonus += 2.2
            elif a == "PRE_EXTREME" and b in ("LEAKING", "RUPTURE"):
                bonus += 1.0
            elif b == "DISORDER_FIELD":
                bonus += 0.8
        return bonus

    @property
    def evolution_score(self) -> float:
        if not self.events:
            return 0.0
        state_power = max(STATE_POWER.get(e.state, 0.0) for e in self.events)
        persistence = math.log1p(self.bar_count) * 1.25
        duration_bonus = math.log1p(max(1.0, self.duration_minutes)) * 0.45
        context = self.max_context_score
        transition = self.transition_bonus
        # M1 is useful but fragile; keep it visible while reducing isolated dominance.
        micro_penalty = 0.82 if self.timeframe == 1 and self.bar_count <= 3 else 1.0
        return round((context * state_power + persistence + duration_bonus + transition) * micro_penalty, 3)

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timeframe_label": tf_label(self.timeframe),
            "currency": self.currency,
            "side": self.side,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "duration_minutes": round(self.duration_minutes, 2),
            "bar_count": self.bar_count,
            "state_path": self.state_path,
            "start_state": self.start_state,
            "end_state": self.end_state,
            "state_span": self.state_span,
            "dominant_state": self.dominant_state,
            "max_context_score": round(self.max_context_score, 3),
            "avg_context_score": round(self.avg_context_score, 3),
            "max_tension_score": round(self.max_tension_score, 3),
            "z_start": round(self.z_start, 4),
            "z_end": round(self.z_end, 4),
            "z_peak_abs": round(self.z_peak_abs, 4),
            "session_phases": self.session_phases,
            "profile_horizons": self.profile_horizons,
            "context_tags": self.tags,
            "transition_bonus": round(self.transition_bonus, 3),
            "evolution_score": self.evolution_score,
        }


@dataclass(frozen=True)
class TransitionCount:
    symbol: str
    timeframe: int
    currency: str
    from_state: str
    to_state: str
    count: int


def _json_tags(text: Optional[str]) -> Tuple[str, ...]:
    if not text:
        return tuple()
    try:
        value = json.loads(text)
    except Exception:
        return tuple()
    if isinstance(value, list):
        return tuple(str(x) for x in value)
    return tuple()


def fetch_zone_events(
    db_path: str,
    symbol: Optional[str] = None,
    timeframes: Optional[Sequence[int]] = None,
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
) -> List[ZoneEvent]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='zone_diagnostics'"
        ).fetchone()
        if not exists:
            raise RuntimeError("Table zone_diagnostics introuvable. Lance d'abord run_zone_context_logger_history.py")

        clauses = []
        params: List[object] = []
        if symbol:
            clauses.append("symbol = ?")
            params.append(symbol)
        if timeframes:
            placeholders = ",".join("?" for _ in timeframes)
            clauses.append(f"timeframe IN ({placeholders})")
            params.extend(int(x) for x in timeframes)
        if currencies:
            placeholders = ",".join("?" for _ in currencies)
            clauses.append(f"currency IN ({placeholders})")
            params.extend(str(x).upper() for x in currencies)
        if since:
            clauses.append("source_created_at >= ?")
            params.append(since)
        if until:
            clauses.append("source_created_at <= ?")
            params.append(until)

        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        rows = conn.execute(
            """
            SELECT *
            FROM zone_diagnostics
            {where}
            ORDER BY symbol, currency, timeframe, source_created_at, id
            """.format(where=where),
            params,
        ).fetchall()
    finally:
        conn.close()

    events: List[ZoneEvent] = []
    for r in rows:
        raw_state = str(r["state"] or "NEUTRAL")
        raw_zone_level = str(r["zone_level"] or "NORMAL")
        raw_tension = float(r["tension_score"] or 0.0)
        raw_context = float(r["context_score"] or 0.0)
        clean_state = normalize_state(raw_state, raw_zone_level, raw_tension, raw_context)
        events.append(ZoneEvent(
            id=int(r["id"]),
            source_created_at=str(r["source_created_at"] or ""),
            symbol=str(r["symbol"] or ""),
            timeframe=int(r["timeframe"]),
            currency=str(r["currency"] or ""),
            state=clean_state,
            zone_level=raw_zone_level,
            z_current=float(r["z_current"] or 0.0),
            z_extreme_dir=str(r["z_extreme_dir"] or "NONE"),
            bars_in_extreme=int(r["bars_in_extreme"] or 0),
            pullback_count=int(r["pullback_count"] or 0),
            absorbed_pullback_count=int(r["absorbed_pullback_count"] or 0),
            depth_slope=float(r["depth_slope"] or 0.0),
            depth_acceleration=float(r["depth_acceleration"] or 0.0),
            tension_score=raw_tension,
            context_score=raw_context,
            profile_name=str(r["profile_name"] or ""),
            profile_horizon=str(r["profile_horizon"] or ""),
            session_phase=str(r["session_phase"] or ""),
            rank_position=r["rank_position"],
            rank_total=r["rank_total"],
            rank_duration_bars=r["rank_duration_bars"],
            price_wall=bool(r["price_wall"]),
            context_tags=_json_tags(r["context_tags_json"]),
            note=str(r["note"] or ""),
        ))
    return events


def build_zone_sequences(
    events: Sequence[ZoneEvent],
    allow_gap_bars: int = 1,
    include_single_bar: bool = True,
) -> List[ZoneSequence]:
    """Build active zone sequences by symbol/currency/timeframe/side.

    A sequence starts when a row becomes active and ends when the stream returns
    to NEUTRAL/NORMAL or when side flips. Small timestamp gaps are tolerated by
    relying on the row order rather than absolute time.
    """
    grouped: Dict[Tuple[str, str, int], List[ZoneEvent]] = {}
    for event in events:
        grouped.setdefault((event.symbol, event.currency, event.timeframe), []).append(event)

    sequences: List[ZoneSequence] = []
    for (symbol, currency, timeframe), rows in grouped.items():
        rows = sorted(rows, key=lambda e: (e.source_created_at, e.id))
        current: Optional[ZoneSequence] = None
        neutral_gap = 0

        for event in rows:
            active = event.active
            side = event.side
            if active:
                if current is None:
                    current = ZoneSequence(symbol=symbol, timeframe=timeframe, currency=currency, side=side, events=[event])
                    neutral_gap = 0
                    continue
                if current.side != side and side != "NONE":
                    if include_single_bar or current.bar_count > 1:
                        sequences.append(current)
                    current = ZoneSequence(symbol=symbol, timeframe=timeframe, currency=currency, side=side, events=[event])
                    neutral_gap = 0
                else:
                    current.events.append(event)
                    neutral_gap = 0
            else:
                if current is not None:
                    neutral_gap += 1
                    if neutral_gap > allow_gap_bars:
                        if include_single_bar or current.bar_count > 1:
                            sequences.append(current)
                        current = None
                        neutral_gap = 0

        if current is not None and (include_single_bar or current.bar_count > 1):
            sequences.append(current)

    sequences.sort(key=lambda s: s.evolution_score, reverse=True)
    return sequences


def count_transitions(events: Sequence[ZoneEvent]) -> List[TransitionCount]:
    grouped: Dict[Tuple[str, str, int], List[ZoneEvent]] = {}
    for event in events:
        grouped.setdefault((event.symbol, event.currency, event.timeframe), []).append(event)

    counts: Dict[Tuple[str, int, str, str, str], int] = {}
    for (symbol, currency, timeframe), rows in grouped.items():
        rows = sorted(rows, key=lambda e: (e.source_created_at, e.id))
        previous: Optional[str] = None
        for event in rows:
            st = event.state
            if previous is not None and st != previous:
                key = (symbol, timeframe, currency, previous, st)
                counts[key] = counts.get(key, 0) + 1
            previous = st

    out = [TransitionCount(symbol=k[0], timeframe=k[1], currency=k[2], from_state=k[3], to_state=k[4], count=v) for k, v in counts.items()]
    out.sort(key=lambda x: (x.count, STATE_POWER.get(x.to_state, 0.0)), reverse=True)
    return out


def latest_active_events(events: Sequence[ZoneEvent], limit: int = 20) -> List[ZoneEvent]:
    active = [e for e in events if e.active]
    active.sort(key=lambda e: (e.source_created_at, e.context_score), reverse=True)
    return active[:limit]


def build_evolution_report(
    db_path: str,
    symbol: Optional[str] = None,
    timeframes: Optional[Sequence[int]] = None,
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    top: int = 20,
) -> str:
    events = fetch_zone_events(
        db_path=db_path,
        symbol=symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=since,
        until=until,
    )
    sequences = build_zone_sequences(events)
    transitions = count_transitions(events)
    latest = latest_active_events(events, limit=min(top, 20))

    state_counts: Dict[str, int] = {}
    tf_counts: Dict[int, int] = {}
    for e in events:
        state_counts[e.state] = state_counts.get(e.state, 0) + 1
        tf_counts[e.timeframe] = tf_counts.get(e.timeframe, 0) + 1

    lines: List[str] = []
    lines.append("PowerFlow Zone Evolution Report - FILM DE ZONE")
    lines.append("=" * 88)
    lines.append(f"Events: {len(events)} | Sequences: {len(sequences)}")
    if symbol:
        lines.append(f"Symbol: {symbol}")
    if timeframes:
        lines.append("Timeframes: " + ", ".join(tf_label(x) for x in timeframes))
    if currencies:
        lines.append("Currencies: " + ", ".join(currencies))
    if since or until:
        lines.append(f"Window: {since or '-inf'} -> {until or '+inf'}")

    lines.append("")
    lines.append("By state:")
    for st, count in sorted(state_counts.items(), key=lambda kv: kv[1], reverse=True):
        lines.append(f"  {st:<16} {count}")

    lines.append("")
    lines.append("By timeframe:")
    for tf, count in sorted(tf_counts.items()):
        lines.append(f"  {tf_label(tf):<5} {count}")

    lines.append("")
    lines.append(f"Top {min(top, len(sequences))} zone sequences:")
    lines.append("-" * 88)
    for idx, seq in enumerate(sequences[:top], start=1):
        lines.append(
            f"{idx:02d}. {seq.currency:<3} {tf_label(seq.timeframe):<3} {seq.side:<4} "
            f"{seq.state_span:<29} score={seq.evolution_score:<7.3f} "
            f"ctx_max={seq.max_context_score:<7.3f} tension_max={seq.max_tension_score:<7.3f} "
            f"bars={seq.bar_count:<3} dur={fmt_duration(seq.duration_minutes):<6} "
            f"{fmt_ts(seq.start_at)} -> {fmt_ts(seq.end_at)}"
        )
        lines.append(
            f"    path={seq.state_path} | z {seq.z_start:+.3f}->{seq.z_end:+.3f} "
            f"peak_abs={seq.z_peak_abs:.3f} | sessions={','.join(seq.session_phases)} | "
            f"horizon={','.join(seq.profile_horizons)}"
        )

    rupture_sequences = [s for s in sequences if s.end_state == "RUPTURE"]
    if rupture_sequences:
        lines.append("")
        lines.append(f"Sequences ending in RUPTURE ({min(10, len(rupture_sequences))} shown):")
        lines.append("-" * 88)
        for idx, seq in enumerate(rupture_sequences[:10], start=1):
            lines.append(
                f"{idx:02d}. {seq.currency:<3} {tf_label(seq.timeframe):<3} {seq.side:<4} "
                f"{seq.state_path:<42} score={seq.evolution_score:<7.3f} "
                f"dur={fmt_duration(seq.duration_minutes):<6} {fmt_ts(seq.start_at)} -> {fmt_ts(seq.end_at)}"
            )

    long_accumulations = [
        s for s in sequences
        if "ACCUMULATING" in s.unique_states and (s.duration_minutes >= 60 or s.bar_count >= 6)
    ]
    if long_accumulations:
        lines.append("")
        lines.append(f"Long accumulation sequences ({min(10, len(long_accumulations))} shown):")
        lines.append("-" * 88)
        for idx, seq in enumerate(long_accumulations[:10], start=1):
            lines.append(
                f"{idx:02d}. {seq.currency:<3} {tf_label(seq.timeframe):<3} {seq.side:<4} "
                f"{seq.state_path:<42} ctx_max={seq.max_context_score:<7.3f} "
                f"dur={fmt_duration(seq.duration_minutes):<6} bars={seq.bar_count:<3}"
            )

    lines.append("")
    lines.append(f"Top {min(top, len(transitions))} state transitions:")
    lines.append("-" * 88)
    for idx, tr in enumerate(transitions[:top], start=1):
        lines.append(
            f"{idx:02d}. {tr.currency:<3} {tf_label(tr.timeframe):<3} "
            f"{tr.from_state:<13} -> {tr.to_state:<13} count={tr.count}"
        )

    lines.append("")
    lines.append("Latest active zone events:")
    lines.append("-" * 88)
    for e in latest:
        lines.append(
            f"{fmt_ts(e.source_created_at)} {tf_label(e.timeframe):<3} {e.currency:<3} "
            f"{e.state:<13} {e.zone_level:<11} z={e.z_current:+.3f} "
            f"tension={e.tension_score:.3f} ctx={e.context_score:.3f} "
            f"{e.profile_name}/{e.profile_horizon}"
        )

    lines.append("")
    lines.append("Lecture tactique:")
    lines.append("-" * 88)
    if sequences:
        top_seq = sequences[0]
        lines.append(
            f"Zone dominante: {top_seq.currency} {tf_label(top_seq.timeframe)} {top_seq.side} "
            f"{top_seq.state_span}, {fmt_duration(top_seq.duration_minutes)}, "
            f"score evolution {top_seq.evolution_score:.3f}."
        )
        medium = [s for s in sequences if s.timeframe in MEDIUM_TF]
        short = [s for s in sequences if s.timeframe in SHORT_TF]
        if medium:
            m = medium[0]
            lines.append(
                f"Scenario le plus propre: {m.currency} {tf_label(m.timeframe)} {m.state_span} / {m.state_path} "
                f"ctx_max={m.max_context_score:.3f}."
            )
        if short:
            s = short[0]
            lines.append(
                f"Court terme le plus actif: {s.currency} {tf_label(s.timeframe)} {s.state_span} / {s.state_path} "
                f"ctx_max={s.max_context_score:.3f}."
            )
    else:
        lines.append("Aucune sequence active. Logger plus d'historique ou verifier la table zone_diagnostics.")

    return "\n".join(lines)


__all__ = [
    "normalize_state",
    "ZoneEvent",
    "ZoneSequence",
    "TransitionCount",
    "fetch_zone_events",
    "build_zone_sequences",
    "count_transitions",
    "latest_active_events",
    "build_evolution_report",
    "tf_label",
]
