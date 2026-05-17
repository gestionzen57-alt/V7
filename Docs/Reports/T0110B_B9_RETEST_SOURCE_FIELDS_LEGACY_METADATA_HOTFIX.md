# T0110B — B9 Retest Source Fields Legacy Metadata Hotfix

Status: `READY_FOR_INSTALL`  
Branch proposal: `fix/t0110-retest-source-fields-legacy-metadata`  
Commit proposal: `fix(t0110): keep retest source fields legacy metadata compatible`

## Cause

T0110A reduced the combined suite to one failure:

```text
1 failed, 44 passed
```

The failing test is:

```text
tests/test_t0109_b9_retest_source_signals_v0.py::test_metadata_preserves_prior_layers
```

It expects:

```text
b9_retest_source_status in raw_calibration["retest_source_fields"]
```

T0110A kept `b9_retest_source_status` in `retest_source_signals`, which is semantically clean, but the T0109 legacy metadata test expects it in `retest_source_fields`.

## Fix

T0110B keeps both representations:

```text
retest_source_fields = canonical T0110 source fields + legacy T0109 signal aliases
retest_source_signals = computed T0109 signal fields
```

The active top layer remains:

```text
raw_calibration.version = T0110_RETEST_SOURCE_FIELDS_V0
```

## What changes

Only metadata compatibility.

Moment semantics are not changed.

## Expected tests

```text
45 passed
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
T0110 peut séparer champs source et signaux calculés,
mais il doit rester compatible avec la trace metadata T0109.
```
