from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List

# Allow running from tools/ in an unpacked repo.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pf_t009_reality_board_payload_candidate import (  # noqa: E402
    VERSION,
    build_blocked_missing_input_payload,
    build_payload_candidate,
)


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def write_csv(path: Path, payload: Dict[str, Any]) -> None:
    row = {
        "version": payload.get("version", ""),
        "payload_state": payload.get("payload_state", ""),
        "candidate_id": payload.get("candidate_id", ""),
        "symbol": payload.get("symbol", ""),
        "time_start": payload.get("time_start", ""),
        "time_end": payload.get("time_end", ""),
        "session": payload.get("session", ""),
        "scene_role": payload.get("scene_role", ""),
        "price_verdict": payload.get("price_verdict", ""),
        "source_quality_state": payload.get("source_quality_state", ""),
        "source_mode": payload.get("source_mode", ""),
        "data_visibility": payload.get("data_visibility", ""),
        "memory_family": payload.get("memory_family", ""),
        "memory_confidence_ladder": payload.get("memory_confidence_ladder", ""),
        "false_positive_state": payload.get("false_positive_state", ""),
        "top_match_film_id": payload.get("top_match_film_id", ""),
        "match_count": payload.get("match_count", 0),
        "cross_family_match_count": payload.get("cross_family_match_count", 0),
        "raw_unavailable_in_results": payload.get("raw_unavailable_in_results", False),
        "low_trust_in_results": payload.get("low_trust_in_results", False),
        "forbidden_language_hits": "|".join(payload.get("forbidden_language_hits", [])),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        writer.writeheader()
        writer.writerow(row)


def write_md(path: Path, payload: Dict[str, Any]) -> None:
    risks = payload.get("technical_risks", []) or []
    watch = payload.get("what_to_watch_next_fr", []) or []
    limits = payload.get("limits", []) or []
    lines: List[str] = [
        "# B9 Reality Board Payload Candidate V0",
        "",
        "## État",
        "",
        f"- Payload state : `{payload.get('payload_state', 'UNKNOWN')}`",
        f"- Candidate : `{payload.get('candidate_id', 'UNKNOWN')}`",
        f"- Symbole : `{payload.get('symbol', 'UNKNOWN')}`",
        f"- Fenêtre : `{payload.get('time_start', 'UNKNOWN')}` → `{payload.get('time_end', 'UNKNOWN')}`",
        f"- Session : `{payload.get('session', 'SESSION_UNKNOWN')}`",
        "",
        "## Ce que B9 expose",
        "",
        str(payload.get("attention_reason_fr", "")),
        "",
        "## Lecture B9",
        "",
        str(payload.get("b9_reading_fr", "")),
        "",
        "## Mémoire B6",
        "",
        f"- Famille mémoire : `{payload.get('memory_family', 'UNKNOWN')}`",
        f"- Comparabilité : `{payload.get('memory_confidence_ladder', 'UNKNOWN')}`",
        f"- Film proche : `{payload.get('top_match_film_id', 'NO_MATCH')}`",
        "",
        str(payload.get("memory_context_fr", "")),
        "",
        "## Source quality",
        "",
        f"- Source : `{payload.get('source_mode', 'UNKNOWN')}`",
        f"- Visibilité : `{payload.get('data_visibility', 'UNKNOWN')}`",
        f"- Qualité : `{payload.get('source_quality_state', 'UNKNOWN')}`",
        "",
        "## Risques techniques",
        "",
    ]
    lines += [f"- {risk}" for risk in risks] or ["- Aucun risque technique explicite."]
    lines += ["", "## À surveiller ensuite", ""]
    lines += [f"- {item}" for item in watch] or ["- Aucun élément déclaré."]
    lines += ["", "## Limites", ""]
    lines += [f"- {item}" for item in limits]
    lines += [
        "",
        "## Doctrine",
        "",
        "B9 ne cherche pas le signal.",
        "B9 cherche la trace laissée par l'effort.",
        "Le payload Reality Board reste candidat : il expose une scène, il ne décide pas.",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8", newline="\n")


def make_zip(output_dir: Path, files: List[Path]) -> Path:
    zip_path = output_dir / "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in files:
            if f.exists():
                zf.write(f, f.name)
    return zip_path


def run(args: argparse.Namespace) -> Dict[str, Any]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    brief_path = Path(args.live_brief_json)
    if not brief_path.exists():
        payload = build_blocked_missing_input_payload([str(brief_path)])
    else:
        payload = build_payload_candidate(load_json(brief_path))

    json_path = output_dir / "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0.json"
    md_path = output_dir / "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0.md"
    csv_path = output_dir / "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0.csv"
    manifest_path = output_dir / "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_MANIFEST.json"

    write_json(json_path, payload)
    write_md(md_path, payload)
    write_csv(csv_path, payload)

    manifest = {
        "version": VERSION,
        "payload_state": payload.get("payload_state"),
        "output_dir": str(output_dir),
        "files": [json_path.name, md_path.name, csv_path.name, manifest_path.name, "B9_REALITY_BOARD_PAYLOAD_CANDIDATE_V0.zip"],
        "read_only": True,
        "writes_powerflow_db": False,
        "writes_tick_archive_db": False,
        "writes_dashboard": False,
        "sends_telegram": False,
    }
    write_json(manifest_path, manifest)
    zip_path = make_zip(output_dir, [json_path, md_path, csv_path, manifest_path])

    summary = {
        "version": VERSION,
        "payload_state": payload.get("payload_state"),
        "candidate_id": payload.get("candidate_id"),
        "memory_confidence_ladder": payload.get("memory_confidence_ladder"),
        "top_match_film_id": payload.get("top_match_film_id"),
        "match_count": payload.get("match_count"),
        "forbidden_language_hits": payload.get("forbidden_language_hits", []),
        "raw_unavailable_in_results": payload.get("raw_unavailable_in_results"),
        "zip": str(zip_path),
    }
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build B9 Reality Board payload candidate V0.")
    parser.add_argument("--live-brief-json", required=True, help="Path to B9_LIVE_BRIEF_ONCE_V0.json")
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


if __name__ == "__main__":
    result = run(parse_args())
    print(json.dumps(result, ensure_ascii=False, indent=2))
