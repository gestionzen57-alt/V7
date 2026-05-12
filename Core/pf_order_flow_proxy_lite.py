#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow B6 - Order Flow Proxy Lite

But:
- Lire force_snapshots_v2 en READ_ONLY.
- Estimer une microstructure proxy depuis OHLC M1.
- Produire output/dashboard_surface/<SYMBOL>/microstructure_state.json.
- Ne modifie pas la DB.
- Ne remplace pas le vrai order flow bid/ask volume.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


PREFERRED_TABLES = ("force_snapshots_v2", "force_snapshots")


@dataclass
class M1Row:
    created_at: str
    open: float
    high: float
    low: float
    close: float
    volume: Optional[float]
    spread: Optional[float]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    try:
        s = str(value).replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def safe_float(v: Any) -> Optional[float]:
    try:
        if v is None:
            return None
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except Exception:
        return None


def table_columns(cur: sqlite3.Cursor, table: str) -> List[str]:
    return [r[1] for r in cur.execute(f"PRAGMA table_info({table})").fetchall()]


def pick_ohlc_table(cur: sqlite3.Cursor) -> Tuple[str, Dict[str, str]]:
    existing = {r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    for table in PREFERRED_TABLES:
        if table not in existing:
            continue
        cols = table_columns(cur, table)
        needed = {"symbol", "timeframe", "created_at", "open", "high", "low", "close"}
        if needed.issubset(set(cols)):
            mapping = {
                "table": table,
                "symbol": "symbol",
                "timeframe": "timeframe",
                "timestamp": "created_at",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume" if "volume" in cols else None,
                "spread": "spread" if "spread" in cols else None,
            }
            return table, mapping
    raise RuntimeError("NO_OHLC_TABLE_WITH_REQUIRED_COLUMNS")


def load_m1_rows(db: Path, symbol: str, lookback_rows: int) -> Tuple[List[M1Row], Dict[str, Any]]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    cur = con.cursor()
    table, m = pick_ohlc_table(cur)

    vol_expr = m["volume"] if m["volume"] else "NULL"
    spr_expr = m["spread"] if m["spread"] else "NULL"

    q = f"""
    SELECT {m['timestamp']}, {m['open']}, {m['high']}, {m['low']}, {m['close']}, {vol_expr}, {spr_expr}
    FROM {table}
    WHERE {m['symbol']}=? AND {m['timeframe']}=1
    ORDER BY {m['timestamp']} DESC
    LIMIT ?
    """

    raw = cur.execute(q, (symbol, lookback_rows)).fetchall()
    con.close()

    rows: List[M1Row] = []
    for r in reversed(raw):
        o = safe_float(r[1])
        h = safe_float(r[2])
        l = safe_float(r[3])
        c = safe_float(r[4])
        if o is None or h is None or l is None or c is None:
            continue
        rows.append(M1Row(
            created_at=str(r[0]),
            open=o,
            high=h,
            low=l,
            close=c,
            volume=safe_float(r[5]),
            spread=safe_float(r[6]),
        ))

    meta = {
        "table": table,
        "schema": m,
        "rows_loaded": len(rows),
        "lookback_rows": lookback_rows,
    }
    return rows, meta


def infer_proxy_delta(row: M1Row, pip_factor: float) -> Dict[str, Any]:
    rng = max(row.high - row.low, 0.0)
    body = row.close - row.open

    if rng <= 0:
        close_position = 0.5
        body_ratio = 0.0
    else:
        close_position = max(0.0, min(1.0, (row.close - row.low) / rng))
        body_ratio = max(-1.0, min(1.0, body / rng))

    close_pressure = (close_position - 0.5) * 2.0
    raw_pressure = 0.55 * body_ratio + 0.45 * close_pressure

    spread = row.spread if row.spread is not None else 0.0
    vol = row.volume if row.volume is not None and row.volume > 0 else 1.0

    # Compression volontaire: volume MT4 peut exploser, on log-scale.
    vol_weight = 1.0 + min(math.log10(1.0 + vol), 3.0) / 3.0

    # Spread friction: si le spread s'élargit, la pression est plus chargée,
    # mais on évite de transformer le spread seul en signal.
    spread_weight = 1.0 + min(max(spread, 0.0), 8.0) / 20.0

    proxy_delta = raw_pressure * 100.0 * vol_weight * spread_weight

    return {
        "timestamp": row.created_at,
        "open": row.open,
        "high": row.high,
        "low": row.low,
        "close": row.close,
        "range_pips_proxy": round(rng * pip_factor, 3),
        "body_pips_proxy": round(body * pip_factor, 3),
        "close_position": round(close_position, 4),
        "body_ratio": round(body_ratio, 4),
        "raw_pressure": round(raw_pressure, 4),
        "volume": row.volume,
        "spread": row.spread,
        "proxy_delta": round(proxy_delta, 4),
        "direction": "BUY_PROXY" if proxy_delta > 0 else "SELL_PROXY" if proxy_delta < 0 else "NEUTRAL",
    }


def absorption_rate(deltas: Sequence[float]) -> float:
    if not deltas:
        return 1.0
    total_abs = sum(abs(x) for x in deltas)
    if total_abs <= 1e-9:
        return 1.0

    net = sum(deltas)
    main_sign = 1 if net >= 0 else -1
    opposite = sum(abs(x) for x in deltas if x * main_sign < 0)

    # 0 = rien n'absorbe, 1 = beaucoup de flux opposé
    return max(0.0, min(1.0, opposite / total_abs * 2.0))


def detect_trend(values: Sequence[float]) -> str:
    if len(values) < 4:
        return "UNKNOWN"
    a = sum(values[: len(values)//2])
    b = sum(values[len(values)//2 :])
    if abs(b) > abs(a) * 1.25:
        return "ACCELERATING"
    if abs(b) < abs(a) * 0.75:
        return "DECELERATING"
    return "STABLE"


def compute_state(symbol: str, rows: List[M1Row], meta: Dict[str, Any], window: int) -> Dict[str, Any]:
    pip_factor = 100.0 if "JPY" in symbol.upper() else 10000.0
    events = [infer_proxy_delta(r, pip_factor) for r in rows]
    recent = events[-window:] if events else []
    deltas = [float(e["proxy_delta"]) for e in recent]

    delta_cumulative = sum(deltas)
    abs_rate = absorption_rate(deltas)
    delta_abs_sum = sum(abs(x) for x in deltas)
    pos = sum(x for x in deltas if x > 0)
    neg = abs(sum(x for x in deltas if x < 0))
    total_side = pos + neg
    imbalance_ratio = pos / total_side if total_side > 1e-9 else 0.5

    accumulation_score = min(abs(delta_cumulative) / max(1.0, window * 80.0), 1.0) * 100.0
    tension_score = (1.0 - abs_rate) * 100.0
    imbalance_score = abs(imbalance_ratio - 0.5) * 200.0

    composite = 0.42 * accumulation_score + 0.40 * tension_score + 0.18 * imbalance_score
    composite = max(0.0, min(100.0, composite))

    side = "BUY_SIDE" if delta_cumulative > 0 else "SELL_SIDE" if delta_cumulative < 0 else "NEUTRAL"
    delta_trend = detect_trend(deltas)

    if composite >= 75:
        state = "LOADED"
    elif composite >= 60:
        state = "LOADING"
    elif composite <= 35:
        state = "RELEASED"
    else:
        state = "NEUTRAL"

    # Cas particulier: gros delta mais absorption en hausse => release/reintegration possible.
    if composite >= 55 and abs_rate >= 0.65:
        state = "RELEASING"

    interpretation = {
        "LOADED": "Tension proxy forte, flux dominant peu absorbé.",
        "LOADING": "Tension proxy en chargement.",
        "RELEASING": "Flux opposé visible, absorption/réintégration possible.",
        "RELEASED": "Tension proxy basse ou relâchée.",
        "NEUTRAL": "Flux proxy équilibré.",
    }.get(state, "UNKNOWN")

    alerts = []
    if state == "LOADED":
        alerts.append({
            "type": "MICROSTRUCTURE_PROXY_TENSION",
            "level": "HOT",
            "maturity": "EARLY",
            "message": f"{symbol} tension proxy {side}. Détachement M1 possible si le flux persiste.",
            "confidence": round(min(0.95, 0.50 + composite / 200.0), 3),
        })
    elif state == "LOADING":
        alerts.append({
            "type": "MICROSTRUCTURE_PROXY_LOADING",
            "level": "WATCH",
            "maturity": "EARLY",
            "message": f"{symbol} chargement proxy {side}. Surveiller absorption ou release.",
            "confidence": round(min(0.85, 0.40 + composite / 220.0), 3),
        })
    elif state == "RELEASING":
        alerts.append({
            "type": "MICROSTRUCTURE_PROXY_REINTEGRATION",
            "level": "WATCH",
            "maturity": "EARLY",
            "message": f"{symbol} absorption/réintégration proxy visible.",
            "confidence": round(min(0.80, 0.35 + composite / 260.0), 3),
        })

    return {
        "timestamp": utc_now(),
        "symbol": symbol,
        "timeframe": 1,
        "method": "B6_ORDER_FLOW_PROXY_LITE_V1",
        "mode": "READ_ONLY_DB_PROXY",
        "data_source": meta,
        "microstructure": {
            "state": state,
            "interpretation": interpretation,
            "tension_score": round(composite, 2),
            "delta_cumulative": round(delta_cumulative, 4),
            "delta_window": window,
            "delta_abs_sum": round(delta_abs_sum, 4),
            "delta_trend": delta_trend,
            "absorption": {
                "rate": round(abs_rate, 4),
                "interpretation": "NOT_ABSORBING" if abs_rate < 0.30 else "PARTIAL_ABSORPTION" if abs_rate < 0.70 else "ABSORBING",
                "direction": side,
                "confidence": round(min(0.95, 0.45 + abs(composite - 50.0) / 100.0), 3),
            },
            "imbalance": {
                "ratio": round(imbalance_ratio, 4),
                "direction": "BUY_DOMINANT" if imbalance_ratio > 0.58 else "SELL_DOMINANT" if imbalance_ratio < 0.42 else "BALANCED",
                "magnitude": "EXTREME" if abs(imbalance_ratio - 0.5) > 0.32 else "HIGH" if abs(imbalance_ratio - 0.5) > 0.18 else "NORMAL",
            },
            "spread_behavior": {
                "available": any(e.get("spread") is not None for e in recent),
                "note": "Spread utilisé comme friction si disponible, sinon ignoré.",
            },
            "alerts": alerts,
            "recent_proxy_events": recent[-12:],
        },
        "fusion_with_powerflow": {
            "b6_microstructure_proxy": True,
            "can_elevate_confidence": state in ("LOADED", "LOADING"),
            "recommended_fusion": "Injecter dans powerflow_live_brief comme contexte précoce, pas comme ordre.",
        },
        "technical_risks": [
            "ORDER_FLOW_PROXY_NOT_TRUE_LEVEL2",
            "MT4_NATIVE_BID_ASK_VOLUME_ABSENT",
            "M1_OHLC_PROXY_CAN_CREATE_FALSE_POSITIVES",
        ],
    }


def write_outputs(symbol: str, state: Dict[str, Any]) -> Tuple[Path, Path]:
    out_dir = Path("output/dashboard_surface") / symbol
    out_dir.mkdir(parents=True, exist_ok=True)

    json_path = out_dir / "microstructure_state.json"
    txt_path = out_dir / "microstructure_state.txt"

    json_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    m = state.get("microstructure", {})
    a = m.get("absorption", {})
    im = m.get("imbalance", {})
    alerts = m.get("alerts", [])

    lines = [
        f"{symbol} | B6 PROXY | {m.get('state')} | tension={m.get('tension_score')}",
        f"delta={m.get('delta_cumulative')} trend={m.get('delta_trend')}",
        f"absorption={a.get('rate')} {a.get('interpretation')} direction={a.get('direction')}",
        f"imbalance={im.get('ratio')} {im.get('direction')} {im.get('magnitude')}",
        f"alerts={len(alerts)}",
    ]
    for al in alerts[:3]:
        lines.append(f"- {al.get('level')} {al.get('type')} | {al.get('message')}")

    txt_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, txt_path


def build(db: Path, symbol: str, lookback_rows: int, window: int) -> Dict[str, Any]:
    rows, meta = load_m1_rows(db, symbol, lookback_rows)
    state = compute_state(symbol, rows, meta, window)
    write_outputs(symbol, state)
    return state


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--lookback-rows", type=int, default=240)
    ap.add_argument("--window", type=int, default=20)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    state = build(Path(args.db), args.symbol.upper(), args.lookback_rows, args.window)
    m = state["microstructure"]

    if args.pretty:
        print(json.dumps(state, ensure_ascii=False, indent=2))

    print(
        "B6_ORDER_FLOW_PROXY_OK | "
        f"symbol={args.symbol.upper()} | state={m.get('state')} | "
        f"tension={m.get('tension_score')} | delta={m.get('delta_cumulative')} | "
        f"alerts={len(m.get('alerts', []))} | "
        f"out=output/dashboard_surface/{args.symbol.upper()}/microstructure_state.json"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
