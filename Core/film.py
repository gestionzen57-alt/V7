"""
film.py — PowerFlow Film Séquence DB
Rejoue une fenêtre temporelle avec toutes les briques actives.
Testé sur powerflow.db 06/05/2026.

Usage:
    python film.py --last 4h
    python film.py --today
    python film.py --from 08:00 --to 12:00 --date 2026-05-06
    python film.py --today --report
"""

import sqlite3
import argparse
import json
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


DB_DEFAULT = "powerflow.db"
SYMBOL_DEFAULT = "GBPUSD"

# Seuils détection (ajustables)
DETACHMENT_SHIFT_3   = 8.0    # shift M1 sur 3 bars → FIRST_DETACHMENT
FAST_DETACHMENT      = 15.0   # shift > 15 → FAST_BIRTH
COUNTER_THRESHOLD    = -5.0   # reversal après hausse → COUNTER_RELEASE_ATTEMPT
GAP_STRONG           = 15.0   # écart GBP-USD → champ fort
GAP_WEAK             = 5.0    # écart minimal
VOL_HIGH             = 100.0  # volume fort
VOL_LOW              = 30.0   # volume faible


def parse_args():
    p = argparse.ArgumentParser(description="PowerFlow Film Séquence DB")
    p.add_argument("--db", default=DB_DEFAULT)
    p.add_argument("--symbol", default=SYMBOL_DEFAULT)
    p.add_argument("--tf", type=int, default=1, help="Timeframe principal (défaut M1)")
    p.add_argument("--last", default=None, help="Ex: 4h, 8h, 1d")
    p.add_argument("--today", action="store_true", help="Journée courante 06/05")
    p.add_argument("--date", default=None, help="Date YYYY-MM-DD")
    p.add_argument("--from_time", default=None, dest="from_time", help="Heure début HH:MM")
    p.add_argument("--to_time", default=None, dest="to_time", help="Heure fin HH:MM")
    p.add_argument("--report", action="store_true", help="Sauvegarde rapport MD")
    p.add_argument("--out", default=None, help="JSON output optionnel")
    p.add_argument("--min-event", default="INFO", choices=["INFO","WATCH","HOT"],
                   help="Niveau minimum d'événement affiché")
    return p.parse_args()


def get_window(args) -> tuple[Optional[str], Optional[str]]:
    """Retourne (since_iso, until_iso) ou (None, None) pour tout."""
    now = datetime.now(timezone.utc)
    
    if args.today:
        # 06/05 = journée complète dans la DB
        date_str = "2026-05-06"
        return f"{date_str}T00:00:00+00:00", f"{date_str}T23:59:59+00:00"
    
    if args.date:
        date_str = args.date
        t_from = f"{args.from_time}:00" if args.from_time else "00:00:00"
        t_to   = f"{args.to_time}:00" if args.to_time else "23:59:59"
        return f"{date_str}T{t_from}+00:00", f"{date_str}T{t_to}+00:00"

    if args.last:
        m = re.match(r"(\d+)(h|d|m)", args.last)
        if not m:
            raise ValueError(f"Format --last invalide: {args.last}")
        n, unit = int(m.group(1)), m.group(2)
        if unit == "h":
            since = now - timedelta(hours=n)
        elif unit == "d":
            since = now - timedelta(days=n)
        else:
            since = now - timedelta(minutes=n)
        return since.isoformat(), now.isoformat()
    
    return None, None


def load_m1(db_path: str, since: Optional[str], until: Optional[str]) -> list[dict]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    if since and until:
        cur.execute("""
            SELECT created_at, force_gbp, force_usd, force_eur, force_jpy,
                   force_cad, force_chf, force_aud, tick_volume
            FROM force_snapshots_v2
            WHERE timeframe = 1 AND created_at >= ? AND created_at <= ?
            ORDER BY created_at
        """, (since, until))
    else:
        cur.execute("""
            SELECT created_at, force_gbp, force_usd, force_eur, force_jpy,
                   force_cad, force_chf, force_aud, tick_volume
            FROM force_snapshots_v2
            WHERE timeframe = 1
            ORDER BY created_at
        """)

    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


def load_m5(db_path: str, since: Optional[str], until: Optional[str]) -> list[dict]:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    if since and until:
        cur.execute("""
            SELECT created_at, force_gbp, force_usd, force_eur, force_jpy, tick_volume
            FROM force_snapshots_v2
            WHERE timeframe = 5 AND created_at >= ? AND created_at <= ?
            ORDER BY created_at
        """, (since, until))
    else:
        cur.execute("""
            SELECT created_at, force_gbp, force_usd, force_eur, force_jpy, tick_volume
            FROM force_snapshots_v2
            WHERE timeframe = 5
            ORDER BY created_at
        """)

    rows = [dict(r) for r in cur.fetchall()]
    con.close()
    return rows


