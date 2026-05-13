#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
from pathlib import Path

OLD_IMPORT = "import time\nfrom collections import deque, defaultdict\n"
NEW_IMPORT = "import time\nimport os\nimport json\nfrom datetime import datetime, timezone\nfrom collections import deque, defaultdict\n"
INSERT_AFTER = 'TF_LABELS = {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4"}\n'

HELPER_BLOCK = """# ============================================================
# LEGACY TIME-COMP → V7 TEMPORAL BRIDGE
# ============================================================
def _utc_iso(dt) -> str:
    \"""Normalize datetime-like values to UTC ISO string.\"""
    if dt is None:
        return datetime.now(timezone.utc).isoformat()
    try:
        if hasattr(dt, "tzinfo"):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
    except Exception:
        pass
    try:
        return str(dt)
    except Exception:
        return datetime.now(timezone.utc).isoformat()

def _legacy_timecomp_event_type(tc_ev: dict) -> str:
    phase = str(tc_ev.get("phase", "")).upper()
    if phase == "LOCK":
        return "TIME_COMP_LOCK"
    if phase == "BREAK":
        return "TIME_COMP_BREAK"
    return f"TIME_COMP_{phase or 'UNKNOWN'}"

def _legacy_timecomp_direction(tc_ev: dict) -> str:
    if str(tc_ev.get("phase", "")).upper() != "BREAK":
        return "NONE"
    try:
        start = float(tc_ev.get("from_bid", tc_ev.get("center", 0.0)) or 0.0)
        end = float(tc_ev.get("bid", 0.0) or 0.0)
        if end > start:
            return "PAIR_UP"
        if end < start:
            return "PAIR_DOWN"
    except Exception:
        pass
    return "UNKNOWN"

def _legacy_timecomp_jsonl_path(symbol: str) -> str:
    out_dir = os.path.join("output", "dashboard_surface", symbol.upper())
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, "legacy_timecomp_events.jsonl")

def _write_legacy_timecomp_event(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
    \"""Write one legacy TIME-COMP event as a V7-readable JSONL proof.

    This does not change the legacy detection. It only turns console perception
    into a TEMPORAL proof consumable by V7 readers / Spine.
    \"""
    event_at = _utc_iso(getattr(tick, "timestamp", None))
    detected_at = datetime.now(timezone.utc).isoformat()
    phase = str(tc_ev.get("phase", "")).upper()
    direction = _legacy_timecomp_direction(tc_ev)

    price_from = tc_ev.get("from_bid", tc_ev.get("center"))
    price_to = tc_ev.get("bid")

    event = {
        "source": "legacy_engine",
        "layer": "TEMPORAL",
        "symbol": symbol.upper(),
        "timeframe": int(tf),
        "tf_label": tf_label,
        "event": _legacy_timecomp_event_type(tc_ev),
        "phase": phase,
        "direction": direction,
        "event_at": event_at,
        "detected_at": detected_at,
        "price_from": price_from,
        "price_to": price_to,
        "center": tc_ev.get("center"),
        "band": tc_ev.get("band"),
        "ticks": tc_ev.get("ticks"),
        "bid": tc_ev.get("bid"),
        "from_bid": tc_ev.get("from_bid"),
        "technical_risks": [],
    }

    path = _legacy_timecomp_jsonl_path(symbol)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\\n")
    return event
"""

OLD_BLOCK = """    # --- Compression temporelle (observation console) ---
    try:
        tc_ev = detect_time_compression(tick, uid)
        if tc_ev:
            tf_lbl = TF_LABELS.get(tf, f"M{tf}")
            if tc_ev["phase"] == "LOCK":
                print(f"🔒 TIME-COMP LOCK | {pair} {tf_lbl} | "
                      f"bid {tc_ev['bid']} ±{tc_ev['band']} | {tc_ev['ticks']} ticks")
            else:
                print(f"💨 TIME-COMP BREAK | {pair} {tf_lbl} | "
                      f"bid {tc_ev['from_bid']}→{tc_ev['bid']} | {tc_ev['ticks']} ticks")
    except Exception as e:
        print(f"[engine] detect_time_compression ignoré : {e}")"""

NEW_BLOCK = """    # --- Compression temporelle legacy → preuve TEMPORAL V7 ---
    try:
        tc_ev = detect_time_compression(tick, uid)
        if tc_ev:
            tf_lbl = TF_LABELS.get(tf, f"M{tf}")
            tc_record = _write_legacy_timecomp_event(pair, tf, tf_lbl, tick, tc_ev)
            stamp = f"[event_at={tc_record['event_at']} detected_at={tc_record['detected_at']}]"
            if tc_ev["phase"] == "LOCK":
                print(stamp)
                print(f"🔒 TIME-COMP LOCK | {pair} {tf_lbl} | "
                      f"bid {tc_ev['bid']} ±{tc_ev['band']} | {tc_ev['ticks']} ticks")
            else:
                print(stamp)
                print(f"💨 TIME-COMP BREAK | {pair} {tf_lbl} | "
                      f"bid {tc_ev['from_bid']}→{tc_ev['bid']} | {tc_ev['ticks']} ticks")
    except Exception as e:
        print(f"[engine] detect_time_compression ignoré : {e}")"""

def patch_engine(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    if "LEGACY TIME-COMP → V7 TEMPORAL BRIDGE" in text and "tc_record = _write_legacy_timecomp_event" in text:
        print("[OK] engine.py already patched")
        return

    backup = path.with_suffix(path.suffix + ".bak_timecomp_v7")
    backup.write_text(text, encoding="utf-8")

    if "from datetime import datetime, timezone" not in text:
        if OLD_IMPORT not in text:
            raise RuntimeError("Could not locate import block to patch")
        text = text.replace(OLD_IMPORT, NEW_IMPORT, 1)

    if "LEGACY TIME-COMP → V7 TEMPORAL BRIDGE" not in text:
        if INSERT_AFTER not in text:
            raise RuntimeError("Could not locate TF_LABELS insertion point")
        text = text.replace(INSERT_AFTER, INSERT_AFTER + HELPER_BLOCK + "\n", 1)

    if OLD_BLOCK not in text:
        raise RuntimeError("Could not locate original TIME-COMP print block. File may differ from expected version.")
    text = text.replace(OLD_BLOCK, NEW_BLOCK, 1)

    path.write_text(text, encoding="utf-8")
    print(f"[OK] patched {path}")
    print(f"[OK] backup  {backup}")

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="engine.py")
    args = parser.parse_args()
    patch_engine(Path(args.engine))

if __name__ == "__main__":
    main()
