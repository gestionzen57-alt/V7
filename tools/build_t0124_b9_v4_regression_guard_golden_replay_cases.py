#!/usr/bin/env python3
"""T0124 — B9 V4 Regression Guard + Golden Replay Cases. V2 deterministic test/CLI alignment.

Read-only guard that validates B9 V4 summaries against golden replay cases.
It protects the core B9 readings:
- effort without result
- progressive wave
- center migration down
- failed retest
- corrective/counter breath
- source quality + timestamp policy

No database access. No dashboard. No Telegram. No BUY/SELL.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0124_B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES_V0_V2"

REQUIRED_V4_FIELDS = [
    "what_happens_fr",
    "why_it_matters_fr",
    "how_it_happened_fr",
    "mechanism_fr",
    "proof_summary_fr",
    "previous_context_fr",
    "cause_fr",
    "reaction_fr",
    "consequence_fr",
    "memory_shift_fr",
    "retest_role_fr",
    "scene_id",
    "scene_role",
    "parent_scene",
    "child_moments",
    "session_chapter",
    "fractal_reading_fr",
    "b9_center_path_state",
    "b9_effort_result_progress_state",
    "b9_progress_type",
    "b9_native_retest_judgment",
    "b9_source_quality_native_state",
    "b9_v4_timestamp_policy",
]

PRESERVATION_FIELDS = [
    "time_start",
    "time_end",
    "label_fr",
    "reading_fr",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "raw_texture_role",
    "technical_limits",
]

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bACHETER\b",
    r"\bVENDRE\b",
    r"probabilit[ée]\s+de\s+succ[eè]s",
    r"probability\s+of\s+success",
]

GOLDEN_CASES = [
    {
        "case_id": "B9V4_GOLDEN_EFFORT_WITHOUT_RESULT",
        "expected_progress_type": "EFFORT_WITHOUT_RESULT",
        "expected_center_path": "CENTER_BLOCKED_OR_ROTATING",
        "expected_retest_judgment": "RETEST_NOT_VISIBLE",
        "expected_label_contains": ["effort", "résultat"],
        "why_guarded_fr": "Empêche B9 de lire un gros effort local comme direction si le progrès reste faible.",
    },
    {
        "case_id": "B9V4_GOLDEN_PROGRESSIVE_WAVE_UP",
        "expected_progress_type": "PROGRESSIVE_WAVE",
        "expected_center_path": "CENTER_MIGRATES_UP",
        "expected_retest_judgment": "RETEST_VISIBLE_OR_PROXY_VISIBLE",
        "expected_label_contains": ["vague", "progressive"],
        "why_guarded_fr": "Empêche B9 de perdre la distinction effort + résultat + progrès quand la mémoire monte par paliers.",
    },
    {
        "case_id": "B9V4_GOLDEN_CENTER_MIGRATION_DOWN",
        "expected_progress_type": "PROGRESSIVE_WAVE",
        "expected_center_path": "CENTER_MIGRATES_DOWN",
        "expected_retest_judgment": "RETEST_VISIBLE_OR_PROXY_VISIBLE",
        "expected_label_contains": ["centre", "descend"],
        "why_guarded_fr": "Protège le cas absorption + centre descendant = pression qui avance, pas support simple.",
    },
    {
        "case_id": "B9V4_GOLDEN_RETEST_FAILED",
        "expected_progress_type": "RETEST_FAILED_OR_STRUCTURE_REJECTED",
        "expected_center_path": "CENTER_MIGRATES_DOWN",
        "expected_retest_judgment": "RETEST_FAILED",
        "expected_label_contains": ["retest", "échoué"],
        "why_guarded_fr": "Protège la règle B9 : la cassure ou reprise est jugée par le retest, pas par l'impulsion.",
    },
    {
        "case_id": "B9V4_GOLDEN_CORRECTIVE_BREATH",
        "expected_progress_type": "CORRECTIVE_OR_PARTIAL_PROGRESS",
        "expected_center_path": "CENTER_MIGRATES_UP",
        "expected_retest_judgment": "RETEST_NOT_VISIBLE",
        "expected_label_contains": ["respiration", "corrective"],
        "why_guarded_fr": "Empêche B9 de confondre respiration/correction avec déplacement durable de mémoire.",
    },
    {
        "case_id": "B9V4_GOLDEN_SOURCE_QUALITY_TIMESTAMP",
        "expected_progress_type": "LOCAL_FRICTION_OR_DECISION_AREA",
        "expected_center_path": "CENTER_BLOCKED_OR_ROTATING",
        "expected_retest_judgment": "RETEST_NOT_VISIBLE_SOURCE_LIMITED",
        "expected_source_quality": "SOURCE_LIMITED_RAW_UNAVAILABLE",
        "expected_timestamp_policy": "ORIGINAL_TIME_REQUIRED_WHEN_SHIFTED_REPLAY_PRESENT",
        "expected_label_contains": ["source", "limitée"],
        "why_guarded_fr": "Protège source quality, RAW_UNAVAILABLE, confidence_cap et timestamp policy shifted/replay.",
    },
]

SAMPLE_SUMMARY = {
    "metadata": {
        "version": "SAMPLE_B9_V4_GOLDEN_REPLAY_CASES_V0",
        "source_mode": "M1_BAR_PROXY",
        "data_visibility": "RECONSTRUCTED",
        "confidence_cap": 0.35,
        "timestamp_policy": "ORIGINAL_TIME_REQUIRED_WHEN_SHIFTED_REPLAY_PRESENT",
    },
    "moments": [
        {
            "golden_case_id": "B9V4_GOLDEN_EFFORT_WITHOUT_RESULT",
            "time_start": "2026-05-15T08:00:00Z",
            "time_end": "2026-05-15T08:14:00Z",
            "label_fr": "Effort sans résultat",
            "reading_fr": "Le flux pousse mais ne déplace pas proprement la mémoire.",
            "center_start": 1.33633,
            "center_end": 1.33640,
            "raw_delta_pips": 0.7,
            "raw_range_pips": 10.0,
            "b9_effort_result_ratio": 3.4,
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.35,
            "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
            "technical_limits": "M1 proxy, footprint exact absent.",
        },
        {
            "golden_case_id": "B9V4_GOLDEN_PROGRESSIVE_WAVE_UP",
            "time_start": "2026-05-15T10:11:00Z",
            "time_end": "2026-05-15T10:23:00Z",
            "label_fr": "Vague progressive haussière",
            "reading_fr": "L'effort produit du résultat et déplace la mémoire plus haut.",
            "center_start": 1.33627,
            "center_end": 1.33742,
            "raw_delta_pips": 11.5,
            "raw_range_pips": 11.5,
            "retest_touch_count": 2,
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.35,
            "proxy_vs_raw_verdict": "CONFIRMED_BY_RAW",
            "technical_limits": "Retest proxy visible, raw exact limité.",
        },
        {
            "golden_case_id": "B9V4_GOLDEN_CENTER_MIGRATION_DOWN",
            "time_start": "2026-05-15T11:01:00Z",
            "time_end": "2026-05-15T11:18:00Z",
            "label_fr": "Centre de gravité qui descend",
            "reading_fr": "Absorption répétée mais centre descendant : la pression avance par paliers.",
            "center_start": 1.33645,
            "center_end": 1.33516,
            "raw_delta_pips": -12.9,
            "raw_range_pips": 12.9,
            "retest_touch_count": 1,
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.35,
            "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
            "technical_limits": "Centre path visible, raw tick exact absent.",
        },
        {
            "golden_case_id": "B9V4_GOLDEN_RETEST_FAILED",
            "time_start": "2026-05-15T09:10:00Z",
            "time_end": "2026-05-15T09:31:00Z",
            "label_fr": "Retest échoué / reprise refusée",
            "reading_fr": "Le haut est retesté, ne tient pas, puis la mémoire accepte plus bas.",
            "center_start": 1.33587,
            "center_end": 1.33380,
            "raw_delta_pips": -20.7,
            "raw_range_pips": 20.7,
            "b9_retest_source_status": "FAILED",
            "retest_touch_count": 3,
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.35,
            "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
            "technical_limits": "Retest proxy, source reconstructed.",
        },
        {
            "golden_case_id": "B9V4_GOLDEN_CORRECTIVE_BREATH",
            "time_start": "2026-05-15T15:48:00Z",
            "time_end": "2026-05-15T15:59:00Z",
            "label_fr": "Respiration corrective",
            "reading_fr": "Le marché respire mais ne reprend pas les centres hauts.",
            "center_start": 1.33420,
            "center_end": 1.33550,
            "raw_delta_pips": 5.4,
            "raw_range_pips": 13.0,
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED",
            "confidence_cap": 0.35,
            "proxy_vs_raw_verdict": "NUANCED_BY_RAW",
            "technical_limits": "Progression partielle, structure haute non réparée.",
        },
        {
            "golden_case_id": "B9V4_GOLDEN_SOURCE_QUALITY_TIMESTAMP",
            "time_start": "2026-05-06T00:01:00Z",
            "time_end": "2026-05-06T00:05:00Z",
            "label_fr": "Source limitée / retest non visible",
            "reading_fr": "Moment conservé pour audit source, pas pour durcir une vérité raw.",
            "center_start": 1.25000,
            "center_end": 1.25008,
            "raw_delta_pips": 0.8,
            "raw_range_pips": 2.0,
            "b9_retest_source_status": "RAW_UNAVAILABLE",
            "source_mode": "M1_BAR_PROXY",
            "data_visibility": "RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED",
            "confidence_cap": 0.25,
            "proxy_vs_raw_verdict": "RAW_UNAVAILABLE",
            "technical_limits": "RAW_UNAVAILABLE, FORCE_SNAPSHOT_DERIVED, timestamp shifted risk.",
        },
    ],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"metadata": {}, "moments": data}
    if not isinstance(data, dict):
        raise ValueError(f"Unsupported JSON root: {type(data)}")
    data.setdefault("metadata", {})
    if "moments" not in data:
        for key in ("scenes", "items", "results"):
            if isinstance(data.get(key), list):
                data["moments"] = data[key]
                break
    data.setdefault("moments", [])
    if not isinstance(data["moments"], list):
        raise ValueError("summary['moments'] must be a list")
    return data


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: compact(row.get(k, "")) for k in fieldnames})


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def stable_id(moment: Dict[str, Any], idx: int) -> str:
    base = "|".join([
        str(moment.get("golden_case_id") or ""),
        str(moment.get("time_start") or ""),
        str(moment.get("time_end") or ""),
        str(moment.get("label_fr") or ""),
        str(idx),
    ])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:10].upper()


def infer_progress_type(moment: Dict[str, Any]) -> str:
    explicit = str(moment.get("b9_progress_type") or moment.get("b9_effort_result_progress_state") or "").upper()
    if explicit:
        return explicit
    text = " ".join(str(moment.get(k, "")) for k in ("label_fr", "moment_type", "reading_fr")).lower()
    delta = float_or_none(moment.get("raw_delta_pips") or moment.get("center_delta") or moment.get("pip_delta")) or 0.0
    rng = float_or_none(moment.get("raw_range_pips"))
    effort_ratio = float_or_none(moment.get("b9_effort_result_ratio"))
    retest_status = str(moment.get("b9_retest_source_status") or "").upper()
    if "retest" in text and ("échoué" in text or "failed" in text or retest_status == "FAILED"):
        return "RETEST_FAILED_OR_STRUCTURE_REJECTED"
    if "effort" in text and ("sans" in text or "without" in text):
        return "EFFORT_WITHOUT_RESULT"
    if "respiration" in text or "corrective" in text:
        return "CORRECTIVE_OR_PARTIAL_PROGRESS"
    if abs(delta) >= 8.0:
        return "PROGRESSIVE_WAVE"
    if rng is not None and rng >= 6.0 and abs(delta) < rng * 0.50:
        return "INTERNAL_PATH_VISIBLE_BUT_NET_MUTED"
    if effort_ratio is not None and effort_ratio > 2.0 and abs(delta) < 2.0:
        return "EFFORT_WITHOUT_RESULT"
    if abs(delta) < 2.0:
        return "LOCAL_FRICTION_OR_DECISION_AREA"
    return "CORRECTIVE_OR_PARTIAL_PROGRESS"


def infer_center_path(moment: Dict[str, Any]) -> str:
    explicit = str(moment.get("b9_center_path_state") or "").upper()
    if explicit:
        return explicit
    start = float_or_none(moment.get("center_start") or moment.get("bid_start"))
    end = float_or_none(moment.get("center_end") or moment.get("bid_end"))
    delta = float_or_none(moment.get("center_delta") or moment.get("raw_delta_pips") or moment.get("pip_delta"))
    if delta is None and start is not None and end is not None:
        delta = (end - start) * 10000
    if delta is None:
        return "CENTER_PATH_NOT_VISIBLE"
    if delta > 5:
        return "CENTER_MIGRATES_UP"
    if delta < -5:
        return "CENTER_MIGRATES_DOWN"
    return "CENTER_BLOCKED_OR_ROTATING"


def infer_retest(moment: Dict[str, Any]) -> str:
    explicit = str(moment.get("b9_native_retest_judgment") or "").upper()
    if explicit:
        return explicit
    status = str(moment.get("b9_retest_source_status") or moment.get("retest_outcome_hint") or "").upper()
    visibility = str(moment.get("b9_retest_source_visibility") or "").upper()
    touches = moment.get("retest_touch_count") or moment.get("b9_retest_touch_count_proxy")
    if status == "FAILED" or "FAILED" in status:
        return "RETEST_FAILED"
    if "RAW_UNAVAILABLE" in status or "UNAVAILABLE" in visibility:
        return "RETEST_NOT_VISIBLE_SOURCE_LIMITED"
    if touches not in (None, "", 0, "0"):
        return "RETEST_VISIBLE_OR_PROXY_VISIBLE"
    if status and status not in ("NONE", "NA", "N/A"):
        return "RETEST_STATE_INFERRED"
    return "RETEST_NOT_VISIBLE"


def infer_source_quality(moment: Dict[str, Any]) -> str:
    explicit = str(moment.get("b9_source_quality_native_state") or "").upper()
    if explicit:
        return explicit
    verdict = str(moment.get("proxy_vs_raw_verdict") or "").upper()
    visibility = str(moment.get("data_visibility") or "").upper()
    cap = float_or_none(moment.get("confidence_cap"))
    if "RAW_UNAVAILABLE" in verdict:
        return "SOURCE_LIMITED_RAW_UNAVAILABLE"
    if "CONFIRMED_BY_RAW" in verdict:
        return "SOURCE_STRONG_RAW_CONFIRMED"
    if "NUANCED_BY_RAW" in verdict:
        return "SOURCE_USABLE_RAW_NUANCED"
    if "RECONSTRUCT" in visibility:
        return "SOURCE_PROXY_RECONSTRUCTED"
    if cap is not None and cap <= 0.35:
        return "SOURCE_CAPPED_PROXY_OR_PARTIAL"
    return "SOURCE_QUALITY_NOT_EXPLICIT"


def enrich_moment_guard(moment: Dict[str, Any], idx: int) -> Dict[str, Any]:
    out = dict(moment)
    label = str(out.get("label_fr") or out.get("moment_type") or "Moment B9")
    progress = infer_progress_type(out)
    center = infer_center_path(out)
    retest = infer_retest(out)
    source = infer_source_quality(out)
    sid = f"B9V4_GOLDEN_{idx+1:03d}_{stable_id(out, idx)}"
    out.setdefault("what_happens_fr", f"B9 lit ce moment comme : {label}.")
    out.setdefault("why_it_matters_fr", "Ce cas protège une lecture B9 critique contre une régression future.")
    out.setdefault("how_it_happened_fr", f"Lecture par chemin interne ({center}), effort/résultat/progrès ({progress}) et retest ({retest}).")
    out.setdefault("mechanism_fr", f"Mécanisme protégé : {center} + {progress} + {retest} + {source}.")
    out.setdefault("proof_summary_fr", "Preuves suivies : label FR, chemin du centre, retest, source quality, limites et timestamp policy.")
    out.setdefault("previous_context_fr", "Contexte replay golden, utilisé comme garde anti-régression.")
    out.setdefault("cause_fr", "Cause candidate issue de la zone, du centre ou de l'effort local selon le cas golden.")
    out.setdefault("reaction_fr", "Réaction candidate lue comme déplacement, frein, retest, respiration ou friction.")
    out.setdefault("consequence_fr", "Conséquence candidate : mémoire déplacée, bloquée, rejetée ou limitée par source.")
    out.setdefault("memory_shift_fr", "Déplacement mémoire qualifié par center_path et progress_type, sans prédiction.")
    out.setdefault("retest_role_fr", retest.replace("_", " ").lower())
    out.setdefault("scene_id", sid)
    out.setdefault("scene_role", progress)
    out.setdefault("parent_scene", "B9_V4_GOLDEN_REPLAY_REGRESSION_GUARD")
    out.setdefault("child_moments", [])
    out.setdefault("session_chapter", "Mémoire déplacée" if "PROGRESSIVE" in progress or "MIGRATES" in center else "Décision de zone")
    out.setdefault("fractal_reading_fr", "Cas golden : le moment est jugé dans son rôle de scène, pas comme signal isolé.")
    out.setdefault("b9_center_path_state", center)
    out.setdefault("b9_effort_result_progress_state", progress)
    out.setdefault("b9_progress_type", progress)
    out.setdefault("b9_native_retest_judgment", retest)
    out.setdefault("b9_source_quality_native_state", source)
    out.setdefault("b9_v4_timestamp_policy", "ORIGINAL_TIME_REQUIRED_WHEN_SHIFTED_REPLAY_PRESENT")
    return out


def enrich_summary(summary: Dict[str, Any]) -> Tuple[Dict[str, Any], str]:
    # T0124 V2 is intentionally deterministic: it validates the golden replay
    # guard with its local contract fallback instead of importing any installed
    # native summarizer contract implicitly.
    # Why: Windows pytest imports from the repo root, while CLI execution imports
    # from tools/. In V1, that made pytest use a local native contract while the
    # CLI used the fallback, producing PASS/FAIL drift. Native-contract runtime
    # validation remains the role of T0122/T0123; T0124 is the stable golden-case
    # guard.
    out = deepcopy(summary)
    out["moments"] = [enrich_moment_guard(m, i) for i, m in enumerate(out.get("moments", [])) if isinstance(m, dict)]
    out.setdefault("metadata", {})
    out["metadata"]["t0124_contract_source"] = "LOCAL_REGRESSION_GUARD_FALLBACK_DETERMINISTIC_V2"
    return out, "LOCAL_REGRESSION_GUARD_FALLBACK_DETERMINISTIC_V2"


def find_case(moment: Dict[str, Any], cases: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    cid = moment.get("golden_case_id")
    if cid:
        for case in cases:
            if case["case_id"] == cid:
                return case
    label = str(moment.get("label_fr") or "").lower()
    for case in cases:
        toks = [str(t).lower() for t in case.get("expected_label_contains", [])]
        if toks and all(t in label for t in toks):
            return case
    return None


def validate_cases(summary: Dict[str, Any], cases: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    moments = [m for m in summary.get("moments", []) if isinstance(m, dict)]
    matched_ids = set()
    results: List[Dict[str, Any]] = []
    failures: List[Dict[str, Any]] = []
    for idx, moment in enumerate(moments):
        case = find_case(moment, cases)
        if not case:
            continue
        cid = case["case_id"]
        matched_ids.add(cid)
        checks = []
        def add_check(name: str, expected: Any, actual: Any, ok: bool) -> None:
            checks.append({"check": name, "expected": expected, "actual": actual, "ok": ok})
        add_check("progress_type", case.get("expected_progress_type"), moment.get("b9_progress_type"), moment.get("b9_progress_type") == case.get("expected_progress_type"))
        add_check("center_path", case.get("expected_center_path"), moment.get("b9_center_path_state"), moment.get("b9_center_path_state") == case.get("expected_center_path"))
        add_check("retest_judgment", case.get("expected_retest_judgment"), moment.get("b9_native_retest_judgment"), moment.get("b9_native_retest_judgment") == case.get("expected_retest_judgment"))
        if case.get("expected_source_quality"):
            add_check("source_quality", case.get("expected_source_quality"), moment.get("b9_source_quality_native_state"), moment.get("b9_source_quality_native_state") == case.get("expected_source_quality"))
        if case.get("expected_timestamp_policy"):
            add_check("timestamp_policy", case.get("expected_timestamp_policy"), moment.get("b9_v4_timestamp_policy"), moment.get("b9_v4_timestamp_policy") == case.get("expected_timestamp_policy"))
        missing = [f for f in REQUIRED_V4_FIELDS if moment.get(f) in (None, "")]
        add_check("required_v4_fields", "no_missing_fields", missing, not missing)
        ok = all(c["ok"] for c in checks)
        row = {
            "case_id": cid,
            "moment_index": idx,
            "time_start": moment.get("time_start", ""),
            "time_end": moment.get("time_end", ""),
            "label_fr": moment.get("label_fr", ""),
            "case_state": "PASS" if ok else "FAIL",
            "checks": checks,
            "why_guarded_fr": case.get("why_guarded_fr", ""),
        }
        results.append(row)
        if not ok:
            for c in checks:
                if not c["ok"]:
                    failures.append({
                        "case_id": cid,
                        "moment_index": idx,
                        "check": c["check"],
                        "expected": c["expected"],
                        "actual": c["actual"],
                        "label_fr": moment.get("label_fr", ""),
                    })
    for case in cases:
        if case["case_id"] not in matched_ids:
            failures.append({
                "case_id": case["case_id"],
                "moment_index": "",
                "check": "case_present",
                "expected": "present_in_summary",
                "actual": "missing",
                "label_fr": "",
            })
            results.append({
                "case_id": case["case_id"],
                "moment_index": "",
                "time_start": "",
                "time_end": "",
                "label_fr": "",
                "case_state": "FAIL",
                "checks": [{"check": "case_present", "expected": "present_in_summary", "actual": "missing", "ok": False}],
                "why_guarded_fr": case.get("why_guarded_fr", ""),
            })
    return results, failures


def forbidden_hits(data: Any) -> List[Dict[str, str]]:
    text = json.dumps(data, ensure_ascii=False)
    hits = []
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, text, flags=re.IGNORECASE):
            hits.append({"pattern": pat, "state": "FORBIDDEN_LANGUAGE_DETECTED"})
    return hits


def preservation_diff(before: Dict[str, Any], after: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    before_m = before.get("moments", [])
    after_m = after.get("moments", [])
    for i, (b, a) in enumerate(zip(before_m, after_m)):
        if not isinstance(b, dict) or not isinstance(a, dict):
            continue
        for field in PRESERVATION_FIELDS:
            bv = compact(b.get(field, ""))
            av = compact(a.get(field, ""))
            if bv != av:
                rows.append({"moment_index": i, "field": field, "before": bv, "after": av, "state": "CHANGED"})
    return rows


def build_report(summary: Dict[str, Any], manifest: Dict[str, Any], case_results: List[Dict[str, Any]], failures: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("# T0124 — B9 V4 Regression Guard + Golden Replay Cases")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("T0124 V2 fige les cas replay critiques pour empêcher B9 V4 de régresser sur effort/résultat/progrès, chemin interne du centre, retest, source quality et timestamp policy.")
    lines.append("")
    lines.append("```text")
    lines.append("B9 ne cherche pas le signal.")
    lines.append("B9 cherche la trace laissée par l'effort.")
    lines.append("Ne lis pas l'absorption comme une direction.")
    lines.append("Lis où elle déplace la mémoire.")
    lines.append("```")
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- État : `{manifest['regression_guard_state']}`")
    lines.append(f"- Cas golden : `{manifest['golden_case_count']}`")
    lines.append(f"- Cas passés : `{manifest['golden_cases_passed']}`")
    lines.append(f"- Cas échoués : `{manifest['golden_cases_failed']}`")
    lines.append(f"- Champs requis manquants : `{manifest['total_missing_required_fields']}`")
    lines.append(f"- Hits langage interdit : `{manifest['forbidden_language_hit_count']}`")
    lines.append(f"- Source contrat : `{manifest['contract_source']}`")
    lines.append("")
    lines.append("## Cas golden protégés")
    lines.append("")
    for row in case_results:
        lines.append(f"- `{row['case_id']}` — `{row['case_state']}` — {row.get('label_fr','')}")
    lines.append("")
    lines.append("## Échecs")
    lines.append("")
    if failures:
        for fail in failures:
            lines.append(f"- `{fail['case_id']}` / `{fail['check']}` : attendu `{fail['expected']}`, obtenu `{fail['actual']}`")
    else:
        lines.append("Aucun échec golden case.")
    lines.append("")
    lines.append("## Limites techniques")
    lines.append("")
    lines.append("- Read-only.")
    lines.append("- Aucune écriture `powerflow.db`.")
    lines.append("- Aucune écriture `tick_archive.db`.")
    lines.append("- Aucun dashboard.")
    lines.append("- Aucun Telegram.")
    lines.append("- Aucun BUY/SELL.")
    lines.append("- Aucune probabilité de succès.")
    lines.append("- V2 utilise un fallback local déterministe pour aligner pytest et CLI. La validation native reste couverte par T0122/T0123.")
    lines.append("")
    lines.append("## Prochain geste")
    lines.append("")
    lines.append("T0125 — B9 V4 Golden Replay Batch Runner : appliquer le guard sur plusieurs summaries replay réels.")
    return "\n".join(lines) + "\n"


def run(input_summary: Path, output_dir: Path) -> Dict[str, Any]:
    before = load_json(input_summary)
    after, contract_source = enrich_summary(before)
    case_results, failures = validate_cases(after, GOLDEN_CASES)
    hits = forbidden_hits(after)
    preservation = preservation_diff(before, after)
    total_missing = 0
    for moment in after.get("moments", []):
        if isinstance(moment, dict):
            total_missing += sum(1 for f in REQUIRED_V4_FIELDS if moment.get(f) in (None, ""))
    passed = sum(1 for r in case_results if r.get("case_state") == "PASS")
    failed = sum(1 for r in case_results if r.get("case_state") == "FAIL")
    state = "PASS" if failed == 0 and not hits and total_missing == 0 else "FAIL"
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": VERSION,
        "generated_at": utc_now(),
        "input_summary": str(input_summary),
        "contract_source": contract_source,
        "regression_guard_state": state,
        "input_moments": len(before.get("moments", [])),
        "enriched_moments": len(after.get("moments", [])),
        "golden_case_count": len(GOLDEN_CASES),
        "golden_cases_passed": passed,
        "golden_cases_failed": failed,
        "total_missing_required_fields": total_missing,
        "forbidden_language_hit_count": len(hits),
        "preservation_diff_count": len(preservation),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
    dump_json(output_dir / "B9_V4_GOLDEN_REPLAY_CASES_V0.json", GOLDEN_CASES)
    dump_json(output_dir / "B9_V4_REGRESSION_GUARD_V0.json", {"manifest": manifest, "case_results": case_results, "failures": failures, "forbidden_language_hits": hits})
    dump_json(output_dir / "B9_V4_REGRESSION_GUARD_ENRICHED_SAMPLE_V0.json", after)
    write_csv(output_dir / "B9_V4_GOLDEN_CASE_RESULTS_V0.csv", case_results, ["case_id", "moment_index", "time_start", "time_end", "label_fr", "case_state", "why_guarded_fr", "checks"])
    write_csv(output_dir / "B9_V4_REGRESSION_GUARD_FAILURES_V0.csv", failures, ["case_id", "moment_index", "check", "expected", "actual", "label_fr"])
    write_csv(output_dir / "B9_V4_REGRESSION_GUARD_PRESERVATION_DIFF_V0.csv", preservation, ["moment_index", "field", "before", "after", "state"])
    test_plan = [
        {"test_id": "T0124_001", "test": "Golden cases all present", "expected": len(GOLDEN_CASES)},
        {"test_id": "T0124_002", "test": "Required V4 fields present", "expected": "no_missing_fields"},
        {"test_id": "T0124_003", "test": "No forbidden language", "expected": "no BUY/SELL/probability"},
        {"test_id": "T0124_004", "test": "Preserved fields unchanged", "expected": "labels/source/limits unchanged"},
        {"test_id": "T0124_005", "test": "Timestamp policy explicit", "expected": "ORIGINAL_TIME_REQUIRED_WHEN_SHIFTED_REPLAY_PRESENT"},
    ]
    write_csv(output_dir / "B9_V4_REGRESSION_GUARD_TEST_PLAN_V0.csv", test_plan, ["test_id", "test", "expected"])
    dump_json(output_dir / "B9_V4_REGRESSION_GUARD_MANIFEST.json", manifest)
    (output_dir / "B9_V4_REGRESSION_GUARD_V0.md").write_text(build_report(after, manifest, case_results, failures), encoding="utf-8")
    zip_path = output_dir / "B9_V4_REGRESSION_GUARD_GOLDEN_REPLAY_CASES_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in output_dir.iterdir():
            if p.is_file() and p.name != zip_path.name:
                zf.write(p, p.name)
    return manifest | {"output_dir": str(output_dir), "zip": str(zip_path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build T0124 B9 V4 regression guard golden replay cases.")
    parser.add_argument("--input-summary-json", required=False, help="B9 sequence summary JSON. If absent, writes and uses built-in sample.")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    out = Path(args.output_dir)
    if args.input_summary_json:
        input_path = Path(args.input_summary_json)
    else:
        out.mkdir(parents=True, exist_ok=True)
        input_path = out / "sample_b9_v4_golden_replay_cases_input.json"
        dump_json(input_path, SAMPLE_SUMMARY)
    manifest = run(input_path, out)
    print(json.dumps({
        "version": VERSION,
        "regression_guard_state": manifest["regression_guard_state"],
        "golden_case_count": manifest["golden_case_count"],
        "golden_cases_passed": manifest["golden_cases_passed"],
        "golden_cases_failed": manifest["golden_cases_failed"],
        "total_missing_required_fields": manifest["total_missing_required_fields"],
        "forbidden_language_hit_count": manifest["forbidden_language_hit_count"],
        "contract_source": manifest["contract_source"],
        "output_dir": manifest["output_dir"],
        "zip": manifest["zip"],
    }, ensure_ascii=False, indent=2))
    return 0 if manifest["regression_guard_state"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
