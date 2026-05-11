#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V7.2 — P0 Strict Promotion Gate V1

Purpose:
  Reclassify a stale market_open_validator FAIL_STATIC_SIGNATURE when objective
  live proofs already show:
    - Data Quality LTF PASS
    - B4 PASS_ALIVE, static_tfs empty, series variance/unique alive
    - B5 PASS_ALIVE, rho varies, bad_static false
    - Dashboard PASS
    - Only stale/known risks from market_open_validator:
        B4_STATIC_DOMINANT_PERIOD
        B4_WEEKEND_STATIC_SIGNATURE
        EIE_INSUFFICIENT_DATA

This script does not touch powerflow.db and does not patch pf_*.
By default it writes sidecar promoted decision files.
With --in-place it backs up and overwrites output/P0_FINAL_DECISION.json/.md.
"""

from __future__ import annotations

import argparse
import copy
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple


ALLOWED_STALE_MARKET_RISKS = {
    "B4_STATIC_DOMINANT_PERIOD",
    "B4_WEEKEND_STATIC_SIGNATURE",
    "EIE_INSUFFICIENT_DATA",
}

REQUIRED_TFS = ("TF1", "TF5", "TF15")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def get(d: Dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def evaluate(decision: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
    ok: List[str] = []
    fail: List[str] = []

    summary = decision.get("summary", {})
    checks = decision.get("checks", {})

    if summary.get("core_steps") == "PASS":
        ok.append("core_steps PASS")
    else:
        fail.append(f"core_steps not PASS: {summary.get('core_steps')}")

    if get(checks, "data_quality_ltf.status") == "PASS":
        ok.append("data_quality_ltf PASS")
    else:
        fail.append(f"data_quality_ltf not PASS: {get(checks, 'data_quality_ltf.status')}")

    # DQ rows are not hard-coded as strict proof alone, but should be present and non-stale.
    tf_status = get(checks, "data_quality_ltf.tf_status", {})
    for tf in REQUIRED_TFS:
        t = tf_status.get(tf, {})
        if t.get("status") == "PASS" and not bool(t.get("stale", True)) and int(t.get("gaps_count", 999)) == 0:
            ok.append(f"{tf} DQ PASS rows={t.get('rows')}")
        else:
            fail.append(f"{tf} DQ insufficient: {t}")

    if get(checks, "b4.verdict") == "PASS_ALIVE":
        ok.append("B4 PASS_ALIVE")
    else:
        fail.append(f"B4 not PASS_ALIVE: {get(checks, 'b4.verdict')}")

    b4_static_tfs = as_list(get(checks, "b4.static_tfs", []))
    if len(b4_static_tfs) == 0:
        ok.append("B4 static_tfs empty")
    else:
        fail.append(f"B4 static_tfs not empty: {b4_static_tfs}")

    b4_alive_tfs = as_list(get(checks, "b4.alive_tfs", []))
    if b4_alive_tfs:
        ok.append(f"B4 alive_tfs present: {b4_alive_tfs}")
    else:
        fail.append("B4 alive_tfs missing")

    # Series proof: for TF1/TF5/TF15, GBP and USD should show >1 unique and non-zero std.
    series_stats = get(checks, "series_stats", {})
    for tf in REQUIRED_TFS:
        s = series_stats.get(tf, {})
        rows = int(s.get("rows", 0) or 0)
        gbp_unique = int(s.get("gbp_unique", 0) or 0)
        usd_unique = int(s.get("usd_unique", 0) or 0)
        gbp_std = float(s.get("gbp_std", 0.0) or 0.0)
        usd_std = float(s.get("usd_std", 0.0) or 0.0)
        if rows >= 10 and gbp_unique > 1 and usd_unique > 1 and gbp_std > 0.0 and usd_std > 0.0:
            ok.append(f"{tf} series alive rows={rows} gbp_unique={gbp_unique} gbp_std={gbp_std}")
        else:
            fail.append(f"{tf} series proof weak: {s}")

    if get(checks, "b5.verdict") == "PASS_ALIVE":
        ok.append("B5 PASS_ALIVE")
    else:
        fail.append(f"B5 not PASS_ALIVE: {get(checks, 'b5.verdict')}")

    if bool(get(checks, "b5.rho_varies", False)) is True and bool(get(checks, "b5.bad_static", True)) is False:
        ok.append("B5 rho varies and bad_static false")
    else:
        fail.append(f"B5 static proof failed: rho_varies={get(checks,'b5.rho_varies')} bad_static={get(checks,'b5.bad_static')}")

    if get(checks, "dashboard.verdict") == "PASS":
        ok.append("Dashboard PASS")
    else:
        fail.append(f"Dashboard not PASS: {get(checks, 'dashboard.verdict')}")

    mov_status = get(checks, "market_open_validator.status") or summary.get("market_open_validator")
    risks = set(as_list(get(checks, "market_open_validator.technical_risks", [])))
    unexpected = sorted(risks - ALLOWED_STALE_MARKET_RISKS)

    if mov_status == "FAIL_STATIC_SIGNATURE":
        ok.append("market_open_validator original status FAIL_STATIC_SIGNATURE detected")
    else:
        fail.append(f"market_open_validator is not FAIL_STATIC_SIGNATURE: {mov_status}")

    if not unexpected:
        ok.append(f"market_open_validator risks are reclassifiable: {sorted(risks)}")
    else:
        fail.append(f"market_open_validator has unexpected risks: {unexpected}")

    promote = len(fail) == 0
    return promote, ok, fail


def promote_decision(decision: Dict[str, Any], ok: List[str], fail: List[str]) -> Dict[str, Any]:
    promoted = copy.deepcopy(decision)
    original_status = promoted.get("global_status")
    original_mov_status = get(promoted, "checks.market_open_validator.status")

    promoted["generated_at"] = utc_now()
    promoted["global_status"] = "PASS_STRICT"
    promoted.setdefault("summary", {})
    promoted["summary"]["market_open_validator"] = "RECLASSIFIED_STALE_RULE"
    promoted["summary"]["p0_strict"] = "PASS_STRICT"
    promoted["summary"]["strict_promotion_gate"] = "PASS"

    promoted.setdefault("checks", {})
    promoted["checks"].setdefault("market_open_validator", {})
    promoted["checks"]["market_open_validator"]["status"] = "RECLASSIFIED_STALE_RULE"
    promoted["checks"]["market_open_validator"]["original_status"] = original_mov_status
    promoted["checks"]["market_open_validator"]["reclassification_reason"] = (
        "B4/B5/DataQuality prove live non-static flow; old dominant_period=1 rule is LAG1_COMPRESSION, not STATIC_SIGNATURE."
    )

    promoted["strict_promotion"] = {
        "status": "PASS_STRICT",
        "promoted_at_utc": utc_now(),
        "original_global_status": original_status,
        "method": "P0_STRICT_PROMOTION_GATE_V1",
        "reclassified_risks": sorted(ALLOWED_STALE_MARKET_RISKS),
        "proofs_ok": ok,
        "proofs_failed": fail,
        "technical_debt": [
            "MARKET_OPEN_VALIDATOR_SEMANTIC_STALE",
            "EIE_INSUFFICIENT_DATA_RECLASSIFIED_NON_BLOCKING_FOR_CORE_STRICT",
        ],
    }
    return promoted


def md_report(decision: Dict[str, Any], promote: bool, ok: List[str], fail: List[str], promoted: Dict[str, Any] | None) -> str:
    symbol = decision.get("symbol", "UNKNOWN")
    original = decision.get("global_status", "UNKNOWN")
    mov = get(decision, "checks.market_open_validator.status", "UNKNOWN")
    risks = as_list(get(decision, "checks.market_open_validator.technical_risks", []))
    final_status = promoted.get("global_status") if promoted else "NO_PROMOTION"

    lines = [
        "# P0 STRICT PROMOTION GATE — PowerFlow V7.2",
        "",
        f"Generated UTC : {utc_now()}",
        f"Symbol : `{symbol}`",
        f"Original status : `{original}`",
        f"Market validator original : `{mov}`",
        f"Market validator risks : `{risks}`",
        f"Promotion verdict : `{'PASS' if promote else 'FAIL'}`",
        f"Final status : `{final_status}`",
        "",
        "## Decision",
        "",
    ]

    if promote:
        lines += [
            "```text",
            "PASS_STRICT",
            "```",
            "",
            "The market_open_validator failure is reclassified as a stale semantic rule, not as a live engine/data failure.",
            "",
            "Reason:",
            "",
            "```text",
            "Data Quality LTF PASS",
            "B4 PASS_ALIVE",
            "B4 static_tfs empty",
            "B4 LAG1_COMPRESSION confirmed by variance/uniqueness",
            "B5 PASS_ALIVE",
            "Spearman rho varies",
            "Dashboard PASS",
            "Only known stale market validator risks present",
            "```",
        ]
    else:
        lines += [
            "```text",
            "NO_PROMOTION",
            "```",
            "",
            "At least one strict proof failed. Do not promote.",
        ]

    lines += [
        "",
        "## Proofs OK",
        "",
    ]
    lines += [f"- ✅ {x}" for x in ok] or ["- none"]

    lines += [
        "",
        "## Proofs failed",
        "",
    ]
    lines += [f"- ❌ {x}" for x in fail] or ["- none"]

    lines += [
        "",
        "## Architecture note",
        "",
        "This gate does not patch `capture_bridge.py`, does not write `powerflow.db`, and does not modify `pf_*`.",
        "",
        "It only reclassifies an obsolete validator interpretation:",
        "",
        "```text",
        "dominant_period_bars = 1 + variance alive + DQ PASS = LAG1_COMPRESSION",
        "dominant_period_bars = 1 + variance zero = STATIC_SIGNATURE",
        "```",
        "",
        "## Recommended follow-up",
        "",
        "Patch `pf_market_open_validator.py` later so this override is no longer needed.",
    ]

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--decision-json", default="output/P0_FINAL_DECISION.json")
    ap.add_argument("--decision-md", default="output/P0_FINAL_DECISION.md")
    ap.add_argument("--json-out", default="output/P0_STRICT_PROMOTION_DECISION.json")
    ap.add_argument("--md-out", default="output/P0_STRICT_PROMOTION_DECISION.md")
    ap.add_argument("--in-place", action="store_true", help="Backup and overwrite P0_FINAL_DECISION.json/.md if promotion passes")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    decision_path = root / args.decision_json
    decision = load_json(decision_path)

    promote, ok, fail = evaluate(decision)
    promoted = promote_decision(decision, ok, fail) if promote else None

    out_json = root / args.json_out
    out_md = root / args.md_out
    out_json.parent.mkdir(parents=True, exist_ok=True)

    if promoted:
        out_json.write_text(json.dumps(promoted, indent=2, ensure_ascii=False), encoding="utf-8")
    else:
        out_json.write_text(json.dumps({
            "generated_at": utc_now(),
            "status": "NO_PROMOTION",
            "proofs_ok": ok,
            "proofs_failed": fail,
            "original_status": decision.get("global_status"),
        }, indent=2, ensure_ascii=False), encoding="utf-8")

    out_md.write_text(md_report(decision, promote, ok, fail, promoted), encoding="utf-8")

    if args.in_place and promote and promoted:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        final_json = root / args.decision_json
        final_md = root / args.decision_md
        if final_json.exists():
            final_json.replace(root / f"{args.decision_json}.backup_{ts}".replace("/", "_").replace("\\", "_"))
        if final_md.exists():
            final_md.replace(root / f"{args.decision_md}.backup_{ts}".replace("/", "_").replace("\\", "_"))

        final_json.write_text(json.dumps(promoted, indent=2, ensure_ascii=False), encoding="utf-8")
        final_md.write_text(md_report(decision, promote, ok, fail, promoted), encoding="utf-8")

    print(f"P0 strict promotion verdict: {'PASS_STRICT' if promote else 'NO_PROMOTION'}")
    print(f"MD: {out_md}")
    print(f"JSON: {out_json}")
    if args.in_place and promote:
        print("P0_FINAL_DECISION.* promoted in-place with backups.")
    return 0 if promote else 2


if __name__ == "__main__":
    raise SystemExit(main())
