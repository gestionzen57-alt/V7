# README — V7.3.6 Trader Journal J+1

## Install

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v736_trader_journal_j1.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY
```

Avec scheduler :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v736_trader_journal_j1.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -PatchScheduler
```

## Manual run

```powershell
python pf_trader_journal_j1.py --symbols GBPUSD,EURUSD,USDJPY --pretty
```

## Outputs

```text
output/dashboard_surface/trader_journal_j1.json
output/dashboard_surface/trader_journal_j1.md
```
