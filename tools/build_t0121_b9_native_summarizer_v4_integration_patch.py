#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import csv
import zipfile
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))
from typing import Any, Dict, List
from pf_t009_sequence_summarizer_v4_contract import REQUIRED_V4_FIELDS, find_forbidden_language
from pf_t009_sequence_summarizer_v4_integration import integration_probe, enrich_summary_v4_safe

VERSION = "T0121_B9_NATIVE_SUMMARIZER_V4_INTEGRATION_PATCH_V0"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments"):
        if isinstance(summary.get(key), list):
            return summary[key]
    return []


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sequence-summary-json", default="samples/b9_native_summarizer_v4_integration_v0/sample_t009_sequence_summary_raw_calibrated.json")
    ap.add_argument("--output-dir", default="outputs/b9_native_summarizer_v4_integration_patch_v0")
    args = ap.parse_args()
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = load_json(Path(args.sequence_summary_json))
    enriched = enrich_summary_v4_safe(summary)
    moments = get_moments(enriched)
    coverage_rows = []
    missing_counts = {field: 0 for field in REQUIRED_V4_FIELDS}
    for idx, moment in enumerate(moments):
        row = {"moment_index": idx, "label_fr": moment.get("label_fr", moment.get("moment_type", ""))}
        for field in REQUIRED_V4_FIELDS:
            ok = field in moment and moment.get(field) not in (None, "")
            row[field] = "OK" if ok else "MISSING"
            if not ok:
                missing_counts[field] += 1
        coverage_rows.append(row)
    missing_counts = {k: v for k, v in missing_counts.items() if v}
    patch_rows = [
        {"patch_area":"native_integration","status":"READY","rule":"call enrich_summary_v4_safe(summary) before summary return/write"},
        {"patch_area":"fail_open","status":"READY","rule":"if V4 import fails, return original summary"},
        {"patch_area":"timestamp_policy","status":"READY","rule":"use original timestamps when present, keep shifted timestamps visible otherwise"},
        {"patch_area":"forbidden_language","status":"READY","rule":"no BUY/SELL/probability of success"},
    ]
    test_rows = [
        {"test":"contract_fields_present","expected":"all required fields present"},
        {"test":"fail_open","expected":"runtime does not break when optional enrichment is unavailable"},
        {"test":"forbidden_language","expected":"no BUY/SELL/probability of success"},
        {"test":"native_hook_marker","expected":"summarizer contains T0121 marker after apply script"},
    ]
    report = {
        "version": VERSION,
        "input_moments": len(moments),
        "missing_required_field_counts": missing_counts,
        "forbidden_language_hits": find_forbidden_language(enriched),
        "integration_probe": integration_probe(),
        "native_patch_strategy":"safe helper + conservative return summary hook",
        "next_step":"T0122_B9_V4_NATIVE_RUNTIME_VALIDATION",
    }
    (out/"B9_NATIVE_SUMMARIZER_V4_INTEGRATION_PATCH_V0.json").write_text(json.dumps({"report": report, "enriched_summary": enriched}, indent=2, ensure_ascii=False), encoding="utf-8")
    md = f"""# T0121 - B9 Native Summarizer V4 Integration Patch

## Resume executif

T0121 branche le contrat B9 V4 dans le summarizer natif par une integration fail-open.

```text
input_moments = {len(moments)}
missing_required_field_counts = {missing_counts}
forbidden_language_hits = {report['forbidden_language_hits']}
```

## Doctrine

B9 ne cherche pas le signal.
B9 cherche la trace laissee par l'effort.
Ne lis pas l'absorption comme une direction.
Lis ou elle deplace la memoire.

## Strategie integration

- Helper fail-open.
- Backup automatique du summarizer.
- Hook conservateur sur return summary.
- Aucun BUY/SELL, aucune probabilite de succes.

## Prochain geste

T0122 - B9 V4 Native Runtime Validation.
"""
    (out/"B9_NATIVE_SUMMARIZER_V4_INTEGRATION_PATCH_V0.md").write_text(md, encoding="utf-8")
    write_csv(out/"B9_NATIVE_SUMMARIZER_V4_FIELD_COVERAGE_V0.csv", coverage_rows, ["moment_index","label_fr"] + REQUIRED_V4_FIELDS)
    write_csv(out/"B9_NATIVE_SUMMARIZER_V4_INTEGRATION_RULES_V0.csv", patch_rows, ["patch_area","status","rule"])
    write_csv(out/"B9_NATIVE_SUMMARIZER_V4_INTEGRATION_TEST_PLAN_V0.csv", test_rows, ["test","expected"])
    manifest = {"version": VERSION, "outputs": sorted(p.name for p in out.iterdir()), **report}
    (out/"B9_NATIVE_SUMMARIZER_V4_INTEGRATION_PATCH_MANIFEST.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    zip_path = out/"B9_NATIVE_SUMMARIZER_V4_INTEGRATION_PATCH_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in out.iterdir():
            if p != zip_path:
                z.write(p, p.name)
    print(json.dumps({**report, "output_dir": str(out), "zip": str(zip_path)}, indent=2, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
