from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_zone_memory_object_builder import VERSION, build_zone_memory_objects


def _write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            flat = dict(row)
            for key, value in flat.items():
                if isinstance(value, (list, dict)):
                    flat[key] = json.dumps(value, ensure_ascii=False)
            writer.writerow(flat)


def _write_counts_csv(path: Path, counts: Dict[str, int]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["state", "count"])
        writer.writeheader()
        for state, count in sorted(counts.items()):
            writer.writerow({"state": state, "count": count})


def _write_markdown(path: Path, result: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# T0141 — B9 Zone Memory Object Builder V0")
    lines.append("")
    lines.append("B9 ne cherche pas le signal.")
    lines.append("B9 cherche la trace laissée par l’effort.")
    lines.append("Une zone mémoire est une trace comportementale, pas une décision d’exécution.")
    lines.append("")
    lines.append("## Résumé")
    lines.append("")
    lines.append(f"- Moments en entrée : {result.get('moments_input')}")
    lines.append(f"- Objets zone mémoire : {result.get('zone_object_count')}")
    lines.append(f"- RAW_UNAVAILABLE rejetés : {result.get('rejected_raw_unavailable_moments')}")
    lines.append(f"- Moments sans zone exploitable : {result.get('skipped_no_zone_moments')}")
    lines.append("")
    lines.append("## Counts par état")
    lines.append("")
    for state, count in sorted(result.get("state_counts", {}).items()):
        lines.append(f"- {state}: {count}")
    lines.append("")
    lines.append("## Objets mémoire")
    lines.append("")
    for obj in result.get("zone_objects", []):
        lines.append(f"### {obj['zone_id']}")
        lines.append("")
        lines.append(f"- Zone : {obj['zone_low']} → {obj['zone_high']} | centre {obj['zone_center']}")
        lines.append(f"- Première apparition : {obj['first_seen']}")
        lines.append(f"- Dernier test : {obj['last_tested']}")
        lines.append(f"- État : {obj['zone_memory_state']}")
        lines.append(f"- Rôle dominant : {obj['dominant_scene_role']}")
        lines.append(f"- Source : {obj['source_family']} / {obj['source_mode']} / {obj['data_visibility']}")
        lines.append(f"- Accord raw : {obj['proxy_vs_raw_verdict']}")
        lines.append(f"- Lecture : {obj['zone_memory_reading_fr']}")
        lines.append("- Limites techniques :")
        for limit in obj.get("technical_limits", []):
            lines.append(f"  - {limit}")
        lines.append("")
    lines.append("## Ce que B9 ne peut pas conclure")
    lines.append("")
    lines.append("- Une zone mémoire ne donne pas d’ordre.")
    lines.append("- Une zone proxy ne devient pas une vérité raw.")
    lines.append("- Un état de zone ne donne aucun taux de réussite.")
    lines.append("- RAW_UNAVAILABLE reste exclu de la mémoire active.")
    path.write_text("\n".join(lines), encoding="utf-8")


def run(input_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = json.loads(input_json.read_text(encoding="utf-8"))
    result = build_zone_memory_objects(summary)

    json_path = output_dir / "B9_ZONE_MEMORY_OBJECTS_V0.json"
    csv_path = output_dir / "B9_ZONE_MEMORY_OBJECTS_V0.csv"
    md_path = output_dir / "B9_ZONE_MEMORY_OBJECTS_V0.md"
    counts_path = output_dir / "B9_ZONE_MEMORY_OBJECT_COUNTS_V0.csv"
    manifest_path = output_dir / "B9_ZONE_MEMORY_OBJECT_BUILDER_MANIFEST.json"
    zip_path = output_dir / "B9_ZONE_MEMORY_OBJECT_BUILDER_V0.zip"

    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    _write_csv(csv_path, result.get("zone_objects", []))
    _write_counts_csv(counts_path, result.get("state_counts", {}))
    _write_markdown(md_path, result)

    manifest = {
        "version": VERSION,
        "input": str(input_json),
        "output_dir": str(output_dir),
        "zone_object_count": result.get("zone_object_count"),
        "state_counts": result.get("state_counts"),
        "missing_required_field_counts": result.get("missing_required_field_counts"),
        "forbidden_language_hits": result.get("forbidden_language_hits"),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
        "files": [p.name for p in (json_path, csv_path, md_path, counts_path)],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in (json_path, csv_path, md_path, counts_path, manifest_path):
            zf.write(p, p.name)
    manifest["zip"] = str(zip_path)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B9 zone memory objects from a T009/B9 sequence summary.")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    run(args.sequence_summary_json, args.output_dir)


if __name__ == "__main__":
    main()
