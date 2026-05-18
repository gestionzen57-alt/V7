from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_live_brief_once_runner import VERSION, build_live_brief


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Build T0148 B9 live brief once runner outputs")
    p.add_argument("--latest-scene-json", default="outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json")
    p.add_argument("--queue-json", default="outputs/b9_live_scene_candidate_queue_v0/B9_LIVE_SCENE_CANDIDATE_QUEUE_V0.json")
    p.add_argument("--adapter-json", default="outputs/b6_live_scene_adapter_v0/B6_LIVE_SCENE_QUERY_PAYLOAD_V0.json")
    p.add_argument("--similarity-query-json", default="outputs/b6_similarity_query_v0/B6_SIMILARITY_QUERY_RESULT_V0.json")
    p.add_argument("--false-positive-json", default="outputs/b6_false_positive_context_v0/B6_FALSE_POSITIVE_CONTEXT_V0.json")
    p.add_argument("--terrain-synthesis-json", default="outputs/b6_human_terrain_synthesis_v0/B6_HUMAN_TERRAIN_SYNTHESIS_V0.json")
    p.add_argument("--french-report-json", default="outputs/b9_french_trader_scene_report_v0/B9_FRENCH_TRADER_SCENE_REPORT_V0.json")
    p.add_argument("--output-dir", default="outputs/b9_live_brief_once_runner_v0")
    p.add_argument("--top-k", type=int, default=3)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    summary = build_live_brief(
        latest_scene_json=args.latest_scene_json,
        queue_json=args.queue_json,
        adapter_json=args.adapter_json,
        similarity_query_json=args.similarity_query_json,
        false_positive_json=args.false_positive_json,
        terrain_synthesis_json=args.terrain_synthesis_json,
        french_report_json=args.french_report_json,
        output_dir=args.output_dir,
        top_k=args.top_k,
    )
    print(json.dumps({
        "version": VERSION,
        "brief_state": summary.get("brief_state"),
        "candidate_id": summary.get("candidate_id"),
        "match_count": summary.get("match_count"),
        "top_match_film_id": summary.get("top_match_film_id"),
        "missing_inputs": summary.get("missing_inputs"),
        "false_positive_context_available": summary.get("false_positive_context_available"),
        "terrain_synthesis_available": summary.get("terrain_synthesis_available"),
        "forbidden_language_hits": summary.get("forbidden_language_hits"),
        "zip": summary.get("zip"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
