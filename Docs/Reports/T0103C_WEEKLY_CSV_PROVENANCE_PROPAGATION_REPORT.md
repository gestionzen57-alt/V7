# T0103C — Weekly CSV Provenance Propagation Hotfix

## Status

`READY`

## Problem

The calibrated JSON files preserve provenance:

```text
summary_recovery_type = FORCE_SNAPSHOT_DERIVED
data_visibility = RECONSTRUCTED_FORCE_SNAPSHOT_DERIVED
source_mode = M1_BAR_PROXY / TF5_BAR_PROXY / TF30_BAR_PROXY
confidence_cap = 0.35 / 0.25
```

But the weekly aggregate CSV/MD did not propagate those fields.

## Fix

Add a post-process tool:

```text
tools/t0103c_propagate_weekly_provenance.py
```

It scans `t009_sequence_summary_raw_calibrated.json`, extracts provenance from root / `summary_metadata` / `source_profile` / moment-level source profiles, then adds these fields to the aggregate CSV:

```text
summary_recovery_type
source_mode
data_visibility
confidence_cap
source_table
source_timeframe
```

It also appends a provenance matrix to the aggregate Markdown.

## Scripts

```text
scripts/APPLY_T0103C_WEEKLY_CSV_PROVENANCE.ps1
scripts/RUN_T0103C_WEEKLY_RAW_CALIBRATION_V36_WITH_PROVENANCE.ps1
```

## Constraints

- no `powerflow.db` write;
- no `tick_archive.db` write;
- no dashboard;
- no Telegram;
- no decision language;
- `FORCE_SNAPSHOT_DERIVED` remains visibly different from recovered existing B9 summaries.

## Phrase de cap

Raw MT5 donne la texture.  
Ici les scènes sont dérivées d’une source proxy explicite `force_snapshots_v2`, et cette provenance doit rester visible dans tous les outputs agrégés.
