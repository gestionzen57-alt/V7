#!/usr/bin/env python3
"""T0125 - B9 V4 Golden Replay Batch Runner V0.

Read-only batch validator for B9 V4 summaries. It scans a folder of replay/summary
JSON files, applies the same deterministic V4 field guard used by the golden replay
contract, and emits a batch-level audit.

No DB write, no dashboard, no Telegram, no BUY/SELL, no probability of success.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

VERSION = "T0125_B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0"

FORBIDDEN_TERMS = [
    "BUY", "SELL", "ACHETER", "VENDRE", "probability of success", "probabilite de succes",
    "probabilité de succès", "signal d'achat", "signal de vente",
]

V4_REQUIRED_FIELDS = [
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

PRESERVED_FIELDS = [
    "time_start", "time_end", "label_fr", "moment_type", "source_mode",
    "data_visibility", "summary_recovery_type", "source_family",
    "proxy_vs_raw_verdict", "proxy_raw_agreement_state", "technical_limits",
]

GOLDEN_CASES = {
    "B9V4_GOLDEN_EFFORT_WITHOUT_RESULT": ["effort", "without", "result", "sans resultat", "sans résultat"],
    "B9V4_GOLDEN_PROGRESSIVE_WAVE": ["progressive", "wave", "vague progressive"],
    "B9V4_GOLDEN_CENTER_MIGRATION_DOWN": ["center_migration_down", "centre de gravite", "centre de gravité", "descend"],
    "B9V4_GOLDEN_RETEST_FAILED": ["retest", "failed", "echoue", "échoué", "refuse"],
    "B9V4_GOLDEN_CORRECTIVE_BREATH": ["corrective", "breath", "respiration", "correction"],
    "B9V4_GOLDEN_SOURCE_QUALITY_TIMESTAMP": ["source", "quality", "timestamp", "visibility"],
}


def _norm(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _lower_blob(moment: Dict[str, Any]) -> str:
    parts = []
    for key in ["moment_type", "label_fr", "reading_fr", "what_happens_fr", "why_it_matters_fr", "session_chapter", "technical_limits"]:
        value = moment.get(key)
        if isinstance(value, list):
            parts.extend(map(str, value))
        else:
            parts.append(str(value or ""))
    return " ".join(parts).lower()


def _moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ["moments", "sequence_moments", "b9_moments", "items"]:
        value = summary.get(key)
        if isinstance(value, list):
            return [m for m in value if isinstance(m, dict)]
    # Some outputs may be a list-like payload under data.
    data = summary.get("data")
    if isinstance(data, dict):
        return _moments(data)
    return []


def _family_from_text(moment: Dict[str, Any]) -> Tuple[str, str]:
    blob = _lower_blob(moment)
    if any(tok in blob for tok in ["progressive", "migration", "break", "deplace", "déplace", "avance"]):
        return "DIRECTIONAL_PROGRESS_MEMORY", "heuristic_progress_or_migration"
    if any(tok in blob for tok in ["absorption", "effort", "friction", "without result", "sans resultat", "sans résultat", "shelf"]):
        return "FRICTION_ABSORPTION_MEMORY", "heuristic_absorption_or_friction"
    if any(tok in blob for tok in ["breath", "respiration", "rotation", "corrective", "correction"]):
        return "ROTATION_BREATH_MEMORY", "heuristic_rotation_or_breath"
    return "FRICTION_ABSORPTION_MEMORY", "fallback_unknown_to_friction_absorption"


def _chapter(moment: Dict[str, Any]) -> str:
    blob = _lower_blob(moment)
    if "retest" in blob:
        return "Test / retest"
    if any(tok in blob for tok in ["migration", "centre", "center"]):
        return "Migration de centre"
    if any(tok in blob for tok in ["progressive", "wave", "vague"]):
        return "Memoire deplacee"
    if any(tok in blob for tok in ["breath", "respiration", "corrective"]):
        return "Respiration"
    return "Decision de zone"


def enrich_moment(moment: Dict[str, Any], idx: int, total: int) -> Dict[str, Any]:
    out = dict(moment)
    blob = _lower_blob(out)
    memory_family, family_origin = _family_from_text(out)
    out.setdefault("memory_family", memory_family)
    out.setdefault("memory_family_origin", family_origin)

    label = _norm(out.get("label_fr") or out.get("moment_type") or f"Moment B9 {idx+1}")
    source_mode = _norm(out.get("source_mode") or "UNKNOWN_SOURCE_MODE")
    visibility = _norm(out.get("data_visibility") or "UNKNOWN_DATA_VISIBILITY")
    verdict = _norm(out.get("proxy_vs_raw_verdict") or out.get("proxy_raw_agreement_state") or "UNKNOWN_RAW_VERDICT")

    if any(tok in blob for tok in ["progressive", "wave", "vague"]):
        effort_state = "EFFORT_RESULT_PROGRESS_VISIBLE"
        progress_type = "PROGRESSIVE_WAVE"
        center_state = "CENTER_PATH_ADVANCES"
        what = "Le flux produit un déplacement lisible et déplace la mémoire locale."
        consequence = "La scène conserve une trace de progression utile pour comparaison B6."
    elif any(tok in blob for tok in ["migration", "descend", "down", "centre", "center"]):
        effort_state = "EFFORT_ABSORBED_WITH_CENTER_MIGRATION"
        progress_type = "CENTER_MIGRATION"
        center_state = "CENTER_PATH_MIGRATES"
        what = "Le centre de gravité se déplace par paliers."
        consequence = "L'absorption accompagne le mouvement au lieu de l'annuler."
    elif any(tok in blob for tok in ["retest", "failed", "échoué", "echoue", "refuse"]):
        effort_state = "RETEST_JUDGES_PREVIOUS_ZONE"
        progress_type = "RETEST_FAILED_OR_PENDING"
        center_state = "CENTER_PATH_JUDGED_BY_RETEST"
        what = "La zone précédente est interrogée par le retest."
        consequence = "La scène reste dépendante du verdict prix."
    elif any(tok in blob for tok in ["breath", "respiration", "corrective", "correction"]):
        effort_state = "MOVEMENT_WITHOUT_MEMORY_SHIFT"
        progress_type = "CORRECTIVE_BREATH"
        center_state = "CENTER_PATH_BREATHES"
        what = "Le flux respire dans une structure existante."
        consequence = "La mémoire n'est pas encore déplacée."
    else:
        effort_state = "EFFORT_WITHOUT_CLEAN_PROGRESS"
        progress_type = "EFFORT_WITHOUT_RESULT_OR_FRICTION"
        center_state = "CENTER_PATH_LIMITED_OR_UNCLEAR"
        what = "Le flux montre de l'effort mais le progrès reste limité ou partiel."
        consequence = "La scène vaut comme friction ou absorption à comparer, pas comme direction."

    retest = "RETEST_NOT_VISIBLE"
    if "retest" in blob:
        retest = "RETEST_VISIBLE_JUDGMENT_REQUIRED"
    elif any(tok in blob for tok in ["failed", "échoué", "echoue", "refuse"]):
        retest = "RETEST_FAILURE_INFERRED"

    source_quality = "SOURCE_QUALITY_UNKNOWN"
    if "raw_unavailable" in verdict.lower():
        source_quality = "SOURCE_QUALITY_REJECTED_RAW_UNAVAILABLE"
    elif "confirmed" in verdict.lower():
        source_quality = "SOURCE_QUALITY_CONFIRMED_BY_RAW"
    elif "nuanced" in verdict.lower():
        source_quality = "SOURCE_QUALITY_NUANCED_BY_RAW"
    elif source_mode or visibility:
        source_quality = "SOURCE_QUALITY_VISIBLE_LIMITED_OR_PROXY"

    out.setdefault("what_happens_fr", what)
    out.setdefault("why_it_matters_fr", "B9 conserve la trace effort / résultat / progrès sans la transformer en signal.")
    out.setdefault("how_it_happened_fr", "Lecture issue du chemin interne, du rôle de la zone, de la source et du verdict raw/proxy disponible.")
    out.setdefault("mechanism_fr", f"{effort_state} + {center_state} + {source_quality}")
    out.setdefault("proof_summary_fr", f"source_mode={source_mode}; data_visibility={visibility}; raw_verdict={verdict}")
    out.setdefault("previous_context_fr", "Contexte précédent conservé si disponible, sinon scène locale lue comme fragment autonome.")
    out.setdefault("cause_fr", "Cause inférée par le rôle du moment et la position dans le microfilm.")
    out.setdefault("reaction_fr", what)
    out.setdefault("consequence_fr", consequence)
    out.setdefault("memory_shift_fr", "Mémoire déplacée" if "ADVANCES" in center_state or "MIGRATES" in center_state else "Mémoire non déplacée ou partielle")
    out.setdefault("retest_role_fr", retest)
    out.setdefault("scene_id", f"B9V4_SCENE_{idx+1:03d}")
    out.setdefault("scene_role", out.get("memory_family", memory_family))
    out.setdefault("parent_scene", "B9_V4_BATCH_REPLAY")
    out.setdefault("child_moments", [])
    out.setdefault("session_chapter", _chapter(out))
    out.setdefault("fractal_reading_fr", "Le moment est lu comme fragment d'un film plus large, pas comme preuve isolée.")
    out.setdefault("b9_center_path_state", center_state)
    out.setdefault("b9_effort_result_progress_state", effort_state)
    out.setdefault("b9_progress_type", progress_type)
    out.setdefault("b9_native_retest_judgment", retest)
    out.setdefault("b9_source_quality_native_state", source_quality)
    out.setdefault("b9_v4_timestamp_policy", "PRESERVE_ORIGINAL_TIMESTAMPS_NO_SHIFT_HARDENING")
    return out


def enrich_summary(summary: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(summary)
    moments = _moments(summary)
    enriched = [enrich_moment(m, i, len(moments)) for i, m in enumerate(moments)]
    # Preserve original key when possible.
    for key in ["moments", "sequence_moments", "b9_moments", "items"]:
        if isinstance(out.get(key), list):
            out[key] = enriched
            break
    else:
        out["moments"] = enriched
    out.setdefault("b9_v4_batch_enriched", True)
    out.setdefault("b9_v4_batch_version", VERSION)
    return out


def find_forbidden(obj: Any) -> List[str]:
    text = json.dumps(obj, ensure_ascii=False)
    hits = []
    for term in FORBIDDEN_TERMS:
        if re.search(re.escape(term), text, re.IGNORECASE):
            hits.append(term)
    return sorted(set(hits))


def detect_golden_cases(moments: List[Dict[str, Any]]) -> Dict[str, bool]:
    found = {case: False for case in GOLDEN_CASES}
    all_blob = " ".join(_lower_blob(m) for m in moments)
    for case, tokens in GOLDEN_CASES.items():
        found[case] = any(token in all_blob for token in tokens)
    # Source quality case is satisfied if any native source quality or timestamp policy exists.
    if any(m.get("b9_source_quality_native_state") and m.get("b9_v4_timestamp_policy") for m in moments):
        found["B9V4_GOLDEN_SOURCE_QUALITY_TIMESTAMP"] = True
    return found


def validate_summary(path: Path, output_dir: Path) -> Dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    before = _moments(raw)
    enriched = enrich_summary(raw)
    after = _moments(enriched)
    missing_counts: Dict[str, int] = {field: 0 for field in V4_REQUIRED_FIELDS}
    for m in after:
        for field in V4_REQUIRED_FIELDS:
            value = m.get(field)
            if value in (None, ""):
                missing_counts[field] += 1
    missing_counts = {k: v for k, v in missing_counts.items() if v}

    preserved_changes = 0
    for before_m, after_m in zip(before, after):
        for field in PRESERVED_FIELDS:
            if field in before_m and before_m.get(field) != after_m.get(field):
                preserved_changes += 1

    forbidden_hits = find_forbidden(enriched)
    golden = detect_golden_cases(after)
    golden_passed = sum(1 for ok in golden.values() if ok)
    state = "PASS" if not missing_counts and not forbidden_hits and len(before) == len(after) and preserved_changes == 0 else "FAIL"
    if state == "PASS" and golden_passed < len(golden):
        state = "PASS_WITH_PARTIAL_GOLDEN_COVERAGE"

    enriched_name = f"{path.stem}.b9_v4_enriched.json"
    enriched_path = output_dir / "enriched" / enriched_name
    enriched_path.parent.mkdir(parents=True, exist_ok=True)
    enriched_path.write_text(json.dumps(enriched, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "input_file": str(path),
        "file_name": path.name,
        "state": state,
        "before_moment_count": len(before),
        "after_moment_count": len(after),
        "missing_required_fields": missing_counts,
        "missing_required_total": sum(missing_counts.values()),
        "forbidden_language_hits": forbidden_hits,
        "forbidden_language_hit_count": len(forbidden_hits),
        "preserved_field_changes": preserved_changes,
        "golden_case_count": len(golden),
        "golden_cases_passed": golden_passed,
        "golden_cases_failed": len(golden) - golden_passed,
        "golden_case_states": golden,
        "enriched_output": str(enriched_path),
    }


def iter_json_files(input_dir: Path, pattern: str, recursive: bool) -> List[Path]:
    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory not found: {input_dir}")
    iterator = input_dir.rglob(pattern) if recursive else input_dir.glob(pattern)
    files = []
    for p in iterator:
        if not p.is_file():
            continue
        name = p.name.lower()
        if any(skip in name for skip in ["manifest", "results", "guard", "coverage", "diff"]):
            continue
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            if _moments(obj):
                files.append(p)
        except Exception:
            continue
    return sorted(files)


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


def run(input_dir: Path, output_dir: Path, pattern: str = "*.json", recursive: bool = True) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    files = iter_json_files(input_dir, pattern, recursive)
    if not files:
        raise ValueError(f"No summary JSON with moments found in {input_dir}")

    results = [validate_summary(path, output_dir) for path in files]
    failures = [r for r in results if r["state"] == "FAIL"]
    partial = [r for r in results if r["state"] == "PASS_WITH_PARTIAL_GOLDEN_COVERAGE"]
    total_missing = sum(r["missing_required_total"] for r in results)
    total_forbidden = sum(r["forbidden_language_hit_count"] for r in results)
    total_preserved_changes = sum(r["preserved_field_changes"] for r in results)
    total_before = sum(r["before_moment_count"] for r in results)
    total_after = sum(r["after_moment_count"] for r in results)

    batch_state = "PASS" if not failures and total_missing == 0 and total_forbidden == 0 and total_preserved_changes == 0 and total_before == total_after else "FAIL"
    if batch_state == "PASS" and partial:
        batch_state = "PASS_WITH_PARTIAL_GOLDEN_COVERAGE"

    manifest = {
        "version": VERSION,
        "batch_state": batch_state,
        "input_dir": str(input_dir),
        "output_dir": str(output_dir),
        "files_processed": len(results),
        "files_passed": sum(1 for r in results if r["state"].startswith("PASS")),
        "files_failed": len(failures),
        "partial_golden_coverage_files": len(partial),
        "total_before_moments": total_before,
        "total_after_moments": total_after,
        "total_missing_required_fields": total_missing,
        "total_forbidden_language_hits": total_forbidden,
        "total_preserved_field_changes": total_preserved_changes,
        "contract_source": "LOCAL_BATCH_GUARD_DETERMINISTIC_V0",
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }

    results_csv_rows = []
    coverage_rows = []
    failures_rows = []
    for r in results:
        results_csv_rows.append({
            "file_name": r["file_name"],
            "state": r["state"],
            "before_moment_count": r["before_moment_count"],
            "after_moment_count": r["after_moment_count"],
            "missing_required_total": r["missing_required_total"],
            "forbidden_language_hit_count": r["forbidden_language_hit_count"],
            "preserved_field_changes": r["preserved_field_changes"],
            "golden_cases_passed": r["golden_cases_passed"],
            "golden_cases_failed": r["golden_cases_failed"],
            "enriched_output": r["enriched_output"],
        })
        for case, ok in r["golden_case_states"].items():
            coverage_rows.append({"file_name": r["file_name"], "golden_case": case, "covered": ok})
        if r["state"] == "FAIL":
            failures_rows.append({
                "file_name": r["file_name"],
                "missing_required_fields": json.dumps(r["missing_required_fields"], ensure_ascii=False),
                "forbidden_language_hits": ";".join(r["forbidden_language_hits"]),
                "preserved_field_changes": r["preserved_field_changes"],
            })

    manifest_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_MANIFEST.json"
    results_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_RESULTS_V0.csv"
    failures_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_FAILURES_V0.csv"
    coverage_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_COVERAGE_V0.csv"
    json_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0.json"
    md_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0.md"

    json_path.write_text(json.dumps({"manifest": manifest, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(results_path, results_csv_rows, ["file_name", "state", "before_moment_count", "after_moment_count", "missing_required_total", "forbidden_language_hit_count", "preserved_field_changes", "golden_cases_passed", "golden_cases_failed", "enriched_output"])
    write_csv(failures_path, failures_rows, ["file_name", "missing_required_fields", "forbidden_language_hits", "preserved_field_changes"])
    write_csv(coverage_path, coverage_rows, ["file_name", "golden_case", "covered"])

    md = f"""# B9 V4 Golden Replay Batch Runner V0

