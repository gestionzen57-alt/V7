#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pf_coalitions import detect_currency_coalitions, summarize_coalitions


def test_low_respring_coalition():
    vectors = [
        {
            "currency": "GBP",
            "z_basket": -2.24,
            "slope": 0.14,
            "curvature": 0.04,
            "phase": "EARLY_RESPRING",
            "state": "ACCUMULATING",
            "zone_level": "EXTREME",
            "context_score": 8.4,
            "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"],
        },
        {
            "currency": "EUR",
            "z_basket": -2.06,
            "slope": 0.11,
            "curvature": 0.03,
            "phase": "EARLY_RESPRING",
            "state": "ACCUMULATING",
            "zone_level": "EXTREME",
            "context_score": 7.9,
            "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"],
        },
        {
            "currency": "USD",
            "z_basket": 2.45,
            "slope": -0.18,
            "curvature": -0.06,
            "phase": "FOLDING_FROM_HIGH",
            "state": "LEAKING",
            "zone_level": "EXTREME",
            "context_score": 9.1,
            "context_tags": ["M1_SPECIAL_MICROFILM", "LOCAL_ZONE_WORK"],
        },
        {
            "currency": "JPY",
            "z_basket": 0.20,
            "slope": 0.01,
            "curvature": 0.00,
            "phase": "NEUTRAL_ZONE",
        },
    ]

    coalitions = detect_currency_coalitions(vectors)
    assert len(coalitions) == 1
    c = coalitions[0]

    assert set(c.members) == {"GBP", "EUR"}
    assert c.polarity == "LOW"
    assert c.direction == "RISING"
    assert "RESPRING" in c.state
    assert c.leader in {"GBP", "EUR"}
    assert "USD" in c.antagonist_candidates
    assert c.cohesion >= 0.62

    print("OK low respring coalition")
    print(summarize_coalitions(coalitions))


def test_no_coalition_when_direction_differs():
    vectors = [
        {"currency": "GBP", "z_basket": -2.10, "slope": 0.13, "curvature": 0.03},
        {"currency": "EUR", "z_basket": -2.00, "slope": -0.10, "curvature": -0.02},
    ]

    coalitions = detect_currency_coalitions(vectors)
    assert coalitions == []
    print("OK no coalition when directions differ")


if __name__ == "__main__":
    test_low_respring_coalition()
    test_no_coalition_when_direction_differs()
