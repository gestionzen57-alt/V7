#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.3.4b — B6 Live Fusion normalizer hotfix.

Fix:
- Parse B6 text fallback lines:
  state=RELEASED level=INFO tension=...
  direction=SELL_SIDE absorption=...
- Map SELL_SIDE / BUY_SIDE to PAIR_DOWN / PAIR_UP.
- Treat missing B6 on context symbols as informational if only one trade symbol is running B6.
- Do not classify B6 proxy limitations as critical blocking issues.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


INFO_RISKS = {
    "ORDER_FLOW_PROXY_NOT_TRUE_LEVEL2",
    "MT4_NATIVE_BID_ASK_VOLUME_ABSENT",
    "M1_OHLC_PROXY_CAN_CREATE_FALSE_POSITIVES",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {"raw": obj}
    except Exception as exc:
        return {"technical_risks": [f"B6_JSON_LOAD_ERROR:{type(exc).__name__}"]}


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


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


def upper_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s.upper() if s else None


def parse_txt_kv(txt: str) -> Dict[str, str]:
    """
    Parse compact B6 txt lines:
    state=RELEASED level=INFO tension=32.2 delta=-375.6886
    direction=SELL_SIDE absorption=PARTIAL_ABSORPTION imbalance=SELL_DOMINANT alerts=0
    """
    out: Dict[str, str] = {}
    for line in txt.splitlines():
        for k, v in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s]+)", line):
            out[k.lower()] = v.strip()
    return out


def normalize_bias(value: Any) -> str:
    s = upper_or_none(value) or "UNKNOWN"
    aliases = {
        "DOWN": "PAIR_DOWN",
        "SELL": "PAIR_DOWN",
        "SHORT": "PAIR_DOWN",
        "BEARISH": "PAIR_DOWN",
        "SELL_SIDE": "PAIR_DOWN",
        "SELL_DOMINANT": "PAIR_DOWN",
        "OFFER_DOMINANT": "PAIR_DOWN",
        "ASK_DOMINANT": "PAIR_DOWN",
        "UP": "PAIR_UP",
        "BUY": "PAIR_UP",
        "LONG": "PAIR_UP",
        "BULLISH": "PAIR_UP",
        "BUY_SIDE": "PAIR_UP",
        "BUY_DOMINANT": "PAIR_UP",
        "BID_DOMINANT": "PAIR_UP",
        "NEUTRAL": "NEUTRAL",
        "NONE": "NONE",
    }
    return aliases.get(s, s)


def infer_action_level(state: str, level: str, freshness: str, risks: List[str], txt_kv: Dict[str, str]) -> str:
    st = state.upper()
    lv = level.upper()
    fr = freshness.upper()

    # B6 says no immediate pressure / no alert -> keep watch, not wake.
    if "NO_ALERT" in st or lv in {"INFO", "NONE"}:
        return "WATCH"
    if fr in {"STALE", "EXPIRED", "NO_LIVE_PACKET", "NONE"} and lv not in {"HOT", "ACTIVE"}:
        return "WATCH"
    if lv in {"HOT", "ACTIVE"}:
        if any(k in st for k in ("CONFIRMED", "REJECTION", "ACCEPTANCE", "FLOW_TURN", "SECOND_LEG", "IMPULSE")):
            return "WAKE_TRADER"
        return "WATCH_ATTENTION"
    if any(k in st for k in ("CONFLICT", "REINTEGRATION", "TRAP", "ABSORPTION", "REJECTION", "PRESSURE")):
        return "WATCH_ATTENTION"
    return "WATCH"


def infer_freshness(data: Dict[str, Any], txt: str) -> str:
    freshness = deep_get(data, "freshness", "live.freshness", "packet_freshness", "status.freshness", default=None)
    if freshness:
        return str(freshness).upper()

    live_count = deep_get(data, "live_count", "live.live_count", "live.count", default=None)
    expired_count = deep_get(data, "expired_count", "old_count", "live.expired_count", default=None)
    if live_count is not None:
        try:
            if int(live_count) > 0:
                return "LIVE"
        except Exception:
            pass
    if expired_count is not None:
        try:
            if int(expired_count) > 0:
                return "STALE"
        except Exception:
            pass

    up = txt.upper()
    if "NO_LIVE_PACKET" in up:
        return "NO_LIVE_PACKET"
    if "B6.1" in up:
        return "LIVE"
    if "LIVE" in up and "EXPIRED" not in up:
        return "LIVE"
    if "EXPIRED" in up or "STALE" in up:
        return "STALE"
    return "UNKNOWN"


def extract_risks(*objs: Any) -> List[str]:
    out: List[str] = []
    for obj in objs:
        if isinstance(obj, dict):
            vals = []
            for key in ("technical_risks", "risks", "risk_flags", "warnings"):
                v = obj.get(key)
                if isinstance(v, list):
                    vals.extend(v)
                elif v:
                    vals.append(v)
            for val in vals:
                s = str(val)
                if s not in out:
                    out.append(s)
    return out


