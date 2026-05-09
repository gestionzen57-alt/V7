"""
PowerFlow V6 - pf_fractal_zone_stack.py
Version: V0.1

Mission:
    Lire le film de zone deja construit et detecter les empilements fractals :
    meme devise + meme direction + chevauchement temporel + timeframe superieur porteur.

Doctrine:
    - Ne recalcule pas les Z-scores.
    - Ne modifie pas la DB.
    - Ne remplace pas pf_zone_dynamics.py.
    - Transforme des sequences locales en scenes multi-timeframe.

Entree:
    powerflow.db avec table zone_diagnostics
    pf_zone_evolution_reader.py disponible dans le meme dossier.

Sortie:
    structures Python + rapport texte.
"""

from __future__ import annotations

import argparse
import math
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from pf_zone_evolution_reader import (
    ZoneSequence,
    build_zone_sequences,
    fetch_zone_events,
    fmt_duration,
    fmt_ts,
    parse_dt,
    tf_label,
)


TF_ORDER = [1, 5, 15, 30, 60, 240, 1440, 10080]
TF_RANK = {tf: idx for idx, tf in enumerate(TF_ORDER)}

SHORT_TF = {1, 5, 15}
MEDIUM_TF = {15, 30, 60}
LONG_TF = {240, 1440, 10080}

STRONG_STATES = {"EARLY_EXTREME", "ACCUMULATING", "LEAKING", "RUPTURE"}
RELEASE_STATES = {"LEAKING", "RUPTURE", "POST_ZONE"}


def _dt(value: str) -> Optional[datetime]:
    return parse_dt(value)


def _tf_rank(tf: int) -> int:
    return TF_RANK.get(int(tf), 999)


def _interval(seq: ZoneSequence) -> Tuple[Optional[datetime], Optional[datetime]]:
    return _dt(seq.start_at), _dt(seq.end_at)


def _minutes_between(a: datetime, b: datetime) -> float:
    return abs((b - a).total_seconds()) / 60.0


def _overlap_minutes(a: ZoneSequence, b: ZoneSequence) -> float:
    a0, a1 = _interval(a)
    b0, b1 = _interval(b)
    if not a0 or not a1 or not b0 or not b1:
        return 0.0
    start = max(a0, b0)
    end = min(a1, b1)
    if end < start:
        return 0.0
    return max(0.0, (end - start).total_seconds() / 60.0)


def _gap_minutes(a: ZoneSequence, b: ZoneSequence) -> float:
    a0, a1 = _interval(a)
    b0, b1 = _interval(b)
    if not a0 or not a1 or not b0 or not b1:
        return 10**9
    if a1 < b0:
        return _minutes_between(a1, b0)
    if b1 < a0:
        return _minutes_between(b1, a0)
    return 0.0


def _overlaps_or_near(a: ZoneSequence, b: ZoneSequence, max_gap_minutes: float) -> bool:
    if a.currency != b.currency or a.side != b.side:
        return False
    if a.timeframe == b.timeframe:
        return False
    if a.side in ("NONE", "", None):
        return False
    return _overlap_minutes(a, b) > 0.0 or _gap_minutes(a, b) <= max_gap_minutes


def _component_window(sequences: Sequence[ZoneSequence]) -> Tuple[str, str]:
    starts = [s.start_at for s in sequences if s.start_at]
    ends = [s.end_at for s in sequences if s.end_at]
    return (min(starts) if starts else "", max(ends) if ends else "")


def _duration_minutes(start_at: str, end_at: str) -> float:
    start = _dt(start_at)
    end = _dt(end_at)
    if not start or not end:
        return 0.0
    return max(0.0, (end - start).total_seconds() / 60.0)


def _session_union(sequences: Sequence[ZoneSequence]) -> List[str]:
    out: List[str] = []
    for seq in sequences:
        for session in seq.session_phases:
            if session not in out:
                out.append(session)
    return out


def _state_path_union(sequences: Sequence[ZoneSequence]) -> List[str]:
    out: List[str] = []
    for seq in sorted(sequences, key=lambda s: (_tf_rank(s.timeframe), s.start_at)):
        label = f"{tf_label(seq.timeframe)}:{seq.state_path}"
        if label not in out:
            out.append(label)
    return out


