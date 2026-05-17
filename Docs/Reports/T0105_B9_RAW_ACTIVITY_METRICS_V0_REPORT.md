# T0105 — B9 Raw Activity Metrics V0 Report

## Status

`READY_FOR_INSTALL`

## Summary

T0105 extends `pf_t009_raw_calibration.py` with a read-only compatibility block that adds raw activity metrics to calibrated B9 moments.

It builds on T0103 API compat V5.

## Files

- `pf_t009_raw_calibration.py` patched by installer
- `Docs/Reports/T0105_B9_RAW_ACTIVITY_METRICS_V0_REPORT.md`
- `tests/test_t0105_b9_raw_activity_metrics_v0.py`
- `tools/apply_t0105_b9_raw_activity_metrics_v0.py`
- `tools/t0105_raw_activity_append.py.txt`

## Main additions

- tick density;
- gap cadence;
- spread stability;
- B9 dwell seconds;
- B9 center migration speed;
- MT5 volume visibility as experimental broker-relative field.

## Important

This is not the external Temporalité brick.

```text
external_temporality_dependency = False
b9_intrinsic_temporality_scope = MICROFILM_INTERNAL_ONLY
```

## Validation

Expected:

```text
8 passed
```

## Constraints

- no DB write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no global Forex volume claim.
