#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
p0_final_validator.py - PowerFlow V7.2 P0 final decision wrapper.

Purpose:
- read cycle outputs;
- reclassify dominant_period_bars=1 with live variance as LAG1_COMPRESSION, not STATIC_FAIL;
- reclassify *_INSUFFICIENT_DATA as PENDING_DATA_WINDOW, not engine failure;
- produce output/P0_FINAL_DECISION.md and output/P0_FINAL_DECISION.json.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

CORE_REQUIRED_STEPS = {
    "data_quality_guard",
    "regime_engine",
    "temporal_density",
    "spearman_gravity",
    "fractal_resonance",
    "temporal_node_state",
    "currency_energy_probe",
    "confluence_alert",
    "cascade_engine",
    "dashboard_refresh",
}

GOOD_CYCLE_STATES = {"CYCLE_COMPRESSING", "CYCLE_EXPANDING", "COMPRESSING", "EXPANDING"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path, default: Any = None) -> Any:
    try:
        if path.exists() and path.stat().st_size > 0:
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def db_series_stats(db: Path, symbol: str, tfs: List[int], limit: int = 30) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        for tf in tfs:
            rows = cur.execute(
                """
                SELECT created_at, force_gbp, force_usd, bid
                FROM force_snapshots
                WHERE symbol = ?
                  AND timeframe = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (symbol, tf, limit),
            ).fetchall()
            gbp = [float(r[1]) for r in rows if r[1] is not None]
            usd = [float(r[2]) for r in rows if r[2] is not None]

            def std(vals: List[float]) -> float:
                return float(statistics.pstdev(vals)) if len(vals) > 1 else 0.0

            out[f"TF{tf}"] = {
                "rows": len(rows),
                "first": rows[-1][0] if rows else None,
                "last": rows[0][0] if rows else None,
                "gbp_unique": len(set(gbp)),
                "usd_unique": len(set(usd)),
                "gbp_std": round(std(gbp), 6),
                "usd_std": round(std(usd), 6),
                "sample_last": rows[:5],
            }
    finally:
        con.close()
    return out


def db_recent_counts(db: Path, symbol: str, since: Optional[str]) -> Dict[str, Any]:
    if not since:
        return {}
    con = sqlite3.connect(str(db))
    try:
        cur = con.cursor()
        rows = cur.execute(
            """
            SELECT timeframe, COUNT(1), MIN(created_at), MAX(created_at)
            FROM force_snapshots
            WHERE symbol = ?
              AND created_at >= ?
            GROUP BY timeframe
            ORDER BY timeframe
            """,
            (symbol, since),
        ).fetchall()
        return {
            f"TF{int(tf)}": {"rows": int(count), "first": first_ts, "last": last_ts}
            for tf, count, first_ts, last_ts in rows
        }
    finally:
        con.close()


def extract_cycle_steps(cycle: Dict[str, Any], symbol: str) -> Dict[str, Dict[str, Any]]:
    steps = cycle.get("symbol_results", {}).get(symbol, {}).get("steps", []) if isinstance(cycle, dict) else []
    return {s.get("step", f"unknown_{i}"): s for i, s in enumerate(steps)}


def market_validator_status(market_payload: Dict[str, Any]) -> Dict[str, Any]:
    risks: List[str] = []

    def collect(obj: Any) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "technical_risks" and isinstance(v, list):
                    risks.extend([x for x in v if isinstance(x, str)])
                else:
                    collect(v)
        elif isinstance(obj, list):
            for x in obj:
                collect(x)

    collect(market_payload or {})
    static_risks = [r for r in risks if "STATIC" in r or "FROZEN" in r or "STALE" in r]
    insufficient = [r for r in risks if "INSUFFICIENT_DATA" in r or "NO_ROWS" in r]

    if not market_payload:
        return {"status": "MISSING_OUTPUT", "technical_risks": [], "explanation": "No readable market validator JSON."}
    if static_risks:
        return {"status": "FAIL_STATIC_SIGNATURE", "technical_risks": sorted(set(risks)), "explanation": "Static/frozen risks detected."}
    if insufficient:
        return {"status": "PENDING_DATA_WINDOW", "technical_risks": sorted(set(risks)), "explanation": "Only insufficient-data risks detected."}

    status_field = market_payload.get("overall_status") or market_payload.get("status") or market_payload.get("verdict") or "UNKNOWN"
    if str(status_field).upper() in {"OK", "PASS", "CLEAN"}:
        return {"status": "PASS", "technical_risks": sorted(set(risks)), "explanation": "Market validator pass."}
    return {"status": str(status_field), "technical_risks": sorted(set(risks)), "explanation": "Output read; no static signature found."}


def data_quality_ltf_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    status = str(payload.get("overall_status", "MISSING")).upper() if isinstance(payload, dict) else "MISSING"
    reports = payload.get("timeframe_reports", {}) if isinstance(payload, dict) else {}
    tf_status: Dict[str, Any] = {}
    for tf in ("1", "5", "15"):
        rep = reports.get(tf) or reports.get(int(tf)) or {}
        tf_status[f"TF{tf}"] = {
            "status": rep.get("status"),
            "rows": rep.get("rows"),
            "stale": rep.get("stale"),
            "gaps_count": rep.get("gaps_count"),
            "last_timestamp": rep.get("last_timestamp"),
        }
    pass_ltf = status == "PASS" and all(tf_status[k].get("status") == "PASS" for k in ("TF1", "TF5", "TF15"))
    return {"status": "PASS" if pass_ltf else status, "tf_status": tf_status, "technical_risks": payload.get("technical_risks", []) if isinstance(payload, dict) else []}


def temporal_density_status(payload: Dict[str, Any], stats: Dict[str, Any]) -> Dict[str, Any]:
    details = payload.get("details", {}) if isinstance(payload, dict) else {}
    gbp_keys = ["GBP_TF1", "GBP_TF5", "GBP_TF15"]
    gbp = {k: details.get(k, {}) for k in gbp_keys}
    alive_tfs: List[str] = []
    static_tfs: List[str] = []
    lag1_tfs: List[str] = []

    for key, item in gbp.items():
        tf_num = int(key.split("TF")[1])
        tf_stats = stats.get(f"TF{tf_num}", {})
        cycle = item.get("cycle_state")
        period = item.get("dominant_period_bars")
        unique_ok = (
            tf_stats.get("gbp_unique", 0) >= 10
            and tf_stats.get("usd_unique", 0) >= 10
            and tf_stats.get("gbp_std", 0.0) > 0.0001
            and tf_stats.get("usd_std", 0.0) > 0.0001
        )
        cycle_ok = cycle in GOOD_CYCLE_STATES
        if period == 1 and unique_ok and cycle_ok:
            lag1_tfs.append(key)
            alive_tfs.append(key)
        elif period == 1 and not unique_ok:
            static_tfs.append(key)
        elif cycle_ok:
            alive_tfs.append(key)

    state = payload.get("state") if isinstance(payload, dict) else None
    compression_count = payload.get("compression_count", 0) if isinstance(payload, dict) else 0

    if static_tfs:
        verdict = "FAIL_STATIC_SIGNATURE"
    elif len(alive_tfs) >= 2 and state:
        verdict = "PASS_ALIVE"
    else:
        verdict = "PENDING_DATA_WINDOW"
    return {
        "verdict": verdict,
        "state": state,
        "compression_count": compression_count,
        "gbp_details": gbp,
        "lag1_compression_tfs": lag1_tfs,
        "static_tfs": static_tfs,
        "alive_tfs": alive_tfs,
        "explanation": "dominant_period_bars=1 is LAG1_COMPRESSION if uniqueness/std prove live data.",
    }


def spearman_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict) or not payload:
        return {"verdict": "MISSING_OUTPUT"}
    state = payload.get("state")
    details = payload.get("details", {})
    mixed_count = payload.get("mixed_count", len(payload.get("mixed_resolved", [])))
    divergent_count = payload.get("divergent_count", len(payload.get("divergent_pairs", [])))
    synchro_count = payload.get("synchro_count", len(payload.get("synchro_pairs", [])))
    tail = payload.get("tail_extreme", [])
    gbp_usd = details.get("GBP_USD", {})
    rhos: List[float] = []
    for tf in ("TF1", "TF5", "TF15"):
        rho = gbp_usd.get(tf, {}).get("spearman_rho") if isinstance(gbp_usd, dict) else None
        if isinstance(rho, (int, float)):
            rhos.append(float(rho))
    rho_varies = len(set(round(x, 6) for x in rhos)) > 1 if rhos else False
    bad_static = bool(rhos) and (all(abs(x) < 1e-12 for x in rhos) or all(round(x, 3) == -0.85 for x in rhos))
    if bad_static:
        verdict = "FAIL_STATIC_SIGNATURE"
    elif state == "SPEARMAN_GRAVITY_ACTIVE" and (rho_varies or mixed_count or divergent_count or synchro_count or tail):
        verdict = "PASS_ALIVE"
    elif state:
        verdict = "PASS_NEUTRAL_FIELD"
    else:
        verdict = "PENDING_DATA_WINDOW"
    return {"verdict": verdict, "state": state, "mixed_count": mixed_count, "divergent_count": divergent_count, "synchro_count": synchro_count, "tail_extreme": tail, "gbp_usd_rhos": rhos, "rho_varies": rho_varies, "bad_static": bad_static}


def dashboard_status(cycle_steps: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    dash = cycle_steps.get("dashboard_refresh", {})
    ok = dash.get("status") == "OK" and dash.get("returncode") == 0
    tail = dash.get("stdout_tail", "") or ""
    return {"verdict": "PASS" if ok else "FAIL", "behavioral_flow_present": "behavioral_flow=PRESENT" in tail or "Dashboard Sync Agent" in tail, "behavioral_count_present": "behavioral_count=" in tail, "tail": tail[-1200:]}


def build_markdown(result: Dict[str, Any]) -> str:
    checks = result["checks"]
    lines: List[str] = []
    lines.append("# P0 FINAL DECISION - PowerFlow V7.2")
    lines.append("")
    lines.append(f"**Generated at:** {result['generated_at']}")
    lines.append(f"**Symbol:** `{result['symbol']}`")
    lines.append(f"**DB:** `{result['db']}`")
    lines.append(f"**Since:** `{result.get('since') or 'n/a'}`")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"```text\n{result['global_status']}\n```")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    for name, status in result["summary"].items():
        lines.append(f"- **{name}** : `{status}`")
    lines.append("")
    lines.append("## Core cycle steps")
    lines.append("")
    for step, info in result["cycle_steps"].items():
        lines.append(f"- `{step}` : `{info.get('status')}` returncode=`{info.get('returncode')}`")
    lines.append("")
    lines.append("## Data Quality LTF")
    lines.append("")
    lines.append(f"Status: `{checks['data_quality_ltf']['status']}`")
    for tf, item in checks["data_quality_ltf"]["tf_status"].items():
        lines.append(f"- {tf}: status=`{item.get('status')}` rows=`{item.get('rows')}` stale=`{item.get('stale')}` gaps=`{item.get('gaps_count')}` last=`{item.get('last_timestamp')}`")
    lines.append("")
    lines.append("## B4 Temporal Density")
    lines.append("")
    lines.append(f"Verdict: `{checks['b4']['verdict']}`")
    lines.append(f"State: `{checks['b4'].get('state')}`")
    lines.append(f"Compression count: `{checks['b4'].get('compression_count')}`")
    lines.append(f"LAG1 compression TFs: `{checks['b4'].get('lag1_compression_tfs')}`")
    lines.append("")
    lines.append("### Series proof")
    for tf, item in checks["series_stats"].items():
        lines.append(f"- {tf}: rows=`{item['rows']}` GBP unique=`{item['gbp_unique']}` GBP std=`{item['gbp_std']}` USD unique=`{item['usd_unique']}` USD std=`{item['usd_std']}`")
    lines.append("")
    lines.append("## B5 Spearman Gravity")
    lines.append("")
    lines.append(f"Verdict: `{checks['b5']['verdict']}`")
    lines.append(f"State: `{checks['b5'].get('state')}`")
    lines.append(f"Mixed count: `{checks['b5'].get('mixed_count')}`")
    lines.append(f"Divergent count: `{checks['b5'].get('divergent_count')}`")
    lines.append(f"Tail extremes: `{checks['b5'].get('tail_extreme')}`")
    lines.append(f"GBP/USD rhos: `{checks['b5'].get('gbp_usd_rhos')}`")
    lines.append("")
    lines.append("## Market Open Validator")
    lines.append("")
    lines.append(f"Status: `{checks['market_open_validator']['status']}`")
    lines.append(f"Risks: `{checks['market_open_validator'].get('technical_risks')}`")
    lines.append("")
    lines.append("```text")
    lines.append("INSUFFICIENT_DATA = PENDING_DATA_WINDOW")
    lines.append("STATIC_SIGNATURE  = true engine/data failure")
    lines.append("```")
    lines.append("")
    lines.append("## Dashboard")
    lines.append("")
    lines.append(f"Verdict: `{checks['dashboard']['verdict']}`")
    lines.append(f"Behavioral flow present: `{checks['dashboard']['behavioral_flow_present']}`")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    if result["global_status"] == "PASS_STRICT":
        lines.append("P0 strict can be marked PASS.")
    elif result["global_status"] == "PASS_CORE_PARTIAL_STRICT":
        lines.append("PowerFlow core perception is PASS. Strict P0 remains PARTIAL only because market_open_validator is waiting for a full data window.")
    else:
        lines.append("P0 remains blocked. Inspect failed sections above.")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="powerflow.db")
    ap.add_argument("--symbol", default="GBPUSD")
    ap.add_argument("--since", default=None)
    ap.add_argument("--cycle-report", default="output/cycle_report.json")
    ap.add_argument("--data-quality", default=None)
    ap.add_argument("--temporal-density", default=None)
    ap.add_argument("--spearman", default=None)
    ap.add_argument("--market-validator", default=None)
    ap.add_argument("--output-md", default="output/P0_FINAL_DECISION.md")
    ap.add_argument("--output-json", default="output/P0_FINAL_DECISION.json")
    args = ap.parse_args()

    db = Path(args.db)
    out_dir = Path("output")
    cycle = load_json(Path(args.cycle_report), {})
    steps = extract_cycle_steps(cycle, args.symbol)

    dq_path = Path(args.data_quality) if args.data_quality else out_dir / f"data_quality_guard_{args.symbol}.json"
    td_path = Path(args.temporal_density) if args.temporal_density else out_dir / f"temporal_density_{args.symbol}.json"
    sp_path = Path(args.spearman) if args.spearman else out_dir / f"spearman_gravity_{args.symbol}.json"
    mv_path = Path(args.market_validator) if args.market_validator else out_dir / f"market_open_validator_{args.symbol}.json"

    dq = load_json(dq_path, {})
    td = load_json(td_path, load_json(out_dir / "p0_temporal_density.json", {}))
    sp = load_json(sp_path, load_json(out_dir / "p0_spearman_gravity.json", {}))
    mv = load_json(mv_path, {})
    stats = db_series_stats(db, args.symbol, [1, 5, 15], limit=30)
    recent_counts = db_recent_counts(db, args.symbol, args.since)

    core_step_status = {step: steps.get(step, {}).get("status", "MISSING") for step in sorted(CORE_REQUIRED_STEPS)}
    core_steps_ok = all(v == "OK" for v in core_step_status.values())

    checks = {
        "data_quality_ltf": data_quality_ltf_status(dq),
        "b4": temporal_density_status(td, stats),
        "b5": spearman_status(sp),
        "market_open_validator": market_validator_status(mv),
        "dashboard": dashboard_status(steps),
        "series_stats": stats,
        "recent_counts": recent_counts,
    }

    core_pass = (
        core_steps_ok
        and checks["data_quality_ltf"]["status"] == "PASS"
        and checks["b4"]["verdict"] == "PASS_ALIVE"
        and checks["b5"]["verdict"] in {"PASS_ALIVE", "PASS_NEUTRAL_FIELD"}
        and checks["dashboard"]["verdict"] == "PASS"
    )
    market_status = checks["market_open_validator"]["status"]
    if core_pass and market_status == "PASS":
        global_status = "PASS_STRICT"
    elif core_pass and market_status in {"PENDING_DATA_WINDOW", "MISSING_OUTPUT"}:
        global_status = "PASS_CORE_PARTIAL_STRICT"
    elif core_pass:
        global_status = "PASS_CORE_REVIEW_MARKET_VALIDATOR"
    else:
        global_status = "FAIL_OR_PARTIAL_CORE"

    result = {
        "generated_at": now_utc(),
        "symbol": args.symbol,
        "db": str(db),
        "since": args.since,
        "global_status": global_status,
        "summary": {
            "core_steps": "PASS" if core_steps_ok else "PARTIAL",
            "data_quality_ltf": checks["data_quality_ltf"]["status"],
            "b4": checks["b4"]["verdict"],
            "b5": checks["b5"]["verdict"],
            "market_open_validator": market_status,
            "dashboard": checks["dashboard"]["verdict"],
        },
        "cycle_steps": {k: {"status": v.get("status"), "returncode": v.get("returncode")} for k, v in steps.items()},
        "checks": checks,
    }
    write_json(Path(args.output_json), result)
    Path(args.output_md).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output_md).write_text(build_markdown(result), encoding="utf-8")
    print(result["global_status"])
    print(f"json={args.output_json}")
    print(f"md={args.output_md}")
    return 0 if global_status in {"PASS_STRICT", "PASS_CORE_PARTIAL_STRICT", "PASS_CORE_REVIEW_MARKET_VALIDATOR"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
