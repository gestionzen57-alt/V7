#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pf_coalition_relations import (
    personality_relation_score,
    qualify_coalition_relation,
)


def test_personality_relation_score_ordering():
    coalition = ["EUR", "GBP"]

    usd = personality_relation_score(coalition, "USD")
    chf = personality_relation_score(coalition, "CHF")
    xxx = personality_relation_score(coalition, "XXX")

    assert 0.0 <= usd <= 1.0
    assert 0.0 <= chf <= 1.0
    assert xxx == 0.5
    assert usd >= chf


def test_field_score_keeps_relation_detectable():
    coalition = {
        "coalition_id": "EUR_GBP_LOW_ELASTIC_COALITION_RESPRING",
        "members": ["EUR", "GBP"],
        "polarity": "LOW",
        "direction": "RISING",
        "state": "LOW_ELASTIC_COALITION_RESPRING",
        "phase": "MICROFILM_SYNCHRONIZED_FIELD",
        "z_mean": -2.15,
        "slope_mean": 0.125,
        "antagonist_candidates": ["USD"],
        "tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"],
    }

    vectors = [
        {"currency": "GBP", "z_basket": -2.24, "slope": 0.14},
        {"currency": "EUR", "z_basket": -2.06, "slope": 0.11},
        {"currency": "USD", "z_basket": 2.45, "slope": -0.18},
    ]

    relations = qualify_coalition_relation(coalition, vectors)
    assert len(relations) == 1
    assert relations[0].field_score > 0.55


if __name__ == "__main__":
    test_personality_relation_score_ordering()
    test_field_score_keeps_relation_detectable()
    print("OK: test_pf_coalition_relations_personality_bridge")
