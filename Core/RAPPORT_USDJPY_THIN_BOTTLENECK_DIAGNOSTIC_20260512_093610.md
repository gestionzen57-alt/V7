# USDJPY THIN BOTTLENECK DIAGNOSTIC — PowerFlow V7.2.1

Generated UTC : 2026-05-12T09:36:10.419884+00:00
Symbol : `USDJPY`
DB : `C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\powerflow.db`
Primary bottleneck : `MT4_STREAM_INACTIVE_OR_SYMBOL_NOT_INGESTED`
Confidence : `HIGH`

## Verdict

```text
MT4_STREAM_INACTIVE_OR_SYMBOL_NOT_INGESTED
```

## Evidence

- USDJPY has zero rows in force_snapshots.

## Next fix ciblée

- Verify USDJPY is enabled in MT4 EA symbol list.
- Verify bridge receives USDJPY messages before DB insertion.
- Check symbol spelling/suffix in MT4 broker (USDJPY, USDJPY., USDJPYm).

## force_snapshots summary

| Symbol | Total rows | TF1 | TF5 | TF15 | TF30 | TF60 | TF240 | TF1440 | TF10080 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|

### USDJPY TF details

| TF | Rows | Max timestamp | Age sec | Stale | Gap count | Median interval | Max interval |
|---|---:|---|---:|---|---:|---:|---:|
| 1 | 0 | None | None | None | None | None | None |
| 5 | 0 | None | None | None | None | None | None |
| 15 | 0 | None | None | None | None | None | None |
| 30 | 0 | None | None | None | None | None | None |
| 60 | 0 | None | None | None | None | None | None |
| 240 | 0 | None | None | None | None | None | None |
| 1440 | 0 | None | None | None | None | None | None |
| 10080 | 0 | None | None | None | None | None | None |

## Logs scan

- files_scanned : `23`
- USDJPY symbol_hits : `19513`
- db_lock_hits : `50`
- overlap_hits : `1`
- parse_hits : `50`

### DB lock / throttle excerpts

- `logs\task_scheduler.log` — 2026-05-12T08:59:16.473403+00:00 STEP_START USDJPY.behavioral_mapper :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_behavioral_alert_mapper_once.py --symbol USDJPY --temporal output\dashboard_surface\USDJPY\node.json --energy output\dashboard_surface\USDJPY\energy.json --out output/behavioral_alert_queue_USDJPY.json --pretty --summary
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.577448+00:00 STDOUT USDJPY.behavioral_mapper: BEHAVIORAL_ALERT_QUEUE_OK | symbol=USDJPY | temporal=output\dashboard_surface\USDJPY\node.json | energy=output\dashboard_surface\USDJPY\energy.json | out=output\behavioral_alert_queue_USDJPY.json | behavioral_count=1 | degraded_count=0
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.696772+00:00 STEP_START dashboard_refresh :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_powerflow_dashboard_refresh_once.py --skip-cockpit --refresh-cockpit-from-queue --pretty --summary
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.846586+00:00 STDOUT dashboard_refresh: ============================================================ | POWERFLOW V6 — DASHBOARD FULL REFRESH | symbol=GBPUSD | db=powerflow.db | temporal=output\temporal_node_state.json | energy=output\currency_energy_state.json | mode=REFRESH_COCKPIT_FROM_QUEUE | ============================================================ |  | [1/3] Behavioral Alert Mapper | ------------------------------------------------------------ |   OK  out=output\behavi
- `logs\task_scheduler.log` — ^C2026-05-12T09:07:01.840208+00:00 OVERLAP_SKIP cycle=1 previous lock active
- `logs\task_scheduler.log` — 2026-05-12T09:12:46.881540+00:00 STEP_START GBPUSD.behavioral_mapper :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_behavioral_alert_mapper_once.py --symbol GBPUSD --temporal output\dashboard_surface\GBPUSD\node.json --energy output\dashboard_surface\GBPUSD\energy.json --out output/behavioral_alert_queue_GBPUSD.json --pretty --summary
- `logs\task_scheduler.log` — 2026-05-12T09:12:47.075145+00:00 STDOUT GBPUSD.behavioral_mapper: BEHAVIORAL_ALERT_QUEUE_OK | symbol=GBPUSD | temporal=output\dashboard_surface\GBPUSD\node.json | energy=output\dashboard_surface\GBPUSD\energy.json | out=output\behavioral_alert_queue_GBPUSD.json | behavioral_count=4 | degraded_count=0
- `logs\task_scheduler.log` — 2026-05-12T09:13:32.205120+00:00 STEP_START EURUSD.behavioral_mapper :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_behavioral_alert_mapper_once.py --symbol EURUSD --temporal output\dashboard_surface\EURUSD\node.json --energy output\dashboard_surface\EURUSD\energy.json --out output/behavioral_alert_queue_EURUSD.json --pretty --summary
- `logs\task_scheduler.log` — 2026-05-12T09:13:32.551334+00:00 STDOUT EURUSD.behavioral_mapper: BEHAVIORAL_ALERT_QUEUE_OK | symbol=EURUSD | temporal=output\dashboard_surface\EURUSD\node.json | energy=output\dashboard_surface\EURUSD\energy.json | out=output\behavioral_alert_queue_EURUSD.json | behavioral_count=2 | degraded_count=1
- `logs\task_scheduler.log` — 2026-05-12T09:14:18.315545+00:00 STEP_START USDJPY.behavioral_mapper :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_behavioral_alert_mapper_once.py --symbol USDJPY --temporal output\dashboard_surface\USDJPY\node.json --energy output\dashboard_surface\USDJPY\energy.json --out output/behavioral_alert_queue_USDJPY.json --pretty --summary

