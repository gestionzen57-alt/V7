# T0107 — B9 Natural Flow Reading V0 Report

## Status

`READY_FOR_INSTALL`

## Summary

T0107 extends T0106 by adding natural flow interpretation fields directly to B9 raw calibration.

It does not create a Lab detour.

It does not wait for the external Temporalité brick.

It adapts generic order-flow / auction-reading ideas to the PowerFlow B9 microfilm:

- effort vs result;
- initiative vs response;
- rotation vs displacement;
- absorption-like friction;
- exhaustion-like stress;
- trap risk;
- readability.

## Files

- `pf_t009_raw_calibration.py` patched by installer
- `Docs/Contracts/B9_NATURAL_FLOW_READING_V0_CONTRACT.md`
- `Docs/Reports/T0107_B9_NATURAL_FLOW_READING_V0_REPORT.md`
- `tools/apply_t0107_b9_natural_flow_reading_v0.py`
- `tools/t0107_natural_flow_append.py.txt`
- `tests/test_t0107_b9_natural_flow_reading_v0.py`

## Main fields

```text
b9_flow_intent_state
b9_absorption_like_state
b9_exhaustion_like_state
b9_initiative_response_state
b9_auction_state
b9_trap_risk_state
b9_market_readability_state
b9_natural_flow_reading_fr
```

## Constraint

This is interpretation only.

No BUY/SELL.  
No dashboard.  
No Telegram.  
No DB write.  
No global Forex volume claim.  
No external Temporalité dependency.

## Expected tests

```text
10 passed
```
