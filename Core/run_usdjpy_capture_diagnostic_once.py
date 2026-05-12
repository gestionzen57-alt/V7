#!/usr/bin/env python3
"""
PowerFlow V7.2.1 — USDJPY Capture Thin Diagnostic

Read-only DB audit for USDJPY capture/data freshness.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def connect_ro(db_path: str) -> sqlite3.Connection:
    uri = f"file:{Path(db_path).as_posix()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def detect_cols(cols: List[str]) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    lower = {c.lower(): c for c in cols}
    return (
        lower.get("symbol"),
        lower.get("timeframe") or lower.get("tf"),
        lower.get("timestamp") or lower.get("timestamp_utc") or lower.get("time") or lower.get("datetime") or lower.get("created_at") or lower.get("ts"),
    )


def age_seconds(value: Any) -> Optional[int]:
    if value is None:
        return None
    text = str(value).replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).total_seconds()))
    except Exception:
        return None


def audit(db_path: str, symbol: str = "USDJPY") -> Dict[str, Any]:
    symbol = symbol.upper()
    report: Dict[str, Any] = {
        "timestamp_utc": utc_now_iso(),
        "audit": "USDJPY_CAPTURE_THIN_DIAGNOSTIC",
        "symbol": symbol,
        "db_path": db_path,
        "db_mode": "READ_ONLY",
        "technical_risks": [],
    }

    try:
        conn = connect_ro(db_path)
    except Exception as exc:
        report.update({"status": "FAIL", "diagnosis": "DB_OPEN_FAILED", "error": str(exc)})
        return report

    try:
        exists = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='force_snapshots'").fetchone()
        if not exists:
            report.update({"status": "FAIL", "diagnosis": "FORCE_SNAPSHOTS_MISSING"})
            return report

        cols = [r[1] for r in conn.execute("PRAGMA table_info(force_snapshots)").fetchall()]
        symbol_col, tf_col, ts_col = detect_cols(cols)
        report["columns_detected"] = {"symbol": symbol_col, "timeframe": tf_col, "timestamp": ts_col}

        if not symbol_col:
            report["technical_risks"].append("SYMBOL_COLUMN_MISSING")
            report.update({"status": "FAIL", "diagnosis": "SYMBOL_COLUMN_MISSING"})
            return report

        total = conn.execute(
            f"SELECT COUNT(*) FROM force_snapshots WHERE UPPER({symbol_col})=?",
            (symbol,),
        ).fetchone()[0]
        report["rows_total"] = int(total)

        if ts_col:
            earliest = conn.execute(
                f"SELECT MIN({ts_col}) FROM force_snapshots WHERE UPPER({symbol_col})=?",
                (symbol,),
            ).fetchone()[0]
            latest = conn.execute(
                f"SELECT MAX({ts_col}) FROM force_snapshots WHERE UPPER({symbol_col})=?",
                (symbol,),
            ).fetchone()[0]
            report["earliest_timestamp"] = earliest
            report["latest_timestamp"] = latest
            report["latest_age_seconds"] = age_seconds(latest)
        else:
            report["technical_risks"].append("TIMESTAMP_COLUMN_MISSING")

        if tf_col:
            rows_by_tf = [
                {"timeframe": r[0], "rows": int(r[1]), "latest_timestamp": r[2] if ts_col else None}
                for r in conn.execute(
                    f"SELECT {tf_col}, COUNT(*), {('MAX(' + ts_col + ')') if ts_col else 'NULL'} FROM force_snapshots WHERE UPPER({symbol_col})=? GROUP BY {tf_col} ORDER BY {tf_col}",
                    (symbol,),
                ).fetchall()
            ]
            report["rows_by_timeframe"] = rows_by_tf
        else:
            report["technical_risks"].append("TIMEFRAME_COLUMN_MISSING")

        symbol_summary = [
            {"symbol": r[0], "rows": int(r[1]), "latest_timestamp": r[2] if ts_col else None}
            for r in conn.execute(
                f"SELECT {symbol_col}, COUNT(*), {('MAX(' + ts_col + ')') if ts_col else 'NULL'} FROM force_snapshots GROUP BY {symbol_col} ORDER BY COUNT(*) DESC"
            ).fetchall()
        ]
        report["symbol_summary"] = symbol_summary

        latest_age = report.get("latest_age_seconds")
        if total == 0:
            status = "FAIL"
            diagnosis = "USDJPY_NO_ROWS"
            recommendation = "Check MT4 EA symbols list, bridge symbol routing, and force_snapshots insertion for USDJPY."
            report["technical_risks"].extend(["USDJPY_CAPTURE_INACTIVE", "USDJPY_NO_ROWS"])
        elif total < 100:
            status = "DEGRADED"
            diagnosis = "USDJPY_THIN_ROWS"
            recommendation = "USDJPY exists but is too thin. Check capture duration, TF1 feed, and bridge insertion frequency."
            report["technical_risks"].extend(["USDJPY_INSUFFICIENT_ROWS"])
        elif latest_age is not None and latest_age > 3600:
            status = "DEGRADED"
            diagnosis = "USDJPY_STALE_TIMESTAMP"
            recommendation = "USDJPY has rows but is stale. Check live MT4 feed and bridge writer process."
            report["technical_risks"].extend(["USDJPY_STALE_DATA"])
        else:
            status = "PASS"
            diagnosis = "USDJPY_CAPTURE_LIVE_ENOUGH"
            recommendation = "Continue monitoring rows and freshness."

        report.update({"status": status, "diagnosis": diagnosis, "recommendation": recommendation})
        return report
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit USDJPY capture thin/stale state.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="USDJPY")
    parser.add_argument("--output", "--out", dest="output", default="output/usdjpy_capture_thin_diagnostic.json")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    report = audit(args.db, args.symbol)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.pretty:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print(f"USDJPY_DIAGNOSTIC_{report.get('status')} | diagnosis={report.get('diagnosis')} | out={out}")

    return 0 if report.get("status") in {"PASS", "DEGRADED"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
