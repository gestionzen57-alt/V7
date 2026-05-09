# ============================================================
# PowerFlow V5 — bridge.py
# Collecteur pur — adapté au nouveau format EA V5
#
# Changements vs V4 :
#  - parse_tick V5 : lit directement les 8 forces sans paire
#  - maybe_store_force_snapshot : stocke par bar_time (bougie fermée)
#  - Anti-doublon par (symbol, timeframe, bar_time) → ZERO redondance DB
#  - Compatibilité V4 maintenue (fallback si champs V4 présents)
# ============================================================

import asyncio
import json
import time
from datetime import datetime, timezone
from models import Tick, Brain
from db import init_db, insert_force_snapshot
from system_config import (
    TCP_HOST, TCP_PORT, PAIRS, DEBUG_CROSS,
    DB_PATH, FORCE_SNAPSHOTS_ENABLED,
)

CURRENCIES = ("GBP", "USD", "EUR", "JPY", "CAD", "CHF", "AUD", "NZD")

# Clé = (symbol, tf, bar_time) → évite les doublons par bougie fermée
_SNAPSHOT_SEEN = {}

SNAPSHOT_DB_CONN = init_db(DB_PATH) if FORCE_SNAPSHOTS_ENABLED else None


# ============================================================
# PARSE TICK — compatible V5 et V4
# ============================================================
def parse_tick(raw: dict):
    try:
        symbol = raw.get("symbol", "").upper()
        tf = int(raw.get("tf", raw.get("timeframe", 0)))
        if not symbol or tf == 0:
            return None

        # V5 : pas de filtre PAIRS strict — on accepte tout symbole valide
        # (le filtre métier est dans engine.py)

        # Lecture des forces — V5 envoie directement les 8 clés
        gbp = safe_f(raw.get("gbp"))
        usd = safe_f(raw.get("usd"))
        eur = safe_f(raw.get("eur"))
        jpy = safe_f(raw.get("jpy"))
        cad = safe_f(raw.get("cad"))
        chf = safe_f(raw.get("chf"))
        aud = safe_f(raw.get("aud"))
        nzd = safe_f(raw.get("nzd"))

        if gbp is None and usd is None:
            return None  # données inutilisables

        # dev_A / dev_B : on les déduit du symbole si absents (compat V4)
        dev_a = raw.get("dev_A", raw.get("devA", symbol[:3])).lower()
        dev_b = raw.get("dev_B", raw.get("devB", symbol[3:6])).lower()

        forces = {"gbp": gbp, "usd": usd, "eur": eur, "jpy": jpy,
                  "cad": cad, "chf": chf, "aud": aud, "nzd": nzd}
        val_a = forces.get(dev_a)
        val_b = forces.get(dev_b)
        if val_a is None: val_a = 50.0
        if val_b is None: val_b = 50.0

        # Champs optionnels (absents en V5, conservés pour compat V4)
        bid    = safe_f(raw.get("bid", raw.get("close", 0.0))) or 0.0
        spread = safe_f(raw.get("spread", raw.get("spread_points", 0.0))) or 0.0
        volume = int(raw.get("tick_volume", raw.get("volume", 0)) or 0)
        atr    = safe_f(raw.get("atr", 0.0)) or 0.0

        return Tick(
            symbol=symbol, timeframe=tf, timestamp=datetime.now(),
            dev_a=dev_a, dev_b=dev_b, val_a=val_a, val_b=val_b,
            bid=bid, spread=spread, volume=volume, atr=atr,
        )
    except Exception as e:
        print(f"❌ parse_tick : {e}")
        return None


