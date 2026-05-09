"""
lab.py — PowerFlow Lab Rapide
Test de conditions sur force_snapshots_v2 en one-liner.
Testé sur powerflow.db 06/05/2026.

Usage:
    python lab.py "force_gbp > 60" --last 4h
    python lab.py "force_gbp > 60 AND force_usd < 40" --last 4h
    python lab.py "gbp_shift_3 > 10" --last 8h --tf 1
    python lab.py "force_gbp > force_usd AND vol > 100" --last 4h
"""

import sqlite3
import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path


DB_DEFAULT = "powerflow.db"
SYMBOL_DEFAULT = "GBPUSD"

# Variables disponibles dans les conditions
AVAILABLE_VARS = [
    "force_gbp", "force_usd", "force_eur", "force_jpy",
    "force_cad", "force_chf", "force_aud", "force_nzd",
    "vol",             # tick_volume alias
    "spread",          # spread_pips (None-safe → 999 si absent)
    "pip_range",       # None-safe → 0
    "pip_body",        # None-safe → 0
    # Calculés dynamiquement
    "gbp_shift_3",     # delta force_gbp sur 3 bars
    "usd_shift_3",     # delta force_usd sur 3 bars
    "gbp_usd_gap",     # force_gbp - force_usd
    "gbp_dom",         # force_gbp = max de toutes les forces
]


def parse_args():
    p = argparse.ArgumentParser(description="PowerFlow Lab Rapide")
    p.add_argument("condition", help='Condition ex: "force_gbp > 60 AND vol > 50"')
    p.add_argument("--db", default=DB_DEFAULT)
    p.add_argument("--symbol", default=SYMBOL_DEFAULT)
    p.add_argument("--tf", type=int, default=1, help="Timeframe (1=M1, 5=M5, etc.)")
    p.add_argument("--last", default="4h", help="Fenêtre: 3h, 4h, 8h, 1d, all")
    p.add_argument("--out", default=None, help="Fichier JSON output")
    p.add_argument("--limit", type=int, default=50)
    return p.parse_args()


def parse_window(last: str) -> datetime | None:
    """Retourne le datetime de début de fenêtre, ou None pour 'all'."""
    if last == "all":
        return None
    m = re.match(r"(\d+)(h|d|m)", last)
    if not m:
        raise ValueError(f"Format --last invalide: {last}. Exemples: 3h, 4h, 1d, all")
    n, unit = int(m.group(1)), m.group(2)
    now = datetime.now(timezone.utc)
    if unit == "h":
        return now - timedelta(hours=n)
    elif unit == "d":
        return now - timedelta(days=n)
    elif unit == "m":
        return now - timedelta(minutes=n)


def load_bars(db_path: str, symbol: str, tf: int, since: datetime | None) -> list[dict]:
    """Charge les bars depuis force_snapshots_v2."""
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    if since:
        cur.execute("""
            SELECT created_at, force_gbp, force_usd, force_eur, force_jpy,
                   force_cad, force_chf, force_aud, force_nzd,
                   tick_volume, spread_pips, pip_range, pip_body
            FROM force_snapshots_v2
            WHERE timeframe = ? AND created_at >= ?
            ORDER BY created_at
        """, (tf, since.isoformat()))
    else:
        cur.execute("""
            SELECT created_at, force_gbp, force_usd, force_eur, force_jpy,
                   force_cad, force_chf, force_aud, force_nzd,
                   tick_volume, spread_pips, pip_range, pip_body
            FROM force_snapshots_v2
            WHERE timeframe = ?
            ORDER BY created_at
        """, (tf,))

    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]


def enrich(bars: list[dict]) -> list[dict]:
    """Calcule les variables dérivées bar par bar."""
    for i, bar in enumerate(bars):
        # Alias simples
        bar["vol"] = bar.get("tick_volume") or 0
        bar["spread"] = bar.get("spread_pips") or 999.0
        bar["pip_range"] = bar.get("pip_range") or 0.0
        bar["pip_body"] = bar.get("pip_body") or 0.0

        # Gap GBP/USD
        bar["gbp_usd_gap"] = (bar["force_gbp"] or 0) - (bar["force_usd"] or 0)

        # Dominance GBP
        forces = [bar.get(f"force_{c}") or 0 for c in ["gbp", "usd", "eur", "jpy", "cad", "chf", "aud"]]
        bar["gbp_dom"] = 1.0 if (bar["force_gbp"] or 0) == max(forces) else 0.0

        # Shifts sur 3 bars
        if i >= 3:
            prev = bars[i - 3]
            bar["gbp_shift_3"] = (bar["force_gbp"] or 0) - (prev["force_gbp"] or 0)
            bar["usd_shift_3"] = (bar["force_usd"] or 0) - (prev["force_usd"] or 0)
        else:
            bar["gbp_shift_3"] = 0.0
            bar["usd_shift_3"] = 0.0

    return bars


