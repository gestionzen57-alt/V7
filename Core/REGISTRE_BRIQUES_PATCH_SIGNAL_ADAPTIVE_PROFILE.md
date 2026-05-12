# REGISTRE BRIQUES PATCH — SIGNAL_ADAPTIVE_PROFILE

## Brique : pf_signal_adaptive_profile.py

Type : pf_* moteur read-only JSON  
Entrée : output/data_health_monitor.json  
Sorties : profils signal adaptatifs par symbole  
DB write : non  
BUY/SELL : non

## Runner : run_signal_adaptive_profile_once.py

Exécute un profil pour un symbole.

## Runner : run_signal_adaptive_all_once.py

Exécute les profils pour plusieurs symboles.

## Normalizer : dashboard_normalize_signal_adaptive.py

Produit le contrat dashboard :

```text
output/dashboard_surface/signal_adaptive.json
```

## Dashboard Card : dashboard_signal_adaptive_card_patch.html

Affiche :

```text
global_mode
symbol mode
signal_permission
context_confidence
technical_risks
```

## Scheduler Wrapper : scheduler_powerflow_turbo_wrapper.py

Cycle :

```text
scheduler -> data health -> ontology -> signal adaptive
```

## Windows Task Script : setup_windows_task_scheduler_turbo.ps1

Permet de pointer la tâche planifiée vers le wrapper turbo.
