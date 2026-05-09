"""
PowerFlow V6 - run_confluence_scan.py
Version: V0.1.0 — scan journalier fenetre glissante

Mission:
    Rejouer run_confluence sur toute une journée, snapshot par snapshot.
    Sortie : timeline des confluences — qui était tendu, quand, combien de temps.

Usage:
    python run_confluence_scan.py
    python run_confluence_scan.py --date 2026-05-08
    python run_confluence_scan.py --date 2026-05-08 --zone-tf 30
    python run_confluence_scan.py --date 2026-05-08 --json
    python run_confluence_scan.py --date 2026-05-08 --summary
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pf_tension_signature import compute_tension_signature
from pf_zone_dynamics import analyze_zone_dynamics

# ==========================================================================
# CONFIG
# ==========================================================================

DEFAULT_DB      = "powerflow.db"
TABLE_SNAP      = "force_snapshots_v2"
TS_COL          = "created_at"
TF_COL          = "timeframe"

CROSS_TF_PAIRS  = [(1, 8), (5, 8)]
DEFAULT_ZONE_TF = 15
ZONE_BARS       = 30
SCAN_STEP_MIN   = 5       # snapshot toutes les 5 minutes

ZONE_ACTIVE_STATES = {"ACCUMULATING", "EXTREME", "EARLY_EXTREME", "LEAKING"}

CURRENCIES = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
    "NZD": "force_nzd",
}

CONFLUENCE_ORDER = {
    "ELASTIC_IN_EXTREME": 0,
    "ELASTIC_NO_ZONE":    1,
    "ELASTIC_WEAK_ZONE":  2,
    "ZONE_NO_ELASTIC":    3,
    "NOTHING":            4,
}

CONFLUENCE_SHORT = {
    "ELASTIC_IN_EXTREME": "EIE⚡",
    "ELASTIC_NO_ZONE":    "ENZ ",
    "ELASTIC_WEAK_ZONE":  "EWZ ",
    "ZONE_NO_ELASTIC":    "ZNE ",
    "NOTHING":            "... ",
}


# ==========================================================================
# HELPERS
# ==========================================================================

def detect_session(dt_utc: datetime) -> str:
    h = dt_utc.hour
    if 0 <= h < 7:   return "ASIA      "
    if 7 <= h < 9:   return "LON_OPEN  "
    if 9 <= h < 13:  return "LONDON    "
    if 13 <= h < 16: return "PRE_US    "
    if 16 <= h < 21: return "US        "
    return             "US_CLOSE  "


def zone_position_label(z: float, direction: str) -> str:
    if direction == "HIGH":
        if z >= 75: return "SOMMET"
        if z >= 50: return "MIL_H "
        return "BAS_H "
    if direction == "LOW":
        az = abs(z)
        if az >= 75: return "SOMMET"
        if az >= 50: return "MIL_L "
        return "BAS_L "
    return "NEUTRE"


def fetch_series(
    db_path: str,
    force_col: str,
    timeframe: int,
    bars: int,
    before: str,
) -> List[Optional[float]]:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            f"SELECT {force_col} FROM {TABLE_SNAP} "
            f"WHERE {TF_COL}=? AND {TS_COL}<=? "
            f"ORDER BY {TS_COL} DESC LIMIT ?",
            (timeframe, before, bars),
        )
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in reversed(rows)]
    except sqlite3.Error as e:
        print(f"[DB ERROR] {force_col} TF{timeframe}: {e}", file=sys.stderr)
        return []


def fetch_timestamps(
    db_path: str,
    date_str: str,
    step_min: int,
) -> List[str]:
    """Retourne les timestamps TF5 disponibles pour la date donnée."""
    date_start = f"{date_str}T00:00:00+00:00"
    date_end   = f"{date_str}T23:59:59+00:00"
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            f"SELECT DISTINCT {TS_COL} FROM {TABLE_SNAP} "
            f"WHERE {TF_COL}=5 "
            f"  AND {TS_COL} >= ? AND {TS_COL} <= ? "
            f"ORDER BY {TS_COL} ASC",
            (date_start, date_end),
        )
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in rows]
    except sqlite3.Error as e:
        print(f"[DB ERROR] fetch_timestamps: {e}", file=sys.stderr)
        return []


def compute_confluence(elastic_tfs: List[int], zone_state: str) -> str:
    zone_active = zone_state in ZONE_ACTIVE_STATES
    has_multi   = len(elastic_tfs) >= 2
    has_single  = len(elastic_tfs) == 1
    if has_multi and zone_active:   return "ELASTIC_IN_EXTREME"
    if has_multi:                   return "ELASTIC_NO_ZONE"
    if has_single and zone_active:  return "ELASTIC_WEAK_ZONE"
    if zone_active:                 return "ZONE_NO_ELASTIC"
    return "NOTHING"


# ==========================================================================
# SNAPSHOT
# ==========================================================================

def compute_snapshot(
    db_path: str,
    before: str,
    zone_tf: int,
) -> Dict[str, dict]:
    results = {}
    for currency, force_col in CURRENCIES.items():
        tf_sigs = {}
        elastic_tfs = []
        for tf, bars in CROSS_TF_PAIRS:
            series = fetch_series(db_path, force_col, tf, bars, before)
            sig = compute_tension_signature(series)
            tf_sigs[tf] = {"label": sig.label, "score": sig.score}
            if sig.label == "ELASTIC_LOADED":
                elastic_tfs.append(tf)

        zone_series = fetch_series(db_path, force_col, zone_tf, ZONE_BARS, before)
        if len(zone_series) >= 6:
            diag = analyze_zone_dynamics(zone_series, timeframe=zone_tf, currency=currency)
            zone_state   = diag.state
            zone_z       = diag.z_current
            zone_dir     = diag.z_extreme_dir
        else:
            zone_state = "NO_DATA"
            zone_z     = 0.0
            zone_dir   = "NONE"

        position   = zone_position_label(zone_z, zone_dir)
        confluence = compute_confluence(elastic_tfs, zone_state)

        results[currency] = {
            "confluence":  confluence,
            "elastic_tfs": elastic_tfs,
            "tf1_score":   tf_sigs.get(1, {}).get("score", 0),
            "tf5_score":   tf_sigs.get(5, {}).get("score", 0),
            "zone_state":  zone_state,
            "zone_z":      zone_z,
            "zone_dir":    zone_dir,
            "position":    position,
        }
    return results



# ==========================================================================
# FILTRE PERSISTANCE EIE
# ==========================================================================

def filter_persistent_eie(
    snapshots: list,
    min_persist: int = 2,
) -> list:
    """
    Garde uniquement les snapshots où au moins une devise
    est en EIE sur min_persist snapshots consécutifs.
    Retourne la liste filtrée avec annotation de persistance.
    """
    currencies = list(CURRENCIES.keys())
    n = len(snapshots)

    # Calcul de la persistance : pour chaque snap/devise, combien de fois
    # consécutifs EIE en partant de ce snap vers l'avant.
    persist = [[0] * len(currencies) for _ in range(n)]

    for i in range(n - 1, -1, -1):
        for j, c in enumerate(currencies):
            if snapshots[i]["data"][c]["confluence"] == "ELASTIC_IN_EXTREME":
                persist[i][j] = 1 + (persist[i + 1][j] if i + 1 < n else 0)
            else:
                persist[i][j] = 0

    # Filtre : garder les snaps où au moins une devise atteint min_persist.
    filtered = []
    for i, snap in enumerate(snapshots):
        persistent_currencies = [
            currencies[j]
            for j in range(len(currencies))
            if persist[i][j] >= min_persist
        ]
        if persistent_currencies:
            snap = dict(snap)
            snap["persistent_eie"] = persistent_currencies
            filtered.append(snap)

    return filtered


# ==========================================================================
# MAIN
# ==========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="run_confluence_scan")
    parser.add_argument("--db",       default=DEFAULT_DB)
    parser.add_argument("--date",     default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        help="Date a scanner (UTC). Default: aujourd'hui")
    parser.add_argument("--zone-tf",  type=int, default=DEFAULT_ZONE_TF)
    parser.add_argument("--summary",  action="store_true",
                        help="Affiche uniquement les snapshots avec EIE persistant")
    parser.add_argument("--min-persist", type=int, default=2,
                        help="Nombre minimum de snapshots consécutifs EIE (default 2 = 10 min)")
    parser.add_argument("--json",     action="store_true")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"[ERROR] DB introuvable : {args.db}", file=sys.stderr)
        sys.exit(1)

    timestamps = fetch_timestamps(args.db, args.date, SCAN_STEP_MIN)
    if not timestamps:
        print(f"[ERROR] Aucune donnée TF5 pour le {args.date}", file=sys.stderr)
        sys.exit(1)

    print(f"[SCAN] {args.date} — {len(timestamps)} snapshots TF5 — zone TF{args.zone_tf}")

    all_snapshots = []

    for ts in timestamps:
        try:
            dt_utc = datetime.fromisoformat(ts)
            if dt_utc.tzinfo is None:
                dt_utc = dt_utc.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

        snap_data = compute_snapshot(args.db, ts, args.zone_tf)
        session   = detect_session(dt_utc)
        cest_h    = (dt_utc.hour + 2) % 24
        time_str  = f"{cest_h:02d}:{dt_utc.minute:02d}"

        top_confluence = min(
            (d["confluence"] for d in snap_data.values()),
            key=lambda x: CONFLUENCE_ORDER.get(x, 9),
        )

        all_snapshots.append({
            "ts":       ts,
            "time":     time_str,
            "session":  session.strip(),
            "data":     snap_data,
            "top":      top_confluence,
        })

    # Filtre persistance
    if args.min_persist < 1:
        args.min_persist = 1

    if args.min_persist > 1 or args.summary:
        display_snapshots = filter_persistent_eie(all_snapshots, args.min_persist)
        persist_label = f"EIE persistant >= {args.min_persist} snapshots ({args.min_persist * SCAN_STEP_MIN} min)"
    else:
        display_snapshots = all_snapshots
        persist_label = "tous snapshots"

    if args.json:
        print(json.dumps(display_snapshots, indent=2, ensure_ascii=False))
        return

    # Affichage timeline
    header = f"{'HEURE':6}  {'SESSION':10}  " + "  ".join(f"{c:4}" for c in CURRENCIES)
    sep    = "=" * len(header)

    print(sep)
    print(f"  PowerFlow V6 — Confluence Scan — {args.date} — TF{args.zone_tf} zone")
    print(f"  Filtre : {persist_label} — {len(display_snapshots)}/{len(all_snapshots)} snapshots affichés")
    print(sep)
    print(f"  {header}")
    print(f"  {'-' * (len(header))}")

    for snap in display_snapshots:
        row = f"  {snap['time']:6}  {snap['session']:10}  "
        row += "  ".join(
            CONFLUENCE_SHORT.get(snap["data"][c]["confluence"], "?   ")
            for c in CURRENCIES
        )
        persistent = snap.get("persistent_eie", [])
        eie_all = [
            c
            for c in CURRENCIES
            if snap["data"][c]["confluence"] == "ELASTIC_IN_EXTREME"
        ]
        if persistent:
            row += f"  ⚡⚡ {', '.join(persistent)}"
        elif eie_all:
            row += f"  *** {', '.join(eie_all)}"
        print(row)

    print(sep)

    # Résumé EIE
    print(f"\n  Légende : EIE⚡=ELASTIC_IN_EXTREME  ENZ=ELASTIC_NO_ZONE")
    print(f"            EWZ=ELASTIC_WEAK_ZONE    ZNE=ZONE_NO_ELASTIC  ...=NOTHING\n")

    # Compte EIE par devise
    eie_counts: Dict[str, int] = {c: 0 for c in CURRENCIES}
    for snap in display_snapshots:
        for c in CURRENCIES:
            if snap["data"][c]["confluence"] == "ELASTIC_IN_EXTREME":
                eie_counts[c] += 1

    print("  EIE par devise sur la journée :")
    for c, count in sorted(eie_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"    {c:4}  {str(count).rjust(3)}x  {bar}")
    print()


if __name__ == "__main__":
    main()