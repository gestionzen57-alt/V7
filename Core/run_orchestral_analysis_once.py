#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — run_orchestral_analysis_once.py

Runner combining:
    pf_force_inflection.py  → pliures contresens
    pf_force_extrema.py     → valleys / peaks
    pf_orchestral_gravity.py → leader/follower/croisements

Usage:
    python run_orchestral_analysis_once.py --db powerflow.db --symbol GBPUSD \
        --start "2026-05-06T05:00:00+00:00" --end "2026-05-06T21:00:00+00:00" \
        --tfs 15,60 --out output/orchestral_analysis.md

    # JSON mode:
    python run_orchestral_analysis_once.py --db powerflow.db --symbol GBPUSD \
        --start "2026-05-06T07:00:00+00:00" --end "2026-05-06T12:00:00+00:00" \
        --json --out output/orchestral_analysis.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from pf_force_inflection import detect_inflections_multi_tf, inflection_summary
from pf_force_extrema import detect_extrema_multi_tf, extrema_summary
from pf_orchestral_gravity_v02 import (
    compute_orchestra_multi_tf,
    orchestra_markdown_report,
)


def parse_tfs(value: str):
    return [int(x.strip()) for x in value.split(",") if x.strip()]


TF_LABELS = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4"}


def make_markdown_report(
    db: str, symbol: str, start: str, end: str, tfs: list
) -> str:
    lines = ["# POWERFLOW ORCHESTRAL ANALYSIS"]
    lines += [
        "",
        f"**Symbol:** {symbol}",
        f"**Window:** {start} → {end}",
        f"**Timeframes:** {', '.join(TF_LABELS.get(tf, str(tf)) for tf in tfs)}",
        "",
        "---",
        "",
    ]

    # ORCHESTRAL GRAVITY
    states = compute_orchestra_multi_tf(db, symbol, tfs, start, end, avg_bars=3)
    lines.append(orchestra_markdown_report(states, symbol, start, end))

    lines += ["---", "", "## PLIURES / INFLECTIONS", ""]

    inflections = detect_inflections_multi_tf(
        db, symbol, tfs, start, end, contresens_only=True
    )
    for tf in tfs:
        label = TF_LABELS.get(tf, f"TF{tf}")
        events = inflections.get(tf, [])
        summary = inflection_summary(events)
        lines.append(f"### {label} — {summary['count']} inflections ({summary['brutal_plus']} brutal+)")
        lines.append("")

        if not events:
            lines.append("*No contresens inflections.*")
            lines.append("")
            continue

        lines.append("| Time | Currency | Type | Before | After | Δ | Severity |")
        lines.append("|---|---|---|---:|---:|---:|---|")
        for e in events:
            lines.append(
                f"| {e.timestamp[-14:-6]} | {e.currency} | {e.pliure_type} "
                f"| {e.angle_before:+.1f}° | {e.angle_after:+.1f}° "
                f"| {e.delta:+.1f}° | {e.severity} |"
            )
        lines.append("")

    lines += ["---", "", "## VALLEYS / PEAKS", ""]

    extrema = detect_extrema_multi_tf(db, symbol, tfs, start, end)
    for tf in tfs:
        label = TF_LABELS.get(tf, f"TF{tf}")
        events = extrema.get(tf, [])
        summary = extrema_summary(events)
        lines.append(
            f"### {label} — {summary['valleys']} valleys, {summary['peaks']} peaks "
            f"({summary['slow_entry_fast_exit']} SLOW_ENTRY_FAST_EXIT)"
        )
        lines.append("")

        if not events:
            lines.append("*No significant extrema.*")
            lines.append("")
            continue

        lines.append("| Time | Currency | Type | Force | Amplitude | Entry vel | Exit vel | Asymmetry |")
        lines.append("|---|---|---|---:|---:|---:|---:|---|")
        for e in events:
            lines.append(
                f"| {e.timestamp[-14:-6]} | {e.currency} | {e.extrema_type} "
                f"| {e.force_value:.1f} | {e.amplitude:.1f} "
                f"| {e.entry_velocity:.2f} | {e.exit_velocity:.2f} "
                f"| {e.asymmetry} |"
            )
        lines.append("")

    return "\n".join(lines)


def make_json_output(
    db: str, symbol: str, start: str, end: str, tfs: list
) -> dict:
    states = compute_orchestra_multi_tf(db, symbol, tfs, start, end, avg_bars=3)
    inflections = detect_inflections_multi_tf(
        db, symbol, tfs, start, end, contresens_only=True
    )
    extrema = detect_extrema_multi_tf(db, symbol, tfs, start, end)

    return {
        "symbol": symbol,
        "start": start,
        "end": end,
        "timeframes": tfs,
        "orchestral_gravity": {
            str(tf): state.to_dict() if state else None
            for tf, state in states.items()
        },
        "inflections": {
            str(tf): {
                "summary": inflection_summary(evts),
                "events": [e.to_dict() for e in evts],
            }
            for tf, evts in inflections.items()
        },
        "extrema": {
            str(tf): {
                "summary": extrema_summary(evts),
                "events": [e.to_dict() for e in evts],
            }
            for tf, evts in extrema.items()
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--start", required=True)
    ap.add_argument("--end", required=True)
    ap.add_argument("--tfs", default="15,60")
    ap.add_argument("--out", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if not Path(args.db).exists():
        raise SystemExit(f"DB not found: {args.db}")

    tfs = parse_tfs(args.tfs)

    if args.json:
        result = make_json_output(args.db, args.symbol, args.start, args.end, tfs)
        output = json.dumps(result, ensure_ascii=False, indent=2)
    else:
        output = make_markdown_report(args.db, args.symbol, args.start, args.end, tfs)

    if args.out:
        Path(args.out).write_text(output, encoding="utf-8")
        print(f"✅ Orchestral analysis written: {args.out}")
    else:
        print(output)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
