# -*- coding: utf-8 -*-
"""PowerFlow V7.2 — Multi-Symbol Scheduler.

Cycle configurable toutes les 5 minutes par défaut.
Exécute les runners paramétriques par symbole puis la cross-validation une seule fois.
"""
from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = "scheduler_config.json"


@dataclass
class StepResult:
    name: str
    command: list[str]
    returncode: int
    elapsed_seconds: float
    stdout_tail: str = ""
    stderr_tail: str = ""

    @property
    def ok(self) -> bool:
        return self.returncode == 0


@dataclass
class CycleReport:
    cycle_id: int
    started_at: str
    ended_at: str | None = None
    symbols: list[str] = field(default_factory=list)
    steps: list[StepResult] = field(default_factory=list)
    skipped: bool = False
    error_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "symbols": self.symbols,
            "skipped": self.skipped,
            "error_count": self.error_count,
            "steps": [s.__dict__ | {"ok": s.ok} for s in self.steps],
        }


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_config(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {
            "interval_seconds": 300,
            "symbols": ["GBPUSD", "EURUSD", "USDJPY"],
            "enabled": True,
            "log_path": "logs/scheduler.log",
            "db_path": "powerflow.db",
            "max_consecutive_errors": 3,
            "continue_after_symbol_error": True,
            "run_dashboard_refresh": True,
        }
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Invalid config JSON: {p}")
    return data


def _log(log_path: str | Path, message: str) -> None:
    line = f"{_utc_now()} {message}"
    print(line)
    p = Path(log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(line + "\n")


def _run_step(name: str, cmd: list[str], log_path: str | Path, timeout: int = 240) -> StepResult:
    t0 = time.perf_counter()
    _log(log_path, f"STEP_START {name} :: {' '.join(cmd)}")
    proc = subprocess.run(
        cmd,
        text=True,
        capture_output=True,
        timeout=timeout,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    elapsed = time.perf_counter() - t0
    stdout_tail = (proc.stdout or "")[-2000:]
    stderr_tail = (proc.stderr or "")[-2000:]
    status = "OK" if proc.returncode == 0 else "FAIL"
    _log(log_path, f"STEP_END {name} status={status} returncode={proc.returncode} elapsed={elapsed:.2f}s")
    if stdout_tail.strip():
        _log(log_path, f"STDOUT {name}: {stdout_tail.strip().replace(chr(10), ' | ')}")
    if stderr_tail.strip():
        _log(log_path, f"STDERR {name}: {stderr_tail.strip().replace(chr(10), ' | ')}")
    return StepResult(name, cmd, proc.returncode, round(elapsed, 3), stdout_tail, stderr_tail)


def _surface(symbol: str, filename: str) -> str:
    return str(Path("output") / "dashboard_surface" / symbol.upper() / filename)


def _symbol_steps(py: str, db: str, symbol: str) -> list[tuple[str, list[str], int]]:
    sym = symbol.upper()
    return [
        ("temporal_node", [py, "run_temporal_node_state_once.py", "--db", db, "--symbol", sym, "--out", _surface(sym, "node.json"), "--pretty"], 180),
        ("energy", [py, "run_currency_energy_probe_once.py", "--db", db, "--symbol", sym, "--out", _surface(sym, "energy.json"), "--pretty"], 180),
        ("regime_legacy", [py, "run_regime_engine_once.py", "--db", db, "--symbol", sym, "--out", _surface(sym, "regime_legacy.json"), "--pretty"], 180),
        ("temporal_density", [py, "run_temporal_density_once.py", "--db", db, "--symbol", sym, "--out", f"output/temporal_density_state_{sym}.json", "--pretty"], 180),
        ("spearman_gravity", [py, "run_spearman_gravity_once.py", "--db", db, "--symbol", sym, "--out", f"output/spearman_gravity_state_{sym}.json", "--pretty"], 180),
        ("behavioral_mapper", [py, "run_behavioral_alert_mapper_once.py", "--symbol", sym, "--temporal", _surface(sym, "node.json"), "--energy", _surface(sym, "energy.json"), "--out", f"output/behavioral_alert_queue_{sym}.json", "--pretty", "--summary"], 180),
    ]


def _cycle(py: str, db: str, symbols: list[str], config: dict[str, Any], cycle_id: int) -> CycleReport:
    log_path = config.get("log_path", "logs/scheduler.log")
    report = CycleReport(cycle_id=cycle_id, started_at=_utc_now(), symbols=[s.upper() for s in symbols])
    for sym in symbols:
        _log(log_path, f"SYMBOL_START {sym}")
        for step_name, cmd, timeout in _symbol_steps(py, db, sym):
            try:
                result = _run_step(f"{sym}.{step_name}", cmd, log_path, timeout=timeout)
            except subprocess.TimeoutExpired as exc:
                result = StepResult(f"{sym}.{step_name}", cmd, 124, float(timeout), "", str(exc))
                _log(log_path, f"STEP_TIMEOUT {sym}.{step_name} timeout={timeout}")
            report.steps.append(result)
            if not result.ok:
                report.error_count += 1
                if not config.get("continue_after_symbol_error", True):
                    report.ended_at = _utc_now()
                    return report
        _log(log_path, f"SYMBOL_END {sym}")

    all_symbols = ",".join(s.upper() for s in symbols)
    cv_cmd = [py, "run_cross_symbol_validation_once.py", "--db", db, "--symbols", all_symbols, "--pretty"]
    report.steps.append(_run_step("cross_symbol_validation", cv_cmd, log_path, timeout=180))
    if not report.steps[-1].ok:
        report.error_count += 1

    if config.get("run_dashboard_refresh", True):
        dash_cmd = [py, "run_powerflow_dashboard_refresh_once.py", "--skip-cockpit", "--refresh-cockpit-from-queue", "--pretty", "--summary"]
        if Path("run_powerflow_dashboard_refresh_once.py").exists():
            result = _run_step("dashboard_refresh", dash_cmd, log_path, timeout=240)
            report.steps.append(result)
            if not result.ok:
                report.error_count += 1
        else:
            _log(log_path, "DASHBOARD_REFRESH_SKIP runner missing")

    report.ended_at = _utc_now()
    Path("output").mkdir(exist_ok=True)
    Path("output/scheduler_last_cycle_report.json").write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return report


def _lock_path() -> Path:
    return Path("logs") / "scheduler_powerflow.lock"


def _acquire_lock() -> bool:
    lock = _lock_path()
    lock.parent.mkdir(parents=True, exist_ok=True)
    if lock.exists():
        return False
    lock.write_text(str(os.getpid()), encoding="utf-8")
    return True


def _release_lock() -> None:
    try:
        _lock_path().unlink(missing_ok=True)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.2 Multi-Symbol Scheduler")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--db", default=None)
    parser.add_argument("--symbols", default=None, help="CSV override")
    parser.add_argument("--interval-seconds", type=int, default=None)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    config = _load_config(args.config)
    log_path = config.get("log_path", "logs/scheduler.log")
    if not config.get("enabled", True) and not args.once:
        _log(log_path, "SCHEDULER_DISABLED_BY_CONFIG")
        return 0

    db = args.db or config.get("db_path", "powerflow.db")
    symbols = [s.strip().upper() for s in (args.symbols or ",".join(config.get("symbols", ["GBPUSD"]))).split(",") if s.strip()]
    interval = int(args.interval_seconds or config.get("interval_seconds", 300))
    max_errors = int(config.get("max_consecutive_errors", 3))
    py = sys.executable
    cycle_id = 0
    consecutive_errors = 0
    started = time.time()
    completed_cycles = 0

    stop_requested = False

    def _signal_handler(signum: int, frame: Any) -> None:
        nonlocal stop_requested
        stop_requested = True
        _log(log_path, f"STOP_REQUESTED signal={signum}")

    signal.signal(signal.SIGINT, _signal_handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _signal_handler)

    try:
        while not stop_requested:
            cycle_id += 1
            if not _acquire_lock():
                _log(log_path, f"OVERLAP_SKIP cycle={cycle_id} previous lock active")
                if args.once:
                    return 2
                time.sleep(interval)
                continue
            try:
                _log(log_path, f"CYCLE_START id={cycle_id} symbols={symbols}")
                report = _cycle(py, db, symbols, config, cycle_id)
                completed_cycles += 1
                if report.error_count:
                    consecutive_errors += 1
                else:
                    consecutive_errors = 0
                _log(log_path, f"CYCLE_END id={cycle_id} errors={report.error_count} consecutive_errors={consecutive_errors}")
            finally:
                _release_lock()

            if args.once:
                return 0 if consecutive_errors == 0 else 1
            if consecutive_errors >= max_errors:
                _log(log_path, f"MAX_CONSECUTIVE_ERRORS_REACHED value={consecutive_errors}; scheduler stops")
                return 1
            elapsed_cycle_sleep = interval
            for _ in range(elapsed_cycle_sleep):
                if stop_requested:
                    break
                time.sleep(1)
    finally:
        duration = round(time.time() - started, 1)
        _release_lock()
        _log(log_path, f"SCHEDULER_SUMMARY completed_cycles={completed_cycles} duration_seconds={duration} consecutive_errors={consecutive_errors}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
