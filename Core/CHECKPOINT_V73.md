# CHECKPOINT — POWERFLOW V7.3

## Etat valide

PowerFlow V7.3 = `TOPDOWN_MARKET_READER`.

Objectif : rapprocher PowerFlow de la lecture reelle du trader : HTF d'abord, MTF ensuite, LTF seulement pour condition d'attention.

## Dernier etat connu V7.2.1

Briques deja en place :

- Multi-symbol GBPUSD / EURUSD / USDJPY.
- Scheduler turbo wrapper actif.
- Data Health Monitor.
- Signal Adaptive Profile.
- Flow Ontology.
- Cross-symbol validation.
- M1 context score.
- M1 noise ratio probe.
- Dashboard cards.

## Decision V7.3

Ajouter une couche top-down :

```text
HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS -> DAILY_MARKET_READER
```

## Livrable V7.3

Fichiers essentiels :

- `pf_price_schema_probe.py`
- `pf_htf_context_reader.py`
- `pf_zone_rotation_mapper.py`
- `pf_mtf_day_plan_builder.py`
- `pf_ltf_execution_condition_reader.py`
- `pf_daily_market_reader.py`
- `run_topdown_market_reader_once.py`
- `run_topdown_market_reader_all_once.py`
- `dashboard_normalize_topdown_reader.py`

## Commande test

```powershell
python pf_price_schema_probe.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
python run_topdown_market_reader_all_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --pretty
python dashboard_normalize_topdown_reader.py --pretty
```

## Point de reprise

Verifier d'abord :

```text
output/dashboard_surface/price_schema_probe.json
```

Si `price_reading_capability = OHLC_AVAILABLE`, V7.3 peut lire niveaux/zones/sweeps.
Si `FORCE_ONLY_NO_OHLC`, V7.3 peut lire drivers/forces mais pas les zones proprement.

## Doctrine

PowerFlow lit et remonte.
Le trader analyse et decide.
