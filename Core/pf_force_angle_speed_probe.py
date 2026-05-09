# -*- coding: utf-8 -*-
# PowerFlow V6 - Force Angle Speed Probe (read-only)
# No DB writes. No capture_bridge changes.

from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


FORCE_COLS = [
    "force_gbp", "force_usd", "force_eur", "force_jpy",
    "force_cad", "force_chf", "force_aud", "force_nzd"
]


@dataclass
class ForceMetric:
    currency: str
    latest_force: Optional[float]
    delta_force: Optional[float]
    speed_per_min: Optional[float]
    angle_deg: Optional[float]
    direction: str


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow force / speed / angle probe")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--timeframes", default="1,5")
    parser.add_argument("--bars", type=int, default=5)
    parser.add_argument("--out", default="")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    state = build_state(
        db_path=Path(args.db),
        symbol=args.symbol.upper(),
        timeframes=[int(x.strip()) for x in args.timeframes.split(",") if x.strip()],
        bars=args.bars,
    )

    text = json.dumps(state, indent=2 if args.pretty else None, ensure_ascii=False)
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text + "\n", encoding="utf-8")
        print(f"FORCE_ANGLE_SPEED_OK out={out}")
    else:
        print(text)

    return 0


def build_state(db_path: Path, symbol: str, timeframes: Sequence[int], bars: int) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    state: Dict[str, Any] = {
        "meta": {
            "generated_at": _iso(now),
            "source": "pf_force_angle_speed_probe",
            "version": "0.1-readonly",
            "symbol": symbol,
            "bars": bars,
            "angle_definition": "angle_deg = atan(delta_force / elapsed_minutes)",
            "speed_definition": "speed_per_min = delta_force / elapsed_minutes",
        },
        "timeframes": {},
    }

    uri = f"file:{db_path.as_posix()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as conn:
        conn.row_factory = sqlite3.Row
        table = _pick_table(conn)
        cols = _columns(conn, table)

        for tf in timeframes:
            rows = _load_rows(conn, table, cols, symbol, tf, limit=max(30, bars + 5))
            state["timeframes"][_tf_label(tf)] = analyze_tf(rows, tf, bars, cols, now)

    return state


def analyze_tf(rows: List[sqlite3.Row], tf: int, bars: int, cols: Sequence[str], now: datetime) -> Dict[str, Any]:
    out: Dict[str, Any] = {
        "tf_minutes": tf,
        "rows_loaded": len(rows),
        "latest_timestamp": None,
        "data_age_minutes": None,
        "status": "NO_ROWS",
        "metrics": [],
        "pair": {},
        "notes": [],
    }

    if not rows:
        return out

    latest = rows[-1]
    latest_ts = _parse_datetime(latest["created_at"])
    out["latest_timestamp"] = _iso(latest_ts) if latest_ts else latest["created_at"]
    if latest_ts:
        out["data_age_minutes"] = round(max(0.0, (now - latest_ts).total_seconds() / 60.0), 1)
        out["status"] = "LIVE_OK" if out["data_age_minutes"] <= max(10, tf * 2) else "STALE"
    else:
        out["status"] = "UNKNOWN_TIME"

    if len(rows) < 2:
        out["notes"].append("not_enough_rows_for_delta")
        return out

    past_idx = max(0, len(rows) - 1 - bars)
    past = rows[past_idx]
    elapsed = _elapsed_minutes(past["created_at"], latest["created_at"])
    if not elapsed or elapsed <= 0:
        elapsed = tf * max(1, len(rows) - 1 - past_idx)

    force_cols = [c for c in FORCE_COLS if c in cols]

    metrics: List[ForceMetric] = []
    for col in force_cols:
        cur = _num(latest[col])
        old = _num(past[col])
        if cur is None or old is None:
            metrics.append(ForceMetric(col.replace("force_", "").upper(), cur, None, None, None, "UNKNOWN"))
            continue
        delta = cur - old
        speed = delta / elapsed
        angle = math.degrees(math.atan(speed))
        metrics.append(ForceMetric(
            currency=col.replace("force_", "").upper(),
            latest_force=round(cur, 4),
            delta_force=round(delta, 4),
            speed_per_min=round(speed, 4),
            angle_deg=round(angle, 2),
            direction=_direction(delta),
        ))

    out["metrics"] = [asdict(m) for m in metrics]

    gbp = next((m for m in metrics if m.currency == "GBP"), None)
    usd = next((m for m in metrics if m.currency == "USD"), None)
    eur = next((m for m in metrics if m.currency == "EUR"), None)

    if gbp and usd and gbp.latest_force is not None and usd.latest_force is not None:
        gap = gbp.latest_force - usd.latest_force
        delta_gap = None
        if gbp.delta_force is not None and usd.delta_force is not None:
            delta_gap = gbp.delta_force - usd.delta_force
        out["pair"]["gbp_minus_usd_force_gap"] = round(gap, 4)
        out["pair"]["gbp_usd_gap_delta"] = round(delta_gap, 4) if delta_gap is not None else None
        out["pair"]["pair_bias"] = _pair_bias(gap, delta_gap)

    if eur and usd and eur.latest_force is not None and usd.latest_force is not None:
        out["pair"]["eur_usd_sync_hint"] = _sync_hint(eur, usd)

    return out


def _pick_table(conn: sqlite3.Connection) -> str:
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "force_snapshots_v2" in tables:
        return "force_snapshots_v2"
    return "force_snapshots"


def _columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]


def _load_rows(conn: sqlite3.Connection, table: str, cols: Sequence[str], symbol: str, tf: int, limit: int) -> List[sqlite3.Row]:
    col_list = ", ".join([f'"{c}"' for c in cols])
    sql = (
        f'SELECT {col_list} '
        f'FROM "{table}" '
        'WHERE UPPER(symbol)=? AND timeframe=? '
        'ORDER BY created_at DESC '
        'LIMIT ?'
    )
    return list(reversed(conn.execute(sql, (symbol, tf, limit)).fetchall()))


def _num(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_datetime(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _elapsed_minutes(a: Any, b: Any) -> Optional[float]:
    da = _parse_datetime(a)
    db = _parse_datetime(b)
    if not da or not db:
        return None
    return max(0.0, (db - da).total_seconds() / 60.0)


def _direction(delta: float) -> str:
    if delta > 1.0:
        return "UP"
    if delta < -1.0:
        return "DOWN"
    return "FLAT"


def _pair_bias(gap: float, delta_gap: Optional[float]) -> str:
    if delta_gap is not None:
        if delta_gap > 2:
            return "GBP_PULLING_AWAY_FROM_USD"
        if delta_gap < -2:
            return "USD_PULLING_AWAY_FROM_GBP"
    if gap > 5:
        return "GBP_ABOVE_USD"
    if gap < -5:
        return "USD_ABOVE_GBP"
    return "GBP_USD_BALANCED"


def _sync_hint(a: ForceMetric, b: ForceMetric) -> str:
    if a.delta_force is None or b.delta_force is None:
        return "UNKNOWN"
    if a.delta_force > 0 and b.delta_force > 0:
        return "EUR_USD_SYNC_UP"
    if a.delta_force < 0 and b.delta_force < 0:
        return "EUR_USD_SYNC_DOWN"
    return "EUR_USD_DESYNC_OR_OPPOSITION"


def _tf_label(tf: int) -> str:
    return {1: "M1", 5: "M5", 15: "M15", 30: "M30", 60: "H1", 240: "H4", 1440: "D1", 10080: "W1"}.get(tf, f"M{tf}")


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
