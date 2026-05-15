# T002-H DB Replay Comparison for Detached V6 Core

Date: 2026-05-15T16:49:58Z

## Result

- Status: MATCHING_TABLE_NO_ROWS
- DB path: C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\powerflow.db
- Selected table: force_snapshots_v2
- Cases: 0

## Runtime behavior

- Read-only DB inspection.
- Runtime not wired.
- Core/engine.py unchanged.
- Core/capture_bridge.py unchanged.
- Core/pf_engine_v6_adapter.py unchanged.

## Table candidates

- force_snapshots_v2 | score 7
- force_snapshots | score 4
- signals | score 3

## Cases

- none

## Interpretation

No DB replay sample was available. This is not a failure; it defines the next data-access question.

## Next step

Do not wire runtime yet. If samples were found, next step is an adapter shadow-read mode that compares legacy surface and V6 core output without changing process_tick behavior.

