# T0106 — B9 Direct Raw Factors V0

Status: `READY_FOR_INSTALL`  
Branch proposal: `feat/t0106-b9-direct-raw-factors-v0`  
Commit proposal: `feat(t0106): add B9 direct raw factors v0`

## Purpose

T0106 stops treating the new T0105 fields as Lab-only material.

The factors are integrated directly into B9 calibration output.

This is still not a trading signal.

This is not the future external Temporalité brick.

## Direct B9 factors

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

## Temporal factor

B9 uses only intrinsic microfilm time:

```text
TEMPORAL_ZERO_DURATION_ARTIFACT
TEMPORAL_SHORT_IMPULSE
TEMPORAL_ACTIVE_MICROFILM
TEMPORAL_EXTENDED_DWELL
TEMPORAL_LONG_COMPRESSION_OR_ROTATION
```

## Raw activity factor

```text
ACTIVITY_BURST
ACTIVITY_DENSE
ACTIVITY_NORMAL
ACTIVITY_THIN_LIMIT
ACTIVITY_GAPPY_LIMIT
ACTIVITY_UNKNOWN
```

## Spread factor

```text
SPREAD_CLEAN
SPREAD_EXPANDING_CAUTION
SPREAD_UNSTABLE_LIMIT
SPREAD_THIN_DATA_LIMIT
SPREAD_UNKNOWN
```

## Volume factor

Volume is included directly, but only as broker-relative experimental activity visibility:

```text
VOLUME_ABSENT
VOLUME_VISIBLE_BROKER_RELATIVE_NO_DENSITY
VOLUME_VISIBLE_BROKER_RELATIVE_EMPTY
VOLUME_VISIBLE_BROKER_RELATIVE_THIN
VOLUME_VISIBLE_BROKER_RELATIVE_NORMAL
VOLUME_VISIBLE_BROKER_RELATIVE_ACTIVE
```

Forbidden claims:

```text
global Forex volume proves
institutional absorption confirmed
true buyer/seller volume confirmed
```

## Microfilm profiles

```text
ZERO_DURATION_ARTIFACT
SPREAD_UNSTABLE_MICROFILM
GAPPY_MICROFILM_LIMIT
PROGRESSIVE_ROTATIONAL_TRAP
WEAK_RAW_PROGRESS
CLEAN_PROGRESSIVE_MICROFILM
ROTATIONAL_MICROFILM
RAW_CONFIRMED_MICROFILM
MIXED_MICROFILM
```

## Meaning

T0106 turns raw activity into direct B9 interpretation fields.

It does not wait for B6 Lab.

It does not wait for external Temporalité.

B9 can now carry its own microfilm factor summary in every calibrated moment.

## Constraints

- read-only DB access;
- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no B8 fusion;
- no external Temporalité dependency;
- no global Forex volume claim.

## Phrase de cap

```text
B9 intègre directement le temps, la densité, le spread et le volume broker-relative comme facteurs de lecture.
Ce sont des facteurs d’interprétation, pas des décisions.
```
