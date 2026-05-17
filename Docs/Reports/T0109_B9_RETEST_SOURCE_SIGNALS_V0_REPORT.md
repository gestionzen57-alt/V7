# T0109 — B9 Retest Source Signals V0 Report

## Status

`READY_FOR_INSTALL`

## Summary

T0109 adds explicit retest evidence fields after T0108/T0108A.

It reduces blind `RETEST_NOT_VISIBLE` cases by exposing whether B9 actually has source evidence.

## Files

- `pf_t009_raw_calibration.py` patched by installer
- `Docs/Contracts/B9_RETEST_SOURCE_SIGNALS_V0_CONTRACT.md`
- `Docs/Reports/T0109_B9_RETEST_SOURCE_SIGNALS_V0_REPORT.md`
- `tools/apply_t0109_b9_retest_source_signals_v0.py`
- `tools/t0109_retest_source_signals_append.py.txt`
- `tests/test_t0109_b9_retest_source_signals_v0.py`

## Main fields

```text
b9_retest_source_status
b9_retest_touch_count_proxy
b9_retest_delay_proxy_seconds
b9_retest_source_visibility
b9_retest_source_evidence_score
b9_retest_source_signal_state
b9_retest_source_readiness
b9_retest_source_reading_fr
```

## Expected tests

T0107 + T0107A + T0108 + T0108A + T0109:

```text
34 passed
```

## Constraints

- no DB write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.
