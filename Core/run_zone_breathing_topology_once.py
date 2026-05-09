import sqlite3
import numpy as np
from pf_zone_breathing_topology import detect_pullbacks, compute_scores

DB_PATH = "powerflow.db"

def load_series(limit=200):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # ⚠️ on enlève le filtre symbol pour éviter les erreurs
    cursor.execute("""
        SELECT force_eur
        FROM force_snapshots
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))

    rows = cursor.fetchall()
    conn.close()

    series = [r[0] for r in rows if r[0] is not None]
    series.reverse()
    return np.array(series)


def main():
    series = load_series()

    print("Nombre de points:", len(series))

    if len(series) == 0:
        print("❌ ERREUR: aucune donnée dans la DB")
        return

    # seuil dynamique SAFE
    threshold = np.percentile(np.abs(series), 85)

    pullbacks = detect_pullbacks(series, extreme_threshold=threshold)

    scores = compute_scores(pullbacks)

    print("\n=== ZONE BREATHING DIAGNOSTIC ===")
    print(f"pullbacks: {len(pullbacks)}")
    print(f"depth_drift: {scores['depth_drift']:.4f}")
    print(f"mean_duration: {scores['mean_duration']:.2f}")
    print(f"return_efficiency: {scores['return_efficiency']:.4f}")
    print(f"breathing_score: {scores['breathing_score']:.4f}")
    print(f"invalidation_pressure: {scores['invalidation_pressure']:.4f}")

    if scores["invalidation_pressure"] > 0.6:
        print("⚠️ LEAKING ZONE DETECTED")
    elif scores["breathing_score"] > 0.7:
        print("✅ HEALTHY BREATHING")
    else:
        print("… TRANSITION STATE")


if __name__ == "__main__":
    main()