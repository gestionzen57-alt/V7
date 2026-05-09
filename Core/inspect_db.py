import sqlite3

conn = sqlite3.connect("powerflow.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cur.fetchall()]
print(f"Tables ({len(tables)}) :")
for t in tables:
    print(f"\n  [{t}]")
    cur.execute(f"PRAGMA table_info({t})")
    for col in cur.fetchall():
        print(f"    {col[1]}  ({col[2]})")

conn.close()