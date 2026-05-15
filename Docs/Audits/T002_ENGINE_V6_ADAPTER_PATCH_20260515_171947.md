# T002 Engine V6 Adapter Patch

Date: 2026-05-15T15:19:47Z

## Change

- Created Core/pf_engine_v6_adapter.py.
- Redirected Core/capture_bridge.py from legacy direct import to adapter boundary.
- Added tests/test_t002_engine_v6_adapter.py.

## Runtime behavior

- No change intended.
- Adapter delegates 1:1 to legacy engine.process_tick.
- Existing frozen contract remains: (tick: models.Tick, prev: models.Tick, brain: dict, send_alert)

## Why

- T002 was misnamed as pf_engine.py refactor.
- Active runtime boundary is capture_bridge.py -> engine.process_tick.
- The adapter creates a safe V6 seam before extracting legacy internals.

## Technical risks

- Import side effects remain in legacy engine.py until extraction.
- If capture_bridge.py depends on side effects from direct engine import, adapter must remain 1:1.
- Do not move logic into adapter yet; it is a boundary only.