def normalize_symbol(symbol: str, trade_symbol: str) -> Dict[str, Any]:
    symbol = symbol.upper()
    trade_symbol = trade_symbol.upper()
    root = Path("output/dashboard_surface") / symbol
    json_path = root / "b6_live_fusion.json"
    txt_path = root / "b6_live_fusion.txt"

    data = load_json(json_path)
    txt = read_text(txt_path)
    txt_kv = parse_txt_kv(txt)

    state = upper_or_none(deep_get(
        data,
        "live_flow_state",
        "state",
        "b6_state",
        "fusion_state",
        "order_flow_state",
        "reading_state",
        "status",
        "summary.state",
        default=None,
    )) or upper_or_none(txt_kv.get("state"))

    level = upper_or_none(deep_get(
        data,
        "action_level",
        "level",
        "alert_level",
        "packet.level",
        "live.level",
        "summary.level",
        default=None,
    )) or upper_or_none(txt_kv.get("level")) or "NONE"

    raw_bias = deep_get(
        data,
        "pressure_bias",
        "bias",
        "direction",
        "packet.bias",
        "live.bias",
        "summary.bias",
        default=None,
    ) or txt_kv.get("direction") or txt_kv.get("imbalance")
    bias = normalize_bias(raw_bias)

    freshness = infer_freshness(data, txt)

    reading = deep_get(
        data,
        "reading",
        "summary.reading",
        "message",
        "narrative",
        "explain",
        default=None,
    )
    if not reading:
        first_lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
        reading = first_lines[0] if first_lines else ""

    alignment = deep_get(data, "alignment", "context_alignment", default={})
    if not isinstance(alignment, dict):
        alignment = {"raw": alignment}

    evidence = deep_get(data, "evidence", "signals", "components", default={})
    if not isinstance(evidence, dict):
        evidence = {"raw": evidence}
    # Enrich evidence from B6 text.
    for k in ("tension", "delta", "direction", "absorption", "imbalance", "alerts"):
        if k in txt_kv and k not in evidence:
            evidence[k] = txt_kv[k]

    score = deep_get(data, "score", "fusion_score", "confidence", "robustness", default=None)
    if score is None and "tension" in txt_kv:
        try:
            score = float(txt_kv["tension"])
        except Exception:
            score = txt_kv["tension"]

    risks = extract_risks(data)

    if not data and not txt:
        if symbol == trade_symbol:
            risks.append("B6_OUTPUT_MISSING")
            state = "B6_MISSING"
            reading = "B6 output missing for trade symbol."
        else:
            risks.append("B6_CONTEXT_SYMBOL_NOT_RUN")
            state = "B6_CONTEXT_NOT_RUN"
            reading = "B6 not run for context symbol; expected when B6 is trade-symbol scoped."
        freshness = "UNKNOWN"

    if state is None:
        state = "B6_STATE_UNKNOWN"
        risks.append("B6_STATE_UNKNOWN")

    action_level = infer_action_level(state, level, freshness, risks, txt_kv)

    return {
        "symbol": symbol,
        "trade_symbol_scope": symbol == trade_symbol,
        "state": state,
        "bias": bias,
        "level": level,
        "freshness": freshness,
        "score": score,
        "action_level": action_level,
        "alignment": alignment,
        "evidence": evidence,
        "reading": str(reading or ""),
        "source_json": str(json_path),
        "source_txt": str(txt_path),
        "txt_preview": txt[:1500],
        "technical_risks": risks,
        "informational_risks": [r for r in risks if r in INFO_RISKS or r == "B6_CONTEXT_SYMBOL_NOT_RUN"],
    }


def compute_global_status(rows: List[Dict[str, Any]]) -> str:
    trade_rows = [r for r in rows if r.get("trade_symbol_scope")]
    focus = trade_rows or rows
    if any(r.get("action_level") == "WAKE_TRADER" for r in focus):
        return "B6_WAKE_TRADER"
    if any(r.get("action_level") == "WATCH_ATTENTION" for r in focus):
        return "B6_WATCH_ATTENTION"
    if any(r.get("state") not in {"B6_MISSING", "B6_STATE_UNKNOWN", "B6_CONTEXT_NOT_RUN"} for r in focus):
        return "B6_WATCH"
    return "B6_NO_READING"


def is_critical_risk(risk: str, row: Dict[str, Any]) -> bool:
    if risk in INFO_RISKS:
        return False
    if risk == "B6_CONTEXT_SYMBOL_NOT_RUN":
        return False
    if risk == "B6_OUTPUT_MISSING" and not row.get("trade_symbol_scope"):
        return False
    return True


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", default="GBPUSD")
    parser.add_argument("--trade-symbol", default="GBPUSD")
    parser.add_argument("--output", default="output/dashboard_surface/b6_live_fusion_dashboard.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    rows = [normalize_symbol(symbol, args.trade_symbol) for symbol in symbols]

    critical: List[str] = []
    for row in rows:
        for risk in row.get("technical_risks", []):
            if is_critical_risk(risk, row) and risk not in critical:
                critical.append(risk)

    out = {
        "timestamp_utc": now_iso(),
        "method": "B6_LIVE_FUSION_DASHBOARD_NORMALIZED_V734B",
        "trade_symbol": args.trade_symbol.upper(),
        "global_status": compute_global_status(rows),
        "symbols": rows,
        "critical_issues": critical,
        "note": "B6 is treated as a complete parallel live-flow reading layer. Context-symbol B6 absence is informational.",
    }

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(out, indent=2 if args.pretty else None, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"B6_LIVE_FUSION_NORMALIZE_OK | global_status={out['global_status']} | symbols={len(rows)} | out={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
