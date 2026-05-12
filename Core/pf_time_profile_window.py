from __future__ import annotations

import argparse
import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


TF_LABEL_TO_MIN = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "M30": 30,
    "H1": 60,
    "H4": 240,
    "D1": 1440,
}

PROFILES = {
    "LTF": ["M1", "M5", "M15"],
    "MTF": ["M15", "M30", "H1"],
    "HTF": ["H1", "H4", "D1"],
}

PROFILE_ROLES = {
    "LTF": {
        "M1": "MICROFILM",
        "M5": "TACTICAL_RELAY",
        "M15": "BATTLE_WINDOW",
    },
    "MTF": {
        "M15": "MTF_ENTRY",
        "M30": "INTRADAY_ROTATION",
        "H1": "INTRADAY_GRAVITY",
    },
    "HTF": {
        "H1": "HTF_REACTION_BRIDGE",
        "H4": "DOMINANT_STRUCTURE",
        "D1": "DAILY_GRAVITY",
    },
}

PROFILE_DEFAULT_LIMIT = {
    "LTF": 1800,
    "MTF": 1400,
    "HTF": 900,
}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_dt(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    s = s.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y.%m.%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                dt = datetime.strptime(s, fmt)
                break
            except ValueError:
                dt = None
        if dt is None:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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


def choose_col(cols: Sequence[str], candidates: Sequence[str]) -> Optional[str]:
    low = {c.lower(): c for c in cols}
    for name in candidates:
        if name.lower() in low:
            return low[name.lower()]
    return None


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def get_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] for r in rows]


def fetch_rows(
    db: Path,
    symbol: str,
    tf_minutes: Sequence[int],
    limit: int,
) -> Tuple[str, List[Dict[str, Any]], List[str]]:
    risks: List[str] = []
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        preferred = ["force_snapshots_v2", "force_snapshots"]
        for table in preferred:
            if not table_exists(conn, table):
                continue

            cols = get_columns(conn, table)
            symbol_col = choose_col(cols, ["symbol", "pair"])
            tf_col = choose_col(cols, ["timeframe", "tf", "period"])
            time_col = choose_col(cols, ["created_at", "timestamp", "time", "datetime", "ts"])

            if not symbol_col or not tf_col or not time_col:
                risks.append(f"{table}_SCHEMA_INCOMPLETE")
                continue

            placeholders = ",".join(["?"] * len(tf_minutes))
            sql = (
                f"SELECT * FROM {table} "
                f"WHERE {symbol_col}=? AND {tf_col} IN ({placeholders}) "
                f"ORDER BY {time_col} DESC "
                f"LIMIT ?"
            )
            params = [symbol] + list(tf_minutes) + [limit]
            rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
            if rows:
                return table, rows, risks

        return "NONE", [], risks + ["NO_PROFILE_ROWS"]
    finally:
        conn.close()


def extract_ohlc_schema(rows: List[Dict[str, Any]]) -> Dict[str, Optional[str]]:
    if not rows:
        return {}
    cols = list(rows[0].keys())
    return {
        "time": choose_col(cols, ["created_at", "timestamp", "time", "datetime", "ts"]),
        "timeframe": choose_col(cols, ["timeframe", "tf", "period"]),
        "open": choose_col(cols, ["open", "o"]),
        "high": choose_col(cols, ["high", "h"]),
        "low": choose_col(cols, ["low", "l"]),
        "close": choose_col(cols, ["close", "c", "price", "bid"]),
        "symbol": choose_col(cols, ["symbol", "pair"]),
    }


def pct_or_zero(a: Optional[float], b: Optional[float]) -> float:
    if a is None or b is None or b == 0:
        return 0.0
    return (a - b) / abs(b)


def compact_direction(x: float, threshold: float = 0.00002) -> str:
    if x > threshold:
        return "PAIR_UP"
    if x < -threshold:
        return "PAIR_DOWN"
    return "NEUTRAL"


