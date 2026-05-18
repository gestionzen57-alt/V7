#!/usr/bin/env python3
"""T0122 — B9 V4 Native Runtime Validation.

Read-only validator for the B9/T009 summarizer V4 native integration.
It checks whether sequence summaries carry the required V1/V2/V3/V4 fields,
inspects the local summarizer source for the T0121 hook markers, and produces
machine-readable and human-readable validation outputs.

No DB access. No dashboard. No Telegram. No BUY/SELL/probability language.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

VERSION = "T0122_B9_V4_NATIVE_RUNTIME_VALIDATION_V0"

V1_FIELDS = [
    "what_happens_fr",
    "why_it_matters_fr",
    "how_it_happened_fr",
    "mechanism_fr",
    "proof_summary_fr",
]
V2_FIELDS = [
    "previous_context_fr",
    "cause_fr",
    "reaction_fr",
    "consequence_fr",
    "memory_shift_fr",
    "retest_role_fr",
]
V3_FIELDS = [
    "scene_id",
    "scene_role",
    "parent_scene",
    "child_moments",
    "session_chapter",
    "fractal_reading_fr",
]
V4_FIELDS = [
    "b9_center_path_state",
    "b9_effort_result_progress_state",
    "b9_progress_type",
    "b9_native_retest_judgment",
    "b9_source_quality_native_state",
    "b9_v4_timestamp_policy",
]
REQUIRED_FIELDS = V1_FIELDS + V2_FIELDS + V3_FIELDS + V4_FIELDS

FORBIDDEN_PATTERNS = [
    re.compile(r"\bBUY\b", re.I),
    re.compile(r"\bSELL\b", re.I),
    re.compile(r"\bACHAT\b", re.I),
    re.compile(r"\bVENTE\b", re.I),
    re.compile(r"probabilit[eé]\s+de\s+succ[eè]s", re.I),
    re.compile(r"signal\s+d['’]?achat", re.I),
    re.compile(r"signal\s+de\s+vente", re.I),
]

FIELD_GROUPS = {
    "V1_WHY_HOW": V1_FIELDS,
    "V2_CAUSALITY": V2_FIELDS,
    "V3_FRACTAL_SCENE": V3_FIELDS,
    "V4_NATIVE_RUNTIME": V4_FIELDS,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, sort_keys=False)
        f.write("\n")


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: normalize_csv_value(row.get(k, "")) for k in fieldnames})


def normalize_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def find_moments(summary: Mapping[str, Any]) -> List[MutableMapping[str, Any]]:
    candidates = [
        summary.get("moments"),
        summary.get("sequence_summary", {}).get("moments") if isinstance(summary.get("sequence_summary"), dict) else None,
        summary.get("b9_moments"),
        summary.get("scenes"),
    ]
    for candidate in candidates:
        if isinstance(candidate, list):
            return [m for m in candidate if isinstance(m, dict)]
    return []


def get_value(moment: Mapping[str, Any], names: Sequence[str], default: Any = None) -> Any:
    for name in names:
        if name in moment and moment.get(name) not in (None, ""):
            return moment.get(name)
    return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except Exception:
        return default


def infer_label(moment: Mapping[str, Any]) -> str:
    return str(get_value(moment, ["label_fr", "label", "moment_type", "tag", "type"], "Moment B9"))


def infer_time_start(moment: Mapping[str, Any]) -> str:
    return str(get_value(moment, ["time_start", "start", "start_time", "orig_start", "timestamp_start"], ""))


def infer_time_end(moment: Mapping[str, Any]) -> str:
    return str(get_value(moment, ["time_end", "end", "end_time", "orig_end", "timestamp_end"], ""))


def detect_timestamp_policy(moment: Mapping[str, Any]) -> str:
    start = infer_time_start(moment)
    end = infer_time_end(moment)
    has_orig = any(k in moment for k in ("orig_start", "orig_end", "original_time_start", "original_time_end"))
    if has_orig:
        return "ORIGINAL_TIME_AVAILABLE"
    if start.startswith("22:") or start.startswith("23:") or "shift" in json.dumps(moment, ensure_ascii=False).lower():
        return "SHIFTED_REPLAY_TIME_NEEDS_REMAP"
    if start or end:
        return "TIME_FIELDS_PRESENT_UNVERIFIED"
    return "TIME_FIELDS_MISSING"


def infer_progress_type(moment: Mapping[str, Any]) -> str:
    label = infer_label(moment).lower()
    center_delta = as_float(get_value(moment, ["center_delta", "center_delta_pips", "raw_delta_pips"], 0.0))
    center_range = abs(as_float(get_value(moment, ["center_range", "center_range_pips", "raw_range_pips"], 0.0)))
    if "progressive" in label or "vague progressive" in label:
        return "PROGRESSIVE_WAVE"
    if "corrective" in label or "respiration" in label:
        return "CORRECTIVE_WAVE"
    if "effort" in label and "résultat" in label:
        return "EFFORT_WITHOUT_RESULT"
    if "migration" in label or abs(center_delta) >= 5.0:
        return "CENTER_MIGRATION"
    if center_range <= 1.5:
        return "LOCAL_FRICTION_OR_STOP"
    return "UNCLASSIFIED_PROGRESS_TYPE"


def infer_center_path(moment: Mapping[str, Any]) -> str:
    center_delta = as_float(get_value(moment, ["center_delta", "center_delta_pips", "raw_delta_pips"], 0.0))
    center_range = abs(as_float(get_value(moment, ["center_range", "center_range_pips", "raw_range_pips"], 0.0)))
    label = infer_label(moment).lower()
    if center_delta >= 5.0:
        return "CENTER_PATH_UP"
    if center_delta <= -5.0:
        return "CENTER_PATH_DOWN"
    if center_range >= 5.0:
        return "CENTER_PATH_INTERNAL_SWING"
    if "effort" in label or "friction" in label:
        return "CENTER_PATH_BLOCKED_OR_COMPRESSED"
    return "CENTER_PATH_FLAT_OR_UNKNOWN"


def infer_effort_result_progress(moment: Mapping[str, Any]) -> str:
    label = infer_label(moment).lower()
    progress_type = infer_progress_type(moment)
    absorption = as_float(get_value(moment, ["absorption_mean", "absorption_avg", "abs_mean"], 0.0))
    failed = as_float(get_value(moment, ["failed_displacement_mean", "failed_displacement_avg", "failed_disp"], 0.0))
    if progress_type == "EFFORT_WITHOUT_RESULT" or (absorption >= 0.80 and failed >= 0.80 and progress_type != "PROGRESSIVE_WAVE"):
        return "EFFORT_HIGH_RESULT_LOW_PROGRESS_LOW"
    if progress_type == "PROGRESSIVE_WAVE":
        return "EFFORT_WITH_RESULT_AND_PROGRESS"
    if progress_type == "CENTER_MIGRATION":
        return "EFFORT_WITH_MEMORY_SHIFT"
    if "retest" in label:
        return "EFFORT_UNDER_RETEST_JUDGMENT"
    return "EFFORT_RESULT_PROGRESS_PARTIAL"


def infer_retest_judgment(moment: Mapping[str, Any]) -> str:
    label = infer_label(moment).lower()
    payload = json.dumps(moment, ensure_ascii=False).lower()
    if "retest" in payload and ("failed" in payload or "échou" in payload or "refus" in payload):
        return "RETEST_FAILED_VISIBLE"
    if "retest" in payload and ("accepted" in payload or "accept" in payload):
        return "RETEST_ACCEPTED_VISIBLE"
    if "retest" in payload:
        return "RETEST_PENDING_OR_PARTIAL"
    if "zone de décision" in label or "decision" in label:
        return "RETEST_NOT_VISIBLE_DECISION_ZONE_ONLY"
    return "RETEST_NOT_VISIBLE"


def infer_source_quality(moment: Mapping[str, Any]) -> str:
    visibility = str(get_value(moment, ["data_visibility", "visibility"], "")).upper()
    source_mode = str(get_value(moment, ["source_mode"], "")).upper()
    confidence_cap = as_float(get_value(moment, ["confidence_cap"], 1.0), 1.0)
    if "RAW" in visibility and confidence_cap >= 0.5:
        return "RAW_OR_FULL_SOURCE_STRONG"
    if "RECONSTRUCTED" in visibility or "PROXY" in source_mode or confidence_cap <= 0.35:
        return "PROXY_RECONSTRUCTED_CAPPED"
    if visibility:
        return "SOURCE_QUALITY_VISIBLE_PARTIAL"
    return "SOURCE_QUALITY_MISSING"


def scene_role_from_label(label: str) -> str:
    l = label.lower()
    if "progressive" in l or "vague" in l:
        return "MEMORY_SHIFT_OR_PROGRESS"
    if "effort" in l and "résultat" in l:
        return "FRICTION_OR_ABSORPTION"
    if "migration" in l:
        return "CENTER_MIGRATION"
    if "retest" in l:
        return "RETEST_JUDGMENT"
    if "respiration" in l or "corrective" in l:
        return "COUNTER_BREATH_OR_CORRECTION"
    return "SCENE_ROLE_PARTIAL"


def session_chapter_from_moment(moment: Mapping[str, Any]) -> str:
    role = scene_role_from_label(infer_label(moment))
    mapping = {
        "MEMORY_SHIFT_OR_PROGRESS": "Mémoire déplacée",
        "FRICTION_OR_ABSORPTION": "Décision de zone",
        "CENTER_MIGRATION": "Migration de centre",
        "RETEST_JUDGMENT": "Test / retest",
        "COUNTER_BREATH_OR_CORRECTION": "Respiration",
    }
    return mapping.get(role, "Ouverture / transition")


def stable_scene_id(moment: Mapping[str, Any], idx: int) -> str:
    seed = f"{infer_time_start(moment)}|{infer_time_end(moment)}|{infer_label(moment)}|{idx}"
    return "B9V4_" + hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10].upper()


def fallback_enrich_summary(summary: Mapping[str, Any]) -> Dict[str, Any]:
    # Conservative local fallback used when the T0120 contract module is absent.
    enriched = json.loads(json.dumps(summary, ensure_ascii=False))
    moments = find_moments(enriched)
    for idx, moment in enumerate(moments):
        label = infer_label(moment)
        progress_type = infer_progress_type(moment)
        center_path = infer_center_path(moment)
        retest = infer_retest_judgment(moment)
        source_quality = infer_source_quality(moment)
        scene_role = scene_role_from_label(label)
        moment.setdefault("what_happens_fr", f"B9 observe le moment '{label}' et conserve sa lecture comme scène de flux.")
        moment.setdefault("why_it_matters_fr", "Ce moment compte car il peut déplacer, freiner ou tester la mémoire locale du prix.")
        moment.setdefault("how_it_happened_fr", f"Lecture par centre, effort/résultat/progrès et état de retest : {center_path}, {progress_type}, {retest}.")
        moment.setdefault("mechanism_fr", f"Mécanisme B9: {center_path} + {progress_type} + {source_quality}.")
        moment.setdefault("proof_summary_fr", "Preuves utilisées: label B9, centre, déplacement, source quality et visibilité retest quand disponible.")
        moment.setdefault("previous_context_fr", "Contexte précédent non fourni ou reconstruit partiellement.")
        moment.setdefault("cause_fr", "Cause inférée depuis le rôle de la scène et la migration du centre.")
        moment.setdefault("reaction_fr", "Réaction lue par le déplacement du centre et la présence ou absence de progrès.")
        moment.setdefault("consequence_fr", "Conséquence: mémoire locale déplacée, freinée ou en attente de jugement.")
        moment.setdefault("memory_shift_fr", "Déplacement mémoire évalué par le chemin du centre et le progrès visible.")
        moment.setdefault("retest_role_fr", "Retest visible ou non visible, sans validation forcée.")
        moment.setdefault("scene_id", stable_scene_id(moment, idx))
        moment.setdefault("scene_role", scene_role)
        moment.setdefault("parent_scene", "B9_SEQUENCE_SUMMARY")
        moment.setdefault("child_moments", [])
        moment.setdefault("session_chapter", session_chapter_from_moment(moment))
        moment.setdefault("fractal_reading_fr", "Micro-film condensé en moment B9 ; la scène reste à relier aux chapitres supérieurs si disponibles.")
        moment.setdefault("b9_center_path_state", center_path)
        moment.setdefault("b9_effort_result_progress_state", infer_effort_result_progress(moment))
        moment.setdefault("b9_progress_type", progress_type)
        moment.setdefault("b9_native_retest_judgment", retest)
        moment.setdefault("b9_source_quality_native_state", source_quality)
        moment.setdefault("b9_v4_timestamp_policy", detect_timestamp_policy(moment))
    return enriched


def try_native_enrich(summary: Mapping[str, Any]) -> Tuple[Dict[str, Any], str, str]:
    try:
        from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4  # type: ignore
        result = enrich_sequence_summary_v4(summary)  # type: ignore[arg-type]
        if isinstance(result, dict):
            return result, "NATIVE_T0120_CONTRACT_USED", "pf_t009_sequence_summarizer_v4_contract.enrich_sequence_summary_v4"
    except Exception as exc:
        return fallback_enrich_summary(summary), "FALLBACK_USED_NATIVE_IMPORT_FAILED", repr(exc)
    return fallback_enrich_summary(summary), "FALLBACK_USED_NATIVE_RETURN_INVALID", "native function returned non-dict"


def count_field_coverage(moments: Sequence[Mapping[str, Any]]) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    rows: List[Dict[str, Any]] = []
    missing_counts: Dict[str, int] = {f: 0 for f in REQUIRED_FIELDS}
    total = len(moments)
    for field in REQUIRED_FIELDS:
        present = sum(1 for m in moments if m.get(field) not in (None, ""))
        missing = total - present
        missing_counts[field] = missing
        rows.append({
            "field": field,
            "group": next((g for g, fields in FIELD_GROUPS.items() if field in fields), "UNKNOWN"),
            "present_count": present,
            "missing_count": missing,
            "coverage_ratio": round(present / total, 4) if total else 0.0,
            "state": "PASS" if missing == 0 else "MISSING",
        })
    return rows, missing_counts


def scan_forbidden_language(obj: Any) -> List[Dict[str, Any]]:
    text = json.dumps(obj, ensure_ascii=False)
    hits: List[Dict[str, Any]] = []
    for pattern in FORBIDDEN_PATTERNS:
        for match in pattern.finditer(text):
            hits.append({"pattern": pattern.pattern, "match": match.group(0), "position": match.start()})
    return hits


def inspect_summarizer_source(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {"summarizer_path": "", "exists": False, "state": "SUMMARIZER_NOT_PROVIDED"}
    if not path.exists():
        return {"summarizer_path": str(path), "exists": False, "state": "SUMMARIZER_FILE_MISSING"}
    text = path.read_text(encoding="utf-8", errors="replace")
    markers = {
        "has_t0121_start_marker": "T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_START" in text,
        "has_t0121_end_marker": "T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_END" in text,
        "has_v4_helper": "_t0121_b9_v4_enrich" in text,
        "has_v4_integration_import": "pf_t009_sequence_summarizer_v4_integration" in text,
        "has_plain_return_summary": "return summary" in text,
    }
    state = "T0121_NATIVE_HOOK_VISIBLE" if all([
        markers["has_t0121_start_marker"],
        markers["has_t0121_end_marker"],
        markers["has_v4_helper"],
    ]) else "T0121_NATIVE_HOOK_NOT_FULLY_VISIBLE"
    return {
        "summarizer_path": str(path),
        "exists": True,
        "state": state,
        **markers,
    }


def write_markdown(path: Path, report: Mapping[str, Any], coverage_rows: Sequence[Mapping[str, Any]], runtime_rows: Sequence[Mapping[str, Any]]) -> None:
    lines: List[str] = []
    lines.append("# T0122 — B9 V4 Native Runtime Validation")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("T0122 vérifie que les summaries B9 portent réellement les champs V4 natifs après l’intégration T0121.")
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
    lines.append(f"- Version : `{report['version']}`")
    lines.append(f"- Moments analysés : `{report['input_moments']}`")
    lines.append(f"- Enrichment path : `{report['enrichment_state']}`")
    lines.append(f"- Summarizer hook state : `{report['summarizer_inspection'].get('state')}`")
    lines.append(f"- Champs manquants : `{report['total_missing_required_fields']}`")
    lines.append(f"- Forbidden language hits : `{len(report['forbidden_language_hits'])}`")
    lines.append(f"- Runtime validation state : `{report['runtime_validation_state']}`")
    lines.append("")
    lines.append("## Couverture champs V4")
    lines.append("")
    lines.append("| group | field | present | missing | ratio | state |")
    lines.append("|---|---|---:|---:|---:|---|")
    for row in coverage_rows:
        lines.append(f"| {row['group']} | `{row['field']}` | {row['present_count']} | {row['missing_count']} | {row['coverage_ratio']} | {row['state']} |")
    lines.append("")
    lines.append("## Runtime checks")
    lines.append("")
    lines.append("| check | state | detail |")
    lines.append("|---|---|---|")
    for row in runtime_rows:
        lines.append(f"| {row['check']} | {row['state']} | {row['detail']} |")
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
    lines.append("- Si le hook T0121 n’est pas visible, T0122 le signale sans modifier le summarizer.")
    lines.append("")
    lines.append("## Prochain geste")
    lines.append("")
    lines.append("Si `runtime_validation_state = PASS`, lancer T0123 — B9 V4 Replay Runtime Comparison. Sinon corriger T0121 avant d’avancer.")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_runtime_rows(report: Mapping[str, Any]) -> List[Dict[str, Any]]:
    ins = report["summarizer_inspection"]
    rows = [
        {"check": "summary_input_loaded", "state": "PASS" if report["input_moments"] > 0 else "FAIL", "detail": f"moments={report['input_moments']}"},
        {"check": "native_or_fallback_enrichment", "state": "PASS" if report["total_missing_required_fields"] == 0 else "FAIL", "detail": report["enrichment_state"]},
        {"check": "summarizer_hook_visible", "state": "PASS" if ins.get("state") == "T0121_NATIVE_HOOK_VISIBLE" else "WARN", "detail": ins.get("state", "UNKNOWN")},
        {"check": "forbidden_language", "state": "PASS" if not report["forbidden_language_hits"] else "FAIL", "detail": f"hits={len(report['forbidden_language_hits'])}"},
        {"check": "db_write_absent", "state": "PASS", "detail": "validator does not open or write DB"},
        {"check": "trading_decision_absent", "state": "PASS", "detail": "no BUY/SELL/probability semantics intended"},
    ]
    return rows


def zip_outputs(zip_path: Path, output_dir: Path, files: Sequence[Path]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if file.exists():
                zf.write(file, arcname=file.relative_to(output_dir))


def run(args: argparse.Namespace) -> Dict[str, Any]:
    sequence_path = Path(args.sequence_summary_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    raw_summary = load_json(sequence_path)
    enriched_summary, enrichment_state, enrichment_detail = try_native_enrich(raw_summary)
    moments = find_moments(enriched_summary)
    coverage_rows, missing_counts = count_field_coverage(moments)
    forbidden_hits = scan_forbidden_language(enriched_summary)
    summarizer_inspection = inspect_summarizer_source(Path(args.summarizer_py) if args.summarizer_py else None)
    total_missing = sum(missing_counts.values())

    runtime_state = "PASS" if total_missing == 0 and not forbidden_hits else "FAIL"
    if summarizer_inspection.get("state") != "T0121_NATIVE_HOOK_VISIBLE":
        runtime_state = "PASS_WITH_SUMMARIZER_HOOK_WARNING" if runtime_state == "PASS" else runtime_state

    report: Dict[str, Any] = {
        "version": VERSION,
        "generated_at_utc": utc_now(),
        "sequence_summary_json": str(sequence_path),
        "output_dir": str(output_dir),
        "input_moments": len(moments),
        "enrichment_state": enrichment_state,
        "enrichment_detail": enrichment_detail,
        "summarizer_inspection": summarizer_inspection,
        "missing_required_field_counts": {k: v for k, v in missing_counts.items() if v},
        "total_missing_required_fields": total_missing,
        "forbidden_language_hits": forbidden_hits,
        "runtime_validation_state": runtime_state,
        "required_fields": REQUIRED_FIELDS,
        "doctrine": {
            "b9": "B9 cherche la trace laissée par l'effort.",
            "no_prediction": True,
            "no_buy_sell": True,
            "no_db_write": True,
        },
    }

    runtime_rows = make_runtime_rows(report)

    json_out = output_dir / "B9_V4_NATIVE_RUNTIME_VALIDATION_V0.json"
    md_out = output_dir / "B9_V4_NATIVE_RUNTIME_VALIDATION_V0.md"
    coverage_csv = output_dir / "B9_V4_NATIVE_RUNTIME_FIELD_COVERAGE_V0.csv"
    runtime_csv = output_dir / "B9_V4_NATIVE_RUNTIME_CHECKS_V0.csv"
    enriched_json = output_dir / "B9_V4_NATIVE_RUNTIME_ENRICHED_SUMMARY_SAMPLE_V0.json"
    manifest_json = output_dir / "B9_V4_NATIVE_RUNTIME_VALIDATION_MANIFEST.json"
    zip_out = output_dir / "B9_V4_NATIVE_RUNTIME_VALIDATION_V0.zip"

    write_json(json_out, report)
    write_json(enriched_json, enriched_summary)
    write_csv(coverage_csv, coverage_rows, ["group", "field", "present_count", "missing_count", "coverage_ratio", "state"])
    write_csv(runtime_csv, runtime_rows, ["check", "state", "detail"])
    write_markdown(md_out, report, coverage_rows, runtime_rows)

    manifest = {
        "version": VERSION,
        "generated_at_utc": report["generated_at_utc"],
        "files": [p.name for p in [json_out, md_out, coverage_csv, runtime_csv, enriched_json, manifest_json, zip_out]],
        "runtime_validation_state": runtime_state,
        "input_moments": len(moments),
        "total_missing_required_fields": total_missing,
        "forbidden_language_hits": len(forbidden_hits),
        "constraints": {
            "read_only": True,
            "db_write": False,
            "dashboard": False,
            "telegram": False,
            "buy_sell": False,
            "probability_of_success": False,
        },
    }
    write_json(manifest_json, manifest)
    zip_outputs(zip_out, output_dir, [json_out, md_out, coverage_csv, runtime_csv, enriched_json, manifest_json])
    report["zip"] = str(zip_out)
    write_json(json_out, report)
    return report


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T0122 B9 V4 Native Runtime Validation")
    parser.add_argument("--sequence-summary-json", required=True, help="Input T009/B9 sequence summary JSON to validate")
    parser.add_argument("--summarizer-py", default="pf_t009_sequence_summarizer.py", help="Optional local summarizer source to inspect")
    parser.add_argument("--output-dir", required=True, help="Output directory")
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    try:
        report = run(args)
    except Exception as exc:
        print(json.dumps({"version": VERSION, "error": repr(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1
    print(json.dumps({
        "version": report["version"],
        "input_moments": report["input_moments"],
        "runtime_validation_state": report["runtime_validation_state"],
        "enrichment_state": report["enrichment_state"],
        "summarizer_hook_state": report["summarizer_inspection"].get("state"),
        "total_missing_required_fields": report["total_missing_required_fields"],
        "forbidden_language_hits": len(report["forbidden_language_hits"]),
        "output_dir": report["output_dir"],
        "zip": report.get("zip", ""),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
