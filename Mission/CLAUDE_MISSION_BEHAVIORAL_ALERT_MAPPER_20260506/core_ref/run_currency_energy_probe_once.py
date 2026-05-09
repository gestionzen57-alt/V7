#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 — run_currency_energy_probe_once.py

Runner read-only pour pf_currency_energy_probe.

Usage :
    python run_currency_energy_probe_once.py [options]

Options :
    --db          powerflow.db (défaut : powerflow.db)
    --symbol      GBPUSD (défaut : GBPUSD)
    --timeframe   TF principal en minutes (défaut : 15)
    --bars        Nombre de barres à charger (défaut : 50)
    --htf         TFs supérieurs séparés par virgule (défaut : 15,30,60)
    --out         Fichier de sortie JSON (défaut : output/currency_energy_state.json)
    --pretty      Indentation JSON lisible (défaut : activé)
    --no-pretty   JSON compact
    --summary     Affiche un résumé terminal après génération

Interdits :
    - Aucune écriture dans powerflow.db
    - Ne pas modifier capture_bridge.py
    - Pas de Telegram
    - Pas de signal directionnel

Exemple :
    python run_currency_energy_probe_once.py \\
        --db powerflow.db \\
        --symbol GBPUSD \\
        --timeframe 15 \\
        --bars 50 \\
        --htf 15,30,60 \\
        --out output/currency_energy_state.json \\
        --pretty \\
        --summary
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
#  HELPERS TERMINAL
# ═══════════════════════════════════════════════════════════════════════════════

_SEP = "─" * 72


def _print_sep() -> None:
    print(_SEP)


