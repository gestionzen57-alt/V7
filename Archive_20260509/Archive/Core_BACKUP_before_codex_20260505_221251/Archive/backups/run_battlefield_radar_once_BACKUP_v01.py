#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PowerFlow V6 - run_battlefield_radar_once.py
Version: V0.1

Read powerflow.db through run_coalition_relations_once.py V0.3,
build battlefield scenes, and print cockpit-oriented strategic interest.

Read-only:
    - no DB writes
    - no Telegram
    - no temporal window activation
"""

import argparse
import json
from typing import Any, Dict, List, Optional

from run_coalition_relations_once import run_latest, run_scan
from pf_battlefield_radar import (
    build_battlefield_scenes_from_latest_payload,
    build_battlefield_scenes_from_scan_payload,
    cockpit_global_sentence,
    scenes_to_dict,
)


DEFAULT_TIMEFRAMES = [1, 5, 15, 30, 60]


def parse_timeframes(value: Optional[str]) -> List[int]:
    if not value:
        return DEFAULT_TIMEFRAMES
    return [int(x.strip()) for x in value.split(",") if x.strip()]


def scene_sort_key(scene: Any) -> tuple:
    rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1, "WATCH": 0}.get(scene.interest_level, 0)
    return (rank, max(scene.field_score, scene.cohesion), 1 if scene.scene_type == "RELATION_ACTIVE" else 0)


def run_radar(
    *,
    db: str,
    timeframes: List[int],
    scan: int,
    min_field_score: float,
    strong_cohesion: float,
    slope_lag: int,
    max_scenes: int,
) -> Dict[str, Any]:
    all_scenes = []
    per_tf = []

    for tf in timeframes:
        if scan > 0:
            payload = run_scan(
                db,
                timeframe=tf,
                symbol=None,
                currencies=None,
                lookback_rows=1200,
                slope_lag=slope_lag,
                scan=scan,
                min_field_score=min_field_score,
                strong_cohesion=strong_cohesion,
            )
            scenes = build_battlefield_scenes_from_scan_payload(payload, max_scenes=max_scenes)
        else:
            payload = run_latest(
                db,
                timeframe=tf,
                symbol=None,
                currencies=None,
                lookback_rows=1200,
                slope_lag=slope_lag,
                min_field_score=min_field_score,
                strong_cohesion=strong_cohesion,
            )
            scenes = build_battlefield_scenes_from_latest_payload(payload, max_scenes=max_scenes)

        all_scenes.extend(scenes)
        per_tf.append({
            "timeframe": tf,
            "scene_count": len(scenes),
            "scenes": scenes_to_dict(scenes),
        })

    all_scenes.sort(key=scene_sort_key, reverse=True)
    all_scenes = all_scenes[:max_scenes]

    return {
        "module": "run_battlefield_radar_once",
        "version": "V0.1",
        "db": db,
        "timeframes": timeframes,
        "mode": "scan" if scan > 0 else "latest",
        "scan": scan,
        "thresholds": {
            "min_field_score": min_field_score,
            "strong_cohesion": strong_cohesion,
        },
        "global_sentence": cockpit_global_sentence(all_scenes),
        "scene_count": len(all_scenes),
        "scenes": scenes_to_dict(all_scenes),
        "per_timeframe": per_tf,
    }


def print_payload(payload: Dict[str, Any]) -> None:
    print("PowerFlow Battlefield Radar — V0.1")
    print("=" * 72)
    print(payload["global_sentence"])

    print("\nBATAILLES EN PRÉPARATION / SCÈNES D'INTÉRÊT")
    if not payload["scenes"]:
        print("- aucune scène stratégique claire")
        return

    for idx, scene in enumerate(payload["scenes"], start=1):
        print(
            f"{idx:02d}. TF={scene['timeframe']} | {scene['interest_level']} | "
            f"{scene['battle_state']} | {scene['cockpit_sentence']}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Global cockpit radar for battlefield preparation.")
    parser.add_argument("--db", default="powerflow.db")
    parser.add_argument("--timeframes", default="1,5,15,30,60")
    parser.add_argument("--scan", type=int, default=0, help="Scan last N windows per timeframe; 0 = latest only")
    parser.add_argument("--min-field-score", type=float, default=0.45)
    parser.add_argument("--strong-cohesion", type=float, default=0.75)
    parser.add_argument("--slope-lag", type=int, default=1)
    parser.add_argument("--max-scenes", type=int, default=15)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    payload = run_radar(
        db=args.db,
        timeframes=parse_timeframes(args.timeframes),
        scan=args.scan,
        min_field_score=args.min_field_score,
        strong_cohesion=args.strong_cohesion,
        slope_lag=args.slope_lag,
        max_scenes=args.max_scenes,
    )

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print_payload(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
