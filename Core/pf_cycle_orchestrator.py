#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pf_cycle_orchestrator.py
PowerFlow V7.2 - Cycle Orchestrator 9 Steps, runner-driven.

- no capture_bridge.py modification
- no manual write to powerflow.db
- runs existing run_*.py scripts via subprocess
- graceful degradation on non-critical step failure
- writes output/cycle_report.json and output/cycle_runtime_status.json

Version: 1.0.1-p0
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


ORCHESTRATOR_VERSION = "1.0.1-p0"
CYCLE_TARGET_SECONDS = 44
CYCLE_MAX_SECONDS = 60

DEFAULT_SYMBOLS = ("GBPUSD",)
DEFAULT_TFS = "1,5,15,30,60,240"

CORE_DIR = Path(__file__).resolve().parent
REPO_ROOT = CORE_DIR.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "output"


@dataclass(frozen=True)
class StepSpec:
    order: int
    step_name: str
    brick: str
    script: str
    args: tuple[str, ...] = ()
    timeout_seconds: int = 60
    optional: bool = True
    per_symbol: bool = False
    per_tf: bool = False
    accept_rc2_if_output_exists: bool = False
    expected_output: Optional[str] = None


@dataclass
class StepResult:
    order: int
    step_name: str
    brick: str
    script: str
    symbol: Optional[str]
    timeframe: Optional[int]
    status: str
    ok: bool
    returncode: Optional[int]
    duration_seconds: float
    cmd: list[str]
    expected_output: Optional[str] = None
    stdout_tail: str = ""
    stderr_tail: str = ""
    error: Optional[str] = None
    technical_risks: list[str] = field(default_factory=list)


@dataclass
class CycleReport:
    cycle_id: str
    started_at_utc: str
    ended_at_utc: str
    total_duration_seconds: float
    cycle_status: str
    orchestrator_version: str
    db_path: str
    symbols: list[str]
    tfs: list[int]
    steps_total: int
    steps_ok: int
    steps_failed: int
    steps_skipped: int
    technical_risks: list[str]
    steps: list[StepResult]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def tail(text: str, max_chars: int = 2200) -> str:
    if not text:
        return ""
    return text[-max_chars:]


def normalize_symbols(raw: str | Iterable[str] | None) -> list[str]:
    if raw is None:
        return list(DEFAULT_SYMBOLS)
    if isinstance(raw, str):
        parts = raw.split(",")
    else:
        parts = list(raw)
    out: list[str] = []
    for p in parts:
        s = str(p).strip().rstrip(".").upper()
        if s:
            out.append(s)
    return out or list(DEFAULT_SYMBOLS)


def parse_tfs(raw: str | Iterable[int] | None) -> list[int]:
    if raw is None:
        raw = DEFAULT_TFS
    if isinstance(raw, str):
        parts = raw.split(",")
    else:
        parts = raw
    out: list[int] = []
    for p in parts:
        try:
            v = int(str(p).strip())
            if v > 0:
                out.append(v)
        except ValueError:
            pass
    return out or [1, 5, 15, 30, 60, 240]


def script_path(script: str) -> Path:
    p = Path(script)
    if p.is_absolute():
        return p
    c = CORE_DIR / script
    if c.exists():
        return c
    return REPO_ROOT / script


def rel_output(path: str) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return REPO_ROOT / p


def render_token(value: str, symbol: Optional[str], tf: Optional[int], db_path: str, since: str, tfs: str) -> str:
    rendered = value.replace("{db}", db_path).replace("{since}", since).replace("{tfs}", tfs)
    if symbol is not None:
        rendered = rendered.replace("{symbol}", symbol)
    if tf is not None:
        rendered = rendered.replace("{tf}", str(tf))
    return rendered


