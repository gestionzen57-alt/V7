# CURRENT STATE - PowerFlow V7.6.7

Date: 2026-05-15T21:01:26.5402470+02:00
Head: df6403e [CHECKPOINT] Auto-session checkpoint: fin

## Immediate context

Workspace state update for Claude after T004 requalification.

## T004 final/requalified state

T004 began as a USDJPY thin-data investigation.

Initial evidence showed:
- Core/powerflow.db is the active populated DB.
- USDJPY existed historically but was thin relative to GBPUSD.
- During earlier active insertion windows, GBPUSD advanced while USDJPY did not.
- Initial diagnosis was capture/routing/source-feed side, not engine/scoring/dashboard.

Later operator added/activated more EAs:
- USD-base cohort: USDJPY, USDCAD, USDCHF.
- USD-quote cohort: GBPUSD, EURUSD, AUDUSD.

T004-N expanded cohort result:
- USDJPY advanced.
- USDCAD advanced.
- USDCHF advanced.
- GBPUSD advanced.
- EURUSD advanced.
- AUDUSD advanced.

Therefore the hypothesis of a global USD-base blockage is invalidated.

Current T004 interpretation:
- Global USD-base capture blockage: invalidated.
- Probable cause: feed / EA / capture intermittent or initial setup incomplete during the first windows.
- Engine change required: no.
- Scoring change required: no.
- Dashboard change required: no.
- DB schema/path change required: no.

Current dispatch status for T004:
- DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT

Important T004 evidence files:
- Docs/Contracts/T004_FINAL_DIAGNOSIS.json
- Docs/Contracts/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT.json
- Docs/Contracts/T004_USD_BASE_POLARITY_COHORT.json
- Docs/Reports/T004_REQUALIFICATION_AFTER_USD_BASE_COHORT_*.md

## Revalidation commands for later

Command 1:
.\scripts\t004_usd_base_polarity_cohort.ps1 -UsdBaseSymbols @("USDJPY","USDCAD","USDCHF") -UsdQuoteSymbols @("GBPUSD","EURUSD","AUDUSD") -WatchSeconds 180 -IntervalSeconds 10

Command 2:
.\scripts\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10

## Current operating rule

Do not patch Core/engine.py, pf_engine_v6_core.py, scoring, dashboard, or SQLite for T004.

If capture intermittence recurs, add or inspect capture-health instrumentation per symbol before changing PowerFlow perception logic.

## Recent git log

- df6403e [CHECKPOINT] Auto-session checkpoint: fin
- 5be9798 docs(scheduler): update current state for Claude
- 5d05912 feat(scheduler): extend B8 FX cohort scope
- 6d807e3 [CHECKPOINT] Targeted checkpoint: T004-O requalification
- 870dc1b docs(t004): requalify USD-base cohort diagnosis
- 7cfc751 [CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort
- 019ecc5 audit(t004): test USD base polarity routing with USDCAD
- 968cae2 fix(scheduler): filter overlap skip from turbo failures
- 7e70266 fix(scheduler): ignore overlap skip for analytical continuation
- c3e8b66 [CHECKPOINT] Targeted checkpoint: T004-N USD base polarity cohort
- d42a0d5 audit(t004): test USD base polarity routing with USDCAD
- e7442e6 fix(scheduler): initialize core symbol scope before turbo call

## Next logical step

Read Docs/DISPATCH_STATUS.json and continue with the next active task.
Likely areas from recent history:
- Scheduler / turbo / overlap continuation work.
- T002 detached V6 core path if still active.
- Multi-symbol validation now that EA coverage has expanded.
