from __future__ import annotations

import argparse
import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Mapping
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_french_trader_scene_report import VERSION, build_scene_report, to_markdown


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected object JSON in {path}")
    return data


def write_csv(path: Path, rows: List[Mapping[str, Any]]) -> None:
    fields = [
        "moment_index",
        "time_range",
        "title_fr",
        "ce_que_b9_voit",
        "d_ou_vient_le_prix",
        "zone_active",
        "effort_visible",
        "resultat_obtenu",
        "progres_reel",
        "retest_qui_juge",
        "memoire_deplacee",
        "film_b6_proche",
        "pieges_techniques",
        "ce_que_b9_ne_peut_pas_conclure",
        "source_family",
        "source_mode",
        "data_visibility",
        "source_quality_gate_state",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))


def write_counts_csv(path: Path, counts: Mapping[str, int]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["state", "count"])
        writer.writeheader()
        for state, count in sorted(counts.items()):
            writer.writerow({"state": state, "count": count})


def zip_outputs(output_dir: Path, zip_path: Path) -> None:
    names = [
        "B9_FRENCH_TRADER_SCENE_REPORT_V0.md",
        "B9_FRENCH_TRADER_SCENE_REPORT_V0.json",
        "B9_FRENCH_TRADER_SCENE_REPORT_ROWS_V0.csv",
        "B9_FRENCH_TRADER_SCENE_REPORT_SOURCE_COUNTS_V0.csv",
        "B9_FRENCH_TRADER_SCENE_REPORT_MANIFEST.json",
    ]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name in names:
            p = output_dir / name
            if p.exists():
                zf.write(p, arcname=name)


def run(sequence_summary_json: Path, output_dir: Path, memory_brief_json: Path | None = None, top_k: int | None = None) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = load_json(sequence_summary_json)
    memory_brief = load_json(memory_brief_json) if memory_brief_json else None
    report = build_scene_report(summary, memory_brief, top_k=top_k)

    md_path = output_dir / "B9_FRENCH_TRADER_SCENE_REPORT_V0.md"
    json_path = output_dir / "B9_FRENCH_TRADER_SCENE_REPORT_V0.json"
    rows_path = output_dir / "B9_FRENCH_TRADER_SCENE_REPORT_ROWS_V0.csv"
    counts_path = output_dir / "B9_FRENCH_TRADER_SCENE_REPORT_SOURCE_COUNTS_V0.csv"
    manifest_path = output_dir / "B9_FRENCH_TRADER_SCENE_REPORT_MANIFEST.json"
    zip_path = output_dir / "B9_FRENCH_TRADER_SCENE_REPORT_V0.zip"

    md_path.write_text(to_markdown(report), encoding="utf-8")
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    write_csv(rows_path, list(report.get("moment_reports", [])))
    write_counts_csv(counts_path, report.get("source_quality_state_counts", {}))

    manifest = {
        "version": VERSION,
        "report_state": report.get("report_state"),
        "moments": report.get("moments"),
        "forbidden_language_hit_count": len(report.get("forbidden_language_hits", [])),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "order_execution": False,
        "probability_of_success": False,
        "sequence_summary_json": str(sequence_summary_json),
        "memory_brief_json": str(memory_brief_json) if memory_brief_json else None,
        "outputs": {
            "markdown": str(md_path),
            "json": str(json_path),
            "rows_csv": str(rows_path),
            "counts_csv": str(counts_path),
            "manifest": str(manifest_path),
            "zip": str(zip_path),
        },
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    zip_outputs(output_dir, zip_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0134 B9 French Trader Scene Report V0")
    parser.add_argument("--sequence-summary-json", required=True)
    parser.add_argument("--memory-brief-json", default=None)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--top-k", type=int, default=None)
    args = parser.parse_args()

    manifest = run(
        sequence_summary_json=Path(args.sequence_summary_json),
        memory_brief_json=Path(args.memory_brief_json) if args.memory_brief_json else None,
        output_dir=Path(args.output_dir),
        top_k=args.top_k,
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
