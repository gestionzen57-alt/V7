import sqlite3
import os

db_path = "powerflow.db"

if not os.path.exists(db_path):
    print(f"❌ powerflow.db introuvable dans : {os.getcwd()}")
    exit()

print(f"✅ powerflow.db trouvé")
print(f"   Taille : {os.path.getsize(db_path) / 1024:.1f} Ko")
print()

conn = sqlite3.connect(db_path)
c = conn.cursor()

# Tables existantes
print("=== TABLES DISPONIBLES ===")
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
for t in tables:
    print(f"  - {t[0]}")

print()

# force_snapshots
print("=== FORCE_SNAPSHOTS (paires et timeframes) ===")
try:
    c.execute("SELECT symbol, timeframe, COUNT(*) as nb FROM force_snapshots GROUP BY symbol, timeframe ORDER BY symbol, timeframe")
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]} | TF{row[1]} | {row[2]} lignes")
    else:
        print("  ❌ Aucune donnée")
except Exception as e:
    print(f"  ❌ Erreur : {e}")

print()

# Dernière entrée
print("=== DERNIERE ENTREE force_snapshots ===")
try:
    c.execute("SELECT symbol, timeframe, created_at FROM force_snapshots ORDER BY created_at DESC LIMIT 5")
    rows = c.fetchall()
    for row in rows:
        print(f"  {row[0]} | TF{row[1]} | {row[2]}")
except Exception as e:
    print(f"  ❌ Erreur : {e}")

print()

# Signaux récents
print("=== SIGNAUX RECENTS (15 dernières lignes) ===")
try:
    c.execute("SELECT symbol, timeframe, signal_type, created_at FROM signals ORDER BY created_at DESC LIMIT 15")
    rows = c.fetchall()
    if rows:
        for row in rows:
            print(f"  {row[0]} | M{row[1]} | {row[2]} | {row[3]}")
    else:
        print("  ❌ Aucun signal en DB")
except Exception as e:
    print(f"  ❌ Erreur : {e}")

conn.close()
print()
print("=== FIN DU DIAGNOSTIC ===")
