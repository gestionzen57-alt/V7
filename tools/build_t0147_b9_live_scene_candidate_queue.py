from __future__ import annotations

import argparse
import csv
import json
import os
from pathlib import Path
import sys
import zipfile
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_scene_candidate_queue import VERSION, build_queue, csv_rows, markdown_report


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{}]
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def make_zip(output_dir: Path) -> Path:
    zip_path = output_dir / "B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.zip"
    members = [p for p in output_dir.iterdir() if p.is_file() and p.name != zip_path.name]
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in members:
            z.write(p, arcname=p.name)
    return zip_path


def main(argv: list[str] | None = None) -> Dict[str, Any]:
    parser = argparse.ArgumentParser(description="Build T0147 B9 live scene candidate queue V0")
    parser.add_argument("--sequence-summary-json", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--max-candidates", type=int, default=12)
    args = parser.parse_args(argv)

    input_path = Path(args.sequence_summary_json)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    summary = load_json(input_path)
    result = build_queue(summary, max_candidates=args.max_candidates)
    queue = result.get("queue", []) or []
    rejected = result.get("rejected", []) or []
    low_signal = result.get("low_signal", []) or []

    write_json(output_dir / "B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json", result)
    write_json(output_dir / "B9_LATEST_SCENE_CANDIDATE_V0.json", result.get("latest_scene_candidate") or {})
    (output_dir / "B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.md").write_text(markdown_report(result), encoding="utf-8", newline="\n")
    write_csv(output_dir / "B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.csv", csv_rows(queue))
    write_csv(output_dir / "B9_LIVE_SCENE_CANDIDATE_REJECTED_V0.csv", csv_rows(rejected))
    write_csv(output_dir / "B9_LIVE_SCENE_CANDIDATE_LOW_SIGNAL_V0.csv", csv_rows(low_signal))
    manifest = {
        "version": VERSION,
        "input": str(input_path),
        "output_dir": str(output_dir),
        "outputs": sorted([p.name for p in output_dir.iterdir() if p.is_file()]),
        "read_only": True,
        "db_write": False,
        "dashboard": False,
        "telegram": False,
    }
    write_json(output_dir / "B9_LIVE_SCENE_CANDIDATE_QUEUE_MANIFEST.json", manifest)
    zip_path = make_zip(output_dir)

    summary_out = {
        "version": VERSION,
        "queue_state": result.get("queue_state"),
        "moments_seen": result.get("moments_seen"),
        "candidates_active": result.get("candidates_active"),
        "candidates_ready": result.get("candidates_ready"),
        "candidates_review": result.get("candidates_review"),
        "candidates_rejected": result.get("candidates_rejected"),
        "latest_candidate_id": (result.get("latest_scene_candidate") or {}).get("candidate_id") if isinstance(result.get("latest_scene_candidate"), dict) else None,
        "forbidden_language_hits": result.get("forbidden_language_hits"),
        "zip": str(zip_path),
    }
    print(json.dumps(summary_out, ensure_ascii=False, indent=2))
    return summary_out


if __name__ == "__main__":
    main()
