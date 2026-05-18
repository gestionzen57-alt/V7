# T0105 — B9 Raw Activity Metrics V0

Status: `READY_FOR_INSTALL`  
Branch proposal: `feat/t0105-b9-raw-activity-metrics-v0`  
Commit proposal: `feat(t0105): add B9 raw activity metrics v0`

## Purpose

T0105 adds B9 intrinsic microfilm activity metrics to raw calibration.

This is not the external Temporalité brick.

B9 keeps its own internal time:

```text
dwell
compression
release
tick cadence
spread stability
center migration speed
```

## Added fields

### B9 intrinsic time

```text
b9_dwell_seconds
b9_microfilm_duration_seconds
b9_compression_seconds
b9_release_seconds
b9_retest_delay_seconds
b9_center_migration_speed_pips_per_min
b9_intrinsic_temporality_scope
external_temporality_dependency
```

### Raw activity

```text
raw_tick_density_per_second
raw_tick_density_per_minute
raw_gap_count
raw_gap_median_ms
raw_gap_mean_ms
raw_gap_max_ms
raw_activity_profile
raw_activity_regime
```

Allowed profiles:

```text
RAW_ACTIVITY_THIN
RAW_ACTIVITY_NORMAL
RAW_ACTIVITY_DENSE
RAW_ACTIVITY_BURST
RAW_ACTIVITY_GAPPY
RAW_ACTIVITY_UNKNOWN
```

### Spread

```text
raw_spread_mean_pips
raw_spread_min_pips
raw_spread_max_pips
raw_spread_expansion_pips
raw_spread_stability_state
```

Allowed states:

```text
SPREAD_STABLE
SPREAD_EXPANDING
SPREAD_UNSTABLE
SPREAD_THIN_DATA
SPREAD_UNKNOWN
```

### MT5 volume visibility

```text
raw_volume_visibility_state
raw_volume_field
raw_tick_volume_sum
raw_tick_volume_density
raw_volume_confidence_cap
```

Allowed states:

```text
VOLUME_NOT_PRESENT
VOLUME_PRESENT_BROKER_RELATIVE
```

## Doctrine

MT5 volume is broker-relative and experimental.

It can help describe activity, but cannot prove:

```text
global Forex volume
institutional absorption
real buyer/seller volume
```

Spread stability and tick cadence are prioritized before volume.

## Progressive wave enrichment

T0105 can nuance progressive waves with:

```text
PROGRESSIVE_WAVE_SPREAD_UNSTABLE
PROGRESSIVE_WAVE_THIN_ACTIVITY
```

in addition to the existing states:

```text
PROGRESSIVE_WAVE_CONFIRMED
PROGRESSIVE_WAVE_ROTATIONAL
PROGRESSIVE_WAVE_WEAK_RAW
```

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
B9 lit le temps interne du microfilm par dwell, densité, cadence et spread.
Le volume MT5 reste une visibilité expérimentale, jamais une vérité globale.
```
