#!/usr/bin/env python3
"""T0123 — B9 V4 Replay Runtime Comparison.

Read-only comparison utility for B9 sequence summaries.
It compares a before-V4 replay summary with an after/enriched V4 summary.
If no after summary is provided, it applies a local/fallback V4 enrichment so the
field contract can be validated without touching the runtime or databases.
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

VERSION = "T0123_B9_V4_REPLAY_RUNTIME_COMPARISON_V0"

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
    "label_fr",
    "reading_fr",
    "source_mode",
    "data_visibility",
    "confidence_cap",
    "proxy_vs_raw_verdict",
    "raw_texture_role",
    "technical_limits",
    "b9_retest_source_limits",
    "b9_natural_flow_limits",
]

FORBIDDEN_PATTERNS = [
    r"\bBUY\b",
    r"\bSELL\b",
    r"\bACHETER\b",
    r"\bVENDRE\b",
    r"probabilit[ée]\s+de\s+succ[eè]s",
    r"probability\s+of\s+success",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return {"metadata": {}, "moments": data}
    if not isinstance(data, dict):
        raise ValueError(f"Unsupported JSON root in {path}: {type(data)}")
    if "moments" not in data:
        # common fallback naming
        for key in ("scenes", "items", "results"):
            if isinstance(data.get(key), list):
                data = dict(data)
                data["moments"] = data[key]
                break
    data.setdefault("metadata", {})
    data.setdefault("moments", [])
    if not isinstance(data["moments"], list):
        raise ValueError("summary['moments'] must be a list")
    return data


def compact(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def get_moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    moments = summary.get("moments", [])
    return [m for m in moments if isinstance(m, dict)]


def stable_id(moment: Dict[str, Any], idx: int) -> str:
    base = "|".join([
        str(moment.get("time_start") or moment.get("start_time") or ""),
        str(moment.get("time_end") or moment.get("end_time") or ""),
        str(moment.get("label_fr") or moment.get("moment_type") or moment.get("tags") or ""),
        str(idx),
    ])
    return hashlib.sha1(base.encode("utf-8")).hexdigest()[:10].upper()


def infer_label(moment: Dict[str, Any]) -> str:
    label = moment.get("label_fr") or moment.get("moment_type") or moment.get("b9_natural_flow_reading_fr")
    if label:
        return str(label)
    delta = float_or_none(moment.get("raw_delta_pips") or moment.get("pip_delta") or 0) or 0.0
    effort = float_or_none(moment.get("b9_effort_result_ratio"))
    if abs(delta) < 1.0 and (effort is None or effort >= 0):
        return "Effort sans résultat"
    if delta > 0:
        return "Vague progressive haussière"
    if delta < 0:
        return "Centre de gravité qui descend"
    return "Zone de friction locale"


def float_or_none(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def infer_progress_type(moment: Dict[str, Any]) -> str:
    delta = float_or_none(moment.get("raw_delta_pips") or moment.get("pip_delta")) or 0.0
    rng = float_or_none(moment.get("raw_range_pips"))
    effort_ratio = float_or_none(moment.get("b9_effort_result_ratio"))
    text = " ".join(str(moment.get(k, "")) for k in ("label_fr", "moment_type", "b9_natural_flow_reading_fr", "tags")).lower()
    if "effort" in text and ("sans" in text or "without" in text):
        return "EFFORT_WITHOUT_RESULT"
    if abs(delta) >= 8.0:
        return "PROGRESSIVE_WAVE"
    if rng is not None and rng >= 6.0 and abs(delta) < rng * 0.45:
        return "INTERNAL_PATH_VISIBLE_BUT_NET_MUTED"
    if effort_ratio is not None and effort_ratio > 2.0 and abs(delta) < 2.0:
        return "EFFORT_WITHOUT_RESULT"
    if abs(delta) < 2.0:
        return "LOCAL_FRICTION_OR_DECISION_AREA"
    return "CORRECTIVE_OR_PARTIAL_PROGRESS"


def infer_center_path(moment: Dict[str, Any]) -> str:
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
    status = str(moment.get("b9_retest_source_status") or moment.get("retest_outcome_hint") or "").upper()
    visibility = str(moment.get("b9_retest_source_visibility") or "").upper()
    touches = moment.get("retest_touch_count") or moment.get("b9_retest_touch_count_proxy")
    if "RAW_UNAVAILABLE" in status or "UNAVAILABLE" in visibility:
        return "RETEST_NOT_VISIBLE_SOURCE_LIMITED"
    if touches not in (None, "", 0, "0"):
        return "RETEST_VISIBLE_OR_PROXY_VISIBLE"
    if status and status not in ("NONE", "NA", "N/A"):
        return "RETEST_STATE_INFERRED"
    return "RETEST_NOT_VISIBLE"


def infer_source_quality(moment: Dict[str, Any]) -> str:
    verdict = str(moment.get("proxy_vs_raw_verdict") or "").upper()
    visibility = str(moment.get("data_visibility") or moment.get("raw_data_visibility") or "").upper()
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


def enrich_moment_fallback(moment: Dict[str, Any], idx: int, total: int) -> Dict[str, Any]:
    out = dict(moment)
    label = infer_label(moment)
    progress = infer_progress_type(moment)
    center = infer_center_path(moment)
    retest = infer_retest(moment)
    source = infer_source_quality(moment)
    sid = f"B9V4_SCENE_{idx+1:03d}_{stable_id(moment, idx)}"
    out.setdefault("what_happens_fr", f"B9 lit le moment comme : {label}.")
    out.setdefault("why_it_matters_fr", "Ce moment compte parce qu'il indique comment l'effort déplace, bloque ou nuance la mémoire locale.")
    out.setdefault("how_it_happened_fr", f"Lecture par chemin interne du centre ({center}), effort/résultat/progrès ({progress}) et retest ({retest}).")
    out.setdefault("mechanism_fr", f"Mécanisme B9 V4 : {center} + {progress} + {retest} + {source}.")
    out.setdefault("proof_summary_fr", "Preuves conservées : source_mode, data_visibility, raw/proxy verdict, texture raw et limites disponibles.")
    out.setdefault("previous_context_fr", "Contexte précédent reconstruit depuis la séquence de moments, sans conclusion directionnelle.")
    out.setdefault("cause_fr", "Cause candidate : effort local, zone/mémoire travaillée ou retest selon les preuves disponibles.")
    out.setdefault("reaction_fr", "Réaction candidate : déplacement, frein, absorption, respiration ou migration de centre.")
    out.setdefault("consequence_fr", "Conséquence candidate : la mémoire reste stable, se déplace, ou demande un retest visible.")
    out.setdefault("memory_shift_fr", "Déplacement mémoire qualifié par le chemin du centre et la visibilité source.")
    out.setdefault("retest_role_fr", retest.replace("_", " ").lower())
    out.setdefault("scene_id", sid)
    out.setdefault("scene_role", progress)
    out.setdefault("parent_scene", "B9_REPLAY_SEQUENCE_V4")
    out.setdefault("child_moments", [])
    out.setdefault("session_chapter", "Mémoire déplacée" if "PROGRESSIVE" in progress or "MIGRATES" in center else "Décision de zone")
    out.setdefault("fractal_reading_fr", "Micro-moment replacé dans la scène : l'événement n'est pas lu seul, il est lu dans son rôle de séquence.")
    out.setdefault("b9_center_path_state", center)
    out.setdefault("b9_effort_result_progress_state", progress)
    out.setdefault("b9_progress_type", progress)
    out.setdefault("b9_native_retest_judgment", retest)
    out.setdefault("b9_source_quality_native_state", source)
    out.setdefault("b9_v4_timestamp_policy", "ORIGINAL_TIME_REQUIRED_WHEN_SHIFTED_REPLAY_PRESENT")
    return out


def enrich_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    # Prefer the actual T0120/T0121 contract if installed in Core.
    try:
        from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4  # type: ignore
        enriched = enrich_sequence_summary_v4(deepcopy(summary))
        if isinstance(enriched, dict) and isinstance(enriched.get("moments"), list):
            return enriched
    except Exception:
        pass
    out = deepcopy(summary)
    moments = get_moments(out)
    out["moments"] = [enrich_moment_fallback(m, i, len(moments)) for i, m in enumerate(moments)]
    out.setdefault("metadata", {})
    out["metadata"]["t0123_fallback_enrichment_used"] = True
    return out


def count_forbidden(obj: Any) -> List[str]:
    text = json.dumps(obj, ensure_ascii=False)
    hits = []
    for pat in FORBIDDEN_PATTERNS:
        if re.search(pat, text, re.IGNORECASE):
            hits.append(pat)
    return hits


def compare(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    b_m = get_moments(before)
    a_m = get_moments(after)
    n = min(len(b_m), len(a_m))

    coverage_rows = []
    total_missing = 0
    for field in REQUIRED_V4_FIELDS:
        present = sum(1 for m in a_m if compact(m.get(field)) != "")
        missing = len(a_m) - present
        total_missing += missing
        coverage_rows.append({
            "field": field,
            "present_count": present,
            "missing_count": missing,
            "coverage_ratio": round(present / len(a_m), 6) if a_m else 0.0,
        })

    preservation_rows = []
    changed_preserved = 0
    for i in range(n):
        row = {"moment_index": i}
        for f in PRESERVATION_FIELDS:
            before_v = compact(b_m[i].get(f))
            after_v = compact(a_m[i].get(f))
            if before_v and after_v and before_v != after_v:
                changed_preserved += 1
                row[f] = "CHANGED"
            elif before_v and not after_v:
                changed_preserved += 1
                row[f] = "DROPPED"
            elif before_v == after_v:
                row[f] = "PRESERVED"
            else:
                row[f] = "NOT_PRESENT_BEFORE"
        preservation_rows.append(row)

    diff_rows = []
    for i in range(n):
        before_keys = set(b_m[i].keys())
        after_keys = set(a_m[i].keys())
        added = sorted(after_keys - before_keys)
        removed = sorted(before_keys - after_keys)
        diff_rows.append({
            "moment_index": i,
            "before_key_count": len(before_keys),
            "after_key_count": len(after_keys),
            "added_key_count": len(added),
            "removed_key_count": len(removed),
            "v4_added_fields": ";".join([k for k in added if k in REQUIRED_V4_FIELDS]),
            "removed_keys": ";".join(removed[:20]),
        })

    timestamp_rows = []
    shifted_like = 0
    original_like = 0
    for i, m in enumerate(a_m):
        has_shift = any(k in m for k in ("raw_time_shift_min", "shifted_time", "replay_shift_min"))
        has_orig = any(k in m for k in ("orig_start", "orig_end", "original_start", "original_end", "time_start", "time_end", "start_time", "end_time"))
        policy = m.get("b9_v4_timestamp_policy", "")
        if has_shift:
            shifted_like += 1
        if has_orig:
            original_like += 1
        timestamp_rows.append({
            "moment_index": i,
            "has_shift_marker": has_shift,
            "has_original_or_display_time": has_orig,
            "b9_v4_timestamp_policy": policy,
            "timestamp_state": "OK" if has_orig else "MISSING_DISPLAY_TIME",
        })

    forbidden_hits = count_forbidden(after)
    state = "PASS"
    if len(b_m) != len(a_m):
        state = "FAIL_MOMENT_COUNT_CHANGED"
    elif total_missing:
        state = "FAIL_MISSING_V4_FIELDS"
    elif forbidden_hits:
        state = "FAIL_FORBIDDEN_LANGUAGE"
    elif changed_preserved:
        state = "PASS_WITH_PRESERVATION_WARNINGS"

    return {
        "version": VERSION,
        "generated_at": utc_now(),
        "runtime_comparison_state": state,
        "before_moment_count": len(b_m),
        "after_moment_count": len(a_m),
        "total_missing_required_fields": total_missing,
        "forbidden_language_hits": forbidden_hits,
        "changed_preserved_field_cells": changed_preserved,
        "shifted_like_moments": shifted_like,
        "original_like_moments": original_like,
        "field_coverage_rows": coverage_rows,
        "moment_preservation_rows": preservation_rows,
        "field_diff_rows": diff_rows,
        "timestamp_policy_rows": timestamp_rows,
    }


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_md(path: Path, report: Dict[str, Any], before_path: Path, after_mode: str) -> None:
    lines = []
    lines.append("# T0123 — B9 V4 Replay Runtime Comparison")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("T0123 compare un summary B9 avant/après enrichissement V4 pour vérifier que B9 gagne en lecture de scène sans perdre les moments, la provenance, la source quality ni les limites.")
    lines.append("")
    lines.append("Doctrine :")
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
    lines.append(f"- État : `{report['runtime_comparison_state']}`")
    lines.append(f"- Moments avant : `{report['before_moment_count']}`")
    lines.append(f"- Moments après : `{report['after_moment_count']}`")
    lines.append(f"- Champs requis manquants : `{report['total_missing_required_fields']}`")
    lines.append(f"- Langage interdit détecté : `{len(report['forbidden_language_hits'])}`")
    lines.append(f"- Cellules de provenance/limites changées : `{report['changed_preserved_field_cells']}`")
    lines.append(f"- Mode after : `{after_mode}`")
    lines.append("")
    lines.append("## Ce que T0123 vérifie")
    lines.append("")
    lines.append("```text")
    lines.append("1. Le nombre de moments ne change pas.")
    lines.append("2. Les champs V4 existent sur chaque moment.")
    lines.append("3. Les champs source/provenance/limites ne sont pas effacés.")
    lines.append("4. Les timestamps shifted/replay sont signalés par policy.")
    lines.append("5. Aucun BUY/SELL, aucune probabilité de succès.")
    lines.append("```")
    lines.append("")
    lines.append("## Fichiers CSV")
    lines.append("")
    lines.append("```text")
    lines.append("B9_V4_REPLAY_FIELD_DIFF_V0.csv")
    lines.append("B9_V4_REPLAY_MOMENT_PRESERVATION_V0.csv")
    lines.append("B9_V4_REPLAY_REQUIRED_FIELD_COVERAGE_V0.csv")
    lines.append("B9_V4_REPLAY_TIMESTAMP_POLICY_V0.csv")
    lines.append("```")
    lines.append("")
    lines.append("## Limites")
    lines.append("")
    lines.append("Read-only. Aucune écriture powerflow.db. Aucune écriture tick_archive.db. Aucun dashboard. Aucun Telegram. Aucun BUY/SELL. Aucune probabilité de succès.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=VERSION)
    ap.add_argument("--before-summary-json", required=True)
    ap.add_argument("--after-summary-json", default="")
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    before_path = Path(args.before_summary_json)
    after_path = Path(args.after_summary_json) if args.after_summary_json else None
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    before = load_json(before_path)
    if after_path and after_path.exists():
        after = load_json(after_path)
        after_mode = "provided_after_summary"
    else:
        after = enrich_summary(before)
        after_mode = "generated_by_installed_contract_or_fallback"

    report = compare(before, after)
    report["input_before_summary_json"] = str(before_path)
    report["input_after_summary_json"] = str(after_path) if after_path else ""
    report["after_mode"] = after_mode
    report["read_only"] = True
    report["db_write"] = False
    report["dashboard"] = False
    report["telegram"] = False
    report["buy_sell"] = False
    report["probability_of_success"] = False

    json_path = out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_V0.json"
    md_path = out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_V0.md"
    enriched_path = out_dir / "B9_V4_REPLAY_ENRICHED_SUMMARY_SAMPLE_V0.json"
    manifest_path = out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_MANIFEST.json"
    zip_path = out_dir / "B9_V4_REPLAY_RUNTIME_COMPARISON_V0.zip"

    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    enriched_path.write_text(json.dumps(after, indent=2, ensure_ascii=False), encoding="utf-8")
    write_md(md_path, report, before_path, after_mode)
    write_csv(out_dir / "B9_V4_REPLAY_FIELD_DIFF_V0.csv", report["field_diff_rows"])
    write_csv(out_dir / "B9_V4_REPLAY_MOMENT_PRESERVATION_V0.csv", report["moment_preservation_rows"])
    write_csv(out_dir / "B9_V4_REPLAY_REQUIRED_FIELD_COVERAGE_V0.csv", report["field_coverage_rows"])
    write_csv(out_dir / "B9_V4_REPLAY_TIMESTAMP_POLICY_V0.csv", report["timestamp_policy_rows"])

    manifest = {
        "version": VERSION,
        "generated_at": report["generated_at"],
        "files": [
            json_path.name,
            md_path.name,
            enriched_path.name,
            "B9_V4_REPLAY_FIELD_DIFF_V0.csv",
            "B9_V4_REPLAY_MOMENT_PRESERVATION_V0.csv",
            "B9_V4_REPLAY_REQUIRED_FIELD_COVERAGE_V0.csv",
            "B9_V4_REPLAY_TIMESTAMP_POLICY_V0.csv",
            zip_path.name,
        ],
        "runtime_comparison_state": report["runtime_comparison_state"],
        "read_only": True,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [json_path, md_path, enriched_path, manifest_path,
                  out_dir / "B9_V4_REPLAY_FIELD_DIFF_V0.csv",
                  out_dir / "B9_V4_REPLAY_MOMENT_PRESERVATION_V0.csv",
                  out_dir / "B9_V4_REPLAY_REQUIRED_FIELD_COVERAGE_V0.csv",
                  out_dir / "B9_V4_REPLAY_TIMESTAMP_POLICY_V0.csv"]:
            z.write(p, arcname=p.name)

    print(json.dumps({
        "version": VERSION,
        "runtime_comparison_state": report["runtime_comparison_state"],
        "before_moment_count": report["before_moment_count"],
        "after_moment_count": report["after_moment_count"],
        "total_missing_required_fields": report["total_missing_required_fields"],
        "forbidden_language_hits": len(report["forbidden_language_hits"]),
        "changed_preserved_field_cells": report["changed_preserved_field_cells"],
        "output_dir": str(out_dir),
        "zip": str(zip_path),
    }, indent=2, ensure_ascii=False))
    return 0 if report["runtime_comparison_state"].startswith("PASS") else 2


if __name__ == "__main__":
    raise SystemExit(main())
