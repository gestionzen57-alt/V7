import sqlite3

conn = sqlite3.connect("powerflow.db")
q = """
SELECT timeframe, COUNT(*), MAX(created_at)
FROM force_snapshots
WHERE symbol = ?
GROUP BY timeframe
ORDER BY timeframe
"""
for row in conn.execute(q, ("GBPUSD",)).fetchall():
    print(row)
conn.close()
