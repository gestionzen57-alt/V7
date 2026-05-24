"""
run_b9_production_test_v5.py — PowerFlow V7.6.7
Test distribution B9 v5 sur powerflow.db
is_pb + is_inverse corrigés selon C5 v5
"""

import sqlite3
import argparse
from collections import Counter
from pf_price_verdict_v5_1 import get_verdict

# ---------------------------------------------------------------------------
# SESSION DETECTION
# ---------------------------------------------------------------------------
def detect_session(hour: int) -> str:
    if 7 <= hour < 10:
        return "LONDON_OPEN"
    if 12 <= hour < 15:
        return "NY_OPEN"
    if 10 <= hour < 12 or 15 <= hour < 17:
        return "OVERLAP"
    return "OFF_SESSION"


# ---------------------------------------------------------------------------
# WINDOW RUNNER
# ---------------------------------------------------------------------------
def run_windows(db_path: str, window_size: int = 50, session_filter: str = None):
    conn   = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Détecter la colonne timestamp
    cursor.execute("PRAGMA table_info(force_snapshots_v2)")
    cols = [r[1] for r in cursor.fetchall()]
    ts_col = "created_at" if "created_at" in cols else "timestamp"

    query = f"""
        SELECT {ts_col}, close
        FROM force_snapshots_v2
        WHERE symbol = 'GBPUSD'
        ORDER BY {ts_col} ASC
    """
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("❌ Aucune donnée GBPUSD trouvée.")
        return

    print(f"Données GBPUSD : {len(rows)} lignes")
    print(f"Fenêtre : {window_size} ticks | Session : {session_filter or 'ALL'}")
    print("-" * 60)

    verdicts   = []
    confidence = []

    step = max(1, window_size // 2)
    i    = 0

    while i + window_size <= len(rows):
        window = rows[i:i + window_size]
        closes = [r[1] for r in window if r[1] is not None]

        if len(closes) < window_size // 2:
            i += step
            continue

        # Session filter
        ts_str = str(window[0][0])
        try:
            hour = int(ts_str[11:13])
        except Exception:
            hour = 9
        session = detect_session(hour)
        if session_filter and session != session_filter:
            i += step
            continue

        # v5 — C5 : calcul contexte is_pb + is_inverse
        if i >= step:
            ctx_window = rows[i - step:i]
            ctx_closes = [r[1] for r in ctx_window if r[1] is not None]
            if len(ctx_closes) >= 3:
                ctx_net_raw = (ctx_closes[-1] - ctx_closes[0]) / 0.0001
                ctx_net     = abs(ctx_net_raw)
                ctx_dir     = "UP" if ctx_net_raw > 0 else "DOWN"
                cur_net_raw = (closes[-1] - closes[0]) / 0.0001

                # v5 — C5 : is_pb = ALIGNÉ court (continuation)
                is_pb = (
                    ctx_net >= 2.0
                    and (
                        (ctx_dir == "UP"   and cur_net_raw > 0 and abs(cur_net_raw) < ctx_net * 0.85)
                        or (ctx_dir == "DOWN" and cur_net_raw < 0 and abs(cur_net_raw) < ctx_net * 0.85)
                    )
                )
                # v5 — is_inverse = mouvement INVERSE (pour CB + FAILED_REINT)
                is_inverse = (
                    ctx_net >= 2.0
                    and (
                        (ctx_dir == "UP"   and cur_net_raw < 0)
                        or (ctx_dir == "DOWN" and cur_net_raw > 0)
                    )
                )
                context = {
                    "context_direction":   ctx_dir,
                    "context_net_pips":    ctx_net,
                    "is_pullback_context": is_pb,
                    "is_inverse_context":  is_inverse,
                }
            else:
                context = {}
        else:
            context = {}

        verdict = get_verdict(closes, context)
        verdicts.append(verdict.verdict)
        confidence.append(verdict.confidence)

        i += step

    # Distribution
    total = len(verdicts)
    if total == 0:
        print("Aucune fenêtre traitée.")
        return

    counts  = Counter(verdicts)
    avg_conf = sum(confidence) / total if confidence else 0

    print(f"\n{'VERDICT':<30} {'COUNT':>6} {'%':>6}")
    print("-" * 45)
    for verdict, count in sorted(counts.items(), key=lambda x: -x[1]):
        pct = count / total * 100
        print(f"{verdict:<30} {count:>6} {pct:>5.1f}%")
    print("-" * 45)
    print(f"{'TOTAL':<30} {total:>6}")
    print(f"{'Conf moyenne':<30} {avg_conf:>6.3f}")

    # Checks qualité
    print("\n--- Checks qualité v5 ---")
    rej_pct = counts.get("REJECTED", 0) / total * 100
    pw_pct  = counts.get("PROGRESSIVE_WAVE", 0) / total * 100
    cb_pct  = counts.get("COUNTER_BREATH_CANDIDATE", 0) / total * 100
    cm_pct  = counts.get("CENTER_MIGRATION", 0) / total * 100
    pa_pct  = counts.get("PULLBACK_ABSORBED", 0) / total * 100

    print(f"REJECTED      : {rej_pct:.1f}% {'✅' if rej_pct < 10 else '⚠️'} (cible < 10%)")
    print(f"PW            : {pw_pct:.1f}%  {'✅' if 15 <= pw_pct <= 50 else '⚠️'} (cible 15-50%)")
    print(f"CB            : {cb_pct:.1f}%  {'✅' if cb_pct <= 15 else '⚠️'} (cible ≤ 15%)")
    print(f"CM            : {cm_pct:.1f}%  {'✅' if cm_pct <= 20 else '⚠️'} (cible ≤ 20%)")
    print(f"PULLBACK      : {pa_pct:.1f}%  {'✅' if 5 <= pa_pct <= 20 else '⚠️'} (cible 5-20%)")


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="B9 production test v5")
    parser.add_argument("db_path",    type=str, help="Chemin vers powerflow.db")
    parser.add_argument("--window",   type=int, default=50,            help="Taille fenêtre (défaut: 50)")
    parser.add_argument("--session",  type=str, default=None,          help="Filtre session (LONDON_OPEN / NY_OPEN / ...)")
    args = parser.parse_args()

    run_windows(args.db_path, window_size=args.window, session_filter=args.session)
