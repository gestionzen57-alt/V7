from __future__ import annotations

import argparse
import csv
import json
import zipfile
import sys
from pathlib import Path
from typing import Any, Dict, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pf_t009_session_phase_overlay import (
    VERSION,
    enrich_sequence_summary_session_overlay,
    forbidden_hits,
    required_fields,
)

OUTPUT_FILES = [
    "B9_SESSION_PHASE_OVERLAY_V0.md",
    "B9_SESSION_PHASE_OVERLAY_V0.json",
    "B9_SESSION_PHASE_OVERLAY_ROWS_V0.csv",
    "B9_SESSION_PHASE_OVERLAY_COUNTS_V0.csv",
    "B9_SESSION_PHASE_OVERLAY_ENRICHED_SUMMARY_V0.json",
    "B9_SESSION_PHASE_OVERLAY_MANIFEST.json",
    "B9_SESSION_PHASE_OVERLAY_V0.zip",
]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return data


def moments(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    for key in ("moments", "sequence_moments", "b9_moments"):
        value = summary.get(key)
        if isinstance(value, list):
            return value
    return []


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def count_by(rows: List[Dict[str, Any]], key: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for row in rows:
        value = str(row.get(key, "")) or "EMPTY"
        out[value] = out.get(value, 0) + 1
    return out


def build_rows(enriched: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for idx, m in enumerate(moments(enriched), start=1):
        rows.append({
            "moment_index": idx,
            "time_start": m.get("time_start") or m.get("orig_start") or m.get("start") or "",
            "time_start_real": m.get("time_start_real") or m.get("orig_start") or "",
            "label_fr": m.get("label_fr") or m.get("title") or "",
            "b9_session": m.get("b9_session", ""),
            "b9_session_phase": m.get("b9_session_phase", ""),
            "b9_minutes_since_session_open": m.get("b9_minutes_since_session_open", ""),
            "b9_session_bias": m.get("b9_session_bias", ""),
            "b9_session_context_source": m.get("b9_session_context_source", ""),
            "b9_session_reading_fr": m.get("b9_session_reading_fr", ""),
            "b9_session_limits": m.get("b9_session_limits", ""),
        })
    return rows


def missing_required_counts(enriched: Dict[str, Any]) -> Dict[str, int]:
    counts = {field: 0 for field in required_fields()}
    for m in moments(enriched):
        for field in required_fields():
            value = m.get(field)
            if value is None or value == "":
                # minutes_since_session_open can legitimately be blank when timestamp is unknown.
                if field == "b9_minutes_since_session_open" and m.get("b9_session") == "SESSION_UNKNOWN":
                    continue
                counts[field] += 1
    return {k: v for k, v in counts.items() if v}


def make_markdown(manifest: Dict[str, Any], rows: List[Dict[str, Any]]) -> str:
    lines = [
        "# T0132 — B9 Session Phase Overlay V0",
        "",
        "## Résumé exécutif",
        "",
        "B9 Session Phase Overlay ajoute le contexte de session à chaque moment B9.",
        "Il ne décide pas. Il qualifie la scène dans son heure de marché.",
        "",
        "## Doctrine",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "Une scène à London open ne porte pas la même texture qu'une scène en Asian ou dead zone.",
        "",
        "## Counts",
        "",
        f"- moments: {manifest['moments']}",
        f"- missing_required_fields: {manifest['missing_required_field_counts']}",
        f"- forbidden_language_hits: {manifest['forbidden_language_hits']}",
        "",
        "## Counts par session",
        "",
    ]
    for k, v in manifest["session_counts"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Counts par phase", ""]
    for k, v in manifest["phase_counts"].items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## Premiers moments", ""]
    for row in rows[:10]:
        lines.append(
            f"- {row['time_start']} — {row['label_fr']} — {row['b9_session']} / {row['b9_session_phase']} — {row['b9_session_reading_fr']}"
        )
    lines += [
        "",
        "## Limites techniques",
        "",
        "- Le contexte session est une couche de lecture, pas une validation directionnelle.",
        "- Si le timestamp est replay/shifted, T0127 doit rester la source de vérité de remap.",
        "- Aucun accès DB, aucun dashboard, aucun Telegram.",
    ]
    return "\n".join(lines) + "\n"


def run(sequence_summary_json: Path, output_dir: Path) -> Dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary = load_json(sequence_summary_json)
    enriched = enrich_sequence_summary_session_overlay(summary)
    rows = build_rows(enriched)
    missing = missing_required_counts(enriched)
    hits = forbidden_hits(enriched)
    session_counts = count_by(rows, "b9_session")
    phase_counts = count_by(rows, "b9_session_phase")
    state = "PASS" if not missing and not hits and rows else "FAIL"
    manifest = {
        "version": VERSION,
        "session_overlay_state": state,
        "input": str(sequence_summary_json),
        "output_dir": str(output_dir),
        "moments": len(rows),
        "session_counts": session_counts,
        "phase_counts": phase_counts,
        "missing_required_field_counts": missing,
        "forbidden_language_hits": hits,
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
        "buy_sell": False,
        "probability_of_success": False,
    }
    write_json(output_dir / "B9_SESSION_PHASE_OVERLAY_ENRICHED_SUMMARY_V0.json", enriched)
    write_json(output_dir / "B9_SESSION_PHASE_OVERLAY_V0.json", {"manifest": manifest, "rows": rows})
    write_csv(output_dir / "B9_SESSION_PHASE_OVERLAY_ROWS_V0.csv", rows, [
        "moment_index", "time_start", "time_start_real", "label_fr", "b9_session", "b9_session_phase",
        "b9_minutes_since_session_open", "b9_session_bias", "b9_session_context_source", "b9_session_reading_fr", "b9_session_limits",
    ])
    counts_rows = []
    for dimension, counts in (("session", session_counts), ("phase", phase_counts)):
        for key, value in counts.items():
            counts_rows.append({"dimension": dimension, "value": key, "count": value})
    write_csv(output_dir / "B9_SESSION_PHASE_OVERLAY_COUNTS_V0.csv", counts_rows, ["dimension", "value", "count"])
    (output_dir / "B9_SESSION_PHASE_OVERLAY_V0.md").write_text(make_markdown(manifest, rows), encoding="utf-8")
    write_json(output_dir / "B9_SESSION_PHASE_OVERLAY_MANIFEST.json", manifest)
    with zipfile.ZipFile(output_dir / "B9_SESSION_PHASE_OVERLAY_V0.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        for name in OUTPUT_FILES:
            if name.endswith(".zip"):
                continue
            path = output_dir / name
            if path.exists():
                zf.write(path, arcname=name)
    manifest["zip"] = str(output_dir / "B9_SESSION_PHASE_OVERLAY_V0.zip")
    write_json(output_dir / "B9_SESSION_PHASE_OVERLAY_MANIFEST.json", manifest)
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0132 B9 Session Phase Overlay V0")
    parser.add_argument("--sequence-summary-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    manifest = run(args.sequence_summary_json, args.output_dir)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    if manifest["session_overlay_state"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
