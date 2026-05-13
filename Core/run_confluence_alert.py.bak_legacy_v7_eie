"""
run_confluence_alert.py — PowerFlow V7  V2.0
Daemon live : EIE persistant → behavioral_queue + Telegram enrichi B1/B3/B5.

  python run_confluence_alert.py              # daemon 5 min
  python run_confluence_alert.py --once       # 1 scan
  python run_confluence_alert.py --dry-run    # sans Telegram
"""
from __future__ import annotations

import argparse
import json
import logging
import signal
import time
from datetime import datetime, timezone
from pathlib import Path

from pf_confluence_elastic import CURRENCIES, compute_confluence_snapshot
from pf_confluence_gravity import compute_confluence_gravity

DB_PATH_DEFAULT    = Path("powerflow.db")
QUEUE_PATH         = Path("output/behavioral_alert_queue.json")
COOLDOWN_PATH      = Path("output/confluence_alert_last.json")
SCAN_INTERVAL_SEC  = 300
MIN_PERSIST        = 2
COOLDOWN_SECONDS   = 600
QUEUE_MAX_SIZE     = 200
REGIME_PATH        = Path("output/regime_engine_state.json")
SPEARMAN_PATH      = Path("output/spearman_gravity_state.json")
COCKPIT_PATH       = Path("output/cockpit_agentic_state_v01.json")

SESSION_HOURS = {
    "ASIA": (0,8), "LON_OPEN": (8,9), "LONDON": (9,12),
    "PRE_US": (12,14), "US": (14,22), "LATE": (22,24),
}

