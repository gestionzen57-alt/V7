#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pf_coalition_relations import qualify_coalition_relation, summarize_relations


def test_low_block_against_usd_high_folding():
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
        {"currency": "USD", "z_basket": 2.45, "slope": -0.18, "context_tags": ["M1_SPECIAL_MICROFILM"]},
    ]

    relations = qualify_coalition_relation(coalition, vectors)
    assert len(relations) == 1
    r = relations[0]

    assert r.relation_type == "LOW_BLOCK_RESPRING_AGAINST_HIGH_FOLDING"
    assert r.field_state in ("FIELD_SIDE_SHIFT_ACTIVE", "BATTLEFIELD_WINDOW_OPENING", "STRUCTURE_BUILDING")
    assert r.phase in ("ACTIVE_COALITION_ROTATION", "TEMPORAL_WINDOW_PREPARING", "LOW_COALITION_RELEASE_BIRTH")
    assert r.field_score > 0.55
    assert r.antagonist == "USD"

    print("OK low coalition vs USD high folding")
    print(summarize_relations(relations))


def test_weak_timing():
    coalition = {
        "coalition_id": "GBP_EUR_LOW_COALITION",
        "members": ["GBP", "EUR"],
        "polarity": "LOW",
        "direction": "RISING",
        "z_mean": -1.65,
        "slope_mean": 0.05,
        "antagonist_candidates": ["USD"],
    }

    vectors = [
        {"currency": "USD", "z_basket": 1.90, "slope": 0.02},
    ]

    relations = qualify_coalition_relation(coalition, vectors)
    assert len(relations) == 1
    assert relations[0].relation_type == "POLARIZED_FIELD_WITH_WEAK_TIMING"
    assert relations[0].field_state == "POLARITY_PRESENT_TIMING_WEAK"
    print("OK weak timing relation")


if __name__ == "__main__":
    test_low_block_against_usd_high_folding()
    test_weak_timing()
