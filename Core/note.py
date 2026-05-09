#!/usr/bin/env python3
"""
note.py — Capture intuition trader pendant le trading

Usage:
    python note.py "compression GBP 6 bars, spread stable, je sens libération haut"
    python note.py "USD faible, angle plat, pas convaincu"
    python note.py "M1 détache, M5 clean, energy GBP fort, GO"

Capture:
    - timestamp exact
    - ton intuition (texte libre)
    - DB state du moment (dernier bar M1/M5/M15)
    - force snapshots actuelles
    
Output: output/trader_notes.json
"""

import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

# Config
DB_PATH = Path("powerflow.db")
OUTPUT_PATH = Path("output/trader_notes.json")

def get_latest_db_state(db_path: Path, symbol: str = "GBPUSD") -> dict:
    """Récupère le dernier état DB pour contexte."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Dernier bar M1
        cursor.execute("""
            SELECT created_at, timeframe, bid, spread,
                   force_gbp, force_usd, force_eur, force_jpy
            FROM force_snapshots
            WHERE symbol = ? AND timeframe = '1'
            ORDER BY created_at DESC
            LIMIT 1
        """, (symbol,))
        m1 = dict(cursor.fetchone()) if cursor.fetchone() else None
        
        # Dernier bar M5
        cursor.execute("""
            SELECT created_at, timeframe, bid, spread,
                   force_gbp, force_usd
            FROM force_snapshots
            WHERE symbol = ? AND timeframe = '5'
            ORDER BY created_at DESC
            LIMIT 1
        """, (symbol,))
        m5 = dict(cursor.fetchone()) if cursor.fetchone() else None
        
        # Dernier bar M15
        cursor.execute("""
            SELECT created_at, timeframe, bid, spread,
                   force_gbp, force_usd
            FROM force_snapshots
            WHERE symbol = ? AND timeframe = '15'
            ORDER BY created_at DESC
            LIMIT 1
        """, (symbol,))
        m15 = dict(cursor.fetchone()) if cursor.fetchone() else None
        
        conn.close()
        
        return {
            "m1": m1,
            "m5": m5,
            "m15": m15,
        }
    except Exception as e:
        return {"error": str(e)}

def capture_note(note_text: str, symbol: str = "GBPUSD"):
    """Capture note + timestamp + DB state."""
    
    # Timestamp
    now = datetime.now(timezone.utc)
    timestamp_iso = now.isoformat()
    
    # DB state
    db_state = get_latest_db_state(DB_PATH, symbol)
    
    # Note complète
    note = {
        "timestamp": timestamp_iso,
        "note": note_text,
        "symbol": symbol,
        "db_state": db_state,
    }
    
    # Load existing notes
    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    if OUTPUT_PATH.exists():
        with open(OUTPUT_PATH, 'r', encoding='utf-8') as f:
            notes = json.load(f)
    else:
        notes = []
    
    # Append
    notes.append(note)
    
    # Save
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(notes, f, indent=2, ensure_ascii=False)
    
    # Confirmation
    print(f"✅ Note capturée : {timestamp_iso}")
    print(f"📝 '{note_text}'")
    print(f"💾 Sauvegardée dans {OUTPUT_PATH}")
    print(f"📊 Total notes : {len(notes)}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python note.py \"ton intuition ici\"")
        print("\nExemples:")
        print("  python note.py \"compression GBP 6 bars, je sens libération haut\"")
        print("  python note.py \"USD faible, pas convaincu\"")
        print("  python note.py \"M1 détache, M5 clean, GO\"")
        sys.exit(1)
    
    note_text = " ".join(sys.argv[1:])
    capture_note(note_text)

if __name__ == "__main__":
    main()
