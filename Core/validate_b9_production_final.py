#!/usr/bin/env python3
"""PowerFlow B9 production final E2E validator.

This script validates what can be validated locally:
- Flask B9/B8 endpoints if cockpit_server_b9.py is running on port 8880.
- B9 live nodes in output/b9_nodes_live.
- tick_archive.db freshness.
- optional scheduler loop for a bounded live validation window.

It does not activate Telegram and does not write into PowerFlow databases.
"""

from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


UTC = dt.timezone.utc


def utc_now() -> dt.datetime:
    return dt.datetime.now(tz=UTC)


def iso_now() -> str:
    return utc_now().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: Any) -> Optional[dt.datetime]:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    text = text.replace("Z", "+00:00")
    candidates = [
        text,
        text.replace(" ", "T"),
    ]
    for candidate in candidates:
        try:
            parsed = dt.datetime.fromisoformat(candidate)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=UTC)
            return parsed.astimezone(UTC)
        except Exception:
            pass
    return None


def http_json(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        body = response.read().decode("utf-8", errors="replace")
        data = json.loads(body) if body.strip() else {}
        return {
            "ok": 200 <= int(response.status) < 300,
            "status_code": int(response.status),
            "url": url,
            "json": data,
        }


def check_flask(base_url: str) -> Dict[str, Any]:
    endpoints = {
        "health": "/api/health",
        "b9_nodes_live": "/api/b9-nodes-live?symbol=GBPUSD&limit=5",
        "b8_coalition_context": "/api/b8-coalition-context?symbol=GBPUSD",
    }
    results: Dict[str, Any] = {}
    for name, path in endpoints.items():
        url = base_url.rstrip("/") + path
        try:
            results[name] = http_json(url)
        except Exception as exc:
            results[name] = {
                "ok": False,
                "url": url,
                "error": repr(exc),
            }
    ok = all(item.get("ok") for item in results.values())
    return {
        "ok": ok,
        "base_url": base_url,
        "endpoints": results,
    }


def list_nodes(core: Path) -> List[Path]:
    node_dir = core / "output" / "b9_nodes_live"
    return sorted(node_dir.glob("*.json")) if node_dir.exists() else []


def read_node_summary(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {
            "file": path.name,
            "error": repr(exc),
        }
    return {
        "file": path.name,
        "node_id": data.get("node_id", data.get("id", path.stem)),
        "symbol": data.get("symbol", data.get("raw", {}).get("symbol", "UNKNOWN")),
        "verdict": data.get("verdict", data.get("price_verdict_candidate", "UNKNOWN")),
        "mtime_utc": dt.datetime.fromtimestamp(path.stat().st_mtime, tz=UTC).isoformat().replace("+00:00", "Z"),
    }


def check_nodes(core: Path, before_count: Optional[int] = None) -> Dict[str, Any]:
    files = list_nodes(core)
    latest = [read_node_summary(path) for path in files[-10:]]
    out = {
        "ok": len(files) > 0,
        "count": len(files),
        "before_count": before_count,
        "created_during_run": None if before_count is None else len(files) - before_count,
        "latest": latest,
        "dir": str(core / "output" / "b9_nodes_live"),
    }
    if before_count is not None:
        out["ok"] = len(files) > before_count
    return out


def table_columns(conn: sqlite3.Connection, table: str) -> List[str]:
    return [str(row[1]) for row in conn.execute(f"PRAGMA table_info({quote_ident(table)})").fetchall()]


def quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def pick_col(cols: Iterable[str], names: Iterable[str]) -> Optional[str]:
    cols = list(cols)
    lower = {c.lower(): c for c in cols}
    for name in names:
        if name.lower() in lower:
            return lower[name.lower()]
    for col in cols:
        cl = col.lower()
        for name in names:
            if name.lower() in cl:
                return col
    return None


def check_tick_archive(core: Path, max_age_minutes: float = 5.0) -> Dict[str, Any]:
    db_path = core / "tick_archive.db"
    if not db_path.exists():
        return {
            "ok": False,
            "db_path": str(db_path),
            "error": "tick_archive.db missing",
        }

    try:
        conn = sqlite3.connect(str(db_path))
        table = "tick_stream"
        tables = [str(row[0]) for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        if table not in tables:
            candidates = [t for t in tables if "tick" in t.lower()]
            if candidates:
                table = candidates[0]
            else:
                return {
                    "ok": False,
                    "db_path": str(db_path),
                    "tables": tables,
                    "error": "no tick table found",
                }

        cols = table_columns(conn, table)
        symbol_col = pick_col(cols, ["symbol", "pair", "instrument"])
        ts_col = pick_col(cols, ["ts_utc", "timestamp", "time", "datetime", "created_at", "ts"])

        if ts_col is None:
            return {
                "ok": False,
                "db_path": str(db_path),
                "table": table,
                "columns": cols,
                "error": "no timestamp column found",
            }

        params: List[Any] = []
        where = ""
        if symbol_col:
            where = f"WHERE UPPER({quote_ident(symbol_col)}) = ?"
            params.append("GBPUSD")

        count_sql = f"SELECT COUNT(*), MAX({quote_ident(ts_col)}) FROM {quote_ident(table)} {where}"
        count, max_ts = conn.execute(count_sql, params).fetchone()
        parsed = parse_time(max_ts)
        age_min = None
        if parsed:
            age_min = (utc_now() - parsed).total_seconds() / 60.0
        conn.close()

        return {
            "ok": bool(count and count > 0 and age_min is not None and age_min <= max_age_minutes),
            "db_path": str(db_path),
            "table": table,
            "symbol_column": symbol_col,
            "timestamp_column": ts_col,
            "count": int(count or 0),
            "max_timestamp": str(max_ts),
            "age_minutes": age_min,
            "max_age_minutes": max_age_minutes,
        }
    except Exception as exc:
        return {
            "ok": False,
            "db_path": str(db_path),
            "error": repr(exc),
        }


def run_scheduler_loop(core: Path, duration_seconds: int, interval_seconds: int) -> Dict[str, Any]:
    before = len(list_nodes(core))
    logs: List[Dict[str, Any]] = []
    deadline = time.time() + max(1, duration_seconds)
    loops = 0

    while time.time() < deadline:
        loops += 1
        cmd = [
            sys.executable,
            "scheduler_powerflow_turbo_wrapper.py",
            "--symbols",
            "GBPUSD",
            "--continue-on-error",
        ]
        started = time.time()
        proc = subprocess.run(
            cmd,
            cwd=str(core),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        elapsed = round(time.time() - started, 3)
        tail = ((proc.stdout or "") + "\n" + (proc.stderr or ""))[-4000:]
        logs.append({
            "loop": loops,
            "returncode": proc.returncode,
            "elapsed_seconds": elapsed,
            "tail": tail,
        })
        if time.time() < deadline:
            time.sleep(max(1, interval_seconds))

    after = len(list_nodes(core))
    return {
        "ok": after > before and all(item["returncode"] in (0, 1) for item in logs),
        "before_nodes": before,
        "after_nodes": after,
        "created_nodes": after - before,
        "loops": loops,
        "duration_seconds": duration_seconds,
        "logs": logs,
    }


def markdown_status(ok: bool) -> str:
    return "✅" if ok else "❌"


def write_reports(core: Path, report: Dict[str, Any]) -> Tuple[Path, Path]:
    reports_dir = core / "docs" / "Reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    json_path = reports_dir / "B9_PRODUCTION_FINAL_VALIDATION_RESULT.json"
    md_path = reports_dir / "RAPPORT_VALIDATION_B9_PRODUCTION_FINAL.md"

    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    flask = report.get("flask", {})
    nodes = report.get("nodes", {})
    tick = report.get("tick_archive", {})
    sched = report.get("scheduler_5min", {})

    md = f"""# RAPPORT VALIDATION FINALE — Pipeline B9 Production

**Date génération :** {report.get('timestamp_utc')}  
**Statut global :** {markdown_status(report.get('ok', False))} {'PRODUCTION PIPELINE VALIDÉ' if report.get('ok') else 'VALIDATION PARTIELLE / À COMPLÉTER'}  
**Mode Telegram :** OFF / DRY-RUN

---

## 1. Résumé

| Composant | Statut | Détail |
|---|---:|---|
| Flask Server B9+B8 | {markdown_status(flask.get('ok', False))} | endpoints API |
| B9 Nodes Live | {markdown_status(nodes.get('ok', False))} | count={nodes.get('count')} created_during_run={nodes.get('created_during_run')} |
| Tick Archive | {markdown_status(tick.get('ok', False))} | count={tick.get('count')} age_min={tick.get('age_minutes')} |
| Scheduler Runtime | {markdown_status(sched.get('ok', False))} | created_nodes={sched.get('created_nodes')} loops={sched.get('loops')} |

---

## 2. Endpoints API

Base URL : `{flask.get('base_url')}`

| Endpoint | Statut |
|---|---:|
| /api/health | {markdown_status(flask.get('endpoints', {}).get('health', {}).get('ok', False))} |
| /api/b9-nodes-live | {markdown_status(flask.get('endpoints', {}).get('b9_nodes_live', {}).get('ok', False))} |
| /api/b8-coalition-context | {markdown_status(flask.get('endpoints', {}).get('b8_coalition_context', {}).get('ok', False))} |

---

## 3. Nodes B9

Dossier : `{nodes.get('dir')}`  
Nombre : `{nodes.get('count')}`

Derniers nodes :

```json
{json.dumps(nodes.get('latest', []), ensure_ascii=False, indent=2, default=str)}
```

---

## 4. Tick Archive

```json
{json.dumps(tick, ensure_ascii=False, indent=2, default=str)}
```

---

## 5. Scheduler Runtime

```json
{json.dumps({k:v for k,v in sched.items() if k != 'logs'}, ensure_ascii=False, indent=2, default=str)}
```

---

## 6. Activation Telegram

Statut : **NON ACTIVÉ**.

Conditions avant activation :
- endpoints OK ;
- node B9 live créée par scheduler ;
- tick archive frais ;
- message Telegram sans BUY/SELL ;
- phrase finale : `⚡ Perception transmise — Trader filtre.`

---

## 7. Verdict

{('Pipeline B9 validé côté runtime local.' if report.get('ok') else 'Validation partielle : corriger les composants en échec puis relancer ce script.')}

"""
    md_path.write_text(md, encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description="B9 production final E2E validator")
    parser.add_argument("--core", default=str(Path(__file__).resolve().parent))
    parser.add_argument("--flask-url", default="http://localhost:8880")
    parser.add_argument("--skip-flask", action="store_true")
    parser.add_argument("--run-scheduler", action="store_true")
    parser.add_argument("--duration-seconds", type=int, default=300)
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--tick-max-age-minutes", type=float, default=5.0)
    args = parser.parse_args()

    core = Path(args.core).resolve()
    before_nodes = len(list_nodes(core))

    report: Dict[str, Any] = {
        "timestamp_utc": iso_now(),
        "core": str(core),
        "flask": {"ok": None, "skipped": True} if args.skip_flask else check_flask(args.flask_url),
        "tick_archive": check_tick_archive(core, args.tick_max_age_minutes),
        "scheduler_5min": {"ok": None, "skipped": True},
    }

    if args.run_scheduler:
        report["scheduler_5min"] = run_scheduler_loop(
            core,
            duration_seconds=args.duration_seconds,
            interval_seconds=args.interval_seconds,
        )

    report["nodes"] = check_nodes(core, before_count=before_nodes if args.run_scheduler else None)

    required_checks = [
        bool(report["tick_archive"].get("ok")),
        bool(report["nodes"].get("ok")),
    ]
    if not args.skip_flask:
        required_checks.append(bool(report["flask"].get("ok")))
    if args.run_scheduler:
        required_checks.append(bool(report["scheduler_5min"].get("ok")))

    report["ok"] = all(required_checks)

    json_path, md_path = write_reports(core, report)

    print("[B9-PROD-E2E] result=" + ("OK" if report["ok"] else "PARTIAL_OR_FAIL"))
    print("[B9-PROD-E2E] json=" + str(json_path))
    print("[B9-PROD-E2E] md=" + str(md_path))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
