# T004-I DB Writer Attribution Watch

Date: 2026-05-15T17:36:47Z

## Verdict

- Status: DB_ROWS_ADVANCED_DURING_WATCH
- DB: Core/powerflow.db
- Watch seconds: 60
- Row delta: 2
- DB file changed: False
- WAL/journal seen: True
- Capture observations: 0
- Scheduler observations: 0
- Scheduled task candidates: 0

## Recommendations

- Rows advanced during the watch. Use table_delta to identify active insertion target and rerun symbol health if needed.
- Do not change engine/scoring modules until a live writer and row deltas are confirmed.

## Table deltas

- context_htf | before=9917 | after=9917 | delta=0
- flow_packets | before=825 | after=825 | delta=0
- force_snapshots | before=19882 | after=19883 | delta=1
- force_snapshots_v2 | before=16442 | after=16443 | delta=1
- nodes_v6 | before=34 | after=34 | delta=0
- signals | before=9917 | after=9917 | delta=0
- sqlite_sequence | before=7 | after=7 | delta=0
- zone_diagnostics | before=1368 | after=1368 | delta=0

## Capture process observations

- none

## Scheduler process observations

- none

## Scheduled task candidates

- none

## Stop rule

Do not patch USDJPY logic while the live DB writer is not clearly identified.

## Next action

If no writer is visible, operator must start/verify the capture stack and rerun T004-G/T004-I. If writer is visible but no rows advance, inspect insertion errors and DB target.

