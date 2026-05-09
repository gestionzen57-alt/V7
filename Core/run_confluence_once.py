"""
PowerFlow V6 - run_confluence_once.py
Version: V0.2.1 — timestamp + position zone lisible + session

Usage:
    python run_confluence_once.py
    python run_confluence_once.py --before "2026-05-07T17:50:00+00:00"
    python run_confluence_once.py --zone-tf 30
    python run_confluence_once.py --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

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


# ==========================================================================
# SESSION DETECTION
# ==========================================================================

def detect_session(dt_utc: datetime) -> str:
    h = dt_utc.hour
    if 0 <= h < 7:
        return "ASIA"
    if 7 <= h < 9:
        return "LONDON_OPEN"
    if 9 <= h < 13:
        return "LONDON"
    if 13 <= h < 16:
        return "PRE_US"
    if 16 <= h < 21:
        return "US"
    return "US_CLOSE"


# ==========================================================================
# ZONE POSITION LABEL
# ==========================================================================

def zone_position_label(z: float, direction: str) -> str:
    """Traduit le z-score en position lisible dans la zone."""
    if direction == "HIGH":
        if z >= 75:
            return "SOMMET"
        if z >= 50:
            return "MILIEU_H"
        return "BAS_H"
    if direction == "LOW":
        az = abs(z)
        if az >= 75:
            return "SOMMET"
        if az >= 50:
            return "MILIEU_L"
        return "BAS_L"
    return "NEUTRE"


# ==========================================================================
# DB READ
# ==========================================================================

def fetch_series(
    db_path: str,
    force_col: str,
    timeframe: int,
    bars: int,
    before: Optional[str],
) -> List[Optional[float]]:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        if before:
            cur.execute(
                f"SELECT {force_col} FROM {TABLE_SNAP} "
                f"WHERE {TF_COL}=? AND {TS_COL}<=? "
                f"ORDER BY {TS_COL} DESC LIMIT ?",
                (timeframe, before, bars),
            )
        else:
            cur.execute(
                f"SELECT {force_col} FROM {TABLE_SNAP} "
                f"WHERE {TF_COL}=? "
                f"ORDER BY {TS_COL} DESC LIMIT ?",
                (timeframe, bars),
            )
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in reversed(rows)]
    except sqlite3.Error as e:
        print(f"[DB ERROR] {force_col} TF{timeframe}: {e}", file=sys.stderr)
        return []


# ==========================================================================
# CONFLUENCE LOGIC
# ==========================================================================

def compute_confluence(elastic_tfs: List[int], zone_state: str) -> str:
    zone_active = zone_state in ZONE_ACTIVE_STATES
    has_multi   = len(elastic_tfs) >= 2
    has_single  = len(elastic_tfs) == 1

    if has_multi and zone_active:
        return "ELASTIC_IN_EXTREME"
    if has_multi:
        return "ELASTIC_NO_ZONE"
    if has_single and zone_active:
        return "ELASTIC_WEAK_ZONE"
    if zone_active:
        return "ZONE_NO_ELASTIC"
    return "NOTHING"


# ==========================================================================
# MAIN
# ==========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="run_confluence_once")
    parser.add_argument("--db",       default=DEFAULT_DB)
    parser.add_argument("--before",   default=None)
    parser.add_argument("--zone-tf",  type=int, default=DEFAULT_ZONE_TF)
    parser.add_argument("--json",     action="store_true")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"[ERROR] DB introuvable : {args.db}", file=sys.stderr)
        sys.exit(1)

    # Timestamp du snapshot
    now_utc = datetime.now(timezone.utc)
    if args.before:
        try:
            snap_utc = datetime.fromisoformat(args.before)
            if snap_utc.tzinfo is None:
                snap_utc = snap_utc.replace(tzinfo=timezone.utc)
        except ValueError:
            snap_utc = now_utc
    else:
        snap_utc = now_utc

    snap_cest_offset = 2  # CEST = UTC+2
    snap_local_h = (snap_utc.hour + snap_cest_offset) % 24
    snap_time_str = f"{snap_local_h:02d}:{snap_utc.minute:02d} CEST"
    snap_utc_str  = snap_utc.strftime("%Y-%m-%d %H:%M UTC")
    session       = detect_session(snap_utc)

    results: Dict[str, dict] = {}

    for currency, force_col in CURRENCIES.items():

        # Tension cross-TF
        tf_sigs = {}
        elastic_tfs = []
        for tf, bars in CROSS_TF_PAIRS:
            series = fetch_series(args.db, force_col, tf, bars, args.before)
            sig = compute_tension_signature(series)
            tf_sigs[tf] = {"label": sig.label, "score": sig.score}
            if sig.label == "ELASTIC_LOADED":
                elastic_tfs.append(tf)

        # Zone live
        zone_series = fetch_series(
            args.db, force_col, args.zone_tf, ZONE_BARS, args.before
        )
        if len(zone_series) >= 6:
            diag = analyze_zone_dynamics(
                zone_series,
                timeframe=args.zone_tf,
                currency=currency,
            )
            zone_state   = diag.state
            zone_level   = diag.zone_level
            zone_z       = diag.z_current
            zone_dir     = diag.z_extreme_dir
            zone_tension = diag.tension_score
        else:
            zone_state   = "NO_DATA"
            zone_level   = "NORMAL"
            zone_z       = 0.0
            zone_dir     = "NONE"
            zone_tension = 0.0

        position = zone_position_label(zone_z, zone_dir)
        confluence = compute_confluence(elastic_tfs, zone_state)

        results[currency] = {
            "confluence":  confluence,
            "elastic_tfs": elastic_tfs,
            "tf1":         tf_sigs.get(1, {}),
            "tf5":         tf_sigs.get(5, {}),
            "zone": {
                "tf":       args.zone_tf,
                "state":    zone_state,
                "level":    zone_level,
                "z":        zone_z,
                "dir":      zone_dir,
                "position": position,
                "tension":  zone_tension,
            },
        }

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    label_time = f"avant {args.before}" if args.before else "maintenant"
    print("=" * 84)
    print(f"  PowerFlow V6 — Confluence — {snap_time_str} — {snap_utc_str} — Session: {session}")
    print(f"  TF1/TF5 elastic + TF{args.zone_tf} zone live — {label_time}")
    print("=" * 84)

    order = {
        "ELASTIC_IN_EXTREME": 0,
        "ELASTIC_NO_ZONE":    1,
        "ELASTIC_WEAK_ZONE":  2,
        "ZONE_NO_ELASTIC":    3,
        "NOTHING":            4,
    }
    sorted_r = sorted(results.items(), key=lambda x: order.get(x[1]["confluence"], 9))

    for currency, d in sorted_r:
        conf     = d["confluence"].ljust(22)
        tf1_s    = f"TF1={d['tf1'].get('score', 0):.2f}".ljust(11)
        tf5_s    = f"TF5={d['tf5'].get('score', 0):.2f}".ljust(11)
        z        = d["zone"]
        zone_str = f"{z['state']} {z['position']} z={z['z']:.0f}".ljust(28)
        marker   = " ⚡" if d["confluence"] == "ELASTIC_IN_EXTREME" else ""
        print(f"  {currency.ljust(4)}  {conf}  {tf1_s}  {tf5_s}  TF{z['tf']}={zone_str}{marker}")

    print("=" * 84)

    alerts = [c for c, d in results.items() if d["confluence"] == "ELASTIC_IN_EXTREME"]
    if alerts:
        print(f"\n  *** ELASTIC_IN_EXTREME : {', '.join(alerts)} ***")
        print(f"  Compression multi-echelle en zone de gravite active.\n")
    else:
        print()


if __name__ == "__main__":
    main()