# T0108 — B9 Natural Retest & FLOW_MIXED Split V0 Report

## Status

`READY_FOR_INSTALL`

## Summary

T0108 builds on T0107/T0107A.

It splits `FLOW_MIXED` and adds a natural retest reading to B9 calibrated moments.

## Files

- `pf_t009_raw_calibration.py` patched by installer
- `Docs/Contracts/B9_NATURAL_RETEST_MIXED_SPLIT_V0_CONTRACT.md`
- `Docs/Reports/T0108_B9_NATURAL_RETEST_MIXED_SPLIT_V0_REPORT.md`
- `tools/apply_t0108_b9_natural_retest_mixed_split_v0.py`
- `tools/t0108_retest_mixed_split_append.py.txt`
- `tests/test_t0108_b9_natural_retest_mixed_split_v0.py`

## Added fields

```text
b9_mixed_split_state
b9_retest_natural_state
b9_retest_quality_state
b9_context_resolution_state
b9_retest_mixed_reading_fr
```

## Expected tests

```text
8 passed
```

## Constraints

- no DB write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.
