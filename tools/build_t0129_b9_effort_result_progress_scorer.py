from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_effort_result_progress_scorer import (  # noqa: E402
    VERSION,
    count_states,
    enrich_sequence_summary_effort_result_progress,
    find_forbidden_language,
    missing_required_field_counts,
    preservation_diff,
    rows_from_summary,
)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def write_csv(path: Path, rows: List[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = []
    for row in rows:
        for key in row.keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            clean = {}
            for k in fieldnames:
                v = row.get(k, "")
                if isinstance(v, (list, dict)):
                    clean[k] = json.dumps(v, ensure_ascii=False)
                else:
                    clean[k] = v
            writer.writerow(clean)


def build_markdown(manifest: Mapping[str, Any], state_counts: Mapping[str, int]) -> str:
    lines = [
        "# T0129 — B9 Effort / Résultat / Progrès Scorer V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "Ne lis pas l'absorption comme une direction.",
        "Lis où elle déplace la mémoire.",
        "",
        "T0129 transforme chaque moment B9 en triptyque physique : effort, résultat, progrès.",
        "",
        "## Counts",
        "",
        f"- Moments analysés : {manifest.get('moments', 0)}",
        f"- Champs requis manquants : {manifest.get('total_missing_required_fields', 0)}",
        f"- Langage interdit : {manifest.get('forbidden_language_hit_count', 0)}",
        f"- Champs préservés modifiés : {manifest.get('preserved_field_change_count', 0)}",
        "",
        "## États détectés",
        "",
    ]
    for state, count in sorted(state_counts.items()):
        lines.append(f"- {state}: {count}")
    lines.extend(
        [
            "",
            "## Champs ajoutés",
            "",
            "```text",
            "b9_effort_score",
            "b9_result_score",
            "b9_progress_score",
            "b9_effort_result_ratio",
            "b9_progress_type",
            "b9_movement_role",
            "b9_memory_shift_state",
            "b9_effort_result_progress_state",
            "b9_effort_result_progress_reading_fr",
            "b9_effort_result_progress_limits",
            "```",
            "",
            "## États protégés",
            "",
            "```text",
            "EFFORT_WITHOUT_RESULT",
            "PROGRESSIVE_WAVE",
            "CORRECTIVE_BREATH",
            "CENTER_MIGRATION",
            "FAILED_DISPLACEMENT",
            "ABSORPTION_WITH_PROGRESS",
            "ABSORPTION_WITHOUT_PROGRESS",
            "```",
            "",
            "## Limites techniques",
            "",
            "- Les scores sont relatifs à la source et au microfilm disponible.",
            "- Une scène proxy ne devient jamais une vérité raw.",
            "- T0129 ne produit aucune direction de trade, aucune probabilité, aucun ordre.",
            "- Le retest et la source quality restent visibles comme garde-fous.",
        ]
    )
    return "\n".join(lines) + "\n"


def run(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    before = load_json(sequence_summary_json)
    after = enrich_sequence_summary_effort_result_progress(before)
    missing = missing_required_field_counts(after)
    forbidden = find_forbidden_language(after)
    diffs = preservation_diff(before, after)
    rows = rows_from_summary(after)
    state_counts = count_states(after)

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "B9_EFFORT_RESULT_PROGRESS_ENRICHED_SUMMARY_V0.json", after)
    write_json(output_dir / "B9_EFFORT_RESULT_PROGRESS_V0.json", {
        "version": VERSION,
        "input": str(sequence_summary_json),
        "state_counts": state_counts,
        "missing_required_field_counts": missing,
        "forbidden_language_hits": forbidden,
        "preservation_diff": diffs,
    })
    write_csv(output_dir / "B9_EFFORT_RESULT_PROGRESS_ROWS_V0.csv", rows)
    write_csv(output_dir / "B9_EFFORT_RESULT_PROGRESS_STATE_COUNTS_V0.csv", [
        {"state": state, "count": count} for state, count in sorted(state_counts.items())
    ])
    write_csv(output_dir / "B9_EFFORT_RESULT_PROGRESS_PRESERVATION_DIFF_V0.csv", diffs)

    manifest = {
        "version": VERSION,
        "input": str(sequence_summary_json),
        "output_dir": str(output_dir),
        "moments": len(rows),
        "state_counts": state_counts,
        "missing_required_field_counts": missing,
        "total_missing_required_fields": sum(missing.values()),
        "forbidden_language_hits": forbidden,
        "forbidden_language_hit_count": len(forbidden),
        "preserved_field_change_count": len(diffs),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
    md = build_markdown(manifest, state_counts)
    (output_dir / "B9_EFFORT_RESULT_PROGRESS_V0.md").write_text(md, encoding="utf-8")
    write_json(output_dir / "B9_EFFORT_RESULT_PROGRESS_MANIFEST.json", manifest)

    zip_path = output_dir / "B9_EFFORT_RESULT_PROGRESS_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in output_dir.iterdir():
            if file.is_file() and file != zip_path:
                zf.write(file, file.name)
    manifest["zip"] = str(zip_path)
    write_json(output_dir / "B9_EFFORT_RESULT_PROGRESS_MANIFEST.json", manifest)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in output_dir.iterdir():
            if file.is_file() and file != zip_path:
                zf.write(file, file.name)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0129 B9 Effort / Result / Progress Scorer outputs.")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = run(args.sequence_summary_json, args.output_dir)
    print(json.dumps(manifest, indent=2, ensure_ascii=False))
    if manifest["total_missing_required_fields"] or manifest["forbidden_language_hit_count"] or manifest["preserved_field_change_count"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
