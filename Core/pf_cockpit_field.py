"""
PowerFlow V6 - pf_cockpit_field.py
Version: V0.2

Mission:
  Produire une sortie Cockpit ultra-courte a partir de la carte globale des batailles.

Cette brique lit pf_battlefield_map.py, condense le champ global, puis ajoute
le bloc TEMPORAL_PATTERNS via pf_temporal_patterns_cockpit.py.

Objectif:
  Afficher ce qui compte maintenant:
    - champ dominant
    - release visible
    - coalition HIGH / LOW
    - devises bipolaires
    - fenetre temporelle active
    - respiration / pullures / densite / angle
"""

from __future__ import annotations

import argparse
from typing import List, Optional, Sequence

from pf_battlefield_map import (
    build_battlefield_map,
    BattlefieldMap,
    BattlefieldCluster,
    ContestedWindow,
)
from pf_temporal_patterns_cockpit import build_temporal_patterns_cockpit


def _join(items: Sequence[str], limit: int = 6) -> str:
    clean = []
    for item in items:
        if item and item != "-" and item not in clean:
            clean.append(item)
    if not clean:
        return "-"
    if len(clean) <= limit:
        return "/".join(clean)
    return "/".join(clean[:limit]) + "+"


def _release_text(cluster: BattlefieldCluster) -> str:
    releases = [f"{b.currency} {b.side}" for b in cluster.release_battles]
    return _join(releases, limit=5)


def _prep_text(cluster: BattlefieldCluster) -> str:
    preps = [f"{b.currency} {b.side}" for b in cluster.preparation_battles]
    return _join(preps, limit=5)


def _field_side_line(cluster: BattlefieldCluster) -> str:
    high = _join(cluster.high_coalition, limit=6)
    low = _join(cluster.low_coalition, limit=6)
    release = _release_text(cluster)
    prep = _prep_text(cluster)

    if cluster.release_battles:
        return f"{cluster.label}: release={release} | prep={prep} | HIGH={high} | LOW={low}"
    return f"{cluster.label}: prep={prep} | HIGH={high} | LOW={low}"


def render_cockpit_field(bmap: BattlefieldMap, max_lines: int = 6) -> str:
    """
    Rend uniquement le bloc battlefield compact.

    Important:
      Le bloc TEMPORAL_PATTERNS est ajoute ensuite dans build_and_render_cockpit_field(),
      sinon le trim max_lines coupe les lignes temporelles.
    """
    lines: List[str] = []
    top_clusters = bmap.top_clusters
    contested = bmap.contested_windows

    lines.append("COCKPIT FIELD")
    lines.append("=" * 72)

    if not top_clusters:
        lines.append("FIELD_EMPTY - no active battlefield.")
        return "\n".join(lines)

    dominant = top_clusters[0]
    session = dominant.session_path
    lines.append(f"FIELD: {dominant.label} | session={session} | score={dominant.score:.3f}")
    lines.append(f"DOMINANT: {_field_side_line(dominant)}")

    # Add second cluster if it gives the opposite side or context.
    if len(top_clusters) > 1 and max_lines >= 4:
        second = top_clusters[1]
        lines.append(f"OPPOSITE/CONTEXT: {_field_side_line(second)}")

    if contested and max_lines >= 5:
        w = contested[0]
        high = _join(w.high_cluster.high_coalition, limit=6)
        low = _join(w.low_cluster.low_coalition, limit=6)
        lines.append(f"CONTESTED_WINDOW: HIGH={high} vs LOW={low} | {w.label}")

        if w.bipolar_fields:
            top_bipolar = w.bipolar_fields[0]
            lines.append(
                f"BIPOLAR_FOCUS: {top_bipolar.currency} | {top_bipolar.label} | "
                f"HIGH_TF={top_bipolar.high_tf_labels} vs LOW_TF={top_bipolar.low_tf_labels}"
            )

    # Add compact list of key bipolar fields if room remains.
    if contested and contested[0].bipolar_fields and max_lines >= 6:
        fields = contested[0].bipolar_fields[:4]
        compact = []
        for f in fields:
            high_mode = "REL" if f.high_release else "PREP"
            low_mode = "REL" if f.low_release else "PREP"
            compact.append(f"{f.currency}:{high_mode}H/{low_mode}L")
        lines.append(f"BIPOLAR_LIST: {' | '.join(compact)}")

    # Trim while preserving header.
    if max_lines and len(lines) > max_lines + 2:
        lines = lines[:max_lines + 2]

    return "\n".join(lines)


