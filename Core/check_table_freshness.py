import sqlite3

conn = sqlite3.connect("powerflow.db")

tables = ["force_snapshots", "force_snapshots_v2", "signals"]

for table in tables:
    try:
        count, latest = conn.execute(
            f"SELECT COUNT(1), MAX(created_at) FROM {table}"
        ).fetchone()
        print((table, count, latest))
    except Exception as e:
        print((table, "ERROR", str(e)))

conn.close()
