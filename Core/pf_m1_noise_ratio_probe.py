#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — M1 Noise Ratio Probe

Produces output/force_kinematics_state.json consumed by M1_CONTEXT_SCORE.

Doctrine:
- M1 is never censored.
- Noise ratio qualifies the microfilm.
- DB is read-only.
- No BUY/SELL.
"""

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


CURRENCIES = ("GBP", "EUR", "USD", "JPY", "CAD", "CHF", "AUD", "NZD", "XAU")


@dataclass
class M1NoiseInputs:
    db_path: str = "powerflow.db"
    symbol: str = "GBPUSD"
    bars: int = 180
    timeframe: int = 1
    alpha: float = 0.18


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def connect_ro(db_path: str) -> sqlite3.Connection:
    uri = f"file:{Path(db_path).as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def detect_columns(cols: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str], Dict[str, str]]:
    lower = {c.lower(): c for c in cols}

    symbol_col = lower.get("symbol")
    tf_col = lower.get("timeframe") or lower.get("tf")
    ts_col = (
        lower.get("timestamp")
        or lower.get("timestamp_utc")
        or lower.get("time")
        or lower.get("datetime")
        or lower.get("created_at")
        or lower.get("ts")
    )

    currency_cols: Dict[str, str] = {}
    for cur in CURRENCIES:
        candidates = [
            cur.lower(),
            cur.upper(),
            f"force_{cur.lower()}",
            f"{cur.lower()}_force",
            f"{cur.lower()}_zscore",
            f"z_{cur.lower()}",
        ]
        for cand in candidates:
            real = lower.get(cand.lower())
            if real:
                currency_cols[cur] = real
                break

    return symbol_col, tf_col, ts_col, currency_cols


def robust_std(values: List[float]) -> float:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(clean) < 2:
        return 0.0
    med = median(clean)
    mad = median([abs(v - med) for v in clean])
    return 1.4826 * mad


def ema_smooth(values: List[float], alpha: float) -> List[float]:
    if not values:
        return []
    smoothed = [values[0]]
    for v in values[1:]:
        smoothed.append(alpha * v + (1.0 - alpha) * smoothed[-1])
    return smoothed


def diffs(values: List[float]) -> List[float]:
    return [values[i] - values[i - 1] for i in range(1, len(values))]


def bounded(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


def compute_noise_ratio(values: List[float], alpha: float = 0.18) -> Dict[str, Any]:
    clean = [float(v) for v in values if v is not None and math.isfinite(float(v))]
    if len(clean) < 12:
        return {
            "noise_ratio": None,
            "quality": "INSUFFICIENT_DATA",
            "first_detachment": False,
            "technical_risks": ["NOISE_RATIO_INSUFFICIENT_POINTS"],
            "points": len(clean),
        }

    smooth = ema_smooth(clean, alpha=alpha)
    residual = [v - s for v, s in zip(clean, smooth)]

    raw_delta = diffs(clean)
    residual_delta = diffs(residual)

    raw_vol = robust_std(raw_delta)
    residual_vol = robust_std(residual_delta)

    if raw_vol <= 1e-9:
        ratio = 0.0
    else:
        ratio = bounded(residual_vol / raw_vol, 0.0, 1.0)

    # First detachment = latest residual leaves its recent residual envelope.
    recent = residual[-40:] if len(residual) >= 40 else residual
    res_std = robust_std(recent)
    latest_res = residual[-1]
    first_detachment = bool(res_std > 1e-9 and abs(latest_res) >= 1.35 * res_std)

    if ratio < 0.10:
        quality = "CLEAN"
    elif ratio < 0.20:
        quality = "TACTICAL"
    elif ratio < 0.30:
        quality = "NOISY_BUT_USABLE"
    else:
        quality = "NOISY"

    return {
        "noise_ratio": round(ratio, 6),
        "quality": quality,
        "first_detachment": first_detachment,
        "latest_residual": round(latest_res, 6),
        "residual_std": round(res_std, 6),
        "raw_delta_robust_std": round(raw_vol, 6),
        "residual_delta_robust_std": round(residual_vol, 6),
        "points": len(clean),
        "technical_risks": [],
    }


def fetch_series(db_path: str, symbol: str, timeframe: int, bars: int) -> Tuple[Dict[str, List[float]], Dict[str, Any]]:
    meta: Dict[str, Any] = {
        "db_mode": "READ_ONLY",
        "table": "force_snapshots",
        "symbol": symbol.upper(),
        "timeframe": timeframe,
        "technical_risks": [],
    }

    conn = connect_ro(db_path)
    try:
        table_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='force_snapshots'"
        ).fetchone()
        if not table_exists:
            meta["technical_risks"].append("FORCE_SNAPSHOTS_TABLE_MISSING")
            return {}, meta

        cols = [r[1] for r in conn.execute("PRAGMA table_info(force_snapshots)").fetchall()]
        symbol_col, tf_col, ts_col, currency_map = detect_columns(cols)
        meta["detected_columns"] = {
            "symbol": symbol_col,
            "timeframe": tf_col,
            "timestamp": ts_col,
            "currencies": currency_map,
        }

        if not currency_map:
            meta["technical_risks"].append("NO_CURRENCY_COLUMNS_DETECTED")
            return {}, meta

        select_cols = []
        if ts_col:
            select_cols.append(ts_col)
        select_cols.extend(currency_map.values())

        where = []
        params: List[Any] = []
        if symbol_col:
            where.append(f"UPPER({symbol_col})=?")
            params.append(symbol.upper())
        else:
            meta["technical_risks"].append("SYMBOL_COLUMN_MISSING")

        if tf_col:
            where.append(f"{tf_col}=?")
            params.append(int(timeframe))
        else:
            meta["technical_risks"].append("TIMEFRAME_COLUMN_MISSING")

        sql = f"SELECT {', '.join(select_cols)} FROM force_snapshots"
        if where:
            sql += " WHERE " + " AND ".join(where)
        # Prefer timestamp order; fallback rowid.
        if ts_col:
            sql += f" ORDER BY {ts_col} DESC"
        else:
            sql += " ORDER BY rowid DESC"
        sql += " LIMIT ?"
        params.append(int(bars))

        old_factory = conn.row_factory
        conn.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in conn.execute(sql, tuple(params)).fetchall()]
        finally:
            conn.row_factory = old_factory

        rows = list(reversed(rows))  # chronological order for kinematics

        meta["rows"] = len(rows)
        if rows and ts_col:
            meta["earliest_timestamp"] = str(rows[0].get(ts_col))
            meta["latest_timestamp"] = str(rows[-1].get(ts_col))
        elif rows:
            meta["latest_timestamp"] = None
            meta["technical_risks"].append("TIMESTAMP_COLUMN_MISSING")

        series: Dict[str, List[float]] = {}
        for cur, col in currency_map.items():
            vals = []
            for row in rows:
                value = row.get(col)
                try:
                    vals.append(float(value))
                except Exception:
                    pass
            if vals:
                series[cur] = vals

        return series, meta
    finally:
        conn.close()


def build_force_kinematics_state(inputs: M1NoiseInputs) -> Dict[str, Any]:
    series, meta = fetch_series(inputs.db_path, inputs.symbol, inputs.timeframe, inputs.bars)

    currencies: Dict[str, Any] = {}
    risks: List[str] = list(meta.get("technical_risks", []))

    for cur, values in series.items():
        result = compute_noise_ratio(values, alpha=inputs.alpha)
        currencies[cur] = {
            "noise_ratio": result["noise_ratio"],
            "noise_quality": result["quality"],
            "first_detachment": result["first_detachment"],
            "latest_residual": result.get("latest_residual"),
            "residual_std": result.get("residual_std"),
            "points": result.get("points"),
            "technical_risks": result.get("technical_risks", []),
        }
        risks.extend([f"{cur}:{r}" for r in result.get("technical_risks", [])])

    if not currencies:
        risks.append("NO_CURRENCY_SERIES_AVAILABLE")

    return {
        "timestamp_utc": utc_now_iso(),
        "symbol": inputs.symbol.upper(),
        "method": "M1_NOISE_RATIO_PROBE",
        "db_mode": "READ_ONLY",
        "timeframe": inputs.timeframe,
        "bars": inputs.bars,
        "alpha": inputs.alpha,
        "currencies": currencies,
        "meta": meta,
        "technical_risks": risks,
        "note": "Noise ratio qualifies M1 microfilm; it does not censor M1.",
    }


def write_json(data: Mapping[str, Any], output: str) -> None:
    out = Path(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build output/force_kinematics_state.json for M1_CONTEXT_SCORE.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframe", type=int, default=1)
    parser.add_argument("--bars", type=int, default=180)
    parser.add_argument("--alpha", type=float, default=0.18)
    parser.add_argument("--output", "--out", dest="output", default="output/force_kinematics_state.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    state = build_force_kinematics_state(
        M1NoiseInputs(
            db_path=args.db,
            symbol=args.symbol,
            timeframe=args.timeframe,
            bars=args.bars,
            alpha=args.alpha,
        )
    )
    write_json(state, args.output)

    if args.pretty:
        print(json.dumps(state, indent=2, ensure_ascii=False))
    else:
        labels = ",".join(f"{c}:{v.get('noise_ratio')}" for c, v in state.get("currencies", {}).items())
        print(f"M1_NOISE_RATIO_OK | symbol={args.symbol.upper()} | out={args.output} | {labels}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
