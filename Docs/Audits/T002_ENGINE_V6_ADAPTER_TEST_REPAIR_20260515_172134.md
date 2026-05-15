# T002 Engine V6 Adapter Test Repair

Date: 2026-05-15T17:21:34.3287099+02:00

## Repairs

- Removed future annotations from Core/pf_engine_v6_adapter.py so inspect.signature matches the frozen contract.
- Updated tests/test_t002_engine_process_tick_contract.py to expect capture_bridge.py -> pf_engine_v6_adapter.process_tick.

## Why

- The previous contract test still expected the old direct legacy import.
- The adapter boundary is intentional and should now be the protected runtime seam.

## Behavior

- Core/engine.py remains unchanged.
- Adapter still delegates 1:1 to legacy engine.process_tick.
- No DB or runtime behavior change intended.

