import sqlite3
from pathlib import Path

wanted = [
    "force_nzd", "open", "high", "low", "close", "tick_volume",
    "pip_range", "pip_body", "pip_change",
    "spread_points", "spread_price", "spread_pips",
    "ask", "mid", "bar_time", "bar_close_time",
    "server_time", "capture_time", "is_closed_bar"
]

for db in Path(".").rglob("*.db"):
    print("=" * 100)
    print("DB:", db)
    try:
        con = sqlite3.connect(str(db))
        cur = con.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
        print("TABLES:", tables)

        found_any = False
        for table in tables:
            cur.execute(f"PRAGMA table_info({table})")
            cols = [r[1] for r in cur.fetchall()]
            hits = [c for c in cols if c.lower() in wanted or any(w in c.lower() for w in wanted)]
            if hits:
                found_any = True
                print("MATCH TABLE:", table)
                print("COLUMNS:", cols)
                print("HITS:", hits)

        if not found_any:
            print("No EA extended columns found.")

        con.close()
    except Exception as e:
        print("ERROR:", e)
