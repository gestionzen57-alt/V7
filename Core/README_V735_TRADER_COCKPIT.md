# README V7.3.5 — Trader Cockpit

## Installation rapide

Dézipper dans un dossier temporaire puis lancer :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v735_trader_cockpit.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -TradeSymbol GBPUSD
```

## Test manuel

```powershell
cd C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core
python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --pretty
```

## Ouvrir la page

```text
http://localhost:8787/dashboard_trader_cockpit.html
```

## Patch scheduler

Après validation visuelle :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v735_trader_cockpit.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -TradeSymbol GBPUSD `
  -PatchScheduler
```

## Commit

```powershell
git add pf_trader_cockpit_once.py dashboard_trader_cockpit.html patch_scheduler_turbo_trader_cockpit_v735.py
git add RAPPORT_V735_TRADER_COCKPIT.md CHECKPOINT_V735_TRADER_COCKPIT.md LEXIQUE_PATCH_V735_TRADER_COCKPIT.md README_V735_TRADER_COCKPIT.md
git add scheduler_powerflow_turbo_wrapper.py
git commit -m "V7.3.5: add trader cockpit surface"
git push
```
