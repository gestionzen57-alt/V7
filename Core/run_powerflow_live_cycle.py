from __future__ import annotations

import os
import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_DB = Path("powerflow.db")
DEFAULT_DASHBOARD = Path("dashboard_data.json")
DEFAULT_RUNTIME_STATUS = Path("output") / "runtime_status.json"
DEFAULT_PIPELINE_TRACE = Path("output") / "pipeline_trace.json"
DEFAULT_TRADER_ALERT = Path("output") / "trader_alert_state.json"

DEFAULT_REFRESH_RUNNER = Path("run_powerflow_dashboard_refresh_once.py")
DEFAULT_TRADER_ALERT_ENGINE = Path("run_trader_alert_state_once.py")
DEFAULT_TELEGRAM_ENGINE = Path("telegram_trader_alert_v01.py")

DEFAULT_BEHAVIORAL = Path("output") / "behavioral_alert_queue.json"
DEFAULT_COCKPIT = Path("output") / "cockpit_agentic_state_v01.json"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(path: Path, data: dict[str, Any], pretty: bool = True) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2 if pretty else None),
        encoding="utf-8",
    )


def tail_text(text: str, max_chars: int = 2500) -> str:
    if not text:
        return ""
    return text[-max_chars:]


def run_subprocess(cmd: list[str]) -> dict[str, Any]:
    t0 = time.perf_counter()

    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )

    elapsed = round(time.perf_counter() - t0, 3)

    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "elapsed_seconds": elapsed,
        "cmd": cmd,
        "stdout_tail": tail_text(proc.stdout),
        "stderr_tail": tail_text(proc.stderr),
    }


def extract_behavioral_summary(dashboard: dict[str, Any]) -> dict[str, Any]:
    summary = dashboard.get("behavioral_summary") or {}
    flow = dashboard.get("behavioral_flow") or {}

    return {
        "behavioral_count": summary.get("behavioral_count", 0),
        "degraded_count": summary.get("degraded_count", 0),
        "top_alert": summary.get("top_alert") or flow.get("top_alert"),
        "top_level": summary.get("top_level") or flow.get("level"),
        "has_hot": bool(summary.get("has_hot_behavioral", False)),
        "behavioral_flow_status": flow.get("status"),
    }


