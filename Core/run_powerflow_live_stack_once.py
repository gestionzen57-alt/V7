#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent

DEFAULT_SYMBOLS = ["GBPUSD", "EURUSD", "USDJPY"]
PRIMARY_SYMBOL = "GBPUSD"

MISSION_DIR = ROOT / "output" / "missions" / "TURBO_LIVE_STACK"
MISSION_DIR.mkdir(parents=True, exist_ok=True)

REPORT_JSON = MISSION_DIR / "turbo_live_stack_report.json"
REPORT_MD = MISSION_DIR / "TURBO_LIVE_STACK_REPORT.md"
CHECKPOINT_MD = MISSION_DIR / "CHECKPOINT_TURBO_LIVE_STACK.md"
LEXIQUE_PATCH_MD = MISSION_DIR / "LEXIQUE_PATCH_TURBO_LIVE_STACK.md"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_cmd(label: str, args: list[str], timeout: int = 120) -> dict[str, Any]:
    started = now_utc()
    print(f"\n=== RUN {label} ===")
    print(" ".join(args))

    try:
        env = dict(__import__("os").environ)
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("PYTHONUTF8", "1")

        p = subprocess.run(
            args,
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=timeout,
            env=env,
            encoding="utf-8",
            errors="replace",
        )
        stdout = p.stdout or ""
        stderr = p.stderr or ""
        if stdout.strip():
            print(stdout.strip())
        if stderr.strip():
            print(stderr.strip(), file=sys.stderr)

        return {
            "label": label,
            "args": args,
            "started_at": started,
            "ended_at": now_utc(),
            "returncode": p.returncode,
            "ok": p.returncode == 0,
            "stdout_tail": stdout[-4000:],
            "stderr_tail": stderr[-4000:],
        }
    except subprocess.TimeoutExpired as e:
        return {
            "label": label,
            "args": args,
            "started_at": started,
            "ended_at": now_utc(),
            "returncode": 124,
            "ok": False,
            "stdout_tail": (e.stdout or "")[-4000:] if isinstance(e.stdout, str) else "",
            "stderr_tail": "TIMEOUT",
        }
    except Exception as e:
        return {
            "label": label,
            "args": args,
            "started_at": started,
            "ended_at": now_utc(),
            "returncode": 1,
            "ok": False,
            "stdout_tail": "",
            "stderr_tail": f"{type(e).__name__}: {e}",
        }


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return None


def file_info(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.relative_to(ROOT)) if path.is_absolute() else str(path),
        "exists": path.exists(),
        "size": path.stat().st_size if path.exists() else None,
    }


