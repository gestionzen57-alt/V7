from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def write_json(path: Path, data: Any, pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if pretty:
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    else:
        path.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def pick_symbol(items: Any, symbol: str) -> Dict[str, Any]:
    if isinstance(items, dict):
        if symbol in items and isinstance(items[symbol], dict):
            return items[symbol]
        for key in ("symbols", "reports", "packets"):
            if key in items:
                found = pick_symbol(items[key], symbol)
                if found:
                    return found
    if isinstance(items, list):
        for item in items:
            if isinstance(item, dict) and str(item.get("symbol", "")).upper() == symbol.upper():
                return item
    return {}


def norm_direction(value: Any) -> str:
    v = str(value or "").upper()
    if v in {"PAIR_UP", "UP", "BULLISH", "LONG", "BUY", "BUY_SIDE"}:
        return "PAIR_UP"
    if v in {"PAIR_DOWN", "DOWN", "BEARISH", "SHORT", "SELL", "SELL_SIDE"}:
        return "PAIR_DOWN"
    if "DOWN" in v or "SHORT" in v or "SELL" in v or "BEAR" in v:
        return "PAIR_DOWN"
    if "UP" in v or "LONG" in v or "BUY" in v or "BULL" in v:
        return "PAIR_UP"
    return "NEUTRAL"


def simplify_risk(risk: str) -> str:
    mapping = {
        "DATA_HEALTH_STATUS_HTF_INCOMPLETE": "HTF incomplet",
        "GBPUSD_TEMPORAL_GAPS_PRESENT": "Gaps temporels GBPUSD",
        "EURUSD_TEMPORAL_GAPS_PRESENT": "Gaps temporels EURUSD",
        "USDJPY_TEMPORAL_GAPS_PRESENT": "Gaps temporels USDJPY",
        "DAILY_LOW_SAMPLE_FOR_ROTATION": "Daily peu profond",
        "WEEKLY_LOW_SAMPLE_FOR_ROTATION": "Weekly peu profond",
        "CURRENT_DAY_SAMPLE_THIN": "Session du jour peu profonde",
        "PREVIOUS_DAY_REFERENCE_MISSING": "Reference jour precedent manquante",
        "HTF_STRUCTURE_WEAK_DO_NOT_BLOCK_M1": "Structure HTF faible, M1 non bloque",
        "EURUSD_HTF_THIN_H4": "EURUSD H4 peu profond",
        "USDJPY_HTF_THIN_H4": "USDJPY H4 peu profond",
        "EURUSD_D1_NOT_READY": "EURUSD D1 non pret",
        "USDJPY_D1_NOT_READY": "USDJPY D1 non pret",
    }
    return mapping.get(str(risk), str(risk).replace("_", " ").lower())


def risk_gravity(risk: str) -> int:
    r = str(risk).upper()
    if "DATA_HEALTH" in r or "TEMPORAL_GAPS" in r:
        return 0
    if "HTF" in r or "D1" in r:
        return 1
    if "DAILY" in r or "WEEKLY" in r or "SAMPLE" in r:
        return 2
    return 3


def clean_risks(risks: Iterable[Any]) -> List[Dict[str, str]]:
    raw = []
    for r in risks or []:
        s = str(r)
        if not s or s == "None":
            continue
        raw.append(s)
    out = []
    seen = set()
    for r in sorted(raw, key=risk_gravity):
        if r not in seen:
            seen.add(r)
            out.append({"label": simplify_risk(r), "technical_key": r})
    return out


def context_attention(symbol: str, trade_symbol: str, item: Dict[str, Any]) -> str:
    if symbol.upper() != trade_symbol.upper():
        # Context pairs must not steal attention from the trade symbol.
        raw = str(item.get("attention") or item.get("status") or "WATCH_CONTEXT").upper()
        if "WAKE" in raw or "ALERT" in raw:
            return "WATCH_CONTEXT"
        return "WATCH_CONTEXT"
    return str(item.get("attention") or item.get("status") or "WATCH").upper()


def infer_direct_state(main: Dict[str, Any]) -> Dict[str, str]:
    directions = main.get("directions") if isinstance(main.get("directions"), dict) else {}
    daily_dir = norm_direction(directions.get("daily") or main.get("daily_intent") or main.get("daily", {}).get("intent"))
    live_dir = norm_direction(directions.get("live_brief") or main.get("live_brief", {}).get("bias") or main.get("live_brief"))
    b6_dir = norm_direction(directions.get("b6") or main.get("b6", {}).get("bias") or main.get("b6_bias"))

    synthesis = str(main.get("synthesis") or "").upper()
    alignment = str(main.get("alignment") or "").upper()

    if daily_dir == "PAIR_DOWN" and b6_dir == "PAIR_DOWN" and live_dir == "PAIR_UP":
        state = "CONFLIT DAILY/B6 vs LIVE"
        watch = "reintegration, echec PAIR_UP, second test, bascule PAIR_DOWN"
    elif "CONFLICT" in synthesis or "MIXED" in alignment:
        state = "CONFLIT MULTI-LECTURE"
        watch = "reintegration, piege inverse, second test, bascule nette"
    elif "BEARISH" in alignment or (daily_dir == "PAIR_DOWN" and b6_dir == "PAIR_DOWN"):
        state = "CONTEXTE BAISSIER PARTIEL"
        watch = "acceptation basse, rejet de reprise, acceleration apres relais"
    elif "BULLISH" in alignment or daily_dir == "PAIR_UP":
        state = "CONTEXTE HAUSSIER PARTIEL"
        watch = "acceptation haute, rejet de repli, continuation apres relais"
    else:
        state = "SURVEILLANCE CONTEXTE"
        watch = "rejet, acceptation, compression, relachement"

    return {"state": state, "watch": watch}


def build(args: argparse.Namespace) -> Dict[str, Any]:
    symbols = [s.strip().upper() for s in str(args.symbols).split(",") if s.strip()]
    trade_symbol = str(args.trade_symbol).upper()
    base = Path(args.base)

    multiread = read_json(base / "output/dashboard_surface/powerflow_multiread_synthesis.json", {})
    multiread_dash = read_json(base / "output/dashboard_surface/multiread_synthesis_dashboard.json", {})
    live_dash = read_json(base / "output/dashboard_surface/live_brief_dashboard.json", {})
    b6_dash = read_json(base / "output/dashboard_surface/b6_live_fusion_dashboard.json", {})
    daily_dash = read_json(base / "output/dashboard_surface/daily_journal_dashboard.json", {})
    topdown_dash = read_json(base / "output/dashboard_surface/topdown_reader.json", {})

    main = pick_symbol(multiread, trade_symbol) or pick_symbol(multiread_dash, trade_symbol)
    direct = infer_direct_state(main)

    daily = main.get("daily") if isinstance(main.get("daily"), dict) else pick_symbol(daily_dash, trade_symbol)
    topdown = main.get("topdown") if isinstance(main.get("topdown"), dict) else pick_symbol(topdown_dash, trade_symbol)
    live = main.get("live_brief") if isinstance(main.get("live_brief"), dict) else pick_symbol(live_dash, trade_symbol)
    b6 = main.get("b6") if isinstance(main.get("b6"), dict) else pick_symbol(b6_dash, trade_symbol)

    attention = str(main.get("attention") or pick_symbol(multiread_dash, trade_symbol).get("attention") or "WATCH").upper()
    if "WAKE" in attention:
        action = "WAKE_TRADER"
    elif "CONFLICT" in attention:
        action = "WATCH_CONFLICT"
    else:
        action = attention

    context = []
    for symbol in symbols:
        if symbol == trade_symbol:
            continue
        m = pick_symbol(multiread, symbol) or pick_symbol(multiread_dash, symbol)
        context.append({
            "symbol": symbol,
            "attention": context_attention(symbol, trade_symbol, m),
            "synthesis": str(m.get("synthesis") or "CONTEXT_ONLY"),
            "alignment": str(m.get("alignment") or "UNKNOWN"),
            "daily": m.get("daily", {}) if isinstance(m.get("daily"), dict) else {"intent": m.get("daily_intent")},
            "topdown": m.get("topdown", {}) if isinstance(m.get("topdown"), dict) else {"machine_intention": m.get("topdown_intention")},
            "live_brief": m.get("live_brief", {}) if isinstance(m.get("live_brief"), dict) else {"synthesis": m.get("live_brief")},
            "b6": m.get("b6", {}) if isinstance(m.get("b6"), dict) else {"state": m.get("b6_state"), "bias": m.get("b6_bias")},
        })

    risks = clean_risks(main.get("technical_risks") or pick_symbol(multiread_dash, trade_symbol).get("technical_risks") or [])
    info_risks = clean_risks(main.get("informational_risks") or [])

    data = {
        "timestamp_utc": utc_now(),
        "method": "TRADER_COCKPIT_V735B_CLARITY",
        "trade_symbol": trade_symbol,
        "global_action": action,
        "direct_state": direct,
        "main": {
            "symbol": trade_symbol,
            "attention": attention,
            "synthesis": str(main.get("synthesis") or "UNKNOWN"),
            "alignment": str(main.get("alignment") or "UNKNOWN"),
            "directions": main.get("directions", {}),
            "reading": str(main.get("reading") or ""),
            "daily": daily or {},
            "topdown": topdown or {},
            "live": live or {},
            "b6": b6 or {},
            "risks": risks,
            "informational_risks": info_risks,
        },
        "context_symbols": context,
        "scenarios": build_scenarios(direct, main),
        "note": "Trader cockpit clarity surface. One page, one trade symbol, context pairs do not steal attention.",
    }
    return data


def build_scenarios(direct: Dict[str, str], main: Dict[str, Any]) -> List[str]:
    scenarios = []
    state = direct.get("state", "")
    if "CONFLIT" in state:
        scenarios.extend([
            "Reintegration apres poussee live contraire.",
            "Echec PAIR_UP puis retour vers pression daily/B6.",
            "Second test du niveau sweep / rejet daily.",
            "Bascule live vers PAIR_DOWN = conflit qui se resout.",
            "B6 diverge du live : surveiller absorption / friction avant acceleration.",
        ])
    elif "BAISSIER" in state:
        scenarios.extend([
            "Acceptation basse apres rejet haut.",
            "Pullback absorbe puis second leg baissier.",
            "Live doit confirmer PAIR_DOWN pour reveil plus fort.",
        ])
    elif "HAUSSIER" in state:
        scenarios.extend([
            "Acceptation haute apres sweep bas / reprise.",
            "Pullback absorbe puis continuation haussiere.",
            "Live doit rester PAIR_UP pour valider le relais.",
        ])
    else:
        scenarios.extend([
            "Attendre rejet ou acceptation nette.",
            "Observer compression puis relachement.",
            "Surveiller leader/follower et second test.",
        ])
    return scenarios


def build_txt(data: Dict[str, Any]) -> str:
    main = data["main"]
    lines = []
    lines.append(f"{data['trade_symbol']} | {data['global_action']} | {main.get('synthesis')}")
    lines.append(f"ETAT={data['direct_state']['state']}")
    lines.append(f"SURVEILLER={data['direct_state']['watch']}")
    lines.append("")
    lines.append(f"READING={main.get('reading','')}")
    lines.append("")
    for name, key in [("DAILY", "daily"), ("TOPDOWN", "topdown"), ("LIVE", "live"), ("B6", "b6")]:
        obj = main.get(key) or {}
        lines.append(name)
        if isinstance(obj, dict):
            for k, v in list(obj.items())[:8]:
                if isinstance(v, (dict, list)):
                    continue
                lines.append(f"{k}={v}")
        lines.append("")
    lines.append("SCENARIOS")
    for s in data.get("scenarios", []):
        lines.append(f"- {s}")
    lines.append("")
    lines.append("RISQUES UTILES")
    for r in main.get("risks", []):
        lines.append(f"- {r['label']} ({r['technical_key']})")
    return "\n".join(lines) + "\n"


def main(argv: Optional[Iterable[str]] = None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=".")
    p.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    p.add_argument("--trade-symbol", default="GBPUSD")
    p.add_argument("--output", default="output/dashboard_surface/trader_cockpit.json")
    p.add_argument("--txt", default="output/dashboard_surface/trader_cockpit.txt")
    p.add_argument("--pretty", action="store_true")
    args = p.parse_args(argv)

    data = build(args)
    out = Path(args.base) / args.output
    txt = Path(args.base) / args.txt
    write_json(out, data, pretty=True)
    txt.parent.mkdir(parents=True, exist_ok=True)
    txt.write_text(build_txt(data), encoding="utf-8")
    print(f"TRADER_COCKPIT_V735B_OK | action={data['global_action']} | state={data['direct_state']['state']} | out={out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
