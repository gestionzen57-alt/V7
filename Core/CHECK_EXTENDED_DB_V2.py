#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sqlite3
from pathlib import Path

db = Path("powerflow.db")
table = "force_snapshots_v2"

if not db.exists():
    raise SystemExit("Missing powerflow.db")

con = sqlite3.connect(str(db))
cur = con.cursor()

print("=" * 90)
print("DB:", db)

cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
print("TABLES:")
for t in tables:
    print(" -", t)

if table not in tables:
    con.close()
    raise SystemExit("ERROR: force_snapshots_v2 not found")

print("=" * 90)
print("FORCE_SNAPSHOTS_V2 COLUMNS:")
cur.execute(f"PRAGMA table_info({table})")
for r in cur.fetchall():
    print(" -", r[1], r[2])

print("=" * 90)
print("FORCE_SNAPSHOTS_V2 RANGE:")
cur.execute(f"SELECT MIN(created_at), MAX(created_at), COUNT(*) FROM {table}")
print(cur.fetchone())

print("=" * 90)
print("LAST 5 FORCE_SNAPSHOTS_V2:")
cur.execute(f"""
    SELECT created_at, symbol, timeframe, bid, ask, mid, close, tick_volume,
           spread_points, spread_pips,
           force_gbp, force_usd, force_eur, force_jpy,
           force_cad, force_chf, force_aud, force_nzd
    FROM {table}
    ORDER BY created_at DESC, id DESC
    LIMIT 5
""")
print("COLUMNS:", [d[0] for d in cur.description])
for row in cur.fetchall():
    print(row)

con.close()
print("=" * 90)
print("VERDICT: force_snapshots_v2 ready. After bridge receives new payload, rows should appear here.")
