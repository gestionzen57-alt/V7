# T002-D Detached Core Test Repair

Date: 2026-05-15T15:42:53Z

## Repair

- Replaced fragile raw substring guard with AST import inspection.
- Side-effect token scan now ignores comment-only lines.
- Cleaned comments in Core/pf_engine_v6_core.py to avoid false positives.

## Behavior

- Core/engine.py unchanged.
- Core/capture_bridge.py unchanged.
- Core/pf_engine_v6_adapter.py unchanged.
- pf_engine_v6_core.py remains detached from runtime.

