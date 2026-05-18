#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List

# Allow running from repository root or from extracted package.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_sequence_summarizer_v4_contract import (  # noqa: E402
    VERSION,
    enrich_sequence_summary_v4,
    summarize_contract_coverage,
)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_field_coverage_rows(coverage: Dict[str, Any]) -> List[Dict[str, Any]]:
    total = int(coverage.get("moment_count") or 0)
    rows = []
    for field in coverage.get("required_fields", []):
        count = coverage.get("field_coverage_counts", {}).get(field, 0)
        rows.append({
            "field": field,
            "covered_moments": count,
            "total_moments": total,
            "missing_moments": max(total - int(count), 0),
            "coverage_ratio": round((int(count) / total), 4) if total else 0,
        })
    return rows


def build_rules_rows() -> List[Dict[str, Any]]:
    return [
        {
            "rule_id": "T0120_R01",
            "rule": "V1_WHY_HOW_NATIVE",
            "native_fields": "what_happens_fr|why_it_matters_fr|how_it_happened_fr|mechanism_fr|proof_summary_fr",
            "purpose": "Explain the moment without converting it into a signal.",
            "forbidden": "BUY/SELL/probability of success",
        },
        {
            "rule_id": "T0120_R02",
            "rule": "V2_SCENE_CAUSALITY_NATIVE",
            "native_fields": "previous_context_fr|cause_fr|reaction_fr|consequence_fr|memory_shift_fr|retest_role_fr",
            "purpose": "Link moments as cause, reaction, consequence, memory shift.",
            "forbidden": "hard causal certainty when source is proxy/reconstructed",
        },
        {
            "rule_id": "T0120_R03",
            "rule": "V3_FRACTAL_SCENE_NATIVE",
            "native_fields": "scene_id|scene_role|parent_scene|child_moments|session_chapter|fractal_reading_fr",
            "purpose": "Connect microfilm, moment, scene, and chapter.",
            "forbidden": "new heavy spine or dashboard dependency",
        },
        {
            "rule_id": "T0120_R04",
            "rule": "CENTER_PATH_INTERNAL_FILM",
            "native_fields": "b9_center_path_state",
            "purpose": "Avoid start/end blindness by preserving center path reading.",
            "forbidden": "classifying a scene only from first/last value when internal path matters",
        },
        {
            "rule_id": "T0120_R05",
            "rule": "EFFORT_RESULT_PROGRESS_NATIVE",
            "native_fields": "b9_effort_result_progress_state|b9_progress_type",
            "purpose": "Separate effort, result, and progress in native B9 language.",
            "forbidden": "reading absorption as direction",
        },
        {
            "rule_id": "T0120_R06",
            "rule": "NATIVE_RETEST_JUDGE",
            "native_fields": "b9_native_retest_judgment|retest_role_fr",
            "purpose": "Make retest visibility and judgment explicit.",
            "forbidden": "validating a break if retest is not visible",
        },
        {
            "rule_id": "T0120_R07",
            "rule": "SOURCE_QUALITY_NATIVE",
            "native_fields": "b9_source_quality_native_state|proof_summary_fr",
            "purpose": "Keep raw/proxy/source quality visible in every moment.",
            "forbidden": "hardening proxy into raw truth",
        },
        {
            "rule_id": "T0120_R08",
            "rule": "TIMESTAMP_POLICY_NATIVE",
            "native_fields": "b9_v4_timestamp_policy",
            "purpose": "Preserve canonical time fields and flag shifted/replay handling explicitly.",
            "forbidden": "hidden shifted/replay timestamps in final report",
        },
    ]


def build_test_plan_rows() -> List[Dict[str, Any]]:
    return [
        {"test_id": "T0120_TEST_01", "target": "syntax", "command": "python -m py_compile pf_t009_sequence_summarizer_v4_contract.py tools\\build_t0120_b9_native_summarizer_v4_contract_patch.py", "expected": "success"},
        {"test_id": "T0120_TEST_02", "target": "unit", "command": "python -m pytest tests\\test_t0120_b9_native_summarizer_v4_contract_patch.py", "expected": "2 passed"},
        {"test_id": "T0120_TEST_03", "target": "field coverage", "command": "CLI validation", "expected": "all required V1/V2/V3/V4 fields covered on all moments"},
        {"test_id": "T0120_TEST_04", "target": "forbidden language", "command": "scan enriched summary", "expected": "no BUY/SELL/probability hits"},
        {"test_id": "T0120_TEST_05", "target": "retest visibility", "command": "inspect b9_native_retest_judgment", "expected": "NOT_VISIBLE remains explicit and not hardened"},
    ]


