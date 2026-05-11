#!/usr/bin/env python3
"""
PowerFlow V7.2 Dashboard Data Normalizer V0.4

Purpose:
  Build a dedicated dashboard surface under output/dashboard_surface/*.json.
  This prevents the dashboard from depending on sparse/raw runtime files and
  prevents contract validation from warning only because a live engine output has
  no timestamp field.

Doctrine:
  - No DB write. No pf_* imports.
  - No B1/B1+ fusion.
  - No B4/B4+ fusion.
  - Raw direct outputs are never overwritten.
  - Missing data is explicit.
  - Timestamp provenance is explicit: source vs normalizer_generated.
  - Direct placeholder outputs do not override aggregate/live payloads.
  - Surface metadata is injected into payload for dashboard card freshness.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIRECT_TARGETS: dict[str, str] = {
    "regime_legacy": "output/regime_legacy_state.json",
    "regime_hmm": "output/regime_hmm_state.json",
    "kinematics": "output/kinematics_state.json",
    "force_kinematics": "output/force_kinematics_state.json",
    "energy": "output/currency_energy_state.json",
    "density": "output/temporal_density_state.json",
    "wavelet": "output/wavelet_density_state.json",
    "spearman": "output/spearman_gravity_state.json",
    "fractal": "output/fractal_resonance_state.json",
    "texture": "output/volatility_texture_state.json",
    "cascade": "output/cascade_state.json",
    "entropy": "output/alert_entropy_state.json",
    "session": "output/session_context.json",
    "dq": "output/data_quality_report.json",
    "memory": "output/memory_patterns.json",
    "alerts": "output/behavioral_alert_queue.json",
    "node": "output/temporal_node_state.json",
}

AGGREGATE_SOURCES: dict[str, str] = {
    "dashboard": "output/dashboard_data_v7.2.json",
    "cycle": "output/cycle_report.json",
    "p0": "output/P0_FINAL_DECISION.json",
    "p0_lower": "output/p0_final_decision.json",
}

SEARCH_PATHS: dict[str, list[str]] = {
    "regime_legacy": ["regime_legacy", "legacy_regime", "b1_legacy", "regime.legacy", "cycle_steps.regime_legacy"],
    "regime_hmm": ["regime_hmm", "hmm_regime", "b1_hmm", "regime.hmm", "cycle_steps.regime_hmm"],
    "kinematics": ["kinematics", "force_kinematics", "b3", "cycle_steps.kinematics", "summary.kinematics"],
    "force_kinematics": ["force_kinematics", "kinematics", "b3", "cycle_steps.kinematics"],
    "energy": ["energy", "currency_energy", "p1", "cycle_steps.energy", "summary.energy"],
    "density": ["temporal_density", "density", "b4", "cycle_steps.temporal_density", "summary.b4"],
    "wavelet": ["wavelet_density", "wavelet", "b4_wavelet", "b4_plus", "cycle_steps.wavelet_density"],
    "spearman": ["spearman_gravity", "gravity", "b5", "cycle_steps.spearman_gravity", "summary.b5"],
    "fractal": ["fractal_resonance", "resonance", "b7", "cycle_steps.fractal_resonance"],
    "texture": ["volatility_texture", "texture", "b7_texture", "b7_plus", "cycle_steps.volatility_texture"],
    "cascade": ["cascade", "b2", "cycle_steps.cascade", "summary.cascade"],
    "entropy": ["alert_entropy", "entropy", "guard_entropy", "cycle_steps.alert_entropy"],
    "session": ["session", "session_context", "session_overlay", "cycle_steps.session"],
    "dq": ["data_quality", "data_quality_report", "data_quality_ltf", "dq", "cycle_steps.data_quality"],
    "memory": ["memory", "memory_patterns", "memory_context", "b6", "cycle_steps.memory"],
    "alerts": ["behavioral_alert_queue", "alerts", "alert_queue", "p2_alerts"],
    "node": ["temporal_node", "node", "temporal_node_state", "cycle_steps.temporal_node"],
}

TIMESTAMP_KEYS = {"timestamp", "timestamp_utc", "generated_at", "generated_at_utc", "created_at", "updated_at", "time", "ts", "utc", "report_timestamp", "asof", "as_of"}

@dataclass
class SurfaceRecord:
    key: str
    surface_path: str
    action: str
    freshness: str
    source: str | None
    timestamp_provenance: str
    reason: str


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_iso(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def load_json(path: Path) -> tuple[bool, Any, str | None]:
    if not path.exists():
        return False, None, "MISSING"
    try:
        return True, json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:
        return False, None, f"ERROR: {exc}"


def find_timestamps(obj: Any, limit: int = 50) -> list[str]:
    found: list[str] = []
    def walk(x: Any) -> None:
        if len(found) >= limit:
            return
        if isinstance(x, dict):
            for k, v in x.items():
                lk = str(k).lower()
                if isinstance(v, str) and (lk in TIMESTAMP_KEYS or re.search(r"\d{4}-\d{2}-\d{2}T", v)) and parse_iso(v):
                    found.append(v)
                walk(v)
        elif isinstance(x, list):
            for v in x[:250]:
                walk(v)
    walk(obj)
    return found


def get_path(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return None
    return cur


def deep_find(obj: Any, names: set[str], max_depth: int = 8) -> Any:
    if max_depth < 0:
        return None
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in names:
                return v
        for v in obj.values():
            got = deep_find(v, names, max_depth - 1)
            if got is not None:
                return got
    elif isinstance(obj, list):
        for v in obj[:250]:
            got = deep_find(v, names, max_depth - 1)
            if got is not None:
                return got
    return None


def locate_payload(key: str, aggregates: dict[str, Any]) -> tuple[Any | None, str | None]:
    names = {p.split(".")[-1].lower() for p in SEARCH_PATHS.get(key, [])}
    for source_name, data in aggregates.items():
        for path in SEARCH_PATHS.get(key, []):
            direct = get_path(data, path)
            if direct is not None:
                return direct, source_name
        got = deep_find(data, names)
        if got is not None:
            return got, source_name
    return None, None


def explicit_freshness(obj: Any) -> str | None:
    if isinstance(obj, dict):
        v = str(obj.get("freshness") or obj.get("data_freshness") or obj.get("status") or obj.get("overall_status") or "").upper()
        if v in {"MISSING", "ERROR", "STALE", "LIVE", "PASS", "DEGRADED"}:
            if v == "PASS":
                return "LIVE"
            return v
    return None

def is_effective_missing(obj: Any) -> bool:
    """True when a direct file exists but is only a placeholder or empty shell.

    This prevents old normalizer placeholders from masking useful aggregate data.
    """
    if obj is None:
        return True
    if isinstance(obj, list):
        return len(obj) == 0
    if not isinstance(obj, dict):
        return False
    if obj.get("_placeholder") is True:
        return True
    if str(obj.get("freshness") or obj.get("status") or "").upper() == "MISSING":
        # If payload is empty/missing, this is not a real observation.
        payload = obj.get("payload", None)
        if payload in (None, {}, []):
            return True
        # Common placeholder form: status=MISSING plus only metadata fields.
        meaningful = [k for k, v in obj.items() if not str(k).startswith("_") and k not in {"freshness", "status", "timestamp_utc", "data_age_seconds", "source_timestamp_utc", "timestamp_provenance", "payload"} and v not in (None, "", {}, [])]
        return len(meaningful) == 0
    return len(obj) == 0


def enrich_payload_for_dashboard(payload: Any, contract: dict[str, Any], placeholder: bool) -> Any:
    """Inject the dashboard surface contract into the payload itself.

    The HTML unwraps surface files before rendering cards. Without this injection,
    card freshness can fall back to MISSING even when the surface wrapper is valid.
    """
    meta = {
        "timestamp_utc": contract.get("timestamp_utc"),
        "freshness": contract.get("freshness"),
        "data_age_seconds": contract.get("data_age_seconds"),
        "timestamp_provenance": contract.get("timestamp_provenance"),
        "_dashboard_surface_meta": {
            "contract": contract.get("_powerflow_contract"),
            "normalized_at_utc": contract.get("_normalized_at_utc"),
            "raw_source": contract.get("_raw_source"),
            "raw_path": contract.get("_raw_path"),
            "placeholder": placeholder,
        },
    }
    if placeholder:
        return {"status": "MISSING", "reason": "no direct or aggregate payload found", **meta}
    if isinstance(payload, dict):
        enriched = dict(payload)
        # Do not overwrite source fields if they exist; add contract defaults only.
        for k, v in meta.items():
            enriched.setdefault(k, v)
        return enriched
    if isinstance(payload, list):
        return {"items": payload, **meta}
    return {"value": payload, **meta}


def classify_payload(payload: Any, stale_seconds: int, placeholder: bool) -> tuple[str, int | None, str | None, str]:
    if placeholder:
        return "MISSING", None, None, "missing_placeholder"
    explicit = explicit_freshness(payload)
    stamps = find_timestamps(payload)
    now = datetime.now(timezone.utc)
    ages: list[tuple[int, str]] = []
    for stamp in stamps:
        dt = parse_iso(stamp)
        if dt:
            ages.append((max(0, int((now - dt).total_seconds())), stamp))
    if ages:
        age, stamp = min(ages, key=lambda x: x[0])
        return ("LIVE" if age <= stale_seconds else "STALE"), age, stamp, "source"
    if explicit in {"MISSING", "ERROR", "STALE", "LIVE"}:
        return explicit, None, None, "explicit_no_timestamp"
    # Data exists but source timestamp is absent. This is useful data, but not fully contract-clean.
    return "DEGRADED", None, None, "normalizer_generated"


def wrap_surface(key: str, payload: Any, raw_source: str | None, stale_seconds: int, placeholder: bool, raw_path: str | None) -> dict[str, Any]:
    normalized_at = utc_now()
    freshness, age, source_ts, provenance = classify_payload(payload, stale_seconds, placeholder)
    contract_ts = source_ts or normalized_at
    contract = {
        "_powerflow_contract": "V7.2_DASHBOARD_SURFACE",
        "_normalized_by": "dashboard_data_normalizer_v04.py",
        "_normalized_at_utc": normalized_at,
        "_source_key": key,
        "_raw_source": raw_source,
        "_raw_path": raw_path,
        "_placeholder": placeholder,
        "freshness": freshness,
        "data_age_seconds": age if age is not None else 0,
        "timestamp_utc": contract_ts,
        "source_timestamp_utc": source_ts,
        "timestamp_provenance": provenance,
    }
    contract["payload"] = enrich_payload_for_dashboard(payload, contract, placeholder)
    return contract


def main() -> int:
    parser = argparse.ArgumentParser(description="Build PowerFlow V7.2 dashboard surface wrappers.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--surface-dir", default="output/dashboard_surface")
    parser.add_argument("--stale-seconds", type=int, default=180)
    parser.add_argument("--summary-out", default="output/dashboard_normalizer_report.json")
    parser.add_argument("--md-out", default="output/DASHBOARD_NORMALIZER_REPORT.md")
    args = parser.parse_args()

    root = Path(args.root)
    surface_dir = root / args.surface_dir
    surface_dir.mkdir(parents=True, exist_ok=True)
    (root / "output").mkdir(parents=True, exist_ok=True)

    aggregates: dict[str, Any] = {}
    aggregate_status: dict[str, str] = {}
    for name, rel in AGGREGATE_SOURCES.items():
        ok, data, err = load_json(root / rel)
        if ok:
            aggregates[name] = data
            aggregate_status[name] = "READ"
        else:
            aggregate_status[name] = err or "ERROR"

    records: list[SurfaceRecord] = []
    for key, rel in DIRECT_TARGETS.items():
        raw_path = root / rel
        ok, data, err = load_json(raw_path)
        if ok and not is_effective_missing(data):
            wrapped = wrap_surface(key, data, "direct", args.stale_seconds, placeholder=False, raw_path=rel)
            action = "WRAPPED_DIRECT"
            reason = "raw direct output preserved and exposed through dashboard surface"
        else:
            payload, source_name = locate_payload(key, aggregates)
            if payload is None or is_effective_missing(payload):
                wrapped = wrap_surface(key, {}, None, args.stale_seconds, placeholder=True, raw_path=rel)
                action = "PLACEHOLDER_MISSING" if not ok else "DIRECT_PLACEHOLDER_NO_AGGREGATE"
                reason = "no direct or aggregate payload found" if not ok else "direct output was placeholder and no aggregate payload was found"
            else:
                wrapped = wrap_surface(key, payload, source_name, args.stale_seconds, placeholder=False, raw_path=None)
                action = "WRAPPED_AGGREGATE" if not ok else "DIRECT_PLACEHOLDER_REPLACED_BY_AGGREGATE"
                reason = "derived from aggregate output" if not ok else "direct placeholder ignored; aggregate payload exposed"
        out = surface_dir / f"{key}.json"
        out.write_text(json.dumps(wrapped, indent=2, ensure_ascii=False), encoding="utf-8")
        records.append(SurfaceRecord(
            key=key,
            surface_path=str(out.relative_to(root)),
            action=action,
            freshness=str(wrapped.get("freshness")),
            source=wrapped.get("_raw_source"),
            timestamp_provenance=str(wrapped.get("timestamp_provenance")),
            reason=reason,
        ))

    summary = {
        "generated_at_utc": utc_now(),
        "stale_seconds": args.stale_seconds,
        "surface_dir": args.surface_dir,
        "aggregate_status": aggregate_status,
        "records": [asdict(r) for r in records],
        "doctrine": {
            "no_b1_fusion": True,
            "no_b4_fusion": True,
            "raw_outputs_preserved": True,
            "missing_explicit": True,
            "no_db_write": True,
            "no_pf_imports": True,
        },
    }

    summary_path = root / args.summary_out
    summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = [
        "# DASHBOARD DATA NORMALIZER REPORT — PowerFlow V7.2",
        "",
        f"Generated UTC : {summary['generated_at_utc']}",
        f"Surface directory : {args.surface_dir}",
        "Raw direct outputs overwritten : False",
        "",
        "## Doctrine",
        "- No B1/B1+ fusion.",
        "- No B4/B4+ fusion.",
        "- Raw outputs preserved; dashboard reads wrapped surface.",
        "- Missing data is explicit.",
        "- Timestamp provenance is explicit.",
        "- Direct placeholders cannot mask aggregate observations.",
        "- Surface contract fields are injected into payload for card freshness.",
        "- No DB write. No pf_* imports.",
        "",
        "## Aggregate Sources",
        "",
        "| Source | Status |",
        "|---|---|",
    ]
    for name, status in aggregate_status.items():
        lines.append(f"| {name} | {status} |")
    lines.extend(["", "## Surface Records", "", "| Key | Action | Freshness | Timestamp provenance | Source | Path |", "|---|---|---|---|---|---|"])
    for r in records:
        lines.append(f"| {r.key} | {r.action} | {r.freshness} | {r.timestamp_provenance} | {r.source or '-'} | {r.surface_path} |")
    (root / args.md_out).write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Dashboard surface normalization complete: {len(records)} records")
    print(f"Surface: {surface_dir}")
    print(f"JSON: {summary_path}")
    print(f"MD:   {root / args.md_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
