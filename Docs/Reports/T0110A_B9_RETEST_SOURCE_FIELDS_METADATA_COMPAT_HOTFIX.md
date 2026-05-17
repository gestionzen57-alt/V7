# T0110A — B9 Retest Source Fields Metadata Compatibility Hotfix

Status: `READY_FOR_INSTALL`  
Branch proposal: `fix/t0110-retest-source-fields-metadata-compat`  
Commit proposal: `fix(t0110): preserve natural flow metadata in retest source fields layer`

## Cause

T0110 installed enough for its own tests to pass, but the combined suite reported 3 failures.

Failing expectations:

```text
natural_flow_factors must contain b9_flow_intent_state
```

Observed problem:

```text
raw_calibration.natural_flow_factors missing or empty
```

## Diagnosis

T0110 correctly becomes the active top layer:

```text
raw_calibration.version = T0110_RETEST_SOURCE_FIELDS_V0
```

But it did not preserve additive metadata from T0107/T0108/T0109:

```text
natural_flow_factors
retest_mixed_fields
retest_source_fields
retest_source_signals
```

## Fix

T0110A overrides only the top-level `calibrate_summary_with_raw` metadata block.

It keeps:

```text
version = T0110_RETEST_SOURCE_FIELDS_V0
```

and restores:

```text
parent_versions
natural_flow_factors
retest_mixed_fields
retest_source_fields
retest_source_signals
```

## Expected result

Combined suite:

```text
42 passed
```

## Constraints

- read-only DB;
- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no BUY/SELL;
- no external Temporalité dependency;
- no global Forex volume claim.

## Phrase de cap

```text
T0110 nourrit T0109, mais ne doit pas effacer la traçabilité T0107/T0108/T0109.
```
