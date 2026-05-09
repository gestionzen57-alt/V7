import sqlite3

conn = sqlite3.connect("powerflow.db")

for table in ["force_snapshots", "force_snapshots_v2", "signals"]:
    print("\nTABLE", table)
    try:
        rows = conn.execute(f"""
            SELECT timeframe, COUNT(1), MAX(created_at)
            FROM {table}
            WHERE symbol='GBPUSD'
            GROUP BY timeframe
            ORDER BY timeframe
        """).fetchall()
        for row in rows:
            print(row)
    except Exception as e:
        print("ERROR", e)

conn.close()