def summarize_state(primary: str) -> dict[str, Any]:
    base = ROOT / "output" / "dashboard_surface" / primary

    daily = load_json(base / "daily_flow_packet.json") or {}
    topdown = load_json(base / "topdown_market_reader.json") or load_json(base / "topdown_market_reading.json") or {}
    live_decision = load_json(base / "live_decision.json") or {}
    live_brief = load_json(base / "powerflow_live_brief.json") or {}
    b6 = load_json(base / "microstructure_state.json") or {}
    b6_fusion = load_json(base / "b6_live_fusion.json") or {}

    dp = daily.get("daily_packet", {})
    jl = dp.get("journal_levels", {}) if isinstance(dp, dict) else {}

    surface = topdown.get("surface_reading", {}) if isinstance(topdown, dict) else {}

    return {
        "primary_symbol": primary,
        "daily": {
            "method": daily.get("method"),
            "intent": dp.get("intent_detected"),
            "prediction": dp.get("prediction_next_session"),
            "close_position": jl.get("close_position"),
            "high": jl.get("high_of_day"),
            "low": jl.get("low_of_day"),
            "close": jl.get("close"),
            "tested": len(dp.get("tested_levels", []) or []),
            "rejected": len(dp.get("rejected_levels", []) or []),
            "sweeps": len(dp.get("sweep_candidates", []) or []),
            "technical_risks": daily.get("technical_risks", []),
        },
        "topdown": {
            "flux": surface.get("flux"),
            "zone": surface.get("zone"),
            "driver": surface.get("driver"),
            "condition": surface.get("condition"),
            "machine_intention": surface.get("machine_intention"),
            "ontology": surface.get("ontology_dominant_category"),
            "technical_fragility": surface.get("technical_fragility", []),
        },
        "live": {
            "state": live_decision.get("state"),
            "level": live_decision.get("level"),
            "bias": live_decision.get("bias"),
            "message": live_decision.get("message"),
            "live_count": live_decision.get("live_count"),
            "expired_count": live_decision.get("expired_count"),
        },
        "brief": {
            "action": live_brief.get("action"),
            "synthesis": live_brief.get("synthesis"),
            "reading": live_brief.get("reading"),
        },
        "b6": {
            "state": (b6.get("microstructure") or {}).get("state") or b6.get("state"),
            "level": b6.get("level"),
            "tension": (b6.get("microstructure") or {}).get("tension_score") or b6.get("tension_score") or b6.get("tension"),
            "delta": (b6.get("microstructure") or {}).get("delta_cumulative") or b6.get("proxy_delta") or b6.get("delta"),
            "direction": ((b6.get("microstructure") or {}).get("absorption") or {}).get("direction") or b6.get("direction"),
            "absorption": ((b6.get("microstructure") or {}).get("absorption") or {}).get("interpretation") or b6.get("absorption_state") or b6.get("absorption"),
            "imbalance": ((b6.get("microstructure") or {}).get("imbalance") or {}).get("direction") or b6.get("imbalance_state") or b6.get("imbalance"),
            "alerts": len((b6.get("microstructure") or {}).get("alerts", []) or []),
        },
        "b6_fusion": {
            "action": b6_fusion.get("action") or b6_fusion.get("state"),
            "synthesis": b6_fusion.get("synthesis") or b6_fusion.get("reason") or b6_fusion.get("status"),
            "message": b6_fusion.get("message") or b6_fusion.get("reading"),
        },
        "files": [
            file_info(base / "daily_flow_packet.json"),
            file_info(base / "topdown_market_reader.json"),
            file_info(base / "topdown_market_reading.json"),
            file_info(base / "live_decision.json"),
            file_info(base / "cockpit_live_status.txt"),
            file_info(base / "powerflow_live_brief.json"),
            file_info(base / "powerflow_live_brief.txt"),
            file_info(base / "microstructure_state.json"),
            file_info(base / "microstructure_state.txt"),
            file_info(base / "b6_live_fusion.json"),
            file_info(base / "b6_live_fusion.txt"),
            file_info(ROOT / "output" / "dashboard_surface" / "daily_flow_packet.json"),
            file_info(ROOT / "output" / "dashboard_surface" / "daily_flow_packets.json"),
            file_info(ROOT / "output" / "dashboard_surface" / "microstructure_states.json"),
        ],
    }


