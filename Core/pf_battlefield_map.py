"""
PowerFlow V6 - pf_battlefield_map.py
Version: V0.1.2 bipolar currency fields

Mission:
  Construire une carte globale des batailles a partir des battlefields Cockpit.

Cette brique ne recalcule pas les forces.
Elle utilise pf_powerflow_zone_brief.py pour lire zone_diagnostics et produire les zones.
Puis elle groupe ces zones en champs globaux:

  - coalitions HIGH
  - coalitions LOW
  - release windows
  - preparations
  - contradictions
  - microfilm crowd
  - HTF anchors

Doctrine:
  PowerFlow ne cherche pas une verite absolue.
  Il nomme les champs de bataille, les oppositions et les fenetres temporelles.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

from pf_powerflow_zone_brief import (
    ZoneBattle,
    ZoneBrief,
    build_zone_brief,
    fmt_dt,
    fmt_duration,
    tf_label,
)


RELEASE_LABELS = {
    "STRATEGIC_RELEASE_WINDOW",
    "ZONE_RELEASE_WINDOW",
}

PREPARATION_LABELS = {
    "HTF_BATTLEFIELD_PREPARATION",
    "SCENARIO_BATTLEFIELD",
    "MICROFILM_BATTLEFIELD",
    "FRACTAL_ZONE_INTEREST",
    "LOCAL_ACCUMULATION_FIELD",
    "LOCAL_PREPARATION_FIELD",
}

HTF_TIMEFRAMES = {30, 60, 240, 1440, 10080}
MICRO_TIMEFRAMES = {1, 5}


def _overlap_or_gap(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime, max_gap: timedelta) -> bool:
    if b_start <= a_end and b_end >= a_start:
        return True
    if b_start > a_end and (b_start - a_end) <= max_gap:
        return True
    if a_start > b_end and (a_start - b_end) <= max_gap:
        return True
    return False


def _session_set(b: ZoneBattle) -> Set[str]:
    return {s for s in b.sessions if s and s != "-"}


def _has_session_bridge(a: "BattlefieldCluster", b: ZoneBattle) -> bool:
    if not a.sessions or not _session_set(b):
        return True
    return bool(a.sessions & _session_set(b))


@dataclass
class BattlefieldCluster:
    battles: List[ZoneBattle] = field(default_factory=list)

    @property
    def start_at(self) -> datetime:
        return min(b.start_at for b in self.battles)

    @property
    def end_at(self) -> datetime:
        return max(b.end_at for b in self.battles)

    @property
    def duration_label(self) -> str:
        return fmt_duration(self.start_at, self.end_at)

    @property
    def sessions(self) -> Set[str]:
        out: Set[str] = set()
        for b in self.battles:
            out |= _session_set(b)
        return out

    @property
    def session_path(self) -> str:
        ordered: List[str] = []
        seen: Set[str] = set()
        for b in sorted(self.battles, key=lambda x: x.start_at):
            for s in b.sessions:
                if s and s != "-" and s not in seen:
                    ordered.append(s)
                    seen.add(s)
        return "->".join(ordered) if ordered else "-"

    @property
    def currencies(self) -> Set[str]:
        return {b.currency for b in self.battles}

    @property
    def sides(self) -> Set[str]:
        return {b.side for b in self.battles}

    @property
    def timeframes(self) -> Set[int]:
        out: Set[int] = set()
        for b in self.battles:
            out |= set(b.timeframes)
        return out

    @property
    def tf_labels(self) -> str:
        order = [1, 5, 15, 30, 60, 240, 1440, 10080]
        tfs = sorted(self.timeframes, key=lambda x: order.index(x) if x in order else 999)
        return ",".join(tf_label(tf) for tf in tfs)

    @property
    def high_battles(self) -> List[ZoneBattle]:
        return sorted([b for b in self.battles if b.side == "HIGH"], key=lambda x: x.score, reverse=True)

    @property
    def low_battles(self) -> List[ZoneBattle]:
        return sorted([b for b in self.battles if b.side == "LOW"], key=lambda x: x.score, reverse=True)

    @property
    def release_battles(self) -> List[ZoneBattle]:
        return sorted([b for b in self.battles if b.has_release], key=lambda x: x.score, reverse=True)

    @property
    def preparation_battles(self) -> List[ZoneBattle]:
        return sorted([b for b in self.battles if not b.has_release], key=lambda x: x.score, reverse=True)

    @property
    def htf_battles(self) -> List[ZoneBattle]:
        return sorted([b for b in self.battles if set(b.timeframes) & HTF_TIMEFRAMES], key=lambda x: x.score, reverse=True)

    @property
    def micro_battles(self) -> List[ZoneBattle]:
        return sorted([b for b in self.battles if set(b.timeframes) & MICRO_TIMEFRAMES], key=lambda x: x.score, reverse=True)

    @property
    def high_coalition(self) -> List[str]:
        out: List[str] = []
        for b in self.high_battles:
            if b.currency not in out:
                out.append(b.currency)
        return out

    @property
    def low_coalition(self) -> List[str]:
        out: List[str] = []
        for b in self.low_battles:
            if b.currency not in out:
                out.append(b.currency)
        return out

    @property
    def contradiction_currencies(self) -> List[str]:
        high = {b.currency for b in self.high_battles}
        low = {b.currency for b in self.low_battles}
        return sorted(high & low)

    @property
    def score(self) -> float:
        if not self.battles:
            return 0.0
        base = sum(b.score for b in self.battles)
        # Avoid huge scores from many tiny fields, but still reward breadth.
        breadth_bonus = 1.0 + 0.08 * max(0, len(self.currencies) - 1)
        two_side_bonus = 1.18 if {"HIGH", "LOW"}.issubset(self.sides) else 1.0
        release_bonus = 1.22 if self.release_battles else 1.0
        htf_bonus = 1.15 if self.htf_battles else 1.0
        micro_bonus = 1.08 if self.micro_battles else 1.0
        contradiction_penalty = 0.92 if self.contradiction_currencies else 1.0
        return round(base * breadth_bonus * two_side_bonus * release_bonus * htf_bonus * micro_bonus * contradiction_penalty, 3)

    @property
    def tags(self) -> List[str]:
        tags: List[str] = ["BATTLEFIELD_MAP"]
        if {"HIGH", "LOW"}.issubset(self.sides):
            tags.append("DUAL_SIDE_FIELD")
        if len(self.high_battles) >= 2:
            tags.append("HIGH_COALITION")
        if len(self.low_battles) >= 2:
            tags.append("LOW_COALITION")
        if self.release_battles:
            tags.append("RELEASE_PRESENT")
        if len(self.release_battles) >= 2:
            tags.append("MULTI_RELEASE_FIELD")
        if self.preparation_battles:
            tags.append("PREPARATION_PRESENT")
        if self.htf_battles:
            tags.append("HTF_ANCHOR_PRESENT")
        if self.micro_battles:
            tags.append("MICROFILM_PRESENT")
        if len(self.micro_battles) >= 3:
            tags.append("MICROFILM_CROWD")
        if self.contradiction_currencies:
            tags.append("SAME_CURRENCY_CONTRADICTION")
        if len(self.sessions) >= 2:
            tags.append("SESSION_HANDOFF")
        return tags

    @property
    def label(self) -> str:
        has_release = bool(self.release_battles)
        has_htf = bool(self.htf_battles)
        has_micro = bool(self.micro_battles)
        dual = {"HIGH", "LOW"}.issubset(self.sides)

        if has_release and has_htf and dual:
            return "GLOBAL_RELEASE_BATTLEFIELD"
        if has_release and has_htf:
            return "HTF_RELEASE_BATTLEFIELD"
        if has_release and has_micro:
            return "TACTICAL_RELEASE_BATTLEFIELD"
        if has_release:
            return "RELEASE_BATTLEFIELD"
        if has_htf and dual:
            return "HTF_DUAL_PREPARATION_FIELD"
        if has_htf:
            return "HTF_PREPARATION_FIELD"
        if has_micro and len(self.micro_battles) >= 3:
            return "MICROFILM_CROWD_FIELD"
        if dual:
            return "DUAL_SIDE_PREPARATION_FIELD"
        return "LOCAL_BATTLEFIELD"

    @property
    def dominant_battle(self) -> Optional[ZoneBattle]:
        if not self.battles:
            return None
        return max(self.battles, key=lambda b: b.score)

    @property
    def note(self) -> str:
        parts: List[str] = []
        high = ",".join(self.high_coalition[:5]) or "-"
        low = ",".join(self.low_coalition[:5]) or "-"
        parts.append(f"HIGH={high}")
        parts.append(f"LOW={low}")
        if self.release_battles:
            rel = ", ".join(f"{b.currency} {b.side}" for b in self.release_battles[:4])
            parts.append(f"release={rel}")
        if self.preparation_battles:
            prep = ", ".join(f"{b.currency} {b.side}" for b in self.preparation_battles[:4])
            parts.append(f"prep={prep}")
        if self.contradiction_currencies:
            parts.append(f"contradiction={','.join(self.contradiction_currencies)}")
        return " | ".join(parts)

    @property
    def cockpit_line(self) -> str:
        return (
            f"{self.label} | score={self.score:.3f} | "
            f"{fmt_dt(self.start_at)} -> {fmt_dt(self.end_at)} ({self.duration_label}) | "
            f"TF={self.tf_labels} | sessions={self.session_path}"
        )


@dataclass
class BipolarCurrencyField:
    """
    Une meme devise apparait des deux cotes du champ:
      - HIGH sur un ensemble de TF
      - LOW sur un autre ensemble de TF

    Ce n'est pas une erreur.
    C'est une contestation interne / rotation potentielle.
    """
    currency: str
    high_battles: List[ZoneBattle] = field(default_factory=list)
    low_battles: List[ZoneBattle] = field(default_factory=list)

    @property
    def high_score(self) -> float:
        return round(sum(b.score for b in self.high_battles), 3)

    @property
    def low_score(self) -> float:
        return round(sum(b.score for b in self.low_battles), 3)

    @property
    def score(self) -> float:
        release_bonus = 1.18 if (self.high_release or self.low_release) else 1.0
        tf_bonus = 1.12 if (self.has_micro and self.has_htf) else 1.0
        return round((self.high_score + self.low_score) * release_bonus * tf_bonus, 3)

    @property
    def high_release(self) -> bool:
        return any(b.has_release for b in self.high_battles)

    @property
    def low_release(self) -> bool:
        return any(b.has_release for b in self.low_battles)

    @property
    def high_tfs(self) -> Set[int]:
        out: Set[int] = set()
        for b in self.high_battles:
            out |= set(b.timeframes)
        return out

    @property
    def low_tfs(self) -> Set[int]:
        out: Set[int] = set()
        for b in self.low_battles:
            out |= set(b.timeframes)
        return out

    @property
    def has_micro(self) -> bool:
        return bool((self.high_tfs | self.low_tfs) & MICRO_TIMEFRAMES)

    @property
    def has_htf(self) -> bool:
        return bool((self.high_tfs | self.low_tfs) & HTF_TIMEFRAMES)

    @property
    def high_tf_labels(self) -> str:
        order = [1, 5, 15, 30, 60, 240, 1440, 10080]
        return ",".join(tf_label(tf) for tf in sorted(self.high_tfs, key=lambda x: order.index(x) if x in order else 999)) or "-"

    @property
    def low_tf_labels(self) -> str:
        order = [1, 5, 15, 30, 60, 240, 1440, 10080]
        return ",".join(tf_label(tf) for tf in sorted(self.low_tfs, key=lambda x: order.index(x) if x in order else 999)) or "-"

    @property
    def micro_side(self) -> str:
        high_micro = bool(self.high_tfs & MICRO_TIMEFRAMES)
        low_micro = bool(self.low_tfs & MICRO_TIMEFRAMES)
        if high_micro and not low_micro:
            return "HIGH"
        if low_micro and not high_micro:
            return "LOW"
        if high_micro and low_micro:
            return "BOTH"
        return "-"

    @property
    def htf_side(self) -> str:
        high_htf = bool(self.high_tfs & HTF_TIMEFRAMES)
        low_htf = bool(self.low_tfs & HTF_TIMEFRAMES)
        if high_htf and not low_htf:
            return "HIGH"
        if low_htf and not high_htf:
            return "LOW"
        if high_htf and low_htf:
            return "BOTH"
        return "-"

    @property
    def label(self) -> str:
        if self.high_release and self.low_release:
            return "DOUBLE_SIDE_RELEASE_CONTEST"
        if self.high_release and self.htf_side == "LOW":
            return "HIGH_RELEASE_VS_LOW_HTF_PREP"
        if self.low_release and self.htf_side == "HIGH":
            return "LOW_RELEASE_VS_HIGH_HTF_PREP"
        if self.micro_side != "-" and self.htf_side != "-":
            return "MICRO_VS_HTF_ROTATION_CONTEST"
        return "BIPOLAR_CURRENCY_FIELD"

    @property
    def cockpit_line(self) -> str:
        high_mode = "release" if self.high_release else "prep"
        low_mode = "release" if self.low_release else "prep"
        return (
            f"{self.currency}: {self.label} | "
            f"HIGH {high_mode} TF={self.high_tf_labels} score={self.high_score:.3f} "
            f"vs LOW {low_mode} TF={self.low_tf_labels} score={self.low_score:.3f} | "
            f"micro={self.micro_side} htf={self.htf_side} total={self.score:.3f}"
        )


@dataclass
class ContestedWindow:
    high_cluster: BattlefieldCluster
    low_cluster: BattlefieldCluster

    @property
    def start_at(self) -> datetime:
        return min(self.high_cluster.start_at, self.low_cluster.start_at)

    @property
    def end_at(self) -> datetime:
        return max(self.high_cluster.end_at, self.low_cluster.end_at)

    @property
    def duration_label(self) -> str:
        return fmt_duration(self.start_at, self.end_at)

    @property
    def score(self) -> float:
        release_bonus = 1.15 if (self.high_cluster.release_battles or self.low_cluster.release_battles) else 1.0
        return round((self.high_cluster.score + self.low_cluster.score) * release_bonus, 3)

    @property
    def session_path(self) -> str:
        ordered: List[str] = []
        seen: Set[str] = set()
        for s in list(self.high_cluster.sessions) + list(self.low_cluster.sessions):
            if s and s != "-" and s not in seen:
                ordered.append(s)
                seen.add(s)
        return "->".join(ordered) if ordered else "-"

    @property
    def bipolar_fields(self) -> List[BipolarCurrencyField]:
        high_by_currency: Dict[str, List[ZoneBattle]] = {}
        low_by_currency: Dict[str, List[ZoneBattle]] = {}

        for battle in self.high_cluster.high_battles:
            high_by_currency.setdefault(battle.currency, []).append(battle)
        for battle in self.low_cluster.low_battles:
            low_by_currency.setdefault(battle.currency, []).append(battle)

        fields: List[BipolarCurrencyField] = []
        for currency in sorted(set(high_by_currency) & set(low_by_currency)):
            fields.append(BipolarCurrencyField(
                currency=currency,
                high_battles=high_by_currency.get(currency, []),
                low_battles=low_by_currency.get(currency, []),
            ))
        return sorted(fields, key=lambda f: f.score, reverse=True)

    @property
    def label(self) -> str:
        if self.bipolar_fields and (self.high_cluster.release_battles or self.low_cluster.release_battles):
            return "BIPOLAR_CONTESTED_RELEASE_WINDOW"
        if self.bipolar_fields:
            return "INTERNAL_ROTATION_CONTEST"
        if self.high_cluster.release_battles or self.low_cluster.release_battles:
            return "CONTESTED_RELEASE_WINDOW"
        return "CONTESTED_PREPARATION_FIELD"

    @property
    def cockpit_line(self) -> str:
        return (
            f"{self.label} | score={self.score:.3f} | "
            f"{fmt_dt(self.start_at)} -> {fmt_dt(self.end_at)} ({self.duration_label}) | "
            f"HIGH={','.join(self.high_cluster.high_coalition)} | "
            f"LOW={','.join(self.low_cluster.low_coalition)} | sessions={self.session_path}"
        )


def find_contested_windows(
    clusters: Sequence[BattlefieldCluster],
    max_gap_minutes: int = 60,
) -> List[ContestedWindow]:
    max_gap = timedelta(minutes=int(max_gap_minutes))
    high_clusters = [c for c in clusters if c.high_battles and not c.low_battles]
    low_clusters = [c for c in clusters if c.low_battles and not c.high_battles]
    windows: List[ContestedWindow] = []

    for high in high_clusters:
        for low in low_clusters:
            if _overlap_or_gap(high.start_at, high.end_at, low.start_at, low.end_at, max_gap):
                windows.append(ContestedWindow(high_cluster=high, low_cluster=low))

    # Deduplicate extremely similar pairs by currencies + rounded time bounds.
    seen: Set[Tuple[str, str, str, str]] = set()
    unique: List[ContestedWindow] = []
    for w in sorted(windows, key=lambda x: x.score, reverse=True):
        key = (
            ",".join(w.high_cluster.high_coalition),
            ",".join(w.low_cluster.low_coalition),
            fmt_dt(w.start_at),
            fmt_dt(w.end_at),
        )
        if key not in seen:
            unique.append(w)
            seen.add(key)
    return unique


@dataclass
class BattlefieldMap:
    symbol: str
    brief: ZoneBrief
    clusters: List[BattlefieldCluster]
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def top_clusters(self) -> List[BattlefieldCluster]:
        return sorted(self.clusters, key=lambda c: c.score, reverse=True)

    @property
    def release_clusters(self) -> List[BattlefieldCluster]:
        return [c for c in self.top_clusters if c.release_battles]

    @property
    def preparation_clusters(self) -> List[BattlefieldCluster]:
        return [c for c in self.top_clusters if not c.release_battles]

    @property
    def contradiction_clusters(self) -> List[BattlefieldCluster]:
        return [c for c in self.top_clusters if c.contradiction_currencies]

    @property
    def contested_windows(self) -> List[ContestedWindow]:
        return find_contested_windows(self.clusters, max_gap_minutes=60)


def cluster_battles(
    battles: Sequence[ZoneBattle],
    max_cluster_gap_minutes: int = 60,
    require_session_bridge: bool = False,
    cluster_mode: str = "side",
) -> List[BattlefieldCluster]:
    """
    Regroupe les ZoneBattle du brief en cartes globales.
    """
    ordered = sorted(battles, key=lambda b: (b.start_at, b.end_at))
    clusters: List[BattlefieldCluster] = []
    max_gap = timedelta(minutes=int(max_cluster_gap_minutes))

    for battle in ordered:
        added = False
        # Try to attach to the best overlapping / nearby cluster.
        candidates: List[Tuple[float, BattlefieldCluster]] = []
        for cluster in clusters:
            if cluster_mode == "side" and battle.side not in cluster.sides:
                continue
            if cluster_mode == "release" and bool(battle.has_release) != bool(cluster.release_battles):
                continue
            if not _overlap_or_gap(cluster.start_at, cluster.end_at, battle.start_at, battle.end_at, max_gap):
                continue
            if require_session_bridge and not _has_session_bridge(cluster, battle):
                continue
            # Prefer cluster with overlap and similar sessions.
            overlap_seconds = max(
                0.0,
                (min(cluster.end_at, battle.end_at) - max(cluster.start_at, battle.start_at)).total_seconds(),
            )
            session_bonus = 1.0 if (_session_set(battle) & cluster.sessions) else 0.0
            candidates.append((overlap_seconds + session_bonus, cluster))

        if candidates:
            candidates.sort(key=lambda x: x[0], reverse=True)
            candidates[0][1].battles.append(battle)
            added = True

        if not added:
            clusters.append(BattlefieldCluster(battles=[battle]))

    return sorted(clusters, key=lambda c: c.score, reverse=True)


def build_battlefield_map(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframes: Sequence[int] = (1, 5, 15, 30, 60),
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    recent_minutes: Optional[int] = 180,
    min_score: float = 3.0,
    max_gap_minutes: Optional[int] = 90,
    max_cluster_gap_minutes: int = 60,
    require_session_bridge: bool = False,
    cluster_mode: str = "side",
) -> BattlefieldMap:
    brief = build_zone_brief(
        db_path=db_path,
        symbol=symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=since,
        recent_minutes=recent_minutes,
        min_score=min_score,
        max_gap_minutes=max_gap_minutes,
    )
    clusters = cluster_battles(
        brief.battles,
        max_cluster_gap_minutes=max_cluster_gap_minutes,
        require_session_bridge=require_session_bridge,
        cluster_mode=cluster_mode,
    )
    return BattlefieldMap(symbol=symbol, brief=brief, clusters=clusters)


def render_battlefield_map(bmap: BattlefieldMap, top: int = 10) -> str:
    lines: List[str] = []
    lines.append("PowerFlow Battlefield Map - CARTE GLOBALE DES BATAILLES")
    lines.append("=" * 100)
    lines.append(
        f"Symbol: {bmap.symbol} | Events: {bmap.brief.events_count} | "
        f"Zone battles: {len(bmap.brief.battles)} | Battlefield clusters: {len(bmap.clusters)}"
    )
    lines.append(f"Generated UTC: {fmt_dt(bmap.generated_at)}")
    lines.append("")

    top_clusters = bmap.top_clusters[:top]
    lines.append(f"Top {len(top_clusters)} global battlefields:")
    lines.append("-" * 100)
    if not top_clusters:
        lines.append("No battlefield cluster found.")
    for i, c in enumerate(top_clusters, 1):
        lines.append(f"{i:02d}. {c.cockpit_line}")
        lines.append(f"    tags={','.join(c.tags)}")
        lines.append(f"    {c.note}")
        for b in sorted(c.battles, key=lambda x: x.score, reverse=True)[:6]:
            rel = "release" if b.has_release else "prep"
            lines.append(
                f"      - {b.currency} {b.side:<4} {b.label:<30} "
                f"{rel:<7} score={b.score:<8.3f} TF={b.tf_labels:<12} {b.session_path}"
            )

    contested = bmap.contested_windows
    lines.append("")
    lines.append(f"Contested windows ({min(len(contested), 6)} shown):")
    lines.append("-" * 100)
    if not contested:
        lines.append("-")
    else:
        for i, w in enumerate(contested[:6], 1):
            lines.append(f"{i:02d}. {w.cockpit_line}")
            high_releases = ", ".join(f"{b.currency} {b.side}" for b in w.high_cluster.release_battles[:3]) or "-"
            low_releases = ", ".join(f"{b.currency} {b.side}" for b in w.low_cluster.release_battles[:3]) or "-"
            lines.append(f"    high_release={high_releases} | low_release={low_releases}")
            if w.bipolar_fields:
                lines.append("    bipolar:")
                for field in w.bipolar_fields[:6]:
                    lines.append(f"      - {field.cockpit_line}")

    all_bipolar: List[BipolarCurrencyField] = []
    seen_bipolar: Set[Tuple[str, str, str]] = set()
    for window in contested:
        for field in window.bipolar_fields:
            key = (field.currency, field.high_tf_labels, field.low_tf_labels)
            if key not in seen_bipolar:
                all_bipolar.append(field)
                seen_bipolar.add(key)
    all_bipolar = sorted(all_bipolar, key=lambda f: f.score, reverse=True)

    lines.append("")
    lines.append(f"Bipolar currency fields ({min(len(all_bipolar), 8)} shown):")
    lines.append("-" * 100)
    if not all_bipolar:
        lines.append("-")
    else:
        for i, field in enumerate(all_bipolar[:8], 1):
            lines.append(f"{i:02d}. {field.cockpit_line}")

    def section(title: str, items: Sequence[BattlefieldCluster], limit: int = 6) -> None:
        lines.append("")
        lines.append(f"{title} ({min(len(items), limit)} shown):")
        lines.append("-" * 100)
        if not items:
            lines.append("-")
            return
        for i, c in enumerate(items[:limit], 1):
            dom = c.dominant_battle
            dom_txt = f"{dom.currency} {dom.side}" if dom else "-"
            lines.append(
                f"{i:02d}. {c.label:<32} score={c.score:<8.3f} "
                f"dominant={dom_txt:<8} TF={c.tf_labels:<16} {c.session_path}"
            )

    section("Release battlefields", bmap.release_clusters, 8)
    section("Preparation battlefields", bmap.preparation_clusters, 8)
    section("Contradiction / dual-side fields", bmap.contradiction_clusters, 8)

    lines.append("")
    lines.append("Cockpit synthesis:")
    lines.append("-" * 100)
    if top_clusters:
        c = top_clusters[0]
        lines.append(f"Dominant battlefield: {c.cockpit_line}")
        lines.append(c.note)
        if c.release_battles:
            lines.append("Window: release visible in the map.")
        elif c.preparation_battles:
            lines.append("Window: preparation field, watch for release alignment.")
        contested = bmap.contested_windows
        if contested:
            w = contested[0]
            lines.append(f"Contested window: HIGH={','.join(w.high_cluster.high_coalition)} vs LOW={','.join(w.low_cluster.low_coalition)}.")
            if w.bipolar_fields:
                top_bipolar = w.bipolar_fields[0]
                lines.append(f"Bipolar focus: {top_bipolar.cockpit_line}")
        if c.contradiction_currencies:
            lines.append(f"Internal contradiction: same currency on both sides inside one cluster: {','.join(c.contradiction_currencies)}.")
        if len(c.high_battles) >= 2:
            lines.append(f"HIGH coalition: {','.join(c.high_coalition[:6])}.")
        if len(c.low_battles) >= 2:
            lines.append(f"LOW coalition: {','.join(c.low_coalition[:6])}.")
    else:
        lines.append("No dominant battlefield.")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Battlefield Map")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15,30,60")
    parser.add_argument("--currencies", default="")
    parser.add_argument("--since", default="")
    parser.add_argument("--recent-minutes", type=int, default=180)
    parser.add_argument("--min-score", type=float, default=3.0)
    parser.add_argument("--max-gap-minutes", type=int, default=90,
                        help="Split same currency/side zone battles before map clustering.")
    parser.add_argument("--cluster-gap-minutes", type=int, default=60,
                        help="Cluster separate zone battles into a global battlefield when closer than this.")
    parser.add_argument("--cluster-mode", choices=["side", "mixed", "release"], default="side",
                        help="side=separate HIGH/LOW coalitions, mixed=old V0.1 behavior, release=separate release/prep.")
    parser.add_argument("--require-session-bridge", action="store_true")
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    timeframes = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]
    currencies = [x.strip().upper() for x in args.currencies.split(",") if x.strip()] or None

    bmap = build_battlefield_map(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=args.since or None,
        recent_minutes=args.recent_minutes or None,
        min_score=args.min_score,
        max_gap_minutes=args.max_gap_minutes or None,
        max_cluster_gap_minutes=args.cluster_gap_minutes,
        require_session_bridge=args.require_session_bridge,
        cluster_mode=args.cluster_mode,
    )
    report = render_battlefield_map(bmap, top=args.top)
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nOK wrote battlefield map: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