def extract_trader_alert_summary(alert_state: dict[str, Any]) -> dict[str, Any]:
    """
    Extraction défensive : accepte plusieurs formes possibles de trader_alert_state.
    """
    main = (
        alert_state.get("main_alert")
        or alert_state.get("primary_alert")
        or alert_state.get("active_alert")
        or {}
    )

    alerts = alert_state.get("alerts")
    if not main and isinstance(alerts, list) and alerts:
        first = alerts[0]
        if isinstance(first, dict):
            main = first

    level = (
        main.get("level")
        or alert_state.get("level")
        or alert_state.get("top_level")
    )

    title = (
        main.get("title")
        or main.get("name")
        or alert_state.get("title")
        or alert_state.get("top_alert")
    )

    freshness = (
        main.get("freshness")
        or main.get("freshness_state")
        or alert_state.get("freshness")
        or alert_state.get("freshness_state")
    )

    age_seconds = (
        main.get("age_seconds")
        or alert_state.get("age_seconds")
    )

    message = (
        main.get("message")
        or alert_state.get("message")
        or ""
    )

    return {
        "trader_alert_ready": bool(main or title or level),
        "trader_alert_level": level,
        "trader_alert_title": title,
        "trader_alert_freshness": freshness,
        "trader_alert_age_seconds": age_seconds,
        "trader_alert_message": message,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="PowerFlow V6.1 — Live Cycle Orchestrator V0.3"
    )
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--symbol", default="GBPUSD")
    parser.add_argument("--recent-minutes", type=int, default=180)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--pretty", action="store_true")
    parser.add_argument("--summary", action="store_true")
    parser.add_argument("--skip-trader-alert", action="store_true")
    parser.add_argument(
        "--telegram-mode",
        choices=["OFF", "HOT_ONLY", "SCALPING", "SYSTEM_ONLY"],
        default="OFF",
        help="Mode Telegram Trader Alert. Default: OFF",
    )
    parser.add_argument(
        "--telegram-dry-run",
        action="store_true",
        help="Build Telegram message but do not send.",
    )

    args = parser.parse_args()

    generated_at = utc_now()
    t_global = time.perf_counter()

    db_path = Path(args.db)
    warnings: list[str] = []
    steps: dict[str, Any] = {}

    if args.summary:
        print("=" * 55)
        print("  POWERFLOW V6.1 — LIVE CYCLE ORCHESTRATOR V0.3")
        print(f"  symbol={args.symbol} | db={db_path}")
        print(f"  {generated_at}")
        print("=" * 55)

    # ------------------------------------------------------------
    # 1. CHECK DB
    # ------------------------------------------------------------
    if args.summary:
        print("\n[1/6] CHECK DB")

    db_ok = db_path.exists() and db_path.stat().st_size > 0
    db_detail = "MISSING"
    if db_path.exists():
        db_detail = f"OK ({db_path.stat().st_size:,} bytes)" if db_ok else "EMPTY"

    steps["check_db"] = {
        "ok": db_ok,
        "detail": db_detail,
    }

    if args.summary:
        print(f"  {'OK' if db_ok else 'FAIL'}  {db_detail}")

    if not db_ok:
        status = {
            "generated_at": generated_at,
            "symbol": args.symbol,
            "status": "FAIL",
            "db_ok": False,
            "refresh_ok": False,
            "dashboard_ready": False,
            "trader_alert_ready": False,
            "warnings": ["powerflow.db missing or empty"],
            "elapsed_seconds": round(time.perf_counter() - t_global, 3),
        }
        trace = {
            "generated_at": utc_now(),
            "symbol": args.symbol,
            "steps": steps,
        }
        write_json(DEFAULT_RUNTIME_STATUS, status, pretty=args.pretty)
        write_json(DEFAULT_PIPELINE_TRACE, trace, pretty=args.pretty)
        return 1

    # ------------------------------------------------------------
    # 2. RUN DASHBOARD REFRESH
    # ------------------------------------------------------------
    if args.summary:
        print("\n[2/6] RUN REFRESH  (run_powerflow_dashboard_refresh_once.py)")

    refresh_cmd = [
        sys.executable,
        str(DEFAULT_REFRESH_RUNNER),
        "--skip-cockpit",
        "--refresh-cockpit-from-queue",
    ]
    if args.pretty:
        refresh_cmd.append("--pretty")
    if args.summary:
        refresh_cmd.append("--summary")

    refresh_result = run_subprocess(refresh_cmd)
    steps["run_refresh"] = refresh_result

    if args.summary:
        print(
            f"  {'OK' if refresh_result['ok'] else 'FAIL'}  "
            f"elapsed={refresh_result['elapsed_seconds']}s"
        )

    if not refresh_result["ok"]:
        warnings.append("dashboard refresh failed")

    # ------------------------------------------------------------
    # 3. CHECK DASHBOARD
    # ------------------------------------------------------------
    if args.summary:
        print("\n[3/6] CHECK DASHBOARD  (dashboard_data.json)")

    dashboard = load_json(DEFAULT_DASHBOARD)
    behavioral_flow = dashboard.get("behavioral_flow") or {}
    dashboard_ready = bool(behavioral_flow)

    behavioral_summary = extract_behavioral_summary(dashboard)

    steps["check_dashboard"] = {
        "ok": dashboard_ready,
        "behavioral_flow_present": dashboard_ready,
        "warnings": [],
    }

    if not dashboard_ready:
        warnings.append("dashboard_data.json missing behavioral_flow")

    if args.summary:
        print(f"  {'OK' if dashboard_ready else 'WARN'}  behavioral_flow={'PRESENT' if dashboard_ready else 'ABSENT'}")

    # ------------------------------------------------------------
    # 4. RUN TRADER ALERT STATE
    # ------------------------------------------------------------
    trader_alert_ready = False
    trader_alert_summary: dict[str, Any] = {}

    if args.summary:
        print("\n[4/6] RUN TRADER ALERT  (run_trader_alert_state_once.py)")

    if args.skip_trader_alert:
        warnings.append("trader alert skipped")
        steps["run_trader_alert"] = {
            "ok": False,
            "skipped": True,
        }
        if args.summary:
            print("  SKIP  trader alert skipped")
    elif not DEFAULT_TRADER_ALERT_ENGINE.exists():
        warnings.append("pf_trader_alert_state.py missing")
        steps["run_trader_alert"] = {
            "ok": False,
            "missing": str(DEFAULT_TRADER_ALERT_ENGINE),
        }
        if args.summary:
            print("  WARN  pf_trader_alert_state.py missing")
    else:
        trader_cmd = [
            sys.executable,
            str(DEFAULT_TRADER_ALERT_ENGINE),
        ]

        if args.pretty:
            trader_cmd.append("--pretty")

        if args.summary:
            trader_cmd.append("--summary")

        trader_result = run_subprocess(trader_cmd)
        steps["run_trader_alert"] = trader_result

        if args.summary:
            print(
                f"  {'OK' if trader_result['ok'] else 'WARN'}  "
                f"elapsed={trader_result['elapsed_seconds']}s"
            )

        if not trader_result["ok"]:
            warnings.append("trader alert generation failed")

        trader_alert_state = load_json(DEFAULT_TRADER_ALERT)
        trader_alert_summary = extract_trader_alert_summary(trader_alert_state)
        trader_alert_ready = bool(trader_alert_summary.get("trader_alert_ready"))

        if not trader_alert_state:
            warnings.append("trader_alert_state.json missing or empty")

    # ------------------------------------------------------------
    # 5. RUN TELEGRAM TRADER ALERT
    # ------------------------------------------------------------
    telegram_summary: dict[str, Any] = {}

    if args.summary:
        print("\n[5/6] RUN TELEGRAM  (telegram_trader_alert_v01.py)")

    if args.telegram_mode == "OFF":
        steps["run_telegram"] = {
            "ok": True,
            "skipped": True,
            "mode": "OFF",
        }
        telegram_summary = {
            "telegram_mode": "OFF",
            "telegram_ok": True,
            "telegram_sent": False,
            "telegram_verdict": "OFF_SILENCE",
            "telegram_dry_run": False,
        }
        if args.summary:
            print("  SKIP  telegram mode OFF")

    elif not DEFAULT_TELEGRAM_ENGINE.exists():
        warnings.append("telegram_trader_alert_v01.py missing")
        steps["run_telegram"] = {
            "ok": False,
            "missing": str(DEFAULT_TELEGRAM_ENGINE),
            "mode": args.telegram_mode,
        }
        telegram_summary = {
            "telegram_mode": args.telegram_mode,
            "telegram_ok": False,
            "telegram_sent": False,
            "telegram_verdict": "TELEGRAM_SCRIPT_MISSING",
            "telegram_dry_run": bool(args.telegram_dry_run),
        }
        if args.summary:
            print("  WARN  telegram_trader_alert_v01.py missing")

    else:
        telegram_cmd = [
            sys.executable,
            str(DEFAULT_TELEGRAM_ENGINE),
            "--mode",
            args.telegram_mode,
            "--trader",
            str(DEFAULT_TRADER_ALERT),
            "--runtime",
            str(DEFAULT_RUNTIME_STATUS),
        ]

        if args.telegram_dry_run:
            telegram_cmd.append("--dry-run")

        if args.summary:
            telegram_cmd.append("--summary")

        telegram_result = run_subprocess(telegram_cmd)
        steps["run_telegram"] = telegram_result

        stdout_tail = telegram_result.get("stdout_tail", "") or ""
        telegram_ok = bool(telegram_result.get("ok"))

        telegram_sent = (
            "TELEGRAM_OK: True" in stdout_tail
            and "SHOULD_SEND: True" in stdout_tail
            and "DRY_RUN: False" in stdout_tail
        )

        verdict = "UNKNOWN"
        for line in stdout_tail.splitlines():
            if line.startswith("VERDICT:"):
                verdict = line.split(":", 1)[1].strip()
                break

        telegram_summary = {
            "telegram_mode": args.telegram_mode,
            "telegram_ok": telegram_ok,
            "telegram_sent": telegram_sent,
            "telegram_verdict": verdict,
            "telegram_dry_run": bool(args.telegram_dry_run),
        }

        if not telegram_ok:
            warnings.append("telegram trader alert failed")

        if args.summary:
            print(
                f"  {'OK' if telegram_ok else 'WARN'}  "
                f"mode={args.telegram_mode} verdict={verdict}"
            )

    # ------------------------------------------------------------
    # 6. WRITE OUTPUTS
    # ------------------------------------------------------------
    if args.summary:
        print("\n[6/6] WRITE OUTPUTS")

    status_value = "OK"
    if warnings:
        status_value = "WARN"
    if not refresh_result["ok"] or not dashboard_ready:
        status_value = "FAIL"

    elapsed_total = round(time.perf_counter() - t_global, 3)

    runtime_status: dict[str, Any] = {
        "generated_at": utc_now(),
        "symbol": args.symbol,
        "status": status_value,
        "db_ok": db_ok,
        "refresh_ok": bool(refresh_result["ok"]),
        "dashboard_ready": dashboard_ready,
        "behavioral_count": behavioral_summary.get("behavioral_count", 0),
        "degraded_count": behavioral_summary.get("degraded_count", 0),
        "top_alert": behavioral_summary.get("top_alert"),
        "top_level": behavioral_summary.get("top_level"),
        "has_hot": behavioral_summary.get("has_hot", False),
        "warnings": warnings,
        "elapsed_seconds": elapsed_total,
    }

    runtime_status.update(trader_alert_summary)
    runtime_status.update(telegram_summary)
    if "trader_alert_ready" not in runtime_status:
        runtime_status["trader_alert_ready"] = trader_alert_ready

    pipeline_trace: dict[str, Any] = {
        "generated_at": utc_now(),
        "symbol": args.symbol,
        "recent_minutes": args.recent_minutes,
        "steps": steps,
        "behavioral": behavioral_summary,
        "trader_alert": trader_alert_summary,
        "telegram": telegram_summary,
        "film_steps": dashboard.get("film_steps", []) or [],
        "next_watch": dashboard.get("next_watch_enriched", []) or [],
    }

    write_json(DEFAULT_RUNTIME_STATUS, runtime_status, pretty=args.pretty)
    write_json(DEFAULT_PIPELINE_TRACE, pipeline_trace, pretty=args.pretty)

    if args.summary:
        print(f"  OK  runtime_status → {DEFAULT_RUNTIME_STATUS}")
        print(f"  OK  pipeline_trace  → {DEFAULT_PIPELINE_TRACE}")
        print("=" * 55)
        print(f"  LIVE CYCLE  {status_value}  ({elapsed_total}s)")
        print("=" * 55)
        print(f"  top_alert                    {runtime_status.get('top_alert')}")
        print(f"  top_level                    {runtime_status.get('top_level')}")
        print(f"  behavioral_count             {runtime_status.get('behavioral_count')}")
        print(f"  dashboard_ready              {runtime_status.get('dashboard_ready')}")
        print(f"  trader_alert_ready           {runtime_status.get('trader_alert_ready')}")
        print(f"  trader_alert_level           {runtime_status.get('trader_alert_level')}")
        print(f"  trader_alert_freshness       {runtime_status.get('trader_alert_freshness')}")
        print(f"  telegram_mode                {runtime_status.get('telegram_mode')}")
        print(f"  telegram_verdict             {runtime_status.get('telegram_verdict')}")
        print(f"  telegram_sent                {runtime_status.get('telegram_sent')}")
        if warnings:
            print("  warnings")
            for w in warnings:
                print(f"    - {w}")
        print("=" * 55)

    return 0 if status_value in {"OK", "WARN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
