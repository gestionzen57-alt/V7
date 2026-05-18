from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pf_t009_b9_b6_auto_realignment_runner import run_alignment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="T0167 B9/B6 Auto Realignment Runner V0")
    parser.add_argument("--latest-scene-json", default="outputs/b9_live_scene_candidate_queue_v0/B9_LATEST_SCENE_CANDIDATE_V0.json")
    parser.add_argument("--b6-index-json", default="outputs/b6_similarity_index_v0/B6_SIMILARITY_INDEX_V0.json")
    parser.add_argument("--film-cards-json", default="outputs/b6_film_library_v0/B6_FILM_CARDS_V0.json")
    parser.add_argument("--output-dir", default="outputs/b9_b6_auto_realignment_v0")
    parser.add_argument("--top-k", type=int, default=5)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    summary = run_alignment(
        latest_scene_json=Path(args.latest_scene_json),
        b6_index_json=Path(args.b6_index_json) if args.b6_index_json else None,
        film_cards_json=Path(args.film_cards_json) if args.film_cards_json else None,
        output_dir=Path(args.output_dir),
        top_k=args.top_k,
    )
    print(json.dumps({
        "version": summary.get("version"),
        "alignment_state": summary.get("alignment_state"),
        "candidate_id": summary.get("candidate", {}).get("candidate_id", ""),
        "match_count": summary.get("match_count"),
        "top_match_film_id": summary.get("top_match_film_id"),
        "rejected_memory_count": summary.get("rejected_memory_count"),
        "forbidden_language_hits": summary.get("forbidden_language_hits"),
        "zip": summary.get("zip"),
    }, ensure_ascii=False, indent=2))
    # Missing runtime inputs are a valid diagnostic state. Forbidden output language is not.
    return 1 if summary.get("forbidden_language_hits") else 0


if __name__ == "__main__":
    raise SystemExit(main())