@dataclass
class Event:
    ts: str
    level: str          # HOT / WATCH / INFO
    event_type: str     # FIRST_DETACHMENT, NODE_BIRTH, COUNTER_RELEASE_ATTEMPT, ...
    direction: str      # UP / DOWN / NEUTRAL
    gbp: float
    usd: float
    shift_3: float
    gap: float
    vol: float
    m5_relay: str       # CLEAN / THIN / MISSING
    notes: list[str] = field(default_factory=list)


def get_m5_relay_at(m5_bars: list[dict], ts: str) -> str:
    """Donne la qualité du relay M5 le plus proche avant ts."""
    ts_dt = ts[:16]
    candidates = [b for b in m5_bars if b["created_at"][:16] <= ts_dt]
    if not candidates:
        return "MISSING"
    recent = candidates[-1]
    vol = recent.get("tick_volume") or 0
    gbp = recent.get("force_gbp") or 0
    usd = recent.get("force_usd") or 0
    gap = gbp - usd
    if vol < VOL_LOW and abs(gap) < GAP_WEAK:
        return "THIN"
    if abs(gap) >= GAP_STRONG:
        return "CLEAN"
    return "THIN"


def compute_events(m1_bars: list[dict], m5_bars: list[dict]) -> list[Event]:
    """Détecte les événements PowerFlow sur la série M1."""
    events = []
    
    # État interne du film
    last_detach_dir = None
    last_detach_ts = None
    in_counter = False
    compression_count = 0
    prev_shift = 0.0

    for i, bar in enumerate(m1_bars):
        if i < 3:
            continue

        prev3 = m1_bars[i - 3]
        prev1 = m1_bars[i - 1]
        
        gbp = bar.get("force_gbp") or 0
        usd = bar.get("force_usd") or 0
        vol = bar.get("tick_volume") or 0
        gbp_prev3 = prev3.get("force_gbp") or 0
        usd_prev3 = prev3.get("force_usd") or 0
        gbp_prev1 = prev1.get("force_gbp") or 0

        shift_3 = gbp - gbp_prev3
        usd_shift_3 = usd - usd_prev3
        gap = gbp - usd
        ts = bar["created_at"]
        
        # Direction GBP
        direction = "UP" if shift_3 > 0 else ("DOWN" if shift_3 < 0 else "NEUTRAL")
        m5_relay = get_m5_relay_at(m5_bars, ts)

        notes = []

        # === FAST_BIRTH ===
        if abs(shift_3) >= FAST_DETACHMENT:
            level = "HOT"
            etype = "FAST_NODE_BIRTH"
            if vol >= VOL_HIGH:
                notes.append(f"vol_high={vol:.0f}")
            if m5_relay == "CLEAN":
                notes.append("M5_relay=CLEAN")
                etype = "FIRST_DETACHMENT_WITH_CLEAN_RELAY"
            events.append(Event(ts, level, etype, direction, gbp, usd, shift_3, gap, vol, m5_relay, notes))
            last_detach_dir = direction
            last_detach_ts = ts
            in_counter = False
            compression_count = 0

        # === FIRST_DETACHMENT ===
        elif abs(shift_3) >= DETACHMENT_SHIFT_3:
            level = "WATCH"
            etype = "NODE_BIRTH"
            if m5_relay == "CLEAN":
                level = "HOT" if abs(gap) >= GAP_STRONG else "WATCH"
                etype = "FIRST_DETACHMENT_WITH_CLEAN_RELAY" if level == "HOT" else "NODE_BIRTH"
            elif m5_relay == "MISSING":
                notes.append("M5_MISSING")
            
            if vol >= VOL_HIGH:
                notes.append(f"vol_high={vol:.0f}")
            
            events.append(Event(ts, level, etype, direction, gbp, usd, shift_3, gap, vol, m5_relay, notes))
            last_detach_dir = direction
            last_detach_ts = ts
            in_counter = False
            compression_count = 0

        # === COUNTER_RELEASE_ATTEMPT ===
        elif last_detach_dir and shift_3 * (-1 if last_detach_dir == "UP" else 1) >= 3.0:
            if not in_counter:
                level = "WATCH"
                etype = "COUNTER_RELEASE_ATTEMPT"
                if vol < VOL_LOW:
                    notes.append("low_vol → UNSUPPORTED")
                    etype = "COUNTER_RELEASE_UNSUPPORTED"
                events.append(Event(ts, level, etype, direction, gbp, usd, shift_3, gap, vol, m5_relay, notes))
                in_counter = True

        # === COMPRESSION (micro-oscillations serrées) ===
        elif abs(shift_3) < 2.0 and abs(prev_shift) < 2.0:
            compression_count += 1
            if compression_count == 4:
                notes.append(f"bars_compressed=4+")
                events.append(Event(ts, "INFO", "TIGHT_GRAVITY_CLUSTER", "NEUTRAL",
                                    gbp, usd, shift_3, gap, vol, m5_relay, notes))
                compression_count = 0  # reset pour éviter flood
        else:
            compression_count = 0

        prev_shift = shift_3

    return events


