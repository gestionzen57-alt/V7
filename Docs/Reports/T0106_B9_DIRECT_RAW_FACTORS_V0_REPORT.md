# T0106 — B9 Direct Raw Factors V0 Report

## Status

`READY_FOR_INSTALL`

## Summary

T0106 promotes the T0105 raw activity metrics into direct B9 interpretation factors.

It does not create a Lab export.

It does not use the external Temporalité brick.

It adds direct fields to each calibrated moment:

```text
b9_temporal_pressure_state
b9_raw_activity_factor
b9_spread_factor
b9_volume_factor_state
b9_center_speed_factor
b9_microfilm_texture_score
b9_microfilm_quality_state
b9_microfilm_profile
b9_factor_flags
```

## Direct implementation

The installer appends a compatibility block to `pf_t009_raw_calibration.py`.

The existing T0103 runner can then be reused.

## Why this matters

B9 no longer only says:

```text
confirmed / nuanced
```

It can also say:

```text
active dense microfilm
gappy microfilm limit
spread unstable confirmation
progressive rotational trap
weak raw progress
broker-relative volume visible
```

## Volume policy

MT5 volume is now a direct B9 factor, but only as:

```text
BROKER_RELATIVE_ACTIVITY_ONLY_EXPERIMENTAL
```

No global Forex volume claim is allowed.

## Tests

Expected:

```text
9 passed
```

## Constraints

- no DB write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.
