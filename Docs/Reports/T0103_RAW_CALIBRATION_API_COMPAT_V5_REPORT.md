# T0103 Raw Calibration Full API Compatibility V5

Status: READY_FOR_INSTALL
Branch proposal: `fix/t0103-raw-calibration-api-compat-v5`
Commit proposal: `fix(t0103): restore full raw calibration runner api`

## Problem

After V4, `RawCalibrationConfig` is available and the T0103 runner now fails fast correctly.

The next missing runner symbol is:

```text
ImportError: cannot import name 'calibrate_summary_with_raw'
```

The runner imports:

```python
RawCalibrationConfig
calibrate_summary_with_raw
export_json
export_markdown
load_json
```

## Fix V5

Append a complete backward-compatible API block to `pf_t009_raw_calibration.py`:

- `RawCalibrationConfig`
- `load_json`
- `export_json`
- `export_markdown`
- `calibrate_summary_with_raw`

The implementation is read-only and performs direct raw tick calibration using:

```sql
DISTINCT ts_utc, bid, ask, mid, spread
```

It exposes:

- `raw_tick_count_raw`
- `raw_tick_count_dedup`
- `raw_duplicate_count`
- `raw_duplicate_ratio`
- `raw_delta_pips`
- `raw_range_pips`
- `raw_coverage`
- `proxy_vs_raw_verdict`
- `raw_texture_role`
- `progressive_wave_state`

## Important

This is a compatibility bridge. It restores the runner contract and keeps the weekly pipeline usable.

It also preserves the fail-fast rule:

```text
Un rapport vide n’est pas une validation.
```

## Constraints

- read-only
- no `powerflow.db` write
- no `tick_archive.db` write
- no dashboard
- no Telegram
- no BUY/SELL
- no B8 fusion
- broker-relative raw evidence only

## Phrase de cap

Le runner doit échouer fort si la calibration échoue. Un rapport vide n’est pas une validation.
