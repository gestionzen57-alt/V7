"""
PowerFlow V6 - pf_powerflow_zone_brief.py
Version: V0.1.2 temporal-window split
Mission: produire une vue Cockpit globale des batailles de zones.

Cette brique ne recalcule pas les forces.
Elle lit la table derivee zone_diagnostics, construite par:
  - pf_zone_dynamics.py
  - pf_zone_context_logger.py
  - run_zone_context_logger_history.py

Objectif:
  Transformer les diagnostics de zone en brief tactique:
    - batailles en preparation
    - fenetres de release
    - tensions portees par session
    - microfilms actifs

Doctrine:
  PowerFlow ne cherche pas une verite absolue.
  Il nomme les champs d'interet strategique temporel.
"""

from __future__ import annotations

import argparse
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


ACTIVE_STATES = {
    "PRE_EXTREME",
    "EARLY_EXTREME",
    "ACCUMULATING",
    "LEAKING",
    "RUPTURE",
    "DISORDER_FIELD",
}

RELEASE_STATES = {"LEAKING", "RUPTURE"}
BUILD_STATES = {"PRE_EXTREME", "EARLY_EXTREME", "ACCUMULATING"}

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

TF_WEIGHT = {
    1: 0.75,
    5: 1.00,
    15: 1.35,
    30: 1.55,
    60: 1.80,
    240: 2.20,
    1440: 2.60,
    10080: 3.00,
}

TF_ORDER = [1, 5, 15, 30, 60, 240, 1440, 10080]


