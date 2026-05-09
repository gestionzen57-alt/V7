import sqlite3
conn = sqlite3.connect("powerflow.db")
cur = conn.cursor()
cur.execute("SELECT timeframe, COUNT(*) FROM force_snapshots_v2 GROUP BY timeframe ORDER BY timeframe")
for row in cur.fetchall():
    print(f"  TF{row[0]:4d} -> {row[1]} snapshots")
conn.close()
