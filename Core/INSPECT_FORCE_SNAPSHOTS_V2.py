import sqlite3

con = sqlite3.connect("powerflow.db")
cur = con.cursor()

print("="*80)
print("LEGACY force_snapshots by timeframe")
cur.execute("""
SELECT timeframe, COUNT(*), MIN(created_at), MAX(created_at)
FROM force_snapshots
GROUP BY timeframe
ORDER BY timeframe
""")
for row in cur.fetchall():
    print(row)

print("="*80)
print("V2 force_snapshots_v2 by timeframe")
cur.execute("""
SELECT timeframe, COUNT(*), MIN(created_at), MAX(created_at)
FROM force_snapshots_v2
GROUP BY timeframe
ORDER BY timeframe
""")
for row in cur.fetchall():
    print(row)

print("="*80)
print("V2 non-null field check")
fields = [
    "force_nzd", "open", "high", "low", "close", "tick_volume",
    "pip_range", "pip_body", "pip_change",
    "spread_points", "spread_price", "spread_pips",
    "bid", "ask", "mid",
    "bar_time", "bar_close_time", "server_time", "capture_time", "is_closed_bar"
]
for f in fields:
    cur.execute(f"SELECT COUNT(*) FROM force_snapshots_v2 WHERE {f} IS NOT NULL")
    print(f, cur.fetchone()[0])

print("="*80)
print("Last V2 rows full")
cur.execute("""
SELECT *
FROM force_snapshots_v2
ORDER BY id DESC
LIMIT 10
""")
cols = [d[0] for d in cur.description]
print(cols)
for row in cur.fetchall():
    print(row)

con.close()
