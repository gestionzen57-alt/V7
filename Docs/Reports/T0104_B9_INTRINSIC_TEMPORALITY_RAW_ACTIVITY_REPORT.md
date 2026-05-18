# T0104 — B9 Intrinsic Temporality & Raw Activity Report

## Status

`READY_FOR_REVIEW`

## Purpose

This document freezes the doctrine before weekly analysis:

B9 must not depend on the future external Temporalité brick.

B9 has its own intrinsic temporality:

- compression;
- dwell;
- center holding;
- retest delay;
- release;
- digestion;
- rotation;
- exhaustion.

The future Temporalité brick may later describe macro cycle, fractal context, or session maturity, but it is not part of this B9 calibration step.

## Delivered files

- `Docs/Contracts/B9_INTRINSIC_TEMPORALITY_RAW_ACTIVITY_CONTRACT.md`
- `Docs/Reports/T0104_B9_INTRINSIC_TEMPORALITY_RAW_ACTIVITY_REPORT.md`
- `tests/test_t0104_b9_intrinsic_temporality_raw_activity_docs.py`

## Main decisions

### 1. B9 intrinsic time is independent

B9 will focus on microfilm time:

```text
b9_dwell_seconds
b9_compression_seconds
b9_release_seconds
b9_retest_delay_seconds
b9_center_migration_speed_pips_per_min
```

### 2. Raw activity comes before MT5 volume

The safer raw fields to exploit first are:

```text
tick density
gap / cadence
spread stability
range
delta
center migration
```

### 3. MT5 volume is experimental

MT5 volume can help as broker-relative activity context, but it cannot prove true Forex participation.

Allowed:

```text
VOLUME_PRESENT_BROKER_RELATIVE
VOLUME_EXPERIMENTAL_ONLY
```

Forbidden:

```text
global Forex volume confirms
institutional absorption confirmed
real buyers/sellers volume proves
```

## Angles morts preserved

- speed vs intention;
- tick density vs real volume;
- range vs progression;
- breakout vs center migration;
- consumed zone ignored;
- broker-relative raw over-trusted;
- false positives discarded instead of memorized;
- external Temporalité injected too early;
- dwell not measured;
- spread instability ignored.

## Recommended next implementation order

```text
T0105A — raw activity / tick density / gap cadence
T0105B — spread stability fields
T0105C — dwell and compression seconds
T0105D — retest timing
T0105E — center migration speed
T0105F — MT5 volume visibility, experimental only
```

## Constraints

- documentary only;
- no DB write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.

## Phrase de cap

```text
B9 n’attend pas la brique Temporalité.
B9 possède le temps interne du microfilm.
```
