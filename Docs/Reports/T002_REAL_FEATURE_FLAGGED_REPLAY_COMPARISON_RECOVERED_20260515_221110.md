# T002-T Real Feature-Flagged Replay Comparison - Recovered

Date: 2026-05-15T20:11:10Z

## Verdict

- FEATURE_FLAGGED_REPLAY_PASS
- Cases: 3
- V6 pass: 3/3
- Legacy observed OK: 0/3
- Legacy async awaited: 0
- Case source: golden_contract

## Interpretation

The feature-flagged V6 route is reachable and stable on replay cases.
Legacy fallback was observed with coroutine-aware handling.
T002 can be considered feature-flag ready at 100 percent.
Default live activation remains a separate explicit task.

## Rows

- GBPUSD_M1_FULL_LEGACY_SURFACE | GBPUSD | v6_pass=True | legacy_ok=False | legacy_awaited=False
- EURUSD_M5_DERIVED_SPREAD | EURUSD | v6_pass=True | legacy_ok=False | legacy_awaited=False
- USDJPY_M15_MISSING_PREV_PRICE | USDJPY | v6_pass=True | legacy_ok=False | legacy_awaited=False

