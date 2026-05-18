from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_memory_confidence_ladder import VERSION, enrich_sequence_summary, extract_moments, forbidden_language_hits, REQUIRED_FIELDS


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fields})


def safe_text(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return ""
    return str(value)


def build_rows(enriched: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for idx, m in enumerate(extract_moments(enriched), start=1):
        if not isinstance(m, dict):
            continue
        rows.append({
            "idx": idx,
            "date": m.get("date") or safe_text(m.get("time_start"))[:10],
            "time_start": m.get("time_start", ""),
            "time_end": m.get("time_end", ""),
            "label_fr": m.get("label_fr", ""),
            "b9_scene_role": m.get("b9_scene_role") or m.get("scene_role", ""),
            "b9_scene_family": m.get("b9_scene_family", ""),
            "b9_b6_memory_family": m.get("b9_b6_memory_family", ""),
            "b9_memory_false_positive_state": m.get("b9_memory_false_positive_state", ""),
            "b9_source_quality_gate_state": m.get("b9_source_quality_gate_state", ""),
            "proxy_vs_raw_verdict": m.get("proxy_vs_raw_verdict", ""),
            "source_mode": m.get("source_mode", ""),
            "data_visibility": m.get("data_visibility", ""),
            "retest_visible": m.get("retest_visible", ""),
            "retest_result": m.get("retest_result", ""),
            "b9_memory_comparability_state": m.get("b9_memory_comparability_state", ""),
            "b9_memory_comparability_score": m.get("b9_memory_comparability_score", ""),
            "b9_memory_confidence_ladder_flags": safe_text(m.get("b9_memory_confidence_ladder_flags", [])),
            "b9_memory_confidence_ladder_reading_fr": m.get("b9_memory_confidence_ladder_reading_fr", ""),
            "b9_memory_confidence_ladder_limits": safe_text(m.get("b9_memory_confidence_ladder_limits", [])),
        })
    return rows


def missing_required_counts(enriched: Dict[str, Any]) -> Dict[str, int]:
    counts = Counter()
    for m in extract_moments(enriched):
        if not isinstance(m, dict):
            continue
        for field in REQUIRED_FIELDS:
            if field not in m or m.get(field) in (None, "", []):
                counts[field] += 1
    return dict(counts)


def write_markdown(path: Path, summary: Dict[str, Any], rows: List[Dict[str, Any]], counts: Counter, hits: List[str]) -> None:
    lines = []
    lines.append("# T0146 — B9 Memory Confidence Ladder V0")
    lines.append("")
    lines.append("## Résumé exécutif")
    lines.append("")
    lines.append("T0146 transforme les pièges de mémoire en échelle de comparabilité technique. Ce score qualifie la qualité de comparaison, pas une probabilité de résultat.")
    lines.append("")
    lines.append("```text")
    lines.append("B9 lit la scène.")
    lines.append("B6 compare les films.")
    lines.append("T0146 qualifie si la comparaison mémoire est forte, partielle, limitée, décalée ou rejetée.")
    lines.append("```")
    lines.append("")
    lines.append("## Counts")
    lines.append("")
    lines.append(f"- moments : {len(rows)}")
    for key, value in sorted(counts.items()):
        lines.append(f"- {key} : {value}")
    lines.append(f"- forbidden_language_hits : {len(hits)}")
    lines.append("")
    lines.append("## États")
    lines.append("")
    lines.append("- MEMORY_STRONG_COMPARABLE")
    lines.append("- MEMORY_PARTIAL_COMPARABLE")
    lines.append("- MEMORY_SOURCE_LIMITED")
    lines.append("- MEMORY_SESSION_MISMATCH")
    lines.append("- MEMORY_RETEST_MISSING")
    lines.append("- MEMORY_REJECTED_RAW_UNAVAILABLE")
    lines.append("")
    lines.append("## Lignes mémoire")
    lines.append("")
    for r in rows:
        lines.append(f"### {r['idx']} — {r['time_start']} → {r['time_end']}")
        lines.append(f"- label : {r['label_fr']}")
        lines.append(f"- famille scène : {r['b9_scene_family']}")
        lines.append(f"- famille mémoire : {r['b9_b6_memory_family']}")
        lines.append(f"- état : {r['b9_memory_comparability_state']} ({r['b9_memory_comparability_score']})")
        lines.append(f"- lecture : {r['b9_memory_confidence_ladder_reading_fr']}")
        lines.append(f"- limites : {r['b9_memory_confidence_ladder_limits']}")
        lines.append("")
    lines.append("## Limites")
    lines.append("")
    lines.append("Read-only. Aucune écriture powerflow.db. Aucune écriture tick_archive.db. Aucun dashboard. Aucun Telegram. Aucun ordre directionnel. Aucun taux de réussite.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: List[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Build T0146 B9 Memory Confidence Ladder V0")
    parser.add_argument("--sequence-summary-json", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args(argv)

    in_path = Path(args.sequence_summary_json)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    source = load_json(in_path)
    enriched = enrich_sequence_summary(source)
    rows = build_rows(enriched)
    counts = Counter(r["b9_memory_comparability_state"] for r in rows)
    missing = missing_required_counts(enriched)
    hits = forbidden_language_hits(enriched)
    raw_unavailable_allowed = sum(1 for r in rows if r["b9_memory_comparability_state"] != "MEMORY_REJECTED_RAW_UNAVAILABLE" and "RAW_UNAVAILABLE" in (r.get("proxy_vs_raw_verdict", "") + r.get("b9_source_quality_gate_state", "") + r.get("b9_b6_memory_family", "")))

    out_json = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_V0.json"
    rows_csv = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_ROWS_V0.csv"
    counts_csv = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_COUNTS_V0.csv"
    enriched_json = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_ENRICHED_SUMMARY_V0.json"
    md = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_V0.md"
    manifest = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_MANIFEST.json"
    zip_path = out_dir / "B9_MEMORY_CONFIDENCE_LADDER_V0.zip"

    write_json(enriched_json, enriched)
    write_csv(rows_csv, rows, list(rows[0].keys()) if rows else ["idx"])
    write_csv(counts_csv, [{"state": k, "count": v} for k, v in sorted(counts.items())], ["state", "count"])
    write_markdown(md, enriched, rows, counts, hits)

    summary = {
        "version": VERSION,
        "input": str(in_path),
        "output_dir": str(out_dir),
        "moments": len(rows),
        "state_counts": dict(counts),
        "missing_required_field_counts": missing,
        "forbidden_language_hits": hits,
        "raw_unavailable_allowed_count": raw_unavailable_allowed,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
    }
    write_json(out_json, summary)
    write_json(manifest, {"version": VERSION, "files": [p.name for p in [out_json, rows_csv, counts_csv, enriched_json, md]], "summary": summary})

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for p in [out_json, rows_csv, counts_csv, enriched_json, md, manifest]:
            z.write(p, p.name)

    print(json.dumps({
        "version": VERSION,
        "moments": len(rows),
        "state_counts": dict(counts),
        "missing_required_field_counts": missing,
        "forbidden_language_hits": hits,
        "raw_unavailable_allowed_count": raw_unavailable_allowed,
        "zip": str(zip_path),
    }, ensure_ascii=False, indent=2))
    return summary


if __name__ == "__main__":
    main()
