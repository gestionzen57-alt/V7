# T004-O Requalification After Expanded USD Cohort

Date: 2026-05-15T18:44:46Z

## Requalification status

GLOBAL_USD_BASE_BLOCKAGE_INVALIDATED

## Updated cause

FEED_EA_CAPTURE_INTERMITTENT_OR_INITIAL_SETUP_INCOMPLETE

## What changed

The expanded cohort added USD-base and USD-quote controls:

- USD-base: USDJPY, USDCAD, USDCHF
- USD-quote: GBPUSD, EURUSD, AUDUSD

Latest cohort verdict:

USD_BASE_AND_USD_QUOTE_BOTH_ADVANCE

## Live deltas

`json
{
  "USDJPY": 4,
  "USDCAD": 2,
  "USDCHF": 2,
  "GBPUSD": 13,
  "EURUSD": 3,
  "AUDUSD": 2
}
`

## Interpretation

The initial hypothesis of a global USD-base routing block is invalidated by the latest live cohort. USDJPY, USDCAD, and USDCHF all advanced. The earlier USDJPY absence is now best interpreted as feed/EA/capture intermittence or incomplete setup during the first windows.

## What T004 is not

- Global USD-base capture blockage is not confirmed after expanded cohort.
- A simple XXXUSD-only pipeline bug is not supported by the latest live deltas.
- No engine/scoring/dashboard patch is justified.

## Operator actions

- [ ] Keep all active EAs running on USDJPY, USDCAD, USDCHF, GBPUSD, EURUSD, and AUDUSD during validation windows.
- [ ] Rerun T004-N during an active market window if feed cadence changes.
- [ ] Do not patch PowerFlow engine/scoring/dashboard based on the initial USDJPY absence.
- [ ] Use per-symbol live deltas as the primary validation signal after EA/feed changes.

## Engineering actions

- [ ] Keep polarity risk hits for later interpretation audit, not as proven capture blockers.
- [ ] Add a lightweight capture health surface per symbol if this intermittence recurs.
- [ ] Treat the previous USDJPY absence as window/setup dependent unless repeated with all EAs active.

## Dispatch

- Recommended status: DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT
- Dispatch update skipped: False
- Patched dispatch objects:
  - $.tasks.pending[1] -> DIAGNOSED_REQUALIFIED_FEED_CAPTURE_INTERMITTENT

## Stop rule

No engine/scoring/dashboard patch is justified by T004-O.

## Revalidation

`powershell
.\scripts\t004_usd_base_polarity_cohort.ps1 -UsdBaseSymbols @("USDJPY","USDCAD","USDCHF") -UsdQuoteSymbols @("GBPUSD","EURUSD","AUDUSD") -WatchSeconds 180 -IntervalSeconds 10
.\scripts\t004_active_insertion_symbol_delta.ps1 -WatchSeconds 120 -IntervalSeconds 10
`

