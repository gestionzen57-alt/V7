#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pf_coalitions import (
    detect_currency_coalitions,
    personality_compatibility_score,
    role_compatibility_score,
    tempo_compatibility_score,
    volatility_compatibility_score,
)


def test_personality_scores_basic_ordering():
    eur_gbp = personality_compatibility_score("EUR", "GBP")
    jpy_aud = personality_compatibility_score("JPY", "AUD")
    xxx_yyy = personality_compatibility_score("XXX", "YYY")

    assert 0.0 <= eur_gbp <= 1.0
    assert 0.0 <= jpy_aud <= 1.0
    assert xxx_yyy == 0.5
    assert eur_gbp > jpy_aud

    assert role_compatibility_score("EUR", "GBP") == 1.0
    assert tempo_compatibility_score("EUR", "GBP") >= 0.85
    assert volatility_compatibility_score("EUR", "GBP") >= 0.75


def test_coalition_still_detected_with_personality_calibration():
    vectors = [
        {
            "currency": "GBP",
            "z_basket": -2.24,
            "slope": 0.14,
            "curvature": 0.04,
            "phase": "EARLY_RESPRING",
            "context_tags": ["M1_SPECIAL_MICROFILM"],
        },
        {
            "currency": "EUR",
            "z_basket": -2.06,
            "slope": 0.11,
            "curvature": 0.03,
            "phase": "EARLY_RESPRING",
            "context_tags": ["M1_SPECIAL_MICROFILM"],
        },
        {
            "currency": "USD",
            "z_basket": 2.45,
            "slope": -0.18,
            "curvature": -0.06,
            "phase": "FOLDING_FROM_HIGH",
        },
    ]

    coalitions = detect_currency_coalitions(vectors)
    assert len(coalitions) == 1

    c = coalitions[0]
    assert set(c.members) == {"GBP", "EUR"}
    assert c.cohesion >= 0.62


if __name__ == "__main__":
    test_personality_scores_basic_ordering()
    test_coalition_still_detected_with_personality_calibration()
    print("OK: test_pf_coalitions_personality_bridge")
