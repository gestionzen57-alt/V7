"""
PowerFlow V6 - run_confluence_alert.py
Version: V0.1.2 — EIE persistance + fractalité zone + Relational Gravity bridge

Mission:
    Daemon live — scan toutes les 5 min, detecte EIE persistant,
    enrichit avec la fractalité zone + contexte Relational Gravity,
    envoie alerte Telegram via telegram_trader_alert_v01.

Usage:
    python run_confluence_alert.py
    python run_confluence_alert.py --zone-tf 30
    python run_confluence_alert.py --dry-run
    python run_confluence_alert.py --once
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from pf_tension_signature import compute_tension_signature
from pf_zone_dynamics import analyze_zone_dynamics
from pf_confluence_gravity import analyze_confluence_gravity
from telegram_trader_alert_v01 import send_telegram_message, load_env_file

# ==========================================================================
# CONFIG
# ==========================================================================

DEFAULT_DB       = "powerflow.db"
TABLE_SNAP       = "force_snapshots_v2"
TS_COL           = "created_at"
TF_COL           = "timeframe"

CROSS_TF_PAIRS   = [(1, 8), (5, 8)]
DEFAULT_ZONE_TF  = 15
ZONE_BARS        = 30
FRACTAL_TFS      = [(15, 30), (30, 25), (60, 20)]  # (tf, bars)
SCAN_INTERVAL_S  = 300        # 5 minutes
MIN_PERSIST      = 2          # snapshots consecutifs minimum
COOLDOWN_S       = 600        # 10 min anti-spam par devise

ENV_PATH         = Path(".env")
LAST_ALERT_PATH  = Path("output/confluence_alert_last.json")

ZONE_ACTIVE_STATES = {"ACCUMULATING", "EXTREME", "EARLY_EXTREME", "LEAKING"}

CURRENCIES = {
    "GBP": "force_gbp",
    "USD": "force_usd",
    "EUR": "force_eur",
    "JPY": "force_jpy",
    "CAD": "force_cad",
    "CHF": "force_chf",
    "AUD": "force_aud",
    "NZD": "force_nzd",
}


# ==========================================================================
# HELPERS
# ==========================================================================

def detect_session(dt_utc: datetime) -> str:
    h = dt_utc.hour
    if 0 <= h < 7:
        return "ASIA"
    if 7 <= h < 9:
        return "LONDON_OPEN"
    if 9 <= h < 13:
        return "LONDON"
    if 13 <= h < 16:
        return "PRE_US"
    if 16 <= h < 21:
        return "US"
    return "US_CLOSE"


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso_now() -> str:
    return now_utc().isoformat(timespec="seconds")


def fetch_series(
    db_path: str,
    force_col: str,
    timeframe: int,
    bars: int,
) -> List[Optional[float]]:
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            f"SELECT {force_col} FROM {TABLE_SNAP} "
            f"WHERE {TF_COL}=? "
            f"ORDER BY {TS_COL} DESC LIMIT ?",
            (timeframe, bars),
        )
        rows = cur.fetchall()
        conn.close()
        return [row[0] for row in reversed(rows)]
    except sqlite3.Error as e:
        print(f"[DB ERROR] {force_col} TF{timeframe}: {e}", file=sys.stderr)
        return []


def compute_confluence(elastic_tfs: List[int], zone_state: str) -> str:
    zone_active = zone_state in ZONE_ACTIVE_STATES
    has_multi   = len(elastic_tfs) >= 2
    has_single  = len(elastic_tfs) == 1
    if has_multi and zone_active:
        return "ELASTIC_IN_EXTREME"
    if has_multi:
        return "ELASTIC_NO_ZONE"
    if has_single and zone_active:
        return "ELASTIC_WEAK_ZONE"
    if zone_active:
        return "ZONE_NO_ELASTIC"
    return "NOTHING"


# ==========================================================================
# SNAPSHOT
# ==========================================================================

def compute_snapshot(db_path: str, zone_tf: int) -> Dict[str, dict]:
    results = {}
    for currency, force_col in CURRENCIES.items():
        elastic_tfs = []
        tf1_score = 0.0
        tf5_score = 0.0

        for tf, bars in CROSS_TF_PAIRS:
            series = fetch_series(db_path, force_col, tf, bars)
            sig = compute_tension_signature(series)
            if tf == 1:
                tf1_score = sig.score
            if tf == 5:
                tf5_score = sig.score
            if sig.label == "ELASTIC_LOADED":
                elastic_tfs.append(tf)

        # ------------------------------------------------------------------
        # Scan fractalite zone: TF15 / TF30 / TF60
        # ------------------------------------------------------------------
        zone_state_by_tf: Dict[int, str] = {}
        diag15 = None

        for ztf, zbars in FRACTAL_TFS:
            zs = fetch_series(db_path, force_col, ztf, zbars)
            if len(zs) >= 6:
                diag = analyze_zone_dynamics(zs, timeframe=ztf, currency=currency)
                zone_state_by_tf[ztf] = diag.state
                if ztf == 15:
                    diag15 = diag
            else:
                zone_state_by_tf[ztf] = "NO_DATA"

        # Zone principale = TF15, le plus reactif.
        # Fallback defensif si TF15 manque: on conserve une sortie stable.
        if diag15 is not None:
            zone_state = diag15.state
            zone_z     = diag15.z_current
            zone_dir   = diag15.z_extreme_dir
        else:
            zone_state = "NO_DATA"
            zone_z     = 0.0
            zone_dir   = "NONE"

        # Fractalite = nombre de TF en zone active.
        fractal_score = sum(
            1 for state in zone_state_by_tf.values()
            if state in ZONE_ACTIVE_STATES
        )

        results[currency] = {
            "confluence":       compute_confluence(elastic_tfs, zone_state),
            "elastic_tfs":      elastic_tfs,
            "tf1_score":        tf1_score,
            "tf5_score":        tf5_score,
            "zone_state":       zone_state,
            "zone_z":           zone_z,
            "zone_dir":         zone_dir,
            "zone_state_by_tf": zone_state_by_tf,
            "fractal_score":    fractal_score,
        }

    return results


# ==========================================================================
# ANTI-SPAM
# ==========================================================================

def load_last_alerts() -> Dict[str, str]:
    if not LAST_ALERT_PATH.exists():
        return {}
    try:
        data = json.loads(LAST_ALERT_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_last_alerts(alerts: Dict[str, str]) -> None:
    LAST_ALERT_PATH.parent.mkdir(parents=True, exist_ok=True)
    LAST_ALERT_PATH.write_text(
        json.dumps(alerts, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def is_in_cooldown(currency: str, last_alerts: Dict[str, str]) -> bool:
    sent_at_str = last_alerts.get(currency)
    if not sent_at_str:
        return False
    try:
        sent_at = datetime.fromisoformat(sent_at_str)
        if sent_at.tzinfo is None:
            sent_at = sent_at.replace(tzinfo=timezone.utc)
        elapsed = (now_utc() - sent_at).total_seconds()
        return elapsed < COOLDOWN_S
    except ValueError:
        return False


# ==========================================================================
# STATE PERSISTANTE — detection persistance cross-snapshots
# ==========================================================================

# Memoire du dernier snapshot pour detecter la persistance
_previous_eie: Dict[str, int] = {c: 0 for c in CURRENCIES}


def update_persistence(snapshot: Dict[str, dict]) -> Dict[str, int]:
    """Retourne le nombre de snapshots consecutifs EIE par devise."""
    global _previous_eie
    current: Dict[str, int] = {}
    for currency in CURRENCIES:
        conf = snapshot[currency]["confluence"]
        if conf == "ELASTIC_IN_EXTREME":
            current[currency] = _previous_eie.get(currency, 0) + 1
        else:
            current[currency] = 0
    _previous_eie = current
    return current


# ==========================================================================
# MESSAGE BUILDER
# ==========================================================================

def build_alert_message(
    currency: str,
    data: dict,
    persist_count: int,
    session: str,
    zone_tf: int,
    cg,
) -> str:
    now = now_utc()
    cest_h = (now.hour + 2) % 24
    time_str = f"{cest_h:02d}:{now.minute:02d} CEST"

    tf1        = data["tf1_score"]
    tf5        = data["tf5_score"]
    zone       = data["zone_state"]
    z          = data["zone_z"]
    dir_       = data["zone_dir"]
    fractal    = data["fractal_score"]
    tf_states  = data["zone_state_by_tf"]

    persist_str = f"{persist_count * 5} min" if persist_count > 1 else "naissant"

    # Barre fractalite visuelle.
    fractal = max(0, min(3, int(fractal)))
    fractal_bar = "█" * fractal + "░" * (3 - fractal)
    fractal_label = {
        0: "isole",
        1: "partiel",
        2: "aligne",
        3: "FULL ALIGN ⚡",
    }.get(fractal, "?")

    # Detail TF zone.
    tf_detail = "  ".join(
        f"TF{tf}:{str(state)[:4]}"
        for tf, state in sorted(tf_states.items())
    )

    # Detail Relational Gravity / Confluence Gravity.
    roles_by_tf = getattr(cg, "roles_by_tf", {}) or {}
    role_str = " | ".join(
        f"TF{tf}:{str(role)[:4].upper()}"
        for tf, role in sorted(roles_by_tf.items())
    ) or "TF?:NONE"

    fusion_state = getattr(cg, "fusion_state", "UNKNOWN")
    dominant_direction = getattr(cg, "dominant_direction", None)
    dominant_leader = getattr(cg, "dominant_leader", None)
    confidence = getattr(cg, "confidence", "UNKNOWN")

    lines = [
        f"⚡ PowerFlow — ELASTIC IN EXTREME",
        f"",
        f"Devise   : {currency}",
        f"Heure    : {time_str} — {session}",
        f"Persist  : {persist_str} ({persist_count} snapshots)",
        f"",
        f"TF1 score : {tf1:.2f}",
        f"TF5 score : {tf5:.2f}",
        f"Zone TF15 : {zone} z={z:.0f} {dir_}",
        f"",
        f"Fractalite : {fractal_bar} {fractal}/3 — {fractal_label}",
        f"  {tf_detail}",
        f"",
        f"Gravite RG : {fusion_state}",
        f"Direction  : {dominant_direction or '?'} — leader {dominant_leader or '?'}",
        f"Role       : {role_str}",
        f"Confiance  : {confidence}",
        f"",
        f"Compression multi-echelle en zone active.",
        f"Trader filtre et decide.",
    ]
    return "\n".join(lines)


# ==========================================================================
# SCAN ONCE
# ==========================================================================

def scan_once(
    db_path: str,
    zone_tf: int,
    dry_run: bool,
    token: Optional[str],
    chat_id: Optional[str],
) -> None:
    now = now_utc()
    session = detect_session(now)
    cest_h = (now.hour + 2) % 24
    time_str = f"{cest_h:02d}:{now.minute:02d}"

    snapshot = compute_snapshot(db_path, zone_tf)
    persist  = update_persistence(snapshot)
    last_alerts = load_last_alerts()

    alerts_sent = []

    for currency in CURRENCIES:
        p = persist[currency]
        if p < MIN_PERSIST:
            continue
        if is_in_cooldown(currency, last_alerts):
            print(f"  [{time_str}] {currency} EIE x{p} — cooldown actif, skip")
            continue

        data = snapshot[currency]

        # ------------------------------------------------------------------
        # Confluence + Relational Gravity bridge
        # ------------------------------------------------------------------
        cg = analyze_confluence_gravity(
            currency=currency,
            eie_persist=p,
            fractal_score=data["fractal_score"],
        )

        message = build_alert_message(currency, data, p, session, zone_tf, cg)

        print(f"\n  [{time_str}] ⚡ ALERTE {currency} EIE persistant x{p}")
        print(f"  {message[:120]}...")

        if dry_run:
            print(f"  [DRY-RUN] Message prêt — non envoyé")
            last_alerts[currency] = iso_now()
        elif token and chat_id:
            result = send_telegram_message(token, chat_id, message, timeout=10)
            if result.get("ok"):
                print(f"  [TELEGRAM] ✅ Envoyé")
                last_alerts[currency] = iso_now()
                alerts_sent.append(currency)
            else:
                print(f"  [TELEGRAM] ❌ Erreur : {result.get('error', result)}")
        else:
            print(f"  [TELEGRAM] Non configuré — message construit uniquement")

    save_last_alerts(last_alerts)

    if not any(persist[c] >= MIN_PERSIST for c in CURRENCIES):
        print(f"  [{time_str}] {session} — aucun EIE persistant")


# ==========================================================================
# MAIN
# ==========================================================================

def main() -> None:
    parser = argparse.ArgumentParser(description="run_confluence_alert")
    parser.add_argument("--db",       default=DEFAULT_DB)
    parser.add_argument("--zone-tf",  type=int, default=DEFAULT_ZONE_TF)
    parser.add_argument("--dry-run",  action="store_true",
                        help="Construit les messages mais n'envoie pas Telegram")
    parser.add_argument("--once",     action="store_true",
                        help="Un seul scan puis exit (pas de daemon)")
    parser.add_argument("--env",      default=str(ENV_PATH))
    args = parser.parse_args()

    if not Path(args.db).exists():
        print(f"[ERROR] DB introuvable : {args.db}", file=sys.stderr)
        sys.exit(1)

    load_env_file(Path(args.env))
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip() or None
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip() or None

    if not token or not chat_id:
        print("[WARN] TELEGRAM_BOT_TOKEN ou TELEGRAM_CHAT_ID manquant — mode dry-run forcé")
        args.dry_run = True

    print("=" * 60)
    print(f"  PowerFlow V6 — Confluence Alert — TF{args.zone_tf} zone")
    print(f"  Scan toutes les {SCAN_INTERVAL_S // 60} min — persist >= {MIN_PERSIST} snapshots")
    print(f"  Dry-run : {args.dry_run}")
    print("=" * 60)

    if args.once:
        scan_once(args.db, args.zone_tf, args.dry_run, token, chat_id)
        return

    # Daemon loop
    while True:
        try:
            scan_once(args.db, args.zone_tf, args.dry_run, token, chat_id)
        except Exception as e:
            print(f"[ERROR] scan_once failed: {e}", file=sys.stderr)
        time.sleep(SCAN_INTERVAL_S)


if __name__ == "__main__":
    main()