def write_docs(report: dict[str, Any]) -> None:
    summary = report["summary"]
    runs = report["runs"]

    failed = [r for r in runs if not r["ok"]]
    verdict = "TURBO_STACK_OK" if not failed else "TURBO_STACK_PARTIAL"

    lines = []
    lines.append("# PowerFlow Turbo Live Stack Report")
    lines.append("")
    lines.append(f"- Created: `{report['created_at']}`")
    lines.append(f"- Mode: `ONE_SHOT_RUNNER`")
    lines.append(f"- Verdict: `{verdict}`")
    lines.append(f"- Primary symbol: `{summary['primary_symbol']}`")
    lines.append("")
    lines.append("## Pipeline exécuté")
    lines.append("")
    for r in runs:
        status = "OK" if r["ok"] else f"FAIL({r['returncode']})"
        lines.append(f"- `{status}` — {r['label']}")
    lines.append("")
    lines.append("## Lecture primaire")
    lines.append("")
    lines.append("### Daily")
    d = summary["daily"]
    for k, v in d.items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("### TopDown")
    for k, v in summary["topdown"].items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("### Live")
    for k, v in summary["live"].items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("### PowerFlow Brief")
    for k, v in summary["brief"].items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("### B6 Microstructure")
    for k, v in summary["b6"].items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("### B6 Fusion")
    for k, v in summary["b6_fusion"].items():
        lines.append(f"- `{k}`: `{v}`")
    lines.append("")
    lines.append("## Outputs contrôlés")
    lines.append("")
    for f in summary["files"]:
        lines.append(f"- `{f['path']}` exists={f['exists']} size={f['size']}")
    lines.append("")
    lines.append("## Risques techniques")
    lines.append("")
    risks = set()
    for src in ("daily", "topdown"):
        obj = summary.get(src, {})
        for key in ("technical_risks", "technical_fragility"):
            val = obj.get(key, [])
            if isinstance(val, list):
                risks.update(str(x) for x in val)
    if failed:
        risks.add("ONE_OR_MORE_RUNNERS_FAILED")
    if not risks:
        lines.append("- Aucun risque technique bloquant détecté par ce runner.")
    else:
        for risk in sorted(risks):
            lines.append(f"- `{risk}`")
    lines.append("")
    lines.append("## Suite logique")
    lines.append("")
    lines.append("1. Si `TURBO_STACK_OK`, lancer ce runner via tâche Windows 5 min ou l'intégrer dans `scheduler_powerflow_turbo_wrapper.py`.")
    lines.append("2. Si `TURBO_STACK_PARTIAL`, lire les stderr_tail dans le JSON.")
    lines.append("3. Garder M1 uniquement sur GBPUSD si objectif DB compacte.")
    lines.append("4. Ne pas toucher `capture_bridge.py` ni écrire manuellement dans `powerflow.db`.")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    ck = []
    ck.append("# CHECKPOINT — TURBO LIVE STACK")
    ck.append("")
    ck.append(f"- Created: `{report['created_at']}`")
    ck.append(f"- Verdict: `{verdict}`")
    ck.append(f"- Commit context: à vérifier avec `git log -1 --oneline`")
    ck.append("")
    ck.append("## État court")
    ck.append("")
    ck.append(f"- Daily intent: `{summary['daily'].get('intent')}`")
    ck.append(f"- TopDown condition: `{summary['topdown'].get('condition')}`")
    ck.append(f"- Live state: `{summary['live'].get('state')}`")
    ck.append(f"- Brief action: `{summary['brief'].get('action')}`")
    ck.append(f"- B6 state: `{summary['b6'].get('state')}`")
    ck.append(f"- B6 fusion: `{summary['b6_fusion'].get('synthesis')}`")
    ck.append("")
    ck.append("## Fichiers centraux")
    ck.append("")
    ck.append("- `run_powerflow_live_stack_once.py`")
    ck.append("- `output/missions/TURBO_LIVE_STACK/TURBO_LIVE_STACK_REPORT.md`")
    ck.append("- `output/missions/TURBO_LIVE_STACK/CHECKPOINT_TURBO_LIVE_STACK.md`")
    ck.append("- `output/missions/TURBO_LIVE_STACK/LEXIQUE_PATCH_TURBO_LIVE_STACK.md`")
    ck.append("")
    ck.append("## Reprise autre fil")
    ck.append("")
    ck.append("Le cycle complet Daily → TopDown → Live → B6 → Brief → Telegram est automatisé en one-shot.")
    ck.append("La machine perçoit et qualifie. Le trader décide.")
    CHECKPOINT_MD.write_text("\n".join(ck), encoding="utf-8")

    lex = []
    lex.append("# LEXIQUE PATCH — TURBO LIVE STACK")
    lex.append("")
    lex.append("## TURBO_LIVE_STACK")
    lex.append("Runner composite exécutant le cycle live complet PowerFlow en une seule commande.")
    lex.append("")
    lex.append("## B6_LIVE_FUSION")
    lex.append("Fusion entre microstructure proxy B6, Daily Flow Packet, TopDown Reader et Live Decision.")
    lex.append("")
    lex.append("## B6_NO_IMMEDIATE_PRESSURE")
    lex.append("État indiquant que la microstructure proxy ne justifie pas de réveil trader immédiat.")
    lex.append("")
    lex.append("## CONFLICT_OR_REINTEGRATION_TEST")
    lex.append("Tension entre lecture Daily/TopDown et lecture Live/B6. PowerFlow nomme le conflit sans trancher.")
    lex.append("")
    lex.append("## WAKE_TRADER")
    lex.append("Action de transmission indiquant une perception assez chaude pour réveiller l'attention du trader. Ce n'est pas un ordre.")
    lex.append("")
    lex.append("## TELEGRAM_MEMORY_GATE")
    lex.append("Gate anti-spam qui empêche la répétition de la même perception pendant une fenêtre de cooldown.")
    LEXIQUE_PATCH_MD.write_text("\n".join(lex), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--symbols", default="GBPUSD,EURUSD,USDJPY")
    parser.add_argument("--primary", default="GBPUSD")
    parser.add_argument("--send-telegram", action="store_true")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    primary = args.primary.strip().upper()

    py = sys.executable
    runs: list[dict[str, Any]] = []

    plan = [
        ("daily_flow_packet_all", [py, "run_daily_flow_packet_all_once.py", "--db", args.db, "--symbols", ",".join(symbols), "--output", "output/dashboard_surface/daily_flow_packets.json", "--pretty"], 180),
        ("daily_flow_packet_normalize", [py, "dashboard_normalize_daily_flow_packet.py", "--input", "output/dashboard_surface/daily_flow_packets.json", "--output", "output/dashboard_surface/daily_flow_packet.json", "--pretty"], 120),
        ("topdown_market_reader", [py, "run_topdown_market_reader_once.py", "--db", args.db, "--symbol", primary, "--pretty"], 180),
        ("gbpusd_live_decision", [py, "pf_gbpusd_live_decision_once.py"], 120),
        ("cockpit_live_status", [py, "pf_cockpit_live_status_once.py"], 120),
        ("powerflow_live_brief", [py, "pf_powerflow_live_brief_once.py"], 120),
        ("order_flow_proxy_all", [py, "run_order_flow_proxy_all_once.py", "--db", args.db, "--symbols", ",".join(symbols), "--pretty"], 180),
        ("b6_live_fusion", [py, "pf_b6_live_fusion_once.py"], 120),
    ]

    if args.send_telegram:
        plan.extend([
            ("powerflow_telegram_gate", [py, "pf_powerflow_telegram_gate_once.py"], 120),
            ("b6_telegram_gate", [py, "pf_b6_telegram_gate_once.py"], 120),
        ])

    for label, cmd, timeout in plan:
        if not Path(cmd[1]).exists():
            print(f"\n=== SKIP {label} === missing {cmd[1]}")
            runs.append({
                "label": label,
                "args": cmd,
                "started_at": now_utc(),
                "ended_at": now_utc(),
                "returncode": 127,
                "ok": False,
                "stdout_tail": "",
                "stderr_tail": f"MISSING_FILE {cmd[1]}",
            })
            continue
        runs.append(run_cmd(label, cmd, timeout=timeout))

    summary = summarize_state(primary)
    report = {
        "created_at": now_utc(),
        "mode": "ONE_SHOT_RUNNER",
        "db": args.db,
        "symbols": symbols,
        "primary": primary,
        "runs": runs,
        "summary": summary,
    }

    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_docs(report)

    failed = [r for r in runs if not r["ok"]]
    verdict = "TURBO_STACK_OK" if not failed else "TURBO_STACK_PARTIAL"

    print("\n=== TURBO STACK VERDICT ===")
    print(verdict)
    print("report_json=", REPORT_JSON)
    print("report_md  =", REPORT_MD)
    print("checkpoint =", CHECKPOINT_MD)
    print("lexique    =", LEXIQUE_PATCH_MD)

    if args.pretty:
        print(json.dumps({
            "verdict": verdict,
            "summary": summary,
            "failed": [{"label": r["label"], "err": r["stderr_tail"][-500:]} for r in failed],
        }, ensure_ascii=False, indent=2))

    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
