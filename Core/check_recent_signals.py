import sqlite3

conn = sqlite3.connect("powerflow.db")
rows = conn.execute("""
SELECT created_at, symbol, timeframe, signal_type
FROM signals
ORDER BY created_at DESC
LIMIT 10
""").fetchall()

for row in rows:
    print(row)

conn.close()
