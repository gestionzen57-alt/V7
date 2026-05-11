#!/usr/bin/env python3
"""
PowerFlow V7.2 Dashboard Contract Validator V0.3

Improvements over V0.1:
  - Negated doctrine text is not treated as forbidden content.
  - JSON wrappers produced by dashboard_data_normalizer_v02.py are understood.
  - Placeholder/MISSING sources do not create timestamp warnings.
  - Data contract failures remain hard FAIL.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_ATTRS = ["data-brick", "data-method", "data-timestamp", "data-freshness", "data-age-seconds"]
REQUIRED_BRICKS = [
    "B1_LEGACY", "B1_HMM", "DUAL_REGIME_DIVERGENCE",
    "B4_ROLLING", "B4_WAVELET", "DUAL_DENSITY_DIVERGENCE",
    "B3_KALMAN", "B3_CLUSTERS", "P1_ENERGY",
    "B5_SPEARMAN", "B5_TAIL_EXTREMES", "B5_STATE_DISTRIBUTION",
    "B7_RESONANCE", "B7_TEXTURE",
    "B2_CASCADE", "GUARD_ENTROPY",
    "GUARD_SESSION", "GUARD_DATA_QUALITY",
    "B6_MEMORY", "P2_ALERT_MAPPER", "TECHNICAL_RISKS",
]
FORBIDDEN_PATTERNS = [
    (r"regime_final|final_regime|r[ée]gime\s+final", "FORBIDDEN_FINAL_REGIME"),
    (r"density_final|final_density|densit[ée]\s+finale", "FORBIDDEN_FINAL_DENSITY"),
    (r"\bBUY\b|\bSELL\b", "FORBIDDEN_BUY_SELL"),
    (r"probabilit[ée]\s+de\s+succ[èe]s|success_probability", "FORBIDDEN_MEMORY_AS_PROBABILITY"),
]
EXPECTED_JSON = {
    "dashboard": "output/dashboard_data_v7.2.json",
    "cycle": "output/cycle_report.json",
    "p0": "output/P0_FINAL_DECISION.json",
    "regime_legacy": "output/dashboard_surface/regime_legacy.json",
    "regime_hmm": "output/dashboard_surface/regime_hmm.json",
    "kinematics": "output/dashboard_surface/kinematics.json",
    "density": "output/dashboard_surface/density.json",
    "wavelet": "output/dashboard_surface/wavelet.json",
    "spearman": "output/dashboard_surface/spearman.json",
    "fractal": "output/dashboard_surface/fractal.json",
    "texture": "output/dashboard_surface/texture.json",
    "cascade": "output/dashboard_surface/cascade.json",
    "entropy": "output/dashboard_surface/entropy.json",
    "session": "output/dashboard_surface/session.json",
    "dq": "output/dashboard_surface/dq.json",
    "memory": "output/dashboard_surface/memory.json",
    "alerts": "output/dashboard_surface/alerts.json",
    "node": "output/dashboard_surface/node.json",
}

@dataclass
class Finding:
    severity: str
    code: str
    message: str


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(s: str) -> datetime | None:
    if not s or not isinstance(s, str):
        return None
    v = s.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(v)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def strip_allowed_doctrine_text(html: str) -> str:
    """Remove sentences that explicitly state prohibitions, so the validator does not warn on doctrine banners."""
    allowed_phrases = [
        r"Pas de BUY/SELL\.?,?",
        r"Aucun BUY/SELL\.?,?",
        r"Pas de r[ée]gime final unique\.?,?",
        r"Pas de densit[ée] finale unique\.?,?",
        r"Memory\s*=\s*fr[ée]quence historique, jamais probabilit[ée]\.?,?",
        r"aucune probabilit[ée] de succ[èe]s\.?,?",
    ]
    scrubbed = html
    for pattern in allowed_phrases:
        scrubbed = re.sub(pattern, "", scrubbed, flags=re.I)
    return scrubbed


def find_timestamps(obj: Any, limit: int = 30) -> list[str]:
    keys = {"timestamp", "timestamp_utc", "generated_at", "generated_at_utc", "created_at", "updated_at", "time", "ts", "utc", "_normalized_at_utc"}
    found: list[str] = []
    def walk(x: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                if isinstance(v, str) and (k.lower() in keys or re.search(r"\d{4}-\d{2}-\d{2}T", v)):
                    if parse_iso(v):
                        found.append(v)
                walk(v)
        elif isinstance(x, list):
            for v in x[:80]:
                walk(v)
    walk(obj)
    return found


def validate_html(path: Path) -> list[Finding]:
    findings: list[Finding] = []
    html = path.read_text(encoding="utf-8", errors="replace")
    card_re = re.compile(r"<article\b[^>]*class=\"[^\"]*card[^\"]*\"[^>]*>", re.I)
    cards = card_re.findall(html)
    if not cards:
        findings.append(Finding("FAIL", "NO_CARDS", "No dashboard cards found."))
        return findings
    attrs_by_brick: dict[str, dict[str, str]] = {}
    for raw in cards:
        attrs = dict(re.findall(r"(data-[\w-]+)=\"([^\"]*)\"", raw))
        brick = attrs.get("data-brick", "")
        if brick:
            attrs_by_brick[brick] = attrs
        missing = [a for a in REQUIRED_ATTRS if a not in attrs]
        if missing:
            findings.append(Finding("FAIL", "CARD_ATTR_MISSING", f"Card {brick or raw[:80]} missing {missing}."))
    for brick in REQUIRED_BRICKS:
        if brick not in attrs_by_brick:
            findings.append(Finding("FAIL", "REQUIRED_BRICK_MISSING", f"Required brick card not found: {brick}"))
    scrubbed = strip_allowed_doctrine_text(html)
    for pattern, code in FORBIDDEN_PATTERNS:
        if re.search(pattern, scrubbed, re.I):
            findings.append(Finding("WARN", code, f"Forbidden or suspicious wording found outside allowed doctrine context: {code}"))
    if "comparison_no_average" not in html:
        findings.append(Finding("FAIL", "DUAL_REGIME_NO_NO_AVERAGE_METHOD", "Dual regime comparison card must state comparison_no_average."))
    if "comparison_no_fusion" not in html:
        findings.append(Finding("FAIL", "DUAL_DENSITY_NO_NO_FUSION_METHOD", "Dual density comparison card must state comparison_no_fusion."))
    return findings


def classify_json_freshness(data: Any, stale_seconds: int) -> tuple[str, int | None, list[str], str | None]:
    if isinstance(data, dict):
        explicit = str(data.get("freshness") or data.get("data_freshness") or data.get("status") or "").upper()
        if explicit in {"MISSING", "ERROR"}:
            return explicit, None, [], None
        if data.get("_placeholder") is True:
            return "MISSING", None, [], None
        if data.get("_powerflow_contract") == "V7.2_DASHBOARD_SURFACE":
            freshness = str(data.get("freshness") or "DEGRADED").upper()
            age = data.get("data_age_seconds")
            ts = data.get("timestamp_utc")
            provenance = data.get("timestamp_provenance")
            if ts and parse_iso(ts):
                return freshness, age, [ts], ts
            return freshness, age, [], None
    timestamps = find_timestamps(data)
    ages: list[tuple[int, str]] = []
    current = now_utc()
    for t in timestamps:
        dt = parse_iso(t)
        if dt:
            ages.append((max(0, int((current - dt).total_seconds())), t))
    if ages:
        age, stamp = min(ages, key=lambda x: x[0])
        return ("LIVE" if age <= stale_seconds else "STALE"), age, timestamps[:5], stamp
    return "DEGRADED", None, [], None


def validate_outputs(root: Path, stale_seconds: int) -> tuple[list[Finding], dict[str, Any]]:
    findings: list[Finding] = []
    inventory: dict[str, Any] = {}
    for name, rel in EXPECTED_JSON.items():
        p = root / rel
        rec: dict[str, Any] = {"path": str(p), "exists": p.exists()}
        if not p.exists():
            rec["freshness"] = "MISSING"
            inventory[name] = rec
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            rec["valid_json"] = True
            freshness, age, timestamps, chosen = classify_json_freshness(data, stale_seconds)
            rec["freshness"] = freshness
            rec["age_seconds_min"] = age
            rec["timestamps_found"] = timestamps
            rec["chosen_timestamp"] = chosen
            if freshness == "DEGRADED" and not timestamps:
                findings.append(Finding("WARN", "NO_TIMESTAMP_IN_JSON", f"{rel} has no parseable UTC timestamp and is not an explicit MISSING placeholder."))
        except Exception as exc:
            rec["valid_json"] = False
            rec["freshness"] = "ERROR"
            rec["error"] = str(exc)
            findings.append(Finding("FAIL", "INVALID_JSON", f"{rel}: {exc}"))
        inventory[name] = rec
    direct_available = sum(1 for n in ["regime_legacy", "regime_hmm", "kinematics", "density", "wavelet", "spearman", "fractal", "texture"] if inventory[n].get("exists"))
    aggregate_available = any(inventory[n].get("exists") for n in ["dashboard", "cycle", "p0"])
    if direct_available < 4 and aggregate_available:
        findings.append(Finding("INFO", "AGGREGATE_FALLBACK_ACTIVE", "Direct brick files are sparse; dashboard must use aggregate fallback or normalizer."))
    if not aggregate_available and direct_available < 4:
        findings.append(Finding("FAIL", "INSUFFICIENT_DASHBOARD_INPUTS", "Neither aggregate nor enough direct brick JSON files are present."))
    return findings, inventory


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate PowerFlow V7.2 dashboard contract.")
    ap.add_argument("--html", default="dashboard_live_v7.2_final.html")
    ap.add_argument("--root", default=".")
    ap.add_argument("--stale-seconds", type=int, default=180)
    ap.add_argument("--json-out", default="output/dashboard_contract_validation.json")
    ap.add_argument("--md-out", default="output/DASHBOARD_CONTRACT_VALIDATION.md")
    args = ap.parse_args()

    html_path = Path(args.html)
    root = Path(args.root)
    findings: list[Finding] = []
    if html_path.exists():
        findings.extend(validate_html(html_path))
    else:
        findings.append(Finding("FAIL", "HTML_NOT_FOUND", f"Dashboard HTML not found: {html_path}"))
    output_findings, inventory = validate_outputs(root, args.stale_seconds)
    findings.extend(output_findings)

    fail_count = sum(1 for f in findings if f.severity == "FAIL")
    warn_count = sum(1 for f in findings if f.severity == "WARN")
    verdict = "PASS" if fail_count == 0 else "FAIL"
    report = {
        "generated_at": now_utc().isoformat(),
        "verdict": verdict,
        "fail_count": fail_count,
        "warn_count": warn_count,
        "findings": [asdict(f) for f in findings],
        "inventory": inventory,
        "doctrine": {
            "no_final_regime": True,
            "no_final_density": True,
            "memory_is_frequency_not_probability": True,
            "alerts_are_perception_not_decision": True,
        },
    }
    json_out = Path(args.json_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    md_out = Path(args.md_out)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# DASHBOARD CONTRACT VALIDATION — PowerFlow V7.2",
        "",
        f"Generated UTC : {report['generated_at']}",
        f"Verdict : **{verdict}**",
        f"FAIL : {fail_count} | WARN : {warn_count}",
        "",
        "## Findings",
    ]
    if findings:
        for f in findings:
            lines.append(f"- **{f.severity}** `{f.code}` — {f.message}")
    else:
        lines.append("- No findings.")
    lines.extend(["", "## JSON Inventory", "", "| Source | Exists | Freshness | Age sec | Notes |", "|---|---:|---|---:|---|"])
    for name, rec in inventory.items():
        lines.append(f"| {name} | {rec.get('exists')} | {rec.get('freshness','-')} | {rec.get('age_seconds_min','-')} | {rec.get('error','')} |")
    md_out.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"{verdict} dashboard contract validation: {fail_count} fail, {warn_count} warn")
    print(f"JSON: {json_out}")
    print(f"MD:   {md_out}")
    return 0 if verdict == "PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