def _tf_weight(tf: int) -> float:
    if tf == 1:
        return 0.72
    if tf == 5:
        return 0.92
    if tf == 15:
        return 1.10
    if tf == 30:
        return 1.22
    if tf == 60:
        return 1.35
    if tf in LONG_TF:
        return 1.55
    return 1.0


def _consecutive_tf_bonus(tfs: Sequence[int]) -> float:
    ranks = sorted(_tf_rank(tf) for tf in set(tfs))
    if len(ranks) < 2:
        return 0.0
    consecutive_pairs = sum(1 for a, b in zip(ranks, ranks[1:]) if b - a == 1)
    return consecutive_pairs * 0.65


def _has_state(seq: ZoneSequence, states: Set[str]) -> bool:
    return any(st in states for st in seq.unique_states)


@dataclass(frozen=True)
class FractalZoneStack:
    symbol: str
    currency: str
    side: str
    sequences: Tuple[ZoneSequence, ...]
    max_gap_minutes: float

    @property
    def timeframes(self) -> List[int]:
        return sorted({s.timeframe for s in self.sequences}, key=_tf_rank)

    @property
    def timeframe_labels(self) -> List[str]:
        return [tf_label(tf) for tf in self.timeframes]

    @property
    def start_at(self) -> str:
        return _component_window(self.sequences)[0]

    @property
    def end_at(self) -> str:
        return _component_window(self.sequences)[1]

    @property
    def duration_minutes(self) -> float:
        return _duration_minutes(self.start_at, self.end_at)

    @property
    def anchor_sequence(self) -> ZoneSequence:
        return sorted(
            self.sequences,
            key=lambda s: (_tf_rank(s.timeframe), s.evolution_score),
            reverse=True,
        )[0]

    @property
    def trigger_sequence(self) -> ZoneSequence:
        non_m1 = [s for s in self.sequences if s.timeframe != 1]
        pool = non_m1 if non_m1 else list(self.sequences)
        return sorted(pool, key=lambda s: (_tf_rank(s.timeframe), s.evolution_score))[0]

    @property
    def scenario_sequence(self) -> ZoneSequence:
        medium = [s for s in self.sequences if s.timeframe in MEDIUM_TF]
        pool = medium if medium else list(self.sequences)
        return sorted(pool, key=lambda s: (s.evolution_score, _tf_rank(s.timeframe)), reverse=True)[0]

    @property
    def max_context_score(self) -> float:
        return max((s.max_context_score for s in self.sequences), default=0.0)

    @property
    def max_tension_score(self) -> float:
        return max((s.max_tension_score for s in self.sequences), default=0.0)

    @property
    def total_bars(self) -> int:
        return sum(s.bar_count for s in self.sequences)

    @property
    def sessions(self) -> List[str]:
        return _session_union(self.sequences)

    @property
    def state_paths(self) -> List[str]:
        return _state_path_union(self.sequences)

    @property
    def has_release(self) -> bool:
        return any(_has_state(s, RELEASE_STATES) for s in self.sequences)

    @property
    def has_accumulation(self) -> bool:
        return any(_has_state(s, {"ACCUMULATING"}) for s in self.sequences)

    @property
    def has_superior_anchor(self) -> bool:
        """True when a higher timeframe carries at least one lower timeframe."""
        return len(self.timeframes) >= 2 and self.anchor_sequence.timeframe > min(self.timeframes)

    @property
    def has_htf_anchor(self) -> bool:
        """H1/H4/D1/W gravity/structure anchor."""
        return any(s.timeframe >= 60 for s in self.sequences)

    @property
    def has_m1(self) -> bool:
        return any(s.timeframe == 1 for s in self.sequences)

    @property
    def has_m5_m15_relay(self) -> bool:
        tfs = set(self.timeframes)
        return 5 in tfs and 15 in tfs

    @property
    def overlap_density(self) -> float:
        seqs = list(self.sequences)
        if len(seqs) < 2:
            return 0.0
        hits = 0
        pairs = 0
        for i, a in enumerate(seqs):
            for b in seqs[i + 1:]:
                pairs += 1
                if _overlap_minutes(a, b) > 0.0:
                    hits += 1
        return hits / max(1, pairs)

    @property
    def tags(self) -> List[str]:
        tfs = set(self.timeframes)
        tags: List[str] = ["FRACTAL_ZONE_STACK"]

        if self.has_superior_anchor:
            tags.append("SUPERIOR_TF_CARRIED_ZONE")
        if self.has_htf_anchor and any(tf in tfs for tf in (1, 5, 15, 30)):
            tags.append("HTF_ANCHORED_ZONE")
        elif self.anchor_sequence.timeframe >= 30:
            tags.append("SCENARIO_ANCHORED_ZONE")
        if self.has_m5_m15_relay:
            tags.append("M15_SCENARIO_WITH_M5_RELAY")
        if 15 in tfs and 30 in tfs:
            tags.append("M30_M15_SCENARIO_STACK")
        if 30 in tfs and 60 in tfs:
            tags.append("H1_M30_SCENARIO_STACK")
        if any(tf in LONG_TF for tf in tfs):
            tags.append("HTF_GRAVITY_STACK")
        if self.has_m1:
            tags.append("M1_MICROFILM_RELAY")
        if self.has_release:
            tags.append("ZONE_RELEASE_ALIGNMENT")
        if self.has_accumulation:
            tags.append("MULTI_TF_ZONE_ACCUMULATION")
        if len(tfs) >= 3:
            tags.append("TF_CASCADE_BUILD")
        if tfs.issubset(SHORT_TF):
            tags.append("SHORT_FRACTAL_RELEASE")
        if self.overlap_density >= 0.66:
            tags.append("DENSE_TEMPORAL_OVERLAP")

        return tags

    @property
    def stack_score(self) -> float:
        seqs = list(self.sequences)
        if not seqs:
            return 0.0

        weighted = sum(s.evolution_score * _tf_weight(s.timeframe) for s in seqs)
        compression = math.sqrt(len(seqs))
        tf_bonus = math.log1p(len(self.timeframes)) * 2.2
        cascade_bonus = _consecutive_tf_bonus(self.timeframes)
        overlap_bonus = self.overlap_density * 2.5
        anchor_bonus = 3.2 if self.anchor_sequence.timeframe >= 60 else 2.4 if self.anchor_sequence.timeframe >= 30 else 1.4
        release_bonus = 3.0 if self.has_release else 0.0
        accumulation_bonus = 1.8 if self.has_accumulation else 0.0
        m1_penalty = 0.92 if self.has_m1 and len(self.timeframes) <= 2 else 1.0

        score = ((weighted / compression) + tf_bonus + cascade_bonus + overlap_bonus + anchor_bonus + release_bonus + accumulation_bonus) * m1_penalty
        return round(score, 3)

    @property
    def tactical_label(self) -> str:
        tagset = set(self.tags)
        if "HTF_ANCHORED_ZONE" in tagset and "ZONE_RELEASE_ALIGNMENT" in tagset:
            return "HTF_ANCHORED_RELEASE_STACK"
        if "HTF_ANCHORED_ZONE" in tagset:
            return "HTF_ANCHORED_ZONE"
        if "SCENARIO_ANCHORED_ZONE" in tagset and "ZONE_RELEASE_ALIGNMENT" in tagset:
            return "SCENARIO_ANCHORED_RELEASE_STACK"
        if "SCENARIO_ANCHORED_ZONE" in tagset:
            return "SCENARIO_ANCHORED_ZONE"
        if "M15_SCENARIO_WITH_M5_RELAY" in tagset:
            return "M15_SCENARIO_WITH_M5_RELAY"
        if "SHORT_FRACTAL_RELEASE" in tagset:
            return "SHORT_FRACTAL_RELEASE"
        return "FRACTAL_ZONE_STACK"

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "currency": self.currency,
            "side": self.side,
            "timeframes": self.timeframe_labels,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "duration_minutes": round(self.duration_minutes, 2),
            "stack_score": self.stack_score,
            "tactical_label": self.tactical_label,
            "tags": self.tags,
            "anchor_tf": tf_label(self.anchor_sequence.timeframe),
            "trigger_tf": tf_label(self.trigger_sequence.timeframe),
            "scenario_tf": tf_label(self.scenario_sequence.timeframe),
            "max_context_score": round(self.max_context_score, 3),
            "max_tension_score": round(self.max_tension_score, 3),
            "total_bars": self.total_bars,
            "sessions": self.sessions,
            "state_paths": self.state_paths,
            "overlap_density": round(self.overlap_density, 3),
        }


