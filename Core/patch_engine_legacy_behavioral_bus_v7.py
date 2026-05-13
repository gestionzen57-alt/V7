#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Patch PowerFlow legacy engine.py so fast V5 alerts are mirrored into a V7-readable JSONL bus.

Adds:
- output/dashboard_surface/<SYMBOL>/legacy_behavioral_events.jsonl
- output/dashboard_surface/<SYMBOL>/legacy_timecomp_events.jsonl for TIME-COMP if not already wired
- no change to alert decisions; only writes observation/proof records.
"""
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path

MARKER = "LEGACY BEHAVIORAL BUS V7"

HELPER_BLOCK = r'''
# ============================================================
# LEGACY BEHAVIORAL BUS V7
# ============================================================
def _pfv7_utc_iso(dt) -> str:
    """Normalize datetime-like values to UTC ISO string for V7 proof traces."""
    try:
        if dt is None:
            return datetime.now(timezone.utc).isoformat()
        if hasattr(dt, "tzinfo"):
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc).isoformat()
        return str(dt)
    except Exception:
        return datetime.now(timezone.utc).isoformat()


def _pfv7_symbol_dir(symbol: str) -> str:
    out_dir = os.path.join("output", "dashboard_surface", str(symbol).upper())
    os.makedirs(out_dir, exist_ok=True)
    return out_dir


def _pfv7_behavioral_jsonl_path(symbol: str) -> str:
    return os.path.join(_pfv7_symbol_dir(symbol), "legacy_behavioral_events.jsonl")


def _pfv7_timecomp_jsonl_path(symbol: str) -> str:
    return os.path.join(_pfv7_symbol_dir(symbol), "legacy_timecomp_events.jsonl")


def _pfv7_event_time_risks(event_at: str, detected_at: str) -> list[str]:
    risks: list[str] = []
    try:
        ea = datetime.fromisoformat(str(event_at).replace("Z", "+00:00"))
        da = datetime.fromisoformat(str(detected_at).replace("Z", "+00:00"))
        if ea.tzinfo is None:
            ea = ea.replace(tzinfo=timezone.utc)
        if da.tzinfo is None:
            da = da.replace(tzinfo=timezone.utc)
        delta = (ea.astimezone(timezone.utc) - da.astimezone(timezone.utc)).total_seconds()
        if delta > 120:
            risks.append("EVENT_TIME_AHEAD_OF_DETECTED_AT")
        elif delta < -7200:
            risks.append("EVENT_TIME_STALE_VS_DETECTED_AT")
    except Exception:
        risks.append("EVENT_TIME_PARSE_UNCLEAR")
    return risks


def _pfv7_signal_layer(signal_type: str) -> str:
    st = str(signal_type or "").upper()
    if st in {"TIME_COMP_LOCK", "TIME_COMP_BREAK"}:
        return "TEMPORAL"
    if st in {"COMPRESSION", "COMPRESSION_BREAK", "COMPRESSION_SQUEEZE"}:
        return "ENERGY"
    if st in {"SLINGSHOT", "APPROACH", "CROSS", "CONVERGENCE", "SUPER_SWITCH", "FAKEOUT"}:
        return "TACTICAL"
    if st in {"KISS_REJECT", "EXTREME_HIGH", "EXTREME_LOW"}:
        return "ZONE_REACTION"
    return "LEGACY"


def _pfv7_event_role(signal_type: str) -> str:
    st = str(signal_type or "").upper()
    return {
        "TIME_COMP_LOCK": "TEMPORAL_LOCK",
        "TIME_COMP_BREAK": "TEMPORAL_RELEASE",
        "SLINGSHOT": "TACTICAL_REARM_RELEASE",
        "KISS_REJECT": "ZONE_REPULSION",
        "COMPRESSION": "ELASTIC_LOADING_LEGACY",
        "COMPRESSION_BREAK": "ELASTIC_RELEASE_LEGACY",
        "COMPRESSION_SQUEEZE": "PRESSURE_SQUEEZE",
        "APPROACH": "CROSS_OR_REJECT_IMMINENT",
        "EXTREME_HIGH": "ZONE_PRESSURE_HIGH",
        "EXTREME_LOW": "ZONE_PRESSURE_LOW",
        "FAKEOUT": "TRAP_OR_REINTEGRATION",
        "SUPER_SWITCH": "FORCE_SWITCH",
        "CONVERGENCE": "MULTI_TF_CONVERGENCE",
        "CROSS": "DOMINANCE_CROSS",
    }.get(st, st or "UNKNOWN")


def _pfv7_pair_bias_from_signal(sig) -> str:
    try:
        symbol = str(getattr(sig, "symbol", "")).upper()
        strong = str(getattr(sig, "dev_strong", "")).upper()
        weak = str(getattr(sig, "dev_weak", "")).upper()
        if len(symbol) >= 6 and strong and weak:
            base = symbol[:3]
            quote = symbol[3:6]
            if strong == base and weak == quote:
                return "PAIR_UP"
            if strong == quote and weak == base:
                return "PAIR_DOWN"
    except Exception:
        pass
    return "UNKNOWN"


def _pfv7_write_jsonl(path: str, record: dict) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def _write_legacy_behavioral_event(record: dict) -> dict:
    """Append one V7 legacy behavioral proof record."""
    try:
        symbol = str(record.get("symbol", "UNKNOWN")).upper()
        event_at = str(record.get("event_at") or datetime.now(timezone.utc).isoformat())
        detected_at = str(record.get("detected_at") or datetime.now(timezone.utc).isoformat())
        risks = list(record.get("technical_risks") or [])
        for risk in _pfv7_event_time_risks(event_at, detected_at):
            if risk not in risks:
                risks.append(risk)
        record["technical_risks"] = risks
        record.setdefault("source", "legacy_engine")
        record.setdefault("method", "LEGACY_BEHAVIORAL_BUS_V7A")
        _pfv7_write_jsonl(_pfv7_behavioral_jsonl_path(symbol), record)
    except Exception as exc:
        print(f"[engine] legacy behavioral bus ignored: {exc}")
    return record


def _write_legacy_behavioral_signal(sig, htf=None, tick=None) -> dict:
    """Mirror an existing legacy Signal into V7 JSONL. Does not affect alert flow."""
    detected_at = datetime.now(timezone.utc).isoformat()
    event_at = _pfv7_utc_iso(getattr(sig, "timestamp", None) or getattr(tick, "timestamp", None))
    signal_type = str(getattr(sig, "signal_type", "UNKNOWN")).upper()
    symbol = str(getattr(sig, "symbol", getattr(tick, "symbol", "UNKNOWN"))).upper()
    tf = int(getattr(sig, "timeframe", getattr(tick, "timeframe", 0)) or 0)
    tf_label = TF_LABELS.get(tf, f"M{tf}")
    record = {
        "source": "legacy_engine",
        "method": "LEGACY_BEHAVIORAL_BUS_V7A",
        "symbol": symbol,
        "timeframe": tf,
        "tf_label": tf_label,
        "event": signal_type,
        "event_role": _pfv7_event_role(signal_type),
        "layer": _pfv7_signal_layer(signal_type),
        "event_at": event_at,
        "detected_at": detected_at,
        "bias": _pfv7_pair_bias_from_signal(sig),
        "score_hint": getattr(sig, "score", None),
        "level": getattr(sig, "level", None),
        "price": getattr(sig, "price", None) or getattr(tick, "bid", None),
        "dev_strong": getattr(sig, "dev_strong", None),
        "dev_weak": getattr(sig, "dev_weak", None),
        "spread_ok": getattr(sig, "spread_ok", None),
        "volume_badge": getattr(sig, "volume_badge", None),
        "note": getattr(sig, "note", ""),
        "htf_bias": getattr(htf, "bias", None),
        "htf_bias_state": getattr(htf, "bias_state", None),
        "htf_scenario": getattr(htf, "scenario", None),
        "technical_risks": [],
    }
    return _write_legacy_behavioral_event(record)


def _pfv7_timecomp_event_type(tc_ev: dict) -> str:
    phase = str(tc_ev.get("phase", "")).upper()
    if phase == "LOCK":
        return "TIME_COMP_LOCK"
    if phase == "BREAK":
        return "TIME_COMP_BREAK"
    return f"TIME_COMP_{phase or 'UNKNOWN'}"


def _pfv7_timecomp_direction(tc_ev: dict) -> str:
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


def _write_legacy_timecomp_event_v7bus(symbol: str, tf: int, tf_label: str, tick: Tick, tc_ev: dict) -> dict:
    """Write TIME-COMP into both dedicated temporal JSONL and common behavioral bus."""
    event_at = _pfv7_utc_iso(getattr(tick, "timestamp", None))
    detected_at = datetime.now(timezone.utc).isoformat()
    phase = str(tc_ev.get("phase", "")).upper()
    event_name = _pfv7_timecomp_event_type(tc_ev)
    direction = _pfv7_timecomp_direction(tc_ev)
    price_from = tc_ev.get("from_bid", tc_ev.get("center"))
    price_to = tc_ev.get("bid")
    risks = _pfv7_event_time_risks(event_at, detected_at)

    temporal = {
        "source": "legacy_engine",
        "method": "LEGACY_TIMECOMP_BRIDGE_V7A",
        "layer": "TEMPORAL",
        "symbol": str(symbol).upper(),
        "timeframe": int(tf),
        "tf_label": tf_label,
        "event": event_name,
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
        "technical_risks": risks,
    }
    try:
        _pfv7_write_jsonl(_pfv7_timecomp_jsonl_path(symbol), temporal)
    except Exception as exc:
        print(f"[engine] legacy timecomp jsonl ignored: {exc}")

    behavioral = dict(temporal)
    behavioral.update({
        "method": "LEGACY_BEHAVIORAL_BUS_V7A",
        "event_role": _pfv7_event_role(event_name),
        "bias": direction if direction in ("PAIR_UP", "PAIR_DOWN") else "UNKNOWN",
        "score_hint": 2.0 if phase == "LOCK" else 3.5,
        "price": price_to,
        "note": f"TIME-COMP {phase} {tf_label} ticks={tc_ev.get('ticks')}",
    })
    _write_legacy_behavioral_event(behavioral)
    return temporal
'''

TIMECOMP_BLOCK = '''    # --- Compression temporelle legacy -> preuve TEMPORAL V7 ---
    try:
        tc_ev = detect_time_compression(tick, uid)
        if tc_ev:
            tf_lbl = TF_LABELS.get(tf, f"M{tf}")
            tc_record = _write_legacy_timecomp_event_v7bus(pair, tf, tf_lbl, tick, tc_ev)
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
        print(f"[engine] detect_time_compression ignoré : {e}")'''


def ensure_imports(text: str) -> str:
    if "import os" not in text:
        text = text.replace("import time\n", "import time\nimport os\n")
    if "import json" not in text:
        text = text.replace("import os\n", "import os\nimport json\n")
    if "from datetime import datetime, timezone" not in text:
        text = text.replace("import json\n", "import json\nfrom datetime import datetime, timezone\n")
    return text


def insert_helper(text: str) -> str:
    if MARKER in text:
        return text
    pattern = re.compile(r"(TF_LABELS\s*=\s*\{[^\n]+\}\n)")
    match = pattern.search(text)
    if not match:
        raise RuntimeError("Could not find TF_LABELS line for helper insertion")
    return text[:match.end()] + "\n" + HELPER_BLOCK + "\n" + text[match.end():]


def patch_timecomp_block(text: str) -> str:
    # Replace any existing compression-temporelle try block, old or already V7-ish.
    pattern = re.compile(
        r"    # --- Compression temporelle.*?\n"
        r"    try:\n"
        r".*?"
        r"    except Exception as e:\n"
        r"        print\(f\"\[engine\] detect_time_compression ignoré : \{e\}\"\)",
        re.DOTALL,
    )
    new_text, count = pattern.subn(TIMECOMP_BLOCK, text, count=1)
    if count == 0:
        print("[WARN] TIME-COMP block not found; no timecomp replacement applied")
        return text
    return new_text


def patch_persist_calls(text: str) -> str:
    if "_write_legacy_behavioral_signal(sig, htf, tick=tick)" in text:
        return text
    # Patch only function calls, not the function definition.
    return re.sub(
        r"(?<!def )persist_signal\(sig, htf\)",
        "persist_signal(sig, htf); _write_legacy_behavioral_signal(sig, htf, tick=tick)",
        text,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", default="engine.py")
    args = parser.parse_args()
    path = Path(args.engine)
    if not path.exists():
        raise SystemExit(f"engine file not found: {path}")
    original = path.read_text(encoding="utf-8")
    text = original
    text = ensure_imports(text)
    text = insert_helper(text)
    text = patch_timecomp_block(text)
    text = patch_persist_calls(text)
    if text == original:
        print("[OK] no changes needed")
        return 0
    backup = path.with_suffix(path.suffix + ".bak_legacy_behavioral_bus_v7")
    shutil.copy2(path, backup)
    path.write_text(text, encoding="utf-8")
    print(f"[OK] patched {path}")
    print(f"[OK] backup  {backup}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
