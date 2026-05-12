# PowerFlow V7.3.4 — B6 Multi-Read Synthesis

## Objectif

Traiter B6 comme une lecture parallèle complète du flux live, et non comme un simple gate Telegram.

## Nouvelles briques

- `dashboard_normalize_b6_live_fusion.py`
- `pf_powerflow_multiread_synthesis_once.py`
- `dashboard_normalize_multiread_synthesis.py`
- `dashboard_multiread_synthesis_card_patch.html`
- `dashboard_inject_multiread_synthesis_card.py`
- `patch_scheduler_turbo_multiread_v734.py`

## Entrées

- `output/dashboard_surface/daily_journal_dashboard.json`
- `output/dashboard_surface/topdown_reader.json`
- `output/dashboard_surface/live_brief_dashboard.json`
- `output/dashboard_surface/b6_live_fusion_dashboard.json`
- `output/dashboard_surface/signal_adaptive.json`
- `output/dashboard_surface/data_health.json`

## Sorties

- `output/dashboard_surface/b6_live_fusion_dashboard.json`
- `output/dashboard_surface/powerflow_multiread_synthesis.json`
- `output/dashboard_surface/multiread_synthesis_dashboard.json`
- `output/dashboard_surface/<SYMBOL>/powerflow_multiread_synthesis.txt`

## Installation

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v734_b6_multiread_synthesis.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

Avec B6 + dashboard + scheduler :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v734_b6_multiread_synthesis.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -RunB6 `
  -InjectDashboard `
  -PatchScheduler
```
