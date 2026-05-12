# README — DATA_HEALTH_MONITOR

## Mission

Surveiller la santé des données PowerFlow par symbole et timeframe.

Le module mesure :

```text
last_data_utc
age_minutes
row_count
temporal_gaps
symbol status
global_status
```

## Fichiers

```text
pf_data_health_monitor.py
run_data_health_monitor_once.py
dashboard_normalize_data_health.py
install_data_health.ps1
README_DATA_HEALTH.md
```

## Installation

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core

Expand-Archive `
  -Path "C:\Users\User\Downloads\P1_DATA_HEALTH_MONITOR.zip" `
  -DestinationPath ".\_p1_data_health_monitor" `
  -Force

cd .\_p1_data_health_monitor

powershell -ExecutionPolicy Bypass -File .\install_data_health.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

## Commande manuelle

```powershell
python run_data_health_monitor_once.py `
  --db powerflow.db `
  --symbols GBPUSD,EURUSD,USDJPY `
  --output output/data_health_monitor.json `
  --pretty
```

Puis normalisation dashboard :

```powershell
python dashboard_normalize_data_health.py `
  --input output/data_health_monitor.json `
  --output output/dashboard_surface/data_health.json `
  --pretty
```

## DB read-only

Connexion obligatoire :

```python
sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
```

Le module utilise une variante robuste pour les chemins Windows/relatifs, tout en conservant `mode=ro`.

## Table source

Le module découvre automatiquement une table compatible.

Priorité :

```text
force_snapshots
currency_force_snapshots
force_snapshot
market_snapshots
snapshots
```

Colonnes cherchées :

```text
symbol / pair / instrument
timeframe / tf / tf_minutes / timeframe_minutes / period
created_at / timestamp_utc / timestamp / time_utc / datetime_utc / datetime / time / ts / date
```

## Statuts symbole

```text
LIVE_OK
HTF_INCOMPLETE
DATA_STALE
PARTIAL_STALE
```

Règles principales :

```text
DATA_STALE      dernière donnée symbole > 60 minutes ou aucune donnée
HTF_INCOMPLETE  TF240 ou TF1440 < 50 rows
LIVE_OK         TF1/5/15 < 30 minutes et densité minimale OK
PARTIAL_STALE   données récentes présentes mais stack live incomplète
```

## Global status

```text
LIVE_OK
PARTIAL_STALE
CRITICAL_STALE
```

## Outputs

Runtime :

```text
output/data_health_monitor.json
output/dashboard_surface/data_health.json
```

Ne pas committer ces outputs.

## Dashboard contract

```json
{
  "global_status": "LIVE_OK",
  "symbols": [
    {"symbol": "GBPUSD", "status": "LIVE_OK", "last_update_age_min": 5},
    {"symbol": "USDJPY", "status": "DATA_STALE", "last_update_age_min": 120}
  ],
  "critical_issues": ["USDJPY_STALE_DATA", "EURUSD_HTF_INCOMPLETE"]
}
```

Le normalizer ajoute aussi `issues` par symbole.

## Commit

```powershell
git add pf_data_health_monitor.py
git add run_data_health_monitor_once.py
git add dashboard_normalize_data_health.py
git add README_DATA_HEALTH.md

git commit -m "P1: add data health monitor"

git push
```

Ne pas committer :

```text
output/data_health_monitor.json
output/dashboard_surface/data_health.json
_p1_data_health_monitor/
```

## Doctrine

```text
Le monitor mesure la santé des données.
Il ne juge pas le trade.
Il ne produit pas de BUY/SELL.
Il ne modifie pas la DB.
```
