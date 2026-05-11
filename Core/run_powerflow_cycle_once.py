"""
run_powerflow_cycle_once.py
PowerFlow V7.1 — Multi-symbol capable non-blocking cycle orchestrator.

This replacement keeps GBPUSD backward compatibility while adding:
  --symbols GBPUSD,EURUSD,USDJPY,XAUUSD
  --sequential (explicit; current implementation is sequential and safe)
  --continue-on-fail default non-blocking behavior

It calls existing run_* scripts only if present. Missing optional scripts are
reported as SKIPPED, not fatal, so the cycle can be introduced progressively.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

try:
    from pf_symbol_mapper import DEFAULT_SYMBOL, parse_symbols
except ImportError:
    sys.path.append(str(Path(__file__).resolve().parent))
    from pf_symbol_mapper import DEFAULT_SYMBOL, parse_symbols


CORE_DIR = Path(__file__).resolve().parent
REPO_ROOT = CORE_DIR.parent
DEFAULT_OUTPUT = "output/cycle_report.json"


@dataclass(frozen=True)
class CycleStep:
    name: str
    script: str
    args: Sequence[str]
    timeout_seconds: int = 60
    optional: bool = True
    accepts_symbol: bool = True


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def script_path(script: str) -> Path:
    p = Path(script)
    if p.is_absolute():
        return p
    candidate_core = CORE_DIR / script
    if candidate_core.exists():
        return candidate_core
    return REPO_ROOT / script


def default_steps() -> List[CycleStep]:
    """P0 corrected operational steps.

    POWERFLOW_CYCLE_SINCE can be set from PowerShell to validate a tactical window:
      $env:POWERFLOW_CYCLE_SINCE="2026-05-11T01:15:00+00:00"
    """
    cycle_since = os.environ.get("POWERFLOW_CYCLE_SINCE") or datetime.now(timezone.utc).date().isoformat()
    if cycle_since.endswith("+00:00"):
        cycle_since = cycle_since[:-6]
    cycle_end = os.environ.get("POWERFLOW_CYCLE_END") or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "")

    return [
        CycleStep(
            name="data_quality_guard",
            script="run_data_quality_guard_once.py",
            args=[
                "--since", cycle_since,
                "--tfs", "1,5,15",
                "--pretty",
                "--output", "output/data_quality_guard_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=False,
        ),
        CycleStep(
            name="market_open_validator",
            script="run_market_open_validator_once.py",
            args=[
                "--since", cycle_since,
                "--tfs", "1,5,15",
                "--recent-minutes", "180",
                "--pretty",
                "--output", "output/market_open_validator_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=True,
        ),
        CycleStep(
            name="regime_engine",
            script="run_regime_engine_once.py",
            args=[
                "--pretty",
                "--out", "output/regime_result_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=True,
        ),
        CycleStep(
            name="temporal_density",
            script="run_temporal_density_once.py",
            args=[
                "--tfs", "1,5,15",
                "--summary",
                "--pretty",
                "--out", "output/temporal_density_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=False,
        ),
        CycleStep(
            name="spearman_gravity",
            script="run_spearman_gravity_once.py",
            args=[
                "--tfs", "1,5,15",
                "--summary",
                "--pretty",
                "--out", "output/spearman_gravity_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=False,
        ),
        CycleStep(
            name="fractal_resonance",
            script="run_fractal_resonance_once.py",
            args=[
                "--tfs", "1,5,15,30,60",
                "--pretty",
                "--output", "output/fractal_resonance_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=True,
        ),
        CycleStep(
            name="temporal_node_state",
            script="run_temporal_node_state_once.py",
            args=[
                "--recent-minutes", "60",
                "--timeframes", "1,5,15,30,60",
                "--pretty",
                "--out", "output/temporal_node_state.json",
            ],
            timeout_seconds=90,
            optional=True,
            accepts_symbol=True,
        ),
        CycleStep(
            name="currency_energy_probe",
            script="run_currency_energy_probe_once.py",
            args=[
                "--pretty",
                "--out", "output/currency_energy_probe_{symbol}.json",
            ],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=True,
        ),
        CycleStep(
            name="confluence_alert",
            script="run_confluence_alert.py",
            args=[
                "--once",
                "--dry-run",
            ],
            timeout_seconds=90,
            optional=True,
            accepts_symbol=False,
        ),
        CycleStep(
            name="cascade_engine",
            script="run_cascade_engine_once.py",
            args=[],
            timeout_seconds=60,
            optional=True,
            accepts_symbol=False,
        ),
        CycleStep(
            name="dashboard_refresh",
            script="run_powerflow_dashboard_refresh_once.py",
            args=[
                "--pretty",
                "--start", cycle_since,
                "--end", cycle_end,
            ],
            timeout_seconds=90,
            optional=True,
            accepts_symbol=False,
        ),
    ]

def format_args(args: Sequence[str], symbol: str) -> List[str]:
    return [str(a).format(symbol=symbol) for a in args]


def run_step(step: CycleStep, db_path: str, symbol: str, dry_run: bool) -> Dict[str, object]:
    path = script_path(step.script)
    started = time.time()

    if not path.exists():
        return {
            "step": step.name,
            "script": str(path),
            "status": "SKIPPED" if step.optional else "FAIL",
            "reason": "SCRIPT_NOT_FOUND",
            "duration_seconds": 0.0,
        }

    cmd = [sys.executable, str(path), "--db", db_path]
    if step.accepts_symbol:
        cmd.extend(["--symbol", symbol])
    cmd.extend(format_args(step.args, symbol))

    if dry_run:
        return {
            "step": step.name,
            "script": str(path),
            "status": "DRY_RUN",
            "cmd": cmd,
            "duration_seconds": 0.0,
        }

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(CORE_DIR),
            capture_output=True,
            text=True,
            timeout=step.timeout_seconds,
            env=env,
        )
        duration = round(time.time() - started, 3)
        status = "OK" if proc.returncode == 0 else "FAIL"
        # Some PowerFlow runners return 2 while still producing JSON. Keep explicit.
        if proc.returncode == 2 and proc.stdout.strip().startswith("{"):
            status = "ACCEPTED_RETURNCODE_WITH_OUTPUT"
        return {
            "step": step.name,
            "script": str(path),
            "status": status,
            "returncode": proc.returncode,
            "duration_seconds": duration,
            "stdout_tail": proc.stdout[-4000:],
            "stderr_tail": proc.stderr[-4000:],
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "step": step.name,
            "script": str(path),
            "status": "FAIL",
            "reason": "TIMEOUT",
            "timeout_seconds": step.timeout_seconds,
            "duration_seconds": round(time.time() - started, 3),
            "stdout_tail": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr_tail": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "cmd": cmd,
        }
    except Exception as exc:
        return {
            "step": step.name,
            "script": str(path),
            "status": "FAIL",
            "reason": str(exc),
            "duration_seconds": round(time.time() - started, 3),
            "cmd": cmd,
        }


def run_single_cycle(db_path: str, symbol: str, dry_run: bool) -> Dict[str, object]:
    started = time.time()
    steps = default_steps()
    step_results = [run_step(step, db_path, symbol, dry_run) for step in steps]
    statuses = [str(r.get("status")) for r in step_results]
    fail_count = sum(1 for s in statuses if s == "FAIL")
    ok_like = {"OK", "SKIPPED", "DRY_RUN", "ACCEPTED_RETURNCODE_WITH_OUTPUT"}
    status = "OK" if all(s in ok_like for s in statuses) else "PARTIAL"
    if fail_count == len(statuses):
        status = "FAIL"
    return {
        "timestamp": utc_now_iso(),
        "symbol": symbol,
        "status": status,
        "duration_seconds": round(time.time() - started, 3),
        "steps": step_results,
    }


def run_cycle_multi_symbol(db_path: str, symbols: Sequence[str], dry_run: bool) -> Dict[str, object]:
    started = time.time()
    results: Dict[str, object] = {}
    for symbol in symbols:
        try:
            results[symbol] = run_single_cycle(db_path, symbol, dry_run)
        except Exception as exc:
            results[symbol] = {
                "timestamp": utc_now_iso(),
                "symbol": symbol,
                "status": "FAIL",
                "error": str(exc),
            }

    statuses = [str(v.get("status")) for v in results.values() if isinstance(v, dict)]
    overall = "OK" if statuses and all(s == "OK" for s in statuses) else "PARTIAL"
    if statuses and all(s == "FAIL" for s in statuses):
        overall = "FAIL"
    return {
        "timestamp": utc_now_iso(),
        "db_path": db_path,
        "symbols": list(symbols),
        "overall_status": overall,
        "duration_seconds": round(time.time() - started, 3),
        "symbol_results": results,
        "method": "powerflow_cycle_multi_symbol_non_blocking",
    }


def write_report(path: str, payload: Dict[str, object]) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def main() -> int:
    parser = argparse.ArgumentParser(description="PowerFlow cycle orchestrator with multi-symbol support")
    parser.add_argument("--db", default="Core/powerflow.db", help="Path to powerflow.db")
    parser.add_argument("--symbol", default=DEFAULT_SYMBOL, help="Backward-compatible single symbol")
    parser.add_argument("--symbols", default=None, help="Comma-separated symbols; overrides --symbol")
    parser.add_argument("--sequential", action="store_true", help="Explicit sequential mode; default safe mode")
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    raw_symbols = args.symbols if args.symbols else args.symbol
    symbols = parse_symbols(raw_symbols, default=DEFAULT_SYMBOL)
    payload = run_cycle_multi_symbol(args.db, symbols, args.dry_run)
    write_report(args.output, payload)
    print(json.dumps(payload, indent=2 if args.pretty else None, ensure_ascii=False))
    return 0 if payload.get("overall_status") in {"OK", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
