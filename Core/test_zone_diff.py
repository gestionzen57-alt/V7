import sqlite3
from pf_zone_dynamics import analyze_zone_dynamics

db = "powerflow.db"
col = "force_eur"

conn = sqlite3.connect(db)
cur = conn.cursor()

for tf, bars in [(15, 30), (30, 25), (60, 20)]:
    cur.execute(f"SELECT {col} FROM force_snapshots_v2 WHERE timeframe=? ORDER BY created_at DESC LIMIT ?", (tf, bars))
    rows = [r[0] for r in reversed(cur.fetchall())]
    diag = analyze_zone_dynamics(rows, timeframe=tf, currency="EUR")
    print(f"TF{tf:2d} | n={len(rows):2d} | state={diag.state:20s} | z={diag.z_current:+.3f} | profile={diag.profile_name}")

conn.close()