def build_steps() -> list[StepSpec]:
    return [
        StepSpec(1, "STEP_1A_REGIME_LEGACY", "B1_LEGACY", "run_regime_engine_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--pretty", "--out", "output/regime_legacy_{symbol}.json"),
                 60, True, True, False, False, "output/regime_legacy_{symbol}.json"),
        StepSpec(1, "STEP_1B_REGIME_HMM", "B1_HMM", "run_hmm_regime_engine_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--pretty", "--out", "output/regime_hmm_{symbol}.json"),
                 60, True, True, False, False, "output/regime_hmm_{symbol}.json"),
        StepSpec(2, "STEP_2_KINEMATICS", "B3_KALMAN", "run_force_kinematics_orchestrator_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--pretty", "--output", "output/kinematics_{symbol}.json"),
                 60, True, True, False, False, "output/kinematics_{symbol}.json"),
        StepSpec(3, "STEP_3A_TEMPORAL_DENSITY_ROLLING", "B4_ROLLING", "run_temporal_density_once.py",
                 ("--db", "{db}", "--tfs", "{tfs}", "--summary", "--pretty", "--out", "output/temporal_density_state.json"),
                 60, True, False, False, False, "output/temporal_density_state.json"),
        StepSpec(3, "STEP_3B_TEMPORAL_DENSITY_WAVELET", "B4_WAVELET", "run_wavelet_density_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--tf", "{tf}", "--window", "64", "--pretty", "--output", "output/wavelet_density_{symbol}_TF{tf}.json"),
                 60, True, True, True, False, "output/wavelet_density_{symbol}_TF{tf}.json"),
        StepSpec(4, "STEP_4_SPEARMAN_GRAVITY", "B5_SPEARMAN", "run_spearman_gravity_once.py",
                 ("--db", "{db}", "--tfs", "{tfs}", "--summary", "--pretty", "--out", "output/spearman_gravity_state.json"),
                 60, True, False, False, False, "output/spearman_gravity_state.json"),
        StepSpec(5, "STEP_5_MEMORY_PATTERNS", "B6_MEMORY", "run_memory_engine_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--pretty", "--output", "output/memory_patterns_{symbol}.json"),
                 90, True, True, False, False, "output/memory_patterns_{symbol}.json"),
        StepSpec(6, "STEP_6_FRACTAL_RESONANCE", "B7_RESONANCE", "run_fractal_resonance_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--tfs", "{tfs}", "--table", "force_snapshots_v2", "--limit", "800", "--window", "60", "--max-lag", "5", "--force-mode", "base", "--pretty", "--output", "output/fractal_resonance_{symbol}.json"),
                 90, True, True, False, False, "output/fractal_resonance_{symbol}.json"),
        StepSpec(7, "STEP_7_VOLATILITY_TEXTURE", "B7_TEXTURE", "run_volatility_texture_once.py",
                 ("--db", "{db}", "--symbol", "{symbol}", "--timeframe", "{tf}", "--recent-bars", "120", "--pretty", "--output", "output/volatility_texture_{symbol}_TF{tf}.json"),
                 60, True, True, True, False, "output/volatility_texture_{symbol}_TF{tf}.json"),
        StepSpec(8, "STEP_8_ALERT_ENTROPY", "GUARD_ENTROPY", "run_entropy_engine_once.py",
                 ("--pretty", "--output", "output/alert_entropy_state.json"),
                 60, True, False, False, False, "output/alert_entropy_state.json"),
        StepSpec(9, "STEP_9_DASHBOARD_REFRESH", "DASHBOARD_SYNC", "run_powerflow_dashboard_refresh_once.py",
                 ("--pretty", "--skip-cockpit"),
                 120, True, False, False, False, "output/dashboard_data.json"),
    ]


def invocations(step: StepSpec, symbols: list[str], tfs: list[int]) -> list[tuple[Optional[str], Optional[int]]]:
    if step.per_symbol and step.per_tf:
        return [(s, tf) for s in symbols for tf in tfs]
    if step.per_symbol:
        return [(s, None) for s in symbols]
    if step.per_tf:
        return [(None, tf) for tf in tfs]
    return [(None, None)]


def run_step(step: StepSpec, symbol: Optional[str], tf: Optional[int], db_path: str, since: str, tfs_str: str, dry_run: bool) -> StepResult:
    sp = script_path(step.script)
    expected = None
    if step.expected_output:
        expected = str(rel_output(render_token(step.expected_output, symbol, tf, db_path, since, tfs_str)))

    if not sp.exists():
        return StepResult(step.order, step.step_name, step.brick, step.script, symbol, tf, "SKIPPED", True, None, 0.0, [], expected, error=f"missing optional script: {step.script}", technical_risks=["MISSING_OPTIONAL_RUNNER"])

    args = [render_token(a, symbol, tf, db_path, since, tfs_str) for a in step.args]
    cmd = [sys.executable, str(sp)] + args

    if dry_run:
        return StepResult(step.order, step.step_name, step.brick, step.script, symbol, tf, "DRY_RUN", True, 0, 0.0, cmd, expected)

    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"

    t0 = time.perf_counter()
    try:
        proc = subprocess.run(cmd, cwd=str(CORE_DIR), capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=step.timeout_seconds, env=env)
        elapsed = round(time.perf_counter() - t0, 3)
        output_exists = bool(expected and Path(expected).exists())
        ok = proc.returncode == 0 or (step.accept_rc2_if_output_exists and proc.returncode == 2 and output_exists)
        risks = []
        if proc.returncode == 2 and output_exists:
            risks.append("RETURN_CODE_2_ACCEPTED_WITH_OUTPUT")
        if not ok:
            risks.append("STEP_RUNTIME_FAIL")
        return StepResult(step.order, step.step_name, step.brick, step.script, symbol, tf, "OK" if ok else "FAIL", ok, proc.returncode, elapsed, cmd, expected, tail(proc.stdout), tail(proc.stderr), None if ok else (tail(proc.stderr) or tail(proc.stdout) or f"returncode={proc.returncode}"), risks)
    except subprocess.TimeoutExpired as exc:
        elapsed = round(time.perf_counter() - t0, 3)
        return StepResult(step.order, step.step_name, step.brick, step.script, symbol, tf, "FAIL", False, None, elapsed, cmd, expected, tail(exc.stdout or ""), tail(exc.stderr or ""), f"TIMEOUT after {step.timeout_seconds}s", ["ORCHESTRATOR_TIMEOUT"])
    except Exception as exc:
        elapsed = round(time.perf_counter() - t0, 3)
        return StepResult(step.order, step.step_name, step.brick, step.script, symbol, tf, "FAIL", False, None, elapsed, cmd, expected, error=f"{type(exc).__name__}: {exc}", technical_risks=["STEP_EXCEPTION"])


