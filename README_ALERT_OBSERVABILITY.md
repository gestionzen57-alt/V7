# PowerFlow V7.2 — Alert Observability Metrics Pack

This pack adds a non-blocking alert observability brique.

It does not filter alerts.
It does not validate trades.
It does not suppress early signals.
It only measures coverage, distribution, duplicates and technical observability.

## Files

- Core/pf_alert_observability_metrics.py
- Core/run_alert_observability_metrics_once.py
- scripts/validate_alert_observability.ps1

## Install

Copy files into repo root preserving folders.

## Validate

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT
.\scripts\validate_alert_observability.ps1
```

## Run live queue

```powershell
python Core\run_alert_observability_metrics_once.py --pretty
```

## Outputs

- output/alert_metrics.json
- output/alert_metrics.md
