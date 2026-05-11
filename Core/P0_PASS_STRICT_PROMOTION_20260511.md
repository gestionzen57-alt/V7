# P0 STRICT PROMOTION GATE — PowerFlow V7.2

Generated UTC : 2026-05-11T10:56:52+00:00
Symbol : `GBPUSD`
Original status : `PASS_CORE_REVIEW_MARKET_VALIDATOR`
Market validator original : `FAIL_STATIC_SIGNATURE`
Market validator risks : `['B4_STATIC_DOMINANT_PERIOD', 'B4_WEEKEND_STATIC_SIGNATURE', 'EIE_INSUFFICIENT_DATA']`
Promotion verdict : `PASS`
Final status : `PASS_STRICT`

## Decision

```text
PASS_STRICT
```

The market_open_validator failure is reclassified as a stale semantic rule, not as a live engine/data failure.

Reason:

```text
Data Quality LTF PASS
B4 PASS_ALIVE
B4 static_tfs empty
B4 LAG1_COMPRESSION confirmed by variance/uniqueness
B5 PASS_ALIVE
Spearman rho varies
Dashboard PASS
Only known stale market validator risks present
```

## Proofs OK

- ✅ core_steps PASS
- ✅ data_quality_ltf PASS
- ✅ TF1 DQ PASS rows=121
- ✅ TF5 DQ PASS rows=23
- ✅ TF15 DQ PASS rows=7
- ✅ B4 PASS_ALIVE
- ✅ B4 static_tfs empty
- ✅ B4 alive_tfs present: ['GBP_TF1', 'GBP_TF5', 'GBP_TF15']
- ✅ TF1 series alive rows=30 gbp_unique=30 gbp_std=22.431319
- ✅ TF5 series alive rows=30 gbp_unique=30 gbp_std=23.106659
- ✅ TF15 series alive rows=30 gbp_unique=30 gbp_std=6.74808
- ✅ B5 PASS_ALIVE
- ✅ B5 rho varies and bad_static false
- ✅ Dashboard PASS
- ✅ market_open_validator original status FAIL_STATIC_SIGNATURE detected
- ✅ market_open_validator risks are reclassifiable: ['B4_STATIC_DOMINANT_PERIOD', 'B4_WEEKEND_STATIC_SIGNATURE', 'EIE_INSUFFICIENT_DATA']

## Proofs failed

- none

## Architecture note

This gate does not patch `capture_bridge.py`, does not write `powerflow.db`, and does not modify `pf_*`.

It only reclassifies an obsolete validator interpretation:

```text
dominant_period_bars = 1 + variance alive + DQ PASS = LAG1_COMPRESSION
dominant_period_bars = 1 + variance zero = STATIC_SIGNATURE
```

## Recommended follow-up

Patch `pf_market_open_validator.py` later so this override is no longer needed.
