#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

from pf_personalities import (
    DEVISE_PROFILES,
    DevisePersonality,
    behavioral_index,
    behavioral_index_all,
    behavioral_state,
    get_devise_profile,
    list_devises_by_role,
    list_followers,
)


def _build_rows():
    devise_cols = [
        ("usd", "usd_force"),
        ("eur", "eur_force"),
        ("jpy", "jpy_force"),
    ]
    rows = [
        ("t0", 0.0, 0.1, -0.2),
        ("t1", 0.2, 0.5, -0.5),
        ("t2", 0.4, 0.8, -0.6),
        ("t3", 0.6, 0.4, -0.1),
        ("t4", 0.5, 0.3, 0.0),
    ]
    return rows, devise_cols


def test_profiles_registry_shape():
    assert len(DEVISE_PROFILES) == 8

    for code, profile in DEVISE_PROFILES.items():
        assert isinstance(profile, DevisePersonality)
        assert code == code.upper()
        assert profile.devise == code
        assert profile.tempo_tf > 0
        assert profile.amplitude_norm >= 0
        assert profile.lag_bars >= 0


def test_role_and_followers_helpers():
    refuges = list_devises_by_role("refuge")
    assert "JPY" in refuges and "CHF" in refuges

    followers = list_followers()
    assert ("CHF", "JPY", 3) in followers
    assert ("NZD", "AUD", 3) in followers


def test_profile_access_case_insensitive():
    assert get_devise_profile("jpy").devise == "JPY"
    assert get_devise_profile("JpY").devise == "JPY"
    assert get_devise_profile("") is None
    assert get_devise_profile("XXX") is None


def test_behavioral_index_basics():
    rows, devise_cols = _build_rows()

    # USD against itself is zero by design.
    assert behavioral_index("usd", rows, 4, devise_cols) == 0.0

    z_eur = behavioral_index("eur", rows, 4, devise_cols, lookback=5)
    z_jpy = behavioral_index("jpy", rows, 4, devise_cols, lookback=5)

    assert isinstance(z_eur, float)
    assert isinstance(z_jpy, float)
    assert -3.0 <= z_eur <= 3.0
    assert -3.0 <= z_jpy <= 3.0


def test_behavioral_index_edge_cases():
    rows, devise_cols = _build_rows()

    assert behavioral_index("eur", rows, -1, devise_cols) is None
    assert behavioral_index("eur", rows, 99, devise_cols) is None
    assert behavioral_index("gbp", rows, 4, devise_cols) is None

    short_rows = rows[:2]
    assert behavioral_index("eur", short_rows, 1, devise_cols, lookback=20) is None


def test_behavioral_index_all_and_state():
    rows, devise_cols = _build_rows()
    all_z = behavioral_index_all(rows, 4, devise_cols, lookback=5)

    assert set(all_z.keys()) == {"USD", "EUR", "JPY"}

    assert behavioral_state(None) == "N/A"
    assert behavioral_state(2.1) == "EXTREME_HIGH"
    assert behavioral_state(1.2) == "HIGH"
    assert behavioral_state(0.0) == "NORMAL"
    assert behavioral_state(-1.5) == "LOW"
    assert behavioral_state(-2.5) == "EXTREME_LOW"


def test_dataclass_validation_guardrails():
    try:
        DevisePersonality(
            "XXX",
            tempo_tf=5,
            amplitude_norm=-1.0,
            lag_ref=None,
            lag_bars=0,
            volatility_class="LOW",
            role="RISK",
        )
        raise AssertionError("Expected ValueError for amplitude_norm")
    except ValueError:
        pass

    try:
        DevisePersonality(
            "XXX",
            tempo_tf=5,
            amplitude_norm=1.0,
            lag_ref="A",
            lag_bars=1,
            volatility_class="LOW",
            role="RISK",
        )
        raise AssertionError("Expected ValueError for lag_ref format")
    except ValueError:
        pass

    try:
        DevisePersonality(
            "XXX",
            tempo_tf=5,
            amplitude_norm=1.0,
            lag_ref="JPY",
            lag_bars=-1,
            volatility_class="LOW",
            role="RISK",
        )
        raise AssertionError("Expected ValueError for lag_bars")
    except ValueError:
        pass

    p = DevisePersonality(
        "XXX",
        tempo_tf=5,
        amplitude_norm=1.0,
        lag_ref="jpy",
        lag_bars=1,
        volatility_class="LOW",
        role="RISK",
    )
    assert p.lag_ref == "JPY"


if __name__ == "__main__":
    test_profiles_registry_shape()
    test_role_and_followers_helpers()
    test_profile_access_case_insensitive()
    test_behavioral_index_basics()
    test_behavioral_index_edge_cases()
    test_behavioral_index_all_and_state()
    test_dataclass_validation_guardrails()
    print("OK: test_pf_personalities_foundation")
