#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.2.1 — USDJPY Fast Audit

Read-only DB audit.
Goal: classify USDJPY as LIVE / THIN / STALE / MISSING and produce a clear report.
Does not write powerflow.db.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def parse_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    try:
        return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
    except Exception:
        return []


def find_symbol_tables(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
    out = []
    for t in tables:
        cols = table_columns(conn, t)
        lower = {c.lower(): c for c in cols}
        symbol_col = lower.get("symbol")
        if not symbol_col:
            continue
        ts_col = None
        for candidate in ["timestamp", "time", "ts", "datetime", "created_at", "generated_at"]:
            if candidate in lower:
                ts_col = lower[candidate]
                break
        tf_col = None
        for candidate in ["timeframe", "tf"]:
            if candidate in lower:
                tf_col = lower[candidate]
                break
        out.append({"table": t, "columns": cols, "symbol_col": symbol_col, "timestamp_col": ts_col, "timeframe_col": tf_col})
    return out


def count_symbol(conn: sqlite3.Connection, table_info: Dict[str, Any], symbol: str) -> Dict[str, Any]:
    t = table_info["table"]
    sym = table_info["symbol_col"]
    ts = table_info.get("timestamp_col")
    tf = table_info.get("timeframe_col")

    result: Dict[str, Any] = {"table": t, "symbol": symbol, "rows": 0, "by_timeframe": {}, "min_timestamp": None, "max_timestamp": None, "age_seconds": None}

    try:
        result["rows"] = conn.execute(f'SELECT COUNT(*) FROM "{t}" WHERE "{sym}"=?', (symbol,)).fetchone()[0]
    except Exception as e:
        result["error"] = str(e)
        return result

    if ts:
        try:
            row = conn.execute(f'SELECT MIN("{ts}"), MAX("{ts}") FROM "{t}" WHERE "{sym}"=?', (symbol,)).fetchone()
            result["min_timestamp"] = row[0]
            result["max_timestamp"] = row[1]
            max_dt = parse_ts(row[1])
            if max_dt:
                result["age_seconds"] = int((datetime.now(timezone.utc) - max_dt).total_seconds())
        except Exception as e:
            result["timestamp_error"] = str(e)

    if tf:
        try:
            rows = conn.execute(f'SELECT "{tf}", COUNT(*), MIN("{ts if ts else tf}"), MAX("{ts if ts else tf}") FROM "{t}" WHERE "{sym}"=? GROUP BY "{tf}" ORDER BY "{tf}"', (symbol,)).fetchall()
            by_tf = {}
            for r in rows:
                by_tf[str(r[0])] = {"rows": r[1], "min": r[2], "max": r[3]}
            result["by_timeframe"] = by_tf
        except Exception as e:
            result["timeframe_error"] = str(e)

    return result


def classify_force_snapshots(info: Dict[str, Any], stale_seconds: int = 600, min_rows: int = 5) -> str:
    rows = int(info.get("rows") or 0)
    age = info.get("age_seconds")
    if rows <= 0:
        return "MISSING"
    if rows < min_rows:
        return "THIN"
    if age is None:
        return "DEGRADED_NO_TIMESTAMP"
    if age >= stale_seconds:
        return "STALE"
    return "LIVE"


def run_existing_runner(core: Path, symbol: str, db: str) -> Dict[str, Any]:
    runner = core / f"run_audit_{symbol.lower()}_once.py"
    if not runner.exists():
        return {"status": "MISSING_RUNNER", "path": str(runner)}
    cmd = [sys.executable, str(runner), "--db", db, "--pretty"]
    try:
        p = subprocess.run(cmd, cwd=str(core), text=True, capture_output=True, timeout=120)
        return {"status": "RAN", "returncode": p.returncode, "stdout_tail": p.stdout[-4000:], "stderr_tail": p.stderr[-4000:], "cmd": cmd}
    except Exception as e:
        return {"status": "ERROR", "error": str(e), "cmd": cmd}


def make_md(report: Dict[str, Any]) -> str:
    lines = []
    lines.append("# RAPPORT USDJPY CAPTURE AUDIT FAST — PowerFlow V7.2.1")
    lines.append("")
    lines.append(f"Generated UTC : {report['generated_at_utc']}")
    lines.append(f"Symbol : `{report['symbol']}`")
    lines.append(f"DB : `{report['db']}`")
    lines.append(f"Global verdict : `{report['global_verdict']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("```text")
    for k, v in report["summary"].items():
        lines.append(f"{k}: {v}")
    lines.append("```")
    lines.append("")
    lines.append("## force_snapshots")
    lines.append("")
    fs = report.get("force_snapshots")
    if fs:
        lines.append(f"- rows : `{fs.get('rows')}`")
        lines.append(f"- min_timestamp : `{fs.get('min_timestamp')}`")
        lines.append(f"- max_timestamp : `{fs.get('max_timestamp')}`")
        lines.append(f"- age_seconds : `{fs.get('age_seconds')}`")
        lines.append(f"- classification : `{fs.get('classification')}`")
        if fs.get("by_timeframe"):
            lines.append("")
            lines.append("| TF | Rows | Min | Max |")
            lines.append("|---|---:|---|---|")
            for tf, d in fs["by_timeframe"].items():
                lines.append(f"| {tf} | {d.get('rows')} | {d.get('min')} | {d.get('max')} |")
    else:
        lines.append("force_snapshots table not found or no symbol column.")
    lines.append("")
    lines.append("## Symbol tables discovered")
    lines.append("")
    lines.append("| Table | Rows USDJPY | Max timestamp | Age sec |")
    lines.append("|---|---:|---|---:|")
    for item in report["tables"]:
        lines.append(f"| {item.get('table')} | {item.get('rows')} | {item.get('max_timestamp')} | {item.get('age_seconds')} |")
    lines.append("")
    lines.append("## Existing runner output")
    lines.append("")
    runner = report.get("existing_runner", {})
    lines.append(f"status : `{runner.get('status')}`")
    lines.append(f"returncode : `{runner.get('returncode')}`")
    if runner.get("stdout_tail"):
        lines.append("")
        lines.append("```text")
        lines.append(runner["stdout_tail"])
        lines.append("```")
    if runner.get("stderr_tail"):
        lines.append("")
        lines.append("### stderr")
        lines.append("```text")
        lines.append(runner["stderr_tail"])
        lines.append("```")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(report["interpretation"])
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append(report["next_action"])
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("Read-only audit. No DB write. No capture_bridge patch.")
    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="USDJPY")
    ap.add_argument("--core", default=".")
    ap.add_argument("--stale-seconds", type=int, default=600)
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--md-out", default=None)
    args = ap.parse_args()

    core = Path(args.core).resolve()
    db_path = core / args.db
    generated = utc_now()

    report: Dict[str, Any] = {
        "generated_at_utc": generated,
        "symbol": args.symbol,
        "db": str(db_path),
        "tables": [],
        "force_snapshots": None,
        "summary": {},
        "global_verdict": "UNKNOWN",
    }

    if not db_path.exists():
        report["global_verdict"] = "DB_MISSING"
        report["summary"] = {"db_exists": False}
    else:
        conn = sqlite3.connect(str(db_path))
        try:
            tables = find_symbol_tables(conn)
            for ti in tables:
                item = count_symbol(conn, ti, args.symbol)
                report["tables"].append(item)
                if ti["table"] == "force_snapshots":
                    item["classification"] = classify_force_snapshots(item, args.stale_seconds)
                    report["force_snapshots"] = item

            fs = report["force_snapshots"]
            if fs is None:
                report["global_verdict"] = "NO_FORCE_SNAPSHOTS_SYMBOL_TABLE"
                report["summary"] = {"force_snapshots": "not found with symbol column"}
            else:
                report["global_verdict"] = fs["classification"]
                report["summary"] = {
                    "force_snapshots_rows": fs.get("rows"),
                    "force_snapshots_max_timestamp": fs.get("max_timestamp"),
                    "force_snapshots_age_seconds": fs.get("age_seconds"),
                    "classification": fs.get("classification"),
                }
        finally:
            conn.close()

    report["existing_runner"] = run_existing_runner(core, args.symbol, args.db)

    verdict = report["global_verdict"]
    if verdict == "LIVE":
        report["interpretation"] = "USDJPY capture appears live in force_snapshots. If dashboard still shows stale, inspect dashboard surface generation."
        report["next_action"] = "Run scheduler once, hydrate dashboard, then verify USDJPY card freshness."
    elif verdict == "THIN":
        report["interpretation"] = "USDJPY exists but has too few rows. Engine path may work, but capture depth is insufficient."
        report["next_action"] = "Check MT4 EA symbol list and keep capture running; verify rows increase after scheduler cycles."
    elif verdict == "STALE":
        report["interpretation"] = "USDJPY exists but is stale. This is a capture/data freshness problem, not a scheduler or dashboard decision problem."
        report["next_action"] = "Check MT4 EA symbol list, bridge incoming messages for USDJPY, and insertion into force_snapshots."
    elif verdict == "MISSING":
        report["interpretation"] = "No USDJPY rows found. Capture is not feeding USDJPY into force_snapshots."
        report["next_action"] = "Enable USDJPY in MT4 EA / bridge config, then rerun audit."
    else:
        report["interpretation"] = "Audit could not classify USDJPY cleanly. Inspect table discovery and runner output."
        report["next_action"] = "Open the JSON report and inspect available symbol tables."

    json_out = Path(args.json_out) if args.json_out else core / "output" / f"usdjpy_audit_fast_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    md_out = Path(args.md_out) if args.md_out else core / f"RAPPORT_USDJPY_CAPTURE_AUDIT_FAST_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.md"
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_out.write_text(make_md(report), encoding="utf-8")

    print(f"USDJPY_AUDIT_FAST verdict={report['global_verdict']}")
    print(f"JSON: {json_out}")
    print(f"MD: {md_out}")
    return 0 if report["global_verdict"] in {"LIVE", "THIN", "STALE", "MISSING"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