def filter_stackable_sequences(
    sequences: Sequence[ZoneSequence],
    min_score: float = 5.0,
    min_bars: int = 2,
) -> List[ZoneSequence]:
    out: List[ZoneSequence] = []
    for seq in sequences:
        if seq.side in ("", "NONE", None):
            continue
        if seq.evolution_score < min_score:
            continue
        if seq.bar_count < min_bars:
            continue
        if not (seq.max_context_score > 0.0 or seq.max_tension_score > 0.0):
            continue
        out.append(seq)
    return out


def build_fractal_zone_stacks(
    sequences: Sequence[ZoneSequence],
    max_gap_minutes: float = 45.0,
    min_score: float = 5.0,
    min_bars: int = 2,
    require_multi_tf: bool = True,
) -> List[FractalZoneStack]:
    candidates = filter_stackable_sequences(sequences, min_score=min_score, min_bars=min_bars)

    grouped: Dict[Tuple[str, str, str], List[ZoneSequence]] = {}
    for seq in candidates:
        grouped.setdefault((seq.symbol, seq.currency, seq.side), []).append(seq)

    stacks: List[FractalZoneStack] = []
    seen_keys: Set[Tuple[int, ...]] = set()

    for (symbol, currency, side), rows in grouped.items():
        rows = sorted(rows, key=lambda s: (s.start_at, _tf_rank(s.timeframe), -s.evolution_score))
        n = len(rows)
        adjacency: Dict[int, Set[int]] = {i: set() for i in range(n)}

        for i in range(n):
            for j in range(i + 1, n):
                if _overlaps_or_near(rows[i], rows[j], max_gap_minutes=max_gap_minutes):
                    adjacency[i].add(j)
                    adjacency[j].add(i)

        visited: Set[int] = set()
        for i in range(n):
            if i in visited:
                continue
            stack: List[int] = []
            todo = [i]
            visited.add(i)
            while todo:
                cur = todo.pop()
                stack.append(cur)
                for nb in adjacency[cur]:
                    if nb not in visited:
                        visited.add(nb)
                        todo.append(nb)

            component = [rows[idx] for idx in stack]
            tfs = {s.timeframe for s in component}
            if require_multi_tf and len(tfs) < 2:
                continue

            # A fractal stack needs a carrier sequence and a lower/sibling relay.
            # Avoid forming a "stack" from two tiny isolated micro events.
            if max(tfs, key=_tf_rank) == 1:
                continue

            key = tuple(sorted(id(s) for s in component))
            if key in seen_keys:
                continue
            seen_keys.add(key)

            stacks.append(FractalZoneStack(
                symbol=symbol,
                currency=currency,
                side=side,
                sequences=tuple(sorted(component, key=lambda s: (_tf_rank(s.timeframe), s.start_at))),
                max_gap_minutes=max_gap_minutes,
            ))

    stacks.sort(key=lambda s: s.stack_score, reverse=True)
    return stacks


