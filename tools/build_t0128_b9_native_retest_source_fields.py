from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_native_retest_source_fields import (  # noqa: E402
    VERSION,
    REQUIRED_RETEST_FIELDS,
    enrich_sequence_summary_with_native_retest_fields,
    find_forbidden_language,
    find_missing_required_fields,
)

OUTPUT_FILES = [
    "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.md",
    "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.json",
    "B9_NATIVE_RETEST_SOURCE_FIELDS_ROWS_V0.csv",
    "B9_NATIVE_RETEST_SOURCE_FIELDS_COUNTS_V0.csv",
    "B9_NATIVE_RETEST_SOURCE_FIELDS_ENRICHED_SUMMARY_V0.json",
    "B9_NATIVE_RETEST_SOURCE_FIELDS_MANIFEST.json",
]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as f:
        payload = json.load(f)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")


def rows_from_summary(summary: Mapping[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for idx, moment in enumerate(summary.get("moments", []) or [], start=1):
        if not isinstance(moment, Mapping):
            continue
        rows.append(
            {
                "row": idx,
                "time_start": moment.get("time_start") or moment.get("start_time") or "",
                "time_end": moment.get("time_end") or moment.get("end_time") or "",
                "label_fr": moment.get("label_fr") or moment.get("moment_type") or "",
                "retest_visible": moment.get("retest_visible"),
                "retest_source": moment.get("retest_source"),
                "retest_zone": moment.get("retest_zone"),
                "retest_start": moment.get("retest_start"),
                "retest_end": moment.get("retest_end"),
                "retest_result": moment.get("retest_result"),
                "retest_judgment_fr": moment.get("retest_judgment_fr"),
                "source_mode": moment.get("source_mode") or "",
                "data_visibility": moment.get("data_visibility") or "",
                "proxy_vs_raw_verdict": moment.get("proxy_vs_raw_verdict") or "",
            }
        )
    return rows


def write_csv(path: Path, rows: List[Mapping[str, Any]], fieldnames: Iterable[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(fieldnames))
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in writer.fieldnames})


def markdown_report(manifest: Mapping[str, Any], rows: List[Mapping[str, Any]]) -> str:
    counts = manifest["retest_result_counts"]
    lines = [
        "# T0128 — B9 Native Retest Source Fields / T0111B",
        "",
        "## Résumé exécutif",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l’effort.",
        "Le retest juge une scène, il ne produit pas un ordre.",
        "",
        "T0128 enrichit chaque moment B9 avec des champs retest natifs explicites : visible, source, zone, fenêtre, résultat, jugement FR et limites.",
        "",
        "## Counts",
        "",
        f"- moments: {manifest['moments']}",
        f"- retest_visible: {manifest['retest_visible_count']}",
        f"- retest_not_visible: {manifest['retest_not_visible_count']}",
        f"- missing_required_field_counts: {manifest['missing_required_field_counts']}",
        f"- forbidden_language_hits: {manifest['forbidden_language_hits']}",
        "",
        "## Retest result counts",
        "",
    ]
    for key, value in sorted(counts.items()):
        lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Champs natifs",
            "",
        ]
    )
    for field in REQUIRED_RETEST_FIELDS:
        lines.append(f"- `{field}`")
    lines.extend(
        [
            "",
            "## Scènes retest visibles",
            "",
        ]
    )
    visible_rows = [r for r in rows if str(r.get("retest_visible")).lower() == "true"][:20]
    if not visible_rows:
        lines.append("Aucun retest visible dans le sample.")
    else:
        for row in visible_rows:
            lines.append(
                f"- {row.get('time_start')} → {row.get('time_end')} | {row.get('label_fr')} | {row.get('retest_result')} | {row.get('retest_judgment_fr')}"
            )
    lines.extend(
        [
            "",
            "## Limites techniques",
            "",
            "- Un retest non visible reste `RETEST_NOT_VISIBLE`.",
            "- Une scène proxy ne devient pas une vérité raw.",
            "- Le jugement retest est un contexte de scène, pas une décision de trading.",
            "- Aucune écriture `powerflow.db` ou `tick_archive.db`.",
            "- Aucun dashboard, aucun Telegram, aucun BUY/SELL, aucune probabilité de succès.",
        ]
    )
    return "\n".join(lines) + "\n"


def make_zip(output_dir: Path) -> Path:
    zip_path = output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for name in OUTPUT_FILES:
            path = output_dir / name
            if path.exists():
                zf.write(path, arcname=name)
    return zip_path


def run(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    payload = load_json(sequence_summary_json)
    enriched = enrich_sequence_summary_with_native_retest_fields(payload)
    rows = rows_from_summary(enriched)

    retest_counts = Counter(str(row.get("retest_result") or "") for row in rows)
    visible_count = sum(1 for row in rows if str(row.get("retest_visible")).lower() == "true")
    missing = find_missing_required_fields(enriched)
    forbidden = find_forbidden_language(enriched)

    manifest: Dict[str, Any] = {
        "version": "T0128_B9_NATIVE_RETEST_SOURCE_FIELDS_V0",
        "native_retest_source_fields_version": VERSION,
        "input": str(sequence_summary_json),
        "output_dir": str(output_dir),
        "moments": len(rows),
        "retest_visible_count": visible_count,
        "retest_not_visible_count": len(rows) - visible_count,
        "retest_result_counts": dict(sorted(retest_counts.items())),
        "missing_required_field_counts": missing,
        "forbidden_language_hits": forbidden,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }

    write_json(output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_ENRICHED_SUMMARY_V0.json", enriched)
    write_json(output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.json", {"manifest": manifest, "rows": rows})
    write_csv(
        output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_ROWS_V0.csv",
        rows,
        [
            "row",
            "time_start",
            "time_end",
            "label_fr",
            "retest_visible",
            "retest_source",
            "retest_zone",
            "retest_start",
            "retest_end",
            "retest_result",
            "retest_judgment_fr",
            "source_mode",
            "data_visibility",
            "proxy_vs_raw_verdict",
        ],
    )
    count_rows = [{"retest_result": k, "count": v} for k, v in sorted(retest_counts.items())]
    write_csv(output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_COUNTS_V0.csv", count_rows, ["retest_result", "count"])
    (output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_V0.md").write_text(markdown_report(manifest, rows), encoding="utf-8")
    zip_path = make_zip(output_dir)
    manifest["zip"] = str(zip_path)
    write_json(output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_MANIFEST.json", manifest)
    # Refresh zip with final manifest.
    zip_path = make_zip(output_dir)
    manifest["zip"] = str(zip_path)
    write_json(output_dir / "B9_NATIVE_RETEST_SOURCE_FIELDS_MANIFEST.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="T0128 B9 native retest source fields / T0111B")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = run(args.sequence_summary_json, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
