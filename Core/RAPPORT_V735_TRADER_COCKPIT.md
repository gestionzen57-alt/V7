# RAPPORT V7.3.5 — TRADER COCKPIT

## Objectif

V7.3.5 ajoute un cockpit trader séparé du dashboard d'audit technique.

La page actuelle V7.2 reste utile pour debug, mais elle est trop dense pour l'action : trop de cartes, trop de `MISSING`, trop de détails de salle machine. Le trader a besoin d'une surface courte : paire, attention, contexte HTF/Daily/Live/B6, alignement/conflit, scénarios de surveillance.

## Livrables

- `pf_trader_cockpit_once.py`
- `dashboard_trader_cockpit.html`
- `patch_scheduler_turbo_trader_cockpit_v735.py`
- `output/dashboard_surface/trader_cockpit.json`
- `output/dashboard_surface/trader_cockpit.txt`
- `RAPPORT_V735_TRADER_COCKPIT.md`
- `CHECKPOINT_V735_TRADER_COCKPIT.md`
- `LEXIQUE_PATCH_V735_TRADER_COCKPIT.md`
- `README_V735_TRADER_COCKPIT.md`

## Rôle de la brique

`pf_trader_cockpit_once.py` ne calcule pas de nouveau signal primaire.

Il lit les surfaces existantes :

- `daily_journal_dashboard.json`
- `topdown_reader.json`
- `live_brief_dashboard.json`
- `b6_live_fusion_dashboard.json`
- `multiread_synthesis_dashboard.json`
- `data_health.json`
- `signal_adaptive.json`

Puis il produit une lecture synthétique utilisable :

- action : `WATCH`, `WATCH_ATTENTION`, `WAKE_TRADER`
- synthesis : état multi-read dominant
- trader_line : phrase courte de perception
- feux : HTF / Daily / Live / B6
- scénarios de surveillance
- risques techniques utiles uniquement

## Doctrine

Le cockpit trader n'est pas le moteur.

Le cockpit trader lit la surface, simplifie et expose. Il ne décide pas. Il ne cache pas un conflit. Il ne transforme pas une alerte en ordre.

Séparation respectée :

- `pf_*` : perception / synthèse
- `dashboard_*` / HTML : affichage
- `output/dashboard_surface/*` : surface lisible
- trader : arbitrage final

## Différence avec le dashboard V7.2

Le dashboard V7.2 affiche la salle machine : runtime audit, sources live/stale/missing, dual regime, dual density, kinematics, fractal, cascade, session, memory, contract audit.

V7.3.5 affiche la lecture :

```text
GBPUSD | WAKE_TRADER | MULTIREAD_WAKE_TRADER
Lecture : conflit actif daily/topdown vs live. Surveiller réintégration, piège inverse ou second test.
HTF : REJECTION_OR_TRAP_WATCH
DAILY : SHORT_ACCUMULATION
LIVE : PAIR_UP
B6 : PAIR_DOWN / WATCH
ALIGN : CONFLICT
```

## Lecture attendue sur GBPUSD

Exemple après les derniers cycles :

- Daily : `SHORT_ACCUMULATION_OR_DISTRIBUTION_TRAP`
- Topdown : `REJECTION_OR_TRAP_WATCH`
- Live : `PAIR_UP`, `FLOW_PACKET`, `INFO`, `M5`
- B6 : `PAIR_DOWN`, `WATCH`, tension proxy informationnelle
- Multiread : `MULTIREAD_WAKE_TRADER` ou contexte de conflit

Interprétation cockpit : conflit actif entre contexte daily bearish trap et live pair-up. Surveiller réintégration, piège inverse, second test ou retour live pair-down.

## Risques techniques affichables

Le cockpit trader n'affiche que les risques qui qualifient la lecture :

- `DAILY_LOW_SAMPLE_FOR_ROTATION`
- `WEEKLY_LOW_SAMPLE_FOR_ROTATION`
- `GBPUSD_TEMPORAL_GAPS_PRESENT`
- `DATA_HEALTH_STATUS_HTF_INCOMPLETE`

Les risques B6 structurels restent en information secondaire :

- `ORDER_FLOW_PROXY_NOT_TRUE_LEVEL2`
- `MT4_NATIVE_BID_ASK_VOLUME_ABSENT`
- `M1_OHLC_PROXY_CAN_CREATE_FALSE_POSITIVES`

## Commande manuelle

```powershell
python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --pretty
```

Ouvrir :

```text
http://localhost:8787/dashboard_trader_cockpit.html
```

## Commande installation

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v735_trader_cockpit.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -TradeSymbol GBPUSD
```

Avec scheduler :

```powershell
powershell -ExecutionPolicy Bypass -File .\install_v735_trader_cockpit.ps1 `
  -CorePath "C:\Users\User\Desktop\ProjetPowerFlow\IA\GPT\Core" `
  -Symbols GBPUSD,EURUSD,USDJPY `
  -TradeSymbol GBPUSD `
  -PatchScheduler
```

## Validation

Critère de validation : en moins de 5 secondes le trader doit voir :

1. paire active ;
2. niveau d'attention ;
3. daily ;
4. live ;
5. B6 ;
6. conflit ou alignement ;
7. scénario à surveiller.

## Git attendu

Commit recommandé :

```powershell
git add pf_trader_cockpit_once.py dashboard_trader_cockpit.html patch_scheduler_turbo_trader_cockpit_v735.py
git add RAPPORT_V735_TRADER_COCKPIT.md CHECKPOINT_V735_TRADER_COCKPIT.md LEXIQUE_PATCH_V735_TRADER_COCKPIT.md README_V735_TRADER_COCKPIT.md
git add scheduler_powerflow_turbo_wrapper.py
git commit -m "V7.3.5: add trader cockpit surface"
git push
```
