# T0111 — B9 Sequence Summarizer Native Retest Source Fields Scaffold Report

## Status

`SCAFFOLD_READY`

## Why scaffold, not blind patch

`pf_t009_sequence_summarizer.py` must be inspected before modifying the exact moment creation path. This pack therefore installs a pure helper module and tests it thoroughly, while only adding a safe availability marker to the summarizer.

This avoids brittle edits while Claude/GPT Pro workspaces inspect the live file.

## Files

```text
pf_t0111_native_retest_source_fields.py
tools/apply_t0111_b9_native_retest_source_fields_scaffold.py
tests/test_t0111_native_retest_source_fields.py
Docs/Contracts/B9_SEQUENCE_SUMMARIZER_NATIVE_RETEST_SOURCE_FIELDS_V0_CONTRACT.md
Docs/Reports/T0111_B9_SEQUENCE_SUMMARIZER_NATIVE_RETEST_SOURCE_FIELDS_SCAFFOLD_REPORT.md
```

## Helper API

```python
enrich_moment_with_native_retest_source_fields(moment)
enrich_summary_with_native_retest_source_fields(summary)
```

## Expected tests

```text
7 passed
```

## Next integration

After inspecting `pf_t009_sequence_summarizer.py`, wire:

```python
moment = enrich_moment_with_native_retest_source_fields(moment)
```

at the exact moment finalization point.

## Phrase de cap

B9 ne doit pas deviner le retest après coup si le summarizer peut l'exposer dès la scène source.