def eval_condition(bar: dict, condition: str) -> bool:
    """Évalue la condition sur un bar. Retourne False si erreur."""
    # Normalise AND/OR/NOT → and/or/not (SQL-style input accepted)
    expr = re.sub(r'\bAND\b', 'and', condition)
    expr = re.sub(r'\bOR\b', 'or', expr)
    expr = re.sub(r'\bNOT\b', 'not', expr)
    safe_vars = {k: bar.get(k, 0) or 0 for k in AVAILABLE_VARS}
    try:
        return bool(eval(expr, {"__builtins__": {}}, safe_vars))
    except Exception:
        return False


def format_bar(bar: dict, condition: str) -> str:
    """Formatte une ligne de résultat."""
    ts = bar["created_at"][:16]
    gbp = bar.get("force_gbp", 0) or 0
    usd = bar.get("force_usd", 0) or 0
    vol = bar.get("vol", 0)
    shift = bar.get("gbp_shift_3", 0)
    gap = bar.get("gbp_usd_gap", 0)
    direction = "↑GBP" if gap > 0 else "↓USD"
    return f"{ts} | GBP={gbp:5.1f} USD={usd:5.1f} | shift3={shift:+.1f} gap={gap:+.1f} [{direction}] vol={vol:.0f}"


def main():
    args = parse_args()
    db_path = args.db

    if not Path(db_path).exists():
        print(f"❌ DB introuvable: {db_path}")
        return

    print(f"\n🔬 LAB RAPIDE — Test de condition")
    print("=" * 72)
    print(f"Condition : {args.condition}")
    print(f"DB        : {db_path}")
    print(f"TF        : M{args.tf}")
    print(f"Fenêtre   : {args.last}")
    print("=" * 72)

    since = parse_window(args.last)
    bars = load_bars(db_path, args.symbol, args.tf, since)

    if not bars:
        print("❌ Aucune donnée trouvée pour cette fenêtre.")
        return

    bars = enrich(bars)

    matches = [b for b in bars if eval_condition(b, args.condition)]

    print(f"\n📊 {len(bars)} bars analysés | {len(matches)} occurrences\n")

    if not matches:
        print("❌ Aucune occurrence trouvée.")
        return

    # Affiche les N premiers
    display = matches[:args.limit]
    for b in display:
        print(f"  ✅ {format_bar(b, args.condition)}")

    if len(matches) > args.limit:
        print(f"\n  ... ({len(matches) - args.limit} autres non affichés)")

    # Stats rapides
    shifts = [b.get("gbp_shift_3", 0) for b in matches]
    vols = [b.get("vol", 0) for b in matches]
    print(f"\n📈 Stats GBP shift_3 : avg={sum(shifts)/len(shifts):+.1f} | max={max(shifts):+.1f} | min={min(shifts):+.1f}")
    print(f"📈 Stats volume      : avg={sum(vols)/len(vols):.0f} | max={max(vols):.0f}")

    # Export JSON optionnel
    if args.out:
        out = {
            "condition": args.condition,
            "tf": args.tf,
            "window": args.last,
            "total_bars": len(bars),
            "matches_count": len(matches),
            "matches": [
                {
                    "ts": b["created_at"],
                    "force_gbp": b.get("force_gbp"),
                    "force_usd": b.get("force_usd"),
                    "gbp_shift_3": b.get("gbp_shift_3"),
                    "gbp_usd_gap": b.get("gbp_usd_gap"),
                    "vol": b.get("vol"),
                }
                for b in matches
            ]
        }
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(out, indent=2, default=str))
        print(f"\n💾 Résultats → {args.out}")


if __name__ == "__main__":
    main()
