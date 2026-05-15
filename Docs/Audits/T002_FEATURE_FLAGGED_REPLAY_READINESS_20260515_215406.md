# T002-R Feature-Flagged Replay Readiness

Date: 2026-05-15T19:54:06Z

## Verdict

- Status: FEATURE_FLAG_BOUNDARY_VALID_CORE_RUNTIME_ENTRYPOINT_MISSING
- Default live behavior changed: false
- Real V6 replay executed: false

## Adapter

- Signature: (tick: models.Tick, prev: models.Tick, brain: dict, send_alert)
- Signature OK: True
- Env flag: POWERFLOW_T002_USE_V6_CORE
- Strict flag: POWERFLOW_T002_V6_CORE_STRICT

## Core runtime candidates

- none

## Pure helper candidates

- none detected by name heuristic

## Interpretation

The adapter boundary is valid, but pf_engine_v6_core.py does not expose a compatible runtime process_tick entrypoint yet. The safe next step is to add/adapt that entrypoint or build a comparison wrapper before real replay.

## Stop rule

Do not enable V6 core by default until a real replay contract passes.