# ============================================================
# STORE SNAPSHOT — par bougie fermée (bar_time), zéro doublon
# ============================================================
def maybe_store_force_snapshot(raw: dict, tick: Tick):
    if not FORCE_SNAPSHOTS_ENABLED or SNAPSHOT_DB_CONN is None:
        return

    # Clé d'unicité : symbol + tf + bar_time (bougie fermée)
    bar_time = raw.get("bar_time", 0)
    dedup_key = f"{tick.symbol}_{tick.timeframe}_{bar_time}"

    if dedup_key in _SNAPSHOT_SEEN:
        return  # déjà enregistré pour cette bougie

    # Horodatage : on utilise bar_time si disponible (heure exacte de la bougie)
    if bar_time and int(bar_time) > 0:
        try:
            created_at = datetime.fromtimestamp(int(bar_time), tz=timezone.utc).isoformat()
        except Exception:
            created_at = datetime.now(timezone.utc).isoformat()
    else:
        created_at = datetime.now(timezone.utc).isoformat()

    snapshot = {
        "created_at":  created_at,
        "symbol":      tick.symbol,
        "timeframe":   tick.timeframe,
        "bid": _sf(raw.get("bid")),
        "spread":      _sf(raw.get("spread")),
        "force_gbp":   safe_f(raw.get("gbp")),
        "force_usd":   safe_f(raw.get("usd")),
        "force_eur":   safe_f(raw.get("eur")),
        "force_jpy":   safe_f(raw.get("jpy")),
        "force_cad":   safe_f(raw.get("cad")),
        "force_chf":   safe_f(raw.get("chf")),
        "force_aud":   safe_f(raw.get("aud")),
        "force_nzd":   safe_f(raw.get("nzd")),

        # EA extended payload - stored in force_snapshots_v2 when db.py supports it.
        "open":        _sf(raw.get("open")),
        "high":        _sf(raw.get("high")),
        "low":         _sf(raw.get("low")),
        "close":       _sf(raw.get("close")),
        "tick_volume": _sf(raw.get("tick_volume", raw.get("volume"))),

        "pip_range":   _sf(raw.get("pip_range")),
        "pip_body":    _sf(raw.get("pip_body")),
        "pip_change":  _sf(raw.get("pip_change")),

        "spread_points": _sf(raw.get("spread_points")),
        "spread_price":  _sf(raw.get("spread_price")),
        "spread_pips":   _sf(raw.get("spread_pips")),

        "ask":         _sf(raw.get("ask")),
        "mid":         _sf(raw.get("mid")),

        "bar_time":       _sf(raw.get("bar_time")),
        "bar_close_time": _sf(raw.get("bar_close_time")),
        "server_time":    _sf(raw.get("server_time")),
        "capture_time":   _sf(raw.get("capture_time")),
        "is_closed_bar":  raw.get("is_closed_bar"),
    }

    inserted = insert_force_snapshot(SNAPSHOT_DB_CONN, snapshot)
    if inserted is not None:
        _SNAPSHOT_SEEN[dedup_key] = True
        if DEBUG_CROSS:
            print(f"✅ Snapshot: {tick.symbol} M{tick.timeframe} bar={created_at[:16]}")


# ============================================================
# HELPERS
# ============================================================
def safe_f(value):
    try:
        v = float(value)
    except Exception:
        return None
    if v != v: return None
    if v in (2147483647.0, -2147483648.0): return None
    if v < -1000 or v > 1000: return None
    return v

def _sf(value):
    if value is None: return None
    try:
        v = float(value)
        return None if v != v else v
    except Exception:
        return None


# ============================================================
# SERVEUR TCP ASYNC
# ============================================================
async def handle_connection(reader, writer, brain, on_tick):
    buffer = ""
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            buffer += data.decode("utf-8", errors="ignore")
            line = buffer.strip()
            if not line:
                return
            try:
                raw = json.loads(line)
            except json.JSONDecodeError:
                return
                
            if DEBUG_CROSS:
                print(
                    "[RAW]",
                    "symbol=", raw.get("symbol"),
                    "tf=", raw.get("tf"),
                    "timeframe=", raw.get("timeframe"),
                    "bar_time=", raw.get("bar_time"),
                    "close=", raw.get("close"),
                    "bid=", raw.get("bid"),
                    "ask=", raw.get("ask"),
                    "nzd=", raw.get("nzd"),
                    "tick_volume=", raw.get("tick_volume"),
                    "keys=", sorted(raw.keys())
                )

            tick = parse_tick(raw)
            if tick is None:
                return

            key  = f"{tick.symbol}M{tick.timeframe}"
            prev = brain.get(key)
            brain[key] = tick

            maybe_store_force_snapshot(raw, tick)

            if prev is not None:
                await on_tick(tick, prev, brain)

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"❌ handle_connection : {e}")
    finally:
        writer.close()


async def start_bridge(brain, on_tick):
    server = await asyncio.start_server(
        lambda r, w: handle_connection(r, w, brain, on_tick),
        TCP_HOST, TCP_PORT
    )
    addr = server.sockets[0].getsockname()
    print(f"🚀 Bridge V5 TCP prêt — {addr[0]}:{addr[1]}")
    print(f"   Devises : {', '.join(CURRENCIES)}")
    async with server:
        await server.serve_forever()


# ============================================================
# MAIN (test standalone)
# ============================================================
from engine import process_tick

async def dummy_send_alert(sig, htf, brain):
    print(f"🔔 ALERT {sig.signal_type} {sig.symbol} M{sig.timeframe}")

async def on_tick(tick, prev, brain):
    await process_tick(tick, prev, brain, dummy_send_alert)

if __name__ == "__main__":
    brain = {}
    print("🚀 Bridge TCP PowerFlow V5 lancé")
    asyncio.run(start_bridge(brain, on_tick))
