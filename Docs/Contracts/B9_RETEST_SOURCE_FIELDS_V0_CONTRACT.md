# T0110 — B9 Retest Source Fields V0

Status: `READY_FOR_INSTALL`  
Branch proposal: `feat/t0110-b9-retest-source-fields-v0`  
Commit proposal: `feat(t0110): add B9 retest source fields v0`

## Purpose

T0110 gives T0109 better input.

T0109 revealed that many retests are inferred or not visible because B9 summaries do not expose enough source retest fields.

T0110 adds canonical retest source fields before T0109 computes retest evidence.

This is a bridge layer until the sequence summarizer emits these fields natively.

## Added canonical fields

```text
retest_source_fields_version
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

## Outcome hints

```text
RETEST_OUTCOME_ACCEPTED
RETEST_OUTCOME_REJECTED_OR_FAILED
RETEST_OUTCOME_PENDING
RETEST_OUTCOME_FRICTION
RETEST_OUTCOME_ROTATIONAL
RETEST_OUTCOME_NOT_VISIBLE
```

## Confidence states

```text
RETEST_SOURCE_FIELDS_EXPLICIT
RETEST_SOURCE_FIELDS_PARTIAL
RETEST_SOURCE_FIELDS_INFERRED
RETEST_SOURCE_FIELDS_NOT_VISIBLE
```

## Zone memory sync

If `zone_memory` already exists, T0110 may enrich it in the calibrated output only:

```text
zone_memory.touch_count
zone_memory.last_tested
zone_memory.retest_status
```

No database is written.

## Doctrine

B9 should not guess retests from raw texture only when source data exists.

T0110 makes source evidence visible, but preserves uncertainty when the source is silent.

## Constraints

- read-only DB;
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
T0110 nourrit T0109.
B9 doit savoir si le retest vient d'une preuve source, d'une inférence, ou d'un silence.
```
