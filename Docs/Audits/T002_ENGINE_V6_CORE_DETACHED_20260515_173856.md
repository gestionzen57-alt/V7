# T002-D Detached Engine V6 Core

Date: 2026-05-15T15:38:56Z

## Change

- Created Core/pf_engine_v6_core.py.
- Created tests/test_t002_engine_v6_core.py.

## Purpose

Create a detached pure-helper destination before extracting any code from legacy Core/engine.py.

## Runtime behavior

- No runtime wiring.
- Core/engine.py unchanged.
- Core/capture_bridge.py unchanged.
- Core/pf_engine_v6_adapter.py unchanged.

## Initial pure helper

- derive_tick_context(tick, prev, symbol=None)
- EngineTickContext immutable dataclass
- tick_context_to_dict(context)

## Guardrails

- no engine import
- no DB access
- no alert transmission
- no cockpit/dashboard/telegram dependency

## Next extraction candidate

Only after review: compare this derived context against values used inside engine.process_tick and add golden tests before wiring.