def _print_summary(state: dict) -> None:
    """Affiche un résumé lisible du currency_energy_state dans le terminal."""
    meta    = state.get("meta", {})
    capture = state.get("capture", {})
    top     = state.get("top_energy", {})
    ranking = state.get("ranking", [])
    summary = state.get("energy_field_summary", "")

    print()
    _print_sep()
    print("  PowerFlow V6 — Currency Energy State")
    _print_sep()
    print(f"  Symbol   : {meta.get('symbol', '?')}")
    print(f"  TF       : {meta.get('timeframe', '?')}  |  Bars : {meta.get('bars', '?')}")
    print(f"  HTF scan : {meta.get('htf_tfs_scanned', [])}")
    print(f"  At       : {meta.get('generated_at', '?')}")
    print()

    # Capture quality
    cap_status  = capture.get("capture_status", "?")
    cap_age     = capture.get("data_age_minutes")
    cap_penalty = capture.get("capture_quality_penalty", 0.0)
    age_str = f"{cap_age:.1f} min" if cap_age is not None else "unknown"
    print(f"  Capture  : {cap_status}  |  Age: {age_str}  |  Penalty: {cap_penalty:.2f}")
    print()

    # Error case
    if "error" in meta:
        print(f"  ERREUR : {meta['error']}")
        _print_sep()
        return

    # Ranking
    print(f"  {'Rank':<6}{'Currency':<10}{'Score':<10}{'Label':<18}{'Absorption'}")
    _print_sep()
    for row in ranking:
        rank     = row.get("rank", "?")
        currency = row.get("currency", "?")
        score    = row.get("energy_score", 0.0)
        label    = row.get("label", "?")
        absorb   = row.get("absorption", "?")
        print(f"  {rank:<6}{currency:<10}{score:<10.4f}{label:<18}{absorb}")

    print()
    _print_sep()

    # Top energy
    if top:
        highest = top.get("highest", "?")
        high_sc = top.get("highest_score", 0.0)
        transit = top.get("in_transition", [])
        high_f  = top.get("high_field", [])
        weak_f  = top.get("weak_field", [])
        print(f"  DOMINANT      : {highest} ({high_sc:.4f})")
        if high_f:
            print(f"  ENERGY_HIGH   : {', '.join(high_f)}")
        if transit:
            print(f"  IN_TRANSITION : {', '.join(transit)}")
        if weak_f:
            print(f"  WEAK_FIELD    : {', '.join(weak_f)}")
        print()

    # Summary
    print(f"  {summary}")
    _print_sep()

    # Components detail (top 3)
    currencies = state.get("currencies", {})
    top3 = [r["currency"] for r in ranking[:3]]
    if top3:
        print()
        print("  COMPONENTS (top 3) :")
        _print_sep()
        comp_keys = [
            ("zone_tension_norm",      "zone_tension   "),
            ("behavioral_zscore_norm", "behavioral_z   "),
            ("speed_norm",             "speed          "),
            ("angle_norm",             "angle          "),
            ("acceleration_norm",      "acceleration   "),
            ("persistence_norm",       "persistence    "),
            ("basket_deviation_norm",  "basket_dev     "),
            ("htf_context_norm",       "htf_context    "),
        ]
        header = f"  {'Component':<20}" + "".join(f"{c:<10}" for c in top3)
        print(header)
        for key, label in comp_keys:
            row_str = f"  {label:<20}"
            for c in top3:
                val = currencies.get(c, {}).get("components", {}).get(key)
                row_str += f"{val:<10.4f}" if val is not None else f"{'N/A':<10}"
            print(row_str)
        print()

    # Modules availability
    mods = meta.get("modules_available", {})
    if mods:
        print("  Modules :")
        for mod, ok in mods.items():
            status = "OK" if ok else "MISSING"
            print(f"    {mod:<35} {status}")
    _print_sep()
    print()


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="PowerFlow V6 — Currency Energy Probe (read-only)"
    )
    parser.add_argument(
        "--db",
        default="powerflow.db",
        help="Chemin vers powerflow.db (défaut : powerflow.db)",
    )
    parser.add_argument(
        "--symbol",
        default="GBPUSD",
        help="Symbole de trading (défaut : GBPUSD)",
    )
    parser.add_argument(
        "--timeframe",
        type=int,
        default=15,
        help="Timeframe principal en minutes (défaut : 15)",
    )
    parser.add_argument(
        "--bars",
        type=int,
        default=50,
        help="Nombre de barres à charger (défaut : 50)",
    )
    parser.add_argument(
        "--htf",
        default="15,30,60",
        help="Timeframes HTF séparés par virgule pour htf_context_score (défaut : 15,30,60)",
    )
    parser.add_argument(
        "--out",
        default="output/currency_energy_state.json",
        help="Fichier de sortie JSON (défaut : output/currency_energy_state.json)",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="JSON indenté lisible (défaut : activé)",
    )
    parser.add_argument(
        "--no-pretty",
        dest="pretty",
        action="store_false",
        help="JSON compact",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        default=False,
        help="Affiche un résumé dans le terminal après génération",
    )

    args = parser.parse_args()

    # Parse HTF timeframes
    try:
        htf_tfs = [int(x.strip()) for x in args.htf.split(",") if x.strip()]
    except ValueError:
        print(f"ERREUR : --htf invalide : {args.htf}", file=sys.stderr)
        return 1

    if not htf_tfs:
        htf_tfs = [15, 30, 60]

    db_path = Path(args.db)
    out_path = Path(args.out)

    # ── Import probe ──────────────────────────────────────────────────────────
    try:
        from pf_currency_energy_probe import (
            build_currency_energy_state,
            write_currency_energy_state,
        )
    except ImportError as e:
        print(f"ERREUR import pf_currency_energy_probe : {e}", file=sys.stderr)
        print("Vérifier que pf_currency_energy_probe.py est dans le même répertoire.", file=sys.stderr)
        return 1

    # ── Build state ───────────────────────────────────────────────────────────
    print(f"[ENERGY] Lecture {db_path} | {args.symbol} | TF{args.timeframe} | {args.bars} bars")
    print(f"[ENERGY] HTF scan : {htf_tfs}")

    try:
        state = build_currency_energy_state(
            db_path=db_path,
            symbol=args.symbol,
            timeframe=args.timeframe,
            bars=args.bars,
            htf_tfs=htf_tfs,
        )
    except Exception as e:
        print(f"ERREUR build_currency_energy_state : {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    # ── Write JSON ────────────────────────────────────────────────────────────
    try:
        write_currency_energy_state(state, out_path, pretty=args.pretty)
        print(f"[ENERGY] OK → {out_path}")
    except Exception as e:
        print(f"ERREUR écriture {out_path} : {e}", file=sys.stderr)
        return 1

    # ── Summary terminal ─────────────────────────────────────────────────────
    if args.summary:
        _print_summary(state)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