def parse_dt(value: str) -> datetime:
    if value is None:
        return datetime.fromtimestamp(0, tz=timezone.utc)
    text = str(value)
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        # Last fallback for simple SQLite formats
        dt = datetime.strptime(text[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def fmt_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d %H:%M")


def fmt_duration(start: datetime, end: datetime) -> str:
    minutes = max(0, int((end - start).total_seconds() // 60))
    if minutes < 60:
        return f"{minutes}m"
    hours = minutes / 60.0
    if hours < 24:
        return f"{hours:.1f}h"
    return f"{hours / 24.0:.1f}d"


def tf_label(tf: int) -> str:
    return TF_LABELS.get(int(tf), str(tf))


def side_from_row(row: dict) -> str:
    side = row.get("z_extreme_dir") or "NONE"
    if side in ("HIGH", "LOW"):
        return side
    z = row.get("z_current")
    if z is None:
        return "NONE"
    try:
        return "HIGH" if float(z) >= 0 else "LOW"
    except Exception:
        return "NONE"


@dataclass
class ZoneRow:
    created_at: datetime
    symbol: str
    timeframe: int
    currency: str
    state: str
    zone_level: str
    z_current: float
    z_extreme_dir: str
    tension_score: float
    context_score: float
    profile_name: str = ""
    profile_horizon: str = ""
    session_phase: str = ""
    context_tags: str = ""
    note: str = ""

    @property
    def side(self) -> str:
        if self.z_extreme_dir in ("HIGH", "LOW"):
            return self.z_extreme_dir
        return "HIGH" if self.z_current >= 0 else "LOW"

    @property
    def tf_label(self) -> str:
        return tf_label(self.timeframe)


@dataclass
class ZoneBattle:
    currency: str
    side: str
    rows: List[ZoneRow] = field(default_factory=list)

    @property
    def start_at(self) -> datetime:
        return min(r.created_at for r in self.rows)

    @property
    def end_at(self) -> datetime:
        return max(r.created_at for r in self.rows)

    @property
    def duration_label(self) -> str:
        return fmt_duration(self.start_at, self.end_at)

    @property
    def timeframes(self) -> List[int]:
        return sorted({r.timeframe for r in self.rows}, key=lambda x: TF_ORDER.index(x) if x in TF_ORDER else 999)

    @property
    def tf_labels(self) -> str:
        return ",".join(tf_label(tf) for tf in self.timeframes)

    @property
    def states(self) -> List[str]:
        out = []
        for r in sorted(self.rows, key=lambda x: x.created_at):
            if not out or out[-1] != r.state:
                out.append(r.state)
        return out

    @property
    def path(self) -> str:
        return "->".join(self.states)

    @property
    def sessions(self) -> List[str]:
        out = []
        for r in sorted(self.rows, key=lambda x: x.created_at):
            s = r.session_phase or "-"
            if s != "-" and (not out or out[-1] != s):
                out.append(s)
        return out

    @property
    def session_path(self) -> str:
        return "->".join(self.sessions) if self.sessions else "-"

    @property
    def has_release(self) -> bool:
        return any(r.state in RELEASE_STATES for r in self.rows)

    @property
    def has_accumulation(self) -> bool:
        return any(r.state == "ACCUMULATING" for r in self.rows)

    @property
    def has_preparation(self) -> bool:
        return any(r.state in BUILD_STATES for r in self.rows)

    @property
    def latest_active(self) -> ZoneRow:
        active = [r for r in self.rows if r.state in ACTIVE_STATES]
        if active:
            return max(active, key=lambda x: x.created_at)
        return max(self.rows, key=lambda x: x.created_at)

    @property
    def latest_at(self) -> datetime:
        return self.latest_active.created_at

    @property
    def context_max(self) -> float:
        return max((r.context_score for r in self.rows), default=0.0)

    @property
    def tension_max(self) -> float:
        return max((r.tension_score for r in self.rows), default=0.0)

    @property
    def peak_abs_z(self) -> float:
        return max((abs(r.z_current) for r in self.rows), default=0.0)

    @property
    def anchor_tf(self) -> int:
        return max(self.timeframes, key=lambda tf: TF_WEIGHT.get(tf, 1.0))

    @property
    def trigger_tf(self) -> int:
        return min(self.timeframes, key=lambda tf: TF_WEIGHT.get(tf, 1.0))

    @property
    def score(self) -> float:
        # Score Cockpit: poids contexte + multi-TF + duree + session + release
        max_by_tf: Dict[int, float] = {}
        for r in self.rows:
            max_by_tf[r.timeframe] = max(max_by_tf.get(r.timeframe, 0.0), r.context_score)
        tf_score = sum(max_by_tf[tf] * TF_WEIGHT.get(tf, 1.0) for tf in max_by_tf)
        multi_tf_bonus = 1.0 + 0.18 * max(0, len(max_by_tf) - 1)
        release_bonus = 1.25 if self.has_release else 1.0
        accumulation_bonus = 1.12 if self.has_accumulation else 1.0
        session_bonus = 1.0 + 0.08 * max(0, len(set(self.sessions)) - 1)
        duration_hours = max(0.0, (self.end_at - self.start_at).total_seconds() / 3600.0)
        duration_bonus = min(1.30, 1.0 + duration_hours * 0.025)
        return round(tf_score * multi_tf_bonus * release_bonus * accumulation_bonus * session_bonus * duration_bonus, 3)

    @property
    def label(self) -> str:
        tfs = set(self.timeframes)
        if self.has_release and {15, 30, 60}.issubset(tfs):
            return "STRATEGIC_RELEASE_WINDOW"
        if self.has_release and len(tfs) >= 2:
            return "ZONE_RELEASE_WINDOW"
        if {15, 30, 60}.issubset(tfs):
            return "HTF_BATTLEFIELD_PREPARATION"
        if {15, 30}.issubset(tfs) or {30, 60}.issubset(tfs):
            return "SCENARIO_BATTLEFIELD"
        if {1, 5}.issubset(tfs):
            return "MICROFILM_BATTLEFIELD"
        if len(tfs) >= 2:
            return "FRACTAL_ZONE_INTEREST"
        if self.has_accumulation:
            return "LOCAL_ACCUMULATION_FIELD"
        if self.has_preparation:
            return "LOCAL_PREPARATION_FIELD"
        return "ZONE_FIELD"

    @property
    def cockpit_line(self) -> str:
        release_txt = "release" if self.has_release else "preparation"
        return (
            f"{self.currency} {self.side} - {self.label} | "
            f"TF={self.tf_labels} | {release_txt} | "
            f"score={self.score:.3f} | {self.duration_label} | "
            f"{self.session_path}"
        )

    @property
    def note(self) -> str:
        parts = []
        if len(self.timeframes) >= 3:
            parts.append("scene multi-TF")
        elif len(self.timeframes) == 2:
            parts.append("relais deux TF")
        else:
            parts.append("zone locale")
        if self.has_release:
            parts.append("fenetre de release ouverte ou deja active")
        elif self.has_accumulation:
            parts.append("accumulation sans release nette")
        elif self.has_preparation:
            parts.append("zone d'interet en preparation")
        if len(set(self.sessions)) >= 2:
            parts.append("tension portee entre sessions")
        if 1 in self.timeframes:
            parts.append("microfilm present")
        if self.anchor_tf >= 60:
            parts.append("HTF porteur")
        return "; ".join(parts) + "."


@dataclass
class ZoneBrief:
    symbol: str
    events_count: int
    battles: List[ZoneBattle]
    max_gap_minutes: Optional[int] = 90
    recent_minutes: Optional[int] = None
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def strategic(self) -> List[ZoneBattle]:
        return [b for b in self.battles if b.label in ("STRATEGIC_RELEASE_WINDOW", "HTF_BATTLEFIELD_PREPARATION")]

    @property
    def release_windows(self) -> List[ZoneBattle]:
        return [b for b in self.battles if b.has_release]

    @property
    def preparations(self) -> List[ZoneBattle]:
        return [b for b in self.battles if not b.has_release and b.has_preparation]

    @property
    def carried_tensions(self) -> List[ZoneBattle]:
        return [b for b in self.battles if len(set(b.sessions)) >= 2]

    @property
    def microfilms(self) -> List[ZoneBattle]:
        return [b for b in self.battles if 1 in b.timeframes or b.label == "MICROFILM_BATTLEFIELD"]

    def top(self, n: int = 10) -> List[ZoneBattle]:
        return sorted(self.battles, key=lambda b: b.score, reverse=True)[:n]


def _table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]


def _pick_time_column(cols: Sequence[str]) -> str:
    """
    Retourne la colonne temps disponible dans zone_diagnostics.

    Compatibilite:
      - V0.1 logger: source_created_at / logged_at
      - versions futures: created_at / snapshot_at / event_time / timestamp
    """
    candidates = (
        "created_at",
        "source_created_at",
        "snapshot_at",
        "event_time",
        "timestamp",
        "logged_at",
    )
    for name in candidates:
        if name in cols:
            return name
    raise RuntimeError(
        "zone_diagnostics missing a usable time column. "
        "Expected one of: created_at, source_created_at, snapshot_at, "
        "event_time, timestamp, logged_at"
    )


def load_zone_rows(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframes: Sequence[int] = (1, 5, 15, 30, 60),
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    limit_rows: Optional[int] = None,
) -> List[ZoneRow]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cols = set(_table_columns(conn, "zone_diagnostics"))
    time_col = _pick_time_column(cols)

    required = {"timeframe", "currency", "state"}
    missing = required - cols
    if missing:
        raise RuntimeError(f"zone_diagnostics missing required columns: {sorted(missing)}")

    where = ["symbol = ?"] if "symbol" in cols else []
    params: List[object] = [symbol] if "symbol" in cols else []

    if timeframes:
        placeholders = ",".join("?" for _ in timeframes)
        where.append(f"timeframe IN ({placeholders})")
        params.extend([int(tf) for tf in timeframes])

    if currencies:
        placeholders = ",".join("?" for _ in currencies)
        where.append(f"currency IN ({placeholders})")
        params.extend(list(currencies))

    if since:
        where.append(f"{time_col} >= ?")
        params.append(since)

    sql = "SELECT * FROM zone_diagnostics"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {time_col} ASC, id ASC"
    if limit_rows:
        sql += f" LIMIT {int(limit_rows)}"

    rows = []
    for r in conn.execute(sql, params).fetchall():
        d = dict(r)
        z = d.get("z_current")
        ctx = d.get("context_score")
        ten = d.get("tension_score")
        rows.append(ZoneRow(
            created_at=parse_dt(d.get(time_col)),
            symbol=d.get("symbol", symbol),
            timeframe=int(d.get("timeframe")),
            currency=str(d.get("currency")),
            state=str(d.get("state")),
            zone_level=str(d.get("zone_level", "")),
            z_current=float(z) if z is not None else 0.0,
            z_extreme_dir=str(d.get("z_extreme_dir", "")),
            tension_score=float(ten) if ten is not None else 0.0,
            context_score=float(ctx) if ctx is not None else 0.0,
            profile_name=str(d.get("profile_name", "")),
            profile_horizon=str(d.get("profile_horizon", "")),
            session_phase=str(d.get("session_phase", "")),
            context_tags=str(d.get("context_tags", d.get("context_tags_json", ""))),
            note=str(d.get("note", "")),
        ))
    conn.close()
    return rows


def _split_group_by_time_gap(
    group: Sequence[ZoneRow],
    max_gap_minutes: Optional[int],
) -> List[List[ZoneRow]]:
    """
    Decoupe une serie d'evenements d'une meme devise/direction
    en batailles temporelles distinctes.

    Pourquoi:
      Un brief Cockpit ne doit pas fusionner toute la journee en une mega-bataille.
      Si deux evenements sont trop eloignes, ils appartiennent a deux champs differents.

    Exemple:
      max_gap_minutes=90
      AUD LOW Asia/London reste separe de AUD LOW Late US.
    """
    ordered = sorted(group, key=lambda r: r.created_at)
    if not ordered:
        return []

    if max_gap_minutes is None or max_gap_minutes <= 0:
        return [ordered]

    max_gap = timedelta(minutes=int(max_gap_minutes))
    chunks: List[List[ZoneRow]] = []
    current: List[ZoneRow] = [ordered[0]]

    for row in ordered[1:]:
        gap = row.created_at - current[-1].created_at
        if gap > max_gap:
            chunks.append(current)
            current = [row]
        else:
            current.append(row)

    if current:
        chunks.append(current)

    return chunks


def build_battles(
    rows: Sequence[ZoneRow],
    only_active: bool = True,
    min_score: float = 3.0,
    recent_minutes: Optional[int] = None,
    max_gap_minutes: Optional[int] = 90,
) -> List[ZoneBattle]:
    if not rows:
        return []

    latest = max(r.created_at for r in rows)
    cutoff = latest - timedelta(minutes=recent_minutes) if recent_minutes else None

    grouped: Dict[Tuple[str, str], List[ZoneRow]] = {}
    for r in rows:
        if cutoff and r.created_at < cutoff:
            continue
        if only_active and r.state not in ACTIVE_STATES:
            continue
        side = r.side
        if side not in ("HIGH", "LOW"):
            continue
        grouped.setdefault((r.currency, side), []).append(r)

    battles = []
    for (currency, side), group in grouped.items():
        for chunk in _split_group_by_time_gap(group, max_gap_minutes=max_gap_minutes):
            b = ZoneBattle(currency=currency, side=side, rows=chunk)
            if b.score >= min_score:
                battles.append(b)

    return sorted(battles, key=lambda b: b.score, reverse=True)


def build_zone_brief(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframes: Sequence[int] = (1, 5, 15, 30, 60),
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    recent_minutes: Optional[int] = None,
    min_score: float = 3.0,
    max_gap_minutes: Optional[int] = 90,
) -> ZoneBrief:
    rows = load_zone_rows(
        db_path=db_path,
        symbol=symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=since,
    )
    battles = build_battles(
        rows,
        only_active=True,
        min_score=min_score,
        recent_minutes=recent_minutes,
        max_gap_minutes=max_gap_minutes,
    )
    return ZoneBrief(
        symbol=symbol,
        events_count=len(rows),
        battles=battles,
        max_gap_minutes=max_gap_minutes,
        recent_minutes=recent_minutes,
    )


def render_zone_brief(brief: ZoneBrief, top: int = 10) -> str:
    lines: List[str] = []
    lines.append("PowerFlow Zone Brief - COCKPIT FIELD")
    lines.append("=" * 92)
    mode = "recent" if brief.recent_minutes else "history"
    gap_label = f"{brief.max_gap_minutes}m" if brief.max_gap_minutes else "OFF"
    recent_label = f"{brief.recent_minutes}m" if brief.recent_minutes else "ALL"
    lines.append(f"Symbol: {brief.symbol} | Events: {brief.events_count} | Battles: {len(brief.battles)}")
    lines.append(f"Mode: {mode} | recent={recent_label} | max_gap={gap_label}")
    lines.append(f"Generated UTC: {fmt_dt(brief.generated_at)}")
    lines.append("")

    top_battles = brief.top(top)
    lines.append(f"Top {min(top, len(top_battles))} strategic temporal battlefields:")
    lines.append("-" * 92)
    if not top_battles:
        lines.append("No active zone battle found.")
    for i, b in enumerate(top_battles, 1):
        lines.append(f"{i:02d}. {b.cockpit_line}")
        lines.append(
            f"    anchor={tf_label(b.anchor_tf)} trigger={tf_label(b.trigger_tf)} "
            f"ctx_max={b.context_max:.3f} tension_max={b.tension_max:.3f} "
            f"peak_abs_z={b.peak_abs_z:.3f}"
        )
        lines.append(f"    path={b.path} | note={b.note}")

    def section(title: str, items: Sequence[ZoneBattle], limit: int = 6) -> None:
        lines.append("")
        lines.append(f"{title} ({min(len(items), limit)} shown):")
        lines.append("-" * 92)
        if not items:
            lines.append("-")
            return
        for i, b in enumerate(sorted(items, key=lambda x: x.score, reverse=True)[:limit], 1):
            lines.append(
                f"{i:02d}. {b.currency} {b.side:<4} {b.label:<30} "
                f"score={b.score:<8.3f} TF={b.tf_labels:<15} {b.session_path}"
            )

    section("Release windows", brief.release_windows, 8)
    section("Battles in preparation", brief.preparations, 8)
    section("Session-carried tensions", brief.carried_tensions, 8)
    section("Microfilm fields", brief.microfilms, 8)

    lines.append("")
    lines.append("Cockpit synthesis:")
    lines.append("-" * 92)
    if top_battles:
        dominant = top_battles[0]
        lines.append(f"Dominant field: {dominant.cockpit_line}")
        lines.append(f"{dominant.note}")
        if dominant.has_release:
            lines.append("Temporal window: release / rupture field already visible.")
        elif dominant.has_accumulation:
            lines.append("Temporal window: preparation with accumulation, watch for release alignment.")
        else:
            lines.append("Temporal window: interest zone, not mature yet.")
    else:
        lines.append("No dominant active field.")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Zone Brief - Cockpit field")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15,30,60")
    parser.add_argument("--currencies", default="")
    parser.add_argument("--since", default="")
    parser.add_argument("--recent-minutes", type=int, default=0)
    parser.add_argument("--max-gap-minutes", type=int, default=90,
                        help="Split battles when same currency/side events are separated by more than this gap. Use 0 to disable.")
    parser.add_argument("--min-score", type=float, default=3.0)
    parser.add_argument("--top", type=int, default=10)
    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    timeframes = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]
    currencies = [x.strip().upper() for x in args.currencies.split(",") if x.strip()] or None
    brief = build_zone_brief(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=args.since or None,
        recent_minutes=args.recent_minutes or None,
        min_score=args.min_score,
        max_gap_minutes=args.max_gap_minutes or None,
    )
    report = render_zone_brief(brief, top=args.top)
    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nOK wrote brief: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
