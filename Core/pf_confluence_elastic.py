from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

OUT = Path("output/dashboard_surface")


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def write_txt(path: Path, data: dict[str, Any]) -> None:
    e = data.get("eie", {})
    lines = [
        f"{data.get('symbol')} | EIE V7.4 | {e.get('level')} | {e.get('event_type')}",
        f"state={e.get('state')} bias={e.get('bias')} tf={e.get('tf')} score={e.get('score')}",
        f"z={e.get('zone_z')} fractal={e.get('fractal_align')}/{e.get('fractal_total')}",
        "risks=" + (",".join(data.get("technical_risks", [])) or "NONE"),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def f(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return default
        return float(v)
    except Exception:
        return default


def pip_factor(symbol: str) -> float:
    return 100.0 if "JPY" in symbol.upper() else 10000.0


def table_cols(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        return {str(r[1]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    except Exception:
        return set()


def select_ohlc_table(conn: sqlite3.Connection) -> str | None:
    needed = {"symbol", "timeframe", "created_at", "open", "high", "low", "close"}
    for table in ("force_snapshots_v2", "force_snapshots"):
        if needed.issubset(table_cols(conn, table)):
            return table
    return None


def load_rows(db: Path, symbol: str, tf: int, limit: int = 240) -> tuple[list[dict[str, Any]], str | None, list[str]]:
    risks: list[str] = []

    if not db.exists():
        return [], None, ["DB_MISSING"]

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row

    try:
        table = select_ohlc_table(conn)
        if not table:
            return [], None, ["NO_OHLC_TABLE"]

        rows = conn.execute(
            f"""
            SELECT created_at, open, high, low, close
            FROM {table}
            WHERE symbol = ? AND timeframe = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (symbol, tf, limit),
        ).fetchall()

        out: list[dict[str, Any]] = []
        for r in reversed(rows):
            out.append(
                {
                    "timestamp": str(r["created_at"]),
                    "open": f(r["open"]),
                    "high": f(r["high"]),
                    "low": f(r["low"]),
                    "close": f(r["close"]),
                }
            )

        if not out:
            risks.append(f"NO_ROWS_TF_{tf}")

        return out, table, risks

    finally:
        conn.close()


def classify_tf(symbol: str, tf: int, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if len(rows) < 20:
        return {
            "tf": tf,
            "status": "THIN",
            "rows": len(rows),
            "state": "EIE_DATA_THIN",
            "level": "INFO",
            "bias": "NEUTRAL",
            "score": 0.0,
            "z_score": None,
            "recent_delta_pips": 0.0,
            "technical_risks": ["EIE_THIN_SAMPLE"],
        }

    pf = pip_factor(symbol)
    closes = [f(r.get("close")) for r in rows]
    closes = [x for x in closes if x > 0]

    if len(closes) < 20:
        return {
            "tf": tf,
            "status": "THIN",
            "rows": len(rows),
            "state": "EIE_BAD_CLOSE_SAMPLE",
            "level": "INFO",
            "bias": "NEUTRAL",
            "score": 0.0,
            "z_score": None,
            "recent_delta_pips": 0.0,
            "technical_risks": ["EIE_BAD_CLOSE_SAMPLE"],
        }

    last = closes[-1]
    window = closes[-80:] if len(closes) >= 80 else closes
    mu = mean(window)
    sd = pstdev(window) if len(window) > 2 else 0.0
    z = (last - mu) / sd if sd > 0 else 0.0

    deltas = [(closes[i] - closes[i - 1]) * pf for i in range(1, len(closes))]
    recent_delta = sum(deltas[-10:]) if deltas else 0.0
    impulse = abs(recent_delta)

    if z >= 0.75 or recent_delta > 0:
        bias = "PAIR_UP"
    elif z <= -0.75 or recent_delta < 0:
        bias = "PAIR_DOWN"
    else:
        bias = "NEUTRAL"

    az = abs(z)

    if az >= 2.5:
        state = "EIE_OVERSTRETCHED"
    elif az >= 2.0:
        state = "EIE_LOADED"
    elif az >= 1.25:
        state = "EIE_LOADING"
    elif impulse >= 12:
        state = "EIE_RELEASE_PENDING"
    else:
        state = "EIE_IDLE"

    score = min(10.0, round((az * 2.2) + min(impulse / 10.0, 2.5), 2))

    if score >= 7.5:
        level = "HOT"
    elif score >= 6.0:
        level = "ACTIVE"
    elif score >= 4.0:
        level = "WATCH"
    else:
        level = "INFO"

    return {
        "tf": tf,
        "status": "READABLE",
        "rows": len(rows),
        "last_timestamp": rows[-1].get("timestamp"),
        "last_close": last,
        "mean": round(mu, 6),
        "std": round(sd, 8),
        "z_score": round(z, 3),
        "recent_delta_pips": round(recent_delta, 2),
        "state": state,
        "level": level,
        "bias": bias,
        "score": score,
        "technical_risks": [],
    }


def dominant(tf_reads: list[dict[str, Any]], zone_tf: int) -> dict[str, Any]:
    readable = [r for r in tf_reads if r.get("status") == "READABLE"]

    if not readable:
        return {
            "state": "EIE_DATA_THIN",
            "level": "INFO",
            "bias": "NEUTRAL",
            "score": 0.0,
            "tf": zone_tf,
            "event_family": "ELASTIC_CONFLUENCE",
            "event_type": "EIE_DATA_THIN",
            "zone_z": None,
            "fractal_align": 0,
            "fractal_total": 0,
        }

    selected = next((r for r in readable if int(r.get("tf", 0)) == zone_tf), None)
    if not selected:
        selected = max(readable, key=lambda x: f(x.get("score")))

    biases = [r.get("bias") for r in readable if r.get("bias") in ("PAIR_UP", "PAIR_DOWN")]
    up = biases.count("PAIR_UP")
    down = biases.count("PAIR_DOWN")

    if up > down:
        bias = "PAIR_UP"
        align = up
    elif down > up:
        bias = "PAIR_DOWN"
        align = down
    else:
        bias = selected.get("bias") or "NEUTRAL"
        align = 0

    score = f(selected.get("score"))
    if align >= 2 and bias == selected.get("bias"):
        score += 0.7
    if align >= 3:
        score += 0.5
    score = min(10.0, round(score, 2))

    if score >= 7.5:
        level = "HOT"
    elif score >= 6.0:
        level = "ACTIVE"
    elif score >= 4.0:
        level = "WATCH"
    else:
        level = "INFO"

    state = selected.get("state")

    if state in ("EIE_LOADED", "EIE_OVERSTRETCHED") and align >= 2:
        event_type = "EIE_ELASTIC_CONFLUENCE"
    elif state == "EIE_RELEASE_PENDING":
        event_type = "EIE_RELEASE_PENDING"
    elif state == "EIE_LOADING":
        event_type = "EIE_LOADING"
    else:
        event_type = "EIE_MONITOR"

    return {
        "state": state,
        "level": level,
        "bias": bias,
        "score": score,
        "tf": selected.get("tf"),
        "event_family": "ELASTIC_CONFLUENCE",
        "event_type": event_type,
        "zone_z": selected.get("z_score"),
        "zone_timestamp": selected.get("last_timestamp"),
        "zone_close": selected.get("last_close"),
        "fractal_align": align,
        "fractal_total": len(readable),
    }


def analyze(db: Path, symbol: str, zone_tf: int) -> dict[str, Any]:
    all_risks: list[str] = []
    tf_reads: list[dict[str, Any]] = []
    table_used: str | None = None

    for tf in (1, 5, 15):
        rows, table, risks = load_rows(db, symbol, tf)
        table_used = table_used or table
        all_risks.extend(risks)
        read = classify_tf(symbol, tf, rows)
        tf_reads.append(read)
        all_risks.extend(read.get("technical_risks", []))

    dom = dominant(tf_reads, zone_tf)

    return {
        "timestamp_utc": now_utc(),
        "method": "EIE_ELASTIC_CONFLUENCE_V74",
        "symbol": symbol,
        "db_mode": "READ_ONLY",
        "source_table": table_used,
        "zone_tf": zone_tf,
        "eie": {
            **dom,
            "tf_reads": tf_reads,
        },
        "technical_risks": sorted(set(all_risks)),
        "note": "EIE detects elastic/fractal pressure. It does not produce trade decisions.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--zone-tf", type=int, default=15)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    symbol = args.symbol.upper()
    data = analyze(Path(args.db), symbol, args.zone_tf)

    out_dir = OUT / symbol
    write_json(out_dir / "eie_confluence.json", data)
    write_txt(out_dir / "eie_confluence.txt", data)

    if args.pretty:
        print(json.dumps(data, indent=2, ensure_ascii=False))

    e = data.get("eie", {})
    print(
        "EIE_CONFLUENCE_OK | "
        f"{symbol} level={e.get('level')} state={e.get('state')} "
        f"bias={e.get('bias')} score={e.get('score')} out={out_dir / 'eie_confluence.json'}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
