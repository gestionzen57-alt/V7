# RAPPORT V7.3.5b — Trader Cockpit Clarity

## Objectif

V7.3.5b durcit la surface `dashboard_trader_cockpit.html` pour devenir un cockpit trader frontal lisible.

La page V7.2 reste une salle machine / audit. La page V7.3.5b devient la lecture quotidienne principale.

## Changements

- Ajout d'une ligne directe : `ETAT = ...`.
- Ajout d'une ligne directe : `SURVEILLER = ...`.
- EURUSD et USDJPY sont forcés en `WATCH_CONTEXT` quand ils sont paires de contexte.
- Les paires de contexte ne peuvent plus voler l'attention avec un faux `WAKE_TRADER`.
- Les risques techniques sont traduits en langage utile : HTF incomplet, gaps temporels, daily peu profond, weekly peu profond.
- Les clés techniques restent visibles uniquement dans l'audit.
- La page reste une page unique : trade symbol, lectures Daily / Topdown / Live / B6, scénarios, risques utiles, contexte paires.

## Principe PowerFlow

PowerFlow ne décide pas.
PowerFlow nomme la perception.
Le trader filtre, arbitre et agit.

## Fichiers

- `pf_trader_cockpit_once.py`
- `dashboard_trader_cockpit.html`
- `RAPPORT_V735B_TRADER_COCKPIT_CLARITY.md`
- `CHECKPOINT_V735B_TRADER_COCKPIT_CLARITY.md`
- `LEXIQUE_PATCH_V735B_TRADER_COCKPIT_CLARITY.md`

## Sorties

- `output/dashboard_surface/trader_cockpit.json`
- `output/dashboard_surface/trader_cockpit.txt`

## Validation attendue

Commande :

```powershell
python pf_trader_cockpit_once.py --symbols GBPUSD,EURUSD,USDJPY --trade-symbol GBPUSD --output output/dashboard_surface/trader_cockpit.json --txt output/dashboard_surface/trader_cockpit.txt --pretty
```

Résultat attendu :

```text
TRADER_COCKPIT_V735B_OK
```

Puis ouvrir :

```text
http://localhost:8787/dashboard_trader_cockpit.html
```