def split_recent(values: List[float], n: int = 12) -> Tuple[List[float], List[float]]:
    if len(values) < n * 2:
        mid = max(1, len(values) // 2)
        return values[:mid], values[mid:]
    return values[-n:], values[-2 * n : -n]


def compute_tf_state(
    profile: str,
    tf_label: str,
    rows: List[Dict[str, Any]],
    schema: Dict[str, Optional[str]],
) -> Dict[str, Any]:
    tf_min = TF_LABEL_TO_MIN[tf_label]
    tf_col = schema.get("timeframe")
    time_col = schema.get("time")
    open_col = schema.get("open")
    high_col = schema.get("high")
    low_col = schema.get("low")
    close_col = schema.get("close")

    tf_rows = []
    for r in rows:
        if tf_col is None:
            continue
        try:
            if int(float(r.get(tf_col))) == tf_min:
                tf_rows.append(r)
        except Exception:
            continue

    tf_rows = sorted(tf_rows, key=lambda r: str(r.get(time_col) or ""))

    role = PROFILE_ROLES.get(profile, {}).get(tf_label, "TIMEFRAME")
    if not tf_rows:
        return {
            "timeframe": tf_label,
            "role": role,
            "rows": 0,
            "phase": "NO_DATA",
            "bias": "UNKNOWN",
            "force": None,
            "freshness_seconds": None,
            "important_event": "NO_DATA",
            "technical_risks": [f"{tf_label}_NO_ROWS"],
        }

    closes = [safe_float(r.get(close_col)) for r in tf_rows] if close_col else []
    highs = [safe_float(r.get(high_col)) for r in tf_rows] if high_col else []
    lows = [safe_float(r.get(low_col)) for r in tf_rows] if low_col else []
    opens = [safe_float(r.get(open_col)) for r in tf_rows] if open_col else []

    valid = [
        (c, h, l, o, r)
        for c, h, l, o, r in zip(closes, highs, lows, opens, tf_rows)
        if c is not None and h is not None and l is not None
    ]

    if len(valid) < 4:
        return {
            "timeframe": tf_label,
            "role": role,
            "rows": len(tf_rows),
            "phase": "THIN_DATA",
            "bias": "UNKNOWN",
            "force": None,
            "freshness_seconds": None,
            "important_event": "THIN_DATA",
            "technical_risks": [f"{tf_label}_THIN_ROWS"],
        }

    closes2 = [x[0] for x in valid]
    highs2 = [x[1] for x in valid]
    lows2 = [x[2] for x in valid]
    opens2 = [x[3] for x in valid if x[3] is not None]
    last_row = valid[-1][4]
    first_close = closes2[0]
    last_close = closes2[-1]

    recent, prev = split_recent(closes2, n=min(12, max(3, len(closes2) // 4)))
    recent_range = max(recent) - min(recent) if recent else 0.0
    prev_range = max(prev) - min(prev) if prev else recent_range
    compression_ratio = recent_range / prev_range if prev_range else 1.0

    slope = pct_or_zero(last_close, closes2[max(0, len(closes2) - min(24, len(closes2)))])
    speed = pct_or_zero(closes2[-1], closes2[-2])
    accel = speed - pct_or_zero(closes2[-2], closes2[-3]) if len(closes2) >= 3 else 0.0

    recent_high = max(highs2[-min(30, len(highs2)):])
    recent_low = min(lows2[-min(30, len(lows2)):])
    full_high = max(highs2)
    full_low = min(lows2)
    body = pct_or_zero(closes2[-1], opens2[-1]) if opens2 else speed

    direction = compact_direction(slope, threshold=0.00003)
    force = min(1.0, round(abs(slope) * 10000 + abs(speed) * 20000 + abs(accel) * 20000, 3))

    phase = "QUIET"
    event = "NO_MAJOR_EVENT"

    if compression_ratio < 0.45:
        phase = "COMPRESSION_BUILDING"
        event = f"{tf_label}_COMPRESSION"
    if force > 0.45 and abs(accel) > abs(speed) * 0.3:
        phase = "IGNITION_EARLY" if tf_label in ("M1", "M5") else "STRUCTURE_SHIFT"
        event = f"{tf_label}_IGNITION_OR_SHIFT"
    if force > 0.75:
        phase = "RELEASE_ACTIVE"
        event = f"{tf_label}_ACCELERATION"
    if recent_range > prev_range * 1.8 and abs(slope) < 0.00008:
        phase = "FAKEOUT_RISK"
        event = f"{tf_label}_FAKEOUT_RISK"
    if body * slope < 0 and abs(body) > 0.00004:
        phase = "ABSORPTION_OR_REJECTION"
        event = f"{tf_label}_ABSORPTION_OR_REJECTION"

    tf_now = parse_dt(last_row.get(time_col)) if time_col else None
    freshness_seconds = None
    if tf_now:
        freshness_seconds = round((datetime.now(timezone.utc) - tf_now).total_seconds(), 1)

    risks = []
    if freshness_seconds is None:
        risks.append(f"{tf_label}_FRESHNESS_UNKNOWN")
    elif freshness_seconds > tf_min * 60 * 4:
        risks.append(f"{tf_label}_STALE")

    return {
        "timeframe": tf_label,
        "role": role,
        "rows": len(tf_rows),
        "phase": phase,
        "bias": direction,
        "force": force,
        "freshness_seconds": freshness_seconds,
        "last_timestamp_utc": tf_now.isoformat().replace("+00:00", "Z") if tf_now else None,
        "last_close": last_close,
        "recent_high": recent_high,
        "recent_low": recent_low,
        "session_high": full_high,
        "session_low": full_low,
        "slope": round(slope, 8),
        "speed": round(speed, 8),
        "acceleration": round(accel, 8),
        "compression_ratio": round(compression_ratio, 4),
        "important_event": event,
        "technical_risks": risks,
    }


def infer_profile_state(profile: str, tf_states: Dict[str, Dict[str, Any]]) -> Tuple[str, str, str, str, List[str]]:
    risks: List[str] = []
    phases = [str(s.get("phase")) for s in tf_states.values()]
    biases = [str(s.get("bias")) for s in tf_states.values()]
    forces = [safe_float(s.get("force")) or 0.0 for s in tf_states.values()]

    up = biases.count("PAIR_UP")
    down = biases.count("PAIR_DOWN")

    if up > down:
        dominant = "PAIR_UP"
    elif down > up:
        dominant = "PAIR_DOWN"
    elif up and down:
        dominant = "MIXED"
    else:
        dominant = "NEUTRAL"

    max_force = max(forces) if forces else 0.0

    attention = "QUIET"
    if max_force >= 0.75 or any("RELEASE" in p or "FAKEOUT" in p for p in phases):
        attention = "WAKE_TRADER"
    elif max_force >= 0.35 or any("COMPRESSION" in p or "IGNITION" in p or "BATTLE" in p for p in phases):
        attention = "WATCH"

    if profile == "LTF":
        main = "LTF_QUIET"
        m1 = tf_states.get("M1", {})
        m5 = tf_states.get("M5", {})
        m15 = tf_states.get("M15", {})
        release_count = sum(1 for p in phases if "RELEASE" in p)
        active_biases = [b for b in biases if b in ("PAIR_UP", "PAIR_DOWN")]
        divergent_release = release_count >= 2 and len(set(active_biases)) > 1

        if divergent_release:
            main = "LTF_DIVERGENT_RELEASE"
        elif release_count >= 2:
            main = "LTF_RELEASE_ACTIVE"
        elif release_count == 1:
            main = "LTF_PARTIAL_RELEASE"
        elif "IGNITION" in str(m1.get("phase")) and str(m5.get("bias")) == str(m1.get("bias")):
            main = "M1_IGNITION_WITH_M5_RELAY"
        elif "IGNITION" in str(m1.get("phase")):
            main = "M1_IGNITION_RELAY_WAIT"
        elif "COMPRESSION" in " ".join(phases):
            main = "LTF_COMPRESSION_BUILDING"
        elif "FAKEOUT" in " ".join(phases):
            main = "LTF_FAKEOUT_RISK"
        elif str(m15.get("phase")) in ("STRUCTURE_SHIFT", "ABSORPTION_OR_REJECTION"):
            main = "M15_BATTLE_WINDOW"
    elif profile == "MTF":
        main = "MTF_QUIET"
        release_count = sum(1 for p in phases if "RELEASE" in p)
        if release_count >= 2:
            main = "MTF_RELEASE_ACTIVE"
        elif release_count == 1:
            main = "MTF_PARTIAL_RELEASE"
        if "COMPRESSION" in " ".join(phases):
            main = "MTF_INTRADAY_COMPRESSION"
        if "STRUCTURE_SHIFT" in " ".join(phases):
            main = "MTF_STRUCTURE_SHIFT"
        if "ABSORPTION_OR_REJECTION" in " ".join(phases):
            main = "MTF_REACTION_OR_REJECTION"
    else:
        main = "HTF_QUIET"
        release_count = sum(1 for p in phases if "RELEASE" in p)
        if release_count >= 2:
            main = "HTF_RELEASE_ACTIVE"
        elif release_count == 1:
            main = "HTF_PARTIAL_RELEASE"
        if "COMPRESSION" in " ".join(phases):
            main = "HTF_COMPRESSION_OR_INSIDE_RANGE"
        if "STRUCTURE_SHIFT" in " ".join(phases):
            main = "HTF_STRUCTURE_SHIFT"
        if "ABSORPTION_OR_REJECTION" in " ".join(phases):
            main = "HTF_REACTION_ZONE"

    if "FAKEOUT_RISK" in phases:
        fake_risk = "HIGH"
    elif any((safe_float(s.get("compression_ratio")) or 1.0) > 1.6 for s in tf_states.values()):
        fake_risk = "MEDIUM"
    else:
        fake_risk = "LOW"

    if any("COMPRESSION" in p for p in phases) and fake_risk == "LOW":
        compression_quality = "REAL_COMPRESSION_PARTIAL"
    elif any("COMPRESSION" in p for p in phases) and fake_risk != "LOW":
        compression_quality = "WEAK_COMPRESSION"
    else:
        compression_quality = "NO_COMPRESSION"

    return attention, main, dominant, fake_risk, risks + [f"{profile}_PROFILE_OK"]


def build_profile(db: Path, symbol: str, profile: str, limit: Optional[int] = None) -> Dict[str, Any]:
    profile = profile.upper()
    if profile not in PROFILES:
        raise ValueError(f"unknown profile {profile}")

    tf_labels = PROFILES[profile]
    tf_minutes = [TF_LABEL_TO_MIN[x] for x in tf_labels]
    table, rows, risks = fetch_rows(db, symbol, tf_minutes, limit or PROFILE_DEFAULT_LIMIT[profile])
    schema = extract_ohlc_schema(rows)

    tf_states = {
        tf: compute_tf_state(profile, tf, rows, schema)
        for tf in tf_labels
    }

    attention, main_state, dominant_bias, fake_risk, more_risks = infer_profile_state(profile, tf_states)
    risks.extend([r for r in more_risks if r.endswith("_STALE") or r.endswith("_MISSING")])

    recent_events = []
    for tf, state in tf_states.items():
        event = state.get("important_event")
        if event and event not in ("NO_MAJOR_EVENT", "NO_DATA", "THIN_DATA"):
            recent_events.append({
                "timestamp_utc": state.get("last_timestamp_utc"),
                "symbol": symbol,
                "profile": profile,
                "timeframe": tf,
                "event_type": event,
                "phase": state.get("phase"),
                "bias": state.get("bias"),
                "importance": "HOT" if attention == "WAKE_TRADER" else "WATCH",
                "price": state.get("last_close"),
            })

    phrase = f"{profile} {main_state} | bias={dominant_bias} | fake_risk={fake_risk}"

    return {
        "timestamp_utc": now_utc(),
        "method": "TIME_PROFILE_WINDOW_V737A",
        "symbol": symbol,
        "profile": profile,
        "db_table": table,
        "attention": attention,
        "main_state": main_state,
        "cycle_phase": main_state,
        "dominant_bias": dominant_bias,
        "timeframes": tf_states,
        "recent_important_events": recent_events,
        "memory_summary": {},
        "truth_factors": {},
        "compression_quality": "UNKNOWN" if not rows else infer_profile_state(profile, tf_states)[3],
        "fake_risk": fake_risk,
        "elastic_state": "UNKNOWN",
        "cockpit_phrase": phrase,
        "technical_risks": sorted(set(risks)),
        "note": "Time profile reads DB in read-only mode. It perceives phase/cycle and does not decide trades.",
    }


def write_json(path: Path, data: Dict[str, Any], pretty: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2 if pretty else None, ensure_ascii=False),
        encoding="utf-8",
    )


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.3.7 time profile window")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--profile", choices=sorted(PROFILES), required=True)
    parser.add_argument("--output", default=None)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    db = Path(args.db)
    profile = build_profile(db=db, symbol=args.symbol, profile=args.profile, limit=args.limit)

    out = Path(args.output or f"output/dashboard_surface/{args.symbol}/{args.profile.lower()}_profile.json")
    write_json(out, profile, pretty=args.pretty)

    print(
        f"TIME_PROFILE_WINDOW_OK | symbol={args.symbol} | profile={args.profile} | "
        f"attention={profile['attention']} | state={profile['main_state']} | "
        f"bias={profile['dominant_bias']} | out={out}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
