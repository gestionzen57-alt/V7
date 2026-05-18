# T009/B9 Raw Calibration — Schema Compatibility Hotfix

**Mission:** B9 raw calibration V3.2–V3.5 schema compatibility  
**Date:** 2026-05-17  
**Scope:** read-only hotfix for `tick_archive.db.tick_stream` variants

## Diagnostic

The first run of `run_t009_raw_calibration_once.py` failed with:

```text
sqlite3.OperationalError: no such column: time_msc
```

Cause: the calibration query expected `tick_stream.time_msc`, but the local `tick_archive.db` schema does not expose this column. The raw tick archive still contains enough read-only data for calibration through:

```text
ts_utc, bid, ask, mid, spread, gap_ms, source_mode, capture_seq
```

## Fix

`pf_t009_raw_calibration.py` now introspects `tick_stream` with:

```sql
PRAGMA table_info(tick_stream)
```

Then it builds a schema-compatible SELECT dynamically.

Supported variants:

```text
with time_msc
without time_msc but with gap_ms
without capture_seq, falling back to rowid for stable ordering
```

## Safety

The hotfix remains strictly read-only:

```text
- no powerflow.db write
- no tick_archive.db write
- no dashboard import
- no Telegram import
- no BUY/SELL vocabulary
```

## Tests

Added regression coverage:

```text
test_schema_without_time_msc_is_supported
```

Expected local commands:

```powershell
python -m py_compile .\pf_t009_raw_calibration.py .\run_t009_raw_calibration_once.py
python -m pytest .\tests\test_t009_raw_calibration_v32_v35.py -v
```

Expected result after hotfix:

```text
9 passed
```

## Next validation

Rerun calibration on the extracted B9 V3.1 summaries:

```powershell
python .\run_t009_raw_calibration_once.py `
  --summary-json "C:\Users\User\Downloads\_b9_v31_outputs_extract\0800_1200\0800_0900\t009_sequence_summary.json" `
  --tick-db ".\tick_archive.db" `
  --output ".\output\b9_raw_calibrated_v32_v35\0800_0900" `
  --broker-time-shift-min 180
```

The calibrator should now read the local schema without requesting `time_msc`.
