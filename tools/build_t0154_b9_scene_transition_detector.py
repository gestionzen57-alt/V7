from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from typing import Any, Dict, List

from pf_t009_scene_transition_detector import VERSION, detect_scene_transitions


def read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, summary: Dict[str, Any]) -> None:
    lines = [
        "# B9 Scene Transition Detector V0",
        "",
        "## Résumé",
        f"- Version : `{summary['version']}`",
        f"- Moments lus : {summary['moments']}",
        f"- Transitions détectées : {summary['transitions']}",
        f"- Transitions bloquées RAW_UNAVAILABLE : {summary['raw_unavailable_blocked_count']}",
        f"- Langage interdit : {len(summary['forbidden_language_hits'])}",
        "",
        "## Counts par transition",
    ]
    for k, v in summary.get("transition_type_counts", {}).items():
        lines.append(f"- `{k}` : {v}")
    lines += ["", "## Counts par force technique"]
    for k, v in summary.get("transition_strength_counts", {}).items():
        lines.append(f"- `{k}` : {v}")
    lines += ["", "## Transitions"]
    for row in summary.get("rows", []):
        lines += [
            f"### {row['transition_id']} — {row['transition_type']}",
            f"- De : `{row['from_scene_state']}` ({row['from_time_start']} → {row['from_time_end']})",
            f"- Vers : `{row['to_scene_state']}` ({row['to_time_start']} → {row['to_time_end']})",
            f"- Verdict prix : `{row['from_price_verdict']}` → `{row['to_price_verdict']}`",
            f"- Force technique : `{row['transition_strength_state']}`",
            f"- Lecture : {row['transition_reading_fr']}",
            f"- Limites : {row['technical_limits']}",
            "",
        ]
    lines += [
        "## Doctrine",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l’effort.",
        "Une transition de scène qualifie le film ; elle ne produit pas une décision d’exécution.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    p = argparse.ArgumentParser(description="Build T0154 B9 scene transition detector outputs.")
    p.add_argument("--sequence-summary-json", required=True)
    p.add_argument("--output-dir", required=True)
    args = p.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    summary = detect_scene_transitions(read_json(Path(args.sequence_summary_json)))

    write_json(out / "B9_SCENE_TRANSITION_DETECTOR_V0.json", summary)
    write_csv(out / "B9_SCENE_TRANSITIONS_V0.csv", summary["rows"])
    write_csv(out / "B9_SCENE_TRANSITION_COUNTS_V0.csv", [
        {"transition_type": k, "count": v} for k, v in summary["transition_type_counts"].items()
    ])
    write_md(out / "B9_SCENE_TRANSITION_DETECTOR_V0.md", summary)
    manifest = {
        "version": VERSION,
        "output_dir": str(out),
        "files": [
            "B9_SCENE_TRANSITION_DETECTOR_V0.json",
            "B9_SCENE_TRANSITION_DETECTOR_V0.md",
            "B9_SCENE_TRANSITIONS_V0.csv",
            "B9_SCENE_TRANSITION_COUNTS_V0.csv",
        ],
    }
    write_json(out / "B9_SCENE_TRANSITION_DETECTOR_MANIFEST.json", manifest)
    zip_path = out / "B9_SCENE_TRANSITION_DETECTOR_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for name in manifest["files"] + ["B9_SCENE_TRANSITION_DETECTOR_MANIFEST.json"]:
            z.write(out / name, arcname=name)
    print(json.dumps({
        "version": VERSION,
        "moments": summary["moments"],
        "transitions": summary["transitions"],
        "transition_type_counts": summary["transition_type_counts"],
        "raw_unavailable_blocked_count": summary["raw_unavailable_blocked_count"],
        "forbidden_language_hits": summary["forbidden_language_hits"],
        "zip": str(zip_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