def write_json(path: Path, data: object, pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2 if pretty else None), encoding="utf-8")


def result_to_dict(r: StepResult) -> dict:
    d = asdict(r)
    d["cmd_display"] = " ".join(shlex.quote(str(x)) for x in r.cmd) if r.cmd else ""
    return d


def run_cycle(cycle_id: str | int | None = None, symbols: list[str] | None = None, db_path: str = "powerflow.db", tfs: list[int] | None = None, since: str | None = None, output_dir: str | Path = DEFAULT_OUTPUT_DIR, dry_run: bool = False, pretty: bool = True) -> CycleReport:
    symbols = normalize_symbols(symbols)
    tfs = parse_tfs(tfs)
    tfs_str = ",".join(str(x) for x in tfs)
    since = since or datetime.now(timezone.utc).date().isoformat()
    cycle_id = str(cycle_id or uuid.uuid4())

    outdir = Path(output_dir)
    if not outdir.is_absolute():
        outdir = REPO_ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)

    started = utc_now()
    t0 = time.perf_counter()

    results: list[StepResult] = []
    for step in build_steps():
        for symbol, tf in invocations(step, symbols, tfs):
            r = run_step(step, symbol, tf, db_path, since, tfs_str, dry_run)
            results.append(r)
            label = r.step_name + (f" {r.symbol}" if r.symbol else "") + (f" TF{r.timeframe}" if r.timeframe else "")
            print(f"[{r.status}] {label} ({r.duration_seconds:.2f}s)")

    elapsed = round(time.perf_counter() - t0, 3)
    ended = utc_now()

    failed = [r for r in results if r.status == "FAIL"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    ok = [r for r in results if r.ok and r.status not in {"SKIPPED"}]

    if failed and ok:
        status = "PARTIAL"
    elif failed and not ok:
        status = "FAILED"
    else:
        status = "COMPLETE"

    risks: list[str] = []
    if elapsed > CYCLE_MAX_SECONDS:
        risks.append("CYCLE_DURATION_OVER_MAX")
    elif elapsed > CYCLE_TARGET_SECONDS:
        risks.append("CYCLE_DURATION_OVER_TARGET")
    for r in results:
        for risk in r.technical_risks:
            if risk not in risks:
                risks.append(risk)

    report = CycleReport(str(cycle_id), started, ended, elapsed, status, ORCHESTRATOR_VERSION, db_path, symbols, tfs, len(results), len(ok), len(failed), len(skipped), risks, results)

    report_dict = asdict(report)
    report_dict["steps"] = [result_to_dict(r) for r in results]
    write_json(outdir / "cycle_report.json", report_dict, pretty)
    write_json(outdir / "cycle_runtime_status.json", {"generated_at_utc": ended, "cycle_id": report.cycle_id, "cycle_status": report.cycle_status, "orchestrator_version": report.orchestrator_version, "duration_seconds": report.total_duration_seconds, "steps_ok": report.steps_ok, "steps_failed": report.steps_failed, "steps_skipped": report.steps_skipped, "technical_risks": report.technical_risks}, pretty)
    return report


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.2 - Cycle Orchestrator 9 steps")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", "--symbol", dest="symbols", default="GBPUSD")
    parser.add_argument("--tfs", default=DEFAULT_TFS)
    parser.add_argument("--since", default=None)
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args(argv)

    report = run_cycle(symbols=normalize_symbols(args.symbols), db_path=args.db, tfs=parse_tfs(args.tfs), since=args.since, output_dir=args.output_dir, dry_run=args.dry_run, pretty=True)
    print(json.dumps({"cycle_status": report.cycle_status, "duration_seconds": report.total_duration_seconds, "steps_ok": report.steps_ok, "steps_failed": report.steps_failed, "steps_skipped": report.steps_skipped, "report": str(Path(args.output_dir) / "cycle_report.json")}, ensure_ascii=False, indent=2))
    return 0 if report.cycle_status in {"COMPLETE", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

