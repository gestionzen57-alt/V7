# INTEGRATION GUIDE - Dashboard MultiSymbol UI + USDJPY Audit

## Objectif
Installer une UI dashboard multi-symbol et un audit read-only USDJPY dans PowerFlow V7.2.1.

## Installation
Depuis Core ou depuis le dossier extrait du ZIP:

```powershell
powershell -ExecutionPolicy Bypass -File .\git_deploy_dashboard_ui_usdjpy.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core"
```

Avec commit/push:

```powershell
powershell -ExecutionPolicy Bypass -File .\git_deploy_dashboard_ui_usdjpy.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -CommitPush
```

Mode sans remplacement de dashboard_live.html:

```powershell
powershell -ExecutionPolicy Bypass -File .\git_deploy_dashboard_ui_usdjpy.ps1 -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" -NoDashboardReplace
```

## Validation rapide

```powershell
python run_audit_usdjpy_once.py --db powerflow.db --pretty
python test_dashboard_tabs.py --html dashboard_live.html --core . --check-runtime-outputs --pretty
```

## Doctrine
- DB read-only.
- Pas de BUY/SELL.
- Pas de fusion des donnees par symbole.
- Cross-validation globale separee des tabs par symbole.
