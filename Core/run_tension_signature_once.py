"""
PowerFlow V6 - run_tension_signature_once.py
Version: V0.1.3 — cross-TF check ELASTIC_LOADED

Usage:
    python run_tension_signature_once.py
    python run_tension_signature_once.py --tf 5 --bars 20
    python run_tension_signature_once.py --before "2026-05-07T20:50:00+00:00"
    python run_tension_signature_once.py --cross
    python run_tension_signature_once.py --cross --before "2026-05-07T20:50:00+00:00"
    python run_tension_signature_once.py --json
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Dict, List, Optional

from pf_tension_signature import compute_tension_signature, TensionSignature

# ==========================================================================
# CONFIG
# ==========================================================================

DEFAULT_DB    = "powerflow.db"
DEFAULT_TF    = 5
DEFAULT_BARS  = 20
TABLE         = "force_snapshots_v2"
TS_COL        = "created_at"
TF_COL        = "timeframe"

CROSS_TF_PAIRS = [(1, 8), (5, 8), (15, 6)]  # (timeframe, bars)

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
# DB READ
# ==========================================================================

def fetch_series(
    db_path: str,
    force_col: str,
    timeframe: int,
    bars: int,
    before: Optional[str] = None,
) -> List[Optional[float]]:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        if before:
            query = f"""
                SELECT {force_col}
                FROM {TABLE}
                WHERE {TF_COL} = ?
                  AND {TS_COL} <= ?
                ORDER BY {TS_COL} DESC
                LIMIT ?
            """
            cur.execute(query, (timeframe, before, bars))
        else:
            query = f"""
                SELECT {force_col}
                FROM {TABLE}
                WHERE {TF_COL} = ?
                ORDER BY {TS_COL} DESC
                LIMIT ?
            """
            cur.execute(query, (timeframe, bars))
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in reversed(rows)]
    except sqlite3.Error as e:
        print(f"[DB ERROR] {force_col} TF{timeframe}: {e}", file=sys.stderr)
        return []


# ==========================================================================
# CROSS-TF CHECK
# ==========================================================================

def run_cross_tf(
    db_path: str,
    before: Optional[str],
    as_json: bool,
) -> None:
    """
    Pour chaque devise, vérifie si ELASTIC_LOADED apparaît
    sur plusieurs TF simultanément.
    MULTI_TF_ELASTIC = compression multi-échelle confirmée.
    """
    # Structure : {currency: {tf: TensionSignature}}
    all_results: Dict[str, Dict[int, dict]] = {c: {} for c in CURRENCIES}

    for tf, bars in CROSS_TF_PAIRS:
        for currency, force_col in CURRENCIES.items():
            series = fetch_series(db_path, force_col, tf, bars, before)
            sig = compute_tension_signature(series)
            all_results[currency][tf] = sig.to_dict()

    # Synthèse cross-TF
    cross_summary: Dict[str, dict] = {}
    for currency, tf_data in all_results.items():
        elastic_tfs = [
            tf for tf, d in tf_data.items()
            if d["label"] == "ELASTIC_LOADED"
        ]
        if len(elastic_tfs) >= 2:
            cross_label = "MULTI_TF_ELASTIC"
        elif len(elastic_tfs) == 1:
            cross_label = "SINGLE_TF_ELASTIC"
        else:
            cross_label = "NO_ELASTIC"

        cross_summary[currency] = {
            "cross_label": cross_label,
            "elastic_tfs": elastic_tfs,
            "tf_detail": tf_data,
        }

    if as_json:
        print(json.dumps(cross_summary, indent=2, ensure_ascii=False))
        return

    label_time = f"avant {before}" if before else "maintenant"
    print("=" * 72)
    print(f"PowerFlow V6 — Cross-TF Tension — TF{[t for t,_ in CROSS_TF_PAIRS]} — {label_time}")
    print("=" * 72)

    # Tri : MULTI_TF_ELASTIC en premier
    order = {"MULTI_TF_ELASTIC": 0, "SINGLE_TF_ELASTIC": 1, "NO_ELASTIC": 2}
    sorted_currencies = sorted(
        cross_summary.items(),
        key=lambda x: order.get(x[1]["cross_label"], 9)
    )

    for currency, data in sorted_currencies:
        cl = data["cross_label"].ljust(22)
        tfs = str(data["elastic_tfs"]) if data["elastic_tfs"] else "[]"
        scores = "  ".join(
            f"TF{tf}={data['tf_detail'][tf]['score']:.2f}"
            for tf, _ in CROSS_TF_PAIRS
            if tf in data["tf_detail"]
        )
        print(f"  {currency.ljust(4)}  {cl}  elastic={tfs.ljust(12)}  {scores}")

    print("=" * 72)

    # Alerte MULTI_TF_ELASTIC
    multi = [c for c, d in cross_summary.items() if d["cross_label"] == "MULTI_TF_ELASTIC"]
    if multi:
        print(f"\n  *** MULTI_TF_ELASTIC : {', '.join(multi)} ***")
        print(f"  Compression multi-echelle confirmee — elastique charge sur plusieurs TF.")
    print()


# ==========================================================================
# SINGLE TF RUN
# ==========================================================================

def run_single_tf(
    db_path: str,
    tf: int,
    bars: int,
    before: Optional[str],
    as_json: bool,
) -> None:
    results: Dict[str, dict] = {}

    for currency, force_col in CURRENCIES.items():
        series = fetch_series(db_path, force_col, tf, bars, before)
        sig: TensionSignature = compute_tension_signature(series)
        results[currency] = sig.to_dict()

    if as_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return

    label_time = f"avant {before}" if before else "maintenant"
    print("=" * 72)
    print(f"PowerFlow V6 — Tension Signature — TF{tf} — {bars} barres — {label_time}")
    print("=" * 72)
    for currency, d in results.items():
        label_pad  = d["label"].ljust(20)
        score_str  = f"{d['score']:.2f}".rjust(10)
        bars_str   = f"n={d['n_bars']}".ljust(6)
        note_short = d["note"][:55]
        print(f"  {currency.ljust(4)}  {label_pad}  score={score_str}  {bars_str}  {note_short}")
    print("=" * 72)


# ==========================================================================
# MAIN
# ==========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="run_tension_signature_once")
    parser.add_argument("--db",     default=DEFAULT_DB)
    parser.add_argument("--tf",     type=int, default=DEFAULT_TF)
    parser.add_argument("--bars",   type=int, default=DEFAULT_BARS)
    parser.add_argument("--before", default=None,
                        help='Replay. Format: "2026-05-07T20:50:00+00:00"')
    parser.add_argument("--cross",  action="store_true",
                        help="Cross-TF check ELASTIC_LOADED sur TF1/5/15")
    parser.add_argument("--json",   action="store_true")
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"[ERROR] DB introuvable : {args.db}", file=sys.stderr)
        sys.exit(1)

    if args.cross:
        run_cross_tf(args.db, args.before, args.json)
    else:
        run_single_tf(args.db, args.tf, args.bars, args.before, args.json)


if __name__ == "__main__":
    main()