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

from pf_t009_terrain_node_builder import VERSION, build_nodes, enrich_summary_with_nodes, summarize_nodes


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_counts_csv(path: Path, summary: Dict[str, Any]) -> None:
    rows: List[Dict[str, Any]] = []
    for group_name in ["role_counts", "strength_counts", "relevance_counts"]:
        for key, value in summary.get(group_name, {}).items():
            rows.append({"group": group_name, "name": key, "count": value})
    write_csv(path, rows)


def write_markdown(path: Path, summary: Dict[str, Any], nodes: List[Dict[str, Any]]) -> None:
    lines: List[str] = []
    lines.append("# T0142 — B9 Terrain Node Builder V0")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("B9 ne cherche pas le signal.  ")
    lines.append("B9 cherche la trace laissée par l’effort.  ")
    lines.append("Un node terrain cristallise zone, prix, retest, rôle de scène et limites de source.")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- Nodes: {summary.get('node_count', 0)}")
    lines.append(f"- Missing required fields: {summary.get('missing_required_field_counts', {})}")
    lines.append(f"- Forbidden language hits: {summary.get('forbidden_language_hits', [])}")
    lines.append("")
    for group in ["role_counts", "strength_counts", "relevance_counts"]:
        lines.append(f"## {group}")
        lines.append("")
        for key, value in summary.get(group, {}).items():
            lines.append(f"- {key}: {value}")
        lines.append("")
    lines.append("## Nodes terrain")
    lines.append("")
    for node in nodes:
        lines.append(f"### {node['node_id']} — {node['node_role']}")
        lines.append("")
        lines.append(f"- Temps: {node['time_start']} → {node['time_end']}")
        lines.append(f"- Zone: {node['origin_zone_low']} / {node['origin_zone_center']} / {node['origin_zone_high']}")
        lines.append(f"- Verdict prix: {node['price_verdict']}")
        lines.append(f"- Avant / après: {node['zone_status_before']} → {node['zone_status_after']}")
        lines.append(f"- Source: {node['source_family']} | {node['source_mode']} | {node['data_visibility']} | {node['proxy_vs_raw_verdict']}")
        lines.append(f"- Lecture FR: {node['node_reading_fr']}")
        lines.append(f"- Limites: {node['technical_limits']}")
        lines.append("")
    lines.append("## Ce que B9 ne doit pas conclure")
    lines.append("")
    lines.append("- Aucun ordre d’exécution.")
    lines.append("- Aucune probabilité de succès.")
    lines.append("- Aucune scène proxy durcie en vérité raw.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def zip_outputs(zip_path: Path, files: List[Path], base_dir: Path) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in files:
            if file.exists():
                zf.write(file, file.relative_to(base_dir))


def run(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = load_json(sequence_summary_json)
    nodes = build_nodes(summary)
    node_summary = summarize_nodes(nodes)
    enriched = enrich_summary_with_nodes(summary)

    md_path = output_dir / "B9_TERRAIN_NODE_BUILDER_V0.md"
    json_path = output_dir / "B9_TERRAIN_NODE_BUILDER_V0.json"
    nodes_csv = output_dir / "B9_TERRAIN_NODES_V0.csv"
    counts_csv = output_dir / "B9_TERRAIN_NODE_COUNTS_V0.csv"
    enriched_json = output_dir / "B9_TERRAIN_NODE_ENRICHED_SUMMARY_V0.json"
    manifest_path = output_dir / "B9_TERRAIN_NODE_BUILDER_MANIFEST.json"
    zip_path = output_dir / "B9_TERRAIN_NODE_BUILDER_V0.zip"

    write_markdown(md_path, node_summary, nodes)
    write_json(json_path, {"summary": node_summary, "nodes": nodes})
    write_csv(nodes_csv, nodes)
    write_counts_csv(counts_csv, node_summary)
    write_json(enriched_json, enriched)

    manifest = {
        "version": VERSION,
        "input": str(sequence_summary_json),
        "output_dir": str(output_dir),
        "node_count": node_summary["node_count"],
        "missing_required_field_counts": node_summary["missing_required_field_counts"],
        "forbidden_language_hit_count": len(node_summary["forbidden_language_hits"]),
        "role_counts": node_summary["role_counts"],
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
        "files": [p.name for p in [md_path, json_path, nodes_csv, counts_csv, enriched_json, manifest_path, zip_path]],
    }
    write_json(manifest_path, manifest)
    zip_outputs(zip_path, [md_path, json_path, nodes_csv, counts_csv, enriched_json, manifest_path], output_dir)
    manifest["zip"] = str(zip_path)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build B9 Terrain Node Builder V0 outputs")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = run(args.sequence_summary_json, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
