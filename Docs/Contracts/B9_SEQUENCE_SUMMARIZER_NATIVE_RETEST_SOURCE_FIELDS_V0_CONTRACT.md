# T0111 — B9 Sequence Summarizer Native Retest Source Fields V0 Contract

Status: `SCAFFOLD_READY`  
Branch proposal: `feat/t0111-b9-sequence-summarizer-native-retest-source-fields`  
Commit proposal: `feat(t0111): add native retest source fields helper`

## Purpose

T0111 makes the retest source fields native to the B9 sequence summarizer.

T0110 currently reconstructs these fields after the summary is already produced. T0111 provides a pure helper that should be called when each B9 moment is created.

## Native fields

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
zone_memory.touch_count
zone_memory.last_tested
zone_memory.retest_status
```

## Outcome enum

```text
RETEST_OUTCOME_ACCEPTED
RETEST_OUTCOME_REJECTED_OR_FAILED
RETEST_OUTCOME_PENDING
RETEST_OUTCOME_FRICTION
RETEST_OUTCOME_ROTATIONAL
RETEST_OUTCOME_NOT_VISIBLE
```

## Confidence enum

```text
RETEST_SOURCE_FIELDS_EXPLICIT
RETEST_SOURCE_FIELDS_PARTIAL
RETEST_SOURCE_FIELDS_INFERRED
RETEST_SOURCE_FIELDS_NOT_VISIBLE
```

## Integration rule

The helper function is:

```python
from pf_t0111_native_retest_source_fields import enrich_moment_with_native_retest_source_fields

moment = enrich_moment_with_native_retest_source_fields(moment)
```

It should be called at the exact point where `pf_t009_sequence_summarizer.py` finalizes each B9 moment.

## Constraints

- read-only DB;
- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.
