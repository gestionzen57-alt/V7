# B9 Intrinsic Temporality & Raw Activity Contract

Status: `DRAFT_CONTRACT_READY_FOR_REVIEW`  
Scope: B9 microfilm temporal logic, raw tick texture, MT5 volume visibility  
Branch proposal: `docs/t0104-b9-intrinsic-temporality-raw-activity-contract`  
Commit proposal: `docs(t0104): add B9 intrinsic temporality and raw activity contract`

## 1. Core doctrine

B9 must not depend on the future external Temporalité brick.

B9 already has its own intrinsic temporality:

```text
compression time
dwell time
center holding time
retest delay
release time
digestion time
rotation time
exhaustion time
```

This temporality belongs to the microfilm itself.

The external Temporalité brick, not yet defined, may later describe macro maturity, fractal timing, session age, or cycle context. It must not be mixed into B9 until its contract is explicit.

## 2. Separation of roles

```text
B9 intrinsic time
= internal life of the scene.

Future Temporalité brick
= external context, maturity, cycle, fractal time.

B6
= memory of films, analogies, traps, confirmations, invalidations.

Raw MT5
= broker-relative texture check.
```

## 3. B9 intrinsic temporal fields

The following fields may be introduced later as read-only calculated fields.

### Compression / dwell

```text
b9_dwell_seconds
b9_compression_seconds
b9_zone_hold_seconds
b9_center_hold_seconds
```

Purpose:

- measure how long price works a zone;
- distinguish compression from random stagnation;
- detect whether a zone is being consumed or defended.

### Release / digestion

```text
b9_release_seconds
b9_release_efficiency_pips_per_min
b9_digestion_seconds
b9_post_release_rotation_seconds
```

Purpose:

- determine whether release was clean, slow, forced, or rotational;
- avoid calling every movement a progressive wave.

### Retest timing

```text
b9_retest_delay_seconds
b9_retest_dwell_seconds
b9_retest_acceptance_time_seconds
b9_retest_failure_time_seconds
```

Purpose:

- distinguish fast rejection from accepted retest;
- detect retests that look valid on proxy but fail in raw.

### Center migration

```text
b9_center_migration_speed_pips_per_min
b9_center_migration_stability
b9_center_reversion_delay_seconds
```

Purpose:

- detect real center migration;
- distinguish center shift from wick-driven movement;
- preserve the idea that center path is more important than extremes.

## 4. Raw activity fields

Raw activity can enrich B9, but it does not decide.

```text
raw_tick_density_per_second
raw_tick_density_per_minute
raw_gap_median_ms
raw_gap_max_ms
raw_activity_profile
raw_activity_regime
```

Suggested values:

```text
RAW_ACTIVITY_THIN
RAW_ACTIVITY_NORMAL
RAW_ACTIVITY_DENSE
RAW_ACTIVITY_BURST
RAW_ACTIVITY_GAPPY
RAW_ACTIVITY_UNKNOWN
```

Interpretation:

- dense activity can show active microfilm;
- thin activity can weaken confidence;
- burst activity can indicate release or unstable quoting;
- gappy activity lowers confidence.

## 5. Spread fields

Spread is a stronger texture feature than MT5 volume for early B9 raw calibration.

```text
raw_spread_mean
raw_spread_max
raw_spread_min
raw_spread_expansion_pips
raw_spread_stability_state
```

Suggested values:

```text
SPREAD_STABLE
SPREAD_EXPANDING
SPREAD_UNSTABLE
SPREAD_THIN_DATA
SPREAD_UNKNOWN
```

Spread doctrine:

```text
A movement with unstable spread is less clean.
A retest with spread expansion is lower-confidence.
A release with stable spread and center migration is stronger.
```

## 6. MT5 volume doctrine

MT5 volume must not be treated as global Forex volume.

It is broker-relative and may mean:

```text
tick updates
quote activity
broker-side tick volume
platform-specific aggregate
```

It must not be used as proof of true institutional participation.

### Allowed use

```text
raw_volume_visibility_state
raw_tick_volume_sum
raw_tick_volume_delta
raw_tick_volume_density
raw_volume_activity_profile
raw_volume_confidence_cap
```

Suggested values:

```text
VOLUME_NOT_PRESENT
VOLUME_PRESENT_BROKER_RELATIVE
VOLUME_PRESENT_BUT_UNTRUSTED
VOLUME_EXPERIMENTAL_ONLY
```

Allowed interpretation:

- activity context;
- density proxy;
- relative comparison inside same broker feed;
- secondary texture signal.

Forbidden interpretation:

```text
"real market volume confirms"
"buyers/sellers volume proves"
"institutional absorption confirmed"
"global Forex volume confirms"
```

## 7. Progressive wave recalibration

A progressive wave is not just visible movement.

A progressive wave should require:

```text
effort
result
center migration
raw texture support
non-trivial range
non-zero duration
```

Possible states:

```text
PROGRESSIVE_WAVE_CONFIRMED
PROGRESSIVE_WAVE_ROTATIONAL
PROGRESSIVE_WAVE_WEAK_RAW
PROGRESSIVE_WAVE_SPREAD_UNSTABLE
PROGRESSIVE_WAVE_THIN_ACTIVITY
PROGRESSIVE_WAVE_UNKNOWN
```

The most valuable B6 Lab scenes are not only confirmed waves. They include false progressive waves:

```text
rotation disguised as progress
weak raw participation
spread-unstable release
zero-duration artifact
late exhaustion wave
```

## 8. B9 limits

B9 current limits:

1. can over-read M1 proxy scenes;
2. cannot yet fully model multi-day memory alone;
3. raw tick is broker-relative;
4. MT5 volume is not central Forex volume;
5. single-symbol GBPUSD cannot explain whether GBP or USD is the driver;
6. center migration can be confused with wick movement if not raw-checked;
7. progressive waves can hide rotation;
8. compression without dwell measurement is under-defined;
9. retest quality still needs stronger raw timing;
10. zero-duration artifacts must be excluded from market truth.

## 9. Angles morts

```text
confusing speed with intention
confusing tick density with true volume
confusing range with progression
confusing breakout with center migration
ignoring consumed zones
over-trusting broker-relative raw
not preserving false positives
not separating B9 intrinsic time from external Temporalité
not measuring dwell before release
not checking spread stability during retest
```

## 10. Future contract gates

Before adding code, the architect must decide:

```text
Which raw columns are available in tick_archive.db?
Is MT5 volume present?
What exact column name is used?
Is volume tick volume or real volume?
Should raw activity be computed from tick counts first?
Should spread be prioritized before volume?
```

Recommended order:

```text
1. raw tick density
2. gap / cadence
3. spread stability
4. dwell / compression seconds
5. retest timing
6. center migration speed
7. volume visibility only as experimental secondary field
```

## 11. Mandatory constraints

- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard mutation;
- no Telegram;
- no BUY/SELL;
- no B8 fusion;
- no dependency on undefined external Temporalité brick;
- no claim of true global Forex volume.

## 12. Phrase de cap

```text
B9 n’attend pas la brique Temporalité.
B9 possède le temps interne du microfilm.
Le raw enrichit ce temps par densité, spread, dwell et cadence.
Le volume MT5 reste expérimental et broker-relative.
```