_running = True
logging.basicConfig(level=logging.INFO, format="%(asctime)s [CONFLUENCE] %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger("confluence_alert")


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _session_name() -> str:
    h = datetime.now(timezone.utc).hour
    for name, (s, e) in SESSION_HOURS.items():
        if s <= h < e:
            return name
    return "UNKNOWN"

def _fractal_label(score: int) -> str:
    return {0:"NO_ALIGN",1:"PARTIAL_ALIGN",2:"ALIGN",3:"FULL_ALIGN"}.get(score,"NO_ALIGN")

def _load_cooldown() -> dict:
    if COOLDOWN_PATH.exists():
        try:
            return json.loads(COOLDOWN_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def _save_cooldown(cd: dict) -> None:
    COOLDOWN_PATH.parent.mkdir(parents=True, exist_ok=True)
    COOLDOWN_PATH.write_text(json.dumps(cd, indent=2), encoding="utf-8")

def _is_on_cooldown(currency: str, cd: dict) -> bool:
    ts_str = cd.get(currency)
    if not ts_str:
        return False
    try:
        elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(ts_str)).total_seconds()
        return elapsed < COOLDOWN_SECONDS
    except Exception:
        return False

def _write_behavioral_queue(event: dict) -> None:
    existing = []
    if QUEUE_PATH.exists():
        try:
            existing = json.loads(QUEUE_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        except Exception:
            existing = []
    existing.append(event)
    if len(existing) > QUEUE_MAX_SIZE:
        existing = existing[-QUEUE_MAX_SIZE:]
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

def _build_telegram_message(currency, state, cg, session, persist_count) -> str:
    bars = "█" * state.fractal_score + "░" * (3 - state.fractal_score)
    regime_emoji = {"COMPRESSION":"🗜️","TENDANCE":"📈","RANGE":"↔️"}.get(cg.regime,"❓")
    fusion_emoji = {
        "EIE_LEADER_CONFIRMED":"🔥","EIE_FOLLOWER_CONFIRMED":"🟠","EIE_ANTAGONIST":"⚡",
        "EIE_WITH_RG_CONFLICT":"⚠️","EIE_WITH_RG_PARTIAL":"🟡",
        "EIE_WITH_RG_OUTSIDE":"⬜","EIE_NO_RG_DATA":"❔",
    }.get(cg.fusion_state,"")
    noise_str = f" | noise={state.noise_ratio:.2f}" if state.noise_ratio > 0 else ""
    spearman_str = f"\n🔗 B5: {', '.join(cg.spearman_context[:3])}" if cg.spearman_context else ""
    return (
        f"⚡ EIE ALERT — {currency}\n━━━━━━━━━━━━━━━━━━\n"
        f"Zone : {state.zone_state} z={state.zone_z:+.2f} ({state.zone_dir})\n"
        f"Persist : {persist_count}x ({persist_count * 5} min)\n"
        f"Fractal : {bars} {state.fractal_score}/3 {state.fractal_label}\n"
        f"Fusion  : {fusion_emoji} {cg.fusion_state} [{cg.confidence}]\n"
        f"Regime  : {regime_emoji} {cg.regime} ({cg.regime_confidence:.2f}){noise_str}\n"
        f"Session : {session}{spearman_str}"
    )

def _send_telegram(msg: str, env_path: Path) -> bool:
    try:
        from telegram_trader_alert_v01 import send_alert
        return send_alert(msg, env_path=env_path)
    except Exception as e:
        log.warning(f"Telegram unavailable: {e}")
        return False

def run_scan(db_path, zone_tf, dry_run, env_path, persist_state) -> dict:
    regime_contexts = {}
    if REGIME_PATH.exists():
        try:
            rd = json.loads(REGIME_PATH.read_text(encoding="utf-8"))
            htf = rd.get("htf_context_stack", {})
            r = htf.get("D") or htf.get("H4") or rd.get("regime", "UNKNOWN")
            for c in CURRENCIES:
                regime_contexts[c] = r
        except Exception:
            pass

    snap = compute_confluence_snapshot(db_path=db_path, zone_tf=zone_tf, regime_contexts=regime_contexts)
    cd = _load_cooldown()
    session = _session_name()
    new_persist = {c: 0 for c in CURRENCIES}

    for currency in CURRENCIES:
        state = snap.states.get(currency)
        if not state:
            continue
        if state.is_eie:
            new_persist[currency] = persist_state.get(currency, 0) + 1
        else:
            new_persist[currency] = 0
            continue

        persist_count = new_persist[currency]
        if persist_count < MIN_PERSIST:
            log.debug(f"{currency}: EIE naissant ({persist_count}/{MIN_PERSIST})")
            continue
        if _is_on_cooldown(currency, cd):
            log.debug(f"{currency}: cooldown actif")
            continue

        cg = compute_confluence_gravity(
            currency=currency, cockpit_path=COCKPIT_PATH,
            regime_path=REGIME_PATH, spearman_path=SPEARMAN_PATH,
        )
        level = "HOT" if cg.confidence == "HIGH" else "WATCH"
        log.info(f"EIE {level} | {currency} | persist={persist_count} | fractal={state.fractal_score}/3 | {cg.fusion_state} [{cg.confidence}] | regime={cg.regime}")

        event = {
            "type": "ELASTIC_IN_EXTREME", "level": level, "currency": currency,
            "eie_persist": persist_count, "fractal_score": state.fractal_score,
            "fractal_label": _fractal_label(state.fractal_score),
            "fusion_state": cg.fusion_state, "confidence": cg.confidence,
            "zone_state": state.zone_state, "zone_z": round(state.zone_z, 2),
            "zone_dir": state.zone_dir, "regime": cg.regime,
            "regime_confidence": round(cg.regime_confidence, 3),
            "spearman_context": cg.spearman_context[:3],
            "noise_ratio": round(state.noise_ratio, 3),
            "session": session, "timestamp": iso_now(),
            "source": "run_confluence_alert_v2",
        }

        if not dry_run:
            try:
                _write_behavioral_queue(event)
            except Exception as e:
                log.error(f"Queue write error: {e}")

        msg = _build_telegram_message(currency, state, cg, session, persist_count)
        if not dry_run:
            _send_telegram(msg, env_path)
        else:
            log.info(f"[DRY-RUN] Telegram:\n{msg}")

        cd[currency] = iso_now()

    if not dry_run:
        _save_cooldown(cd)
    return new_persist


def _signal_handler(sig, frame):
    global _running
    log.info("Signal reçu — arrêt propre.")
    _running = False


def main():
    global _running
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DB_PATH_DEFAULT)
    parser.add_argument("--zone-tf", type=int, default=15)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--env", type=Path, default=Path(".env"))
    parser.add_argument("--interval", type=int, default=SCAN_INTERVAL_SEC)
    args = parser.parse_args()

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    log.info(f"PowerFlow V7 Confluence Alert V2.0 — db={args.db} zone_tf={args.zone_tf} dry_run={args.dry_run}")
    persist_state = {c: 0 for c in CURRENCIES}

    if args.once:
        run_scan(args.db, args.zone_tf, args.dry_run, args.env, persist_state)
        return

    while _running:
        try:
            persist_state = run_scan(args.db, args.zone_tf, args.dry_run, args.env, persist_state)
        except Exception as e:
            log.error(f"Scan error: {e}")
        for _ in range(args.interval):
            if not _running:
                break
            time.sleep(1)

    log.info("Daemon arrêté proprement.")


if __name__ == "__main__":
    main()