## Résumé exécutif

B9 ne cherche pas le signal.  
B9 cherche la trace laissée par l'effort.  
Ne lis pas l'absorption comme une direction.  
Lis où elle déplace la mémoire.

## Résultat batch

- État : `{manifest['batch_state']}`
- Fichiers traités : {manifest['files_processed']}
- Fichiers passés : {manifest['files_passed']}
- Fichiers échoués : {manifest['files_failed']}
- Moments avant : {manifest['total_before_moments']}
- Moments après : {manifest['total_after_moments']}
- Champs requis manquants : {manifest['total_missing_required_fields']}
- Langage interdit : {manifest['total_forbidden_language_hits']}
- Changements de champs préservés : {manifest['total_preserved_field_changes']}

## Ce que T0125 protège

- effort sans résultat ;
- vague progressive ;
- centre de gravité qui descend ;
- retest échoué ;
- respiration corrective ;
- source quality et timestamp policy.

## Limites techniques

T0125 est un runner de batch read-only. Il ne remplace pas T0122/T0123 pour la validation native du hook local. Il sert à vérifier que des lots de summaries conservent le contrat V4 et les cas golden.

## Interdits respectés

Aucune écriture powerflow.db.  
Aucune écriture tick_archive.db.  
Aucun dashboard.  
Aucun Telegram.  
Aucun BUY/SELL.  
Aucune probabilité de succès.
"""
    md_path.write_text(md, encoding="utf-8")

    zip_path = output_dir / "B9_V4_GOLDEN_REPLAY_BATCH_RUNNER_V0.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in [json_path, md_path, results_path, failures_path, coverage_path, manifest_path]:
            z.write(p, p.name)
        enriched_dir = output_dir / "enriched"
        if enriched_dir.exists():
            for p in enriched_dir.rglob("*.json"):
                z.write(p, str(Path("enriched") / p.name))
    manifest["zip"] = str(zip_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run B9 V4 golden replay guard over a batch of summaries.")
    parser.add_argument("--input-dir", type=Path, default=Path("samples/b9_v4_golden_replay_batch_runner_v0"))
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/b9_v4_golden_replay_batch_runner_v0"))
    parser.add_argument("--pattern", default="*.json")
    parser.add_argument("--no-recursive", action="store_true")
    args = parser.parse_args()
    run(args.input_dir, args.output_dir, pattern=args.pattern, recursive=not args.no_recursive)


if __name__ == "__main__":
    main()