def build_and_render_cockpit_field(
    db_path: str,
    symbol: str = "GBPUSD",
    timeframes: Sequence[int] = (1, 5, 15, 30, 60),
    currencies: Optional[Sequence[str]] = None,
    since: Optional[str] = None,
    recent_minutes: Optional[int] = 180,
    min_score: float = 3.0,
    max_gap_minutes: Optional[int] = 90,
    cluster_gap_minutes: int = 60,
    cluster_mode: str = "side",
    max_lines: int = 6,
    temporal_window: int = 20,
    temporal_density_percentile: float = 85.0,
    temporal_min_breathing_energy: float = 3.0,
    temporal_angle_tolerance: float = 4.0,
    temporal_field_gap_minutes: int = 10,
) -> str:
    bmap = build_battlefield_map(
        db_path=db_path,
        symbol=symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=since,
        recent_minutes=recent_minutes,
        min_score=min_score,
        max_gap_minutes=max_gap_minutes,
        max_cluster_gap_minutes=cluster_gap_minutes,
        require_session_bridge=False,
        cluster_mode=cluster_mode,
    )

    report = render_cockpit_field(bmap, max_lines=max_lines)
    lines = report.splitlines()

    try:
        temporal = build_temporal_patterns_cockpit(
            db_path=db_path,
            symbol=symbol,
            timeframes=timeframes,
            currencies=currencies or ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD"),
            recent_minutes=recent_minutes or 0,
            window=temporal_window,
            density_percentile=temporal_density_percentile,
            min_breathing_energy=temporal_min_breathing_energy,
            angle_tolerance=temporal_angle_tolerance,
            field_gap_minutes=temporal_field_gap_minutes,
            max_lines=max_lines,
        )
        lines.append("")
        lines.extend(temporal.lines)
    except Exception as exc:
        lines.append("")
        lines.append(f"TEMPORAL_PATTERNS: ERROR {exc}")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow Cockpit Field")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5,15,30,60")
    parser.add_argument("--currencies", default="")
    parser.add_argument("--since", default="")
    parser.add_argument("--recent-minutes", type=int, default=180)
    parser.add_argument("--min-score", type=float, default=3.0)
    parser.add_argument("--max-gap-minutes", type=int, default=90)
    parser.add_argument("--cluster-gap-minutes", type=int, default=60)
    parser.add_argument("--cluster-mode", choices=["side", "mixed", "release"], default="side")
    parser.add_argument("--max-lines", type=int, default=6)

    # Temporal plug-in parameters.
    parser.add_argument("--temporal-window", type=int, default=20)
    parser.add_argument("--temporal-density-percentile", type=float, default=85.0)
    parser.add_argument("--temporal-min-breathing-energy", type=float, default=3.0)
    parser.add_argument("--temporal-angle-tolerance", type=float, default=4.0)
    parser.add_argument("--temporal-field-gap-minutes", type=int, default=10)

    parser.add_argument("--out", default="")
    args = parser.parse_args(argv)

    timeframes = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]
    currencies = [x.strip().upper() for x in args.currencies.split(",") if x.strip()] or None

    report = build_and_render_cockpit_field(
        db_path=args.db,
        symbol=args.symbol,
        timeframes=timeframes,
        currencies=currencies,
        since=args.since or None,
        recent_minutes=args.recent_minutes or None,
        min_score=args.min_score,
        max_gap_minutes=args.max_gap_minutes or None,
        cluster_gap_minutes=args.cluster_gap_minutes,
        cluster_mode=args.cluster_mode,
        max_lines=args.max_lines,
        temporal_window=args.temporal_window,
        temporal_density_percentile=args.temporal_density_percentile,
        temporal_min_breathing_energy=args.temporal_min_breathing_energy,
        temporal_angle_tolerance=args.temporal_angle_tolerance,
        temporal_field_gap_minutes=args.temporal_field_gap_minutes,
    )

    print(report)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nOK wrote cockpit field: {args.out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
