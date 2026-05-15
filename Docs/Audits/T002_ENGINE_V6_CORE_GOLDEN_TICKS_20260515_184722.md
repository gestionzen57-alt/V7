# T002-G Golden Tick Comparison Tests

Date: 2026-05-15T16:47:22Z

## Change

- Created Docs/Contracts/T002_ENGINE_V6_CORE_GOLDEN_TICK_CASES.json.
- Created tests/test_t002_engine_v6_core_golden_ticks.py.

## Purpose

Freeze expected outputs for detached pf_engine_v6_core.py before any runtime wiring.

## Golden cases

- GBPUSD_M1_FULL_LEGACY_SURFACE
- EURUSD_M5_DERIVED_SPREAD
- USDJPY_M15_MISSING_PREV_PRICE

## Runtime behavior

- No runtime wiring.
- Core/engine.py unchanged.
- Core/capture_bridge.py unchanged.
- Core/pf_engine_v6_adapter.py unchanged.

## Next rule

Do not connect pf_engine_v6_core.py until these golden tests remain green after a real tick replay comparison.

