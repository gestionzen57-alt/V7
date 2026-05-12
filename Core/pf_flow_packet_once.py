import argparse
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone, timedelta


PACKET_EVENTS = {
    "CROSS",
    "FAKEOUT",
    "SLINGSHOT",
    "COMPRESSION",
    "COMPRESSION_BREAK",
    "APPROACH",
    "EXTREME_HIGH",
    "EXTREME_LOW",
}


def parse_dt(x):
    if not x:
        return None
    try:
        dt = datetime.fromisoformat(str(x).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def pair_bias(symbol, strong, weak):
    strong = (strong or "").upper()
    weak = (weak or "").upper()
    base = symbol[:3].upper()
    quote = symbol[3:].upper()

    if strong == base and weak == quote:
        return "PAIR_UP"
    if strong == quote and weak == base:
        return "PAIR_DOWN"
    return "MIXED"


def packet_name(types):
    s = set(types)

    if "FAKEOUT" in s and ("CROSS" in s or "COMPRESSION_BREAK" in s):
        return "TRAP_REVERSAL_PACKET"

    if "SLINGSHOT" in s and "COMPRESSION_BREAK" in s:
        return "ELASTIC_RELEASE_PACKET"

    if "COMPRESSION" in s and "APPROACH" in s:
        return "PRE_BREAK_TENSION_PACKET"

    if "CROSS" in s and "COMPRESSION_BREAK" in s:
        return "FLOW_TURN_RELEASE_PACKET"

    if "EXTREME_HIGH" in s or "EXTREME_LOW" in s:
        return "EXTREME_PRESSURE_PACKET"

    if "SLINGSHOT" in s:
        return "SLINGSHOT_PACKET"

    if "COMPRESSION_BREAK" in s:
        return "BREAK_PACKET"

    if "CROSS" in s:
        return "CROSS_PACKET"

    return "FLOW_PACKET"


def packet_score(rows):
    base = 0
    for r in rows:
        typ = r["signal_type"]
        sev = int(r.get("score") or 0)

        if typ == "COMPRESSION_BREAK":
            base += 4
        elif typ == "SLINGSHOT":
            base += 4
        elif typ == "FAKEOUT":
            base += 4
        elif typ == "CROSS":
            base += 2
        elif typ == "COMPRESSION":
            base += 2
        elif typ == "APPROACH":
            base += 1
        elif typ in ("EXTREME_HIGH", "EXTREME_LOW"):
            base += 2

        base += min(sev, 5) * 0.35

    return round(base, 2)


def level_from_score(score):
    if score >= 10:
        return "HOT"
    if score >= 6:
        return "ACTIVE"
    if score >= 3:
        return "WATCH"
    return "INFO"


def create_table(cur):
    cur.execute("""
    CREATE TABLE IF NOT EXISTS flow_packets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        symbol TEXT NOT NULL,
        timeframe INTEGER NOT NULL,
        packet_type TEXT NOT NULL,
        packet_level TEXT NOT NULL,
        pair_bias TEXT NOT NULL,
        strong TEXT,
        weak TEXT,
        score REAL NOT NULL,
        event_count INTEGER NOT NULL,
        first_signal_at TEXT,
        last_signal_at TEXT,
        payload_json TEXT NOT NULL
    )
    """)


def fetch_recent_signals(cur, symbol, lookback_min):
    cols = [c[1] for c in cur.execute("PRAGMA table_info(signals)")]

    needed = [
        "created_at", "symbol", "timeframe", "signal_type",
        "dev_strong", "dev_weak", "score", "level", "note"
    ]
    select_cols = [c for c in needed if c in cols]

    rows = cur.execute(
        f"""
        SELECT rowid, {",".join(select_cols)}
        FROM signals
        WHERE symbol=?
        ORDER BY rowid DESC
        LIMIT 80
        """,
        (symbol,)
    ).fetchall()

    now = datetime.now(timezone.utc)
    out = []

    for row in rows:
        d = {"rowid": row[0]}
        d.update(dict(zip(select_cols, row[1:])))
        dt = parse_dt(d.get("created_at"))

        if dt is None:
            continue

        # signals are UTC/local engine time; keep only fresh engine alerts
        if dt < now - timedelta(minutes=lookback_min):
            continue

        if d.get("signal_type") not in PACKET_EVENTS:
            continue

        out.append(d)

    return list(reversed(out))


def build_packets(symbol, rows, window_seconds):
    packets = []

    for r in rows:
        dt = parse_dt(r.get("created_at"))
        if dt is None:
            continue

        placed = False
        tf = int(r.get("timeframe") or 0)
        strong = (r.get("dev_strong") or "").lower()
        weak = (r.get("dev_weak") or "").lower()
        bias = pair_bias(symbol, strong, weak)

        for p in packets:
            p_last = parse_dt(p["last_signal_at"])
            same_tf = p["timeframe"] == tf
            same_bias = p["pair_bias"] == bias
            close_time = p_last and abs((dt - p_last).total_seconds()) <= window_seconds

            if same_tf and same_bias and close_time:
                p["events"].append(r)
                p["last_signal_at"] = r.get("created_at")
                placed = True
                break

        if not placed:
            packets.append({
                "symbol": symbol,
                "timeframe": tf,
                "pair_bias": bias,
                "strong": strong,
                "weak": weak,
                "first_signal_at": r.get("created_at"),
                "last_signal_at": r.get("created_at"),
                "events": [r],
            })

    final = []

    for p in packets:
        types = [e.get("signal_type") for e in p["events"]]
        score = packet_score(p["events"])
        p["packet_type"] = packet_name(types)
        p["packet_level"] = level_from_score(score)
        p["score"] = score
        p["event_count"] = len(p["events"])
        p["types"] = types
        p["notes"] = [
            str(e.get("note") or "").replace("\n", " | ")[:240]
            for e in p["events"]
        ]
        final.append(p)

    level_rank = {
        "HOT": 4,
        "ACTIVE": 3,
        "WATCH": 2,
        "INFO": 1,
    }

    def rank_packet(x):
        return (
            level_rank.get(x.get("packet_level"), 0),
            float(x.get("score") or 0),
            int(x.get("event_count") or 0),
            str(x.get("last_signal_at") or ""),
        )

    final.sort(key=rank_packet, reverse=True)
    return final


def save_packet(cur, packet):
    payload = json.dumps(packet, ensure_ascii=False)

    cur.execute(
        """
        INSERT INTO flow_packets (
            created_at, symbol, timeframe, packet_type, packet_level,
            pair_bias, strong, weak, score, event_count,
            first_signal_at, last_signal_at, payload_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            packet["symbol"],
            packet["timeframe"],
            packet["packet_type"],
            packet["packet_level"],
            packet["pair_bias"],
            packet["strong"],
            packet["weak"],
            packet["score"],
            packet["event_count"],
            packet["first_signal_at"],
            packet["last_signal_at"],
            payload,
        )
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--out", default=None)
    ap.add_argument("--lookback-min", type=int, default=20)
    ap.add_argument("--window-seconds", type=int, default=180)
    ap.add_argument("--pretty", action="store_true")
    args = ap.parse_args()

    db = Path(args.db)
    symbol = args.symbol.upper()

    out = Path(args.out) if args.out else Path(f"output/dashboard_surface/{symbol}/flow_packet.json")
    out.parent.mkdir(parents=True, exist_ok=True)

    con = sqlite3.connect(db)
    cur = con.cursor()
    create_table(cur)

    rows = fetch_recent_signals(cur, symbol, args.lookback_min)
    packets = build_packets(symbol, rows, args.window_seconds)

    result = {
        "meta": {
            "engine": "pf_flow_packet_once",
            "symbol": symbol,
            "lookback_min": args.lookback_min,
            "window_seconds": args.window_seconds,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "packet_count": len(packets),
        "top_packet": packets[0] if packets else None,
        "packets": packets,
    }

    if packets:
        save_packet(cur, packets[0])

    con.commit()
    con.close()

    out.write_text(
        json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None),
        encoding="utf-8"
    )

    if packets:
        p = packets[0]
        print(
            "FLOW_PACKET_OK | "
            f"symbol={symbol} | "
            f"type={p['packet_type']} | "
            f"level={p['packet_level']} | "
            f"bias={p['pair_bias']} | "
            f"tf={p['timeframe']} | "
            f"score={p['score']} | "
            f"events={p['event_count']} | "
            f"out={out}"
        )
    else:
        print(f"FLOW_PACKET_EMPTY | symbol={symbol} | out={out}")


if __name__ == "__main__":
    main()
