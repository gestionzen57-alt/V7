# RAPPORT P5 — FLOW ONTOLOGY DASHBOARD + SCHEDULER  
PowerFlow V7.2.1 — 2026-05-12

## Mission

Livrer les deux suites après P4 :

```text
A. Dashboard Ontology Card
B. Scheduler Integration
```

## Choix technique

L’intégration scheduler est faite via wrapper :

```text
scheduler_powerflow_ontology_wrapper.py
```

et non par patch direct de `scheduler_powerflow.py`.

Raison :

```text
- moins fragile
- compatible Windows Task Scheduler
- garde le scheduler original intact
- évite les dépendances circulaires
- permet rollback immédiat
```

## Séquence wrapper

```text
1. scheduler_powerflow.py --once --symbols {symbols}
2. run_flow_ontology_cycle_once.py --symbols {symbols}
```

## Card dashboard

Fichier :

```text
dashboard_flow_ontology_card_patch.html
```

Elle affiche :

```text
ontology_coverage
dominant_behavior_category
alerts_unmapped
alerts_by_category
technical_risks
```

## Runner cycle

Fichier :

```text
run_flow_ontology_cycle_once.py
```

Il supporte multi-symbol :

```text
output/behavioral_alert_queue_{symbol}.json
output/dashboard_surface/{symbol}/behavioral_alert_queue.json
fallback output/behavioral_alert_queue.json
```

Outputs produits :

```text
output/flow_ontology_report_{symbol}.json
output/dashboard_surface/{symbol}/flow_ontology_report.json
output/flow_ontology_report.json
output/dashboard_surface/flow_ontology_report.json
output/dashboard_surface/flow_ontology_cycle_summary.json
```

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File .\install_ontology_dashboard_scheduler.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

Avec dashboard :

```powershell
-InjectDashboard
```

Avec Windows Task Scheduler :

```powershell
-UpdateTask
```

## Conclusion

P5 rend l’ontologie opérationnelle en continu :

```text
alertes -> ontologie -> dashboard -> scheduler cycle
```

Le moteur ne décide pas.
Il nomme le flux.
