#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.3.4b — Multi-Read Synthesis hotfix.

Fix:
- Direction grammar:
  SHORT_ACCUMULATION = PAIR_DOWN
  LONG_ACCUMULATION = PAIR_UP
  SELL_SIDE = PAIR_DOWN
  BUY_SIDE = PAIR_UP
- B6 RELEASED + SELL_SIDE remains a live flow reading, not UNKNOWN.
- Context-symbol B6 absence is not treated as structural failure.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {"raw": obj}
    except Exception as exc:
        return {"technical_risks": [f"LOAD_ERROR:{path.name}:{type(exc).__name__}"]}


def write_json(path: Path, data: Dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2 if pretty else None, ensure_ascii=False), encoding="utf-8")


def deep_get(data: Dict[str, Any], *paths: str, default: Any = None) -> Any:
    for path in paths:
        obj: Any = data
        ok = True
        for part in path.split("."):
            if isinstance(obj, dict) and part in obj:
                obj = obj[part]
            else:
                ok = False
                break
        if ok and obj not in (None, "", [], {}):
            return obj
    return default


def list_find_by_symbol(data: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    symbol = symbol.upper()
    for key in ("symbols", "reports", "items", "rows"):
        seq = data.get(key)
        if isinstance(seq, list):
            for item in seq:
                if isinstance(item, dict) and str(item.get("symbol", "")).upper() == symbol:
                    return item
    packets = data.get("packets")
    if isinstance(packets, dict):
        item = packets.get(symbol) or packets.get(symbol.upper()) or packets.get(symbol.lower())
        if isinstance(item, dict):
            return item
    return {}


def as_text(value: Any, default: str = "UNKNOWN") -> str:
    if value is None:
        return default
    s = str(value).strip()
    return s if s else default


def direction_from_text(*values: Any) -> str:
    text = " ".join(as_text(v, "") for v in values).upper()

    # Strong explicit compound terms first.
    if "SHORT_ACCUMULATION" in text or "DISTRIBUTION_TRAP" in text:
        return "PAIR_DOWN"
    if "LONG_ACCUMULATION" in text or "STOP_HUNT" in text:
        return "PAIR_UP"
    if "HIGH_SWEEP" in text or "DOWNSIDE_ACCEPTANCE" in text:
        return "PAIR_DOWN"
    if "LOW_SWEEP" in text or "UPSIDE_ACCEPTANCE" in text:
        return "PAIR_UP"

    down_terms = (
        "PAIR_DOWN", "SELL_SIDE", "SELL_DOMINANT", "SELL", "SHORT", "BEARISH",
        "DOWNSIDE", "BREAK_PRESSURE_DOWN", "REJECTION_DOWN"
    )
    up_terms = (
        "PAIR_UP", "BUY_SIDE", "BUY_DOMINANT", "BUY", "LONG", "BULLISH",
        "UPSIDE", "BREAK_PRESSURE_UP", "REJECTION_UP"
    )

    down = any(t in text for t in down_terms)
    up = any(t in text for t in up_terms)

    if down and not up:
        return "PAIR_DOWN"
    if up and not down:
        return "PAIR_UP"
    if down and up:
        return "MIXED"
    return "NEUTRAL"


def alignment_state(daily_dir: str, topdown_dir: str, live_dir: str, b6_dir: str) -> str:
    dirs = [d for d in (daily_dir, topdown_dir, live_dir, b6_dir) if d not in {"UNKNOWN", "NEUTRAL", "NONE"}]
    if not dirs:
        return "NO_DIRECTIONAL_ALIGNMENT"
    if "MIXED" in dirs:
        return "MIXED_OR_AMBIGUOUS"
    ups = dirs.count("PAIR_UP")
    downs = dirs.count("PAIR_DOWN")
    if ups >= 3:
        return "BULLISH_ALIGNMENT"
    if downs >= 3:
        return "BEARISH_ALIGNMENT"
    if ups > 0 and downs > 0:
        return "CONFLICT"
    if ups > downs:
        return "PARTIAL_BULLISH_ALIGNMENT"
    if downs > ups:
        return "PARTIAL_BEARISH_ALIGNMENT"
    return "NO_DIRECTIONAL_ALIGNMENT"


def choose_attention(alignment: str, b6_action: str, live_status: str, risks: List[str]) -> str:
    b6 = b6_action.upper()
    live = live_status.upper()
    if any("DATA_STALE" in r for r in risks):
        return "DEGRADED_WATCH"
    if b6 == "WAKE_TRADER":
        return "WAKE_TRADER"
    if alignment in {"BULLISH_ALIGNMENT", "BEARISH_ALIGNMENT"} and b6 in {"WATCH_ATTENTION", "WAKE_TRADER"}:
        return "WAKE_TRADER"
    if "ALERT" in live or "WAKE" in live:
        return "WAKE_TRADER"
    if alignment == "CONFLICT":
        return "WATCH_ATTENTION_CONFLICT"
    if alignment in {"PARTIAL_BEARISH_ALIGNMENT", "PARTIAL_BULLISH_ALIGNMENT"} and b6 != "WATCH":
        return "WATCH_ATTENTION"
    if b6 == "WATCH_ATTENTION":
        return "WATCH_ATTENTION"
    return "WATCH"


def collect_risks(*objs: Dict[str, Any]) -> List[str]:
    risks: List[str] = []
    for obj in objs:
        for key in ("technical_risks", "risks", "critical_issues"):
            val = obj.get(key)
            if isinstance(val, list):
                for x in val:
                    s = str(x)
                    if s not in risks:
                        risks.append(s)
            elif val:
                s = str(val)
                if s not in risks:
                    risks.append(s)
    return risks


def filter_display_risks(risks: List[str]) -> List[str]:
    informational = {
        "ORDER_FLOW_PROXY_NOT_TRUE_LEVEL2",
        "MT4_NATIVE_BID_ASK_VOLUME_ABSENT",
        "M1_OHLC_PROXY_CAN_CREATE_FALSE_POSITIVES",
        "B6_CONTEXT_SYMBOL_NOT_RUN",
    }
    return [r for r in risks if r not in informational]


def build_symbol_synthesis(symbol: str, inputs: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    symbol = symbol.upper()

    daily = list_find_by_symbol(inputs["daily_journal"], symbol)
    topdown = list_find_by_symbol(inputs["topdown"], symbol)
    live = list_find_by_symbol(inputs["live_brief"], symbol)
    b6 = list_find_by_symbol(inputs["b6"], symbol)
    signal = list_find_by_symbol(inputs["signal_adaptive"], symbol)
    health = list_find_by_symbol(inputs["data_health"], symbol)

    root = Path("output/dashboard_surface") / symbol
    if not daily:
        daily = load_json(root / "daily_journal.json")
    if not topdown:
        topdown = load_json(root / "topdown_market_reader.json")
    if not live:
        live = load_json(root / "powerflow_live_brief.json")
    if not b6:
        b6 = load_json(root / "b6_live_fusion.json")

    daily_intent = as_text(deep_get(daily, "intent", "intent_detected", "daily_packet.intent_detected", default="UNKNOWN"))
    daily_prediction = as_text(deep_get(daily, "prediction", "prediction_next_session", "daily_packet.prediction_next_session", default="UNKNOWN"))
    close_position = as_text(deep_get(daily, "close_position", "daily_packet.journal_levels.close_position", default="UNKNOWN"))

    topdown_flux = as_text(deep_get(topdown, "flux", "htf_read", "context.htf_read", "summary.flux", default="UNKNOWN"))
    topdown_intention = as_text(deep_get(topdown, "machine_intention", "plan_bias", "summary.machine_intention", default="UNKNOWN"))
    topdown_window = as_text(deep_get(topdown, "window", "global_window", "entry_attention", default="UNKNOWN"))

    live_status = as_text(deep_get(live, "status", "action", "state", default="UNKNOWN"))
    live_synthesis = as_text(deep_get(live, "synthesis", "reading_state", default=deep_get(live, "summary.synthesis", default="UNKNOWN")))
    live_packet = as_text(deep_get(live, "packet", "live.packet", default="NONE"))
    live_bias = as_text(deep_get(live, "bias", "live.bias", default="NONE"))

    b6_state = as_text(deep_get(b6, "state", "live_flow_state", "b6_state", "fusion_state", default="UNKNOWN"))
    b6_bias = as_text(deep_get(b6, "bias", "pressure_bias", "direction", default="NONE"))
    b6_action = as_text(deep_get(b6, "action_level", "level", "alert_level", default="WATCH"))
    b6_reading = as_text(deep_get(b6, "reading", "message", "narrative", default=""))

    signal_mode = as_text(deep_get(signal, "mode", "signal_mode", default="UNKNOWN"))
    signal_permission = as_text(deep_get(signal, "signal_permission", "permission", default="UNKNOWN"))
    data_status = as_text(deep_get(health, "status", "global_status", default="UNKNOWN"))

    daily_dir = direction_from_text(daily_intent, daily_prediction)
    topdown_dir = direction_from_text(topdown_flux, topdown_intention)
    live_dir = direction_from_text(live_synthesis, live_packet, live_bias)
    b6_dir = direction_from_text(b6_state, b6_bias, b6_reading)

    align = alignment_state(daily_dir, topdown_dir, live_dir, b6_dir)
    raw_risks = collect_risks(daily, topdown, live, b6, signal, health)
    risks = filter_display_risks(raw_risks)
    attention = choose_attention(align, b6_action, live_status, risks)

    if align == "BEARISH_ALIGNMENT":
        synthesis = "DAILY_TOPDOWN_B6_BEARISH_ALIGNMENT"
    elif align == "BULLISH_ALIGNMENT":
        synthesis = "DAILY_TOPDOWN_B6_BULLISH_ALIGNMENT"
    elif align == "CONFLICT":
        synthesis = "MULTIREAD_CONFLICT"
    elif align == "PARTIAL_BEARISH_ALIGNMENT":
        synthesis = "PARTIAL_BEARISH_CONTEXT_WITH_B6"
    elif align == "PARTIAL_BULLISH_ALIGNMENT":
        synthesis = "PARTIAL_BULLISH_CONTEXT_WITH_B6"
    elif b6_state not in {"UNKNOWN", "B6_MISSING", "B6_CONTEXT_NOT_RUN"}:
        synthesis = "B6_CONTEXT_ADDED"
    else:
        synthesis = "CONTEXT_ONLY_WAIT_B6"

    reading_parts = [
        f"Daily={daily_intent}",
        f"Topdown={topdown_intention}",
        f"LiveBrief={live_synthesis}",
        f"B6={b6_state}/{b6_bias}",
        f"Alignment={align}",
    ]

    return {
        "symbol": symbol,
        "attention": attention,
        "synthesis": synthesis,
        "alignment": align,
        "directions": {
            "daily": daily_dir,
            "topdown": topdown_dir,
            "live_brief": live_dir,
            "b6": b6_dir,
        },
        "daily": {
            "intent": daily_intent,
            "prediction": daily_prediction,
            "close_position": close_position,
        },
        "topdown": {
            "flux": topdown_flux,
            "machine_intention": topdown_intention,
            "window": topdown_window,
        },
        "live_brief": {
            "status": live_status,
            "synthesis": live_synthesis,
            "packet": live_packet,
            "bias": live_bias,
        },
        "b6": {
            "state": b6_state,
            "bias": b6_bias,
            "action_level": b6_action,
            "reading": b6_reading,
        },
        "signal_adaptive": {
            "mode": signal_mode,
            "permission": signal_permission,
        },
        "data_health": {
            "status": data_status,
        },
        "reading": " | ".join(reading_parts),
        "technical_risks": risks,
        "informational_risks": [r for r in raw_risks if r not in risks],
    }


def write_symbol_txt(symbol: str, item: Dict[str, Any]) -> None:
    out = Path("output/dashboard_surface") / symbol / "powerflow_multiread_synthesis.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"{symbol} | {item['attention']} | {item['synthesis']}",
        f"alignment={item['alignment']}",
        f"directions=daily:{item['directions']['daily']} topdown:{item['directions']['topdown']} live:{item['directions']['live_brief']} b6:{item['directions']['b6']}",
        "",
        "DAILY",
        f"intent={item['daily']['intent']}",
        f"prediction={item['daily']['prediction']}",
        f"close_position={item['daily']['close_position']}",
        "",
        "TOPDOWN",
        f"flux={item['topdown']['flux']}",
        f"machine_intention={item['topdown']['machine_intention']}",
        f"window={item['topdown']['window']}",
        "",
        "LIVE BRIEF",
        f"status={item['live_brief']['status']}",
        f"synthesis={item['live_brief']['synthesis']}",
        f"packet={item['live_brief']['packet']}",
        f"bias={item['live_brief']['bias']}",
        "",
        "B6",
        f"state={item['b6']['state']}",
        f"bias={item['b6']['bias']}",
        f"action_level={item['b6']['action_level']}",
        f"reading={item['b6']['reading']}",
        "",
        "SIGNAL / DATA",
        f"signal_mode={item['signal_adaptive']['mode']}",
        f"signal_permission={item['signal_adaptive']['permission']}",
        f"data_status={item['data_health']['status']}",
        "",
        "RISKS",
    ]
    risks = item.get("technical_risks") or []
    if risks:
        lines.extend(f"- {risk}" for risk in risks)
    else:
        lines.append("- none")
    info = item.get("informational_risks") or []
    if info:
        lines.append("")
        lines.append("INFO")
        lines.extend(f"- {risk}" for risk in info)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def global_status(items: List[Dict[str, Any]]) -> str:
    if any(x["attention"] == "WAKE_TRADER" for x in items):
        return "MULTIREAD_WAKE_TRADER"
    if any("CONFLICT" in x["attention"] for x in items):
        return "MULTIREAD_CONFLICT_WATCH"
    if any(x["attention"] == "WATCH_ATTENTION" for x in items):
        return "MULTIREAD_WATCH_ATTENTION"
    return "MULTIREAD_WATCH"


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--output", default="output/dashboard_surface/powerflow_multiread_synthesis.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    inputs = {
        "daily_journal": load_json(Path("output/dashboard_surface/daily_journal_dashboard.json")),
        "topdown": load_json(Path("output/dashboard_surface/topdown_reader.json")),
        "live_brief": load_json(Path("output/dashboard_surface/live_brief_dashboard.json")),
        "b6": load_json(Path("output/dashboard_surface/b6_live_fusion_dashboard.json")),
        "signal_adaptive": load_json(Path("output/dashboard_surface/signal_adaptive.json")),
        "data_health": load_json(Path("output/dashboard_surface/data_health.json")),
    }

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    items = [build_symbol_synthesis(symbol, inputs) for symbol in symbols]
    for item in items:
        write_symbol_txt(item["symbol"], item)

    critical: List[str] = []
    for item in items:
        for risk in item.get("technical_risks", []):
            if risk not in critical:
                critical.append(risk)

    out = {
        "timestamp_utc": now_iso(),
        "method": "POWERFLOW_MULTIREAD_SYNTHESIS_V734B",
        "global_status": global_status(items),
        "symbols": items,
        "critical_issues": critical,
        "note": "Multi-read synthesis names alignment/conflict between Daily, Topdown, Live Brief and B6. It does not decide trades.",
    }

    write_json(Path(args.output), out, pretty=args.pretty)
    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"MULTIREAD_SYNTHESIS_OK | global_status={out['global_status']} | symbols={len(items)} | out={args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
