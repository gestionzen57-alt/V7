# DASHBOARD WRAPPER HARDENING — PowerFlow V7.2

## Objet

Deux durcissements mineurs après livraison finale :

1. `dashboard_hydration_failure_doctor.py` lit maintenant les deux patterns de logs :
   - `dashboard_hydrate_*.log`
   - `dashboard_hydration_*.log`

2. `run_dashboard_live_stack.ps1` vérifie les exit codes des sous-process :
   - normalizer
   - contract validator
   - coverage doctor

Avant, le wrapper pouvait afficher `OK Dashboard stack` même si un sous-process Python avait échoué.

## Installation

Copier les deux fichiers dans `Core/` :

```powershell
copy .\runtime\dashboard_hydration_failure_doctor.py .\
copy .\runtime\run_dashboard_live_stack.ps1 .\
```

## Validation

```powershell
python -m py_compile .\dashboard_hydration_failure_doctor.py

.\run_dashboard_live_stack.ps1 `
  -Root . `
  -Html .\dashboard_live_v7.2_final.html `
  -Normalize `
  -Validate `
  -Doctor

.\run_hydration_failure_doctor.ps1 -CorePath .
```

Attendu :

```text
PASS dashboard contract validation: 0 fail, 0 warn
WARN/failed : 0
```

## Commit recommandé

```text
Dashboard: harden V7.2 wrapper exit checks and log doctor
```
