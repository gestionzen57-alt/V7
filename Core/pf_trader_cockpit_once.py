#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.3.5 - Trader Cockpit Builder

Reads existing dashboard_surface outputs and produces a trader-first cockpit:
- one actionable perception page
- no audit grid noise
- no order decision
- technical risks only when they qualify the reading
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def read_text(path: Path, default: str = "") -> str:
    try:
        if path.exists():
            return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return default
    return default


def write_json(path: Path, data: Any, pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )


def pick_symbol_obj(payload: Any, symbol: str) -> Dict[str, Any]:
    s = symbol.upper()
    if isinstance(payload, dict):
        if payload.get("symbol", "").upper() == s:
            return payload
        for key in ("symbols", "reports", "items", "packets", "readings"):
            val = payload.get(key)
            if isinstance(val, list):
                for item in val:
                    if isinstance(item, dict) and str(item.get("symbol", "")).upper() == s:
                        return item
            if isinstance(val, dict):
                candidate = val.get(s) or val.get(symbol)
                if isinstance(candidate, dict):
                    return candidate
        candidate = payload.get(s) or payload.get(symbol)
        if isinstance(candidate, dict):
            return candidate
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict) and str(item.get("symbol", "")).upper() == s:
                return item
    return {}


def first_non_empty(*values: Any, default: Any = None) -> Any:
    for val in values:
        if val not in (None, "", [], {}):
            return val
    return default


def norm_direction(value: Any) -> str:
    text = str(value or "").upper()
    if any(k in text for k in ("PAIR_DOWN", "SHORT", "BEAR", "SELL", "DOWNSIDE")):
        return "PAIR_DOWN"
    if any(k in text for k in ("PAIR_UP", "LONG", "BULL", "BUY", "UPSIDE")):
        return "PAIR_UP"
    return "NEUTRAL"


def scenario_lines(daily_dir: str, live_dir: str, b6_dir: str, synthesis: str, daily_intent: str) -> List[str]:
    lines: List[str] = []
    synth = synthesis.upper()
    intent = daily_intent.upper()
    if daily_dir == "PAIR_DOWN" and live_dir == "PAIR_UP":
        lines += [
            "Réintégration après poussée live PAIR_UP.",
            "Piège inverse si la poussée PAIR_UP échoue.",
            "Second test du niveau sweep / rejet daily.",
            "Acceptation baissière si le live retourne PAIR_DOWN.",
        ]
    elif daily_dir == "PAIR_UP" and live_dir == "PAIR_DOWN":
        lines += [
            "Réintégration après pression live PAIR_DOWN.",
            "Piège inverse si la pression vendeuse échoue.",
            "Second test du low sweep / zone de réaction.",
            "Acceptation haussière si le live retourne PAIR_UP.",
        ]
    elif "SWEEP" in intent or "ACCUMULATION" in intent:
        lines += [
            "Surveiller acceptation ou rejet après sweep.",
            "Observer second test du niveau travaillé.",
            "Nommer rapidement réintégration, continuation ou trap.",
        ]
    elif "CONFLICT" in synth:
        lines += [
            "Conflit actif entre lectures : surveiller bascule du live.",
            "Attendre que M1/M5 nomme acceptation ou échec.",
        ]
    else:
        lines += [
            "Surveiller naissance M1/M5 avant toute lecture forte.",
            "Attendre rejet, absorption, relais ou cassure nette.",
        ]

    if b6_dir in ("PAIR_DOWN", "PAIR_UP") and b6_dir != live_dir and live_dir != "NEUTRAL":
        lines.append("B6 diverge du live : surveiller absorption / friction avant accélération.")
    return lines[:5]


