#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pf_battlefield_radar import (
    antagonist_role_weight,
    build_battlefield_scenes_from_latest_payload,
)


def test_role_weights_ordering():
    usd = antagonist_role_weight("USD")
    chf = antagonist_role_weight("CHF")
    eur = antagonist_role_weight("EUR")
    xxx = antagonist_role_weight("XXX")

    assert usd >= chf >= eur >= 0.0
    assert xxx == 0.0


def test_relation_keeps_priority_over_coalition():
    payload = {
        "timeframe": 15,
        "time_key": "2026-05-01T08:15:00+00:00",
        "active_relations": [
            {
                "coalition_members": ["EUR", "GBP"],
                "antagonist": "USD",
                "relation_type": "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING",
                "field_state": "BATTLEFIELD_WINDOW_OPENING",
                "field_score": 0.60,
                "tags": ["M5_M15_INTERMEDIATE_FIELD"],
            }
        ],
        "strong_coalitions": [
            {
                "members": ["CHF", "JPY"],
                "state": "HIGH_PRESSURE_COALITION_FOLDING",
                "phase": "MICROFILM_SYNCHRONIZED_FIELD",
                "cohesion": 0.95,
                "antagonist_candidates": [],
                "tags": ["M1_SPECIAL_MICROFILM"],
            }
        ],
    }

    scenes = build_battlefield_scenes_from_latest_payload(payload)

    assert len(scenes) >= 2
    assert scenes[0].scene_type == "RELATION_ACTIVE"
    assert scenes[0].strategic_score > scenes[1].strategic_score


if __name__ == "__main__":
    test_role_weights_ordering()
    test_relation_keeps_priority_over_coalition()
    print("OK: test_pf_battlefield_radar_personality_bridge")
