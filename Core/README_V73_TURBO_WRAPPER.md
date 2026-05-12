# README — V7.3 TURBO WRAPPER

## Objet

Ce patch integre V7.3 TOPDOWN_MARKET_READER dans le cycle turbo PowerFlow.

Le wrapper execute maintenant la chaine :

1. `scheduler_powerflow.py --once`
2. `run_data_health_monitor_once.py`
3. `dashboard_normalize_data_health.py`
4. `run_flow_ontology_cycle_once.py`
5. `run_signal_adaptive_all_once.py`
6. `dashboard_normalize_signal_adaptive.py`
7. `pf_price_schema_probe.py`
8. `run_topdown_market_reader_all_once.py`
9. `dashboard_normalize_topdown_reader.py`

## Commande manuelle

```powershell
python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY
```

## Outputs principaux

- `output/data_health_monitor.json`
- `output/dashboard_surface/data_health.json`
- `output/dashboard_surface/flow_ontology_cycle_summary.json`
- `output/dashboard_surface/signal_adaptive_profiles.json`
- `output/dashboard_surface/signal_adaptive.json`
- `output/dashboard_surface/price_schema_probe.json`
- `output/dashboard_surface/topdown_market_reader.json`
- `output/dashboard_surface/topdown_reader.json`

## Doctrine

PowerFlow V7.3 lit le marche en top-down :

`HTF_CONTEXT -> MTF_DAY_PLAN -> LTF_EXECUTION_CONDITIONS`

Le M1 reste le microfilm tactique. Il est qualifie, jamais censure.
