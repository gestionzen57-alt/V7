# README — P5 FLOW ONTOLOGY DASHBOARD + SCHEDULER

## Mission

Livrer les deux suites logiques après P4 :

```text
A. Dashboard Ontology Card
B. Scheduler Integration
```

## Fichiers

```text
dashboard_flow_ontology_card_patch.html
dashboard_inject_flow_ontology_card.py
run_flow_ontology_cycle_once.py
scheduler_powerflow_ontology_wrapper.py
setup_windows_task_scheduler_ontology.ps1
install_ontology_dashboard_scheduler.ps1
README_ONTOLOGY_DASHBOARD_SCHEDULER.md
RAPPORT_P5_ONTOLOGY_DASHBOARD_SCHEDULER_20260512.md
```

## Principe

### Dashboard Card

Lit :

```text
output/flow_ontology_report.json
```

fallback :

```text
output/dashboard_surface/flow_ontology_report.json
```

Affiche :

```text
coverage
dominant behavior
unmapped count
category counts
technical_risks
```

### Scheduler Integration

Stratégie safe :

```text
scheduler_powerflow_ontology_wrapper.py
```

Le wrapper exécute :

```text
python scheduler_powerflow.py --once --symbols GBPUSD,EURUSD,USDJPY
python run_flow_ontology_cycle_once.py --symbols GBPUSD,EURUSD,USDJPY
```

Pourquoi wrapper plutôt que patch brutal ?

```text
- évite regex fragile dans scheduler_powerflow.py
- compatible Windows Task Scheduler
- garde scheduler original intact
- intègre l’ontologie après la génération des alertes
```

## Installation test sans patch dashboard ni task

```powershell
powershell -ExecutionPolicy Bypass -File .\install_ontology_dashboard_scheduler.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

## Installation avec injection dashboard

```powershell
powershell -ExecutionPolicy Bypass -File .\install_ontology_dashboard_scheduler.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -InjectDashboard
```

## Installation avec update Windows Task Scheduler

```powershell
powershell -ExecutionPolicy Bypass -File .\install_ontology_dashboard_scheduler.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -InjectDashboard `
  -UpdateTask
```

## Test manuel wrapper

```powershell
python scheduler_powerflow_ontology_wrapper.py --symbols GBPUSD,EURUSD,USDJPY --pretty
```

## Test seulement ontologie cycle

```powershell
python scheduler_powerflow_ontology_wrapper.py --skip-scheduler --symbols GBPUSD,EURUSD,USDJPY --pretty
```

## Outputs

```text
output/flow_ontology_report.json
output/dashboard_surface/flow_ontology_report.json
output/flow_ontology_report_GBPUSD.json
output/dashboard_surface/GBPUSD/flow_ontology_report.json
output/flow_ontology_report_EURUSD.json
output/dashboard_surface/EURUSD/flow_ontology_report.json
output/flow_ontology_report_USDJPY.json
output/dashboard_surface/USDJPY/flow_ontology_report.json
output/dashboard_surface/flow_ontology_cycle_summary.json
```

Ne pas committer ces outputs.

## Commit

```powershell
git add dashboard_flow_ontology_card_patch.html
git add dashboard_inject_flow_ontology_card.py
git add run_flow_ontology_cycle_once.py
git add scheduler_powerflow_ontology_wrapper.py
git add setup_windows_task_scheduler_ontology.ps1
git add README_ONTOLOGY_DASHBOARD_SCHEDULER.md
git add RAPPORT_P5_ONTOLOGY_DASHBOARD_SCHEDULER_20260512.md

git commit -m "P5: add flow ontology dashboard card and scheduler wrapper"
git push
```

Si `-InjectDashboard` a été utilisé :

```powershell
git add dashboard_live.html
```

## Contraintes

```text
Pas de BUY/SELL
Pas de DB write
Ontologie = nommer le flux
Scheduler original non modifié
Dashboard lit seulement les outputs
```
