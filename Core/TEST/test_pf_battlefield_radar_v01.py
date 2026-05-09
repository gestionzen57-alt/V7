#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pf_battlefield_radar import (
    build_battlefield_scenes_from_scan_payload,
    cockpit_global_sentence,
    summarize_battlefield_scenes,
)


def main() -> None:
    payload = {
        "timeframe": 15,
        "active_windows": [
            {
                "time_key": "2026-05-01T08:15:00+00:00",
                "active_relations": [
                    {
                        "coalition_members": ["AUD", "CAD"],
                        "antagonist": "JPY",
                        "relation_type": "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING",
                        "field_state": "STRUCTURE_BUILDING",
                        "field_score": 0.57,
                        "tags": ["M5_M15_INTERMEDIATE_FIELD"],
                    }
                ],
                "strong_coalitions": [],
            }
        ],
        "strong_coalition_windows": [
            {
                "time_key": "2026-05-01T23:13:00+00:00",
                "strong_coalitions": [
                    {
                        "members": ["CHF", "EUR"],
                        "state": "HIGH_PRESSURE_COALITION_FOLDING",
                        "phase": "MICROFILM_SYNCHRONIZED_FIELD",
                        "cohesion": 0.94,
                        "antagonist_candidates": [],
                        "tags": ["M1_SPECIAL_MICROFILM"],
                    }
                ],
            }
        ],
    }

    scenes = build_battlefield_scenes_from_scan_payload(payload)
    assert len(scenes) == 2
    assert scenes[0].interest_level == "HIGH"
    assert any(s.scene_type == "RELATION_ACTIVE" for s in scenes)
    assert any(s.scene_type == "COALITION_STRONG" for s in scenes)

    print("OK pf_battlefield_radar V0.1")
    print(cockpit_global_sentence(scenes))
    print(summarize_battlefield_scenes(scenes))


if __name__ == "__main__":
    main()
