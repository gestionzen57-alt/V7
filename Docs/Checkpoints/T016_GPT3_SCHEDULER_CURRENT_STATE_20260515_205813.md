# T016 — GPT-3 Scheduler Current State

Date: 2026-05-15 20:58:13 +02:00

## Role

GPT-3 Scheduler: orchestration temps réel, Telegram dry-run, scheduler wrappers, B8/multidevise scope.

## Completed by GPT-3 Scheduler

### T007 — Telegram safety default

- un_powerflow_v76_telegram_cycle.ps1 default Telegram mode is now dry-run.
- Telegram live/send requires explicit mode.
- Trader Telegram remains contextual only.
- No BUY/SELL semantics.

### T010 — UTF-8 Telegram dry-run cleanup

- V7.6 Telegram dry-run subprocess stdout is decoded as UTF-8.
- Dry-run output no longer mojibakes accents/arrows.
- No DB patch.
- No Dashboard patch.

### T011 / T012 — Core multi-symbol scope for B8

- Core scheduler / B8 / multiread can receive a wider symbol scope.
- Trader-facing Telegram tail remains GBPUSD.
- GBPUSD remains the execution/trader symbol.

### T013B / T013C — Scheduler overlap handling

- OVERLAP_SKIP from scheduler_core is filtered from turbo failures under --continue-on-error.
- Analytical layers can continue when scheduler lock is active.
- B8/multiread verification can run without treating scheduler overlap as fatal.

### T015 — B8 FX cohort scope extension

PowerFlow/B8 scope now includes:

$coreSymbols

Verified aggregate outputs contained all 13 symbols:

- data_health.json
- signal_adaptive_profiles.json
- 	opdown_market_reader.json
- powerflow_multiread_synthesis.json
- multiread_synthesis_dashboard.json
- 8_cross_surface.json
- 8_cross_surface.txt

## Important architecture decision

GBPUSD is the primary traded/execution symbol.

Only GBPUSD should require dense M1 / tickvolume-per-second style depth.

Context symbols are for field reading, not execution:

### USD cohort

- EURUSD
- GBPUSD
- AUDUSD
- NZDUSD
- USDJPY
- USDCAD
- USDCHF

### GBP cohort

- GBPUSD
- EURGBP
- GBPJPY
- GBPAUD
- GBPCAD
- GBPCHF
- GBPNZD

## Data doctrine

Do not force every pair to have the same depth as GBPUSD.

Expected role split:

- GBPUSD: execution symbol, full stack, M1/M5/M15/H1/H4, timing, detachment, rejection, impulse.
- USD/GBP cohort symbols: context symbols, M5/M15/H1/H4 enough, coalition, antagonists, gravity, polarity, tempo.

If B8 says DEGRADED or INSUFFICIENT_CROSS_COVERAGE, it may be because it still expects full execution-grade density across every symbol. That should be requalified.

## Next recommended task

### T017 — B8 role-aware coverage model

Goal:

- Distinguish execution_symbol from context_symbols.
- Do not penalize context symbols for missing M1/tickvolume/sec.
- Create role-aware statuses:
  - GBPUSD_FULL_STACK_READY
  - USD_INDEX_CONTEXT_READY
  - GBP_INDEX_CONTEXT_READY
  - B8_CONTEXT_READY
  - B8_CONTEXT_DEGRADED
- Keep Dashboard V7.4 / FR Trader V5 untouched.
- No DB modification.
- No BUY/SELL.

## Forbidden / preserved

- No DB modification.
- No Dashboard HTML modification.
- No T004 patch by GPT-3 Scheduler.
- No Core Engine T002/T003 modification.
- No BUY/SELL.
- Telegram transmits only; it is not source of truth.
- Scheduler orchestrates only; it does not decide.
