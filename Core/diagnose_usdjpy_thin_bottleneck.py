#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.2.1 — USDJPY THIN diagnostic V1

Mission:
  Diagnose exact bottleneck for USDJPY capture THIN among:
    - MT4 stream inactive / incomplete
    - Bridge parsing miscalibrated
    - DB insert latency / throttle
    - Cross-symbol contention
    - TF aggregation gap

Read-only:
  - Opens powerflow.db with uri mode=ro when possible
  - Reads logs and JSON outputs only
  - Does not write DB
  - Produces JSON + Markdown reports
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]
DEFAULT_TFS = [1, 5, 15, 30, 60, 240, 1440, 10080]
STALE_BY_TF_SECONDS = {
    1: 180,
    5: 600,
    15: 1800,
    30: 3600,
    60: 7200,
    240: 21600,
    1440: 172800,
    10080: 1209600,
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def parse_ts(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(s)
    except Exception:
        # Try common sqlite string without timezone
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f"):
            try:
                dt = datetime.strptime(s[:26], fmt).replace(tzinfo=timezone.utc)
                break
            except Exception:
                dt = None
        if dt is None:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return default


def open_ro_db(path: Path) -> sqlite3.Connection:
    # Try read-only first. Fall back only if Windows uri path issues.
    uri = f"file:{path.as_posix()}?mode=ro"
    try:
        return sqlite3.connect(uri, uri=True)
    except Exception:
        return sqlite3.connect(str(path))


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    return conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone()[0] > 0


def columns(conn: sqlite3.Connection, table: str) -> List[str]:
    try:
        return [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
    except Exception:
        return []


def find_col(cols: List[str], candidates: Iterable[str]) -> Optional[str]:
    lower = {c.lower(): c for c in cols}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def db_table_scan(conn: sqlite3.Connection, symbols: List[str]) -> List[Dict[str, Any]]:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    out = []
    for (table,) in rows:
        cols = columns(conn, table)
        symbol_col = find_col(cols, ["symbol", "pair", "instrument"])
        if not symbol_col:
            continue
        ts_col = find_col(cols, ["timestamp", "time", "ts", "datetime", "created_at", "generated_at", "bar_time"])
        tf_col = find_col(cols, ["timeframe", "tf", "period"])
        item = {
            "table": table,
            "symbol_col": symbol_col,
            "timestamp_col": ts_col,
            "timeframe_col": tf_col,
            "symbols": {},
        }
        for symbol in symbols:
            sym_info: Dict[str, Any] = {"rows": 0, "min_timestamp": None, "max_timestamp": None, "age_seconds": None}
            try:
                sym_info["rows"] = conn.execute(f'SELECT COUNT(*) FROM "{table}" WHERE "{symbol_col}"=?', (symbol,)).fetchone()[0]
            except Exception as e:
                sym_info["error"] = str(e)
            if ts_col:
                try:
                    mn, mx = conn.execute(
                        f'SELECT MIN("{ts_col}"), MAX("{ts_col}") FROM "{table}" WHERE "{symbol_col}"=?',
                        (symbol,),
                    ).fetchone()
                    sym_info["min_timestamp"] = mn
                    sym_info["max_timestamp"] = mx
                    max_dt = parse_ts(mx)
                    if max_dt:
                        sym_info["age_seconds"] = int((utc_now() - max_dt).total_seconds())
                except Exception as e:
                    sym_info["timestamp_error"] = str(e)
            if ts_col and tf_col:
                try:
                    tf_rows = conn.execute(
                        f'SELECT "{tf_col}", COUNT(*), MIN("{ts_col}"), MAX("{ts_col}") FROM "{table}" WHERE "{symbol_col}"=? GROUP BY "{tf_col}"',
                        (symbol,),
                    ).fetchall()
                    sym_info["by_timeframe"] = {
                        str(tf): {"rows": n, "min_timestamp": mn, "max_timestamp": mx}
                        for tf, n, mn, mx in tf_rows
                    }
                except Exception as e:
                    sym_info["tf_error"] = str(e)
            item["symbols"][symbol] = sym_info
        out.append(item)
    return out


def force_snapshot_stats(conn: sqlite3.Connection, symbols: List[str], tfs: List[int], table: str = "force_snapshots") -> Dict[str, Any]:
    if not table_exists(conn, table):
        return {"exists": False, "error": "force_snapshots table missing"}
    cols = columns(conn, table)
    symbol_col = find_col(cols, ["symbol"])
    tf_col = find_col(cols, ["timeframe", "tf"])
    ts_col = find_col(cols, ["timestamp", "time", "ts", "datetime"])
    if not (symbol_col and tf_col and ts_col):
        return {"exists": True, "error": f"missing required cols symbol/timeframe/timestamp; columns={cols}"}

    out: Dict[str, Any] = {"exists": True, "table": table, "symbols": {}, "comparison": {}}
    for symbol in symbols:
        s_info: Dict[str, Any] = {"total_rows": 0, "timeframes": {}}
        try:
            s_info["total_rows"] = conn.execute(f'SELECT COUNT(*) FROM "{table}" WHERE "{symbol_col}"=?', (symbol,)).fetchone()[0]
        except Exception as e:
            s_info["error"] = str(e)

        for tf in tfs:
            tf_info: Dict[str, Any] = {}
            try:
                n, mn, mx = conn.execute(
                    f'SELECT COUNT(*), MIN("{ts_col}"), MAX("{ts_col}") FROM "{table}" WHERE "{symbol_col}"=? AND "{tf_col}"=?',
                    (symbol, tf),
                ).fetchone()
                tf_info.update({"rows": n, "min_timestamp": mn, "max_timestamp": mx})
                max_dt = parse_ts(mx)
                if max_dt:
                    tf_info["age_seconds"] = int((utc_now() - max_dt).total_seconds())
                    tf_info["is_stale"] = tf_info["age_seconds"] > STALE_BY_TF_SECONDS.get(tf, tf * 60 * 3)
                else:
                    tf_info["age_seconds"] = None
                    tf_info["is_stale"] = n == 0

                # latest 200 timestamps for gap/interval diagnostics
                latest_rows = conn.execute(
                    f'SELECT "{ts_col}" FROM "{table}" WHERE "{symbol_col}"=? AND "{tf_col}"=? ORDER BY "{ts_col}" DESC LIMIT 200',
                    (symbol, tf),
                ).fetchall()
                dts = [parse_ts(r[0]) for r in latest_rows]
                dts = [d for d in dts if d is not None]
                dts = list(reversed(dts))
                intervals = []
                for a, b in zip(dts, dts[1:]):
                    intervals.append((b - a).total_seconds())
                expected = tf * 60
                gap_threshold = max(expected * 1.8, expected + 90)
                gaps = [x for x in intervals if x > gap_threshold]
                tf_info["intervals_count"] = len(intervals)
                tf_info["median_interval_seconds"] = median(intervals) if intervals else None
                tf_info["max_interval_seconds"] = max(intervals) if intervals else None
                tf_info["gap_count"] = len(gaps)
                tf_info["gap_threshold_seconds"] = gap_threshold
                tf_info["expected_interval_seconds"] = expected
                if intervals:
                    tf_info["irregularity_ratio"] = round(len(gaps) / max(1, len(intervals)), 4)
                else:
                    tf_info["irregularity_ratio"] = None
            except Exception as e:
                tf_info["error"] = str(e)
            s_info["timeframes"][str(tf)] = tf_info
        out["symbols"][symbol] = s_info

    # Ratios versus GBPUSD baseline
    base = out["symbols"].get("GBPUSD", {}).get("timeframes", {})
    for symbol in symbols:
        if symbol == "GBPUSD":
            continue
        out["comparison"][symbol] = {}
        for tf in tfs:
            b_rows = safe_int(base.get(str(tf), {}).get("rows"))
            s_rows = safe_int(out["symbols"].get(symbol, {}).get("timeframes", {}).get(str(tf), {}).get("rows"))
            out["comparison"][symbol][str(tf)] = {
                "rows": s_rows,
                "gbpusd_rows": b_rows,
                "row_ratio_vs_gbpusd": round(s_rows / b_rows, 4) if b_rows else None,
            }
    return out


def median(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    s = sorted(vals)
    n = len(s)
    mid = n // 2
    if n % 2:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2


def scan_logs(core: Path, symbol: str, max_files: int = 80) -> Dict[str, Any]:
    logs_dir = core / "logs"
    result = {
        "logs_dir_exists": logs_dir.exists(),
        "files_scanned": 0,
        "symbol_hits": 0,
        "errors": [],
        "bridge_hits": [],
        "db_lock_hits": [],
        "overlap_hits": [],
        "parse_hits": [],
        "recent_files": [],
    }
    if not logs_dir.exists():
        return result
    files = sorted([p for p in logs_dir.rglob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)[:max_files]
    result["recent_files"] = [str(p.relative_to(core)) for p in files[:20]]
    patterns = {
        "errors": re.compile(r"(error|exception|traceback|failed|fail)", re.I),
        "db_lock": re.compile(r"(database is locked|sqlite.*locked|lock|throttle|queue|busy)", re.I),
        "overlap": re.compile(r"(OVERLAP_SKIP|previous lock|scheduler.*lock)", re.I),
        "parse": re.compile(r"(parse|invalid|malformed|decode|symbol)", re.I),
        "bridge": re.compile(r"(bridge|capture|socket|tcp|insert|force_snapshots)", re.I),
    }
    for p in files:
        result["files_scanned"] += 1
        try:
            txt = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        rel = str(p.relative_to(core))
        if symbol.upper() in txt.upper():
            result["symbol_hits"] += txt.upper().count(symbol.upper())
            if patterns["bridge"].search(txt):
                result["bridge_hits"].append(rel)
        for line in tail_lines(txt, 300):
            if symbol.upper() in line.upper() or patterns["errors"].search(line) or patterns["db_lock"].search(line) or patterns["overlap"].search(line):
                if patterns["errors"].search(line):
                    result["errors"].append({"file": rel, "line": line[:500]})
                if patterns["db_lock"].search(line):
                    result["db_lock_hits"].append({"file": rel, "line": line[:500]})
                if patterns["overlap"].search(line):
                    result["overlap_hits"].append({"file": rel, "line": line[:500]})
                if patterns["parse"].search(line) and symbol.upper() in line.upper():
                    result["parse_hits"].append({"file": rel, "line": line[:500]})
    # truncate
    for k in ["errors", "db_lock_hits", "overlap_hits", "parse_hits"]:
        result[k] = result[k][:50]
    result["bridge_hits"] = result["bridge_hits"][:30]
    return result


def tail_lines(txt: str, n: int) -> List[str]:
    lines = txt.splitlines()
    return lines[-n:]


def run_runner(core: Path, cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
    try:
        p = subprocess.run(cmd, cwd=str(core), text=True, capture_output=True, timeout=timeout)
        return {
            "cmd": cmd,
            "returncode": p.returncode,
            "stdout_tail": p.stdout[-6000:],
            "stderr_tail": p.stderr[-6000:],
        }
    except Exception as e:
        return {"cmd": cmd, "error": str(e), "returncode": None}


def classify(report: Dict[str, Any]) -> Dict[str, Any]:
    fs = report.get("force_snapshots", {})
    symbols = fs.get("symbols", {})
    usdjpy = symbols.get("USDJPY", {})
    gbpusd = symbols.get("GBPUSD", {})
    eurusd = symbols.get("EURUSD", {})
    logs = report.get("logs", {})

    result = {
        "primary_bottleneck": "UNCLASSIFIED",
        "confidence": "LOW",
        "evidence": [],
        "excluded": [],
        "next_fix": [],
        "technical_risks": [],
    }

    usd_total = safe_int(usdjpy.get("total_rows"))
    gbp_total = safe_int(gbpusd.get("total_rows"))
    eur_total = safe_int(eurusd.get("total_rows"))
    usd_tf = usdjpy.get("timeframes", {})
    gbp_tf = gbpusd.get("timeframes", {})

    if usd_total == 0:
        result["primary_bottleneck"] = "MT4_STREAM_INACTIVE_OR_SYMBOL_NOT_INGESTED"
        result["confidence"] = "HIGH"
        result["evidence"].append("USDJPY has zero rows in force_snapshots.")
        if gbp_total > 0 or eur_total > 0:
            result["evidence"].append("Other symbols have rows, so global DB is not empty.")
        result["next_fix"] += [
            "Verify USDJPY is enabled in MT4 EA symbol list.",
            "Verify bridge receives USDJPY messages before DB insertion.",
            "Check symbol spelling/suffix in MT4 broker (USDJPY, USDJPY., USDJPYm).",
        ]
        return result

    # Lower TF vs higher TF
    lower_tfs = ["1", "5", "15"]
    higher_tfs = ["30", "60", "240", "1440", "10080"]
    lower_rows = sum(safe_int(usd_tf.get(tf, {}).get("rows")) for tf in lower_tfs)
    higher_rows = sum(safe_int(usd_tf.get(tf, {}).get("rows")) for tf in higher_tfs)
    lower_recent = any(not usd_tf.get(tf, {}).get("is_stale", True) and safe_int(usd_tf.get(tf, {}).get("rows")) > 0 for tf in lower_tfs)
    high_missing_or_stale = all(safe_int(usd_tf.get(tf, {}).get("rows")) == 0 or usd_tf.get(tf, {}).get("is_stale", True) for tf in higher_tfs)

    # Compare ratios
    low_ratio_samples = []
    for tf in lower_tfs:
        u = safe_int(usd_tf.get(tf, {}).get("rows"))
        g = safe_int(gbp_tf.get(tf, {}).get("rows"))
        if g:
            low_ratio_samples.append(u / g)
    avg_low_ratio = sum(low_ratio_samples) / len(low_ratio_samples) if low_ratio_samples else None

    irregular_lower = []
    for tf in lower_tfs:
        irr = usd_tf.get(tf, {}).get("irregularity_ratio")
        if isinstance(irr, (int, float)) and irr > 0.20:
            irregular_lower.append(tf)

    has_db_lock = bool(logs.get("db_lock_hits"))
    has_overlap = bool(logs.get("overlap_hits"))
    has_parse = bool(logs.get("parse_hits"))
    symbol_hits = safe_int(logs.get("symbol_hits"))

    if lower_rows > 0 and high_missing_or_stale:
        result["primary_bottleneck"] = "TF_AGGREGATION_GAP"
        result["confidence"] = "HIGH" if lower_recent else "MEDIUM"
        result["evidence"].append(f"USDJPY lower TF rows exist/recent={lower_recent}; higher TF rows missing/stale.")
        result["evidence"].append(f"lower_rows={lower_rows}, higher_rows={higher_rows}.")
        result["next_fix"] += [
            "Inspect TF aggregation path for USDJPY M30/H1+.",
            "Compare aggregation source table and timeframe scheduler for USDJPY.",
            "Check whether scheduler only refreshes M1/M5/M15 for USDJPY.",
        ]
        return result

    if has_parse and symbol_hits > 0 and usd_total < max(10, gbp_total * 0.05):
        result["primary_bottleneck"] = "BRIDGE_PARSING_MIS_CALIBRATED"
        result["confidence"] = "MEDIUM"
        result["evidence"].append("Logs contain USDJPY parse/symbol hits while DB rows are very low.")
        result["evidence"].append(f"USDJPY total={usd_total}, GBPUSD total={gbp_total}.")
        result["next_fix"] += [
            "Inspect capture_bridge symbol normalization for USDJPY broker suffix.",
            "Log raw incoming USDJPY payload shape before parsing.",
            "Add non-invasive parser counters per symbol.",
        ]
        return result

    if has_db_lock or has_overlap:
        result["primary_bottleneck"] = "DB_INSERT_LATENCY_OR_CROSS_SYMBOL_CONTENTION"
        result["confidence"] = "MEDIUM"
        if has_db_lock:
            result["evidence"].append("Logs contain DB lock/throttle/queue indicators.")
        if has_overlap:
            result["evidence"].append("Logs contain OVERLAP_SKIP / previous lock indicators.")
        result["next_fix"] += [
            "Measure insert latency per symbol in capture bridge logs.",
            "Check scheduler overlap frequency and lock lifetime.",
            "Consider per-symbol insert queue or shorter transaction batches after diagnostics.",
        ]
        return result

    if avg_low_ratio is not None and avg_low_ratio < 0.20:
        result["primary_bottleneck"] = "MT4_STREAM_INCOMPLETE_OR_PAIR_TICK_RATE_TOO_LOW"
        result["confidence"] = "MEDIUM"
        result["evidence"].append(f"USDJPY lower TF row ratio vs GBPUSD is low: {avg_low_ratio:.3f}.")
        result["evidence"].append("No strong DB lock/parse evidence found in logs.")
        result["next_fix"] += [
            "Verify USDJPY Market Watch active and EA subscribed.",
            "Compare real tick arrival counts in MT4 journal for USDJPY vs GBPUSD/EURUSD.",
            "If tick rate truly low, add timer-based heartbeat bar generation for USDJPY without manual DB writes.",
        ]
        return result

    if irregular_lower:
        result["primary_bottleneck"] = "IRREGULAR_MT4_STREAM_OR_DB_THROTTLE"
        result["confidence"] = "MEDIUM"
        result["evidence"].append(f"USDJPY lower TF intervals irregular on TFs: {irregular_lower}.")
        result["next_fix"] += [
            "Compare capture timestamps with MT4 journal ticks.",
            "If MT4 ticks are regular but DB is irregular, inspect bridge/DB.",
            "If MT4 ticks are irregular, classify as stream/tick availability.",
        ]
        return result

    if usd_total > 0:
        result["primary_bottleneck"] = "THIN_BUT_ACTIVE_NEEDS_LONGER_WINDOW_OR_SYMBOL_CAPTURE_BOOST"
        result["confidence"] = "LOW"
        result["evidence"].append("USDJPY has rows but no decisive parse/lock/aggregation signature.")
        result["next_fix"] += [
            "Run diagnostics for a longer window.",
            "Add per-symbol counters in capture bridge logs before patching behavior.",
            "Keep current dashboard warning active.",
        ]
        return result

    return result


def make_md(report: Dict[str, Any]) -> str:
    c = report.get("classification", {})
    lines = [
        "# USDJPY THIN BOTTLENECK DIAGNOSTIC — PowerFlow V7.2.1",
        "",
        f"Generated UTC : {report.get('generated_at_utc')}",
        f"Symbol : `USDJPY`",
        f"DB : `{report.get('db')}`",
        f"Primary bottleneck : `{c.get('primary_bottleneck')}`",
        f"Confidence : `{c.get('confidence')}`",
        "",
        "## Verdict",
        "",
        "```text",
        f"{c.get('primary_bottleneck')}",
        "```",
        "",
        "## Evidence",
        "",
    ]
    ev = c.get("evidence") or []
    lines.extend([f"- {x}" for x in ev] or ["- none"])
    lines += ["", "## Next fix ciblée", ""]
    lines.extend([f"- {x}" for x in c.get("next_fix", [])] or ["- none"])
    lines += ["", "## force_snapshots summary", ""]
    fs = report.get("force_snapshots", {})
    if not fs.get("exists"):
        lines.append(f"`force_snapshots` unavailable: {fs.get('error')}")
    else:
        lines.append("| Symbol | Total rows | TF1 | TF5 | TF15 | TF30 | TF60 | TF240 | TF1440 | TF10080 |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for sym, sinfo in fs.get("symbols", {}).items():
            tfs = sinfo.get("timeframes", {})
            vals = [safe_int(tfs.get(str(tf), {}).get("rows")) for tf in [1, 5, 15, 30, 60, 240, 1440, 10080]]
            lines.append(f"| {sym} | {safe_int(sinfo.get('total_rows'))} | " + " | ".join(str(v) for v in vals) + " |")
        lines += ["", "### USDJPY TF details", ""]
        u = fs.get("symbols", {}).get("USDJPY", {}).get("timeframes", {})
        lines.append("| TF | Rows | Max timestamp | Age sec | Stale | Gap count | Median interval | Max interval |")
        lines.append("|---|---:|---|---:|---|---:|---:|---:|")
        for tf in [1, 5, 15, 30, 60, 240, 1440, 10080]:
            d = u.get(str(tf), {})
            lines.append(
                f"| {tf} | {safe_int(d.get('rows'))} | {d.get('max_timestamp')} | {d.get('age_seconds')} | {d.get('is_stale')} | {d.get('gap_count')} | {d.get('median_interval_seconds')} | {d.get('max_interval_seconds')} |"
            )
    lines += ["", "## Logs scan", ""]
    logs = report.get("logs", {})
    lines += [
        f"- files_scanned : `{logs.get('files_scanned')}`",
        f"- USDJPY symbol_hits : `{logs.get('symbol_hits')}`",
        f"- db_lock_hits : `{len(logs.get('db_lock_hits', []))}`",
        f"- overlap_hits : `{len(logs.get('overlap_hits', []))}`",
        f"- parse_hits : `{len(logs.get('parse_hits', []))}`",
        "",
    ]
    if logs.get("db_lock_hits"):
        lines += ["### DB lock / throttle excerpts", ""]
        for h in logs.get("db_lock_hits", [])[:10]:
            lines.append(f"- `{h.get('file')}` — {h.get('line')}")
    if logs.get("overlap_hits"):
        lines += ["", "### Overlap excerpts", ""]
        for h in logs.get("overlap_hits", [])[:10]:
            lines.append(f"- `{h.get('file')}` — {h.get('line')}")
    if logs.get("parse_hits"):
        lines += ["", "### Parse excerpts", ""]
        for h in logs.get("parse_hits", [])[:10]:
            lines.append(f"- `{h.get('file')}` — {h.get('line')}")
    lines += ["", "## Existing audit runner", ""]
    for key, val in report.get("runners", {}).items():
        lines.append(f"### {key}")
        lines.append("")
        lines.append(f"- returncode : `{val.get('returncode')}`")
        if val.get("stdout_tail"):
            lines.append("")
            lines.append("```text")
            lines.append(val["stdout_tail"][-2000:])
            lines.append("```")
        if val.get("stderr_tail"):
            lines.append("")
            lines.append("```text")
            lines.append(val["stderr_tail"][-2000:])
            lines.append("```")
    lines += [
        "",
        "## Architecture decision",
        "",
        "```text",
        "Do not patch capture_bridge.py until this diagnostic is reviewed.",
        "Do not write powerflow.db.",
        "Do not change P0 or dashboard.",
        "Next change must target the classified bottleneck only.",
        "```",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--core", default=".")
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    ap.add_argument("--timeframes", default="1,5,15,30,60,240,1440,10080")
    ap.add_argument("--json-out", default=None)
    ap.add_argument("--md-out", default=None)
    ap.add_argument("--skip-runners", action="store_true")
    args = ap.parse_args()

    core = Path(args.core).resolve()
    db_path = core / args.db
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    tfs = [int(x.strip()) for x in args.timeframes.split(",") if x.strip()]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

    report: Dict[str, Any] = {
        "generated_at_utc": utc_now().isoformat(),
        "core": str(core),
        "db": str(db_path),
        "symbols": symbols,
        "timeframes": tfs,
        "db_tables": [],
        "force_snapshots": {},
        "logs": {},
        "runners": {},
        "classification": {},
    }

    if not db_path.exists():
        report["classification"] = {
            "primary_bottleneck": "DB_MISSING",
            "confidence": "HIGH",
            "evidence": [f"DB not found: {db_path}"],
            "next_fix": ["Start from correct Core directory or restore powerflow.db."],
        }
    else:
        conn = open_ro_db(db_path)
        try:
            report["db_tables"] = db_table_scan(conn, symbols)
            report["force_snapshots"] = force_snapshot_stats(conn, symbols, tfs)
        finally:
            conn.close()

        report["logs"] = scan_logs(core, "USDJPY")

        if not args.skip_runners:
            # Run existing audit scripts if available.
            run_audit = core / "run_audit_usdjpy_once.py"
            if run_audit.exists():
                report["runners"]["run_audit_usdjpy_once.py"] = run_runner(core, [sys.executable, str(run_audit), "--db", args.db, "--pretty"])
            fast = core / "audit_usdjpy_fast.py"
            if fast.exists() and fast.name != Path(__file__).name:
                report["runners"]["audit_usdjpy_fast.py"] = run_runner(core, [sys.executable, str(fast), "--db", args.db, "--symbol", "USDJPY", "--core", "."])

        report["classification"] = classify(report)

    out_dir = core / "output"
    out_dir.mkdir(exist_ok=True)
    json_out = Path(args.json_out) if args.json_out else out_dir / f"usdjpy_thin_bottleneck_diagnostic_{stamp}.json"
    md_out = Path(args.md_out) if args.md_out else core / f"RAPPORT_USDJPY_THIN_BOTTLENECK_DIAGNOSTIC_{stamp}.md"
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_out.write_text(make_md(report), encoding="utf-8")

    print(f"USDJPY_THIN_DIAGNOSTIC bottleneck={report['classification'].get('primary_bottleneck')} confidence={report['classification'].get('confidence')}")
    print(f"JSON: {json_out}")
    print(f"MD: {md_out}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