LEVEL_ORDER = {"HOT": 0, "WATCH": 1, "INFO": 2}

def level_icon(level: str) -> str:
    return {"HOT": "🔥", "WATCH": "👀", "INFO": "ℹ️"}.get(level, "·")

def dir_icon(direction: str) -> str:
    return {"UP": "↑", "DOWN": "↓", "NEUTRAL": "→"}.get(direction, "")

def relay_icon(relay: str) -> str:
    return {"CLEAN": "✅", "THIN": "⚠️", "MISSING": "❌"}.get(relay, "?")


def print_film(events: list[Event], min_level: str = "INFO"):
    min_order = LEVEL_ORDER.get(min_level, 2)
    visible = [e for e in events if LEVEL_ORDER.get(e.level, 2) <= min_order]

    print(f"\n{'='*72}")
    print(f"🎬 FILM POWERFLOW — {len(visible)} événements ({min_level}+)")
    print(f"{'='*72}\n")

    for e in visible:
        icon = level_icon(e.level)
        d = dir_icon(e.direction)
        r = relay_icon(e.m5_relay)
        notes_str = " | " + " ".join(e.notes) if e.notes else ""
        print(f"{icon} {e.ts[:16]}  {e.event_type:<42} {d} "
              f"GBP={e.gbp:5.1f} USD={e.usd:5.1f} shift={e.shift_3:+5.1f} "
              f"gap={e.gap:+5.1f} M5relay={r}{notes_str}")

    print(f"\n{'='*72}")
    hot_count = sum(1 for e in visible if e.level == "HOT")
    watch_count = sum(1 for e in visible if e.level == "WATCH")
    info_count = sum(1 for e in visible if e.level == "INFO")
    print(f"RÉSUMÉ : 🔥 HOT={hot_count} | 👀 WATCH={watch_count} | ℹ️ INFO={info_count}")


def save_report(events: list[Event], out_path: str, since: str, until: str):
    lines = [
        f"# FILM POWERFLOW — {since[:10] if since else 'ALL'}",
        f"**Généré**: {datetime.now(timezone.utc).isoformat()[:16]}",
        f"**Fenêtre**: {since[:16] if since else 'ALL'} → {until[:16] if until else 'ALL'}",
        "",
        "| Timestamp | Level | Event | Dir | GBP | USD | Shift3 | Gap | M5relay | Notes |",
        "|-----------|-------|-------|-----|-----|-----|--------|-----|---------|-------|",
    ]
    for e in events:
        notes = " / ".join(e.notes) if e.notes else ""
        lines.append(
            f"| {e.ts[:16]} | {e.level} | {e.event_type} | {e.direction} | "
            f"{e.gbp:.1f} | {e.usd:.1f} | {e.shift_3:+.1f} | {e.gap:+.1f} | "
            f"{e.m5_relay} | {notes} |"
        )
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text("\n".join(lines))
    print(f"\n📄 Rapport → {out_path}")


def main():
    args = parse_args()
    db_path = args.db

    if not Path(db_path).exists():
        print(f"❌ DB introuvable: {db_path}")
        return

    since, until = get_window(args)

    print(f"\n🎬 FILM POWERFLOW")
    print(f"DB     : {db_path}")
    print(f"Fenêtre: {(since or 'ALL')[:16]} → {(until or 'ALL')[:16]}")

    m1_bars = load_m1(db_path, since, until)
    m5_bars = load_m5(db_path, since, until)

    if not m1_bars:
        print("❌ Aucune donnée M1 pour cette fenêtre.")
        return

    print(f"M1: {len(m1_bars)} bars | M5: {len(m5_bars)} bars")

    events = compute_events(m1_bars, m5_bars)
    print_film(events, min_level=args.min_event)

    if args.report:
        ts_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        out_path = f"output/film_report_{ts_str}.md"
        save_report(events, out_path, since or "ALL", until or "ALL")

    if args.out:
        data = [
            {
                "ts": e.ts, "level": e.level, "event": e.event_type,
                "direction": e.direction, "gbp": e.gbp, "usd": e.usd,
                "shift_3": e.shift_3, "gap": e.gap, "vol": e.vol,
                "m5_relay": e.m5_relay, "notes": e.notes
            }
            for e in events
        ]
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(json.dumps(data, indent=2))
        print(f"💾 JSON → {args.out}")


if __name__ == "__main__":
    main()
