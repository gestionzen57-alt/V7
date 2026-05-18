# T0108A — B9 Retest Mixed Metadata / Test Compatibility Hotfix

Status: `READY_FOR_INSTALL`  
Branch proposal: `fix/t0108-retest-mixed-metadata-compat`  
Commit proposal: `fix(t0108): preserve natural flow metadata in retest mixed layer`

## Cause

T0108 installed correctly, but the combined test suite showed two failures:

1. `test_t0107_fields_are_added` expected the top-level raw calibration version to remain:

```text
T0107_NATURAL_FLOW_READING_V0
```

After T0108, the top version becomes:

```text
T0108_RETEST_MIXED_SPLIT_V0
```

This is expected because T0108 is the active top layer.

2. `test_flags_preserve_t0107_and_add_t0108` expected `natural_flow_factors` to remain visible in `raw_calibration`.

T0108 did not preserve that metadata key.

## Fix

T0108A does two things:

1. keeps `raw_calibration.version = T0108_RETEST_MIXED_SPLIT_V0`;
2. restores `natural_flow_factors` and adds `parent_versions`.

It also patches the T0107 test to be forward-compatible:

```text
T0107_NATURAL_FLOW_READING_V0
or
T0108_RETEST_MIXED_SPLIT_V0
```

## Why this is correct

T0108 extends T0107. It should not pretend to still be T0107 at the top level, but it must keep T0107 metadata visible.

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
T0108 ajoute le retest et le split du mixed flow.
Il ne doit pas effacer la traçabilité T0107.
```