def compact_risks(*risk_lists: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for risks in risk_lists:
        if not isinstance(risks, Iterable) or isinstance(risks, (str, bytes, dict)):
            continue
        for r in risks:
            text = str(r)
            if not text or text in seen:
                continue
            seen.add(text)
            out.append(text)
    return out[:10]


def build_symbol(core: Path, symbol: str) -> Dict[str, Any]:
    surface = core / "output" / "dashboard_surface"
    symdir = surface / symbol

    multiread_all = read_json(surface / "multiread_synthesis_dashboard.json", {})
    b6_all = read_json(surface / "b6_live_fusion_dashboard.json", {})
    live_all = read_json(surface / "live_brief_dashboard.json", {})
    daily_all = read_json(surface / "daily_journal_dashboard.json", read_json(surface / "daily_flow_packet.json", {}))
    topdown_all = read_json(surface / "topdown_reader.json", {})
    signal_all = read_json(surface / "signal_adaptive.json", {})
    data_health = read_json(surface / "data_health.json", {})

    multiread = pick_symbol_obj(multiread_all, symbol)
    b6 = pick_symbol_obj(b6_all, symbol)
    live = pick_symbol_obj(live_all, symbol)
    daily = pick_symbol_obj(daily_all, symbol)
    topdown = pick_symbol_obj(topdown_all, symbol)
    signal = pick_symbol_obj(signal_all, symbol)
    health = pick_symbol_obj(data_health, symbol)

    brief_txt = read_text(symdir / "powerflow_live_brief.txt")
    b6_txt = read_text(symdir / "b6_live_fusion.txt")
    cockpit_live_txt = read_text(symdir / "cockpit_live_status.txt")

    attention = first_non_empty(multiread.get("attention"), live.get("status"), default="WATCH")
    synthesis = first_non_empty(multiread.get("synthesis"), live.get("synthesis"), default="UNKNOWN")
    alignment = first_non_empty(multiread.get("alignment"), default="UNKNOWN")
    reading = first_non_empty(multiread.get("reading"), live.get("reading"), default="Lecture incomplète : surfaces encore partielles.")

    daily_intent = first_non_empty(daily.get("intent"), daily.get("intent_detected"), multiread.get("daily_intent"), default="UNKNOWN")
    daily_prediction = first_non_empty(daily.get("prediction"), daily.get("prediction_next_session"), default="UNKNOWN")
    daily_close = first_non_empty(daily.get("close_position"), default="UNKNOWN")
    daily_dir = norm_direction(daily_intent + " " + daily_prediction)

    topdown_intention = first_non_empty(topdown.get("machine_intention"), topdown.get("topdown_intention"), multiread.get("topdown_intention"), default="UNKNOWN")
    topdown_flux = first_non_empty(topdown.get("flux"), topdown.get("htf_read"), default="UNKNOWN")
    topdown_window = first_non_empty(topdown.get("window"), default="UNKNOWN")
    topdown_driver = first_non_empty(topdown.get("driver"), topdown.get("dominant_driver"), default="UNKNOWN")

    live_packet = first_non_empty(live.get("packet"), default="NONE")
    live_bias = first_non_empty(live.get("bias"), default="NONE")
    live_level = first_non_empty(live.get("level"), default="NONE")
    live_tf = live.get("tf")
    live_score = live.get("score")
    live_count = live.get("live_count")
    live_dir = norm_direction(live_bias)

    b6_state = first_non_empty(b6.get("state"), multiread.get("b6_state"), default="UNKNOWN")
    b6_bias = first_non_empty(b6.get("bias"), multiread.get("b6_bias"), default="UNKNOWN")
    b6_action = first_non_empty(b6.get("action_level"), b6.get("b6_action"), default="WATCH")
    b6_level = first_non_empty(b6.get("level"), default="NONE")
    b6_score = b6.get("score")
    b6_evidence = b6.get("evidence", {}) if isinstance(b6.get("evidence"), dict) else {}
    b6_dir = norm_direction(b6_bias)

    sig_mode = first_non_empty(signal.get("mode"), default="UNKNOWN")
    sig_perm = first_non_empty(signal.get("permission"), default="UNKNOWN")
    data_status = first_non_empty(health.get("status"), data_health.get("global_status"), default="UNKNOWN")

    risks = compact_risks(
        multiread.get("technical_risks", []),
        live.get("risks", []),
        daily.get("technical_risks", []),
        topdown.get("technical_risks", []),
        health.get("technical_risks", []),
    )
    info_risks = compact_risks(
        multiread.get("informational_risks", []),
        b6.get("informational_risks", []),
    )

    action = "WATCH"
    att = str(attention).upper()
    glob = str(multiread_all.get("global_status", "")).upper()
    if "WAKE" in att or "WAKE" in glob or str(live.get("status", "")).upper() == "WAKE_TRADER":
        action = "WAKE_TRADER"
    elif "WATCH_ATTENTION" in att or str(live.get("status", "")).upper() == "WATCH_ATTENTION":
        action = "WATCH_ATTENTION"

    scenarios = scenario_lines(daily_dir, live_dir, b6_dir, str(synthesis), str(daily_intent))

    trader_line = reading
    if action == "WAKE_TRADER" and "CONFLICT" in str(synthesis).upper():
        trader_line = "Conflit actif : daily/topdown piège-rejet, live pousse en sens opposé. Surveiller réintégration, piège inverse ou second test."
    elif daily_dir == b6_dir and daily_dir != "NEUTRAL":
        trader_line = f"Contexte partiellement aligné {daily_dir} : daily et B6 pointent ensemble, live doit confirmer ou invalider."

    return {
        "symbol": symbol,
        "action": action,
        "attention": attention,
        "synthesis": synthesis,
        "alignment": alignment,
        "trader_line": trader_line,
        "topdown": {
            "flux": topdown_flux,
            "intention": topdown_intention,
            "window": topdown_window,
            "driver": topdown_driver,
        },
        "daily": {
            "intent": daily_intent,
            "prediction": daily_prediction,
            "close_position": daily_close,
            "direction": daily_dir,
            "tested": first_non_empty(daily.get("tested"), daily.get("tested_count"), default=None),
            "rejected": first_non_empty(daily.get("rejected"), daily.get("rejected_count"), default=None),
            "sweeps": first_non_empty(daily.get("sweeps"), daily.get("sweep_count"), default=None),
        },
        "live": {
            "packet": live_packet,
            "level": live_level,
            "bias": live_bias,
            "direction": live_dir,
            "tf": live_tf,
            "score": live_score,
            "live_count": live_count,
        },
        "b6": {
            "state": b6_state,
            "bias": b6_bias,
            "direction": b6_dir,
            "action": b6_action,
            "level": b6_level,
            "score": b6_score,
            "evidence": b6_evidence,
        },
        "signal_adaptive": {
            "mode": sig_mode,
            "permission": sig_perm,
        },
        "data_health": {
            "status": data_status,
        },
        "scenarios": scenarios,
        "technical_risks": risks,
        "informational_risks": info_risks,
        "sources": {
            "brief_txt_available": bool(brief_txt),
            "b6_txt_available": bool(b6_txt),
            "cockpit_live_txt_available": bool(cockpit_live_txt),
        },
    }


def render_txt(data: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append("POWERFLOW V7.3.5 - TRADER COCKPIT")
    lines.append(f"timestamp_utc={data.get('timestamp_utc')}")
    lines.append(f"global_status={data.get('global_status')}")
    lines.append("")
    for s in data.get("symbols", []):
        lines.append("=" * 72)
        lines.append(f"{s['symbol']} | {s['action']} | {s['synthesis']}")
        lines.append(f"alignment={s.get('alignment')}")
        lines.append(f"lecture={s.get('trader_line')}")
        lines.append("")
        lines.append("FEUX")
        lines.append(f"HTF={s['topdown'].get('intention')} | window={s['topdown'].get('window')} | flux={s['topdown'].get('flux')}")
        lines.append(f"DAILY={s['daily'].get('intent')} | close={s['daily'].get('close_position')} | dir={s['daily'].get('direction')}")
        lines.append(f"LIVE={s['live'].get('packet')} | bias={s['live'].get('bias')} | tf={s['live'].get('tf')} | score={s['live'].get('score')}")
        lines.append(f"B6={s['b6'].get('state')} | bias={s['b6'].get('bias')} | level={s['b6'].get('level')} | score={s['b6'].get('score')}")
        lines.append("")
        lines.append("SCENARIOS")
        for idx, scenario in enumerate(s.get("scenarios", []), 1):
            lines.append(f"{idx}. {scenario}")
        risks = s.get("technical_risks", [])
        if risks:
            lines.append("")
            lines.append("RISQUES TECHNIQUES")
            for r in risks:
                lines.append(f"- {r}")
    lines.append("")
    lines.append("Note: cockpit de perception. Aucun ordre. Le trader arbitre.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", default=".")
    ap.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    ap.add_argument("--trade-symbol", default="GBPUSD")
    ap.add_argument("--output", default="output/dashboard_surface/trader_cockpit.json")
    ap.add_argument("--txt", default="output/dashboard_surface/trader_cockpit.txt")
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    core = Path(args.core).resolve()
    symbols = [x.strip().upper() for x in args.symbols.split(",") if x.strip()]
    trade_symbol = args.trade_symbol.upper()
    ordered = [trade_symbol] + [s for s in symbols if s != trade_symbol]

    readings = [build_symbol(core, s) for s in ordered]
    global_status = "WATCH"
    if any(str(s.get("action", "")).upper() == "WAKE_TRADER" for s in readings):
        global_status = "WAKE_TRADER"
    elif any(str(s.get("action", "")).upper() == "WATCH_ATTENTION" for s in readings):
        global_status = "WATCH_ATTENTION"

    data = {
        "timestamp_utc": utc_now(),
        "method": "TRADER_COCKPIT_V735",
        "global_status": global_status,
        "trade_symbol": trade_symbol,
        "symbols": readings,
        "note": "Trader cockpit is a readable perception surface. It does not decide trades.",
    }

    out = core / args.output
    txt = core / args.txt
    write_json(out, data, pretty=args.pretty)
    txt.parent.mkdir(parents=True, exist_ok=True)
    txt.write_text(render_txt(data), encoding="utf-8")

    print(f"TRADER_COCKPIT_OK | global_status={global_status} | trade_symbol={trade_symbol} | symbols={len(readings)} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
