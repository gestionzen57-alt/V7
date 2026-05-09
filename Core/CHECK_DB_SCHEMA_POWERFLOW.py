import sqlite3
from pathlib import Path

paths = ["powerflow.db", "db/powerflow.db"]

for path in paths:
    print("=" * 90)
    print("DB:", path)

    if not Path(path).exists():
        print("MISSING")
        continue

    try:
        con = sqlite3.connect(path)
        cur = con.cursor()

        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print("TABLES:")
        for t in tables:
            print(" -", t)

        if "force_snapshots" in tables:
            print("\nFORCE_SNAPSHOTS COLUMNS:")
            cur.execute("PRAGMA table_info(force_snapshots)")
            cols = cur.fetchall()
            for r in cols:
                print(" -", r[1], r[2])

            print("\nFORCE_SNAPSHOTS RANGE:")
            cur.execute("SELECT MIN(created_at), MAX(created_at), COUNT(*) FROM force_snapshots")
            print(cur.fetchone())

            print("\nLAST 5 FORCE SNAPSHOTS:")
            cur.execute("""
                SELECT *
                FROM force_snapshots
                ORDER BY created_at DESC
                LIMIT 5
            """)
            colnames = [d[0] for d in cur.description]
            print("COLUMNS:", colnames)
            for row in cur.fetchall():
                print(row)

        con.close()

    except Exception as e:
        print("ERROR:", e)
