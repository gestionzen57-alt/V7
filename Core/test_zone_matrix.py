import sqlite3
from pf_zone_dynamics import analyze_zone_dynamics

db = "powerflow.db"
conn = sqlite3.connect(db)
cur = conn.cursor()

currencies = {"EUR":"force_eur","GBP":"force_gbp","JPY":"force_jpy","CHF":"force_chf","AUD":"force_aud"}

print(f"{'CCY':4s} {'TF':4s} {'state':22s} {'z':>8s} {'profile':8s}")
print("-" * 55)
for cur_name, col in currencies.items():
    for tf, bars in [(15,30),(30,25),(60,20)]:
        conn2 = sqlite3.connect(db)
        c2 = conn2.cursor()
        c2.execute(f"SELECT {col} FROM force_snapshots_v2 WHERE timeframe=? ORDER BY created_at DESC LIMIT ?", (tf, bars))
        rows = [r[0] for r in reversed(c2.fetchall())]
        conn2.close()
        diag = analyze_zone_dynamics(rows, timeframe=tf, currency=cur_name)
        print(f"{cur_name:4s} TF{tf:<3d} {diag.state:22s} z={diag.z_current:+8.2f} {diag.profile_name}")
    print()

conn.close()
