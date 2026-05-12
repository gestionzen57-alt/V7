# PowerFlow V7.3 — TOPDOWN_MARKET_READER

## Mission

PowerFlow V7.3 transforme les briques V7.2.1 en lecture top-down exploitable :

```text
HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS
```

Le moteur ne décide pas. Il lit, qualifie, nomme et remonte.
Le trader analyse et décide.

## Fichiers livres

- `pf_price_schema_probe.py` : audit read-only de la DB pour trouver OHLC / force snapshots.
- `pf_htf_context_reader.py` : lecture Weekly / Daily / H4 quand OHLC disponible.
- `pf_zone_rotation_mapper.py` : zones testees, rejetees, breaks, reintegrations.
- `pf_mtf_day_plan_builder.py` : preparation H1 / M30 / M15.
- `pf_ltf_execution_condition_reader.py` : conditions M15 / M5 / M1.
- `pf_daily_market_reader.py` : assemblage top-down + journal quotidien.
- `run_topdown_market_reader_once.py` : runner 1 symbole.
- `run_topdown_market_reader_all_once.py` : runner multi-symbole.
- `dashboard_normalize_topdown_reader.py` : normalisation dashboard.
- `dashboard_topdown_reader_card_patch.html` : carte dashboard.
- `dashboard_inject_topdown_reader_card.py` : injection idempotente dans `dashboard_live.html`.
- `install_topdown_market_reader.ps1` : installation + py_compile + test.

## Installation

Depuis le dossier extrait :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_topdown_market_reader.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

Avec injection dashboard :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_topdown_market_reader.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -InjectDashboard
```

Avec commit/push :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_topdown_market_reader.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -InjectDashboard `
  -CommitPush
```

## Commandes directes

```powershell
python pf_price_schema_probe.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty

python run_topdown_market_reader_once.py --db powerflow.db --symbol GBPUSD --pretty

python run_topdown_market_reader_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty

python dashboard_normalize_topdown_reader.py --pretty
```

## Outputs

Par symbole :

```text
output/dashboard_surface/{symbol}/topdown_market_reading.json
output/daily_journal/{symbol}/{date}_topdown_market_reading.json
output/daily_journal/{symbol}/{date}_topdown_market_reading.md
```

Global dashboard :

```text
output/dashboard_surface/topdown_market_reader.json
output/dashboard_surface/topdown_reader.json
output/dashboard_surface/price_schema_probe.json
```

## Doctrine

- PowerFlow part du HTF.
- M1 reste le microfilm d'entree, jamais censure, seulement qualifie.
- La sortie principale parle flux, zone, rotation, relais, fenetre.
- Les mesures brutes restent en drill-down.
- Aucun BUY/SELL.
- Read-only DB strict.