def build_report(enriched: Dict[str, Any], coverage: Dict[str, Any], output_dir: Path) -> str:
    moments = enriched.get("moments", [])
    erp_counts = coverage.get("effort_result_progress_counts", {})
    retest_counts = coverage.get("native_retest_judgment_counts", {})
    forbidden = coverage.get("forbidden_language_hits", [])
    return f"""# T0120 — B9 Native Summarizer V4 Contract Patch

## Résumé exécutif

T0120 ajoute un contrat V4 natif testable pour les summaries T009/B9.

Il ne remplace pas le moteur et ne modifie aucune base. Il fournit une couche pure Python que `pf_t009_sequence_summarizer.py` peut appeler avant l'écriture JSON/Markdown.

Phrase de cap :

```text
B9 ne cherche pas le signal.
B9 cherche la trace laissée par l'effort.
Ne lis pas l'absorption comme une direction.
Lis où elle déplace la mémoire.
```

## Résultat CLI

```text
version = {VERSION}
input_moments = {len(moments)}
forbidden_language_hits = {forbidden}
output_dir = {output_dir}
```

## Champs natifs ajoutés

### V1 — Why / How

```text
what_happens_fr
why_it_matters_fr
how_it_happened_fr
mechanism_fr
proof_summary_fr
```

### V2 — Scene Causality

```text
previous_context_fr
cause_fr
reaction_fr
consequence_fr
memory_shift_fr
retest_role_fr
```

### V3 — Fractal Scene

```text
scene_id
scene_role
parent_scene
child_moments
session_chapter
fractal_reading_fr
```

### V4 — B9 native contract

```text
b9_center_path_state
b9_effort_result_progress_state
b9_progress_type
b9_native_retest_judgment
b9_source_quality_native_state
b9_v4_timestamp_policy
```

## Counts effort / résultat / progrès

```json
{json.dumps(erp_counts, ensure_ascii=False, indent=2)}
```

## Counts retest natif

```json
{json.dumps(retest_counts, ensure_ascii=False, indent=2)}
```

## Intégration recommandée dans le summarizer

```python
from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4

summary = build_existing_t009_summary(...)
summary = enrich_sequence_summary_v4(summary)
write_summary(summary)
```

## Limites techniques

```text
Read-only.
Aucune écriture powerflow.db.
Aucune écriture tick_archive.db.
Aucun dashboard.
Aucun Telegram.
Aucun BUY/SELL.
Aucune probabilité de succès.
Les champs proxy restent proxy.
Un retest non visible reste non visible.
La politique timestamp ne réécrit pas silencieusement les heures shifted/replay.
```

## Prochaine brique

```text
T0121 — B9 Native Summarizer V4 Integration Patch
```

Objectif : brancher ce contrat dans `pf_t009_sequence_summarizer.py` si la revue architecte valide l'interface.
"""


def build_patch_text() -> str:
    return """diff --git a/pf_t009_sequence_summarizer.py b/pf_t009_sequence_summarizer.py
--- a/pf_t009_sequence_summarizer.py
+++ b/pf_t009_sequence_summarizer.py
@@
+# T0120 integration sketch only.
+# Add near imports after architecture review:
+# from pf_t009_sequence_summarizer_v4_contract import enrich_sequence_summary_v4
@@
-# write_summary(summary)
+# summary = enrich_sequence_summary_v4(summary)
+# write_summary(summary)
"""


def make_zip(zip_path: Path, files: Iterable[Path], root: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if file.exists() and file.is_file():
                zf.write(file, file.relative_to(root).as_posix())


def main() -> int:
    parser = argparse.ArgumentParser(description="Build T0120 B9 native summarizer V4 contract outputs")
    parser.add_argument("--sequence-summary-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    input_path = Path(args.sequence_summary_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = load_json(input_path)
    enriched = enrich_sequence_summary_v4(summary)
    coverage = summarize_contract_coverage(enriched)

    enriched_json = output_dir / "B9_NATIVE_SUMMARIZER_V4_CONTRACT_PATCH_V0.json"
    report_md = output_dir / "B9_NATIVE_SUMMARIZER_V4_CONTRACT_PATCH_V0.md"
    coverage_csv = output_dir / "B9_NATIVE_SUMMARIZER_V4_FIELD_COVERAGE_V0.csv"
    rules_csv = output_dir / "B9_NATIVE_SUMMARIZER_V4_PATCH_RULES_V0.csv"
    test_csv = output_dir / "B9_NATIVE_SUMMARIZER_V4_TEST_PLAN_V0.csv"
    patch_txt = output_dir / "B9_NATIVE_SUMMARIZER_V4_INTEGRATION_SKETCH.patch"
    manifest_json = output_dir / "B9_NATIVE_SUMMARIZER_V4_CONTRACT_PATCH_MANIFEST.json"
    zip_path = output_dir / "B9_NATIVE_SUMMARIZER_V4_CONTRACT_PATCH_V0.zip"

    write_json(enriched_json, enriched)
    write_text(report_md, build_report(enriched, coverage, output_dir))
    write_csv(coverage_csv, build_field_coverage_rows(coverage), ["field", "covered_moments", "total_moments", "missing_moments", "coverage_ratio"])
    write_csv(rules_csv, build_rules_rows(), ["rule_id", "rule", "native_fields", "purpose", "forbidden"])
    write_csv(test_csv, build_test_plan_rows(), ["test_id", "target", "command", "expected"])
    write_text(patch_txt, build_patch_text())

    manifest = {
        "version": VERSION,
        "input": str(input_path),
        "output_dir": str(output_dir),
        "input_moments": len(enriched.get("moments", [])),
        "missing_required_field_counts": coverage.get("missing_required_field_counts", {}),
        "forbidden_language_hits": coverage.get("forbidden_language_hits", []),
        "effort_result_progress_counts": coverage.get("effort_result_progress_counts", {}),
        "native_retest_judgment_counts": coverage.get("native_retest_judgment_counts", {}),
        "files": [p.name for p in [enriched_json, report_md, coverage_csv, rules_csv, test_csv, patch_txt, manifest_json, zip_path]],
        "policies": ["read-only", "no DB write", "no dashboard", "no Telegram", "no BUY/SELL", "no probability of success"],
    }
    write_json(manifest_json, manifest)
    make_zip(zip_path, [enriched_json, report_md, coverage_csv, rules_csv, test_csv, patch_txt, manifest_json], output_dir)

    print(json.dumps({
        "version": VERSION,
        "input_moments": manifest["input_moments"],
        "missing_required_field_counts": manifest["missing_required_field_counts"],
        "forbidden_language_hits": manifest["forbidden_language_hits"],
        "output_dir": str(output_dir),
        "zip": str(zip_path),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
