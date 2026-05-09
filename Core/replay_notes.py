#!/usr/bin/env python3
"""
replay_notes.py — Rejoue tes notes avec ce qui s'est passé après

Usage:
    python replay_notes.py --today
    python replay_notes.py --last 4h
    python replay_notes.py --all
    python replay_notes.py --note 5  # note #5

Pour chaque note :
    - Affiche ton intuition
    - Affiche le DB state du moment
    - Rejoue les 30 min suivantes
    - Te montre si tu avais raison
"""

import json
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Config
NOTES_PATH = Path("output/trader_notes.json")
DB_PATH = Path("powerflow.db")

def load_notes():
    """Charge toutes les notes."""
    if not NOTES_PATH.exists():
        print(f"❌ Pas de notes trouvées dans {NOTES_PATH}")
        return []
    
    with open(NOTES_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def filter_notes(notes, mode, value=None):
    """Filtre les notes selon le mode."""
    now = datetime.now(timezone.utc)
    
    if mode == "all":
        return notes
    
    elif mode == "today":
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return [n for n in notes if datetime.fromisoformat(n["timestamp"]) >= today_start]
    
    elif mode == "last":
        # value = "4h" → timedelta
        if value.endswith("h"):
            hours = int(value[:-1])
            cutoff = now - timedelta(hours=hours)
        elif value.endswith("m"):
            minutes = int(value[:-1])
            cutoff = now - timedelta(minutes=minutes)
        else:
            cutoff = now - timedelta(hours=4)  # défaut
        
        return [n for n in notes if datetime.fromisoformat(n["timestamp"]) >= cutoff]
    
    elif mode == "note":
        # value = 5 → note #5
        idx = int(value) - 1
        if 0 <= idx < len(notes):
            return [notes[idx]]
        return []
    
    return notes

def get_bars_after(db_path: Path, timestamp: str, symbol: str, timeframe: str, minutes_after: int = 30):
    """Récupère les bars qui ont suivi la note."""
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # timestamp note
        note_time = datetime.fromisoformat(timestamp)
        after_time = note_time + timedelta(minutes=minutes_after)
        
        cursor.execute("""
            SELECT created_at, bid, spread, force_gbp, force_usd
            FROM force_snapshots
            WHERE symbol = ?
              AND timeframe = ?
              AND created_at >= ?
              AND created_at <= ?
            ORDER BY created_at ASC
        """, (symbol, timeframe, timestamp, after_time.isoformat()))
        
        bars = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return bars
    
    except Exception as e:
        return {"error": str(e)}

def analyze_aftermath(bars_m1, note_text):
    """Analyse ce qui s'est passé après."""
    if not bars_m1 or isinstance(bars_m1, dict):
        return "❌ Pas de données DB après cette note"
    
    if len(bars_m1) < 2:
        return "⚠️ Pas assez de bars après pour analyser"
    
    # Prix mouvement
    first_bid = bars_m1[0]["bid"]
    max_bid = max(b["bid"] for b in bars_m1)
    min_bid = min(b["bid"] for b in bars_m1)
    last_bid = bars_m1[-1]["bid"]
    
    pip_high = (max_bid - first_bid) * 10000
    pip_low = (first_bid - min_bid) * 10000
    pip_net = (last_bid - first_bid) * 10000
    
    # Force mouvement
    first_gbp = bars_m1[0]["force_gbp"]
    last_gbp = bars_m1[-1]["force_gbp"]
    gbp_delta = last_gbp - first_gbp
    
    first_usd = bars_m1[0]["force_usd"]
    last_usd = bars_m1[-1]["force_usd"]
    usd_delta = last_usd - first_usd
    
    # Direction détectée dans la note
    direction_hint = None
    if "haut" in note_text.lower() or "up" in note_text.lower() or "monte" in note_text.lower():
        direction_hint = "UP"
    elif "bas" in note_text.lower() or "down" in note_text.lower() or "baisse" in note_text.lower():
        direction_hint = "DOWN"
    
    # Résultat
    result = f"""
    Prix après 30 min :
      High : +{pip_high:.1f} pips
      Low  : -{pip_low:.1f} pips
      Net  : {pip_net:+.1f} pips
    
    Force après 30 min :
      GBP : {gbp_delta:+.3f}
      USD : {usd_delta:+.3f}
    """
    
    # Validation intuition
    if direction_hint == "UP" and pip_net > 3:
        result += "\n    ✅ Ton intuition était JUSTE (mouvement UP confirmé)"
    elif direction_hint == "DOWN" and pip_net < -3:
        result += "\n    ✅ Ton intuition était JUSTE (mouvement DOWN confirmé)"
    elif direction_hint and abs(pip_net) < 2:
        result += "\n    ⚠️ Mouvement plat (intuition non confirmée)"
    elif direction_hint:
        result += "\n    ❌ Mouvement inverse à ton intuition"
    else:
        result += f"\n    📊 Mouvement : {pip_net:+.1f} pips"
    
    return result

def replay_note(note, idx):
    """Rejoue une note."""
    print("\n" + "="*80)
    print(f"📝 NOTE #{idx+1}")
    print("="*80)
    
    timestamp = note["timestamp"]
    dt = datetime.fromisoformat(timestamp)
    
    print(f"\n🕐 Timestamp : {dt.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print(f"💭 Intuition : \"{note['note']}\"")
    
    # DB state du moment
    db_state = note.get("db_state", {})
    m1 = db_state.get("m1")
    m5 = db_state.get("m5")
    
    if m1:
        print(f"\n📊 DB State (moment de la note) :")
        print(f"  M1 : bid={m1.get('bid', 'N/A'):.5f} | GBP={m1.get('force_gbp', 0):.3f} | USD={m1.get('force_usd', 0):.3f}")
        if m5:
            print(f"  M5 : bid={m5.get('bid', 'N/A'):.5f} | GBP={m5.get('force_gbp', 0):.3f} | USD={m5.get('force_usd', 0):.3f}")
    
    # Ce qui s'est passé après
    symbol = note.get("symbol", "GBPUSD")
    bars_m1 = get_bars_after(DB_PATH, timestamp, symbol, "1", minutes_after=30)
    
    print(f"\n🎬 Ce qui s'est passé après :")
    aftermath = analyze_aftermath(bars_m1, note['note'])
    print(aftermath)

def main():
    parser = argparse.ArgumentParser(description="Rejoue tes notes trader")
    parser.add_argument("--all", action="store_true", help="Toutes les notes")
    parser.add_argument("--today", action="store_true", help="Notes d'aujourd'hui")
    parser.add_argument("--last", type=str, help="Dernières X heures (ex: 4h)")
    parser.add_argument("--note", type=int, help="Note spécifique (ex: 5)")
    
    args = parser.parse_args()
    
    # Load notes
    notes = load_notes()
    if not notes:
        return
    
    # Filter
    if args.today:
        filtered = filter_notes(notes, "today")
    elif args.last:
        filtered = filter_notes(notes, "last", args.last)
    elif args.note:
        filtered = filter_notes(notes, "note", str(args.note))
    elif args.all:
        filtered = notes
    else:
        # Défaut : today
        filtered = filter_notes(notes, "today")
    
    if not filtered:
        print("❌ Aucune note trouvée avec ces critères")
        return
    
    print(f"\n🎯 {len(filtered)} note(s) trouvée(s)\n")
    
    # Replay chaque note
    for idx, note in enumerate(filtered):
        # Trouve l'index réel dans la liste complète
        real_idx = notes.index(note)
        replay_note(note, real_idx)
    
    print("\n" + "="*80)
    print("✅ Replay terminé")

if __name__ == "__main__":
    main()
