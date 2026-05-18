from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_center_path_internal_film import (  # noqa: E402
    REQUIRED_FIELDS,
    VERSION,
    enrich_sequence_summary_center_path,
    forbidden_language_hits,
    preservation_diff,
    required_field_coverage,
)


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def moments(summary: Any) -> List[Mapping[str, Any]]:
    if isinstance(summary, list):
        return [m for m in summary if isinstance(m, Mapping)]
    if isinstance(summary, Mapping):
        for key in ("moments", "items", "scenes"):
            value = summary.get(key)
            if isinstance(value, list):
                return [m for m in value if isinstance(m, Mapping)]
    return []


def write_csv(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: _cell(row.get(k)) for k in fields})


def _cell(value: Any) -> Any:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return value


def markdown_report(manifest: Dict[str, Any], shape_counts: Counter, visibility_counts: Counter, state_counts: Counter) -> str:
    lines = [
        "# T0130 — B9 Center Path Internal Film V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne juge plus seulement deux photos du centre (`center_start -> center_end`).",
        "T0130 ajoute une lecture du film interne du centre : chemin, range, excursions, inflexions, forme et limites.",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l’effort.",
        "Ne lis pas l’absorption comme une direction.",
        "Lis où elle déplace la mémoire.",
        "",
        "## Counts",
        "",
        f"- Moments lus : {manifest['moments']}",
        f"- Champs requis manquants : {manifest['total_missing_required_fields']}",
        f"- Hits langage interdit : {manifest['forbidden_language_hit_count']}",
        f"- Changements champs préservés : {manifest['preserved_field_changes']}",
        "",
        "## Visibility",
        "",
    ]
    for key, value in sorted(visibility_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Shapes", ""])
    for key, value in sorted(shape_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Internal progress states", ""])
    for key, value in sorted(state_counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Limites techniques",
        "",
        "- Si le chemin natif n’est pas visible, T0130 expose `CENTER_PATH_START_END_ONLY` ou `CENTER_PATH_PROXY_EXTREMES`.",
        "- Les extrêmes dérivés ne sont pas durcis comme chronologie raw.",
        "- Le score de chemin interne n’est pas une décision de trade.",
        "- Aucun BUY/SELL, aucune probabilité de succès.",
        "",
        "## Prochaine brique",
        "",
        "T0131 — B9 Memory Brief Injector V0, à exécuter en GPT Pro étendue.",
    ])
    return "\n".join(lines) + "\n"


def run(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    before = load_json(sequence_summary_json)
    before_moments = moments(before)
    after = enrich_sequence_summary_center_path(before)
    after_moments = moments(after)

    coverage = required_field_coverage(after_moments)
    missing_rows = [{"field": field, "missing_count": count} for field, count in coverage.items()]
    total_missing = sum(coverage.values())
    hits = forbidden_language_hits(after)
    diffs = preservation_diff(before_moments, after_moments)

    shape_counts = Counter(str(m.get("b9_center_path_shape", "")) for m in after_moments)
    visibility_counts = Counter(str(m.get("b9_center_path_visibility", "")) for m in after_moments)
    state_counts = Counter(str(m.get("b9_internal_progress_state", "")) for m in after_moments)

    rows = []
    for i, m in enumerate(after_moments, start=1):
        rows.append(
            {
                "moment_index": i,
                "time_start": m.get("time_start") or m.get("start_time"),
                "time_end": m.get("time_end") or m.get("end_time"),
                "label_fr": m.get("label_fr"),
                "moment_type": m.get("moment_type"),
                "b9_center_path_visibility": m.get("b9_center_path_visibility"),
                "b9_center_path_points": m.get("b9_center_path_points"),
                "b9_center_start": m.get("b9_center_start"),
                "b9_center_end": m.get("b9_center_end"),
                "b9_center_min": m.get("b9_center_min"),
                "b9_center_max": m.get("b9_center_max"),
                "b9_center_range_pips": m.get("b9_center_range_pips"),
                "b9_center_net_delta_pips": m.get("b9_center_net_delta_pips"),
                "b9_center_max_favorable_excursion_pips": m.get("b9_center_max_favorable_excursion_pips"),
                "b9_center_max_adverse_excursion_pips": m.get("b9_center_max_adverse_excursion_pips"),
                "b9_center_inflexion_count": m.get("b9_center_inflexion_count"),
                "b9_center_path_shape": m.get("b9_center_path_shape"),
                "b9_internal_progress_state": m.get("b9_internal_progress_state"),
                "b9_center_path_reading_fr": m.get("b9_center_path_reading_fr"),
            }
        )

    manifest: Dict[str, Any] = {
        "version": VERSION,
        "input": str(sequence_summary_json),
        "output_dir": str(output_dir),
        "moments": len(after_moments),
        "total_missing_required_fields": total_missing,
        "missing_required_field_counts": coverage,
        "forbidden_language_hits": hits,
        "forbidden_language_hit_count": len(hits),
        "preserved_field_changes": len(diffs),
        "shape_counts": dict(shape_counts),
        "visibility_counts": dict(visibility_counts),
        "internal_progress_state_counts": dict(state_counts),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }

    save_json(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_V0.json", {"manifest": manifest, "enriched_summary": after})
    save_json(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_ENRICHED_SUMMARY_V0.json", after)
    save_json(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_MANIFEST.json", manifest)

    write_csv(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_ROWS_V0.csv", rows, list(rows[0].keys()) if rows else ["moment_index"])
    write_csv(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_FIELD_COVERAGE_V0.csv", missing_rows, ["field", "missing_count"])
    write_csv(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_PRESERVATION_DIFF_V0.csv", diffs, ["moment_index", "field", "before", "after"])

    report = markdown_report(manifest, shape_counts, visibility_counts, state_counts)
    (output_dir / "B9_CENTER_PATH_INTERNAL_FILM_V0.md").write_text(report, encoding="utf-8")

    zip_path = output_dir / "B9_CENTER_PATH_INTERNAL_FILM_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(output_dir.iterdir()):
            if p.is_file() and p.name != zip_path.name:
                z.write(p, p.name)
    manifest["zip"] = str(zip_path)
    save_json(output_dir / "B9_CENTER_PATH_INTERNAL_FILM_MANIFEST.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0130 B9 Center Path Internal Film V0 outputs.")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = run(args.sequence_summary_json, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
