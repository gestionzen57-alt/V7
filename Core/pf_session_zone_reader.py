"""
PowerFlow V6 - pf_session_zone_reader.py
Version: V0.1

Mission:
    Lire les scenes fractales deja detectees et raconter la dimension session + temps.

Doctrine:
    - Ne recalcule pas les Z-scores.
    - Ne modifie pas la DB.
    - Ne remplace pas pf_zone_dynamics.py, pf_zone_evolution_reader.py, ni pf_fractal_zone_stack.py.
    - Transforme un FRACTAL_ZONE_STACK en histoire temporelle :
        Asia seed -> London forge -> US release -> Late US microfilm.

Entree:
    powerflow.db avec table zone_diagnostics.
    pf_zone_evolution_reader.py et pf_fractal_zone_stack.py dans le meme dossier.

Sortie:
    structures Python + rapport texte lisible pour Cockpit/Lab.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

from pf_zone_evolution_reader import (
    ZoneEvent,
    build_zone_sequences,
    fetch_zone_events,
    fmt_duration,
    fmt_ts,
    tf_label,
)
from pf_fractal_zone_stack import (
    FractalZoneStack,
    build_fractal_zone_stacks,
)


SESSION_ORDER = ["ASIA", "LONDON_OPEN", "LONDON", "US", "LATE_US", "UNKNOWN"]
SESSION_RANK = {name: idx for idx, name in enumerate(SESSION_ORDER)}

RELEASE_STATES = {"LEAKING", "RUPTURE", "POST_ZONE"}
ACCUMULATION_STATES = {"EARLY_EXTREME", "ACCUMULATING", "PRE_EXTREME"}
STRONG_STATES = {"EARLY_EXTREME", "ACCUMULATING", "LEAKING", "RUPTURE", "POST_ZONE"}


def _session_rank(name: str) -> int:
    return SESSION_RANK.get((name or "UNKNOWN").upper(), len(SESSION_ORDER))


def _event_score(event: ZoneEvent) -> float:
    return max(float(event.context_score or 0.0), float(event.tension_score or 0.0))


def _ordered_events(stack: FractalZoneStack) -> List[ZoneEvent]:
    events: List[ZoneEvent] = []
    for seq in stack.sequences:
        events.extend(seq.events)
    events.sort(key=lambda e: (e.source_created_at, e.timeframe, e.currency))
    return events


def _unique_preserve(values: Sequence[str]) -> List[str]:
    out: List[str] = []
    for value in values:
        value = (value or "UNKNOWN").upper()
        if value not in out:
            out.append(value)
    return out


def _session_path_from_events(events: Sequence[ZoneEvent]) -> List[str]:
    return _unique_preserve([e.session_phase or "UNKNOWN" for e in events])


def _session_counts(events: Sequence[ZoneEvent]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for event in events:
        session = (event.session_phase or "UNKNOWN").upper()
        counts[session] = counts.get(session, 0) + 1
    return counts


def _session_max_scores(events: Sequence[ZoneEvent]) -> Dict[str, float]:
    scores: Dict[str, float] = {}
    for event in events:
        session = (event.session_phase or "UNKNOWN").upper()
        scores[session] = max(scores.get(session, 0.0), _event_score(event))
    return scores


def _first_session(events: Sequence[ZoneEvent]) -> str:
    for event in events:
        return (event.session_phase or "UNKNOWN").upper()
    return "UNKNOWN"


def _last_session(events: Sequence[ZoneEvent]) -> str:
    for event in reversed(events):
        return (event.session_phase or "UNKNOWN").upper()
    return "UNKNOWN"


def _peak_session(events: Sequence[ZoneEvent]) -> str:
    if not events:
        return "UNKNOWN"
    best = max(events, key=_event_score)
    return (best.session_phase or "UNKNOWN").upper()


def _first_release_session(events: Sequence[ZoneEvent]) -> Optional[str]:
    for event in events:
        if event.state in RELEASE_STATES:
            return (event.session_phase or "UNKNOWN").upper()
    return None


def _has_state(events: Sequence[ZoneEvent], states: set[str]) -> bool:
    return any(event.state in states for event in events)


def _compact_session_timeline(events: Sequence[ZoneEvent]) -> List[str]:
    counts = _session_counts(events)
    scores = _session_max_scores(events)
    sessions = sorted(counts, key=_session_rank)
    return [f"{s}:{counts[s]}e/{scores.get(s, 0.0):.1f}" for s in sessions]


@dataclass(frozen=True)
class SessionZoneStory:
    stack: FractalZoneStack
    events: Tuple[ZoneEvent, ...] = field(default_factory=tuple)

    @property
    def symbol(self) -> str:
        return self.stack.symbol

    @property
    def currency(self) -> str:
        return self.stack.currency

    @property
    def side(self) -> str:
        return self.stack.side

    @property
    def timeframes(self) -> List[str]:
        return self.stack.timeframe_labels

    @property
    def start_at(self) -> str:
        return self.stack.start_at

    @property
    def end_at(self) -> str:
        return self.stack.end_at

    @property
    def duration_minutes(self) -> float:
        return self.stack.duration_minutes

    @property
    def session_path(self) -> List[str]:
        return _session_path_from_events(self.events)

    @property
    def origin_session(self) -> str:
        return _first_session(self.events)

    @property
    def terminal_session(self) -> str:
        return _last_session(self.events)

    @property
    def peak_session(self) -> str:
        return _peak_session(self.events)

    @property
    def release_session(self) -> Optional[str]:
        return _first_release_session(self.events)

    @property
    def has_release(self) -> bool:
        return self.release_session is not None

    @property
    def has_accumulation(self) -> bool:
        return _has_state(self.events, {"ACCUMULATING"})

    @property
    def has_late_us_microfilm(self) -> bool:
        return "LATE_US" in self.session_path and self.stack.has_m1

    @property
    def has_session_handoff(self) -> bool:
        return len(self.session_path) >= 2

    @property
    def is_full_day_carry(self) -> bool:
        path = set(self.session_path)
        return ("ASIA" in path and ("US" in path or "LATE_US" in path)) or self.duration_minutes >= 8 * 60

    @property
    def session_timeline(self) -> List[str]:
        return _compact_session_timeline(self.events)

    @property
    def tags(self) -> List[str]:
        tags: List[str] = ["SESSION_ZONE_STORY"]
        path = set(self.session_path)

        if self.origin_session == "ASIA":
            tags.append("ASIA_SEED")
        if "LONDON_OPEN" in path:
            tags.append("LONDON_OPEN_FORGE")
        if "LONDON" in path:
            tags.append("LONDON_FORGE")
        if self.has_session_handoff:
            tags.append("SESSION_HANDOFF")
        if self.is_full_day_carry:
            tags.append("FULL_DAY_CARRY")
        if self.has_accumulation:
            tags.append("SESSION_CARRIED_TENSION")
        if self.has_release:
            tags.append("SESSION_RELEASE")
            if self.release_session == "US":
                tags.append("US_RELEASE")
            elif self.release_session == "LATE_US":
                tags.append("LATE_US_RELEASE")
            elif self.release_session in ("LONDON_OPEN", "LONDON"):
                tags.append("LONDON_RELEASE")
        if self.has_late_us_microfilm:
            tags.append("LATE_US_MICROFILM")
        if self.stack.has_htf_anchor:
            tags.append("HTF_SESSION_ANCHOR")
        if "ZONE_RELEASE_ALIGNMENT" in self.stack.tags:
            tags.append("ZONE_RELEASE_ALIGNMENT")
        if "TF_CASCADE_BUILD" in self.stack.tags:
            tags.append("TF_CASCADE_BUILD")
        if "DENSE_TEMPORAL_OVERLAP" in self.stack.tags:
            tags.append("DENSE_SESSION_OVERLAP")

        return tags

    @property
    def story_label(self) -> str:
        tagset = set(self.tags)
        if "ASIA_SEED" in tagset and "SESSION_RELEASE" in tagset:
            return "ASIA_SEEDED_SESSION_RELEASE"
        if "FULL_DAY_CARRY" in tagset and "SESSION_RELEASE" in tagset:
            return "FULL_DAY_CARRIED_RELEASE"
        if "LONDON_OPEN_FORGE" in tagset and "US_RELEASE" in tagset:
            return "LONDON_FORGE_US_RELEASE"
        if "LONDON_FORGE" in tagset and "US_RELEASE" in tagset:
            return "LONDON_TO_US_RELEASE"
        if "LATE_US_MICROFILM" in tagset and "SESSION_RELEASE" in tagset:
            return "LATE_US_MICROFILM_RELEASE"
        if "SESSION_CARRIED_TENSION" in tagset and "HTF_SESSION_ANCHOR" in tagset:
            return "HTF_SESSION_CARRIED_TENSION"
        if "SESSION_CARRIED_TENSION" in tagset:
            return "SESSION_CARRIED_TENSION"
        if "LATE_US_MICROFILM" in tagset:
            return "LATE_US_MICROFILM_FIELD"
        return "SESSION_ZONE_FIELD"

    @property
    def session_score(self) -> float:
        path_count = len(self.session_path)
        handoff_bonus = max(0, path_count - 1) * 1.8
        duration_bonus = math.log1p(max(1.0, self.duration_minutes)) * 1.15
        release_bonus = 5.0 if self.has_release else 0.0
        accumulation_bonus = 2.4 if self.has_accumulation else 0.0
        asia_bonus = 2.2 if self.origin_session == "ASIA" else 0.0
        full_day_bonus = 3.2 if self.is_full_day_carry else 0.0
        htf_bonus = 2.2 if self.stack.has_htf_anchor else 0.0
        micro_penalty = 0.88 if self.stack.has_m1 and len(self.stack.timeframes) <= 2 else 1.0
        score = (
            self.stack.stack_score
            + handoff_bonus
            + duration_bonus
            + release_bonus
            + accumulation_bonus
            + asia_bonus
            + full_day_bonus
            + htf_bonus
        ) * micro_penalty
        return round(score, 3)

    @property
    def narrative(self) -> str:
        origin = self.origin_session
        peak = self.peak_session
        release = self.release_session or "NO_RELEASE"
        path = " -> ".join(self.session_path)
        if self.has_release:
            return f"{origin} pose/porte, {peak} concentre, {release} libere. Session path: {path}."
        if self.has_accumulation:
            return f"{origin} pose/porte, {peak} concentre, pas de release nette. Session path: {path}."
        return f"Champ actif faible, path session: {path}."

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "currency": self.currency,
            "side": self.side,
            "story_label": self.story_label,
            "session_score": self.session_score,
            "timeframes": self.timeframes,
            "start_at": self.start_at,
            "end_at": self.end_at,
            "duration_minutes": round(self.duration_minutes, 2),
            "origin_session": self.origin_session,
            "peak_session": self.peak_session,
            "release_session": self.release_session,
            "terminal_session": self.terminal_session,
            "session_path": self.session_path,
            "session_timeline": self.session_timeline,
            "tags": self.tags,
            "stack_label": self.stack.tactical_label,
            "stack_score": self.stack.stack_score,
            "anchor_tf": tf_label(self.stack.anchor_sequence.timeframe),
            "trigger_tf": tf_label(self.stack.trigger_sequence.timeframe),
            "scenario_tf": tf_label(self.stack.scenario_sequence.timeframe),
            "narrative": self.narrative,
        }


def build_session_zone_stories(
    stacks: Sequence[FractalZoneStack],
    min_stack_score: float = 5.0,
) -> List[SessionZoneStory]:
    stories: List[SessionZoneStory] = []
    for stack in stacks:
        if stack.stack_score < min_stack_score:
            continue
        events = tuple(_ordered_events(stack))
        if not events:
            continue
        stories.append(SessionZoneStory(stack=stack, events=events))
    stories.sort(key=lambda story: story.session_score, reverse=True)
    return stories


def build_session_zone_report(
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
    min_stack_score: float = 5.0,
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
    stories = build_session_zone_stories(stacks, min_stack_score=min_stack_score)

    lines: List[str] = []
    lines.append("PowerFlow Session Zone Report - HISTOIRE TEMPORELLE")
    lines.append("=" * 96)
    lines.append(
        f"Events: {len(events)} | Local sequences: {len(sequences)} | Fractal stacks: {len(stacks)} | Session stories: {len(stories)}"
    )
    if symbol:
        lines.append(f"Symbol: {symbol}")
    if timeframes:
        lines.append("Timeframes: " + ", ".join(tf_label(x) for x in timeframes))
    if currencies:
        lines.append("Currencies: " + ", ".join(currencies))
    lines.append(
        f"Max temporal gap: {max_gap_minutes:.0f}m | Min sequence score: {min_sequence_score:.1f} | Min stack score: {min_stack_score:.1f}"
    )

    lines.append("")
    lines.append(f"Top {min(top, len(stories))} session zone stories:")
    lines.append("-" * 96)
    for idx, story in enumerate(stories[:top], start=1):
        release = story.release_session or "-"
        lines.append(
            f"{idx:02d}. {story.currency:<3} {story.side:<4} {story.story_label:<30} "
            f"score={story.session_score:<7.3f} stack={story.stack.stack_score:<7.3f} "
            f"tfs={','.join(story.timeframes):<18} dur={fmt_duration(story.duration_minutes):<6} "
            f"{fmt_ts(story.start_at)} -> {fmt_ts(story.end_at)}"
        )
        lines.append(
            f"    origin={story.origin_session:<12} peak={story.peak_session:<12} release={release:<12} "
            f"terminal={story.terminal_session:<12} anchor={tf_label(story.stack.anchor_sequence.timeframe)} "
            f"trigger={tf_label(story.stack.trigger_sequence.timeframe)} scenario={tf_label(story.stack.scenario_sequence.timeframe)}"
        )
        lines.append(
            f"    sessions={'->'.join(story.session_path)} | timeline={','.join(story.session_timeline)}"
        )
        lines.append(
            f"    stack={story.stack.tactical_label} | tags={','.join(story.tags)}"
        )
        lines.append(f"    note={story.narrative}")

    carried = [s for s in stories if "SESSION_CARRIED_TENSION" in s.tags]
    releases = [s for s in stories if "SESSION_RELEASE" in s.tags]
    asia = [s for s in stories if "ASIA_SEED" in s.tags]
    london_forge = [s for s in stories if "LONDON_OPEN_FORGE" in s.tags or "LONDON_FORGE" in s.tags]
    late_micro = [s for s in stories if "LATE_US_MICROFILM" in s.tags]

    lines.append("")
    lines.append(f"Session carried tension ({min(10, len(carried))} shown):")
    lines.append("-" * 96)
    for idx, story in enumerate(carried[:10], start=1):
        lines.append(
            f"{idx:02d}. {story.currency:<3} {story.side:<4} {story.story_label:<30} "
            f"score={story.session_score:<7.3f} path={'->'.join(story.session_path):<30} "
            f"tfs={','.join(story.timeframes):<16}"
        )

    lines.append("")
    lines.append(f"Session releases ({min(10, len(releases))} shown):")
    lines.append("-" * 96)
    for idx, story in enumerate(releases[:10], start=1):
        lines.append(
            f"{idx:02d}. {story.currency:<3} {story.side:<4} release={story.release_session:<12} "
            f"origin={story.origin_session:<12} peak={story.peak_session:<12} "
            f"score={story.session_score:<7.3f} {story.stack.tactical_label}"
        )

    lines.append("")
    lines.append(f"Asia seeds ({min(10, len(asia))} shown):")
    lines.append("-" * 96)
    for idx, story in enumerate(asia[:10], start=1):
        release = story.release_session or "-"
        lines.append(
            f"{idx:02d}. {story.currency:<3} {story.side:<4} release={release:<12} "
            f"path={'->'.join(story.session_path):<34} score={story.session_score:<7.3f}"
        )

    lines.append("")
    lines.append(f"London forge fields ({min(10, len(london_forge))} shown):")
    lines.append("-" * 96)
    for idx, story in enumerate(london_forge[:10], start=1):
        release = story.release_session or "-"
        lines.append(
            f"{idx:02d}. {story.currency:<3} {story.side:<4} release={release:<12} "
            f"peak={story.peak_session:<12} score={story.session_score:<7.3f} "
            f"{story.story_label}"
        )

    lines.append("")
    lines.append(f"Late US microfilm fields ({min(10, len(late_micro))} shown):")
    lines.append("-" * 96)
    for idx, story in enumerate(late_micro[:10], start=1):
        lines.append(
            f"{idx:02d}. {story.currency:<3} {story.side:<4} {story.story_label:<30} "
            f"score={story.session_score:<7.3f} tfs={','.join(story.timeframes):<16} "
            f"{fmt_ts(story.start_at)} -> {fmt_ts(story.end_at)}"
        )

    lines.append("")
    lines.append("Lecture tactique:")
    lines.append("-" * 96)
    if stories:
        top_story = stories[0]
        lines.append(
            f"Histoire dominante: {top_story.currency} {top_story.side} {top_story.story_label}, "
            f"TF={','.join(top_story.timeframes)}, score={top_story.session_score:.3f}."
        )
        lines.append(
            f"Origine: {top_story.origin_session} | concentration: {top_story.peak_session} | "
            f"release: {top_story.release_session or 'aucune'} | terminal: {top_story.terminal_session}."
        )
        lines.append(top_story.narrative)
        if "ASIA_SEED" in top_story.tags:
            lines.append("La scene porte une memoire depuis Asia: tension de session transportee.")
        if "LONDON_OPEN_FORGE" in top_story.tags or "LONDON_FORGE" in top_story.tags:
            lines.append("London travaille la zone: forge de liquidite / champ de bataille.")
        if top_story.has_release:
            lines.append("La scene contient une liberation: l'energie a fui, rompu ou commence a se liberer.")
        else:
            lines.append("La scene reste portee: accumulation/context actif sans release nette dans cette fenetre.")
    else:
        lines.append("Aucune histoire de session trouvee. Logger plus d'historique ou reduire min_stack_score.")

    return "\n".join(lines)


__all__ = [
    "SessionZoneStory",
    "build_session_zone_stories",
    "build_session_zone_report",
]
