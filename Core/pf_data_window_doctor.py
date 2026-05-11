from __future__ import annotations

import argparse
import json
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VERSION = "DataWindowDoctorV0.2-live-aware"


@dataclass
class TfWindow:
    timeframe: int
    expected_interval_minutes: int
    rows_strict_window: int
    rows_live_window: int
    expected_rows_strict: int
    expected_rows_live: int
    first_timestamp_strict: str | None
    last_timestamp: str | None
    age_minutes_vs_db_anchor: float | None
    strict_coverage_ratio: float
    live_coverage_ratio: float
    gaps_count_live: int
    max_gap_minutes_live: float | None
    stale: bool
    insufficient_live_rows: bool
    insufficient_strict_rows: bool
    pass_live: bool
    pass_strict: bool
    technical_risks: list[str]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_ts(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        s = str(value).strip().replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def iso_z(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_p0_status(path: Path) -> str:
    if not path.exists():
        return "UNKNOWN"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("global_status", "final_status", "p0_status", "status", "verdict"):
            val = data.get(key)
            if val:
                return str(val)
        summary = data.get("summary") or {}
        for key in ("global_status", "final_status", "p0_status", "status", "verdict"):
            val = summary.get(key)
            if val:
                return str(val)
    except Exception:
        return "UNKNOWN"
    return "UNKNOWN"


def detect_time_column(conn: sqlite3.Connection, table: str) -> str:
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
    if "created_at" in cols:
        return "created_at"
    if "timestamp" in cols:
        return "timestamp"
    if "capture_time" in cols:
        return "capture_time"
    raise RuntimeError(f"NO_TIME_COLUMN:{table}")


def count_gaps(points: list[datetime], expected_minutes: int) -> tuple[int, float | None]:
    if len(points) < 2:
        return 0, None

    gaps = 0
    max_gap = 0.0
    tolerance = max(expected_minutes * 1.8, expected_minutes + 1)

    ordered = sorted(points)
    for a, b in zip(ordered, ordered[1:]):
        delta = (b - a).total_seconds() / 60.0
        max_gap = max(max_gap, delta)
        if delta > tolerance:
            gaps += 1

    return gaps, round(max_gap, 3)


def analyze_tf(
    all_points: list[datetime],
    anchor: datetime,
    tf: int,
    strict_minutes: int,
    live_minutes: int,
    min_live_ratio: float,
    min_strict_ratio: float,
) -> TfWindow:
    expected = tf
    strict_cutoff = anchor.timestamp() - strict_minutes * 60
    live_cutoff = anchor.timestamp() - live_minutes * 60

    strict_points = [p for p in all_points if p.timestamp() >= strict_cutoff and p <= anchor]
    live_points = [p for p in all_points if p.timestamp() >= live_cutoff and p <= anchor]

    last = max(all_points) if all_points else None
    first_strict = min(strict_points) if strict_points else None

    age = None
    if last:
        age = round((anchor - last).total_seconds() / 60.0, 3)

    expected_rows_strict = max(1, strict_minutes // tf)
    expected_rows_live = max(1, live_minutes // tf)

    strict_ratio = round(len(strict_points) / expected_rows_strict, 3) if expected_rows_strict else 0.0
    live_ratio = round(len(live_points) / expected_rows_live, 3) if expected_rows_live else 0.0

    gaps_live, max_gap_live = count_gaps(live_points, expected)

    stale_limit = max(tf * 2.2, tf + 2)
    stale = age is None or age > stale_limit

    insufficient_live = live_ratio < min_live_ratio
    insufficient_strict = strict_ratio < min_strict_ratio

    risks: list[str] = []
    if stale:
        risks.append("STALE_TF")
    if insufficient_live:
        risks.append("INSUFFICIENT_LIVE_ROWS")
    if insufficient_strict:
        risks.append("INSUFFICIENT_STRICT_ROWS")
    if gaps_live > 0:
        risks.append("LIVE_GAPS_DETECTED")

    pass_live = not stale and not insufficient_live and gaps_live == 0
    pass_strict = pass_live and not insufficient_strict

    return TfWindow(
        timeframe=tf,
        expected_interval_minutes=expected,
        rows_strict_window=len(strict_points),
        rows_live_window=len(live_points),
        expected_rows_strict=expected_rows_strict,
        expected_rows_live=expected_rows_live,
        first_timestamp_strict=iso_z(first_strict),
        last_timestamp=iso_z(last),
        age_minutes_vs_db_anchor=age,
        strict_coverage_ratio=strict_ratio,
        live_coverage_ratio=live_ratio,
        gaps_count_live=gaps_live,
        max_gap_minutes_live=max_gap_live,
        stale=stale,
        insufficient_live_rows=insufficient_live,
        insufficient_strict_rows=insufficient_strict,
        pass_live=pass_live,
        pass_strict=pass_strict,
        technical_risks=risks,
    )


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        f"# Data Window Doctor — {result['symbol']}",
        "",
        f"- generated_at_utc: `{result['generated_at_utc']}`",
        f"- version: `{result['version']}`",
        f"- p0_status: `{result['p0_status']}`",
        f"- verdict: `{result['verdict']}`",
        f"- db_anchor_timestamp: `{result['db_anchor_timestamp']}`",
        "",
        "## Summary",
        "",
        f"- live_ltf_pass: `{result['summary']['live_ltf_pass']}`",
        f"- strict_pass: `{result['summary']['strict_pass']}`",
        f"- blocking_live_tfs: `{', '.join(result['summary']['blocking_live_tfs']) or 'none'}`",
        f"- pending_strict_tfs: `{', '.join(result['summary']['pending_strict_tfs']) or 'none'}`",
        "",
        "## Timeframes",
        "",
        "| TF | live rows | strict rows | age min | live pass | strict pass | risks |",
        "|---:|---:|---:|---:|:---:|:---:|---|",
    ]

    for tf in result["timeframes"]:
        lines.append(
            f"| {tf['timeframe']} | {tf['rows_live_window']}/{tf['expected_rows_live']} "
            f"| {tf['rows_strict_window']}/{tf['expected_rows_strict']} "
            f"| {tf['age_minutes_vs_db_anchor']} "
            f"| {tf['pass_live']} | {tf['pass_strict']} "
            f"| {', '.join(tf['technical_risks']) or '-'} |"
        )

    lines += [
        "",
        "## Next action",
        "",
        result["next_action"],
        "",
    ]

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--table", default="force_snapshots")
    parser.add_argument("--strict-minutes", "--lookback-minutes", dest="strict_minutes", type=int, default=180)
    parser.add_argument("--live-minutes", type=int, default=30)
    parser.add_argument("--tfs", default="1,5,15,30,60,240")
    parser.add_argument("--min-live-ratio", type=float, default=0.35)
    parser.add_argument("--min-strict-ratio", type=float, default=0.85)
    parser.add_argument("--p0-json", default="output/P0_FINAL_DECISION.json")
    parser.add_argument("--output-json", default=None)
    parser.add_argument("--output-md", default=None)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    out_json = Path(args.output_json or f"output/data_window_doctor_{args.symbol}.json")
    out_md = Path(args.output_md or f"output/data_window_doctor_{args.symbol}.md")
    out_json.parent.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "generated_at_utc": utc_now(),
        "version": VERSION,
        "symbol": args.symbol,
        "db": args.db,
        "table": args.table,
        "strict_minutes": args.strict_minutes,
        "live_minutes": args.live_minutes,
        "db_anchor_timestamp": None,
        "p0_status": load_p0_status(Path(args.p0_json)),
        "verdict": "DATA_WINDOW_FAIL",
        "summary": {
            "live_ltf_pass": False,
            "strict_pass": False,
            "blocking_live_tfs": [],
            "pending_strict_tfs": [],
        },
        "technical_risks": [],
        "timeframes": [],
        "next_action": "",
    }

    db_path = Path(args.db)
    if not db_path.exists():
        result["technical_risks"] = ["DB_MISSING"]
        result["next_action"] = "DB absente."
        out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        write_markdown(out_md, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2

    try:
        conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
        time_col = detect_time_column(conn, args.table)

        rows = conn.execute(
            f"""
            SELECT timeframe, {time_col}
            FROM {args.table}
            WHERE symbol = ?
            ORDER BY timeframe, {time_col}
            """,
            (args.symbol,),
        ).fetchall()

        by_tf: dict[int, list[datetime]] = {}
        all_points: list[datetime] = []

        for tf_raw, ts_raw in rows:
            dt = parse_ts(ts_raw)
            if dt is None:
                continue
            tf = int(tf_raw)
            by_tf.setdefault(tf, []).append(dt)
            all_points.append(dt)

        conn.close()

        if not all_points:
            result["technical_risks"] = ["NO_ROWS_FOR_SYMBOL"]
            result["next_action"] = "Aucune ligne pour symbole."
            out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            write_markdown(out_md, result)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2

        anchor = max(all_points)
        result["db_anchor_timestamp"] = iso_z(anchor)

        tfs = [int(x.strip()) for x in args.tfs.split(",") if x.strip()]
        windows: list[TfWindow] = []

        for tf in tfs:
            window = analyze_tf(
                all_points=by_tf.get(tf, []),
                anchor=anchor,
                tf=tf,
                strict_minutes=args.strict_minutes,
                live_minutes=args.live_minutes,
                min_live_ratio=args.min_live_ratio,
                min_strict_ratio=args.min_strict_ratio,
            )
            windows.append(window)

        result["timeframes"] = [asdict(w) for w in windows]

        ltf_tfs = {1, 5, 15}
        blocking_live = [
            f"TF{w.timeframe}"
            for w in windows
            if w.timeframe in ltf_tfs and not w.pass_live
        ]
        pending_strict = [
            f"TF{w.timeframe}"
            for w in windows
            if w.timeframe in ltf_tfs and w.pass_live and not w.pass_strict
        ]

        live_ltf_pass = len(blocking_live) == 0
        strict_pass = live_ltf_pass and len(pending_strict) == 0

        result["summary"] = {
            "live_ltf_pass": live_ltf_pass,
            "strict_pass": strict_pass,
            "blocking_live_tfs": blocking_live,
            "pending_strict_tfs": pending_strict,
        }

        all_risks = sorted({risk for w in windows for risk in w.technical_risks})
        result["technical_risks"] = all_risks

        if not live_ltf_pass:
            result["verdict"] = "DATA_WINDOW_FAIL"
            result["next_action"] = "Corriger capture live LTF avant PASS_STRICT."
            rc = 2
        elif not strict_pass:
            result["verdict"] = "DATA_WINDOW_PENDING"
            result["next_action"] = "Flux LTF vivant. Laisser accumuler la fenêtre stricte sans bloquer P0 live."
            rc = 1
        else:
            result["verdict"] = "DATA_WINDOW_PASS"
            result["next_action"] = "Fenêtre data strictement validée."
            rc = 0

    except Exception as exc:
        result["verdict"] = "DATA_WINDOW_FAIL"
        result["technical_risks"] = [f"DOCTOR_EXCEPTION:{type(exc).__name__}:{exc}"]
        result["next_action"] = "Corriger doctor runtime."
        rc = 2

    out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    write_markdown(out_md, result)

    print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())

