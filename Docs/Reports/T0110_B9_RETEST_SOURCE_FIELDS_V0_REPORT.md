# T0110 — B9 Retest Source Fields V0 Report

## Status

`READY_FOR_INSTALL`

## Summary

T0110 adds canonical retest source fields before T0109 computes retest source signals.

This improves the retest evidence layer without inventing a trading signal.

## Files

- `pf_t009_raw_calibration.py` patched by installer
- `Docs/Contracts/B9_RETEST_SOURCE_FIELDS_V0_CONTRACT.md`
- `Docs/Reports/T0110_B9_RETEST_SOURCE_FIELDS_V0_REPORT.md`
- `tools/apply_t0110_b9_retest_source_fields_v0.py`
- `tools/t0110_retest_source_fields_append.py.txt`
- `tests/test_t0110_b9_retest_source_fields_v0.py`

## Added fields

```text
retest_touch_count
retest_first_touch_time
retest_last_touch_time
retest_delay_seconds
retest_acceptance_dwell_seconds
retest_rejection_speed_pips_per_min
retest_zone_distance_pips
retest_outcome_hint
retest_source_field_confidence
```

## Expected tests

T0107 + T0107A + T0108 + T0108A + T0109 + T0110:

```text
42 passed
```

## Constraints

- no DB write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.
