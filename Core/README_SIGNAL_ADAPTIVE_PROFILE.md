# README — SIGNAL_ADAPTIVE_PROFILE TURBO

## Mission

Transformer le test local USDJPY en brique PowerFlow propre, paramétrique, multi-symbol.

## Fichiers

```text
pf_signal_adaptive_profile.py
run_signal_adaptive_profile_once.py
run_signal_adaptive_all_once.py
dashboard_normalize_signal_adaptive.py
dashboard_signal_adaptive_card_patch.html
dashboard_inject_signal_adaptive_card.py
scheduler_powerflow_turbo_wrapper.py
setup_windows_task_scheduler_turbo.ps1
install_signal_adaptive_turbo.ps1
README_SIGNAL_ADAPTIVE_PROFILE.md
LEXIQUE_PATCH_SIGNAL_ADAPTIVE_PROFILE.md
REGISTRE_BRIQUES_PATCH_SIGNAL_ADAPTIVE_PROFILE.md
RAPPORT_P2_SIGNAL_ADAPTIVE_PROFILE_TURBO_20260512.md
```

## Principe

Le module lit :

```text
output/data_health_monitor.json
```

et produit :

```text
output/dashboard_surface/{symbol}/signal_adaptive_profile.json
output/dashboard_surface/signal_adaptive_profiles.json
output/dashboard_surface/signal_adaptive.json
```

## Modes

```text
FULL_STACK_SIGNAL_READY
M1_TACTICAL_THIN_HTF
M1_ONLY_NO_RELAY
DATA_NOT_READY
```

## Permissions

```text
ALLOW_FULL_STACK_QUALIFIED
ALLOW_M1_QUALIFIED
ALLOW_M1_DEGRADED
HOLD_PERCEPTION_ONLY
```

Ce ne sont pas des ordres. Ce sont des états de perception.

## Installation simple

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core

Expand-Archive `
  -Path "C:\Users\User\Downloads\P2_SIGNAL_ADAPTIVE_PROFILE_TURBO.zip" `
  -DestinationPath ".\_p2_signal_adaptive_turbo" `
  -Force

cd .\_p2_signal_adaptive_turbo

powershell -ExecutionPolicy Bypass -File .\install_signal_adaptive_turbo.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

## Avec dashboard

```powershell
powershell -ExecutionPolicy Bypass -File .\install_signal_adaptive_turbo.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -InjectDashboard
```

## Avec scheduler turbo

```powershell
powershell -ExecutionPolicy Bypass -File .\install_signal_adaptive_turbo.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -InjectDashboard `
  -UpdateTask
```

## Test manuel

```powershell
python run_data_health_monitor_once.py --db powerflow.db --symbols GBPUSD,EURUSD,USDJPY --output output/data_health_monitor.json --pretty
python run_signal_adaptive_all_once.py --symbols GBPUSD,EURUSD,USDJPY --pretty
python dashboard_normalize_signal_adaptive.py --pretty
```

## Wrapper turbo

```powershell
python scheduler_powerflow_turbo_wrapper.py --symbols GBPUSD,EURUSD,USDJPY --pretty
```

Le wrapper exécute :

```text
1. scheduler_powerflow.py --once
2. data health monitor
3. data health normalizer
4. flow ontology cycle
5. signal adaptive profiles
6. signal adaptive normalizer
```

## Commit

```powershell
git add pf_signal_adaptive_profile.py
git add run_signal_adaptive_profile_once.py
git add run_signal_adaptive_all_once.py
git add dashboard_normalize_signal_adaptive.py
git add dashboard_signal_adaptive_card_patch.html
git add dashboard_inject_signal_adaptive_card.py
git add scheduler_powerflow_turbo_wrapper.py
git add setup_windows_task_scheduler_turbo.ps1
git add README_SIGNAL_ADAPTIVE_PROFILE.md
git add LEXIQUE_PATCH_SIGNAL_ADAPTIVE_PROFILE.md
git add REGISTRE_BRIQUES_PATCH_SIGNAL_ADAPTIVE_PROFILE.md
git add RAPPORT_P2_SIGNAL_ADAPTIVE_PROFILE_TURBO_20260512.md

git commit -m "P2: add signal adaptive profile turbo layer"
git push
```

Si `-InjectDashboard` :

```powershell
git add dashboard_live.html
```

## Ne pas committer

```text
output/dashboard_surface/signal_adaptive*.json
output/dashboard_surface/*/signal_adaptive_profile.json
_p2_signal_adaptive_turbo/
dashboard_live.html.bak_signal_adaptive_*
```

## Doctrine

```text
M1 jamais censuré.
HTF thin qualifie, ne bloque pas.
Aucun BUY/SELL.
Aucun DB write.
Symbol paramétrique.
```
