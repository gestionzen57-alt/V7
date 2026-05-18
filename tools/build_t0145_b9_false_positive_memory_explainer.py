# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_false_positive_memory_explainer import VERSION, explain_summary


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        return data
    if isinstance(data, list):
        return {"moments": data}
    raise ValueError(f"Unsupported JSON root in {path}")


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "moment_id",
        "time_start",
        "time_end",
        "b9_b6_scene_family",
        "b9_b6_memory_family",
        "top_match_film_id",
        "top_match_family",
        "b9_memory_false_positive_state",
        "b9_memory_false_positive_score",
        "b9_memory_false_positive_flags",
        "b9_memory_comparison_state",
        "b9_memory_similarity_caution_fr",
        "b9_memory_difference_explanation_fr",
        "b9_memory_technical_limits",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            out = dict(row)
            for key in ("b9_memory_false_positive_flags", "b9_memory_technical_limits"):
                out[key] = " | ".join(out.get(key, []))
            writer.writerow(out)


def write_counts_csv(path: Path, title: str, counts: Dict[str, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([title, "count"])
        for key, value in sorted(counts.items()):
            writer.writerow([key, value])


def write_md(path: Path, summary: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# T0145 — B9 False Positive Memory Explainer V0")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("B9 lit la scène. B6 compare les films. T0145 explique pourquoi une similarité peut tromper.")
    lines.append("")
    lines.append("La ressemblance n'est pas une répétition. Une mémoire proche reste une comparaison technique, pas une décision d'exécution.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Moments analysés : {summary['moments']}")
    lines.append(f"- Raw unavailable autorisé à tort : {summary['raw_unavailable_allowed_count']}")
    lines.append(f"- Langage interdit : {', '.join(summary['forbidden_language_hits']) if summary['forbidden_language_hits'] else 'aucun'}")
    lines.append("")
    lines.append("## États faux positif mémoire")
    lines.append("")
    for key, value in sorted(summary["state_counts"].items()):
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Drapeaux techniques")
    lines.append("")
    if summary["flag_counts"]:
        for key, value in sorted(summary["flag_counts"].items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- Aucun drapeau technique majeur.")
    lines.append("")
    lines.append("## Lecture par moment")
    lines.append("")
    for row in summary["rows"]:
        lines.append(f"### {row['moment_id']} — {row['time_start']} → {row['time_end']}")
        lines.append("")
        lines.append(f"- Famille scène : `{row['b9_b6_scene_family'] or 'UNKNOWN'}`")
        lines.append(f"- Famille mémoire : `{row['b9_b6_memory_family'] or 'UNKNOWN'}`")
        lines.append(f"- Film proche : `{row['top_match_film_id'] or 'UNKNOWN'}`")
        lines.append(f"- État FP mémoire : `{row['b9_memory_false_positive_state']}`")
        lines.append(f"- Score technique : {row['b9_memory_false_positive_score']}")
        lines.append(f"- Comparaison : `{row['b9_memory_comparison_state']}`")
        lines.append(f"- Lecture : {row['b9_memory_similarity_caution_fr']}")
        lines.append(f"- Différences : {row['b9_memory_difference_explanation_fr']}")
        if row["b9_memory_false_positive_flags"]:
            lines.append(f"- Drapeaux : {', '.join(row['b9_memory_false_positive_flags'])}")
        lines.append("")
    lines.append("## Ce que T0145 ne conclut pas")
    lines.append("")
    lines.append("T0145 ne dit pas que la scène va se répéter. Il ne donne aucune probabilité de résultat et aucun ordre d'exécution.")
    lines.append("")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def create_zip(path: Path, files: List[Path], base: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if file.exists():
                zf.write(file, file.relative_to(base))


def run(args: argparse.Namespace) -> Dict[str, Any]:
    input_path = Path(args.sequence_summary_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    data = read_json(input_path)
    summary = explain_summary(data)

    out_json = output_dir / "B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.json"
    out_md = output_dir / "B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.md"
    out_csv = output_dir / "B9_FALSE_POSITIVE_MEMORY_ROWS_V0.csv"
    out_counts = output_dir / "B9_FALSE_POSITIVE_MEMORY_COUNTS_V0.csv"
    out_flags = output_dir / "B9_FALSE_POSITIVE_MEMORY_FLAGS_V0.csv"
    out_enriched = output_dir / "B9_FALSE_POSITIVE_MEMORY_ENRICHED_SUMMARY_V0.json"
    manifest = output_dir / "B9_FALSE_POSITIVE_MEMORY_EXPLAINER_MANIFEST.json"
    out_zip = output_dir / "B9_FALSE_POSITIVE_MEMORY_EXPLAINER_V0.zip"

    write_json(out_json, {k: v for k, v in summary.items() if k != "enriched_summary"})
    write_json(out_enriched, summary["enriched_summary"])
    write_csv(out_csv, summary["rows"])
    write_counts_csv(out_counts, "state", summary["state_counts"])
    write_counts_csv(out_flags, "flag", summary["flag_counts"])
    write_md(out_md, summary)

    manifest_data = {
        "version": VERSION,
        "input": str(input_path),
        "output_dir": str(output_dir),
        "files": [
            out_json.name,
            out_md.name,
            out_csv.name,
            out_counts.name,
            out_flags.name,
            out_enriched.name,
            manifest.name,
            out_zip.name,
        ],
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "execution_decision": False,
    }
    write_json(manifest, manifest_data)
    create_zip(out_zip, [out_json, out_md, out_csv, out_counts, out_flags, out_enriched, manifest], output_dir)

    return {
        "version": VERSION,
        "moments": summary["moments"],
        "state_counts": summary["state_counts"],
        "raw_unavailable_allowed_count": summary["raw_unavailable_allowed_count"],
        "forbidden_language_hits": summary["forbidden_language_hits"],
        "output_dir": str(output_dir),
        "zip": str(out_zip),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0145 B9 False Positive Memory Explainer V0")
    parser.add_argument("--sequence-summary-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()
    result = run(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