def build_fractal_stack_report(
    db_path: str,
    symbol: Optional[str] = None,
    timeframes: Optional[Sequence[int]] = None,
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    until: Optional[str] = None,
    top: int = 20,
    max_gap_minutes: float = 45.0,
    min_sequence_score: float = 5.0,
    min_bars: int = 2,
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
    stacks = build_fractal_zone_stacks(
        sequences,
        max_gap_minutes=max_gap_minutes,
        min_score=min_sequence_score,
        min_bars=min_bars,
        require_multi_tf=True,
    )

    lines: List[str] = []
    lines.append("PowerFlow Fractal Zone Stack Report - SCENE MULTI-TF")
    lines.append("=" * 92)
    lines.append(f"Events: {len(events)} | Local sequences: {len(sequences)} | Fractal stacks: {len(stacks)}")
    if symbol:
        lines.append(f"Symbol: {symbol}")
    if timeframes:
        lines.append("Timeframes: " + ", ".join(tf_label(x) for x in timeframes))
    if currencies:
        lines.append("Currencies: " + ", ".join(currencies))
    lines.append(f"Max temporal gap: {max_gap_minutes:.0f}m | Min sequence score: {min_sequence_score:.1f}")

    lines.append("")
    lines.append(f"Top {min(top, len(stacks))} fractal zone stacks:")
    lines.append("-" * 92)

    for idx, stack in enumerate(stacks[:top], start=1):
        lines.append(
            f"{idx:02d}. {stack.currency:<3} {stack.side:<4} {stack.tactical_label:<28} "
            f"score={stack.stack_score:<7.3f} tfs={','.join(stack.timeframe_labels):<18} "
            f"dur={fmt_duration(stack.duration_minutes):<6} {fmt_ts(stack.start_at)} -> {fmt_ts(stack.end_at)}"
        )
        lines.append(
            f"    anchor={tf_label(stack.anchor_sequence.timeframe)} "
            f"trigger={tf_label(stack.trigger_sequence.timeframe)} "
            f"scenario={tf_label(stack.scenario_sequence.timeframe)} "
            f"ctx_max={stack.max_context_score:.3f} tension_max={stack.max_tension_score:.3f} "
            f"overlap={stack.overlap_density:.2f}"
        )
        lines.append(
            f"    tags={','.join(stack.tags)} | sessions={','.join(stack.sessions)}"
        )
        for path in stack.state_paths:
            lines.append(f"      {path}")

    anchored = [s for s in stacks if "SUPERIOR_TF_CARRIED_ZONE" in s.tags]
    release = [s for s in stacks if "ZONE_RELEASE_ALIGNMENT" in s.tags]
    micro = [s for s in stacks if "M1_MICROFILM_RELAY" in s.tags]

    lines.append("")
    lines.append(f"Superior TF carried stacks ({min(10, len(anchored))} shown):")
    lines.append("-" * 92)
    for idx, stack in enumerate(anchored[:10], start=1):
        lines.append(
            f"{idx:02d}. {stack.currency:<3} {stack.side:<4} {','.join(stack.timeframe_labels):<16} "
            f"anchor={tf_label(stack.anchor_sequence.timeframe):<3} score={stack.stack_score:<7.3f} "
            f"{fmt_ts(stack.start_at)} -> {fmt_ts(stack.end_at)}"
        )

    lines.append("")
    lines.append(f"Release alignments ({min(10, len(release))} shown):")
    lines.append("-" * 92)
    for idx, stack in enumerate(release[:10], start=1):
        lines.append(
            f"{idx:02d}. {stack.currency:<3} {stack.side:<4} {stack.tactical_label:<28} "
            f"score={stack.stack_score:<7.3f} tfs={','.join(stack.timeframe_labels):<16} "
            f"{fmt_duration(stack.duration_minutes):<6}"
        )

    lines.append("")
    lines.append(f"Microfilm relays ({min(10, len(micro))} shown):")
    lines.append("-" * 92)
    for idx, stack in enumerate(micro[:10], start=1):
        lines.append(
            f"{idx:02d}. {stack.currency:<3} {stack.side:<4} tfs={','.join(stack.timeframe_labels):<16} "
            f"score={stack.stack_score:<7.3f} {fmt_ts(stack.start_at)} -> {fmt_ts(stack.end_at)}"
        )

    lines.append("")
    lines.append("Lecture tactique:")
    lines.append("-" * 92)
    if stacks:
        top_stack = stacks[0]
        lines.append(
            f"Scene fractale dominante: {top_stack.currency} {top_stack.side} "
            f"{top_stack.tactical_label}, TF={','.join(top_stack.timeframe_labels)}, "
            f"score={top_stack.stack_score:.3f}."
        )
        lines.append(
            f"TF porteur: {tf_label(top_stack.anchor_sequence.timeframe)} | "
            f"relais tactique: {tf_label(top_stack.trigger_sequence.timeframe)} | "
            f"scenario: {tf_label(top_stack.scenario_sequence.timeframe)}."
        )
        if top_stack.has_release:
            lines.append("La scene contient une fuite/rupture: la zone a libere ou commence a liberer l'energie.")
        elif top_stack.has_accumulation:
            lines.append("La scene contient une accumulation multi-TF: le bassin travaille encore.")
        else:
            lines.append("La scene est active mais pas encore mature: continuer le film.")
    else:
        lines.append("Aucun empilement fractal trouve. Elargir la fenetre, reduire min_sequence_score, ou logger plus d'historique.")

    return "\n".join(lines)


__all__ = [
    "FractalZoneStack",
    "build_fractal_zone_stacks",
    "build_fractal_stack_report",
    "filter_stackable_sequences",
]
