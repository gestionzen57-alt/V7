#!/usr/bin/env python3
"""
PowerFlow V7.3 turbo scheduler wrapper.

Purpose:
- Run the existing multi-symbol PowerFlow scheduler once.
- Then refresh the auxiliary surface layers:
  data health, ontology, signal adaptive, price schema, topdown reader.

Doctrine:
- Read-only analytical layers after the scheduler core.
- No trade decision, no BUY/SELL output.
- M1 is qualified, never censored.
- V7.3 topdown stack: HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Sequence


TAIL_LIMIT = 12000


@dataclass
class StepResult:
    label: str
    returncode: int
    elapsed_seconds: float
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.returncode == 0


def _now_seconds() -> float:
    return time.perf_counter()


def _emit_tail(label: str, stream_name: str, text: str, limit: int = TAIL_LIMIT) -> None:
    if not text:
        return
    clean = text.strip()
    if not clean:
        return
    if len(clean) > limit:
        clean = "[...TRUNCATED_TO_TAIL...]\n" + clean[-limit:]
    print(f"{stream_name} {label}: {clean}")


def run_step(label: str, command: Sequence[str], cwd: Path, required: bool = True) -> StepResult:
    started = _now_seconds()
    printable = " ".join(str(part) for part in command)
    print(f"> {printable}")

    proc = subprocess.run(
        list(command),
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    elapsed = round(_now_seconds() - started, 3)
    result = StepResult(
        label=label,
        returncode=proc.returncode,
        elapsed_seconds=elapsed,
        stdout=proc.stdout or "",
        stderr=proc.stderr or "",
    )

    status = "OK" if result.ok else "FAIL"
    print(f"STEP_END {label} status={status} returncode={result.returncode} elapsed={elapsed}s")
    _emit_tail(label, "STDOUT", result.stdout)
    _emit_tail(label, "STDERR", result.stderr)

    if required and not result.ok:
        raise RuntimeError(f"required step failed: {label} returncode={result.returncode}")

    return result


def parse_symbols(raw: str) -> str:
    symbols = [part.strip().upper() for part in raw.split(",") if part.strip()]
    if not symbols:
        raise ValueError("no symbols provided")
    return ",".join(symbols)


def build_steps(py: str, symbols: str) -> List[tuple[str, List[str]]]:
    return [
        (
            "scheduler_core",
            [py, "scheduler_powerflow.py", "--once", "--symbols", symbols],
        ),
        (
            "data_health_monitor",
            [
                py,
                "run_data_health_monitor_once.py",
                "--db",
                "powerflow.db",
                "--symbols",
                symbols,
                "--output",
                "output/data_health_monitor.json",
            ],
        ),
        (
            "data_health_normalize",
            [
                py,
                "dashboard_normalize_data_health.py",
                "--input",
                "output/data_health_monitor.json",
                "--output",
                "output/dashboard_surface/data_health.json",
            ],
        ),
        (
            "flow_ontology_cycle",
            [py, "run_flow_ontology_cycle_once.py", "--symbols", symbols],
        ),
        (
            "signal_adaptive_all",
            [
                py,
                "run_signal_adaptive_all_once.py",
                "--symbols",
                symbols,
                "--data-health",
                "output/data_health_monitor.json",
            ],
        ),
        (
            "signal_adaptive_normalize",
            [
                py,
                "dashboard_normalize_signal_adaptive.py",
                "--input",
                "output/dashboard_surface/signal_adaptive_profiles.json",
                "--output",
                "output/dashboard_surface/signal_adaptive.json",
            ],
        ),
        (
            "price_schema_probe",
            [py, "pf_price_schema_probe.py"],
        ),
        (
            "topdown_market_reader_all",
            [py, "run_topdown_market_reader_all_once.py", "--symbols", symbols],
        ),
        (
            "topdown_reader_normalize",
            [
                py,
                "dashboard_normalize_topdown_reader.py",
                "--input",
                "output/dashboard_surface/topdown_market_reader.json",
                "--output",
                "output/dashboard_surface/topdown_reader.json",
            ],
        ),
    ]


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="PowerFlow V7.3 turbo wrapper")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--continue-on-error", action="store_true")
    args = parser.parse_args(list(argv) if argv is not None else None)

    core = Path(__file__).resolve().parent
    symbols = parse_symbols(args.symbols)
    py = sys.executable

    started = _now_seconds()
    results: List[StepResult] = []
    errors: List[str] = []

    print(f"TURBO_V73_CYCLE_START | symbols={symbols} | core={core}")

    for label, command in build_steps(py, symbols):
        try:
            results.append(run_step(label, command, cwd=core, required=not args.continue_on_error))
        except Exception as exc:
            errors.append(f"{label}:{exc}")
            print(f"STEP_EXCEPTION {label}: {exc}")
            if not args.continue_on_error:
                elapsed = round(_now_seconds() - started, 3)
                print(
                    "TURBO_V73_CYCLE_FAIL | "
                    f"symbols={symbols} | completed_steps={len(results)} | "
                    f"errors={len(errors)} | duration_seconds={elapsed}"
                )
                return 1

    failed = [result.label for result in results if not result.ok]
    errors.extend(failed)
    elapsed = round(_now_seconds() - started, 3)

    if errors:
        print(
            "TURBO_V73_CYCLE_FAIL | "
            f"symbols={symbols} | steps={len(results)} | errors={errors} | "
            f"duration_seconds={elapsed}"
        )
        return 1


    run_step("gbpusd_live_decision", [
        sys.executable, "pf_gbpusd_live_decision_once.py",
    ], core)
    run_step("cockpit_live_status", [
        sys.executable, "pf_cockpit_live_status_once.py",
    ], core)
    run_step("powerflow_live_brief", [
        sys.executable, "pf_powerflow_live_brief_once.py",
    ], core)
    run_step("live_brief_normalize", [
        sys.executable, "dashboard_normalize_live_brief.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/live_brief_dashboard.json",
    ], core)

    run_step("b6_live_fusion", [
        sys.executable, "pf_b6_live_fusion_once.py",
    ], core)
    run_step("b6_live_fusion_normalize", [
        sys.executable, "dashboard_normalize_b6_live_fusion.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/b6_live_fusion_dashboard.json",
    ], core)
    run_step("multiread_synthesis", [
        sys.executable, "pf_powerflow_multiread_synthesis_once.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/powerflow_multiread_synthesis.json",
    ], core)
    run_step("multiread_synthesis_normalize", [
        sys.executable, "dashboard_normalize_multiread_synthesis.py",
        "--input", "output/dashboard_surface/powerflow_multiread_synthesis.json",
        "--output", "output/dashboard_surface/multiread_synthesis_dashboard.json",
    ], core)

    run_step("time_profile_ltf", [
        sys.executable, "run_ltf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profile_mtf", [
        sys.executable, "run_mtf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profile_htf", [
        sys.executable, "run_htf_profile_once.py",
        "--symbol", "GBPUSD",
    ], core)
    run_step("time_profiles_normalize", [
        sys.executable, "dashboard_normalize_time_profiles.py",
        "--symbol", "GBPUSD",
        "--output", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)

    run_step("trader_cockpit", [
        sys.executable, "pf_trader_cockpit_once.py",
        "--symbols", symbols,
        "--trade-symbol", "GBPUSD",
        "--output", "output/dashboard_surface/trader_cockpit.json",
        "--txt", "output/dashboard_surface/trader_cockpit.txt",
    ], core)
    run_step("trader_cockpit_time_profiles_enrich", [
        sys.executable, "pf_trader_cockpit_time_profiles_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--time-profiles", "output/dashboard_surface/time_profiles_dashboard.json",
    ], core)

    run_step("b8_cross_surface", [
        sys.executable, "pf_b8_cross_surface_once.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/b8_cross_surface.json",
        "--txt", "output/dashboard_surface/b8_cross_surface.txt",
    ], core)

    run_step("trader_cockpit_b8_enrich", [
        sys.executable, "pf_trader_cockpit_b8_enrich.py",
        "--cockpit-json", "output/dashboard_surface/trader_cockpit.json",
        "--cockpit-txt", "output/dashboard_surface/trader_cockpit.txt",
        "--b8", "output/dashboard_surface/b8_cross_surface.json",
    ], core)

    run_step("trader_journal_j1", [
        sys.executable, "pf_trader_journal_j1.py",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/trader_journal_j1.json",
        "--md", "output/dashboard_surface/trader_journal_j1.md",
    ], core)

    print(
        "TURBO_V73_CYCLE_OK | "
        f"symbols={symbols} | steps={len(results)} | duration_seconds={elapsed} | "
        "layers=data_health,ontology,signal_adaptive,price_schema,topdown_reader,time_profiles,live_brief,b6,multiread,trader_cockpit,b8,daily_journal"
    )


    return 0


if __name__ == "__main__":
    raise SystemExit(main())

    run_step("daily_journal_all", [
        sys.executable, "run_daily_journal_all_once.py",
        "--db", "powerflow.db",
        "--symbols", symbols,
        "--output", "output/dashboard_surface/daily_journal.json",
    ], core)
    run_step("daily_journal_normalize", [
        sys.executable, "dashboard_normalize_daily_journal.py",
        "--input", "output/dashboard_surface/daily_journal.json",
        "--output", "output/dashboard_surface/daily_journal_dashboard.json",
    ], core)
