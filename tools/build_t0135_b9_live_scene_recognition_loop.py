from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_scene_recognition_loop import run


def optional_path(value: str | None) -> Optional[Path]:
    if not value:
        return None
    p = Path(value)
    return p if p.exists() else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Build T0135 B9 Live Scene Recognition Loop V0 outputs.")
    parser.add_argument("--live-scene-json", required=True)
    parser.add_argument("--similarity-query-json")
    parser.add_argument("--false-positive-json")
    parser.add_argument("--terrain-synthesis-json")
    parser.add_argument("--french-report-json")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()
    manifest = run(
        live_scene_json=Path(args.live_scene_json),
        similarity_query_json=optional_path(args.similarity_query_json),
        false_positive_json=optional_path(args.false_positive_json),
        terrain_synthesis_json=optional_path(args.terrain_synthesis_json),
        french_report_json=optional_path(args.french_report_json),
        output_dir=Path(args.output_dir),
        top_k=args.top_k,
    )
    print(json.dumps({
        "version": manifest["version"],
        "recognition_state": manifest["recognition_state"],
        "loop_id": manifest["loop_id"],
        "match_count": manifest["match_count"],
        "top_match_film_id": manifest["top_match_film_id"],
        "cross_family_match_count": manifest["cross_family_match_count"],
        "low_trust_in_results": manifest["low_trust_in_results"],
        "raw_unavailable_in_results": manifest["raw_unavailable_in_results"],
        "false_positive_context_available": manifest["false_positive_context_available"],
        "terrain_synthesis_available": manifest["terrain_synthesis_available"],
        "forbidden_language_hit_count": len(manifest["forbidden_language_hits"]),
        "output_dir": args.output_dir,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
