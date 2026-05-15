# T002-F Detached V6 Core Legacy Fields

Date: 2026-05-15T16:43:27Z

## Change

- Extended Core/pf_engine_v6_core.py with LegacyTickSurface.
- Added derive_legacy_tick_surface(tick).
- Added legacy_tick_surface_to_dict(surface).
- Added tests/test_t002_engine_v6_core_legacy_surface.py.

## Fields now explicitly supported

- dev_a
- dev_b
- gap
- spread
- timeframe
- val_a
- val_b

## Runtime behavior

- No runtime wiring.
- Core/engine.py unchanged.
- Core/capture_bridge.py unchanged.
- Core/pf_engine_v6_adapter.py unchanged.

## Why

T002-E showed that legacy engine.process_tick reads dev_a, dev_b, val_a, val_b, gap, timeframe and spread.
This patch gives the detached V6 core a pure typed surface for those fields before any migration.

## Next rule

Do not connect this into process_tick until a golden comparison test exists on real/synthetic ticks.

