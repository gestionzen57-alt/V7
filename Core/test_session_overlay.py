from __future__ import annotations

from pf_session_overlay import get_session_context, VALID_BIASES


def check(ts: str, session: str, phase: str) -> None:
    ctx = get_session_context(ts)
    assert ctx["session"] == session, (ts, ctx)
    assert ctx["session_phase"] == phase, (ts, ctx)
    assert isinstance(ctx["minutes_since_open"], int), ctx
    assert ctx["minutes_since_open"] >= 0, ctx
    assert ctx["session_bias"] in VALID_BIASES, ctx
    assert ctx["method"] == "SESSION_OVERLAY_V2", ctx


def test_required_cases() -> None:
    check("2026-05-11T22:15:00Z", "ASIAN", "IGNITION")
    check("2026-05-11T07:05:00Z", "LONDON", "IGNITION")
    check("2026-05-11T13:30:00Z", "OVERLAP", "MAX_VELOCITY_BATTLEFIELD")
    check("2026-05-11T20:30:00Z", "DEAD_ZONE", "DEAD_ZONE")


def test_boundaries_non_negative() -> None:
    for hour in range(24):
        ctx = get_session_context(f"2026-05-11T{hour:02d}:00:00Z")
        assert ctx["minutes_since_open"] >= 0, ctx
        assert ctx["session_bias"] in VALID_BIASES, ctx


if __name__ == "__main__":
    test_required_cases()
    test_boundaries_non_negative()
    print("PASS test_session_overlay")
