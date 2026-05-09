#!/usr/bin/env python3
from __future__ import annotations
import argparse, json, os, subprocess, sys, time, uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

TIMEOUT_SECONDS = 30
NODE_TIMEOUT_SECONDS = 90
DEFAULT_WINDOW_MINUTES = 180
OUT = Path("output")
P = {"report": OUT / "cycle_report.json", "quality": OUT / "data_quality_guard.json",
     "validator": OUT / "market_open_validator.json", "entropy": OUT / "entropy_engine.json",
     "session": OUT / "session_overlay.json", "session_input": OUT / "session_overlay_input.json",
     "node": OUT / "temporal_node_state.json", "energy": OUT / "currency_energy.json",
     "queue": OUT / "behavioral_alert_queue.json", "cascade": OUT / "cascade_state.json",
     "dashboard": OUT / "dashboard_data.json"}

def now(): return datetime.now(timezone.utc)
def iso(): return now().isoformat(timespec="seconds")
def today(): return now().date().isoformat()
def log(step, msg): print(f"[{iso()}] [step {step}] {msg}", flush=True)
def clean_symbol(symbol): return symbol.strip().rstrip(".").upper()
def compact(text, limit=2000): return " ".join(text.replace("\r", "\n").split())[:limit]
def timeout_for(script): return NODE_TIMEOUT_SECONDS if script == "run_temporal_node_state_once.py" else TIMEOUT_SECONDS
def window(minutes):
    end, start = now(), now() - timedelta(minutes=minutes)
    return tuple(x.isoformat(timespec="seconds").replace("+00:00", "") for x in (start, end))
def env_utf8():
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env
def pack(step, module, status, ms, err=None):
    return {"step": step, "module": module, "status": status, "duration_ms": ms, "error": err}

def write_session_input():
    payload = {"alerts": []}
    if P["queue"].exists():
        try:
            raw = json.loads(P["queue"].read_text(encoding="utf-8"))
            if isinstance(raw, list): payload = {"alerts": raw}
            elif isinstance(raw, dict) and any(k in raw for k in ("alerts", "items", "queue", "behavioral_alert_queue")): payload = raw
        except (OSError, json.JSONDecodeError):
            pass
    P["session_input"].write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def steps():
    return [
        (1, "run_data_quality_guard_once.py", P["quality"], lambda a: ["--db", a.db, "--since", a.since, "--pretty", "--output", str(P["quality"])], (0, 2)),
        (2, "run_market_open_validator_once.py", P["validator"], lambda a: ["--db", a.db, "--since", a.since, "--recent-minutes", str(a.recent_minutes), "--pretty", "--output", str(P["validator"])], (0, 2)),
        (3, "run_entropy_engine_once.py", P["entropy"], lambda a: ["--db", a.db, "--symbol", a.symbol, "--pretty", "--output", str(P["entropy"])], (0,)),
        (4, "run_session_overlay_once.py", P["session"], lambda a: ["--input", str(P["session_input"]), "--pretty", "--output", str(P["session"])], (0,)),
        (5, "run_temporal_node_state_once.py", P["node"], lambda a: ["--db", a.db, "--symbol", a.symbol, "--pretty", "--out", str(P["node"])], (0,)),
        (6, "run_currency_energy_probe_once.py", P["energy"], lambda a: ["--db", a.db, "--symbol", a.symbol, "--pretty", "--out", str(P["energy"])], (0,)),
        (7, "run_confluence_alert.py", P["queue"], lambda a: ["--once"], (0,)),
        (8, "run_cascade_engine_once.py", P["cascade"], lambda a: ["--output", str(P["cascade"])], (0,)),
        (9, "run_powerflow_dashboard_refresh_once.py", P["dashboard"], lambda a: ["--db", a.db, "--symbol", a.symbol, "--start", a.start, "--end", a.end, "--temporal", str(P["node"]), "--energy", str(P["energy"]), "--behavioral-queue", str(P["queue"]), "--dashboard-out", str(P["dashboard"]), "--pretty"], (0,)),
    ]

def run_step(spec, args):
    n, script, out_path, make_args, accepted = spec
    module, cmd, t0 = Path(script).stem, [sys.executable, script, *make_args(args)], time.perf_counter()
    timeout = timeout_for(script)
    if n == 4: write_session_input()
    if args.dry_run:
        log(n, "DRY-RUN " + " ".join(cmd)); return pack(n, module, "OK", 0)
    if not Path(script).is_file():
        err = f"missing script: {script}"; log(n, f"FAIL {module} (0 ms): {err}"); return pack(n, module, "FAIL", 0, err)
    log(n, "START " + " ".join(cmd))
    try:
        proc = subprocess.run(cmd, timeout=timeout, check=False, text=True, capture_output=True, env=env_utf8())
        ms = int((time.perf_counter() - t0) * 1000)
        if proc.returncode == 0:
            log(n, f"OK {module} ({ms} ms)"); return pack(n, module, "OK", ms)
        if proc.returncode in accepted and out_path.exists():
            log(n, f"OK {module} ({ms} ms): accepted returncode={proc.returncode}; output={out_path}")
            return pack(n, module, "OK", ms)
        err = compact(proc.stderr or proc.stdout or f"returncode={proc.returncode}")
    except subprocess.TimeoutExpired as exc:
        ms, err = int((time.perf_counter() - t0) * 1000), f"timeout after {timeout}s"
        if exc.stderr or exc.stdout: err += ": " + compact(str(exc.stderr or exc.stdout))
    except OSError as exc:
        ms, err = int((time.perf_counter() - t0) * 1000), compact(str(exc))
    log(n, f"FAIL {module} ({ms} ms): {err}")
    return pack(n, module, "FAIL", ms, err)

def parse_args():
    parser = argparse.ArgumentParser(description="Run one full PowerFlow V7.1 cycle.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--since", default=today(), help="YYYY-MM-DD for quality validators")
    parser.add_argument("--recent-minutes", type=int, default=180)
    parser.add_argument("--window-minutes", type=int, default=DEFAULT_WINDOW_MINUTES)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    args.symbol = clean_symbol(args.symbol)
    args.start, args.end = window(args.window_minutes)
    return args

def main():
    args = parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    started, cycle_id, t0 = iso(), str(uuid.uuid4()), time.perf_counter()
    log("cycle", f"START cycle_id={cycle_id} db={args.db} symbol={args.symbol} since={args.since} dry_run={args.dry_run}")
    results = [run_step(spec, args) for spec in steps()]
    ok = sum(1 for item in results if item["status"] == "OK")
    status = "COMPLETE" if ok == len(results) else ("FAILED" if ok == 0 else "PARTIAL")
    report = {"cycle_id": cycle_id, "started_at_utc": started, "total_duration_ms": int((time.perf_counter() - t0) * 1000), "steps": results, "cycle_status": status}
    P["report"].write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    log("cycle", f"END status={status} duration_ms={report['total_duration_ms']} report={P['report']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