### Overlap excerpts

- `logs\task_scheduler.log` — ^C2026-05-12T09:07:01.840208+00:00 OVERLAP_SKIP cycle=1 previous lock active

### Parse excerpts

- `logs\task_scheduler.log` — 2026-05-12T08:59:15.404337+00:00 STEP_START USDJPY.regime_legacy :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_regime_engine_once.py --db powerflow.db --symbol USDJPY --out output\dashboard_surface\USDJPY\regime_legacy.json --pretty
- `logs\task_scheduler.log` — 2026-05-12T08:59:15.618531+00:00 STDOUT USDJPY.regime_legacy: REGIME_LEGACY_OK | symbol=USDJPY | out=output\dashboard_surface\USDJPY\regime_legacy.json | regime=UNKNOWN | confidence=0.0
- `logs\task_scheduler.log` — 2026-05-12T08:59:15.618924+00:00 STEP_START USDJPY.temporal_density :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_temporal_density_once.py --db powerflow.db --symbol USDJPY --out output/temporal_density_state_USDJPY.json --pretty
- `logs\task_scheduler.log` — 2026-05-12T08:59:15.912277+00:00 STEP_START USDJPY.spearman_gravity :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_spearman_gravity_once.py --db powerflow.db --symbol USDJPY --out output/spearman_gravity_state_USDJPY.json --pretty
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.473403+00:00 STEP_START USDJPY.behavioral_mapper :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_behavioral_alert_mapper_once.py --symbol USDJPY --temporal output\dashboard_surface\USDJPY\node.json --energy output\dashboard_surface\USDJPY\energy.json --out output/behavioral_alert_queue_USDJPY.json --pretty --summary
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.577448+00:00 STDOUT USDJPY.behavioral_mapper: BEHAVIORAL_ALERT_QUEUE_OK | symbol=USDJPY | temporal=output\dashboard_surface\USDJPY\node.json | energy=output\dashboard_surface\USDJPY\energy.json | out=output\behavioral_alert_queue_USDJPY.json | behavioral_count=1 | degraded_count=0
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.577765+00:00 SYMBOL_END USDJPY
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.578067+00:00 STEP_START cross_symbol_validation :: C:\Users\User\AppData\Local\Python\pythoncore-3.14-64\python.exe run_cross_symbol_validation_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
- `logs\task_scheduler.log` — 2026-05-12T08:59:16.696399+00:00 STDOUT cross_symbol_validation: "MODERATE", |         "evidence_count": 1 |       }, |       "JPY": { |         "score": 0.729883, |         "raw_score": 41.49, |         "label": "STRONG", |         "evidence_count": 1 |       }, |       "USD": { |         "score": -1.0, |         "raw_score": -56.844747, |         "label": "WEAK", |         "evidence_count": 3 |       } |     }, |     "symbol_evidence": [ |       { |         "symbol": "GBPUSD", |         "base"
- `logs\task_scheduler.log` — 2026-05-12T09:12:01.837049+00:00 CYCLE_START id=1 symbols=['GBPUSD', 'EURUSD', 'USDJPY']

## Existing audit runner

### run_audit_usdjpy_once.py

- returncode : `0`

```text
rames": [
    1
  ],
  "other_symbols": [
    "EURGBP",
    "EURJPY",
    "EURUSD",
    "GBPJPY",
    "GBPUSD",
    "USDJPY"
  ],
  "symbol_counts": [
    {
      "symbol": "GBPUSD",
      "rows": 11415
    },
    {
      "symbol": "EURUSD",
      "rows": 616
    },
    {
      "symbol": "EURGBP",
      "rows": 1
    },
    {
      "symbol": "EURJPY",
      "rows": 1
    },
    {
      "symbol": "GBPJPY",
      "rows": 1
    },
    {
      "symbol": "USDJPY",
      "rows": 1
    }
  ],
  "symbol_latest": [
    {
      "symbol": "EURGBP",
      "rows": 1,
      "latest_timestamp": "2026-04-29T11:18:00+00:00"
    },
    {
      "symbol": "EURJPY",
      "rows": 1,
      "latest_timestamp": "2026-04-29T11:18:00+00:00"
    },
    {
      "symbol": "EURUSD",
      "rows": 616,
      "latest_timestamp": "2026-05-11T11:40:00+00:00"
    },
    {
      "symbol": "GBPJPY",
      "rows": 1,
      "latest_timestamp": "2026-05-04T12:20:00+00:00"
    },
    {
      "symbol": "GBPUSD",
      "rows": 11415,
      "latest_timestamp": "2026-05-12T12:34:00+00:00"
    },
    {
      "symbol": "USDJPY",
      "rows": 1,
      "latest_timestamp": "2026-05-04T12:20:00+00:00"
    }
  ],
  "usdjpy_rows_preview_limit": 500,
  "usdjpy_rows": [
    {
      "id": 3317,
      "created_at": "2026-05-04T12:20:00+00:00",
      "symbol": "USDJPY",
      "timeframe": 1,
      "bid": 156.981,
      "spread": 3.0,
      "force_gbp": 25.86,
      "force_usd": 43.5,
      "force_eur": 36.83,
      "force_jpy": 84.99,
      "force_cad": 54.97,
      "force_chf": 42.34,
      "force_aud": 34.29
    }
  ],
  "status": "DEGRADED",
  "diagnosis": "STALE DATA - CAPTURE INACTIVE OR INCOMPLETE",
  "recommendation": "Check MT4 EA symbols list / Check bridge insertion logic / Verify USDJPY enabled in capture",
  "action_required": "URGENT",
  "expected": {
    "rows_total": "> 100 if capture OK",
    "latest_timestamp": "today/recent if capture OK",
    "timeframes": "multiple active TFs if full capture OK"
  }
}

```
### audit_usdjpy_fast.py

- returncode : `0`

```text
USDJPY_AUDIT_FAST verdict=THIN
JSON: C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\output\usdjpy_audit_fast_20260512_093612.json
MD: C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core\RAPPORT_USDJPY_CAPTURE_AUDIT_FAST_20260512_093612.md

```

## Architecture decision

```text
Do not patch capture_bridge.py until this diagnostic is reviewed.
Do not write powerflow.db.
Do not change P0 or dashboard.
Next change must target the classified bottleneck only.
```
