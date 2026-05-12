# REGISTRE BRIQUES PATCH — V7.3 TURBO WRAPPER

## scheduler_powerflow_turbo_wrapper.py

Type : orchestration.

Role : executer le cycle PowerFlow principal puis les couches dashboard/lecture : data health, ontology, signal adaptive, price schema, topdown reader.

Dependances appelees :

- `scheduler_powerflow.py`
- `run_data_health_monitor_once.py`
- `dashboard_normalize_data_health.py`
- `run_flow_ontology_cycle_once.py`
- `run_signal_adaptive_all_once.py`
- `dashboard_normalize_signal_adaptive.py`
- `pf_price_schema_probe.py`
- `run_topdown_market_reader_all_once.py`
- `dashboard_normalize_topdown_reader.py`

## install_v73_turbo_wrapper.ps1

Type : installation / patch.

Role : sauvegarder l'ancien wrapper, copier le nouveau wrapper, compiler, tester, optionnellement mettre a jour la tache Windows et commiter.

Options :

- `-CorePath`
- `-Symbols`
- `-UpdateTask`
- `-CommitPush`
