# T002-E Legacy Tick Surface vs Detached V6 Core

Date: 2026-05-15T16:21:44Z

## Purpose

Compare what legacy engine.process_tick reads from tick/prev against what detached pf_engine_v6_core currently derives.

## Runtime behavior

- No runtime wiring.
- Core/engine.py unchanged.
- Core/capture_bridge.py unchanged.
- Core/pf_engine_v6_adapter.py unchanged.
- Core/pf_engine_v6_core.py kept as detached pure helper.

## process_tick tick/prev surface

- process_tick lines: 896-1178
- tick attribute fields: 9
- prev attribute fields: 3
- tick subscript fields: 0
- prev subscript fields: 0

## Fields currently covered by pf_engine_v6_core

- symbol
- timestamp

## Direct fields not yet covered

- dev_a
- dev_b
- gap
- spread
- timeframe
- val_a
- val_b

## Nested fields requiring manual interpretation

- none

## Raw tick attrs

- tick.dev_a | lines 903
- tick.dev_b | lines 903
- tick.gap | lines 1123
- tick.spread | lines 911
- tick.symbol | lines 900, 901
- tick.timeframe | lines 897, 900, 902
- tick.timestamp | lines 952, 972, 993, 1006, 1033, 1070, 1090, 1127, 1171
- tick.val_a | lines 917, 980, 1057, 1101, 1113
- tick.val_b | lines 917, 980, 1057, 1101, 1113

## Raw prev attrs

- prev.gap | lines 1123
- prev.val_a | lines 1154, 1156, 1161, 1162
- prev.val_b | lines 1154, 1156, 1161, 1162

## Raw tick subscript fields

- none

## Raw prev subscript fields

- none

## Next extraction rule

Only promote a field into pf_engine_v6_core after adding a synthetic test and verifying it is genuinely used by process_tick logic.

## Technical risk

- Static AST can over-detect helper expressions.
- Dynamic fields accessed through getattr or dict indirection may be invisible.
- Coverage gap is not a failure; it is a migration map.

