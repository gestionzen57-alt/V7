# T010 — B9 MT5 Raw Tick Recorder — Spec & Delivery Report

**Project:** PowerFlow V7.6.7 / T009-B9 Battlefield Flux  
**Branch target:** `feat/t010-b9-mt5-raw-tick-recorder`  
**Doctrine:** B9 reads the microfilm. It does not trade, does not alert live, and does not modify `powerflow.db`.

---

## 1. Mission

Create a separated MT5 raw tick recorder pipeline for PowerFlow B9:

```text
MT5 raw tick recorder
→ CSV raw ticks
→ Python SQLite importer/writer
→ tick_archive.db
→ tick_stream
→ B9 / T009 raw microfilm
```

This is deliberately separate from the existing MT4 indicator path:

```text
MT4 indicator
→ powerflow.db
→ force_snapshots_v2
→ PowerFlow indicator / M1 proxy / forces
```

---

## 2. Delivered files

```text
MQL5/T009_TickRecorder_MT5.mq5
Core/tick_archive_writer.py
Core/import_mt5_ticks_csv.py
Core/tests/test_t009_mt5_tick_archive.py
Core/docs/Reports/T010_B9_MT5_RAW_TICK_RECORDER_SPEC.md
```

---

## 3. Functional scope

### MT5 recorder

`MQL5/T009_TickRecorder_MT5.mq5` captures / exports:

```text
symbol
time
time_msc
bid
ask
last
mid
spread
volume
volume_real
flags
source_mode
broker
server_time
capture_seq
gap_ms
quality_flags
```

Supported source modes:

```text
ONTICK_RAW
HISTORICAL_RAW
TIMER_1S_SAMPLE
```

The EA writes CSV files only. It performs no trading action.

### SQLite archive writer

`Core/tick_archive_writer.py` owns `tick_archive.db` and table `tick_stream`.

Important protections:

```text
- refuses to open/write a DB named powerflow.db
- enables WAL mode
- creates tick_stream if missing
- source_mode is mandatory and constrained
- duplicates are guarded by symbol + ts_epoch_ms + source_mode + capture_seq
```

### CSV importer

`Core/import_mt5_ticks_csv.py` imports MT5 CSV rows into `tick_archive.db`.

Example:

```powershell
python Core/import_mt5_ticks_csv.py --csv C:\Users\User\AppData\Roaming\MetaQuotes\Terminal\Common\Files\PowerFlow_T009_ticks_GBPUSD.csv --db Core\tick_archive.db
```

---

## 4. DB schema

Table:

```sql
tick_stream
```

Columns:

```text
id, symbol, ts_utc, ts_epoch_ms, bid, ask, last, mid, spread,
volume, volume_real, flags, source, source_mode, broker, server_time,
capture_seq, gap_ms, quality_flags, created_at_utc
```

Indexes:

```text
ux_tick_stream_symbol_ts_mode_seq
ix_tick_stream_symbol_ts
ix_tick_stream_source_mode
```

---

## 5. Tests

Test file:

```text
Core/tests/test_t009_mt5_tick_archive.py
```

Coverage:

```text
test_insert_raw_tick
test_duplicate_same_ms_capture_seq
test_gap_ms
test_source_mode_historical_raw
test_quality_flags
test_query_lookback
test_wal_enabled
test_mid_spread_calculation
test_import_mt5_csv
test_powerflow_db_protection
```

Expected command:

```powershell
python -m pytest Core/tests/test_t009_mt5_tick_archive.py -v
```

---

## 6. Validation commands

Compile Python:

```powershell
python -m py_compile Core/tick_archive_writer.py Core/import_mt5_ticks_csv.py
```

Run tests:

```powershell
python -m pytest Core/tests/test_t009_mt5_tick_archive.py -v
```

CLI validation sample:

```powershell
python Core/import_mt5_ticks_csv.py --csv "$env:TEMP\t010_b9_sample_ticks.csv" --db "$env:TEMP\tick_archive_t010_validation.db"
```

---

## 7. Limits / blockers

```text
- The MQL5 file is delivered as source; final MT5 compilation must be done in MetaEditor.
- This phase does not integrate tick_archive.db into the live PowerFlow engine.
- This phase does not write to powerflow.db.
- This phase does not replace MT4 indicator / force_snapshots_v2.
- Historical MT5 availability depends on broker tick history.
```

---

## 8. Monday validation objective

Compare the same time window across:

```text
M1_BAR_PROXY from powerflow.db / force_snapshots_v2
HISTORICAL_RAW from MT5 / tick_archive.db
ONTICK_RAW live from MT5 / tick_archive.db
```

Reading target:

```text
Does RAW tick microfilm show dwell, failed displacement, center migration,
absorption, trap, or imbalance earlier / cleaner than M1_BAR_PROXY?
```

---

## 9. Claude review checklist

```text
[ ] Confirm file placement: MQL5/ + Core/
[ ] Run Python compile and tests
[ ] Compile MQL5 file in MetaEditor
[ ] Confirm CSV path in MT5 Common Files
[ ] Import a small historical CSV to tick_archive.db
[ ] Confirm tick_stream rows exist
[ ] Confirm powerflow.db unchanged
[ ] Decide whether T009 should read tick_archive.db in next phase
```
